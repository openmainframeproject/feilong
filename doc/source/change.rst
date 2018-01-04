
.. _`Change log`:

Release Notes
*************

Release 1.0.0
-------------

zVMCloudConnector 1.0.0 release includes many basic features that enables
z/VM Cloud management through zVMCloudConnector APIs.

**Supported features**

* Host(hypervisor) management

  get host information and get host disk pool information.

* Guests(virtual machines) management

  - Provisoning: create, delete guest definition; capture, deploy guests;
    create, delete, configure disks; create, delete, couple, uncouple vnics to
    vswitch; configure vnics and network interfaces.

  - Power actions including start, stop, softstop, reboot, reset, pause,
    unpause and get power state.

  - Query information: get guest information, guest list, get guest definition
    information, get console outputs, get nic information.

* Image management

  Support import, export, delete images; query image information, get image
  root disk size.

* Network features

  - vswitch: create, delete vswitch; grant, revoke vswitch access,
    get vswitch list, query vswitch information, set user vlan id.

  - Hot plug/unplug network interfaces to live guest.

* Monitoring

  Inspect virtual machine cpu, memory and vnic stats.

* RESTful API

  zVMCloudConnector provides standard RESTful API, which makes it easier to
  integrate with other cloud platforms. zVMCloudConnector RESTful API supports
  to be configured in a HTTP or HTTPS server.

* Authorization mechanism

  Support token based validation mechanism to make sure all zVMCloudConnector
  RESTful API requests are authorized.

* IUCV management channel

  zVMCloudConnector manages virtual machines through z/VM IUCV communication
  channel, which does not require network connection.

* Monitoring data cache

  Implement a cache layer in zVMCloudConnector to improve performance of getting
  monitoring data.

Release 0.3.2
-------------

Beta release since Dec 4, 2017
