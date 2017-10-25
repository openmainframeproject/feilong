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


z/VM sdk install
----------------

* Through RPM/DEB

TBD

* Through Code directly install

- Build Install zthin rpm

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

Refer to xxx for more 

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

