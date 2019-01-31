Image and cloud-init Configuration
**********************************

This section discusses setting up the Linux on System z(zLinux) that is the
target of the initial image capture, after capturing this zLinux, an image will
be generated, it can be used to import into z/VM Cloud Connector's image
repository or Openstack glance for later deployment.

Image Requirements
==================

These are the requirements for an image to be captured and deployed by zVM
cloud connector:

1. The supported Linux distributions are:

- RHEL 6.x
- RHEL 7.x
- SLES 11.x
- SLES 12.x
- Ubuntu 16.04

Where x is the zLinux's minor release number

2. The supported root disk type for capture/deploy are:

- FBA
- ECKD

**NOTE**: An image deployed via z/VM Cloud Connector must match the disk type
configured by disk_pool in /etc/zvmsdk/zvmsdk.conf, only either FBA or ECKD image
can be deployed in zvmsdk, but not both at the same time. If you wish to switch
image types, you need to change the disk_pool configuration option and restart
sdkserver to make the changes take effect.

3. If you capture a zLinux with root disk size greater than 5GB, or if you deploy
   an image to an root disk larger than 5G in size, please modify the timeout value
   for httpd service to make it work expected. Please refer to :ref:`Configure Apache`
   section in this document for reference.

4. The zLinux that used as the source of the captured image should meet the
   following criteria:

  a. The root file system must not be on a logical volume

  b. The minidisk on which the root file system resides should be a minidisk of
     the same type as desired for a subsequent deploy (for example, an ECKD disk
     image should be captured for a subsequent deploy to an ECKD disk), and it should
     not be a full-pack minidisk, since cylinder 0 on full-pack minidisks is reserved.

  c. If the source image is captured from minidisk with virtual address 0100, it must
     be deployed to the virtual address 0100 of target Virtual Machine(VM) , otherwise, the deployed vm
     will failed to start up. The root disk's vdev can be configured with user_root_vdev
     option under zvm section in /etc/zvmsdk/zvmsdk.conf. The recommendation vdev of root
     disk is 0100, this is also the default value.

  d. The root disk should have a single partition

  e. z/VM Cloud Connector only support deploy an image to a disk larger or equal than
     the source image's root disk size , otherwise, it would result in loss of data.
     The image's root disk size can be got by command.

    .. code-block:: text

        hexdump -C -n 64 <image_path>

Make a Deployable Image for z/VM Cloud Connector
================================================

Install Linux on z Systems(zLinux) in a Virtual Machine
-------------------------------------------------------

1. Prepare a Linux on z Systems virtual server in the z/VM system. You will
   have to make adjustments to the procedures that are documented in the below cook 
   book in order to keep the resulting virtual server within the bounds of the above
   image requirements.

- For RHEL6.4 and SLES 11 SP3 installation, see http://www.vm.ibm.com/pubs/redbooks/sg248147/files/24814700.pdf
- For RHEL 7 installation, see http://www.redbooks.ibm.com/abstracts/sg248303.html?Open
- For SLES 12 installation, see http://www.redbooks.ibm.com/abstracts/sg248890.html?Open
- For Ubuntu 16.04 installation, see http://www.redbooks.ibm.com/redbooks/pdfs/sg248354.pdf

2. Install the mkisofs and openssl modules on it.

3. Make sure SELinux is disabled and the SSH connection (default port number is 22)
   can pass the firewall.

4. Set UseDNS no in /etc/ssh/sshd_config file in order to improve the inventory
   collection efficiency.

5. For Ubuntu 16.04, you must enable root ssh access. By default, root ssh access
   is not enabled.

Installation and Configuration of IUCV service in zLinux
--------------------------------------------------------

z/VM Cloud Connector manages the deployed VM via IUCV channel. IUCV service
should be configured on zLinux before capture it to make image. Following the below
steps to install and configure IUCV service.

