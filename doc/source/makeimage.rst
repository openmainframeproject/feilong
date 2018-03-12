
Basic Usage
***********

This section discusses setting up the Linux on System z(zLinux) that is the
target of the initial image capture, after capturing this zLinux, an image will
be generated, it can be used to import into zVM cloud connector's image
repository or Openstack glance for later deployment.

Image Requirements
==================

These are the requirements for an image to be captured and deployed by zVM
cloud connector:
The supported Linux distributions are:
– RHEL 6.x
– RHEL 7.x
– SLES 11.x
– SLES 12.x
– Ubuntu 16.04

Where x is the zLinux's detail release number

The supported root disk type for capture/deploy are:
– FBA
– ECKD

An image deployed by zVM cloud connector must match the disk type configured by
disk_pool in /etc/zvmsdk/zvmsdk.conf, only either FBA or ECKD image can be
deployed in zvmsdk, but not both at the same time. If you wish to switch
image types, you need to change the disk_pool configuration option and restart
sdkserver to make the changes take effect.

If you capture a zLinux with root disk size greater than 5GB, or if you deploy 
an image to an root disk larger than 5G in size, please modify the timeout value
for httpd service to make it work expected. Please refer to Configure Apache¶ 
section in this document for reference.

The zLinux that used as the source of the captured image should meet the 
following criteria: 
- The root filesystem must not be on a logical volume.
- The minidisk on which the root filesystem resides should be a minidisk of
the same type as desired for a subsequent deploy (for example, an ECKD disk
image should be captured for a subsequent deploy to an ECKD disk), and it should
not be a full-pack minidisk, since cylinder 0 on full-pack minidisks is reserved,
and be defined with virtual address 0100
- The root disk should have a single partition.
- zVM cloud connector only support deploy an image to a disk larger or equal than
the source image's root disk size , otherwise, it would result in loss of data.
The image's root disk size can be got by command.

    .. code-block:: text

        hexdump -C -n 64 <image_path>


Make a Deployable zVM Image for zVM Cloud Connector
====================================================

Install Linux on z Systems(zLinux) in a Virtual Machine
-------------------------------------------------------

1.Prepare a Linux on z Systems virtual server in the z/VM system.For more
information, refer to the IBM Redbook: The Virtualization Cookbook for z/VM 6.3,
RHEL 6.4 and SLES 11 SP3. You will have to make adjustments to the procedures
that are documented in this Redbook in order to keep the resulting virtual
server within the bounds of the image requirements. See “Image Requirements”
on above section).
- For RHEL 7 installation, see http://www.redbooks.ibm.com/abstracts/sg248303.html?Open.
- For SLES 12 installation, see http://www.redbooks.ibm.com/abstracts/sg248890.html?Open.
- For Ubuntu 16.04 installation, see http://www.redbooks.ibm.com/redbooks/pdfs/sg248354.pdf
Note that ext file sytem is supported for RHEL6.x, SLES11.x, and Ubuntu 16.04; 
both the ext and xfs file systems are supported for RHEL 7 and SLES 12.

2.Install the mkisofs and openssl modules on it.

3.Make sure SELinux is disabled and the SSH connection (default port number is 22)
 can pass the firewall.

4 Set UseDNS no in /etc/ssh/sshd_config file in order to improve the inventory
 collection efficiency.

5 For Ubuntu 16.04, you must enable root ssh access. By default, root ssh access
 is not enabled.


Installation and Configuration of IUCV service in zLinux
--------------------------------------------------------

zVM cloud connector manage the deployed vm by IUCV channel. IUCV service
should be configured on zLinux before capture to make image. Following the below
steps to install and configure IUCV service. 


Configuration of zvmguestconfigure on zLinux
............................................

1 Logon your BYOL, and copy the following files to target vm

    .. code-block:: text

        scp -r /opt/zthin/bin/IUCV/ root@<zLinux_ip>:/root/

    Where: <zLinux_ip> is the ip address of zLinux

2 Logon zLinux, install and configure IUCV service by commands:

    .. code-block:: text

        cd /root/IUCV
        ./iucvserverdaemoninstaller.sh -a <auth_userid>

