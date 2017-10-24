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
from zvmsdk import networkops


class SDKNetworkOpsTestCase(base.SDKTestCase):

    def setUp(self):
        self.networkops = networkops.get_networkops()

    @mock.patch.object(networkops.get_networkops()._smutclient, 'create_nic')
    def test_create_nic(self, create_nic):
        self.networkops.create_nic("fakeid", '1000', 'Fake_nic_id',
                                   ip_addr="ipaddr",
                                   active=True)
        create_nic.assert_called_with("fakeid", vdev='1000',
                                      nic_id='Fake_nic_id',
                                      mac_addr=None, ip_addr="ipaddr",
                                      active=True)

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'get_vm_nic_vswitch_info')
    def test_get_vm_nic_vswitch_info(self, get_nic_vswitch_info):
        self.networkops.get_vm_nic_vswitch_info("fakenode")
        get_nic_vswitch_info.assert_called_with("fakenode")

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'get_vswitch_list')
    def test_get_vswitch_list(self, get_vswitch_list):
        self.networkops.get_vswitch_list()
        get_vswitch_list.assert_called_with()

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'couple_nic_to_vswitch')
    @mock.patch('zvmsdk.utils._is_guest_exist')
    def test_couple_nic_to_vswitch(self, ige, couple_nic_to_vswitch):
        ige.return_value = True
        self.networkops.couple_nic_to_vswitch("fake_userid", "nic_vdev",
                                              "fake_VS_name",
                                              True)
        couple_nic_to_vswitch.assert_called_with("fake_userid",
                                                 "nic_vdev",
                                                 "fake_VS_name",
                                                 active=True)

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'uncouple_nic_from_vswitch')
    @mock.patch('zvmsdk.utils._is_guest_exist')
    def test_uncouple_nic_from_vswitch(self, ige, uncouple_nic_from_vswitch):
        ige.return_value = True
        self.networkops.uncouple_nic_from_vswitch("fake_userid",
                                                  "nic_vdev",
                                                  True)
        uncouple_nic_from_vswitch.assert_called_with("fake_userid",
                                                     "nic_vdev",
                                                     active=True)

    @mock.patch.object(networkops.get_networkops()._smutclient, 'add_vswitch')
    def test_add_vswitch(self, add_vswitch):
        self.networkops.add_vswitch("fakename", "fakerdev",
                                    controller='*',
                                    connection='CONNECT', network_type='IP',
                                    router="NONROUTER", vid='UNAWARE',
                                    port_type='ACCESS', gvrp='GVRP',
                                    queue_mem=8, native_vid=2, persist=False)
        add_vswitch.assert_called_with("fakename", rdev="fakerdev",
                                       controller='*', connection='CONNECT',
                                       network_type='IP', router="NONROUTER",
                                       vid='UNAWARE', port_type='ACCESS',
                                       gvrp='GVRP', queue_mem=8,
                                       native_vid=2, persist=False)

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'grant_user_to_vswitch')
    def test_grant_user_to_vswitch(self, grant_user):
        self.networkops.grant_user_to_vswitch("vswitch_name", "userid")
        grant_user.assert_called_with("vswitch_name", "userid")

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'revoke_user_from_vswitch')
    def test_revoke_user_from_vswitch(self, revoke_user):
        self.networkops.revoke_user_from_vswitch("vswitch_name", "userid")
        revoke_user.assert_called_with("vswitch_name", "userid")

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'set_vswitch_port_vlan_id')
    def test_set_vswitch_port_vlan_id(self, set_vswitch):
        self.networkops.set_vswitch_port_vlan_id("vswitch_name",
                                                 "userid", "vlan_id")
        set_vswitch.assert_called_with("vswitch_name", "userid", "vlan_id")

    @mock.patch.object(networkops.get_networkops()._smutclient, 'set_vswitch')
    def test_set_vswitch(self, set_vswitch):
        self.networkops.set_vswitch("vswitch_name", grant_userid='fake_id')
        set_vswitch.assert_called_with("vswitch_name", grant_userid='fake_id')

    @mock.patch.object(networkops.get_networkops()._smutclient,
                       'delete_vswitch')
    def test_delete_vswitch(self, delete_vswitch):
        self.networkops.delete_vswitch("vswitch_name", True)
        delete_vswitch.assert_called_with("vswitch_name", True)

    @mock.patch.object(networkops.get_networkops()._smutclient, 'delete_nic')
    def test_delete_nic(self, delete_nic):
        self.networkops.delete_nic("userid", "vdev", True)
        delete_nic.assert_called_with("userid", "vdev",
                                      active=True)
