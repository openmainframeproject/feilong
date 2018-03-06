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

Introduction
************

What is the z/VM Cloud Connector
================================

The z/VM cloud connector is a development sdk for manage z/VM.
It provides a set of APIs to operate z/VM including guest, image,
network, volume etc.

Just like os-win for nova hyperv driver and oslo.vmware for
nova VMware driver, z/VM cloud connector (CloudLib4zvm) is
for nova z/vm driver and other z/VM related openstack driver such
as neutron, ceilometer.

Integration Samples
===================

* Sample 1: for openstack

.. image:: ./images/openstack_zcc.jpg

* Sample 2: for other solutions like VMware etc.

.. image:: ./images/3rd_iaas.jpg

Internal Architecture
=====================

Here's internal component list of zvm cloud connector.

.. image:: ./images/zcc_internal.jpg

Comparison with VMware OpenStack driver
=======================================

Here's architecture comparsion between z/VM and VMware enablement for openstack.

.. image:: ./images/zvm_vmware.jpg
