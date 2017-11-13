====================
Sample for using sdk
====================

Sample
------

There's a sample file inside zvm sdk's source tree (tools/sample.py)
A couple of configuration items need to be modified such as
IP address, disk pool name etc, then use python to run
the command like following to deploy a new guest::

   import sample
   sample.run_guest()

Here's the code:

.. include:: ../../tools/sample.py
   :literal:
