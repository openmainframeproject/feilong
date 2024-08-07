..
 Copyright Contributors to the Feilong Project.
 SPDX-License-Identifier: CC-BY-4.0

Quick Start
***********

This is the document that describes the installation, configuration,
and basic usages of Feilong.

Pre-requirements
================

1. Feilong depends on the under-layer z/VM SMAPI support to manage
the z/VM objects. For the Feilong to work normally, the managed z/VM
system should be updated to the latest level with APARs listed in the 
`z/VM service Information`_ installed.

.. _z/VM service Information: http://www.vm.ibm.com/sysman/osmntlvl.html

.. note::
   please make sure you applied http://www-01.ibm.com/support/docview.wss?uid=isg1VM66120
   if z/VM 6.4 is used.

2. Feilong has to be installed inside a Linux running on z/VM.
Currently supported distros include the most current supported versions:

  - SUSE Linux Enterprise Server 15.x
  - Red Hat Enterprise Linux 9.x
  - Ubuntu 24.04 LTS

  From now on, BYOL (Bring Your Own Linux) will be used to represent
  the Linux on which the Feilong will be run.

  For the Feilong to run, the BYOL must have enough free disk space (>100M).
  And besides that, the following updates need to be made to the BYOL.

Preparation on BYOL
-------------------

1. Authorize BYOL user for z/VM SMAPI call.

   VSMWORK1 AUTHLIST needs to be updated in order to make the BYOL
   machine be able to issue SMAPI call. Refer to `z/VM Systems Management
   Application Programming`_ for how to make it.

.. note::
   It is recommend to consider increase the SMAPI long call server and DIRMAINT
   DATAMOVE machine if heavy concurrent workload is going to be run through Feilong.
   See `z/VM Systems Management Application Programming`_ for how to make it.

2. Update BYOL definition for spawning guests.

   Assume BYOL has its definition on z/VM, it needs to have following statement in
   its User Directory in order to link disk during stage of spawning guests.

   .. code-block:: text

       OPTION LNKNOPAS

   If under RACF, RACF command need to be executed like below while the ``BYOL``
   is the name of the virtual machine which is going to run Feilong service.

   .. code-block:: text

       RAC PERMIT BYOL CLASS(VMRDR) ID(VSMWORK1) ACCESS(UPDATE)

.. note::
   Please note when under RACF (ESM of z/VM) is used, additional setup for SMAPI is needed
   to make the BYOL able to work.

   See `z/VM Systems Management Application Programming`_ for how to make it.

3. Update BYOL definition about IUCV

   Assume BYOL has its definition on z/VM, it needs to have following entry in
   its User Directory in order to communicate with the managed guests by the IUCV
   channel

   .. code-block:: text

       IUCV ANY

   See `z/VM Systems Management Application Programming`_ for how to make it.

.. _z/VM Systems Management Application Programming: https://www.ibm.com/support/knowledgecenter/SSB27U_6.4.0/com.ibm.zvm.v640.dmse6/toc.htm

4. Enable reader device

   In order to get console output of target vm, BYOL's reader device needs to
   be enabled to receive console output spool files send from target vm

   Use the following command on BYOL itself to achieve that:

   .. code-block:: text

       [root@xxxx ~]# cio_ignore -r 000c
       [root@xxxx ~]# chccwdev -e 000c
       Setting device 0.0.000c online
       Done

   If something like 'is already  online' is returned, it means reader already
   online and feel free to ignore the warning.

5. Enable punch device

   In order to spawn guest, BYOL needs to be able to punch files to spawned
   guests' reader, so the punch device on BYOL needs to be enabled.

   Use the following command on BYOL itself to achieve that:

   .. code-block:: text

       [root@xxxx ~]# cio_ignore -r 000d
       [root@xxxx ~]# chccwdev -e 000d
       Setting device 0.0.000d online
       Done

   If something like 'is already  online' is returned, it means punch already
   online and feel free to ignore the warning.

.. note::
   Preparation step 2 and step 3 require to logoff then re-logon the
   BYOL to make the updates become effective.

Installation Requirements
-------------------------

The supported Python version includes:

- Python 2.7
- Python 3+

Installation using OBS Packages
===============================

The Open Build Service (OBS) is a generic system to build and distribute binary packages from sources in an automatic, consistent and reproducible way.
OBS builds and provides an installable version of the zthin and zvmsdk packages for each of the distributions (RHEL, SLES, Ubuntu).

RPM for RHEL/Alma/Rocky
-----------------------

SSH onto the BYOL as root user, and then follow the following steps:

