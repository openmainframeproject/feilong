#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import os
import shutil
import sqlite3
import sys
import tempfile
import types

import mock

from zvmsdk import config
from zvmsdk import database
from zvmsdk import database_migration_md5_to_sha512 as md5_migration
from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk.tests.unit import base


CONF = config.CONF
_PLUGIN_MODULE = 'zvmsdk_test_db_backend_plugin'


class FakeBackend(db_interface.DbBackend):

    def network(self):
        return 'network-op'

    def guest(self):
        return 'guest-op'

    def image(self):
        return 'image-op'

    def fcp(self):
        return 'fcp-op'

    def fcp_ops(self):
        return 'fcp-ops'


class FakeEntryPoint(object):

    def __init__(self, value):
        self.name = 'fake'
        self.value = value

    def load(self):
        module_name, _, attr = self.value.partition(':')
        return getattr(sys.modules[module_name], attr)


class DbBackendLoaderTestCase(base.SDKTestCase):

    def setUp(self):
        super(DbBackendLoaderTestCase, self).setUp()
        self.old_backend = CONF.database.backend
        database._DB_BACKEND = None
        plugin = types.ModuleType(_PLUGIN_MODULE)
        plugin.create = mock.Mock(side_effect=FakeBackend)
        plugin.create_other = FakeBackend
        plugin.create_wrong_type = lambda: object()
        plugin.create_broken = mock.Mock(side_effect=RuntimeError('boom'))
        sys.modules[_PLUGIN_MODULE] = plugin
        self.plugin = plugin
        patcher = mock.patch.object(database, '_find_backend_entry_points',
                                    return_value=[])
        self.find = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        base.set_conf('database', 'backend', self.old_backend)
        database._DB_BACKEND = None
        sys.modules.pop(_PLUGIN_MODULE, None)
        super(DbBackendLoaderTestCase, self).tearDown()

    def _register(self, *factories):
        self.find.return_value = [FakeEntryPoint(_PLUGIN_MODULE + ':' + f)
                                  for f in factories]

    def test_default_is_sqlite(self):
        self.assertEqual('sqlite', self.old_backend)
        backend = database.get_db_backend()
        self.assertIsInstance(backend, database.SqliteBackend)
        self.find.assert_not_called()

    def test_sqlite_backend_returns_reference_operators(self):
        backend = database.get_db_backend()
        self.assertIsInstance(backend.network(), database.NetworkDbOperator)
        self.assertIsInstance(backend.guest(), database.GuestDbOperator)
        self.assertIsInstance(backend.image(), database.ImageDbOperator)
        self.assertIsInstance(backend.fcp(), database.FCPDbOperator)
        self.assertIsInstance(backend.fcp_ops(),
                              db_interface.FcpOperationsBase)

    def test_backend_loaded_once(self):
        backend = database.get_db_backend()
        self.assertIs(backend, database.get_db_backend())

    def test_plugin_backend(self):
        self._register('create')
        base.set_conf('database', 'backend', 'mybackend')
        backend = database.get_db_backend()
        self.assertIsInstance(backend, FakeBackend)
        self.assertEqual('guest-op', backend.guest())
        self.find.assert_called_once_with('mybackend')

    def test_plugin_not_registered(self):
        base.set_conf('database', 'backend', 'mariadb')
        self.assertRaisesRegex(exception.SDKDatabaseException,
                               "zvmsdk.db_backends",
                               database.get_db_backend)
        self.assertIsNone(database._DB_BACKEND)

    def test_dotted_path_is_not_imported(self):
        # a module named in the configuration is never imported
        base.set_conf('database', 'backend', _PLUGIN_MODULE + '.create')
        with mock.patch('importlib.import_module') as import_module:
            self.assertRaises(exception.SDKDatabaseException,
                              database.get_db_backend)
        import_module.assert_not_called()
        self.plugin.create.assert_not_called()

    def test_plugin_registered_twice(self):
        self._register('create', 'create_other')
        base.set_conf('database', 'backend', 'mybackend')
        self.assertRaisesRegex(exception.SDKDatabaseException,
                               "registered more than once",
                               database.get_db_backend)

    def test_plugin_found_twice_same_factory(self):
        self._register('create', 'create')
        base.set_conf('database', 'backend', 'mybackend')
        self.assertIsInstance(database.get_db_backend(), FakeBackend)

    def test_plugin_factory_missing(self):
        self._register('nope')
        base.set_conf('database', 'backend', 'mybackend')
        self.assertRaises(exception.SDKDatabaseException,
                          database.get_db_backend)

    def test_plugin_factory_raises(self):
        self._register('create_broken')
        base.set_conf('database', 'backend', 'mybackend')
        self.assertRaises(exception.SDKDatabaseException,
                          database.get_db_backend)

    def test_plugin_wrong_type(self):
        self._register('create_wrong_type')
        base.set_conf('database', 'backend', 'mybackend')
        self.assertRaises(exception.SDKDatabaseException,
                          database.get_db_backend)
        self.assertIsNone(database._DB_BACKEND)


