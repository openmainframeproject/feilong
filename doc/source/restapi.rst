**********
 REST API
**********

This is a reference for the zvm cloud connector (cloudlib4zvm) API.

Common output
=============

zvm cloud connector returns following output as reference, in case
encounter an error, those information will be helpful to report bug/issue.
The following API reference document will only cover ``out`` part as
it's different for each API.

.. restapi_parameters:: parameters.yaml
  - overallRC: ret_overallrc
  - rc: ret_rc
  - rs: ret_rs
  - errmsg: ret_errmsg
  - modID: ret_modID
  - output: ret_output

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

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_token_create.tpl
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

Get Guests stats including cpu and memory
-----------------------------------------

**GET /guests/stats**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid_list: userid_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: stats_guest

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_stats.tpl
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

  - output: guest_vnics

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

  - output: user_direct_guest

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

  - output: guest_info
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

Start a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_start_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_create.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Stop guest
----------

Stop a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_stop_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_stop.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Pause guest
-----------

Pause a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_pause_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_pause.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Unpause guest
-------------

Unpause a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_unpause_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_unpause.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Reboot guest
------------

Reboot a guest, this will use 'reboot' command on the
given guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_reboot_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_reboot.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Reset guest
-----------

Reset a guest, this will first gracefully logoff the guest from
z/VM it is running on, then log on the guest and IPL.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_userid
  - action: action_reset_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_reset.tpl
   :language: javascript

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

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_console_output.tpl
   :language: javascript

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

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_deploy.tpl
   :language: javascript

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

  - output: power_status_guest

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

.. restapi_parameters:: parameters.yaml

  - output: host_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_info.tpl
   :language: javascript

Get Host disk pool info
-----------------------

**GET /host/disk_info/{disk}**

* Request:

.. restapi_parameters:: parameters.yaml

  - disk: disk_host

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: disk_info_host

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

.. restapi_parameters:: parameters.yaml

  - output: disk_info_host

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

**POST /images**

* Request:

.. restapi_parameters:: parameters.yaml

  - image: image_name
  - url: image_url
  - image_meta: image_metadata
  - remotehost: remotehost_image

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_create_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Get root disk size of image
---------------------------

**GET /images/{name}/root_disk_size**

* Request:

.. restapi_parameters:: parameters.yaml

  - name: image_name

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: root_disk_size_image

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_get_root_disk_size.tpl
   :language: javascript

Delete image
------------

**DELETE /images/{name}**

* Request:

.. restapi_parameters:: parameters.yaml

  - name: image_name

* Response code:

  HTTP status code 204 on success.

* Response contents:

  No response.

Volume(s)
=========

Lists, creates, shows details for, updates, and deletes volumes.

Attach volume to Guest
----------------------

**POST /guests/{userid}/volumes**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response:

  HTTP status code 204 on Success.

* Response contents

  No response.

Detach volume from Guest
------------------------

**DELETE /guests/{userid}/volumes**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response:

  HTTP status code 204 on Success.

* Response contents

  No response.

VSwitch
=======

Lists, creates, shows details for, updates, and deletes vswitch.

Create vswitch
--------------

**POST /vswitchs**

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name_body
  - rdev: rdev_vswitch
  - controller: controller_vswitch
  - connection: connection_vswitch
  - network_type: network_type_vswitch
  - router: router_vswitch
  - vid: vid_vswitch
  - port_type: port_type_vswitch
  - gvrp: gvrp_vswitch
  - queue_mem: queue_mem_vswitch
  - native_vid: native_vid_vswitch
  - persist: persist_option_vswitch

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

List vswitchs
-------------

**GET /vswitchs**

* Request:

  No parameter needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: vswitch_list

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_get.tpl
   :language: javascript

Update vswitch
--------------

**PUT /vswitchs/{name}**

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_update_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Delete vswitch
--------------

**DELETE /vswitchs/{name}**

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name

* Response code:

  HTTP status code 204 on success.

* Response contents:

  No response.
