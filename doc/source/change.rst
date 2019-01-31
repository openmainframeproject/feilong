.. _`Change log`:

Release Notes
*************

Release 1.4.0
-------------

New features released with zVMCLoudConnector 1.4.0:

* Attach/detach volume to inactive guest.

* Support set hostname without cloud-init.

Release 1.3.0
-------------
New features released with zVMCloudConnector 1.3.0:

* Support upload image through octet stream.

* Guest live migrate, support live migrate in z/VM SSI cluster.

* Live resize guest memory, and static resize guest memory.

* Attach/detach volume to active guest.

Release 1.2.1
-------------
zVMCloudConnector 1.2.1 includes one change:

* Support "application/json,utf-8" context type in restclient.

Release 1.2.0
-------------
Following new features released with zVMCloudConnector 1.2.0:

* Dedicate OSA device to guest. If osa_device specified when invoking
  z/VM Cloud Connector restful API to create network interface, the OSA device
  will be dedicated to the guest.

* Resize CPUs of guest. Resize guest CPU count by updating static definition.

* Live resize CPUs of guest. Currently only increasing CPU count is supported,
  decreasing is not supported.

Release 1.1.0
-------------
zVMCloudConnector 1.1.0 is mainly includes the change:

* Switch config drive format from tgz to iso9660

    Config drive in iso9660 format is commonly used by cloud-init.

Release 1.0.1
-------------

zVMCloudConnector 1.0.1 release mainly adapts to the SMAPI changes in z/VM 6.4
APAR VM66120 1Q 2018. If the z/VM 6.4 has been applied APAR VM66120, must
upgrade z/VM Cloud Connector to 1.0.1 .

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
