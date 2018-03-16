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

General info
************

Content of this package
========================

The zvm cloud connector package (also known as zvm sdk) is a client library
written in pure Python that interacts with `z/VM`_ SMAPI (System management API)
of `IBM Z`_ or `LinuxONE`_ machines. The goal of this package is to make the
z/VM SMAPI easy to be consumed by upper layer programmers and provide a set
of APIs to be called through RESTful interfaces.

.. _IBM Z: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/
.. _z/VM: http://www.vm.ibm.com/

The z/VM SMAPI is the access point for any external tools to
manage the z/VM running on IBM Z or LinuxONE platform. It supports management of
lifecycle and configuration of various platform resources, such as Guest,
CPU, memory, virtual switches, Storage, and more.

Version
=======

This documentation applies to version |release| of the zvm cloud connector package.
You can also see that version in the top left corner of this page.

The zvm cloud connector package uses the rules of `Semantic Versioning 2.0.0`_ for 
its version.

.. _Semantic Versioning 2.0.0: http://semver.org/spec/v2.0.0.html

Compatibility
=============

In this package, compatibility is always seen from the perspective of the user
of the package. Thus, a backwards compatible new version of this package means
that the user can safely upgrade to that new version without encountering
compatibility issues.

This package uses the rules of `Semantic Versioning 2.0.0`_ for compatibility
between package versions, and for :ref:`deprecations <Deprecations>`.

Violations of these compatibility rules are described in section
:ref:`Change log`.

.. _`Deprecations`:

Deprecations
============

Deprecated functionality is marked accordingly in this documentation and in the
:ref:`Change log`

Bug reporting and questions
===========================
If you encounter any problem with this package, please open a bug against
`cloud connector issue tracker`_ or ask question `cloud connector question`_

.. _cloud connector issue tracker: https://bugs.launchpad.net/python-zvm-sdk/+bug
.. _cloud connector question: https://answers.launchpad.net/python-zvm-sdk/

License
=======
This package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://raw.githubusercontent.com/zhmcclient/python-zhmcclient/master/LICENSE
