..
 Copyright Contributors to the Feilong Project.
 SPDX-License-Identifier: CC-BY-4.0

.. _`Change log`:

Release Notes
*************

Release 1.6.7
-------------

New features to be released with Feilong 1.6.7 (not yet released):

* Direct access to CP through ``vmcp`` instead of SMAPI for some operations
  (new ``use_smapi`` configuration option).

* Pluggable database backend.

* Multiple disk pools.

* New APIs: list of minidisks, list of PCIF devices.

* Guest creation: ``logon_by``, comments in the user directory, custom CPU
  share; DHCP for network interfaces.

* RHEL 10, Ubuntu 24.04 and 25 support.

* Image checksums use SHA-512 instead of MD5.

* SMAPI timeout configuration.

* Fixes in FCP management (release on VM deletion, leaked FCP devices).

* zthin 3.2.0: z/VM 7.1 and 7.2 support, the new
  ``smcli System_Processor_Query`` command, the ``refresh_bootmap`` tool
  for boot from volume, and security fixes for buffer overflows.

* Many documentation fixes.

Release 1.6.6
-------------

New features released with Feilong 1.6.6 (2023-11-13):

* FCP Multipath Templates are aware of PCHIDs: the PCHID of each FCP device
  is stored in the database, ``get_volume_connector`` selects FCP devices
  according to it, and the new tool ``zvmsdk-getpchid`` lists the PCHIDs
  used by all FCP Multipath Templates.

* Alternate IPL path for boot from volume (multipath IPL, using
  ``IPL LOADDEV``).

* Extend LVM partitions.

* Run ``wipefs`` before copying an image to the target disk.

* Support more ``DEF STOR`` statement formats when resizing guest memory.

* Get DASD group details.

* Synchronize the database with z/VM after releasing FCP devices.

Release 1.6.5
-------------

New features released with Feilong 1.6.5 (2023-05-04):

* Volume attach/detach: per-VM lock instead of a global lock, new
  ``do_rollback`` parameter, ``fcp_template_id`` in ``connection_info``.

* Bring FCP devices online with ``chzdev`` instead of ``chccwdev``.

* Network: deploy Ubuntu 20.04 and 22.04 with multiple NICs; the gateway of
  the primary NIC becomes the default gateway.

* Report an error when deploying a guest from volume with only one path.

* Fix FCP leftovers when detaching the last volume, and a potential memory
  leak due to syslog.

Release 1.6.4
-------------

New features released with Feilong 1.6.4 (2022-10-31):

* FCP Multipath Templates: create, edit, delete and list templates of FCP
  devices, optionally per storage provider; ``get_volume_connector`` and
  the FCP usage APIs take a ``fcp_template_id``. The ``fcp_list`` option is
  removed from ``zvmsdk.conf``, and the ``get_all_fcp_usage`` API is
  removed.

* RHEL 9 and Ubuntu 22.04 support.

* MTU configuration of the network interfaces for RHEL, SLES, Ubuntu and
  RHCOS.

* Resize CPUs with share units.

* ``port_type`` parameter when coupling a NIC to a vswitch.

* ``guest_get_info`` also returns the number of online CPUs, the OS
  distribution and the kernel version.

* New ``/smapi-healthy`` REST API to report the status of SMAPI calls.

* Use zEDC to speed up image compression.

* Enhanced rollback of volume attach/detach.

* Mask the ``X-Auth-Token`` value in the logs.

Release 1.6.3
-------------

New features released with Feilong 1.6.3 (2022-01-26):

* Get the SSI cluster information of the host; ``guest_list`` works in an
  SSI cluster.

* User directory statements: ``SCHEDULE`` (CPU pool), ``COMMAND PCIF``,
  ``COMMAND SET VMRELOCATE * DOMAIN Z15ONLY`` and
  ``COMMAND SET SHARE &USERID RELATIVE``.

* FCP management: WWPN columns in the FCP table, map of physical and virtual
  WWPNs, ``min_fcp_path_count``, owner of the FCP devices, synchronization
  of the FCP database when restarting sdkserver. ``get_volume_connector``
  returns the total number of FCP paths.

* ``wwid`` parameter for ``refresh_bootmap``, and timeout for the execution
  of punch scripts.

