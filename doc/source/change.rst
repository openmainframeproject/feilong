.. Copyright 2017,2018 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Change log`:

Release Notes
*************

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
