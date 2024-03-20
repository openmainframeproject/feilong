..
 Copyright Contributors to the Feilong Project.
 SPDX-License-Identifier: CC-BY-4.0

General info
************

Content of this package
========================

Feilong (also known as python-zvm-sdk) is a client library written in Python
that interacts with `z/VM`_ SMAPI (System management API) of `IBM Z`_ or
`LinuxONE`_ machines. The goal of this package is to make the z/VM SMAPI easy
to be consumed by upper layer programmers and provide a set of APIs to be
called through RESTful interfaces.

.. _IBM Z: https://www.ibm.com/z
.. _LinuxONE: https://www.ibm.com/linuxone
.. _z/VM: https://www.ibm.com/products/zvm

The z/VM SMAPI is the access point for any external tools to
manage the z/VM running on IBM Z or LinuxONE platform. It supports management of
lifecycle and configuration of various platform resources, such as guest,
CPU, memory, virtual switches, disk storage, and more.

Version
=======

This documentation applies to version |release| of the Feilong package (python-zvm-sdk).
You can also see that version in the top left corner of this page.

The Feilong package (python-zvm-sdk) uses the rules of `Semantic Versioning 2.0.0`_ for
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
`Feilong issue tracker`_ or ask question `Feilong question`_

.. _Feilong issue tracker: https://bugs.launchpad.net/python-zvm-sdk/+bug
.. _Feilong question: https://answers.launchpad.net/python-zvm-sdk/

License
=======

This package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://raw.githubusercontent.com/zhmcclient/python-zhmcclient/master/LICENSE