* Live migration: ``dest_zcc_userid`` may be ``None``, and IUCV
  authorization is skipped when migrating RHCOS guests.

* Cache the list of volumes of the host.

Release 1.6.2
-------------

New features released with Feilong 1.6.2 (2021-07-30):

* Guest creation: ``account``, ``user_profile`` and ``comments`` of the user
  directory.

* ``get_fcp_usage`` and ``set_fcp_usage`` APIs.

* Get the volumes of a disk pool and volume information from the host;
  ``disk_pool`` may be ``None`` in ``host_get_diskpool_volumes``.

* Capture a guest that is shut off; restart an active guest after capturing
  it.

* Boot from volume: ``refresh_bootmap`` supports RHCOS and LVM guests, with a
  configurable timeout; multiple paths per FCP device in the RHCOS kernel
  command line.

* Volume detach: remove the LUN permanently, put FCP devices offline after
  detaching the last volume, and continue when the volume is in use.

* Adjust the CPU definition for LinuxONE.

Release 1.6.1
-------------

New features released with Feilong 1.6.1 (2021-02-03):

* z/VM 7.2 support.

* z/VM Cloud Connector is renamed to Feilong in the documentation.

* Swap disk as VDISK.

* VLAN ID parameter when coupling a NIC to a vswitch.

* New configuration option ``user_default_max_reserved_memory``; the default
  value of ``user_default_max_memory`` becomes 64G.

* ``live_resize_memory`` supports the new output format of ``lsmem``.

* ``disk_pool`` is ``None`` by default.

* ``guest_start`` checks that the guest is reachable, with a timeout.

* ``refresh_bootmap`` returns a dictionary and supports RHCOS 4.7.

Release 1.6.0
-------------

New features released with Feilong 1.6.0 (2020-09-18):

* Ubuntu 20.04 and SLES 15 support.

* Punch scripts for volume attach/detach are generated from Jinja2
  templates.

* XFS file system for guests that boot from volume.

* FCP path selection: traverse FCP devices and WWPNs to look for a proper
  path, support non-contiguous FCP lists.

* Images captured from an FCP volume have no header; default compression
  level for captured images.

* ``port_macs`` is optional in ``guest_register``.

* Code of Conduct, and CI checks with GitHub Actions.

* Red Hat CoreOS (RHCOS) support: image import, deployment from ECKD or FCP
  disks, Ignition, fixed IP configuration.

* Boot from volume: ``guest_create`` and ``guest_deploy`` support it, new
  ``refresh_bootmap`` API, extend the root partition of a volume, reserve
  FCP devices (``reserve`` flag of ``get_volume_connector``).

* RHEL 8 provisioning, with SELinux in enforcing mode.

* Guest onboarding in ``guest_register`` and new offboarding API
  ``guest_deregister``.

* List the guests of the hypervisor; get the power state and the user
  directory of a guest from the hypervisor; get adapters information.

* Swap partitions.

* Disk types 3390-? and 9336-?; z/VM 7.1 API functional level.

* ``image_query`` returns a timestamp.

* The project moves to the Open Mainframe Project.

Release 1.5.0
-------------

New features released with zVMCloudConnector 1.5.0 (2019-11-14):

* Multipath FCP devices, and several volumes attached to the same guest.

* IPL from CMS, IPL parameters and load parameters.

* Virtual device number when creating a guest.

* Option to create disks without formatting them.

* Resize the last partition of an ECKD disk with several partitions.

* Write DNS information in the network configuration files of RHEL.

* Documentation under the CC BY 4.0 license.

* Support a remote host sshd port other than 22.

* Use ``wicked ifreload all`` for SLES 12.

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

Release 1.2.4
-------------

zVMCloudConnector 1.2.4 includes the following changes:

* Upper-case the user IDs read from the database when checking that a guest
  exists.

* Include the test requirements and ``tox.ini`` in the source package.

Release 1.2.3
-------------

zVMCloudConnector 1.2.3 includes the following changes:

* Remove the Python 3 version check.

* Update the Python classifiers.

Release 1.2.2
-------------

zVMCloudConnector 1.2.2 includes one change:

* Support Python 3.6.

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

Release 1.1.1
-------------

zVMCloudConnector 1.1.1 includes one change:

* Allow WebOb 1.8.x.

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
