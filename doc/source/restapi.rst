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
(This document is a beta version now)

Version
=======
Lists version of this API.

Get zvm cloud connector version
-------------------------------

**GET /**

* Request:

  No parameters needed.

* Response code:

  HTTP status code 200 on success.

* Response contents:

  Return the version of the zvm cloud connect API.

.. restapi_parameters:: parameters.yaml

  - output : ret_output
  - api_version: api_version_sdk
  - min_version: min_version_sdk
  - max_version: max_version_sdk
  - version: version_sdk

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_version.tpl
   :language: javascript

Token
=====

Create token
------------

**POST /token**

Get a valid token to perform further request by using user and password.

* Request:

.. restapi_parameters:: parameters.yaml

  - X-Admin-Token: token_admin

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

List names of all the VMs on this host

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

Create a vm in z/VM

* Request:

.. restapi_parameters:: parameters.yaml

  - guest: guest_dict
  - userid: userid_create
  - vcpus: guest_vcpus
  - memory: guest_memory
  - user_profile: user_profile_guest
  - disk_list: disk_list_guest
  - size: size_disk
  - format: format_disk
  - is_boot_disk: is_boot_disk
  - disk_pool: disk_pool_guest
    

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
  - disk_list: disk_list_guest
  - size: size_disk
  - format: format_disk
  - is_boot_disk: is_boot_disk
  - disk_pool: disk_pool_guest

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
  - userid: nic_userid
  - interface: nic_interface
  - switch: vswitch_name_body
  - port: nic_port
  - comments: nic_comments

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
  - max_mem_kb: guest_memory_kb_max
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

Delete network interface
------------------------

**DELETE /guests/{userid}/interface**

Delete one network interface on giving guest.

* Request:

.. restapi_parameters:: parameters.yaml

  - userid: guest_userid
  - interface: network_interface_info
  - os_version: guest_os_version
  - vdev: nic_interface
  - active: active_flag

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_delete_network_interface.tpl
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
  - image: image_name
  - transportfiles: transportfiles
  - remotehost: remotehost_transportfiles
  - vdev: deploy_vdev

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
  - image: image_name
  - capturetype: capture_type
  - compresslevel: compress_level

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
  - imagename: image_name
  - imageosdistro: guest_os_version
  - md5sum: image_md5sum
  - disk_size_units: root_disk_size_image
  - image_size_in_bytes: physical_disk_size_image
  - type: image_type
  - comments: image_comments

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

**POST /images**

Import an image into image repository

* Request:

.. restapi_parameters:: parameters.yaml

  - image: image_dict
  - image_name: image_name
  - url: image_import_url
  - image_meta: image_metadata
  - remote_host: remotehost_image_import

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
  - dest_url: image_export_url
  - remote_host: remotehost_image_export

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

Lists, creates, updates, and deletes vswitch.

Create vswitch
--------------

**POST /vswitches**

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

List vswitches
--------------

**GET /vswitches**

Get the list of vswitch name on the host

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

GET vswitch details
-------------------

**GET /vswitches/{name}**

Get the details of a vswitch

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name

* Response code:

  HTTP status code 200 on success.

* Response contents:

.. restapi_parameters:: parameters.yaml

  - output: vswitch_details

* Response sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_query.tpl
   :language: javascript

Grant user to vswitch
---------------------

**PUT /vswitches/{name}**

Grant an user to access vswitch

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name
  - vswitch: vswitch_info
  - grant_userid: guest_userid

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_update_req.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Revoke user from vswitch
------------------------

**PUT /vswitches/{name}**

Revoke the user access from vswitch

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name
  - vswitch: vswitch_info
  - revoke_userid: guest_userid

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_update_revoke.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Set user VLANID to vswitch
--------------------------

**PUT /vswitches/{name}**

Set vlan id for user when connecting to the vswitch

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name
  - vswitch: vswitch_info
  - user_vlan_id: user_vlan_id
  - userid: guest_userid
  - vlanid: vlan_id

* Request sample:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_set_vlan.tpl
   :language: javascript

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.

Delete vswitch
--------------

**DELETE /vswitches/{name}**

Delete a vswitch by using given name.

* Request:

.. restapi_parameters:: parameters.yaml

  - name: vswitch_name

* Response code:

  HTTP status code 200 on success.

* Response contents:

  No response.