1. Add the feilong AlmaLinux repository from OBS

    .. code-block:: text

        # dnf config-manager --add-repo=https://download.opensuse.org/repositories/Virtualization:/feilong/AlmaLinux_9/

2. Disable gpgkeycheck flag

    Add the flag `gpgkeycheck=0`to the /etc/yum.repos.d/download.opensuse.org_repositories_Virtualization_feilong_AlmaLinux_9_.repo file.

3. Disable SELinux

    Update the config file `/etc/selinux/config` and set `SELINUX=disabled`. 
    Make sure you reboot to ensure the changes are reflected and SELinux is disabled.
    We are considering writing SELinux policies for Feilong that would enable to not disable SELinux as a whole.

4. Install the Extra Packages for Enterprise Linux.

    Packages in EPEL are dependencies for the feilong packages installation.
    Make sure you add both the EPEL and the EPEL-Next repos.

5. Install the zthin and zvmsdk packages
    
    .. code-block:: text

        # dnf install zthin zvmsdk

6. Skip to the SSH key authentication between consumer and BYOL section to continue.

RPM for SLES
------------

SSH onto the BYOL as root user, and then follow the following steps:

1. Register to the SUSE Package Hub using SUSEConnect and refresh the available repos list.

    Packages in the PackageHub are dependencies for the feilong package installation

    .. code-block:: text

        # SUSEConnect --product PackageHub/15.5/s390x

2. Add the feilong SUSE repository from OBS

    .. code-block:: text
        
        # zypper ar https://download.opensuse.org/repositories/Virtualization:/feilong/SLE_15_SP5/ feilong
        # zypper refresh

3. Disable SELinux
   
   Make sure SELinux is set to disabled mode.
   We are considering writing SELinux policies for Feilong that would enable to not disable SELinux as a whole.

4. Install the zthin and zvmsdk packages
    
    .. code-block:: text

        # zypper in zthin zvmsdk

6. Skip to the SSH key authentication between consumer and BYOL section to continue.

Debian for Ubuntu
-----------------

(to be continued)


Manual Installation
===================

z/VM zthin install
------------------

zthin is a library written in C that works as part of the Feilong.
It mainly focuses on socket connection from BYOL to z/VM SMAPI(System Management API).
Feilong requires zthin as the backend to communicate with z/VM SMAPI,
thus it needs to be installed before installing Feilong.

SSH onto the BYOL as root user, and then follow the following steps:

1. Clone build project from github

   .. code-block:: text

       # git clone https://github.com/mfcloud/build-zvmsdk.git

2. Trigger the build tool

   The build tool depends on the following commands: *rpmbuild*, *gcc*, so you should make
   sure these commands are usable on BYOL before running the following build.

   .. code-block:: text

       # cd build-zvmsdk
       # /usr/bin/bash buildzthinrpm_rhel master

   If this build finishes successfully, the result rpm will be generated
   in the /root/zthin-build/RPMS/s390x/ directory named in the format
   *zthin-version-snapdate.s390x.rpm* where *version* is the zthin version
   number and *date* is the build date.

3. Install the rpm generated in last step

   .. code-block:: text

       # rpm -ivh /root/zthin-build/RPMS/s390x/zthin-3.1.0-snap201710300123.s390x.rpm

   Be sure to replace the *zthin-3.1.0-snap201710300123.s390x.rpm* with your own
   rpm name.

4. Verify zthin can work

   .. code-block:: text

       # /opt/zthin/bin/smcli Image_Query_DM -T opncloud

   If all things went well, this smcli command should be
   able to return the directory entry of user OPNCLOUD.

   If this command failed, you need to check the following items:

   * The BYOL user is successfully authorized to issue SMAPI call.
   * The SMAPI server on this z/VM host is working normally.
   * The zthin rpm is installed without any error.

5. Optionally, Consider to add ``/opt/zthin/bin/`` into $PATH so you can use ``smcli`` command directly.

z/VM SDK install
----------------

z/VM SDK is the upper transition layer of Feilong. It implements the
supported SDK APIs by communicating with the zthin backend.

   * Clone python-zvm-sdk project from github

     .. code-block:: text

         # git clone https://github.com/openmainframeproject/python-zvm-sdk.git

     (If this has been done in the "z/VM zthin install" step, this step can be
     obsoleted.)

   * Install z/VM sdk

     Please ensure to update your setuptools to the latest version before doing this step,
     the following installation step would rely on it to automatically install the depended
     python packages.

     .. code-block:: text

         # cd python-zvm-sdk
         # python ./setup.py install

