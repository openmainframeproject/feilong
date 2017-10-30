*****************
Quick start guide 
*****************

This is the document that describe the install, configuration
and basic usage of zvm cloud connector (z/VM SDK).

===============
Prerequirements
===============

z/VM SDK has to be installed inside a Linux running on z/VM.
Currently, those are tested:

- RHEL 6.x/7.x
- SLES 11.x/12.x

In order to utilize z/VM SDK, user need pre install a Linux
with enough free space (>100M).

From now on, BYOL (Bring your own linux) will be used to represent
the Linux which running z/VM SDK on.

=======
Install
=======

Dependency install
------------------

Some dependency python packages need to be installed.

- netaddr
- jsonschema
- pyjwt
- six

Those packages are located at pypi_. Usually
user is able to install them by using following command::

  pip install netaddr

.. _pypi: http://pypi.python.org/

z/VM zthin install
------------------

zthin is a library written by c and mainly focus on socket connection
from BYOL to z/VM SMAPI.

SSH onto the BYOL as root user, and then follow the following steps:

- Clone python-zvm-sdk project from github::

  [root@xxxx ~]# git clone https://github.com/mfcloud/python-zvm-sdk.git

- Trigger the build tool::

  [root@xxxx ~]# cd python-zvm-sdk
  [root@xxxx ~]# sh ./zthin-parts/buildzthingithub master

If this build finishes successfully, the result rpm will be generated
in the /root/zthin-build/RPMS/s390x/ directory named in the format
*zthin-version-snapdate.s390x.rpm* where *version* is the zthin version
number and *date* is the build date.

- Install the rpm generated in last step::

  [root@xxxx ~]# rpm -ivh /root/zthin-build/RPMS/s390x/*zthin-3.1.0-snap201710300123.s390x.rpm*

Be sure to replace the *zthin-3.1.0-snap201710300123.s390x.rpm* with your own
rpm name.

- Verify zthin can work::

  [root@xxxx ~]# /opt/zthin/bin/smcli Image_Query_DM -T opncloud

If the zthin rpm is installed normally, the previous smcli command should be
able to return the directory entry of user OPNCLOUD.

z/VM sdk install
----------------

- **Through RPM/DEB**

  - Under current plan, there is no rpm/deb files to be supported,
    it might be changed and for now please install through code directly.

- **Through Source Code directly**

* Clone python-zvm-sdk project from github

    (If this has been done in the "z/VM zthin install" step, this step can be
    obsoleted.)::

    [root@xxxx ~]# git clone https://github.com/mfcloud/python-zvm-sdk.git

* Install z/VM sdk::

    [root@xxxx ~]# cd python-zvm-sdk
    [root@xxxx ~]# python ./setup.py install

=============
Configuration
=============

Guest definition update
-----------------------

* Update VSMWORK1 AUTHLIST in SMAPI VMSYS:VSMWORK1. 

VSMWORK1 AUTHLIST need to be updated in order to make the BYOL
Linux guest machine be able to issue SMAPI call. See z/VM Systems Management
Application Programming for how to make it.

* Update User direct of BYOL

Assume BYOL has its definition on z/VM, it need has following setting in
its user directory in order to link disk during guest create stage::
  
  OPTION LNKNOPAS

See See z/VM Systems Management Application Programming for how to make it.

* Enable punch device

In order to spawn guest, BYOL need punch files to spawned guests' reader,
so device punch need to be enabled.

use following command on BYOL itself to achieve that::

  [root@xxxx ~]# cio_ignore -r d
  [root@xxxx ~]# chccwdev -e d
  Setting device 0.0.000d online
  Done

If something like 'is already  online' is returned, it means punch already
online and feel free to ignore the warning.

z/VM SDK configuration
----------------------

Refer to z/VM SDK configuration guide for more information.

Here's a sample configuration of z/VM SDK::

  [default]

  [logging]
  log_dir = /tmp
  log_level = logging.INFO

  [zvm]
  host = opnstk1
  client_type = xcat
  diskpool_type = ECKD
  diskpool = xcateckd
  disk_pool = ECKD:xcateckd
  user_default_password = password
  default_ephemeral_mntdir = /mnt/ephemeral/

  [network]
  my_ip = 127.0.0.1

  [database]
  path = /tmp/zvmsdkdb

============
Verification
============

Try following command in your zvmsdk tools folder,
if you can get host info, that means z/VM sdk configuration done::

  [root@0823rhel72 sdkclient]# python
  Python 2.7.5 (default, Oct 11 2015, 17:46:32)
  [GCC 4.8.3 20140911 (Red Hat 4.8.3-9)] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import sdkclient.client
  >>> s = sdkclient.client.SDKClient()
  >>> s.send_request('host_get_info')
  {u'rs': 0, u'overallRC': 0, u'modID': None, u'rc': 0, u'output': {u'disk_available': 3217, u'ipl_time': u'IPL at 10/08/17 21:14:04 EDT', u'vcpus_used': 6, u'hypervisor_type': u'zvm', u'vcpus': 6, u'zvm_host': u'OPNSTK1', u'memory_mb': 51200.0, u'cpu_info': {u'cec_model': u'2817', u'architecture': u's390x'}, u'disk_total': 3623, u'hypervisor_hostname': u'OPNSTK1', u'hypervisor_version': 640, u'disk_used': 406, u'memory_mb_used': 33894.4}, u'errmsg': u''}
  >>>