Where: auth_userid is the BYOL's userid, you may get the detail
usage of iucvserverdaemoninstaller.sh by command

    .. code-block:: text

        ./iucvserverdaemoninstaller.sh -h

3 Logon your BYOL, run a simple command to check the if the iucv 
channel is set up correctly by commands:

    .. code-block:: text

      /opt/zthin/bin/IUCV/iucvclnt <zLinux_userid> date

Where: <zLinux_userid> is the userid of zLinux. 

If above commands execute successfully, you may continue to next steps.
Otherwise, stop here and re-check the configuration.


Configuration of activation engine(AE) in zLinux
------------------------------------------------
To do useful work with the user data, the zLinux image must be configured to
run a service that retrieves the user data passed from the zVM cloud connector
and then takes some actions based on the contents of that data. This service is
also known as an activation engine (AE).

For zLinux images that deployed by zVM cloud connector, zvmguestconfigure must
be installed and configured as the pre-AE before any other underlying AE.
Customers can choose their own underlying AE, such as cloud-init,
scp-cloud-init, and so on, according to their requirements. In this document,
we use cloud-init as an example when showing how to configure an image.
These steps of configuration zvmguestconfigure and cloud-init are described in
subsequent sections.

Configuration of zvmguestconfigure in zLinux
--------------------------------------------

The zVM Cloud Connector supports initiating changes to zLinux while it is shut
down or the virtual machine is logged off.The changes to zLinux are implemented
using zvmguestconfigure that is run when Linux is booted the next time.

The zvmguestconfigure script/service must be installed in the zLinux so it
can process change request files transmitted by zVM cloud connector to the
reader of the zLinux as a class X file, zvmguestconfigure also bridge the gap
of zLinux and higher layer of zVM Cloud, for example, it will make iso9660
loop device that will be consumed by cloud-init, which is the common active
engine to handle early initialization of a cloud instance.The steps of how to
install zvmguestconfigure is described in subsequence sections.

Configuration of zvmguestconfigure on RHEL6.x and SLES11.x
............................................................

Perform the following steps:
1 Log on your BYOL, and copy the zvmguestconfigure script that is located at
<zvmsdk_download_path>/python-zvm-sdk/tools/share/zvmguestconfigure to your
zLinux, where zvmsdk_download_path can be found at section z/VM SDK install

2 Logon on your zLinux, change the script to specify the authorizedSenders in 
zvmguestconfigure file. It is recommended that this be set to a list of user IDs
which are allowed to transmit changes to the machine. At a minimum, this list
should include the userid of BYOL, which is usually OPNCLOUD. (It can be set
to '*', which indicates any virtual machine on the same LPAR may
send configuration requests to it)

3 zvmguestconfigure is configured to run with run level 2, 3 and 5. It is not
configured to run as part of custom run level 4. If that run level is going to
be used, then the # Default-Start: line at the beginning of the file should be
updated to specify run level 4 in addition to the current run levels.

4 Copy the zvmguestconfigure file to /etc/init.d and make it executable

5 Add the zvmguestconfigure as a service by issuing:

    .. code-block:: text

    chkconfig --add zvmguestconfigure

6 Activate the script by issuing:

    .. code-block:: text

        chkconfig zvmguestconfigure on

If you wish to run with custom run level 4, then add 4 to the list of levels:

  .. code-block:: text

        chkconfig --level 2345 zvmguestconfigure on

7. Verify that you installed the correct version of zvmguestconfigure on the
target machine. Do this by issuing the following service command:

    .. code-block:: text

        service zvmguestconfigure version
        zvmguestconfigure version: 1.0

8 Verify that zvmguestconfigure on the target machine is configured to handle
requests from the server specified at step 2. Do this by issuing the following
service command:

    .. code-block:: text

        service zvmguestconfigure status
        zvmguestconfigure is enabled to accept configuration reader files from: OPNCLOUD

If zvmguestconfigure is not enabled to accept configuration reader files then verify
that you followed Step 2.

Configuration of zvmguestconfigure on RHEL 7.x and SLES 12.x
............................................................

Perform the following steps:
1 Log on your BYOL, and copy the zvmguestconfigure and zvmguestconfigure.service
script that is located at <zvmsdk_download_path>/python-zvm-sdk/tools/share/zvmguestconfigure 
to your zLinux, where zvmsdk_download_path can be found at the section z/VM SDK install

