General info
************

This section provides answers to frequent asked questions.

FAQ
===

Change default NIC address
--------------------------

For NIC address on to be created VM, the default value 1000 is defined by zVM
Cloud connector configuration file, generally it is defined by ``default_nic_vdev``
item of ``zvm`` section in ``/etc/zvmsdk/zvmsdk.conf``.

If you want to create a VM with different value, change it to any integer you
want and make sure no conflict to other address then restart the z/VM cloud connector.

Log on through 3270 or PCOM terminal
------------------------------------

Currently, z/VM cloud connector doesn't support to set a password for virtual machine
(the definition in user directory), it is designed from a security perspective.
Only the administrator has the authority to logon the virtual machine through x3270
or PCOM, the common user is only allowed to connect to guest through network
(ssh with id and password)

Refer to ``default_admin_userid`` configuration in ``zvm`` section for more detail info.
