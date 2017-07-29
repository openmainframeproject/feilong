**********
 REST API
**********

This is a reference for the cloudlib4zvm API.

Version
=======

Lists version of this API.

token
=====

Create and validate token.

Guest(s)
========

Lists, creates, shows details for, updates, and deletes guests.

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

  - Sample output:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_host_info.tpl
   :language: javascript

Get Host disk pool info
-----------------------

* GET /host/disk_info/{disk}

  - Request:

  request

  - Response:

  response

  - Sample output:

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

  - Sample output:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_query.tpl
   :language: javascript

Create image
------------

* POST /images

  - Request:

  request

  - Response:

  response

  - Sample output:

Get root disk size of image
---------------------------

* GET /images/{name}/root_disk_size

  - Request:

  request

  - Response:

  response

  - Sample output:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_image_get_root_disk_size.tpl
   :language: javascript

Delete image
------------

* DELETE /images/{name}

  - Request:

  request

  - Response:

  response

  - Sample output:

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

  - Sample output:

  sample output

List vswitchs
-------------

* GET /vswitchs

  - Request:

  request

  - Response:

  response

  - Sample output:

.. literalinclude:: ../../zvmsdk/tests/sdkwsgi/api_templates/test_vswitch_get.tpl
   :language: javascript

Update vswitch
--------------

* PUT /vswitchs/{name}

  - Request:

  request

  - Response:

  response

  - Sample output:

Delete vswitch
--------------

* DELETE /vswitchs/{name}

  - Request:

  request

  - Response:

  response

  - Sample output:
