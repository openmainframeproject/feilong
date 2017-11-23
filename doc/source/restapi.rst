RESTful APIs
************

This is a reference for the z/VM Cloud Connector RESTful API.

Response Data Definition
========================

The following table gives a reference of general response data definition
of each z/VM Cloud Connector RESTful API. In case of encountering an error,
those information will be helpful to report bug/issue.

.. restapi_parameters:: parameters.yaml

  - overallRC: ret_overallrc
  - rc: ret_rc
  - rs: ret_rs
  - errmsg: ret_errmsg
  - modID: ret_modID
  - output: ret_output

The following detail API description will only cover ``output`` part as
it's different for each API.
(This document is a beta version, if you find some API that is not clearly
described, you can refer to the z/VM SDK API section for the API description.)

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

  - output : ret_output
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

Get a valid token to perform further request by using user and password.

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

.. restapi_parameters:: parameters.yaml

  - X-Auth-Token: auth_token

Guest(s)
========

Lists, creates, shows details for, updates, and deletes guests.

List Guests
-----------

**GET /guests**

List all guests managed by zvm cloud connecter on the host.

* Request:

  None

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: guest_list

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_list.tpl
   :language: javascript

Create Guest
------------

**POST /guests**

Create a new guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_dict
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

Guest add disks
---------------

**POST /guests/{userid}/disks**

Add disks for a guest

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - disk_info: disk_info
  - disk_list: disk_list

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_add_disks.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No Response

Guest delete disks
------------------

**DELETE /guests/{userid}/disks**

Delete disks form a guest

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - vdev_info: vdev_info
  - vdev_list: disk_vdev_list

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_delete_disks.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No Response

Get Guests stats including cpu and memory
-----------------------------------------

**GET /guests/stats**

Get guests cpu, memory information.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: userid_list_guest

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

Get guests virtual nic information.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: userid_list_guest

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: guest_vnics

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_vnics_info.tpl
   :language: javascript

Get Guests nic info
---------------------

**GET /guests/nics**

Get guests nic information, including userid, nic number, vswitch, nic id and comments.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid_opt
  - nic_id: nic_id_opt
  - vswitch: vswitch_name_opt

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: guests_nic_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_nic_info.tpl
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

Delete Guest
------------

**DELETE /guests/{userid}**

Delete a guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No Response


Get Guest info
--------------

**GET /guests/{userid}/info**

Get running information of guest.

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

.. restapi_parameters:: parameters.yaml

  - output: guest_nic_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_nic.tpl
   :language: javascript

Create Guest nic
----------------

**POST /guests/{userid}/nic**

Create a virtual nic on giving guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - nic: nic_set_info
  - vdev: vdev_number
  - nic_id: nic_identifier
  - mac_addr: mac_address
  - active: active_flag

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_create_nic.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Create network interface
------------------------

**POST /guests/{userid}/interface**

Create one or more network interfaces on giving guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - interface: network_interface_info
  - os_version: guest_os_version
  - guest_networks: guest_networks_list
  - active: active_flag

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_create_network_interface.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:


Start guest
-----------

Start a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_start_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_start_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Stop guest
----------

Stop a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_stop_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_stop_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Softstop guest
--------------

Stop a guest gracefully, it will firstly shutdown the os on vm, then stop the vm.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_softstop_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_softstop_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Pause guest
-----------

Pause a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_pause_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_pause_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Unpause guest
-------------

Unpause a guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_unpause_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_unpause_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Reboot guest
------------

Reboot a guest, this will use 'reboot' command on the
given guest.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_reboot_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_reboot_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Reset guest
-----------

Reset a guest, this will first gracefully logoff the guest from
z/VM it is running on, then log on the guest and IPL.

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_reset_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_reset_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get guest console output
------------------------

**POST /guests/{userid}/action**

Get console output of the guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_get_console_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_console_output_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  - output: console_output

Deploy guest
------------

**POST /guests/{userid}/action**

After guest created, deploy image onto the guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_deploy_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_deploy_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Capture guest
-------------

**POST /guests/{userid}/action**

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - action: action_capture_guest

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_capture_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

Get Guest power state
---------------------

**GET /guests/{userid}/power_state**

Get power state of the guest.

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

Couple or uncouple nic with vswitch on the guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - vdev: vdev_guest
  - info: couple_info
  - couple: couple_action
  - active: active_flag
  - vswitch: vswitch_name_body_opt

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_couple_uncouple_nic.tpl
   :language: javascript

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
  - active: active_flag

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Host
====

Get info from host (hypervisor) running on.

Get Host Info
-------------

**GET /host**

Get host information.

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

**GET /host/disk/{disk}**

Get disk pool information on the host.

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

Get the list of image info in image repository.

* Request:

.. restapi_parameters:: parameters.yaml

  - imagename: imagename

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: image_info

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

**POST /images**

Create a new image.

* Request:

.. restapi_parameters:: parameters.yaml

  - image: image_dict
  - image_name: image_name
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

Export image
------------

**PUT /images**

Export the image to the specified location.

* Request:

.. restapi_parameters:: parameters.yaml

  - image: image_dict
  - image_name: image_name
  - dest_url: image_url
  - remotehost: remotehost_image

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_export_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: export_image_dict

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_export_res.tpl
   :language: javascript

Get root disk size of image
---------------------------

**GET /images/{name}/root_disk_size**

Get the root disk size of the image.

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

Delete an image.

* Request:

.. restapi_parameters:: parameters.yaml

  - name: image_name

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

VSwitch
=======

Lists, creates, shows details for, updates, and deletes vswitch.

Create vswitch
--------------

**POST /vswitchs**

Create a new vswitch.

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

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_create.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

List vswitchs
-------------

**GET /vswitchs**

List vswitches.

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

Update a vswitch.

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

Delete a vswitch by using given name.

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.