2 Logon on your zLinux, change the script to specify the authorizedSenders in 
zvmguestconfigure file. It is recommended that this be set to a list of user IDs
which are allowed to transmit changes to the machine. At a minimum, this list
should include the userid of BYOL, which is usually OPNCLOUD. (It can be set
to '*', which indicates any virtual machine on the same LPAR may
send configuration requests to it)

3 Copy the zvmguestconfigure script to the /usr/bin/ folder and make it executable.

4. Install the zvmguestconfigure.service in the target zLinux:
-If the target Linux machine is RHEL7.x, copy the zvmguestconfigureconf4z.service
file to: /lib/systemd/system
-If the target Linux machine is SLES12.x, copy the zvmguestconfigure.service
file to: /usr/lib/systemd/system

Also, if the target machine is SLES12.x, it is recommended that you change 
the NetworkManager.service to be wicked.service in the zvmguestconfigure.service

5 Enable the zvmguestconfigure service by issuing:

    .. code-block:: text

          systemctl enable zvmguestconfigure.service

6 Start the zvmguestconfigure service by issuing:

    .. code-block:: text

    systemctl start zvmguestconfigure.service

Configuration of zvmguestconfigure on Ubuntu 16.04
..................................................

1 Log on your BYOL, and copy the zvmguestconfigure and zvmguestconfigure.service
script that is located at <zvmsdk_download_path>/python-zvm-sdk/tools/share/zvmguestconfigure 
to your zLinux, where zvmsdk_download_path can be found at the section z/VM SDK install

2 Logon on your zLinux, change the script to specify the authorizedSenders in 
zvmguestconfigure file. It is recommended that this be set to a list of user IDs
which are allowed to transmit changes to the machine. At a minimum, this list
should include the userid of BYOL, which is usually OPNCLOUD. (It can be set
to '*', which indicates any virtual machine on the same LPAR may
send configuration requests to it)

3 On zLinux, copy the zvmguestconfigure script to the /usr/bin/ folder and make
it executable.

4 Install the zvmguestconfigure.service in the target Ubuntu machine, tailor the
zvmguestconfigure.service file for an Ubuntu 16.04 image by modifying the file 
contents as follows:
[Unit]
Description=Activation engine for configuring z/VM when it starts
Wants=local-fs.target
After=local-fs.target
Before=cloud-init-local.service network-pre.target
[Service]
Type=oneshot
ExecStart=/usr/bin/zvmguestconfigure start
StandardOutput=journal+console
[Install]
WantedBy=multi-user.target

After that, copy the zvmguestconfigure.service file to /lib/systemd/system.

5 Enable the zvmguestconfigure service by issuing:

    .. code-block:: text

          systemctl enable zvmguestconfigure.service

6 Start the zvmguestconfigure service by issuing:

    .. code-block:: text

        systemctl start zvmguestconfigure.service


Installation and Configuration of cloud-init
--------------------------------------------
Please note that if customer did not pass customize data via openstack, cloud-init
may not need to be installed.???

OpenStack uses cloud-init as its activation engine.
Some distributions include cloud-init either already installed or available to
be installed. If your distribution does not include cloud-init, you can
download the code from https://launchpad.net/cloud-init/+download. After
installation, if you issue the following shell command and no errors occur,
cloud-init is installed correctly.

    .. code-block:: text

        cloud-init init --local

Installation and configuration of cloud-init differs among different Linux
distributions, and cloud-init source code may change. This section provides 
general information, but you may have to tailor cloud-init to meet the needs
of your Linux distribution. You can find a community-maintained list of
dependencies at http://ibm.biz/cloudinitLoZ.

The z/VM OpenStack support has been tested with cloud-init 0.7.4 and 0.7.5 for
RHEL6.x and SLES11.x, 0.7.6 for RHEL7.x and SLES12.x, and 0.7.8 for Ubuntu 16.04.
If you are using a different version of cloud-init, you should change your
specification of the indicated commands accordingly.



Import the images to glance in openstack
----------------------------------------



Import the images to sdk server
-------------------------------



