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

    @mock.patch.object(zvmclient.XCATClient, 'get_vm_nic_switch_info')
    def test_get_vm_nic_switch_info(self, get_nic_switch_info):
        self.networkops.get_vm_nic_switch_info("fakenode")
        get_nic_switch_info.assert_called_with("fakenode")

    @mock.patch.object(zvmclient.XCATClient, 'preset_vm_network')
    def test_preset_vm_network(self, preset_vm_network):
        self.networkops.preset_vm_network("fake_id", "fake_ip")
        preset_vm_network.assert_called_with("fake_id", "fake_ip")

    @mock.patch.object(zvmclient.XCATClient, 'host_get_port_list')
    def test_host_get_port_list(self, get_port):
        self.networkops.host_get_port_list()
        get_port.assert_called_with()

    @mock.patch.object(zvmclient.XCATClient, 'clean_network_resource')
    def test_clean_network_resource(self, clean_network_resource):
        self.networkops.clean_network_resource("fake_user_id")
        clean_network_resource.assert_called_with("fake_user_id")

    @mock.patch.object(zvmclient.XCATClient, 'get_admin_created_vsw')
    def test_get_admin_created_vsw(self, get_admin_created_vsw):
        self.networkops.get_admin_created_vsw()
        get_admin_created_vsw.assert_called_with()

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

    @mock.patch.object(zvmclient.XCATClient, 'port_bound')
    def test_vswitch_bound_port(self, port_bound):
        self.networkops.vswitch_bound_port("port_id", "network_type",
                                          "physical_network",
                                          "segmentation_id", "userid")
        port_bound.assert_called_with("port_id", "network_type",
                                      "physical_network",
                                      "segmentation_id", "userid")

    @mock.patch.object(zvmclient.XCATClient, 'port_unbound')
    def test_vswitch_unbound_port(self, port_unbound):
        self.networkops.vswitch_unbound_port("port_id", "physical_network",
                                             "userid")
        port_unbound.assert_called_with("port_id", "physical_network",
                                        "userid")

    @mock.patch.object(zvmclient.XCATClient, 'vswitch_update_port_info')
    def vswitch_update_port_info(self, vswitch_update_port_info):
        self.networkops.vswitch_update_port_info("port_id",
                                                 "switch_name",
                                                 "vlan")
        vswitch_update_port_info.assert_called_with("port_id",
                                                    "switch_name",
                                                    "vlan")

    @mock.patch.object(zvmclient.XCATClient, 'guest_port_get_user_info')
    def test_guest_port_get_user_info(self, get_port_info):
        self.networkops.guest_port_get_user_info("port_id")
        get_port_info.assert_called_with("port_id")

    @mock.patch.object(zvmclient.XCATClient, 'host_put_user_direct_online')
    def test_host_put_user_direct_online(self, put_online):
        self.networkops.host_put_user_direct_online()
        put_online.assert_called_with()

    @mock.patch.object(zvmclient.XCATClient, 'host_add_nic_to_user_direct')
    def test_host_add_nic_to_user_direct(self, add_nic):
        self.networkops.host_add_nic_to_user_direct("user_id", "port_id",
                                                    "mac", "switch_name")
        add_nic.assert_called_with("user_id", "port_id",
                                   "mac", "switch_name")
