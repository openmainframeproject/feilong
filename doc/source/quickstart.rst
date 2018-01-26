
Quick Start
***********

This is the document that describes the installation, configuration,
and basic usages of z/VM Cloud Connector.

Pre-requirements
================

z/VM Cloud Connector has to be installed inside a Linux running on z/VM.
Currently planned to be supported distros include the most current
supported versions:

- SUSE Linux Enterprise Server
- Red Hat Enterprise Linux
- Ubuntu 16.04 LTS

**NOTE**: This guide is based on RHEL 7.2, you may need to adjust the commands
on other Linux distros.

From now on, BYOL (Bring Your Own Linux) will be used to represent
the Linux on which the z/VM Cloud Connector will be run.

For the z/VM Cloud Connector to run, the BYOL must have enough free disk space (>100M).
And besides that, the following updates need to be made to the BYOL.

Preparation on BYOL
-------------------

1. Authorize BYOL user for z/VM SMAPI call.

   VSMWORK1 AUTHLIST needs to be updated in order to make the BYOL
   machine be able to issue SMAPI call. Refer to `z/VM Systems Management
   Application Programming`_ for how to make it.

.. note::
   It is recommend to consider increase the SMAPI long call server and DIRMAINT
   DATAMOVE machine if heavy concurrent workload is going to be run through z/VM
   Cloud connector. See `z/VM Systems Management Application Programming`_ for how to make it.

2. Update BYOL definition for spawning guests.

   Assume BYOL has its definition on z/VM, it needs to have following statement in
   its User Directory in order to link disk during stage of spawning guests.

   .. code-block:: text

       OPTION LNKNOPAS

   See `z/VM Systems Management Application Programming`_ for how to make it.

3. Update BYOL definition about IUCV

   Assume BYOL has its definition on z/VM, it needs to have following entry in
   its User Directory in order to communicate with the managed guests by the IUCV
   channel

   .. code-block:: text

       IUCV ANY

   See `z/VM Systems Management Application Programming`_ for how to make it.

.. _z/VM Systems Management Application Programming: https://www.ibm.com/support/knowledgecenter/SSB27U_6.4.0/com.ibm.zvm.v640.dmse6/toc.htm

4. Enable punch device

   In order to spawn guest, BYOL needs to be able to punch files to spawned
   guests' reader, so the punch device on BYOL needs to be enabled.

   Use the following command on BYOL itself to achieve that:

   .. code-block:: text

       [root@xxxx ~]# cio_ignore -r d
       [root@xxxx ~]# chccwdev -e d
       Setting device 0.0.000d online
       Done

   If something like 'is already  online' is returned, it means punch already
   online and feel free to ignore the warning.

5. SSH key authentication between consumer and BYOL server

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
   zvmsdk: is running user the of BYOL server.
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
 
.. note::
   If the host key of nova-compute server changed, please run
   the following command on zvmsdk server to clean the cached host key of
   nova-compute server from zvmsdk server's known_hosts file

   .. code-block:: text

       ssh-keygen -R nova-compute-ip

Installation Requirements
-------------------------

The supported Python version includes:

- Python 2.7


Installation
============

z/VM zthin install
------------------

zthin is a library written in C that works as part of the z/VM Cloud Connectorworking.
It mainly focuses on socket connection from BYOL to z/VM SMAPI(System Management API).
z/VM Cloud Connector requires zthin as the backend to communicate with z/VM SMAPI,
thus it needs to be installed before installing z/VM Cloud Connector.

SSH onto the BYOL as root user, and then follow the following steps:

1. Clone z/VM Cloud Connector build project from github

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

z/VM SDK install
----------------

z/VM SDK is the upper transition layer of z/VM Cloud Connector. It implements the
supported SDK APIs by communicating with the zthin backend.

1. **Through RPM/DEB**

   Under current plan, there is no rpm/deb files to be supported,
   it might be changed and for now please install through code directly.

2. **Through Source Code directly**

   * Clone python-zvm-sdk project from github

     .. code-block:: text

         # git clone https://github.com/mfcloud/python-zvm-sdk.git

     (If this has been done in the "z/VM zthin install" step, this step can be
     obsoleted.)

   * Install z/VM sdk

     Please ensure to update your setuptools to the latest version before doing this step,
     the following installation step would rely on it to automatically install the depended
     python packages.

     .. code-block:: text

         # cd python-zvm-sdk
         # python ./setup.py install

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
    # This param is required
    my_ip=127.0.0.1

    [sdkserver]
    bind_addr=127.0.0.1
    bind_port=2000
    max_worker_count=64

    [wsgi]
    auth=none

    [zvm]
    # zVM disk pool and type for root/ephemeral disks.
    # This param is required
    disk_pool=ECKD:eckdpool

Setup for z/VM SDK Daemon
=========================

The z/VM Cloud Connector is designed to be run inside a daemon. The daemon server is bond to
the configured socket for receiving requests and then call the requested SDK API.

The daemon server would be run with user 'zvmsdk' and group 'zvmsdk', the following user and folder
setup should be made on BYOL for the z/VM SDK daemon to run.

* Create 'zvmsdk' user and group

  .. code-block:: text

      # useradd -d /var/lib/zvmsdk/ -m -U -p PASSWORD zvmsdk

  Replace the *PASSWORD* with your own password for the new created user.

* Configure sudo access for 'zvmsdk' user

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

Try the following python commands on BYOL.
If the two send_request commands all returns 'overallRC' as 0, that means the z/VM SDK daemon
is setup and running normally.

For use of the z/VM Cloud Connector RESTful-API, please continue to the section
of :ref:`Setup web server for running RESTful API` for the additional setup.

.. code-block:: python

    [root@test python-zvm-sdk] # python
    Python 2.7.5 (default, Aug 23 2017, 19:53:20)
    [GCC 4.8.3 20140911 (Red Hat 4.8.3-9)] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from zvmconnector import connector
    >>> c = connector.ZVMConnector('127.0.0.1', 2000)
    >>> c.send_request('host_get_info')
    {u'rs': 0, u'overallRC': 0, u'modID': None, u'rc': 0, u'output': {u'disk_available': 3171, u'ipl_time': u'IPL at 11/13/17 00:46:45 EST', u'vcpus_used': 6, u'hypervisor_type': u'zvm', u'vcpus': 6, u'zvm_host': u'OPNSTK1', u'memory_mb': 51200.0, u'cpu_info': {u'cec_model': u'2817', u'architecture': u's390x'}, u'disk_total': 3601, u'hypervisor_hostname': u'OPNSTK1', u'hypervisor_version': 640, u'disk_used': 430, u'memory_mb_used': 36761.6}, u'errmsg': u''}
    >>> c.send_request('vswitch_get_list')
    {u'rs': 0, u'overallRC': 0, u'modID': None, u'rc': 0, u'output': [u'DTCSMAPI', u'FVTVSW01', u'VSW1', u'VSW2', u'XCATVSW1', u'XCATVSW2'], u'errmsg': u''}
    >>>
