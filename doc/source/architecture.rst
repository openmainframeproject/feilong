
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
