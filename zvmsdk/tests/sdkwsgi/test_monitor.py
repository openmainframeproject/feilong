# Copyright 2017 IBM Corp.
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


from zvmsdk.tests.sdkwsgi import base
from zvmsdk.tests.sdkwsgi import test_utils


class MonitorTestCase(base.ZVMConnectorBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(MonitorTestCase, self).__init__(methodName)
        self.test_utils = test_utils.ZVMConnectorTestUtils()
        self.userid1 = None
        self.userid2 = None

    def setUp(self):
        super(MonitorTestCase, self).setUp()

        # create test servers
        try:
            self.userid1 = self.test_utils.guest_deploy()
            self.userid2 = self.test_utils.guest_deploy()
        finally:
            self.addCleanup(self.test_utils.guest_destroy, self.userid1)
            self.addCleanup(self.test_utils.guest_destroy, self.userid2)

    def test_monitor(self):
        self.assertEqual(True, True)
