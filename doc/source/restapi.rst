**********
 REST API
**********

This is a reference for the cloudlib4zvm API.

Version
=======

Lists version of this API.

Get SDK version
---------------

* GET /

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_version.tpl
   :language: javascript

token
=====

Create and validate token.

Guest(s)
========

Lists, creates, shows details for, updates, and deletes guests.

List Guests
-----------

* GET /guests

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_list.tpl
   :language: javascript

Create Guest
------------

* POST /guests

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Get Guests cpu info
-------------------

* GET /guests/cpuinfo

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_cpu_info.tpl
   :language: javascript

Get Guests memory info
----------------------

* GET /guests/meminfo

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_memory_info.tpl
   :language: javascript

Get Guests vnics info
---------------------

* GET /guests/vnicsinfo

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guests_get_vnics_info.tpl
   :language: javascript

Show Guest
----------

* GET /guests/{userid}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get.tpl
   :language: javascript

Update Guest
------------

* PUT /guests/{userid}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Delete Guest
------------

* DELETE /guests/{userid}

  - Request:

  request

  - Response:

  response

  - HTTP status code 204 on Success.

Get Guest info
--------------

* GET /guests/{userid}/info

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_info.tpl
   :language: javascript

Get Guest nic info
------------------

* GET /guests/{userid}/nic

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_nic.tpl
   :language: javascript

Create Guest nic
----------------

* POST /guests/{userid}/nic

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Guest action
------------

* POST /guests/{userid}/action

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Get Guest power state
---------------------

* GET /guests/{userid}/power_state

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_guest_get_power_state.tpl
   :language: javascript

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

Update Guest nic
----------------

* PUT /guests/{userid}/nic/{vdev}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Delete Guest nic
----------------

* DELETE /guests/{userid}/nic/{vdev}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Host
====

Get info from host (hypervisor) running on.

Get Host Info
-------------

* GET /host/info

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_info.tpl
   :language: javascript

Get Host disk pool info
-----------------------

* GET /host/disk_info/{disk}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_disk_info.tpl
   :language: javascript

Image(s)
========

Lists, creates, shows details for, updates, and deletes images.

List images
-----------

* GET /images

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

* POST /images

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Get root disk size of image
---------------------------

* GET /images/{name}/root_disk_size

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_get_root_disk_size.tpl
   :language: javascript

Delete image
------------

* DELETE /images/{name}

  - Request:

  request

  - Response:

  response

  - HTTP status code 204 on Success.

Volume(s)
=========

Lists, creates, shows details for, updates, and deletes volumes.

VSwitch
=======

Lists, creates, shows details for, updates, and deletes vswitch.

Create vswitch
--------------

* POST /vswitchs

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

List vswitchs
-------------

* GET /vswitchs

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_get.tpl
   :language: javascript

Update vswitch
--------------

* PUT /vswitchs/{name}

  - Request:

  request

  - Response:

  response

  - HTTP status code 200 on Success.

Delete vswitch
--------------

* DELETE /vswitchs/{name}

  - Request:

  request

  - Response:

  response

  - HTTP status code 204 on Success.
