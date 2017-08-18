**********
 REST API
**********

This is a reference for the cloudlib4zvm API.

Version
=======

Lists version of this API.

Get SDK version
---------------

**GET /**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  Return the version of the SDK API.

.. restapi_parameters:: parameters.yaml

  - min_version: min_version_sdk
  - max_version: max_version_sdk
  - version: version_sdk

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_version.tpl
   :language: javascript

token
=====

Create token
------------

**POST /token**

* Request:

.. restapi_parameters:: parameters.yaml

  - user: token_user
  - password: token_password

* Response code:

  HTTP status code 200 on success.

* Response contents:

Guest(s)
========

Lists, creates, shows details for, updates, and deletes guests.

List Guests
-----------


**GET /guests**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  `FIXME`: should only list guests managed/created by SDK.

.. restapi_parameters:: parameters.yaml

  - guests: guest_list

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_list.tpl
   :language: javascript

Create Guest
------------

**POST /guests**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - vcpus: guest_vcpus
  - memory: guest_memory
  - user_profile: user_profile_guest
  - disk_list: disk_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get Guests cpu info
-------------------

**GET /guests/cpuinfo**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid_list: userid_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - cpu: cpu_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_cpu_info.tpl
   :language: javascript

Get Guests memory info
----------------------

**GET /guests/meminfo**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - memory:

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_memory_info.tpl
   :language: javascript

Get Guests vnics info
---------------------

**GET /guests/vnicsinfo**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - vnics:

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_vnics_info.tpl
   :language: javascript

Show Guest definition
---------------------

**GET /guests/{userid}**

Display the user direct by the given userid.

* Request:

  - userid: The userid to be displayed, it should comply with z/VM userid standard.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - user_direct: The user direct of the given userid.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get.tpl
   :language: javascript

Update Guest
------------

**PUT /guests/{userid}**

Update given guest.

* Request:

  - userid: The userid to be updated.

* Response code:

  HTTP status code 200 on success.

* Response contents:


Delete Guest
------------

**DELETE /guests/{userid}**

* Request:

  - userid: The userid to be deleted.

* Response code:

  HTTP status code 204 on success.

* Response contents:

Get Guest info
--------------

**GET /guests/{userid}/info**

* Request:

  - userid: The userid to get information from.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - info: the object of the information returned
  - max_mem_kb:
  - num_cpu:
  - cpu_time_us:
  - power_state:
  - mem_kb:

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_info.tpl
   :language: javascript

Get Guest nic info
------------------

**GET /guests/{userid}/nic**

* Request:

  - userid: The userid to get nic information from.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - nic: the nic information

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_nic.tpl
   :language: javascript

Create Guest nic
----------------

**POST /guests/{userid}/nic**

* Request:

  - userid: The userid to create nic.

* Response code:

  HTTP status code 200 on success.

* Response contents:

Start guest
-----------

**POST /guests/{userid}/action**

* Request:

  - guest:
  - action:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Stop guest
----------

**POST /guests/{userid}/action**

* Request:

  - guest:
  - action:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get guest console output 
------------------------

**POST /guests/{userid}/action**

* Request:

  - guest:
  - action:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Deploy guest
------------

**POST /guests/{userid}/action**

* Request:

  - guest:
  - action:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get Guest power state
---------------------

**GET /guests/{userid}/power_state**

* Request:

  - userid: The userid to get power state information from.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - power_state: the power state of the guest.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_power_state.tpl
   :language: javascript

Update Guest nic
----------------

**PUT /guests/{userid}/nic/{vdev}**

* Request:

  - userid:
  - vdev:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Delete Guest nic
----------------

**DELETE /guests/{userid}/nic/{vdev}**

* Request:

  - userid:
  - vdev:

* Response code:

  HTTP status code 204 on success.

* Response contents:

Host
====

Get info from host (hypervisor) running on.

Get Host Info
-------------

**GET /host/info**

* Request:

  No parameters needed. 

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - host: the object of host information.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_info.tpl
   :language: javascript

Get Host disk pool info
-----------------------

**GET /host/disk_info/{disk}**

* Request:

  - disk: the disk name to get pool information from.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - disk_info: the object of disk information.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_disk_info.tpl
   :language: javascript

Image(s)
========

Lists, creates, shows details for, updates, and deletes images.

List images
-----------

**GET /images**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - disk_info: the object of disk information.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

**POST /images**

* Request:

  - image:
  - url:
  - remotehost:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get root disk size of image
---------------------------

**GET /images/{name}/root_disk_size**

* Request:

  - name: Name of the image to get root disk size from.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - size: the size of the given disk.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_get_root_disk_size.tpl
   :language: javascript

Delete image
------------

**DELETE /images/{name}**

* Request:

  Name of the image to be deleted.

* Response code:

  HTTP status code 204 on success.

* Response contents:

Volume(s)
=========

Lists, creates, shows details for, updates, and deletes volumes.

Attach volume to Guest
----------------------

* POST /guests/{userid}/volumes

  - Request:

  request

  - Response:

  response

  - HTTP status code 204 on Success.

Detach volume from Guest
------------------------

* DELETE /guests/{userid}/volumes

  - Request:

  request

  - Response:

  response

  - HTTP status code 204 on Success.

VSwitch
=======

Lists, creates, shows details for, updates, and deletes vswitch.

Create vswitch
--------------

**POST /vswitchs**

* Request:

  - vswitch:
  - name:
  - rdev:
  - controller:
  - connection:
  - queue_mem:
  - router:
  - network_type:
  - vid:
  - port_type:
  - update:
  - gvrp:
  - native_vid:  

* Response code:

  HTTP status code 200 on success.

* Response contents:

List vswitchs
-------------

**GET /vswitchs**

* Request:

  No parameter needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - vswlist: a list of vswitch that defined in the z/VM.

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_get.tpl
   :language: javascript

Update vswitch
--------------

**PUT /vswitchs/{name}**

* Request:

  -name:

* Response code:

  HTTP status code 200 on success.

* Response contents:

Delete vswitch
--------------

**DELETE /vswitchs/{name}**

* Request:

  -name: the name of the vswitch to be deleted.

* Response code:

  HTTP status code 204 on success.

* Response contents:
