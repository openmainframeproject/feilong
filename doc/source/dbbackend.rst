..
 Copyright Contributors to the Feilong Project.
 SPDX-License-Identifier: CC-BY-4.0

.. _`database backends`:

Database Backends
*****************

Feilong keeps its data (NIC bindings, guests, images, FCP devices and FCP
Multipath Templates) in a database. By default this is four SQLite files in
the directory set by ``dir`` in the ``[database]`` section of
``zvmsdk.conf``.

The ``backend`` option of the same section lets a deployment replace SQLite
with another implementation, for example one that stores the data in a
central service. Feilong itself ships only the SQLite backend.

Selecting a backend
===================

.. code-block:: text

    [database]
    # the default: local SQLite files under 'dir'
    backend = sqlite

    # or the name of a backend registered by an installed package
    backend = mybackend

Any value other than ``sqlite`` must be the name of an entry point in the
``zvmsdk.db_backends`` group. The package that provides the backend
registers it when it is installed, for example in its ``setup.py``:

.. code-block:: python

    entry_points={
        'zvmsdk.db_backends': [
            'mybackend = mypackage.zvmsdk_backend:create',
        ],
    },

The entry point is a factory: a callable that takes no arguments and returns
a ``zvmsdk.db_interface.DbBackend``. Feilong loads it once per process, the
first time it needs the database. If no installed package registers the
name, two packages register it with different factories, the factory cannot
be loaded or raises, or it returns something that is not a ``DbBackend``,
the database call fails with ``SDKDatabaseException`` naming the configured
value.

Notes:

* Leaving ``backend`` unset, or setting it to ``sqlite``, keeps today's
  behaviour: same files, schema and locking.
* Changing the backend does not move any data. Copying existing data into
  a new backend is the job of whoever provides that backend.
* Tools that work on the SQLite files directly, such as
  ``zvmsdk/database_migration_md5_to_sha512.py``, refuse to run when
  ``backend`` is not ``sqlite``.

Security
========

A backend is Python code that runs inside the Feilong processes
(``sdkserver``, the REST API and the command line tools), with their
privileges, and it sees all the data Feilong keeps. Choosing a backend is
the same as choosing code to run as the SDK, so:

* Keep ``zvmsdk.conf`` owned by root and not writable by anybody else.
  Whoever can change ``backend`` there chooses which installed backend
  Feilong runs.
* Install backends only from trusted packages, into root-owned locations on
  the Python path of the SDK processes. Feilong loads only a backend that an
  installed package registered in ``zvmsdk.db_backends``; it never imports a
  module named in the configuration. Anybody who can install a package, or
  put a module earlier on that Python path, can still run code as the SDK,
  backend or not.
* A backend that keeps the data in another process or on another host must
  authenticate that peer and protect the data in transit, since that data
  includes the FCP devices and WWPNs used for volume attachment.

Writing a backend
=================

A backend implements the abstract classes in ``zvmsdk.db_interface``. The
SQLite classes in ``zvmsdk.database`` are the reference implementation, and
a backend must behave the same way.

``DbBackend``
    Has the methods ``network()``, ``guest()``, ``image()``, ``fcp()`` and
    ``fcp_ops()``, returning a ``NetworkDbOperatorBase``,
    ``GuestDbOperatorBase``, ``ImageDbOperatorBase``, ``FCPDbOperatorBase``
    and ``FcpOperationsBase``. Each call may return a new object or a shared
    one; the objects must be safe to use from several threads.

Operators
    Method names, arguments and return shapes are those of
    ``NetworkDbOperator``, ``GuestDbOperator``, ``ImageDbOperator`` and
    ``FCPDbOperator`` in ``zvmsdk.database``. Each method call must be
    atomic by itself: Feilong opens no database transaction outside the
    backend.

Rows
    Rows must behave like ``sqlite3.Row``: access by index, by column name
    (case-insensitive), unpacking, ``keys()`` and ``dict(row)``. A backend
    that does not return ``sqlite3.Row`` can use ``zvmsdk.db_interface.DbRow``.

Errors
    Raise the same Feilong exceptions as the SQLite implementation, for
    example ``SDKObjectNotExistError``, ``SDKConflictError``,
    ``SDKNetworkOperationError``, ``SDKGuestOperationError`` and
    ``SDKDatabaseException``, so that callers need no change.

FCP operations
--------------

FCP volume code needs several FCP database calls to be atomic together.
These are grouped into the operations of ``FcpOperationsBase``, and each one
must run as a single transaction in the backend:

* ``increase_connections(fcp_list, assigner_id)``
* ``decrease_connections(fcp_list)``
* ``allocate(assigner_id, fcp_template_id, sp_name, pchid_info, zvm_fcps=None)``
* ``release(assigner_id, fcp_template_id)``
* ``sync_with_zvm(zvm_fcps)``
* ``get_pchid_usage()``

None of them calls z/VM. The z/VM state they need is passed in as
``zvm_fcps``, a dict keyed by lowercase FCP ID whose values are
``(fcp_id, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner)`` sequences.

``allocate`` works in two passes, so that z/VM is queried only when needed
and never inside a database transaction:

1. Called without ``zvm_fcps``, it returns the FCP devices already allocated
   to the assigner, if any. Otherwise it changes nothing and returns
   ``(NEED_ZVM_SYNC, fcp_template_id)`` with the resolved template ID.
2. The caller queries z/VM and calls ``allocate`` again with ``zvm_fcps``
   and that template ID. The backend syncs the FCP data with ``zvm_fcps``
   and reserves new FCP devices, in one transaction.

Within one process, Feilong holds a lock from each z/VM FCP query until its
result is applied, by ``allocate`` or ``sync_with_zvm``. The FCP data is
therefore always synced with z/VM snapshots in the order they were taken,
and a slower request cannot apply an older snapshot over a newer one.

``zvmsdk.fcp_ops.TransactionalFcpOperations(db, transaction)`` implements
these operations on top of any ``FCPDbOperatorBase`` and a ``transaction``
callable that returns a nestable context manager running its body as one
transaction. A backend that keeps its data in another process can run it
there with its own FCP operator and transaction, instead of rewriting the
FCP logic.

Testing a backend
=================

``zvmsdk/tests/unit/db_contract`` holds contract tests that use only the
``zvmsdk.db_interface`` API. To run them against a backend, provide a
fixture that returns the backend over an empty store and mix it into each
contract class:

.. code-block:: python

    import unittest

    from zvmsdk.tests.unit import db_contract


    class MyFixture(db_contract.BackendFixture):

        def create_backend(self):
            # a DbBackend over an empty store; register clean-up with
            # self.addCleanup()
            ...


    class MyFCPContractTest(MyFixture, db_contract.FCPContract,
                            unittest.TestCase):
        pass

``db_contract.CONTRACTS`` lists all contract classes.
``zvmsdk/tests/unit/db_contract/test_sqlite.py`` runs them against the SQLite
backend.
