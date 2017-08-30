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

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_create_token.tpl
   :language: javascript

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

  - userid: userid_body
  - vcpus: guest_vcpus
  - memory: guest_memory
  - user_profile: user_profile_guest
  - disk_list: disk_list_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_create.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No Response

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

  - cpu: cpu_info_guest

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_cpu_info.tpl
   :language: javascript

Get Guests memory info
----------------------

**GET /guests/meminfo**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid_list: userid_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - memory: guest_memory

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_memory_info.tpl
   :language: javascript

Get Guests vnics info
---------------------

**GET /guests/vnicsinfo**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid_list: userid_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - vnics: guest_vnics

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_vnics_info.tpl
   :language: javascript

Show Guest definition
---------------------

**GET /guests/{userid}**

Display the user direct by the given userid.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - user_direct: user_direct_guest

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get.tpl
   :language: javascript

Update Guest
------------

**PUT /guests/{userid}**

Update given guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No Response

Delete Guest
------------

**DELETE /guests/{userid}**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 204 on success.

* Response contents:

  No Response


Get Guest info
--------------

**GET /guests/{userid}/info**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - info: guest_info
  - max_mem_kb: guest_memory_kb
  - num_cpu: num_cpu_guest
  - cpu_time_us: cpu_time_us_guest
  - power_state: power_status_guest
  - mem_kb: guest_memory_kb

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_info.tpl
   :language: javascript

Get Guest nic info
------------------

**GET /guests/{userid}/nic**

Return the nic and vswitch pair for specified guest

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - nic: guest_nic_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_nic.tpl
   :language: javascript

Create Guest nic
----------------

**POST /guests/{userid}/nic**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Start guest
-----------

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_start_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Stop guest
----------

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_stop_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Get guest console output 
------------------------

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_get_console_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

  `FIXME`: implement the output contents

Deploy guest
------------

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_deploy_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Get Guest power state
---------------------

**GET /guests/{userid}/power_state**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - power_state: power_status_guest

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_power_state.tpl
   :language: javascript

Update Guest nic
----------------

**PUT /guests/{userid}/nic/{vdev}**

Couple nic to vswitch

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - vdev: vdev_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:
  
  No response.

Delete Guest nic
----------------

**DELETE /guests/{userid}/nic/{vdev}**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - vdev: vdev_guest

* Response code:

  HTTP status code 204 on success.

* Response contents:
  
  No response.

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