Upgrade z/VM SDK
----------------

If the z/VM SDK was installed via ``python setup.py install``, you can fetch and
checkout to new version, then upgrade it by issue ``python setup.py install`` again.

.. note::
   If upgrade from version equal or lower than 1.6.2, to **1.6.3** or newer version,
   you have to add two new columns - **wwpn_npiv** and **wwpn_phy** into fcp table in
   sdk_fcp database with type **`varchar(16)`**, which located at
   ``/var/lib/zvmsdk/databases/sdk_fcp.sqlite``, for example, by sqlite3 command:
   ``ALTER TABLE fcp ADD COLUMN wwpn_npiv varchar(16)`` and
   ``ALTER TABLE fcp ADD COLUMN wwpn_phy varchar(16)``

.. _`ssh_key`:

SSH key authentication between consumer and BYOL server
-------------------------------------------------------

For image import/export function, BYOL's running user(eg zvmsdk) needs to
authorized by the user of the consumer (eg nova-compute) if they are not in
same host. For example, if you want to import/export image from/to nova
compute server，please make ensure you can ssh nova@nova-compute-ip without
password from zvmsdk user on BYOL server. Refer to the following steps to
configure it:

Logon to the nova-compute server and change the nova user’s right to be
able to log in, and make sure port 22 is open.

.. code-block:: text

    ssh root@nova-compute-ip
    usermod -s /bin/bash nova

where:
nova-compute-ip: is the IP address of the nova compute node.

Change to nova user and inject the zvmsdk server's public key into it.

.. code-block:: text

    su - nova
    scp zvmsdk@zvmsdk-ip:/var/lib/zvmsdk/.ssh/id_rsa.pub $HOME mkdir -p $HOME/.ssh
    mv $HOME/id_rsa.pub $HOME/.ssh/authorized_keys

where:
zvmsdk: is running user of the BYOL server.
zvmsdk-ip: is the IP address of the BYOL server
Note: If the $HOME/.ssh/authorized_keys file already exists,
you just need to append the BYOL’s public key to it.

Ensure that the file mode under the $HOME/.ssh folder is 644.

