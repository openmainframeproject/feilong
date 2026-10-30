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

    @mock.patch('zvmsdk.smtclient.SMTClient.attach_pcif')
    def test_attach_pcif(self, attach_pcif):
        self.networkops.attach_pcif("fakeid", '00000112', active=True)
        attach_pcif.assert_called_with("fakeid", '00000112', active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.detach_pcif')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    def _zdirect_delete(self, os_version, intf_name, intf_info, execute_cmd,
                        detach_pcif):
        intf_info.return_value = [intf_name]
        self.networkops.zdirect_delete_network_configuration(
            "fakeid", os_version, '00000112', active=True)
        intf_info.assert_called_once_with("fakeid", '00000112')
        detach_pcif.assert_called_once_with("fakeid", '00000112', active=True)
        return execute_cmd

    def test_zdirect_delete_network_configuration_rhel(self):
        execute_cmd = self._zdirect_delete('rhel9.2', 'enc112')
        execute_cmd.assert_called_once_with(
            "fakeid", 'rm -f /etc/sysconfig/network-scripts/ifcfg-enc112')

    def test_zdirect_delete_network_configuration_sles(self):
        execute_cmd = self._zdirect_delete('sles15sp4', 'enc112')
        execute_cmd.assert_called_once_with(
            "fakeid", 'rm -f /etc/sysconfig/network/ifcfg-enc112')

    def test_zdirect_delete_network_configuration_ubuntu20(self):
        execute_cmd = self._zdirect_delete('ubuntu22.04', 'enc112')
        execute_cmd.assert_called_once_with(
            "fakeid", 'rm -f /etc/netplan/enc112.yaml')

    def test_zdirect_delete_network_configuration_ubuntu16(self):
        execute_cmd = self._zdirect_delete('ubuntu16.04', 'enc112')
        execute_cmd.assert_called_once_with(
            "fakeid", 'rm -f /etc/network/interfaces.d/enc112')

    def test_zdirect_delete_network_configuration_rhcos(self):
        # nothing to remove in the guest, the pcif is still detached
        execute_cmd = self._zdirect_delete('rhcos4', 'enc112')
        execute_cmd.assert_not_called()

    @mock.patch('zvmsdk.smtclient.SMTClient.detach_pcif')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    def test_zdirect_delete_network_configuration_guest_cmd_failed(
            self, intf_info, execute_cmd, detach_pcif):
        # the pcif must still be detached if the guest can not be cleaned
        intf_info.side_effect = exception.SDKInternalError(msg="fake")
        self.networkops.zdirect_delete_network_configuration(
            "fakeid", 'rhel9', '00000112', active=True)
        execute_cmd.assert_not_called()
        detach_pcif.assert_called_once_with("fakeid", '00000112',
                                            active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.detach_pcif')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    def test_zdirect_delete_network_configuration_rm_failed(
            self, intf_info, execute_cmd, detach_pcif):
        intf_info.return_value = ['enc112']
        execute_cmd.side_effect = exception.SDKSMTRequestFailed(
            {'overallRC': 1}, "fake")
        self.networkops.zdirect_delete_network_configuration(
            "fakeid", 'rhel9', '00000112', active=True)
        detach_pcif.assert_called_once_with("fakeid", '00000112',
                                            active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.detach_pcif')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    def test_zdirect_delete_network_configuration_inactive(
            self, intf_info, execute_cmd, detach_pcif):
        # no interface in the guest to clean when it is not active
        self.networkops.zdirect_delete_network_configuration(
            "fakeid", 'rhel9', '00000112', active=False)
        intf_info.assert_not_called()
        execute_cmd.assert_not_called()
        detach_pcif.assert_called_once_with("fakeid", '00000112',
                                            active=False)

    @mock.patch('zvmsdk.smtclient.SMTClient.detach_pcif')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    def test_zdirect_delete_network_configuration_unknown_os(
            self, intf_info, execute_cmd, detach_pcif):
        # an unsupported os_version can not stop the pcif detach either
        self.networkops.zdirect_delete_network_configuration(
            "fakeid", 'unknownos1', '00000112', active=True)
        execute_cmd.assert_not_called()
        detach_pcif.assert_called_once_with("fakeid", '00000112',
                                            active=True)

    @mock.patch('zvmsdk.smtclient.SMTClient.guest_reboot')
    @mock.patch('zvmsdk.smtclient.SMTClient.execute_cmd')
    @mock.patch('zvmsdk.smtclient.SMTClient.update_guestdb_with_net_set')
    @mock.patch('zvmsdk.smtclient.SMTClient.punch_file')
    @mock.patch.object(networkops.NetworkOPS,
                       '_generate_zdirect_network_doscript')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_neth_interface_info')
    @mock.patch('zvmsdk.smtclient.SMTClient.is_first_network_config')
    @mock.patch('zvmsdk.smtclient.SMTClient.get_guest_temp_path')
    def _zdirect_config(self, restart, temp_path, is_first, intf_info,
                        doscript, punch, update_db, execute_cmd, reboot):
        temp_path.return_value = '/tmp/fakepath'
        is_first.return_value = False
        intf_info.return_value = ['enc112']
        doscript.return_value = ('/tmp/fakepath/network.doscript',
                                 'service zvmguestconfigure start')
        with mock.patch('shutil.rmtree'):
            self.networkops.zdirect_network_configuration(
                "fakeid", '00000112', [], active=True, restart=restart)
        return execute_cmd, reboot

    def test_zdirect_network_configuration_restart(self):
        execute_cmd, reboot = self._zdirect_config(True)
        reboot.assert_called_once_with("fakeid")

    def test_zdirect_network_configuration_hot_attach(self):
        execute_cmd, reboot = self._zdirect_config(False)
        reboot.assert_not_called()
        cmd = execute_cmd.call_args[0][1]
        # ifup when available, NetworkManager otherwise (RHEL 8 and later)
        self.assertIn('ifup enc112', cmd)
        self.assertIn('nmcli connection reload', cmd)
        self.assertIn('nmcli device connect "enc112"', cmd)

    def test_zdirect_network_configuration_hot_attach_reports_failure(self):
        execute_cmd, reboot = self._zdirect_config(False)
        cmd = execute_cmd.call_args[0][1]
        # a failed bring-up must reach the caller, not be hidden by '|| true'
        self.assertNotIn('true', cmd)

    def test_create_neth_configuration_files_clean_only_first(self):
        net = [{'cidr': '192.168.1.0/24', 'gateway_addr': '192.168.1.1',
                'ip_addr': '192.168.1.5', 'mtu': 1500}]
        files, clean = self.networkops._create_neth_configuration_files(
            net, 'enc112', True)
        self.assertEqual('/etc/sysconfig/network-scripts/ifcfg-enc112',
                         files[0][0])
        self.assertEqual('\nrm -f /etc/sysconfig/network-scripts/ifcfg-en*\n',
                         clean)
        _, clean = self.networkops._create_neth_configuration_files(
            net, 'enc112', False)
        self.assertEqual('', clean)
