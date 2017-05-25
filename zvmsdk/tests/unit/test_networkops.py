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
        self.networkops.create_port("fakeid", "nic_info", "ipaddr")
        create_port.assert_called_with("fakeid", "nic_info", ip_addr="ipaddr")

    @mock.patch.object(zvmclient.XCATClient, 'get_vm_nic_switch_info')
    def test_get_vm_nic_switch_info(self, get_nic_switch_info):
        self.networkops.get_vm_nic_switch_info("fakenode")
        get_nic_switch_info.assert_called_with("fakenode")

    @mock.patch.object(zvmclient.XCATClient, 'update_ports')
    def test_update_ports(self, update_ports):
        self.networkops.update_ports(set())
        update_ports.assert_called_with(set())

    @mock.patch.object(zvmclient.XCATClient, 'get_vswitch_list')
    def test_get_vswitch_list(self, get_vswitch_list):
        self.networkops.get_vswitch_list()
        get_vswitch_list.assert_called_with()

    @mock.patch.object(zvmclient.XCATClient, 'couple_nic_to_vswitch')
    def test_couple_nic_to_vswitch(self, couple_nic_to_vswitch):
        self.networkops.couple_nic_to_vswitch("fake_VS_name", "fake_VS_port",
                                              "fake_userid",
                                              True)
        couple_nic_to_vswitch.assert_called_with("fake_VS_name",
                                                 "fake_VS_port",
                                                 "fake_userid",
                                                 True)

    @mock.patch.object(zvmclient.XCATClient, 'uncouple_nic_from_vswitch')
    def test_uncouple_nic_from_vswitch(self, uncouple_nic_from_vswitch):
        self.networkops.uncouple_nic_from_vswitch("fake_VS_name",
                                                  "fake_VS_port",
                                                  "fake_userid",
                                                  True)
        uncouple_nic_from_vswitch.assert_called_with("fake_VS_name",
                                                     "fake_VS_port",
                                                     "fake_userid",
                                                     True)

    @mock.patch.object(zvmclient.XCATClient, 'add_vswitch')
    def test_add_vswitch(self, add_vswitch):
        self.networkops.add_vswitch("fakename",
                                    "fakerdev",
                                    '*', 1, 8, 0, 2, 0, 1, 1, 2, 1)
        add_vswitch.assert_called_with("fakename",
                                       "fakerdev",
                                       '*', 1, 8, 0, 2, 0, 1, 1, 2, 1)