1. Logon your BYOL(Bring Your Own Linux, which will be used to represent the Linux
   on which the z/VM Cloud Connector will be run), and copy the following files
   to target VM

   .. code-block:: text

       scp -r /opt/zthin/bin/IUCV/ root@<zLinux_ip>:/root/

   Where: <zLinux_ip> is the ip address of zLinux

2. Logon zLinux, install and configure IUCV service by commands:

   .. code-block:: text

       cd /root/IUCV
       ./iucvserverdaemoninstaller.sh -a <auth_userid>

   Where: auth_userid is the userid of the BYOL that can talk to zLinux via
   IUCV channel, case insensitive, for example:

   .. code-block:: text

       ./iucvserverdaemoninstaller.sh -a OPNCLOUD
       Setting the authorized client userid to be: OPNCLOUD
       IUCV server daemon is configured and started successfully

   you may get the detail usage of iucvserverdaemoninstaller.sh by command:

   .. code-block:: text

       ./iucvserverdaemoninstaller.sh -h

3. Logon your BYOL, run a simple command to check the if the iucv 
   channel is set up correctly by commands:

   .. code-block:: text

       /opt/zthin/bin/IUCV/iucvclnt <zLinux_userid> date

   Where: <zLinux_userid> is the userid of zLinux.

If above commands execute successfully, you may continue to next steps.
Otherwise, stop here and re-check the configuration.


Configuration of activation engine(AE) in zLinux
------------------------------------------------
To do useful work with the user data, the zLinux image must be configured to
run a service that retrieves the user data passed from the z/VM Cloud Connector
and then takes some actions based on the contents of that data. This service is
also known as an activation engine (AE).

For zLinux images that deployed by z/VM Cloud Connector, zvmguestconfigure must
be installed and started as the pre-AE before any other underlying AE.
Customers can choose their own underlying AE, such as cloud-init, according to
their requirements. In this document,we use cloud-init as an example when showing
how to configure an image. These steps of configuration zvmguestconfigure and
cloud-init are described in subsequent sections.

Configuration of zvmguestconfigure in zLinux
--------------------------------------------
The zvmguestconfigure script/service must be installed in the zLinux so it
can process the request files transmitted by z/VM Cloud Connector to the
reader of the zLinux as a class X file. zvmguestconfigure also act as the bridge
between the zLinux and higher layer of zVM Cloud. Take spawning a VM via Openstack
nova-zvm-driver for example, the image use cloud-init as the underlying AE.
If customer spawn a new VM with some customized data to initialize
the VM via nova boot command. The overall work flow of the customized data is
listed as below:

1. Openstack nova-zvm-driver generate the cfgdrive.iso file which is iso9660 format
   and with label 'config-2', this file is used to customize the target VM

2. nova-zvm-driver then call z/VM Cloud Connector to punch the cfgdrive.iso file to
   target VM's reader

3. When target VM start up, the installed zvmguestconfigure will download cfgdrive.iso
   file and then mount it as loop device

4. When cloud-init run, it will automatically find the proper configure drive data source
   via command ``blkid -t TYPE=iso9660 -o device``, then consume the data provided
   by cfgdrive.iso to customize the VM

The z/VM Cloud Connector supports initiating changes to zLinux while it is shut
down or the virtual machine is logged off.The changes to zLinux are implemented
using zvmguestconfigure that is run when Linux is booted the next time. The steps
of how to install zvmguestconfigure is described in subsequence sections.

Configuration of zvmguestconfigure on RHEL6.x and SLES11.x
..........................................................

Perform the following steps:

1. Log on your BYOL, and copy the zvmguestconfigure script that is located at
   <zvmsdk_path>/python-zvm-sdk/tools/share/zvmguestconfigure to your
   zLinux, where zvmsdk_path can be found at section z/VM SDK install

2. Logon on your zLinux, change the script to specify the authorizedSenders in 
   zvmguestconfigure file. It is recommended that this be set to a list of user IDs
   which are allowed to transmit changes to the machine. At a minimum, this list
   should include the userid of BYOL, which is usually OPNCLOUD. (It can be set
   to '*', which indicates any virtual machine on the same LPAR may
   send configuration requests to it)

