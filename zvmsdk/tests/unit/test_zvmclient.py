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


from zvmsdk import client
from zvmsdk.config import CONF
from zvmsdk.tests.unit import base


class SDKZVMClientTestCase(base.SDKTestCase):
    """Testcases for compute APIs."""
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self.zvmclient = client.get_zvmclient()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self.zvmclient, client.XCATClient))
