================
Name of the spec
================

z/VM SMAPI currency

Problem description
===================

There are a set of SMAPI will be changed, including:

Use Cases
---------

New SMAPI need zthin support.

Proposed change
===============

1) Add zthin support for new SMAPI.
2) Replace old internal use only API with new APIs.

Alternatives
------------

N/A

REST API impact
---------------

No because this is internal use only API.

DB impact
---------

N/A

Security impact
---------------

New APIs will introduce some RACF support in turn enhance security a little bit.

End user impact
---------------------

N/A

Performance Impact
------------------

New APIs should be similar performance to old one.

Upper layer integration impact
------------------------------

N/A

Upgrade impact
--------------

No, only concern here is the z/VM APAR version and z/VM version.

Implementation
==============

Assignee(s)
-----------

Who will work on it?

Work Items
----------

Some break down items on TODO.

Dependencies
============

Any special dependency?

Testing
=======

Any additional test need to be done, such as openstack 3rd party CI?

Documentation Impact
====================

Any document to be updated?