3. zvmguestconfigure is configured to run with run level 2, 3 and 5. It is not
   configured to run as part of custom run level 4. If that run level is going to
   be used, then the # Default-Start: line at the beginning of the file should be
   updated to specify run level 4 in addition to the current run levels.

4. Copy the zvmguestconfigure file to /etc/init.d and make it executable

5. Add the zvmguestconfigure as a service by issuing:

   .. code-block:: text

       chkconfig --add zvmguestconfigure

6. Activate the script by issuing:

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

8. Verify that zvmguestconfigure on the target machine is configured to handle
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

1. Log on your BYOL, and copy the zvmguestconfigure and zvmguestconfigure.service
   script that are located at <zvmsdk_path>/python-zvm-sdk/tools/share/ folder
   to your zLinux, where zvmsdk_path can be found at the section z/VM SDK install.

2. Logon on your zLinux, change the script to specify the authorizedSenders in 
   zvmguestconfigure file. It is recommended that this be set to a list of user IDs
   which are allowed to transmit changes to the machine. At a minimum, this list
   should include the userid of BYOL, which is usually OPNCLOUD. (It can be set
   to '*', which indicates any virtual machine on the same LPAR may send configuration requests to it).

3. Copy the zvmguestconfigure script to the /usr/bin/ folder and make it executable.

4. Install the zvmguestconfigure.service in the target zLinux:

- If the target Linux machine is RHEL7.x, copy the zvmguestconfigureconf4z.service file to: /lib/systemd/system

- If the target Linux machine is SLES12.x, copy the zvmguestconfigure.service file to: /usr/lib/systemd/system
  and it is recommended that you change the NetworkManager.service to be wicked.service in the zvmguestconfigure.service

5. Enable the zvmguestconfigure service by issuing:

   .. code-block:: text

       systemctl enable zvmguestconfigure.service

6. Start the zvmguestconfigure service by issuing:

   .. code-block:: text

       systemctl start zvmguestconfigure.service

Configuration of zvmguestconfigure on Ubuntu 16.04
..................................................

1. Logon your BYOL, and copy the zvmguestconfigure and zvmguestconfigure.service
   script that are located at <zvmsdk_path>/python-zvm-sdk/tools/share/zvmguestconfigure 
   to your zLinux, where zvmsdk_path can be found at the section z/VM SDK install

2. Logon your zLinux, change the script to specify the authorizedSenders in 
   zvmguestconfigure file. It is recommended that this be set to a list of user IDs
   which are allowed to transmit changes to the machine. At a minimum, this list
   should include the userid of BYOL. (It can be set to '*', which indicates any
   virtual machine on the same LPAR may send configuration requests to it)

3. On zLinux, copy the zvmguestconfigure script to the /usr/bin/ folder and make
   it executable.

4. Install the zvmguestconfigure.service in the target Ubuntu machine, tailor the
   zvmguestconfigure.service file for an Ubuntu 16.04 image by modifying the file 
   contents as follows:

   .. code-block:: text

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

5. Enable the zvmguestconfigure service by issuing:

   .. code-block:: text

       systemctl enable zvmguestconfigure.service

6. Start the zvmguestconfigure service by issuing:

   .. code-block:: text

       systemctl start zvmguestconfigure.service

Installation and Configuration of cloud-init
--------------------------------------------

Please note that if customer won't pass customize data via openstack configdrive,
cloud-init will not need to be installed. In this case, the steps in this section
can be ignored.

OpenStack uses cloud-init as its activation engine.Some distributions include
cloud-init either already installed or available to be installed.
If your distribution does not include cloud-init, you can download the code
from https://launchpad.net/cloud-init/+download. After
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
specification of the indicated commands accordingly.During cloud-init
installation, some dependency packages may be required. You can use yum/zypper
and python setuptools to easily resolve these dependencies.
See https://pypi.python.org/pypi/setuptools for more information.

