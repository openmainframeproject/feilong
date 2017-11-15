
Sample for using sdk
********************

Sample
======

There's a sample file inside zvm sdk's source tree (tools/sample.py)
A couple of configuration items need to be modified such as
IP address, disk pool name etc, then use python to run
the command like following to deploy a new guest::

   import sample
   sample.run_guest()

Here's the code:

.. include:: ../../tools/sample.py
   :literal:

Sample flow in detail
=====================

Spawn a new virutal machine

.. image:: ./images/spawn_flow.jpg

1) Image import from external image repository into zvm cloud connector , for one image, only need to be done once
2) Store the information into DB record
3) Call from upper layer to create a guest, this will define a .user direct. through z/VM SMAPI and DIRMAINT based on user input along with the disks allocations 
4) SMAPI call DIRMAINT to define a user direct
5) Call from upper layer to deploy a guest
6) In turn, cloud connector start to copy disk contents from image to the allocated disks in step 3
7) Post deploy actions such as network setup, customerized files from cloud connector the new deploy VM
8) Start the VM 
9) During power on of the VM (first time) , doing setup of the network and utilize the customerized files to update network, hostname etc (by default, using cloud-init)


Create a Vswitch

.. image:: ./images/create_vswitch_flow.jpg

1) Call from upper layer to trigger the Vswitch create call
2) HTTP service (cloud connector REST API) get the request and handle to cloud connector server
3) In turn SMAPI was called and handle the VSWITCH cerate command, this will include persistent definition of Vswitch and define in z/VM CP
4) CP was called to create vswitch on the fly