class DbBackendEntryPointTestCase(base.SDKTestCase):
    """The lookup of a backend registered by an installed package."""

    def setUp(self):
        super(DbBackendEntryPointTestCase, self).setUp()
        site = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, site)
        dist_info = os.path.join(site, 'zvmsdk_test_backend-1.0.dist-info')
        os.mkdir(dist_info)
        with open(os.path.join(dist_info, 'METADATA'), 'w') as f:
            f.write('Metadata-Version: 2.1\nName: zvmsdk-test-backend\n'
                    'Version: 1.0\n')
        with open(os.path.join(dist_info, 'entry_points.txt'), 'w') as f:
            f.write('[zvmsdk.db_backends]\ntestbackend = %s:create\n'
                    % _PLUGIN_MODULE)
        sys.path.insert(0, site)
        self.addCleanup(sys.path.remove, site)
        plugin = types.ModuleType(_PLUGIN_MODULE)
        plugin.create = FakeBackend
        sys.modules[_PLUGIN_MODULE] = plugin
        self.addCleanup(sys.modules.pop, _PLUGIN_MODULE, None)

    def test_registered_backend_is_found(self):
        found = database._find_backend_entry_points('testbackend')
        self.assertEqual(1, len(found))
        self.assertIsInstance(found[0].load()(), FakeBackend)

    def test_other_names_are_not_found(self):
        self.assertEqual([], database._find_backend_entry_points('other'))

    def test_load_registered_backend(self):
        self.assertIsInstance(database._load_db_backend('testbackend'),
                              FakeBackend)


class DbInterfaceTestCase(base.SDKTestCase):

    def test_sqlite_operators_implement_interface(self):
        pairs = [(database.NetworkDbOperator,
                  db_interface.NetworkDbOperatorBase),
                 (database.GuestDbOperator,
                  db_interface.GuestDbOperatorBase),
                 (database.ImageDbOperator,
                  db_interface.ImageDbOperatorBase),
                 (database.FCPDbOperator,
                  db_interface.FCPDbOperatorBase)]
        for impl, iface in pairs:
            self.assertTrue(issubclass(impl, iface))
            # every abstract method has a concrete implementation
            self.assertEqual(frozenset(), impl.__abstractmethods__)

    def test_interface_covers_all_public_methods(self):
        pairs = [(database.NetworkDbOperator,
                  db_interface.NetworkDbOperatorBase),
                 (database.GuestDbOperator,
                  db_interface.GuestDbOperatorBase),
                 (database.ImageDbOperator,
                  db_interface.ImageDbOperatorBase),
                 (database.FCPDbOperator,
                  db_interface.FCPDbOperatorBase)]
        total = 0
        for impl, iface in pairs:
            public = {n for n in vars(impl)
                      if not n.startswith('_') and callable(getattr(impl, n))}
            self.assertEqual(set(), public - set(dir(iface)), impl.__name__)
            total += len(public)
        self.assertEqual(69, total)

    def test_incomplete_backend_cannot_be_created(self):
        class Partial(db_interface.DbBackend):
            def network(self):
                pass

        self.assertRaises(TypeError, Partial)


class DbRowTestCase(base.SDKTestCase):

    def setUp(self):
        super(DbRowTestCase, self).setUp()
        self.row = db_interface.DbRow(('fcp_id', 'connections'),
                                      ('1a00', 2))

    def test_access(self):
        self.assertEqual('1a00', self.row[0])
        self.assertEqual(2, self.row['connections'])
        self.assertEqual(2, self.row['CONNECTIONS'])
        self.assertEqual(2, len(self.row))
        fcp_id, connections = self.row
        self.assertEqual(('1a00', 2), (fcp_id, connections))
        self.assertEqual(['fcp_id', 'connections'], self.row.keys())
        self.assertEqual({'fcp_id': '1a00', 'connections': 2},
                         dict(self.row))
        self.assertEqual(('1a00',), self.row[:1])

    def test_missing_key(self):
        self.assertRaises(IndexError, self.row.__getitem__, 'nope')
        self.assertRaises(IndexError, self.row.__getitem__, 5)

    def test_from_dict_and_equality(self):
        other = db_interface.DbRow.from_dict(
            {'fcp_id': '1a00', 'connections': 2})
        self.assertEqual(self.row, other)
        self.assertEqual(hash(self.row), hash(other))
        self.assertNotEqual(self.row,
                            db_interface.DbRow(('fcp_id',), ('1a00',)))

    def test_length_mismatch(self):
        self.assertRaises(ValueError, db_interface.DbRow, ('a', 'b'), (1,))

    def test_matches_sqlite_row(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        sqlite_row = conn.execute(
            "SELECT '1a00' AS fcp_id, 2 AS connections").fetchone()
        conn.close()
        self.assertEqual(sqlite_row.keys(), self.row.keys())
        self.assertEqual(tuple(sqlite_row), tuple(self.row))
        self.assertEqual(dict(sqlite_row), dict(self.row))
        self.assertEqual(sqlite_row['Connections'], self.row['Connections'])

    def test_duplicate_column_matches_sqlite_row(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        sqlite_row = conn.execute(
            "SELECT 'a' AS tmpl_id, 'b' AS TMPL_ID").fetchone()
        conn.close()
        row = db_interface.DbRow(sqlite_row.keys(), tuple(sqlite_row))
        self.assertEqual(sqlite_row['tmpl_id'], row['tmpl_id'])
        self.assertEqual('a', row['TMPL_ID'])


class Md5MigrationBackendCheckTestCase(base.SDKTestCase):

    def _write_conf(self, text):
        fd, path = tempfile.mkstemp(suffix='.conf')
        with os.fdopen(fd, 'w') as f:
            f.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_backend_default(self):
        path = self._write_conf('[image]\nsdk_image_repository=/x\n')
        self.assertEqual('sqlite', md5_migration.get_db_backend(path))
        self.assertEqual('sqlite',
                         md5_migration.get_db_backend('/no/such/file'))

    def test_refuses_non_sqlite_backend(self):
        path = self._write_conf('[database]\nbackend = mybackend\n')
        argv = ['prog', '--config', path, '--db-path', '/no/such/db']
        with mock.patch.object(sys, 'argv', argv), \
                mock.patch.object(md5_migration,
                                  'migrate_database') as migrate:
            self.assertEqual(1, md5_migration.main())
        migrate.assert_not_called()