Installation and Configuration of cloud-init on RHEL 6.x
........................................................

1. Download the cloud-init tar file from Init scripts for use on cloud images
   https://launchpad.net/cloud-init/+download

2. Using the file cloud-init-0.7.5 as an example,
   untar this file by issuing the following command:

   .. code-block:: text

       tar -zxvf cloud-init-0.7.5.tar.gz

3. Issue the following to install cloud-init:

   .. code-block:: text

       cd ./cloud-init-0.7.5
       python setup.py build
       python setup.py install
       cp ./sysvinit/redhat/* /etc/init.d

4. Update /etc/init.d/cloud-init-local to ensure that it starts after the
   zvmguestconfigure and sshd services. On RHEL 6, change the # Required-Start
   line in the ### BEGIN INIT INFO section from:

   .. code-block:: text

       ### BEGIN INIT INFO
       # Provides: cloud-init-local
       # Required-Start: $local_fs $remote_fs
       # Should-Start: $time
       # Required-Stop:

   to:

   .. code-block:: text

        ### BEGIN INIT INFO
        # Provides: cloud-init-local
        # Required-Start: $local_fs $remote_fs zvmguestconfigure sshd
        # Should-Start: $time
        # Required-Stop:

5. The default configuration file /etc/cloud/cloud.cfg is for ubuntu, not RHEL.
   To tailor it for RHEL:

  a. Replace distro:ubuntu with distro:rhel at around line 79.

  b. Change the default user name, password and gecos as you wish, at around lines 82 to 84

  c. Change the groups tag to remove user groups that are not available for this distribution.
     After the change, the groups tag at around line 85 should appear similar to the following:
     groups: [adm, audio, cdrom, dialout, floppy, video, dip]

   For more information on how to configure cloud-init, please check the cloud-init documentation
   http://cloudinit.readthedocs.org/.

6. Cloud-init will try to add user syslog to group adm. This needs to be
   changed. RHEL does not have a syslog user by default, so issue:

   .. code-block:: text

       useradd syslog

7. Add the cloud-init related service with the following commands:

   .. code-block:: text

       chkconfig --add cloud-init-local
       chkconfig --add cloud-init
       chkconfig --add cloud-config
       chkconfig --add cloud-final

8. Then start them with the following sequence:

   .. code-block:: text

       chkconfig cloud-init-local on
       chkconfig cloud-init on
       chkconfig cloud-config on
       chkconfig cloud-final on

   You can issue ls -l /etc/rc5.d/ | grep -e xcat -e cloud to find the services.
   (Make sure that zvmguestconfigure starts before any cloud-init service.)

   .. code-block:: text

       lrwxrwxrwx. 1 root root 22 Jun 13 04:39 S50xcatconfinit -> ../init.d/zvmguestconfigure
       lrwxrwxrwx. 1 root root 26 Jun 13 04:39 S51cloud-init-local -> ../init.d/cloud-init-local
       lrwxrwxrwx. 1 root root 20 Jun 13 04:39 S52cloud-init -> ../init.d/cloud-init
       lrwxrwxrwx. 1 root root 22 Jun 13 04:39 S53cloud-config -> ../init.d/cloud-config
       lrwxrwxrwx. 1 root root 21 Jun 13 04:39 S54cloud-final -> ../init.d/cloud-final

9. To verify cloud-init configuration, issue: cloud-init init --local

   .. code-block:: text

       cloud-init init --local

   Make sure that no errors occur. The following warning messages can be ignored:

   /usr/lib/python2.6/site-packages/Cheetah-2.4.4-py2.6.egg/Cheetah/Compiler.py:1509: UserWarning:
   You don’t have the C version of NameMapper installed! I’m disabling Cheetah’s useStackFrames
   option as it is painfully slow with the Python version of NameMapper. You should get a copy
   of Cheetah with the compiled C version of NameMapper. You don’t have the C version of NameMapper installed!

10. Issue following command, if this file exists, or cloud-init will not work after reboot.

    .. code-block:: text

        rm -rf /var/lib/cloud 

Installation and Configuration of cloud-init on SLES11.x
........................................................

1. Download the cloud-init tar file from https://launchpad.net/cloud-init/+download.

2. Using the file cloud-init-0.7.5 as an example, untar this file by issuing
   the following command:

   .. code-block:: text

       tar -zxvf cloud-init-0.7.5.tar.gz


3. Issue the following commands to install cloud-init:

   .. code-block:: text

       cd ./cloud-init-0.7.5
       python setup.py build
       python setup.py install

   **NOTE:**: After you issue the command tar -zxvf cloud-init-0.7.5.tar.gz,
   the directory ./sysvinit/sles/ does not exist. So you have to copy the
   cloud-init related services from ./sysvinit/redhat/* to /etc/init.d/:

   .. code-block:: text

       cp ./sysvinit/redhat/* /etc/init.d

   You will find that four scripts, cloud-init-local, cloud-init, cloud-config,
   and cloud-final are added to /etc/init.d/. Modify each of them by replacing
   the variable:

   .. code-block:: text

       cloud_init="/usr/bin/cloud-init"

   with:

   .. code-block:: text

       cloud_init="/usr/local/bin/cloud-init"

4. Update /etc/init.d/cloud-init-local to ensure that it starts after the
   zvmguestconfigure service. On SLES, change the # Required-Start line in the 
   ### BEGIN INIT INFO section from:

   .. code-block:: text

       ### BEGIN INIT INFO
       # Provides: cloud-init-local
       # Required-Start: $local_fs $remote_fs
       # Should-Start: $time
       # Required-Stop:

   to:

   .. code-block:: text

       ### BEGIN INIT INFO
       # Provides: cloud-init-local
       # Required-Start: $local_fs $remote_fs zvmguestconfigure
       # Should-Start: $time
       # Required-Stop:

5. The default configuration file /etc/cloud/cloud.cfg is for ubuntu, not SLES. To tailor it for SLES:

  a. Replace distro:ubuntu with distro:sles at around line 79.

  b. Change the default user name, password and gecos as you wish, at around lines 82 to 84.

  c. Change the groups at around line 85: groups: [adm, audio, cdrom, dialout, floppy, video, dip]

  d. Cloud-init will try to add user syslog to group adm. This needs to be changed. For SLES, issue the following commands:

     .. code-block:: text

         useradd syslog
         groupadd adm

  For more information on changing these values, see the cloud-init documentation http://cloudinit.readthedocs.org/ 

6. Start the cloud-init related services with the following commands, 
   ignoring the error “insserv: Service network is missed in the runlevels 4
   to use service cloud-init” if it occurs:

   .. code-block:: text

       insserv cloud-init-local
       insserv cloud-init
       insserv cloud-config
       insserv cloud-final

   At this point, you should find that the services in /etc/init.d/rcX.d appear as
   you would expect (make sure that zvmguestconfigure starts before any cloud-init service):

   .. code-block:: text

       lrwxrwxrwx. 1 root root 22 Jun 13 04:39 S50xcatconfinit -> ../init.d/zvmguestconfigure
       lrwxrwxrwx. 1 root root 26 Jun 13 04:39 S51cloud-init-local -> ../init.d/cloud-init-local
       lrwxrwxrwx. 1 root root 20 Jun 13 04:39 S52cloud-init -> ../init.d/cloud-init
       lrwxrwxrwx. 1 root root 22 Jun 13 04:39 S53cloud-config -> ../init.d/cloud-config
       lrwxrwxrwx. 1 root root 21 Jun 13 04:39 S54cloud-final -> ../init.d/cloud-final

7. To verify cloud-init configuration, issue:

   .. code-block:: text

       cloud-init init --local

   Make sure that no errors occur. The following warning messages can be ignored:
   /usr/lib/python2.6/site-packages/Cheetah-2.4.4-py2.6.egg/Cheetah/Compiler.py:1509:
   UserWarning:
   You don’t have the C version of NameMapper installed! I’m disabling Cheetah’s useStackFrames
   option as it is painfully slow with the Python version of NameMapper. You should get a copy
   of Cheetah with the compiled C version of NameMapper.
   You don’t have the C version of NameMapper installed!

8. Issue following command, if this file exists, or cloud-init will not work after reboot.

   .. code-block:: text

       rm -rf /var/lib/cloud 

Installation and Configuration of cloud-init on RHEL 7.x and SLES 12.x
......................................................................

1. Download cloud-init0.7.6 from https://launchpad.net/cloud-init/+download.

2. Untar it with this command:

   .. code-block:: text

       tar -zxvf cloud-init-0.7.6.tar.gz

3. Issue the following commands to install cloud-init:

   .. code-block:: text

        cd ./cloud-init-0.7.6
        python setup.py build
        python setup.py install --init-system systemd

4. OpenStack on z/VM uses ConfigDrive as the data source during the installation
   process. You must add the following lines to the default
   configuration file, /etc/cloud/cloud.cfg:

   .. code-block:: text

       # Example datasource config
       # datasource:
       #   Ec2:
       #
       # metadata_urls: [ ’blah.com’ ]
       #
       # timeout: 5 # (defaults to 50 seconds) 
       #
       #     max_wait: 10 # (defaults to 120 seconds)
       datasource_list: [ ConfigDrive, None ]
       datasource:
         ConfigDrive:
           dsmode: local

   **NOTE:** please pay attention to the indentation, otherwise, cloud-init may not
   work as expected.

5. In order to work well with other products, the service start up sequence
   for cloud-init-local and cloud-init should be changed to the following.
   (The cloud-init related service files are located in the folder
   /lib/systemd/system/ for RHEL7.x and in /usr/lib/systemd/system/ for SLES12.x)

   .. code-block:: text

     cat /lib/systemd/system/cloud-init-local.service
     [Unit]
     Description=Initial cloud-init job (pre-networking)
     Wants=local-fs.target sshd.service sshd-keygen.service
     After=local-fs.target sshd.service sshd-keygen.service
     [Service]
     Type=oneshot
     ExecStart=/usr/bin/cloud-init init --local
     RemainAfterExit=yes
     TimeoutSec=0
     # Output needs to appear in instance console output
     StandardOutput=journal+console
     [Install]
     WantedBy=multi-user.target

     # cat /lib/systemd/system/cloud-init.service
     [Unit]
     Description=Initial cloud-init job (metadata service crawler)
     After=local-fs.target network.target cloud-init-local.service
     Requires=network.target
     Wants=local-fs.target cloud-init-local.service
     [Service]
     Type=oneshot
     ExecStart=/usr/bin/cloud-init init
     RemainAfterExit=yes
     TimeoutSec=0
     # Output needs to appear in instance console output
     StandardOutput=journal+console
     [Install]
     WantedBy=multi-user.target

6. Manually create the cloud-init-tmpfiles.conf file: 

   .. code-block:: text

        touch /etc/tmpfiles.d/cloud-init-tmpfiles.conf

   Insert comments into the file by issuing the following command:

   .. code-block:: text

       echo "d /run/cloud-init 0700 root root - -" > /etc/tmpfiles.d/cloud-init-tmpfiles.conf

7. Because RHEL does not have a syslog user by default, you have to add it manually: 

   .. code-block:: text

        useradd syslog

8. In /etc/cloud/cloud.cfg, remove the ubuntu-init-switch, growpart and
   resizefs modules from the cloud_init_modules section. Here is the
   cloud_init_modules section after the change:

   .. code-block:: text

         # The modules that run in the ’init’ stage
         cloud_init_modules:
          - migrator
          - seed_random
          - bootcmd
          - write-files
          - set_hostname
          - update_hostname
          - update_etc_hosts
          - ca-certs
          - rsyslog
          - users-groups
          - ssh

9. In /etc/cloud/cloud.cfg, remove the emit_upstart, ssh-import-id,
   grub-dpkg, apt-pipelining, apt-config, landscape, and byobu modues
   from the cloud_config section. Here is the cloud_config_modules section
   after the change:

   .. code-block:: text

     cloud_config_modules:
     # Emit the cloud config ready event
     # this can be used by upstart jobs for ’start on cloud-config’.
      - disk_setup
      - mounts
      - locale
      - set-passwords
      - package-update-upgrade-install
      - timezone
      - puppet
      - salt-minion
      - mcollective
      - disable-ec2-metadata
      - runcmd

10. The default /etc/cloud/cloud.cfg file is for ubuntu,
    and must be updated for RHEL and SLES. To tailor this file for RHEL and SLES:

  a. Change the disable_root: true line to: disable_root: false

  b. In the system_info section, replace distro:ubuntu with distro:rhel or distro:sles according to
     the distribution you will use.

  c. Change the default user name, password, and gecos under default_user configuration section as needed for your installation.

  d. Change the groups tag to remove the user groups that are not available on this distribution. When cloud-init starts up at first time, it will create the specified users and groups. The following is a sample configuration for SLES:

  .. code-block:: text

      system_info:
      # This will affect which distro class gets used
      distro: sles
       # Default user name + that default user’s groups (if added/used)
      default_user:
       name: sles
       lock_passwd: false
       plain_text_passwd: ’sles’
       gecos: sles12user
       groups: users
       sudo: ["ALL=(ALL) NOPASSWD:ALL"]
       shell: /bin/bash

  For more information on cloud-init configurations, see: http://cloudinit.readthedocs.org/en/latest/topics/examples.html

11. Enable and start the cloud-init related services by issuing the following commands:

    .. code-block:: text

        systemctl enable cloud-init-local.service
        systemctl start cloud-init-local.service
        systemctl enable cloud-init.service
        systemctl start cloud-init.service
        systemctl enable cloud-config.service
        systemctl start cloud-config.service
        systemctl enable cloud-final.service
        systemctl start cloud-final.service

   If you experience problems the first time you start cloud-config.service and
   cloud-final.service, try starting them again.

12. Ensure all cloud-init services are in active status by issuing the following commands:

    .. code-block:: text

        systemctl status cloud-init-local.service
        systemctl status cloud-init.service
        systemctl status cloud-config.service
        systemctl status cloud-final.service

13. Optionally, you can start the multipath service:

    .. code-block:: text

        systemctl enable multipathd
        systemctl start multipathd
        systemctl status multipathd

14. Remove the /var/lib/cloud directory (if it exists), so that cloud-init will
    not run after a reboot: 

    .. code-block:: text

        rm -rf /var/lib/cloud

Installation and Configuration of cloud-init on Ubuntu 16.04
............................................................

For Ubuntu 16.04, cloud-init0.7.8 or higher is required. The examples in this
section use cloud-init0.7.8.

1. Download cloud-init0.7.8 from https://launchpad.net/cloud-init/+download. 
   Untar it with this command:

   .. code-block:: text

       tar -zxvf cloud-init-0.7.8.tar.gz

2. Issue the following commands to install cloud-init:

   .. code-block:: text

       cd ./cloud-init-0.7.8
       python3 setup.py build
       python3 setup.py install --init-system systemd

   **NOTE:** You might have to install all the dependencies that cloud-init 
   requires according to your source z/VM environment. For example, you might
   have to install setuptools before installing cloud-init. For more information,
   see https://pypi.python.org/pypi/setuptools.

3. OpenStack on z/VM uses ConfigDrive as the data source during the
   installation process. You must add the following lines to the
   default configuration file, /etc/cloud/cloud.cfg:

   .. code-block:: text

       # Example datasource config
       # datasource:
       #   Ec2:
       #
       # metadata_urls: [ ’blah.com’ ]
       #
       # timeout: 5 # (defaults to 50 seconds) 
       #
       #     max_wait: 10 # (defaults to 120 seconds)
       datasource_list: [ ConfigDrive, None ]
       datasource:
         ConfigDrive:
           dsmode: local

   **NOTE:** please pay attention to the indentation, otherwise, cloud-init may not
   work as expected.

4. Enable root login by configuring the /etc/cloud/cloud.cfg file:

   .. code-block:: text

       disable_root: false

5. Optionally, you can tailor the modules that run during the cloud-config
   stage or the cloud-final stage by modifying cloud_config_modules or
   cloud_final_modules in /etc/cloud/cloud.cfg file.
   Enable and start the cloud-init related services by issuing the following commands:

   .. code-block:: text

      ln -s /usr/local/bin/cloud-init /usr/bin/cloud-init
      systemctl enable cloud-init-local.service
      systemctl start cloud-init-local.service
      systemctl enable cloud-init.service
      systemctl start cloud-init.service
      systemctl enable cloud-config.service
      systemctl start cloud-config.service
      systemctl enable cloud-final.service
      systemctl start cloud-final.service

6. Ensure all cloud-init services are in active status by issuing the following commands:

   .. code-block:: text

      systemctl status cloud-init-local.service
      systemctl status cloud-init.service
      systemctl status cloud-config.service
      systemctl status cloud-final.service

7. If you intend to use persistent disks, start the multipath service:

   .. code-block:: text

      systemctl enable multipathd
      systemctl start multipathd
      systemctl status multipathd

8. Remove the /var/lib/cloud directory (if it exists), so that cloud-init will
   not run after a reboot:

   .. code-block:: text

       rm -rf /var/lib/cloud

Capture the zLinux to Generate the Image
========================================

After zLinux is well configured for capture, shut down it and logoff the userid,
then perform the following steps to generate the image:

Logon your BYOL, type the command:

.. code-block:: text

    /opt/zthin/bin/creatediskimage <zLinux_userid> <vdev> <image_location>

Where:
<zLinux_userid> is the userid of the zLinux, 
<vdev> is the device number for capture, 
<image_location> is the image's store location


Import the Images to z/VM Cloud Connector
=========================================

If you want to import the image to z/VM Cloud Connector, you can use REST API.
Type the following command:

.. code-block:: text

    # curl http://1.2.3.4:8080/images -H "Content-Type:application/json" -H 'X-Auth-Token:<your token>' -X POST -d '{"image": {"url": "file:///var/lib/zvmsdk/images/0100", "image_meta": {"os_version": "rhel6.7"}, "image_name": "0100", "remote_host": "root@6.7.8.9"}}'
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": "", "errmsg": ""}

Please note that if the source image is located at same server as BYOL, there is no need
to specify the remote_host parameter in data field. And please refer to :ref:`TokenUsage` to get
your token to fill in the request area ``<your token>``.

Verify the import result by command:

.. code-block:: text

    # curl http://127.0.0.1:8080/images?imagename=0100 -X GET -H "Content-Type:application/json" -H 'X-Auth-Token:<your token>'
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": [{"image_size_in_bytes": "236435482", "disk_size_units": "1100:CYL", "md5sum": "26ddd19301d4f9c8a85e812412164bb8", "comments": null, "imagename": "0100", "imageosdistro": "rhel6.7", "type": "rootonly"}], "errmsg": ""}

During image import you may meet following error:

.. code-block:: text

    {u'rs': 10, u'overallRC': 300, u'modID': 40, u'rc': 300, u'output': u'', 'errmsg': u"Image import error:
    Copying image file from remote filesystem failed with error Warning: Permanently added '6.7.8.9' (ECDSA)
    to the list of known hosts.\r\nPermission denied, please try again.\r\nPermission denied, please try again.
    \r\nPermission denied (publickey,gssapi-keyex,gssapi-with-mic,password).\r\n"}

If similar error happens, you need to configure the ssh authentication between
your BYOL server and the server that source image located. You need to append the
public key of the owner that running sdkserver to the .ssh/authorized_keys file of
the user where your source image located. Please refer to :ref:`ssh_key` for reference.

