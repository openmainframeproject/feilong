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

import mock

from zvmsdk.tests.unit import base
from zvmsdk import client as zvmclient
from zvmsdk import networkops


class SDKNetworkOpsTestCase(base.SDKTestCase):

    def setUp(self):
        self.networkops = networkops.get_networkops()

    @mock.patch.object(zvmclient.XCATClient, 'create_port')
    def test_create_port(self, create_port):
        self.networkops.create_port("fakeid", "fake_nic_id",
                                    "fake_mac", "fake_nic_vdev")
        create_port.assert_called_with("fakeid", "fake_nic_id",
                                       "fake_mac", "fake_nic_vdev")

    @mock.patch.object(zvmclient.XCATClient, 'update_ports')
    def test_update_ports(self, update_ports):
        self.networkops.update_ports(set())
        update_ports.assert_called_with(set())
