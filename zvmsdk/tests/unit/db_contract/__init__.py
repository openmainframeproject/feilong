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

"""Contract tests for database backends.

The tests use only the ``zvmsdk.db_interface`` API, so they run against any
backend. To test a backend, mix a fixture that implements
``create_backend()`` into each contract class::

    class MyFixture(db_contract.BackendFixture):
        def create_backend(self):
            # return a DbBackend over an empty store; register clean-up
            # with self.addCleanup()
            ...

    class MyNetworkTest(MyFixture, db_contract.NetworkContract,
                        unittest.TestCase):
        pass

``test_sqlite.py`` runs the suite against the built-in SQLite backend.
"""

from zvmsdk.tests.unit.db_contract.fcp import FCPContract
from zvmsdk.tests.unit.db_contract.fcp_operations import \
    FcpOperationsContract
from zvmsdk.tests.unit.db_contract.guest import GuestContract
from zvmsdk.tests.unit.db_contract.image import ImageContract
from zvmsdk.tests.unit.db_contract.network import NetworkContract
from zvmsdk.tests.unit.db_contract.fixture import BackendFixture


CONTRACTS = (NetworkContract, GuestContract, ImageContract, FCPContract,
             FcpOperationsContract)

__all__ = ['BackendFixture', 'CONTRACTS', 'FCPContract',
           'FcpOperationsContract', 'GuestContract', 'ImageContract',
           'NetworkContract']
