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

"""The backend contract suite run against the built-in SQLite backend."""

import inspect
import re
import shutil
import tempfile

from zvmsdk import config
from zvmsdk import database
from zvmsdk import db_interface
from zvmsdk.tests.unit import base
from zvmsdk.tests.unit import db_contract


CONF = config.CONF
_CONNS = ('_NETWORK_CONN', '_IMAGE_CONN', '_GUEST_CONN', '_FCP_CONN')


class SqliteFixture(db_contract.BackendFixture):
    """Each test gets new, empty SQLite files in a temporary directory."""

    def create_backend(self):
        db_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, db_dir, True)
        saved = {name: getattr(database, name) for name in _CONNS}
        old_dir = CONF.database.dir

        def restore():
            for name in _CONNS:
                conn = getattr(database, name)
                if conn is not None:
                    conn.close()
                setattr(database, name, saved[name])
            CONF.database.dir = old_dir

        self.addCleanup(restore)
        for name in _CONNS:
            setattr(database, name, None)
        CONF.database.dir = db_dir
        return database.SqliteBackend()


class SqliteNetworkContractTestCase(SqliteFixture, db_contract.NetworkContract,
                                    base.SDKTestCase):
    pass


class SqliteGuestContractTestCase(SqliteFixture, db_contract.GuestContract,
                                  base.SDKTestCase):
    pass


class SqliteImageContractTestCase(SqliteFixture, db_contract.ImageContract,
                                  base.SDKTestCase):
    pass


class SqliteFCPContractTestCase(SqliteFixture, db_contract.FCPContract,
                                base.SDKTestCase):
    pass


class SqliteFcpOperationsContractTestCase(SqliteFixture,
                                          db_contract.FcpOperationsContract,
                                          base.SDKTestCase):
    pass


class ContractCoverageTestCase(base.SDKTestCase):
    """Every interface method is exercised by its contract class."""

    def test_every_method_is_covered(self):
        pairs = [(db_interface.NetworkDbOperatorBase,
                  db_contract.NetworkContract),
                 (db_interface.GuestDbOperatorBase, db_contract.GuestContract),
                 (db_interface.ImageDbOperatorBase, db_contract.ImageContract),
                 (db_interface.FCPDbOperatorBase, db_contract.FCPContract),
                 (db_interface.FcpOperationsBase,
                  db_contract.FcpOperationsContract)]
        for iface, contract in pairs:
            source = inspect.getsource(inspect.getmodule(contract))
            methods = [name for name, _ in inspect.getmembers(
                iface, inspect.isfunction) if not name.startswith('_')]
            missing = [m for m in methods
                       if not re.search(r'\.\s*%s\(' % m, source)]
            self.assertEqual([], missing, contract.__name__)
