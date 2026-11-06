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
from zvmsdk import exception
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

    # ------------------------------------------------------------------
    # zdirect_network_configuration
    # ------------------------------------------------------------------
    @mock.patch.object(shutil, 'rmtree')
    @mock.patch('zvmsdk.smtclient.SMTClient.guest_reboot')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.update_guestdb_with_net_set')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._generate_zdirect_network_doscript')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_first_network_config')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_rhcos')
    def test_zdirect_network_configuration_nonrhcos(
            self, mock_is_rhcos, mock_intf, mock_temp_path, mock_is_first,
            mock_doscript, mock_punch, mock_update_guestdb,
            mock_execute_cmd, mock_reboot, mock_rmtree):
        """Non-RHCOS path punches the doscript, updates guestdb, reboots."""
        mock_is_rhcos.return_value = False
        mock_intf.return_value = 'enc110'
        mock_temp_path.return_value = '/tmp/fakepath'
        mock_is_first.return_value = True
        mock_doscript.return_value = ('/tmp/fakepath/doscript', 'svc_cmd')
        mock_rmtree.return_value = None

        network = {'ip_addr': '192.168.1.10',
                   'gateway_addr': '192.168.1.1',
                   'cidr': '192.168.1.0/24'}
        self.networkops.zdirect_network_configuration(
            'fakeid', 'rhel7', '00000110', network, active=True)

        mock_intf.assert_called_with('fakeid', '00000110')
        mock_doscript.assert_called_once_with(
            'fakeid', 'enc110', 'rhel7', network, '/tmp/fakepath',
            True, active=True)
        mock_punch.assert_called_once_with(
            'fakeid', '/tmp/fakepath/doscript', 'X')
        mock_update_guestdb.assert_called_once_with('fakeid')
        mock_execute_cmd.assert_called_once_with('fakeid', 'svc_cmd')
        mock_reboot.assert_called_once_with('fakeid')
        mock_rmtree.assert_called_once_with('/tmp/fakepath')

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch('zvmsdk.smtclient.SMTClient.guest_reboot')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.update_guestdb_with_net_set')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._generate_zdirect_network_doscript')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_first_network_config')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_rhcos')
    def test_zdirect_network_configuration_not_active(
            self, mock_is_rhcos, mock_intf, mock_temp_path, mock_is_first,
            mock_doscript, mock_punch, mock_update_guestdb,
            mock_execute_cmd, mock_reboot, mock_rmtree):
        """active=False: execute_cmd and reboot are both skipped."""
        mock_is_rhcos.return_value = False
        mock_intf.return_value = 'enc110'
        mock_temp_path.return_value = '/tmp/fakepath'
        mock_is_first.return_value = False
        mock_doscript.return_value = ('/tmp/fakepath/doscript', '')
        mock_rmtree.return_value = None

        network = {'method': 'dhcp'}
        self.networkops.zdirect_network_configuration(
            'fakeid', 'rhel7', '00000110', network, active=False)

        mock_execute_cmd.assert_not_called()
        mock_update_guestdb.assert_not_called()
        mock_reboot.assert_not_called()

    @mock.patch.object(shutil, 'rmtree')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._generate_zdirect_network_doscript')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_first_network_config')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_rhcos')
    def test_zdirect_network_configuration_cleanup_on_generate_error(
            self, mock_is_rhcos, mock_intf, mock_temp_path, mock_is_first,
            mock_doscript, mock_punch, mock_rmtree):
        """The temp folder is removed even if doscript generation fails."""
        mock_is_rhcos.return_value = False
        mock_intf.return_value = 'enc110'
        mock_temp_path.return_value = '/tmp/fakepath'
        mock_is_first.return_value = False
        mock_doscript.side_effect = ValueError('boom')

        self.assertRaises(ValueError,
                          self.networkops.zdirect_network_configuration,
                          'fakeid', 'rhel7', '00000110',
                          {'method': 'dhcp'}, active=True)
        mock_punch.assert_not_called()
        mock_rmtree.assert_called_once_with('/tmp/fakepath')

    @mock.patch('zvmsdk.smtclient.SMTClient.is_rhcos')
    def test_zdirect_network_configuration_rhcos(self, mock_is_rhcos):
        """RHCOS is not supported for zdirect_network_configuration."""
        mock_is_rhcos.return_value = True
        network = {'ip_addr': '192.168.1.10', 'cidr': '192.168.1.0/24'}
        self.assertRaises(exception.SDKFunctionNotImplementError,
                          self.networkops.zdirect_network_configuration,
                          'fakeid', 'rhcos4', '00000110', network, active=True)

    # ------------------------------------------------------------------
    # _generate_zdirect_network_doscript
    # ------------------------------------------------------------------
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_network_doscript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_invokeScript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._add_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_neth_configuration_files')
    def test_generate_zdirect_network_doscript_active(
            self, mock_conf_files, mock_add_file, mock_invoke, mock_doscript):
        """active=True returns doscript path and service command."""
        mock_conf_files.return_value = (
            [('/etc/sysconfig/network-scripts/ifcfg-enc110', 'cfg_content')],
            '')
        mock_doscript.return_value = '/tmp/fakepath/doscript'

        network = {'ip_addr': '192.168.1.10', 'cidr': '192.168.1.0/24'}
        script, cmds = self.networkops._generate_zdirect_network_doscript(
            'fakeid', 'enc110', 'rhel7', network, '/tmp/fakepath',
            first=False, active=True)

        self.assertEqual(script, '/tmp/fakepath/doscript')
        self.assertEqual(cmds, 'systemctl start zvmguestconfigure.service')
        mock_conf_files.assert_called_once_with(
            network, 'rhel7', False, 'enc110')
        mock_invoke.assert_called_once()

    @mock.patch('zvmsdk.networkops.NetworkOPS._create_network_doscript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_invokeScript')
    @mock.patch('zvmsdk.networkops.NetworkOPS._add_file')
    @mock.patch('zvmsdk.networkops.NetworkOPS._create_neth_configuration_files')
    def test_generate_zdirect_network_doscript_not_active(
            self, mock_conf_files, mock_add_file, mock_invoke, mock_doscript):
        """active=False returns doscript path and empty cmds string."""
        mock_conf_files.return_value = (
            [('/etc/sysconfig/network-scripts/ifcfg-enc110', 'cfg_content')],
            '')
        mock_doscript.return_value = '/tmp/fakepath/doscript'

        network = {'method': 'dhcp'}
        script, cmds = self.networkops._generate_zdirect_network_doscript(
            'fakeid', 'enc110', 'rhel7', network, '/tmp/fakepath',
            first=False, active=False)

        self.assertEqual(script, '/tmp/fakepath/doscript')
        self.assertEqual(cmds, '')

    # ------------------------------------------------------------------
    # _create_neth_configuration_files — uses real dist classes
    # ------------------------------------------------------------------
    def test_create_neth_configuration_files_rhel_static_full(self):
        """RHEL: static with ip, gateway, cidr, mtu → correct ifcfg content."""
        network = {'ip_addr': '192.168.1.10',
                   'gateway_addr': '192.168.1.1',
                   'cidr': '192.168.1.0/24',
                   'mtu': 1500,
                   'dns_addr': ['9.0.2.1', '9.0.3.1']}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel7', first=False, intf_name='enc110')

        self.assertEqual(len(files), 1)
        path, cfg_str = files[0]
        self.assertEqual(path,
                         '/etc/sysconfig/network-scripts/ifcfg-enc110')
        self.assertIn('BOOTPROTO="static"', cfg_str)
        self.assertIn('IPADDR="192.168.1.10"', cfg_str)
        self.assertIn('GATEWAY="192.168.1.1"', cfg_str)
        self.assertIn('NETMASK="255.255.255.0"', cfg_str)
        self.assertIn('MTU="1500"', cfg_str)
        self.assertIn('NETTYPE="NETH"', cfg_str)
        self.assertIn('DNS1="9.0.2.1"', cfg_str)
        self.assertIn('DNS2="9.0.3.1"', cfg_str)
        self.assertEqual(clean_cmd, '')

    def test_create_neth_configuration_files_rhel_static_minimal(self):
        """RHEL: static without optional gateway/ip leaves those fields empty."""
        network = {'cidr': '10.0.0.0/8'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel7', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertNotIn('GATEWAY', cfg_str)
        self.assertIn('IPADDR=""', cfg_str)
        self.assertIn('NETMASK="255.0.0.0"', cfg_str)

    def test_create_neth_configuration_files_rhel_slash32_no_broadcast(self):
        """RHEL: /32 has no broadcast address, so BROADCAST is omitted."""
        network = {'ip_addr': '10.0.0.5', 'cidr': '10.0.0.5/32'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel7', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertNotIn('BROADCAST', cfg_str)
        self.assertIn('NETMASK="255.255.255.255"', cfg_str)

    def test_create_neth_configuration_files_rhel_dhcp(self):
        """RHEL: dhcp method — no static IPADDR/GATEWAY/NETMASK fields."""
        network = {'method': 'dhcp'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel7', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertIn('BOOTPROTO="dhcp"', cfg_str)
        self.assertNotIn('IPADDR', cfg_str)
        self.assertNotIn('GATEWAY', cfg_str)
        self.assertNotIn('NETMASK', cfg_str)

    def test_create_neth_configuration_files_rhel_first_sets_clean_cmd(self):
        """RHEL: first=True removes only the specific ifcfg file, not ifcfg-enc*."""
        network = {'method': 'dhcp'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel8', first=True, intf_name='enc110')

        self.assertIn('rm -f', clean_cmd)
        self.assertIn('ifcfg-enc110', clean_cmd)
        # Must NOT wipe all enc* files (would destroy other OSA interfaces)
        self.assertNotIn('ifcfg-enc*', clean_cmd)

    def test_create_neth_configuration_files_first_false_no_clean_cmd(self):
        """first=False: clean_cmd carries no rm command regardless of OS."""
        network = {'method': 'dhcp'}
        for os_ver in ('rhel7', 'sles12', 'ubuntu16', 'ubuntu20'):
            files, clean_cmd = self.networkops._create_neth_configuration_files(
                network, os_ver, first=False, intf_name='enc110')
            self.assertNotIn('rm -f', clean_cmd,
                             'Unexpected rm in clean_cmd for %s first=False' % os_ver)

    def test_create_neth_configuration_files_sles_first_sets_clean_cmd(self):
        """SLES: first=True removes only the specific ifcfg file, not ifcfg-eth*."""
        network = {'method': 'dhcp'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'sles12', first=True, intf_name='enc110')

        self.assertIn('rm -f', clean_cmd)
        self.assertIn('ifcfg-enc110', clean_cmd)
        # Must NOT wipe all eth* files (would destroy other OSA interfaces)
        self.assertNotIn('ifcfg-eth*', clean_cmd)

    def test_create_neth_configuration_files_ubuntu20_first_sets_clean_cmd(self):
        """Ubuntu20: first=True removes only the specific netplan file, not *.yaml."""
        network = {'method': 'dhcp'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu20', first=True, intf_name='enc110')

        self.assertIn('rm -f', clean_cmd)
        self.assertIn('/etc/netplan/60-neth-enc110.yaml', clean_cmd)
        # Must NOT wipe cloud-init or other netplan files
        self.assertNotIn('*.yaml', clean_cmd)

    def test_create_neth_configuration_files_sles_static(self):
        """SLES: static method → SLES-format ifcfg in /etc/sysconfig/network/."""
        network = {'ip_addr': '10.0.0.5',
                   'gateway_addr': '10.0.0.1',
                   'cidr': '10.0.0.0/24'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'sles12', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertEqual(path, '/etc/sysconfig/network/ifcfg-enc110')
        self.assertIn("BOOTPROTO='static'", cfg_str)
        self.assertIn("IPADDR='10.0.0.5'", cfg_str)
        self.assertIn("GATEWAY='10.0.0.1'", cfg_str)
        self.assertIn("NETTYPE='NETH'", cfg_str)
        self.assertIn("STARTMODE='onboot'", cfg_str)

    def test_create_neth_configuration_files_sles_dns(self):
        """SLES: dns_addr → NETCONFIG_DNS_STATIC_SERVERS sed commands in clean_cmd.

        Wicked ignores DNS1=/DNS2= in ifcfg files; the correct mechanism is
        NETCONFIG_DNS_STATIC_SERVERS in /etc/sysconfig/network/config.
        The DNS commands are appended to clean_cmd so they run inside
        invokeScript.sh on both first and subsequent deployments.
        """
        network = {'ip_addr': '10.0.0.5',
                   'gateway_addr': '10.0.0.1',
                   'cidr': '10.0.0.0/24',
                   'dns_addr': ['9.0.2.1', '9.0.3.1']}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'sles12', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        # DNS1=/DNS2= must NOT appear in the ifcfg file — wicked ignores them
        self.assertNotIn('DNS1=', cfg_str)
        self.assertNotIn('DNS2=', cfg_str)
        # DNS must be configured via NETCONFIG_DNS_STATIC_SERVERS
        self.assertIn('NETCONFIG_DNS_STATIC_SERVERS', clean_cmd)
        self.assertIn('9.0.2.1', clean_cmd)
        self.assertIn('9.0.3.1', clean_cmd)
        # The sed command must first strip any existing value (idempotent)
        self.assertIn("sed -i", clean_cmd)
        self.assertIn('/etc/sysconfig/network/config', clean_cmd)

    def test_create_neth_configuration_files_sles_no_dns(self):
        """SLES: no dns_addr → no NETCONFIG_DNS_STATIC_SERVERS in clean_cmd."""
        network = {'ip_addr': '10.0.0.5',
                   'gateway_addr': '10.0.0.1',
                   'cidr': '10.0.0.0/24'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'sles12', first=False, intf_name='enc110')

        self.assertNotIn('NETCONFIG_DNS_STATIC_SERVERS', clean_cmd)

    def test_create_neth_configuration_files_rhel_dns_not_in_clean_cmd(self):
        """RHEL: dns_addr → DNS1=/DNS2= in the ifcfg file, NOT in clean_cmd."""
        network = {'ip_addr': '10.0.0.5',
                   'cidr': '10.0.0.0/24',
                   'dns_addr': ['9.0.2.1']}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'rhel8', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertIn('DNS1="9.0.2.1"', cfg_str)
        # RHEL uses DNS1= in ifcfg; clean_cmd should carry no DNS commands
        self.assertNotIn('NETCONFIG_DNS_STATIC_SERVERS', clean_cmd)

    def test_create_neth_configuration_files_ubuntu16_static(self):
        """Ubuntu16: static method → /etc/network/interfaces.d/ format."""
        network = {'ip_addr': '192.168.2.5',
                   'gateway_addr': '192.168.2.1',
                   'cidr': '192.168.2.0/24',
                   'dns_addr': ['8.8.8.8']}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu16', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertEqual(path, '/etc/network/interfaces.d/enc110')
        self.assertIn('iface enc110 inet static', cfg_str)
        self.assertIn('address 192.168.2.5', cfg_str)
        self.assertIn('gateway 192.168.2.1', cfg_str)
        self.assertIn('dns-nameservers 8.8.8.8', cfg_str)
        self.assertNotIn('mtu', cfg_str)

    def test_create_neth_configuration_files_ubuntu16_no_gateway(self):
        """Ubuntu16: no gateway/broadcast → those lines are omitted."""
        network = {'ip_addr': '192.168.2.5', 'cidr': '192.168.2.5/32'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu16', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertIn('address 192.168.2.5', cfg_str)
        self.assertNotIn('gateway', cfg_str)
        self.assertNotIn('broadcast', cfg_str)

    def test_create_neth_configuration_files_ubuntu16_with_mtu(self):
        """Ubuntu16: writes mtu line only when mtu is provided."""
        network = {'ip_addr': '192.168.2.5',
                    'gateway_addr': '192.168.2.1',
                    'cidr': '192.168.2.0/24',
                    'mtu': 1492}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu16', first=False, intf_name='enc110')

        path, cfg_str = files[0]
        self.assertIn('mtu 1492\n', cfg_str)

    def test_create_neth_configuration_files_ubuntu20_static(self):
        """Ubuntu20: static method → Netplan YAML dict in /etc/netplan/."""
        network = {'ip_addr': '192.168.3.5',
                   'gateway_addr': '192.168.3.1',
                   'cidr': '192.168.3.0/24',
                   'mtu': 1500}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu20', first=False, intf_name='enc110')

        path, cfg = files[0]
        self.assertEqual(path, '/etc/netplan/60-neth-enc110.yaml')
        self.assertIsInstance(cfg, dict)
        self.assertEqual(cfg['network']['version'], 2)
        eth = cfg['network']['ethernets']['enc110']
        self.assertIn('192.168.3.5/24', eth['addresses'])
        self.assertEqual(eth['routes'],
                         [{'to': '0.0.0.0/0', 'via': '192.168.3.1'}])
        self.assertNotIn('gateway4', eth)
        self.assertEqual(eth['mtu'], 1500)

    def test_create_neth_configuration_files_ubuntu20_no_gateway_no_cidr(self):
        """Ubuntu20: no gateway_addr omits gateway4; no cidr omits slash."""
        network = {'ip_addr': '192.168.3.5'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu20', first=False, intf_name='enc110')

        path, cfg = files[0]
        eth = cfg['network']['ethernets']['enc110']
        self.assertEqual(eth['addresses'], ['192.168.3.5'])
        self.assertNotIn('gateway4', eth)
        self.assertNotIn('routes', eth)

    def test_create_neth_configuration_files_ubuntu20_dhcp(self):
        """Ubuntu20: uppercase DHCP method → dhcp4: True in Netplan YAML."""
        network = {'method': 'DHCP'}
        files, clean_cmd = self.networkops._create_neth_configuration_files(
            network, 'ubuntu20', first=False, intf_name='enc110')

        path, cfg = files[0]
        eth = cfg['network']['ethernets']['enc110']
        self.assertTrue(eth.get('dhcp4'))
