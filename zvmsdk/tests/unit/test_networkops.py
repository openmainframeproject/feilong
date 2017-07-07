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

    @mock.patch.object(zvmclient.XCATClient, 'create_nic')
    def test_create_nic(self, create_nic):
        self.networkops.create_nic("fakeid", '1000', 'Fake_nic_id', "ipaddr")
        create_nic.assert_called_with("fakeid", vdev='1000',
                                      nic_id='Fake_nic_id', ip_addr="ipaddr")

    @mock.patch.object(zvmclient.XCATClient, 'get_vm_nic_switch_info')
    def test_get_vm_nic_switch_info(self, get_nic_switch_info):
        self.networkops.get_vm_nic_switch_info("fakenode")
        get_nic_switch_info.assert_called_with("fakenode")

    @mock.patch.object(zvmclient.XCATClient, 'get_vswitch_list')
    def test_get_vswitch_list(self, get_vswitch_list):
        self.networkops.get_vswitch_list()
        get_vswitch_list.assert_called_with()

    @mock.patch.object(zvmclient.XCATClient, 'couple_nic_to_vswitch')
    def test_couple_nic_to_vswitch(self, couple_nic_to_vswitch):
        self.networkops.couple_nic_to_vswitch("fake_VS_name", "nic_vdev",
                                              "fake_userid",
                                              True)
        couple_nic_to_vswitch.assert_called_with("fake_VS_name",
                                                 "nic_vdev",
                                                 "fake_userid",
                                                 True)

    @mock.patch.object(zvmclient.XCATClient, 'uncouple_nic_from_vswitch')
    def test_uncouple_nic_from_vswitch(self, uncouple_nic_from_vswitch):
        self.networkops.uncouple_nic_from_vswitch("fake_VS_name",
                                                  "nic_vdev",
                                                  "fake_userid",
                                                  True)
        uncouple_nic_from_vswitch.assert_called_with("fake_VS_name",
                                                     "nic_vdev",
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

    @mock.patch.object(zvmclient.XCATClient, 'grant_user_to_vswitch')
    def test_grant_user_to_vswitch(self, grant_user):
        self.networkops.grant_user_to_vswitch("vswitch_name", "userid")
        grant_user.assert_called_with("vswitch_name", "userid")

    @mock.patch.object(zvmclient.XCATClient, 'revoke_user_from_vswitch')
    def test_revoke_user_from_vswitch(self, revoke_user):
        self.networkops.revoke_user_from_vswitch("vswitch_name", "userid")
        revoke_user.assert_called_with("vswitch_name", "userid")

    @mock.patch.object(zvmclient.XCATClient, 'set_vswitch_port_vlan_id')
    def test_set_vswitch_port_vlan_id(self, set_vswitch):
        self.networkops.set_vswitch_port_vlan_id("vswitch_name",
                                                 "userid", "vlan_id")
        set_vswitch.assert_called_with("vswitch_name", "userid", "vlan_id")

    @mock.patch.object(zvmclient.XCATClient, 'update_nic_definition')
    def test_update_nic_definition(self, add_nic):
        self.networkops.update_nic_definition("user_id", "nic_vdev",
                                              "mac", "switch_name")
        add_nic.assert_called_with("user_id", "nic_vdev",
                                   "mac", "switch_name")

    @mock.patch.object(zvmclient.XCATClient, 'set_vswitch')
    def test_set_vswitch(self, set_vswitch):
        self.networkops.set_vswitch("vswitch_name", grant_userid='fake_id')
        set_vswitch.assert_called_with("vswitch_name", grant_userid='fake_id')

    @mock.patch.object(zvmclient.XCATClient, 'delete_vswitch')
    def test_delete_vswitch(self, delete_vswitch):
        self.networkops.delete_vswitch("vswitch_name", 2)
        delete_vswitch.assert_called_with("vswitch_name", 2)