.. code-block:: text

    chmod -R 644 $HOME/.ssh/*

Issue the following command to determine if SELinux is enabled on the system.

.. code-block:: text

    getenforce

If SELinux is enabled then set SELinux contexts on the nova home directory.

.. code-block:: text

    su -
    chcon -R -t ssh_home_t nova_home

where:
nova_home：is the home directory for the nova user on the nova compute server.
You can obtain nova_home by issuing: echo ~nova

**NOTE:** If the host key of nova-compute server changed, please run
the following command on zvmsdk server to clean the cached host key of
nova-compute server from zvmsdk server's known_hosts file

.. code-block:: text

    ssh-keygen -R nova-compute-ip

Configuration Sample
====================

After z/VM SDK is installed, a file named 'zvmsdk.conf.sample' is generated
under the /etc/zvmsdk/ folder. It contains all the supported configurations
for z/VM SDK. You can refer to it to create your own configuration file which
should be named as zvmsdk.conf.

Here's a sample configuration in which several options marked as 'required'
should be customized according to your environment.

.. code-block:: text

    [database]
    dir=/var/lib/zvmsdk/databases/

    [image]
    sdk_image_repository=/var/lib/zvmsdk/images

    [logging]
    log_level=INFO
    log_dir=/var/log/zvmsdk/

    [network]
    # IP address of the Linux machine which is running SDK on.
    # This config option is required
    my_ip=127.0.0.1

    [sdkserver]
    bind_addr=127.0.0.1
    bind_port=2000
    max_worker_count=64

    [wsgi]
    auth=none

    [zvm]
    # zVM disk pool and type for root/ephemeral disks.
    # This config option is required
    disk_pool=ECKD:eckdpool

    # PROFILE name to use when creating a z/VM guest.
    # This config option is required
    user_profile=osdflt

    # The default maximum number of virtual processers the user can define.
    user_default_max_cpu=32

    # The default maximum size of memory the user can define.
    user_default_max_memory=64G

For the details of all configuration options, please refer to
:ref:`configuration options`.

Setup for z/VM SDK Daemon
=========================

The Feilong is designed to be run inside a daemon. The daemon server is bond to
the configured socket for receiving requests and then call the requested SDK API.

The daemon server would be run with user 'zvmsdk' and group 'zvmsdk', the following user and folder
setup should be made on BYOL for the z/VM SDK daemon to run.

* Create 'zvmsdk' user and group

  .. code-block:: text

      # useradd -d /var/lib/zvmsdk/ -m -U -p PASSWORD zvmsdk

  Replace the *PASSWORD* with your own password for the new created user.

* Configure sudo access for 'zvmsdk' user (optional)

  If Feilong is installed from source code ``python setup.py install`` or from package install
  such as deb or rpm, then you can skip this step as it's already done during install stage.

  The z/VM SDK Daemon relies on some privileged commands for the management of the z/VM host, so you
  need to grant the 'zvmsdk' user to run following commands with sudo without password:

  * /usr/sbin/vmcp
  * /opt/zthin/bin/smcli
  * /usr/sbin/chccwdev
  * /usr/sbin/cio_ignore
  * /usr/sbin/fdasd
  * /usr/sbin/fdisk
  * /usr/sbin/vmur
  * /usr/bin/mount
  * /usr/bin/umount
  * /usr/sbin/mkfs
  * /usr/sbin/mkfs.xfs
  * /usr/sbin/dasdfmt
  * /opt/zthin/bin/unpackdiskimage
  * /opt/zthin/bin/creatediskimage
  * /opt/zthin/bin/linkdiskandbringonline
  * /opt/zthin/bin/offlinediskanddetach

  A sample is given in the following block, copy the content to /etc/sudoers.d/zvmsdk:

  .. code-block:: text

      # cat /etc/sudoers.d/zvmsdk
      zvmsdk ALL = (ALL) NOPASSWD:/usr/sbin/vmcp, /opt/zthin/bin/smcli, /usr/sbin/chccwdev, /usr/sbin/cio_ignore, /usr/sbin/fdasd, /usr/sbin/fdisk, /usr/sbin/vmur, /usr/bin/mount, /usr/bin/umount, /usr/sbin/mkfs, /usr/sbin/mkfs.xfs, /usr/sbin/dasdfmt, /opt/zthin/bin/unpackdiskimage, /opt/zthin/bin/creatediskimage, /opt/zthin/bin/linkdiskandbringonline, /opt/zthin/bin/offlinediskanddetach

* Setup home directory

  .. code-block:: text

      # mkdir -p /var/lib/zvmsdk
      # chown -R zvmsdk:zvmsdk /var/lib/zvmsdk
      # chmod -R 755 /var/lib/zvmsdk

* Setup log directory

  The folder to which the z/VM SDK log would be written to can be configured with the 'log_dir'
  option in 'default' section. By default, the log folder is '/var/log/zvmsdk'. If you have customized
  the 'log_dir' value, you need to change the folder in following commands accordingly.

  .. code-block:: text

      # mkdir -p /var/log/zvmsdk
      # chown -R zvmsdk:zvmsdk /var/log/zvmsdk
      # chmod -R 755 /var/log/zvmsdk

* Setup configuration directory

  .. code-block:: text

      # mkdir -p /etc/zvmsdk
      # chown -R zvmsdk:zvmsdk /etc/zvmsdk
      # chmod -R 755 /etc/zvmsdk
      # ls -l /etc/zvmsdk

  A file named zvmsdk.conf should be found under /etc/zvmsdk folder and contains at least all the required
  options before the z/VM SDK daemon can be started.

Start z/VM SDK Daemon
=====================

Configure the sdkserver service to start automatically at boot by command:
.. code-block:: text

    # systemctl enable sdkserver

The z/VM SDK Daemon can be started via the following command:

.. code-block:: text

    # systemctl start sdkserver

And make sure the sdkserver service status is 'active (running)' as following:

.. code-block:: text

    # systemctl status sdkserver
    ● sdkserver.service - zVM SDK API server
       Loaded: loaded (/usr/lib/systemd/system/sdkserver.service; disabled; vendor preset: disabled)
       Active: active (running) since Mon 2017-11-20 00:47:18 EST; 3s ago
     Main PID: 5779 (sdkserver)
       CGroup: /system.slice/sdkserver.service
               └─5779 /usr/bin/python /usr/bin/sdkserver

    Nov 20 00:47:18 0822rhel7 systemd[1]: Started zVM SDK API server.
    Nov 20 00:47:18 0822rhel7 systemd[1]: Starting zVM SDK API server...
    Nov 20 00:47:18 0822rhel7 sdkserver[5779]: INFO: [MainThread] SDK server now listening

Verification
============

You can verify that the process is listenning on the configured port.
For example:

.. code-block:: text

    # netstat -anp | grep 2000
    tcp        0      0 127.0.0.1:2000          0.0.0.0:*               LISTEN      56434/python
