
Quick Start
***********

This is the document that describes the installation, configuration
and basic usages of z/VM Cloud Connector.

Pre-requirements
================

z/VM Cloud Connector has to be installed inside a Linux running on z/VM.
Currently, those distros are tested:

- RHEL 6.x/7.x
- SLES 11.x/12.x
- Ubuntu 16.04

**NOTE**: This guide is based on RHEL 7, you may need to adjust the commands
on other Linux distros.

From now on, BYOL (Bring Your Own Linux) will be used to represent
the Linux on which the z/VM Cloud Connector will be run.

For the z/VM Cloud Connector to run, the BYOL must have enough free space (>100M).
And besides that, the following updates need to be made to the BYOL.

Preparation on BYOL
-------------------

1. **Authorize BYOL user for z/VM SMAPI call.**

   VSMWORK1 AUTHLIST need to be updated in order to make the BYOL
   machine be able to issue SMAPI call. Refer to z/VM Systems Management
   Application Programming for how to make it.

2. **Update BYOL definition for spawning guests.**

   Assume BYOL has its definition on z/VM, it needs to have following entry in
   its User Directory in order to link disk during stage of spawning guests.

   .. code-block:: text

       OPTION LNKNOPAS

   See z/VM Systems Management Application Programming for how to make it.

3. **Enable punch device**

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

Installation
============

Dependency install
------------------

The following python packages are depended by the z/VM Cloud Connector, they need to
be firstly installed:

* netaddr
* jsonschema
* pyjwt
* six

Those packages are located at pypi_. Usually
user is able to install them by using following command::

  pip install netaddr

.. _pypi: http://pypi.python.org/

z/VM zthin install
------------------

zthin is a library written by c working as part of the z/VM Cloud Connector.
It mainly focuses on socket connection from BYOL to z/VM SMAPI(System Management API).
z/VM Cloud Connector requires zthin as the backend to communicate with z/VM SMAPI,
thus it needs to be installed defore installing z/VM Cloud Connector.

SSH onto the BYOL as root user, and then follow the following steps:

1. Clone python-zvm-sdk project from github

   .. code-block:: text

       [root@xxxx ~]# git clone https://github.com/mfcloud/python-zvm-sdk.git

2. Trigger the build tool

   .. code-block:: text

       [root@xxxx ~]# cd python-zvm-sdk
       [root@xxxx ~]# sh ./zthin-parts/buildzthingithub master

   If this build finishes successfully, the result rpm will be generated
   in the /root/zthin-build/RPMS/s390x/ directory named in the format
   *zthin-version-snapdate.s390x.rpm* where *version* is the zthin version
   number and *date* is the build date.

3. Install the rpm generated in last step

   .. code-block:: text

       [root@xxxx ~]# rpm -ivh /root/zthin-build/RPMS/s390x/zthin-3.1.0-snap201710300123.s390x.rpm

   Be sure to replace the *zthin-3.1.0-snap201710300123.s390x.rpm* with your own
   rpm name.

4. Verify zthin can work::

   .. code-block:: text

       [root@xxxx ~]# /opt/zthin/bin/smcli Image_Query_DM -T opncloud

   If the zthin rpm is installed normally, the previous smcli command should be
   able to return the directory entry of user OPNCLOUD.

z/VM SDK install
----------------

z/VM SDK is the upper transition layer of z/VM Cloud Connector. It implements the
supported SDK APIs by communicating with the zthin backend.

1. **Through RPM/DEB**

   * Under current plan, there is no rpm/deb files to be supported,
   it might be changed and for now please install through code directly.


2. **Through Source Code directly**

   * Clone python-zvm-sdk project from github

   .. code-block:: text

       [root@xxxx ~]# git clone https://github.com/mfcloud/python-zvm-sdk.git

   (If this has been done in the "z/VM zthin install" step, this step can be
   obsoleted.)

   * Install z/VM sdk

   .. code-block:: text

       [root@xxxx ~]# cd python-zvm-sdk
       [root@xxxx ~]# python ./setup.py install

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
      log_level=logging.INFO
      log_dir=/var/log/zvmsdk/

      [network]
      # IP address of the Linux machine which is running SDK on.
      # This param is required
      my_ip=127.0.0.1

      [sdkserver]
      bind_addr=127.0.0.1
      bind_port=2000
      max_worker_count=64
      connect_type=socket

      [wsgi]
      auth=none

      [zvm]
      # z/VM host name of this hypervisor.
      # This param is required
      host=zvmhost

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

      [root@xxxx ~]# useradd -d /var/lib/zvmsdk/ -m -U -p PASSWORD zvmsdk

  Replace the *PASSWORD* with your own password for the new created user.

* Setup home directory

  .. code-block:: text

      [root@xxxx ~]# mkdir -p /var/lib/zvmsdk
      [root@xxxx ~]# chown -R zvmsdk:zvmsdk /var/lib/zvmsdk
      [root@xxxx ~]# chmod -R 755 /var/lib/zvmsdk

* Setup log directory

  The folder to which the z/VM SDK log would be written to can be configured with the 'log_dir'
  option in 'default' section. By default, the log folder is '/var/log/zvmsdk'. If you have customized
  the 'log_dir' value, you need to change the folder in following commands accordingly.

  .. code-block:: text

      [root@xxxx ~]# mkdir -p /var/log/zvmsdk
      [root@xxxx ~]# chown -R zvmsdk:zvmsdk /var/log/zvmsdk
      [root@xxxx ~]# chmod -R 755 /var/log/zvmsdk

* Setup configuration directory

  .. code-block:: text

      [root@xxxx ~]# mkdir -p /etc/zvmsdk
      [root@xxxx ~]# chown -R zvmsdk:zvmsdk /etc/zvmsdk
      [root@xxxx ~]# chmod -R 755 /etc/zvmsdk
      [root@xxxx ~]# ls -l /etc/zvmsdk

  A file named zvmsdk.conf should be found under /etc/zvmsdk folder and contains at least all the required
  options before the z/VM SDK daemon can be started.

Verification
============

Try following command in your zvmsdk tools folder,
if you can get host info, that means z/VM sdk configuration done.

   .. code-block:: python

  [root@xxxx sdkclient]# python
  Python 2.7.5 (default, Oct 11 2015, 17:46:32)
  [GCC 4.8.3 20140911 (Red Hat 4.8.3-9)] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import sdkclient.client
  >>> s = sdkclient.client.SDKClient()
  >>> s.send_request('host_get_info')
  {u'rs': 0, u'overallRC': 0, u'modID': None, u'rc': 0, u'output': {u'disk_available': 3217, u'ipl_time': u'IPL at 10/08/17 21:14:04 EDT', u'vcpus_used': 6, u'hypervisor_type': u'zvm', u'vcpus': 6, u'zvm_host': u'OPNSTK1', u'memory_mb': 51200.0, u'cpu_info': {u'cec_model': u'2817', u'architecture': u's390x'}, u'disk_total': 3623, u'hypervisor_hostname': u'OPNSTK1', u'hypervisor_version': 640, u'disk_used': 406, u'memory_mb_used': 33894.4}, u'errmsg': u''}
  >>>
