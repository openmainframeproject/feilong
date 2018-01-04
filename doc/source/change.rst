
.. _`Change log`:

Release Notes
*************

Release 1.0.0
-------------

zVMCloudConnector 1.0.0 release includes many basic features that enables
z/VM Cloud management through zVMCloudConnector APIs.

**Supported features**

* Host(hypervisor) management

  get host information and get host disk pool information

* Guests(virtual machines) management

  - Provisoning: create/delete guest definition, capture/deploy, create/delete
    disks, configure disks, create/delete vnics, couple/uncouple nic to
    vswitch, configure vnics and network interfaces

  - Power actions including start, stop, softstop, reboot, reset, pause,
    unpause, get power state

  - Query information: get guest information, guest list, get definition
    information, get console outputs, get nic information

* Image management

  Support import, export, delete images; query image information, get image
  root disk size

* Network features

  - vswitch: create, delete, update vswitch; grant, revoke vswitch access,
    get vswitch list, query vswitch information, set user vlan id

  - Hot plug/unplug network interfaces to live guest

* Monitoring

  Inspect cpu, memory stats, inspect vnic stats

* RESTful API

  zVMCloudConnector provides standard RESTful API, which makes it easier to
  integrate with other cloud platforms. Included features:

* Authorization mechanism

  Support token based validation mechanism to make sure all zVMCloudConnector
  RESTful API requests are authorized.

* IUCV management channel

  zVMCloudConnector manages virtual machines through z/VM IUCV communication
  channel, which not requires network connection.

* Monitoring data cache

  Implement a cache layer in zVMCloudConnector to improve performance of getting
  monitoring data

**Know Issues**

Not applicable for now.

Release 0.3.2
-------------

Beta release since Dec 4, 2017
