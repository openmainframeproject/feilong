#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2018 IBM Corp.
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
import shutil

from zvmsdk.tests.unit import base
from zvmsdk import dist
from zvmsdk import networkops


class SDKNetworkOpsTestCase(base.SDKTestCase):

    def setUp(self):
        self.networkops = networkops.get_networkops()

    @mock.patch('zvmsdk.smtclient.SMTClient.create_nic')
    def test_create_nic(self, create_nic):
        self.networkops.create_nic("fakeid", '1000', 'Fake_nic_id',
                                   active=True)
        create_nic.assert_called_with("fakeid", vdev='1000',
                                      nic_id='Fake_nic_id',
                                      mac_addr=None, active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.get_vswitch_list')
    def test_get_vswitch_list(self, get_vswitch_list):
        self.networkops.get_vswitch_list()
        get_vswitch_list.assert_called_with()

    @mock.patch('zvmsdk.smtclient.SMTClient.couple_nic_to_vswitch')
    def test_couple_nic_to_vswitch(self, couple_nic_to_vswitch):
        self.networkops.couple_nic_to_vswitch("fake_userid", "nic_vdev",
                                              "fake_VS_name",
                                              active=True, vlan_id=5)
        couple_nic_to_vswitch.assert_called_with("fake_userid",
                                                 "nic_vdev",
                                                 "fake_VS_name",
                                                 vlan_id=5,
                                                 active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.uncouple_nic_from_vswitch')
    def test_uncouple_nic_from_vswitch(self, uncouple_nic_from_vswitch):
        self.networkops.uncouple_nic_from_vswitch("fake_userid",
                                                  "nic_vdev",
                                                  True)
        uncouple_nic_from_vswitch.assert_called_with("fake_userid",
                                                     "nic_vdev",
                                                     active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.add_vswitch')
    def test_add_vswitch(self, add_vswitch):
        self.networkops.add_vswitch("fakename", "fakerdev",
                                    controller='*',
                                    connection='CONNECT',
                                    network_type='ETHERNET',
                                    router="NONROUTER", vid='UNAWARE',
                                    port_type='ACCESS', gvrp='GVRP',
                                    queue_mem=8, native_vid=2, persist=False)
        add_vswitch.assert_called_with("fakename", rdev="fakerdev",
                                       controller='*', connection='CONNECT',
                                       network_type='ETHERNET',
                                       router="NONROUTER",
                                       vid='UNAWARE', port_type='ACCESS',
                                       gvrp='GVRP', queue_mem=8,
                                       native_vid=2, persist=False)

    @mock.patch('zvmsdk.smtclient.SMTClient.grant_user_to_vswitch')
    def test_grant_user_to_vswitch(self, grant_user):
        self.networkops.grant_user_to_vswitch("vswitch_name", "userid")
        grant_user.assert_called_with("vswitch_name", "userid")

    @mock.patch('zvmsdk.smtclient.SMTClient.revoke_user_from_vswitch')
    def test_revoke_user_from_vswitch(self, revoke_user):
        self.networkops.revoke_user_from_vswitch("vswitch_name", "userid")
        revoke_user.assert_called_with("vswitch_name", "userid")

    @mock.patch('zvmsdk.smtclient.SMTClient.set_vswitch_port_vlan_id')
    def test_set_vswitch_port_vlan_id(self, set_vswitch):
        self.networkops.set_vswitch_port_vlan_id("vswitch_name",
                                                 "userid", "vlan_id")
        set_vswitch.assert_called_with("vswitch_name", "userid", "vlan_id")

    @mock.patch('zvmsdk.smtclient.SMTClient.set_vswitch')
    def test_set_vswitch(self, set_vswitch):
        self.networkops.set_vswitch("vswitch_name", grant_userid='fake_id')
        set_vswitch.assert_called_with("vswitch_name", grant_userid='fake_id')

    @mock.patch('zvmsdk.smtclient.SMTClient.delete_vswitch')
    def test_delete_vswitch(self, delete_vswitch):
        self.networkops.delete_vswitch("vswitch_name", True)
        delete_vswitch.assert_called_with("vswitch_name", True)

    @mock.patch('zvmsdk.smtclient.SMTClient.delete_nic')
    def test_delete_nic(self, delete_nic):
        self.networkops.delete_nic("userid", "vdev", True)
        delete_nic.assert_called_with("userid", "vdev",
                                      active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.get_nic_info')
    def test_get_nic_info(self, get_nic_info):
        self.networkops.get_nic_info(userid='testid', vswitch='VSWITCH')
        get_nic_info.assert_called_with(userid='testid', nic_id=None,
                                        vswitch='VSWITCH')

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.update_guestdb_with_net_set')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._generate_network_doscript')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_first_network_config')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    def test_network_configuration(self, temp_path, is_first, doscript, punch,
                                   update_guestdb, execute_cmd, rmtree):
        userid = 'fakeid'
        os_version = 'rhel7.2'
        network_info = []
        network_file_path = '/tmp'
        active_cmds = 'execute command'
        network_doscript = 'file'

        temp_path.return_value = network_file_path
        is_first.return_value = True
        doscript.return_value = (network_doscript, active_cmds)
        rmtree.return_value = None

        self.networkops.network_configuration(userid, os_version, network_info,
                              active=True)
        temp_path.assert_called_with(userid)
        is_first.assert_called_with(userid)
        doscript.assert_called_with(userid, os_version, network_info,
                                    network_file_path, True, active=True)
        punch.assert_called_with(userid, network_doscript, "X")
        update_guestdb.assert_called_with(userid)
        execute_cmd.assert_called_with(userid, active_cmds)

    @mock.patch('zvmsdk.dist.LinuxDistManager.get_linux_dist')
    @mock.patch.object(dist.rhel7, 'create_network_configuration_files')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_znetconfig')
    @mock.patch('zvmsdk.networkops.NetworkOPS._add_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_invokeScript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_network_doscript')
    def test_generate_network_doscript_not_active(self, doscript, invokeScript,
                                    add_file, znetconfig, config, linux_dist):
        net_conf_files = [('target1', 'content1')]
        net_cmd_file = [('target2', 'content2')]
        net_conf_cmds = ''
        clean_cmd = ''
        net_enable = ''
        userid = 'fakeid'
        os_version = 'rhel7.2'
        network_info = []
        first = False
        network_file_path = '/tmp'
        files_and_cmds = net_conf_files, net_conf_cmds, clean_cmd, net_enable
        files_map = []
        files_map.append({'target_path': 'target1',
                        'source_file': "0000"})
        files_map.append({'target_path': 'target2',
                        'source_file': "0001"})
        linux_dist.return_value = dist.rhel7
        config.return_value = files_and_cmds
        znetconfig.return_value = net_cmd_file
        add_file.return_value = None
        invokeScript.return_value = None
        doscript.return_value = 'result1'

        r1, r2 = self.networkops._generate_network_doscript(userid,
                                    os_version, network_info,
                                    network_file_path, first, active=False)
        linux_dist.assert_called_with(os_version)
        config.assert_called_with(network_file_path, network_info,
                                  first, active=False)
        invokeScript.assert_called_with(network_file_path, clean_cmd,
                                        files_map)
        doscript.assert_called_with(network_file_path)

        self.assertEqual(r1, 'result1')
        self.assertEqual(r2, '')

    @mock.patch('zvmsdk.dist.LinuxDistManager.get_linux_dist')
    @mock.patch.object(dist.rhel7, 'create_network_configuration_files')
    @mock.patch.object(dist.rhel7, 'create_active_net_interf_cmd')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_znetconfig')
    @mock.patch('zvmsdk.networkops.NetworkOPS._add_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_invokeScript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_network_doscript')
    def test_generate_network_doscript_active(self, doscript, invokeScript,
                                    add_file, znetconfig, active_cmd,
                                    config, linux_dist):
        net_conf_files = [('target1', 'content1')]
        net_cmd_file = [('target2', 'content2')]
        active_net_cmd = 'create_active_net_interf_cmd'
        net_conf_cmds = ''
        clean_cmd = ''
        net_enable = ''
        userid = 'fakeid'
        os_version = 'rhel7.2'
        network_info = []
        first = False
        network_file_path = '/tmp'
        files_and_cmds = net_conf_files, net_conf_cmds, clean_cmd, net_enable
        files_map = []
        files_map.append({'target_path': 'target1',
                        'source_file': "0000"})
        files_map.append({'target_path': 'target2',
                        'source_file': "0001"})
        linux_dist.return_value = dist.rhel7
        config.return_value = files_and_cmds
        active_cmd.return_value = active_net_cmd
        znetconfig.return_value = net_cmd_file
        add_file.return_value = None
        invokeScript.return_value = None
        doscript.return_value = 'result1'

        r1, r2 = self.networkops._generate_network_doscript(userid,
                                    os_version, network_info,
                                    network_file_path, first, active=True)
        linux_dist.assert_called_with(os_version)
        config.assert_called_with(network_file_path, network_info,
                                  first, active=True)
        invokeScript.assert_called_with(network_file_path, clean_cmd,
                                        files_map)
        doscript.assert_called_with(network_file_path)

        self.assertEqual(r1, 'result1')
        self.assertEqual(r2, active_net_cmd)

    @mock.patch('zvmsdk.smtclient.SMTClient.query_vswitch')
    def test_vswitch_query(self, query_vswitch):
        self.networkops.vswitch_query("vswitch_name")
        query_vswitch.assert_called_with("vswitch_name")

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._add_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_znetconfig')
    @mock.patch.object(dist.rhel7, 'get_network_configuration_files')
    @mock.patch.object(dist.rhel7, 'delete_vdev_info')
    @mock.patch.object(dist.rhel7, 'create_active_net_interf_cmd')
    @mock.patch('zvmsdk.dist.LinuxDistManager.get_linux_dist')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    def test_delete_network_configuration(self, temp_path, linux_dist,
                                          active_cmd, delete_vdev,
                                          get_netconf_files, znetconfig,
                                          add_file, punch, execute_cmd,
                                          rmtree):
        userid = 'fakeid'
        os_version = 'rhel7.2'
        vdev = '1000'

        net_cmd_file = [('target', 'content')]
        active_net_cmd = 'create_active_net_interf_cmd'
        delete_vdev_info = 'delete_vdev_info'
        get_network_configuration_files = 'network_conf_file'
        network_file_path = '/tmp'

        temp_path.return_value = network_file_path
        linux_dist.return_value = dist.rhel7
        active_cmd.return_value = active_net_cmd
        delete_vdev.return_value = delete_vdev_info
        get_netconf_files.return_value = get_network_configuration_files
        znetconfig.return_value = net_cmd_file
        add_file.return_value = None
        rmtree.return_value = None

        self.networkops.delete_network_configuration(userid, os_version, vdev,
                              active=True)
        temp_path.assert_called_with(userid)
        linux_dist.assert_called_with(os_version)
        get_netconf_files.assert_called_with(vdev)
        delete_vdev.assert_called_with(vdev)
        punch.assert_called_with(userid, '/tmp/DEL1000.sh', "X")
        execute_cmd.assert_called_with(userid, active_net_cmd)

    @mock.patch('zvmsdk.smtclient.SMTClient.dedicate_OSA')
    def test_dedicate_OSA(self, dedicate_OSA):
        self.networkops.dedicate_OSA("fakeid", 'F000', vdev='1000',
                                     active=True)
        dedicate_OSA.assert_called_with("fakeid", 'F000', vdev='1000',
                                        active=True)
