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


from zvmsdk.tests.functional import base

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import exception


CONF = config.CONF


class SDKVswitchTestCase(base.SDKAPIBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(SDKVswitchTestCase, self).__init__(methodName)
        self.basevm = "TESTVMID"
        self.client = zvmclient.get_zvmclient()
        self.vswitch = "SDKTEST"

    def setUp(self):
        super(SDKVswitchTestCase, self).setUp()
        self.addCleanup(self.sdkapi.vswitch_delete, self.vswitch)

    def _get_vswitch_acc_info(self, vswitch_name):
        # This can only applies to Vlan aware vswitch
        command = "vmcp q vswitch %s acc" % vswitch_name
        rd = self.client.run_commands_on_node(CONF.xcat.zhcp_node, command)
        info = {}
        userid_match = False
        authorized_userids = []
        ports = {}
        info['aware'] = False
        info['userbased'] = True
        info['network_type'] = 'IP'
        for i in range(len(rd)):
            ls = rd[i]
            sec = ls.split(':')
            if ls.__contains__("Default VLAN:"):
                info['aware'] = True
                info['default_porttype'] = sec[-1].strip()
                info['default_vlan'] = sec[-2].split()[0].strip()
                continue
            if ls.__contains__("MAC address:"):
                info['mac'] = sec[2].split()[0]
                continue
            if ls.__contains__("Uplink Port:"):
                userid_match = False
                continue
            if userid_match:
                if 'aware' not in info.keys():
                    continue
                if info['aware']:
                    vlan_id = sec[-1].strip()
                    port_type = sec[-2].split()[0].strip()
                    userid = sec[-3].split()[0].strip()
                    ports[userid] = {'type': port_type,
                                         'vlanid': vlan_id}
                    authorized_userids.append(userid)
                else:
                    authorized_userids.extend(sec[1].strip().split())
                continue
            if ls.__contains__("Authorized userids:"):
                userid_match = True
                continue
            if ls.__contains__("RDEV:"):
                rdev = sec[2].strip().split()[0]
                vdev = sec[3].strip().split()[0]
                controller = sec[4].strip().split()[0]
                info['uplink_port'] = {'rdev': rdev,
                                       'vdev': vdev,
                                       'controller': controller}
                continue
            if ls.__contains__("PORTBASED"):
                info['userbased'] = False
                continue
            if ls.__contains__("ETHERNET"):
                info['network_type'] = 'ETHERNET'
                continue
        info['authorized_users'] = authorized_userids
        info['ports'] = ports
        return info

    def test_vswitch_get_list(self):
        """ Positive test case of vswitch_get_list """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        # Test
        vswitch_list = self.sdkapi.vswitch_get_list()
        self.assertIsInstance(vswitch_list, list)
        self.assertTrue(vswitch_name in vswitch_list)

    def test_vswitch_grant_revoke(self):
        """ Positive test case of vswitch_grant_user and
        vswitch_revoke_user """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        # grant and check
        self.sdkapi.vswitch_grant_user(vswitch_name, self.basevm)
        vsw_info = self._get_vswitch_acc_info(vswitch_name)
        self.assertTrue(('authorized_users' in vsw_info.keys()) and
                        (self.basevm.upper() in vsw_info['authorized_users']))
        # revoke and check
        self.sdkapi.vswitch_revoke_user(vswitch_name, self.basevm)
        vsw_info = self._get_vswitch_acc_info(vswitch_name)
        self.assertTrue(('authorized_users' in vsw_info.keys()) and
                        (self.basevm.upper() not in
                         vsw_info['authorized_users']))

    def test_vswitch_grant_not_exist(self):
        """ Error case of vswitch_grant_user: vswitch not exist """
        # Setup test env
        vswitch_name = self.vswitch
        if vswitch_name in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete(vswitch_name)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_grant_user,
                          vswitch_name, self.basevm)

    def test_vswitch_revoke_not_exist(self):
        """ Error case of vswitch_revoke_user: vswitch not exist """
        # Setup test env
        vswitch_name = self.vswitch
        if vswitch_name in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete(vswitch_name)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_revoke_user,
                          vswitch_name, self.basevm)

    def test_vswitch_set_port_vlanid(self):
        """ Positive case of vswitch_set_port_vlanid """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111', vid=1)
        # Test
        self.sdkapi.vswitch_set_vlan_id_for_user(vswitch_name,
                                                 self.basevm, 1000)
        # Check authorized user and vlanid
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertTrue(('ports' in vsw.keys()) and
                        (self.basevm.upper() in vsw['ports'].keys()))
        self.assertEqual(vsw['ports'][self.basevm.upper()]['vlanid'], '1000')

    def test_vswitch_set_port_invalid_vlanid(self):
        """ Error case of vswitch_set_port_vlanid: vlanid value invalid """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111', vid=1)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_set_vlan_id_for_user,
                          vswitch_name, self.basevm, 0)

    def test_vswitch_set_port_vlanid_vswitch_unaware(self):
        """ Error case of vswitch_set_port_vlanid: vswitch vlan unaware """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_set_vlan_id_for_user,
                          vswitch_name, self.basevm, 1000)

    def test_vswitch_set_port_vlanid_vswitch_not_exist(self):
        """ Error case of vswitch_set_port_vlanid: vswitch not exist """
        # Setup test env
        vswitch_name = self.vswitch
        if vswitch_name in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete(vswitch_name)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_set_vlan_id_for_user,
                          vswitch_name, self.basevm, 1000)

    def test_vswitch_create_vlan_unaware(self):
        """ Positive case of vswitch_create: Vlan unaware"""
        # Test
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertEqual(vsw['aware'], False)
        zhcp_userid = self.client._get_zhcp_userid().upper()
        self.assertListEqual([zhcp_userid], vsw['authorized_users'])
        self.assertEqual(vsw['userbased'], True)
        self.assertIn('uplink_port', vsw.keys())
        self.assertEqual(vsw['uplink_port']['rdev'], '1111.P00')

    def test_vswitch_create_vlan_aware(self):
        """ Positive case of vswitch_create: Vlan aware"""
        # Test
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111', vid=1000)
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertEqual(vsw['aware'], True)
        self.assertEqual(vsw['network_type'], 'ETHERNET')
        self.assertEqual(vsw['userbased'], True)
        self.assertIn('uplink_port', vsw.keys())
        self.assertEqual(vsw['uplink_port']['rdev'], '1111.P00')
        zhcp_userid = self.client._get_zhcp_userid().upper()
        self.assertListEqual([zhcp_userid.upper()], vsw['authorized_users'])
        self.assertTrue(('ports' in vsw.keys()) and
                        (zhcp_userid in vsw['ports'].keys()))
        self.assertEqual(vsw['ports'][zhcp_userid]['vlanid'], '1000')

    def test_vswitch_create_existed_change_vdev(self):
        """ Positive case of vswitch_create: existed vswitch with
        different vdev specified """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        # Test
        self.sdkapi.vswitch_create(vswitch_name, '2222')
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertIn('uplink_port', vsw.keys())
        self.assertEqual(vsw['uplink_port']['rdev'], '2222.P00')

    def test_vswitch_create_long_name(self):
        """ Error case of vswitch_create: name length > 8 """
        # Test
        vswitch_name = "TESTLONGVSWNAME"
        # Default network type is Ethernet, it cann't specify router value
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111')
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())

    def test_vswitch_create_syntax_error(self):
        """ Error case of vswitch_create: wrong argument combination """
        # Test
        vswitch_name = self.vswitch
        # Default network type is Ethernet, it cann't specify router value
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111',
                          router=1)
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())

    def test_vswitch_create_input_error(self):
        """ Error case of vswitch_create: wrong input value """
        # Test
        vswitch_name = self.vswitch
        # Default network type is Ethernet, it cann't specify router value
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111',
                          queue_mem=10)

    def test_vswitch_delete(self):
        """ Positive case of vswitch_delete """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111')
        self.assertIn(vswitch_name, self.sdkapi.vswitch_get_list())
        # Test
        self.sdkapi.vswitch_delete(vswitch_name)
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())

    def test_vswitch_delete_not_exist(self):
        """ Positive case of vswitch_delete: vswitch not exist """
        # Setup test env
        vswitch_name = self.vswitch
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())
        # Test
        self.sdkapi.vswitch_delete(vswitch_name)


class SDKNICTestCase(base.SDKAPIBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(SDKNICTestCase, self).__init__(methodName)
        self.basevm = "NICTEST"
        self.client = zvmclient.get_zvmclient()
        self.vswitch = "VSWTEST"

    def setUp(self):
        super(SDKNICTestCase, self).setUp()
        self.sdkapi.guest_create(self.basevm, 1, 1024)
        self.addCleanup(self.sdkapi.guest_delete, self.basevm)

    def test_guest_create_nic(self):
        """ Test each parameter of guest_create_nic. """
        zhcp_node = self.client._get_hcp_info()['nodename']
        default_vdev = CONF.zvm.default_nic_vdev

        print("Creating NIC with default vdev, not active.")
        self.sdkapi.guest_create_nic(self.basevm, persist=True)
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        # Assert default nic vdev is added into both switch tab and user direct
        self.assertIn(default_vdev, nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF %s TYPE QDIO DEVICES 3') %
                      (zhcp_node, default_vdev), vm_definition)

        print("Creating NIC with fixed vdev.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='3000')
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        # Assert default nic vdev is added into both switch tab and user direct
        self.assertIn('3000', nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF 3000 TYPE QDIO DEVICES 3') % zhcp_node,
                      vm_definition)

        print("Creating NIC without vdev, should use max_vdev+3 as default.")
        self.sdkapi.guest_create_nic(self.basevm)
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        # Assert default nic vdev is added into both switch tab and user direct
        self.assertIn('3003', nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF 3003 TYPE QDIO DEVICES 3') % zhcp_node,
                      vm_definition)

        print("Creating NIC with vdev conflict with defined NIC.")
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.guest_create_nic,
                          self.basevm, vdev='3002')

        # Start test parameter nic_id
        print("Creating NIC with nic_id.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='4000', nic_id='123456')
        # Check the nic_id added in the switch table
        switch_tab = self.client._get_nic_ids()
        nic_id_in_tab = ''
        for e in switch_tab:
            sec = e.split(',')
            userid = sec[0].strip('"')
            interface = sec[4].strip('"')
            if (userid == self.basevm) and (interface == '4000'):
                nic_id_in_tab = sec[2].strip('"')
        self.assertEqual(nic_id_in_tab, '123456')

        # Start test parameter mac_addr
        print("Creating NIC with mac_addr.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='5000',
                                     mac_addr='02:00:00:12:34:56')
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        # Check nic is added to switch table, mac_addr defined in user direct
        self.assertIn('5000', nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF 5000 TYPE QDIO DEVICES 3 MACID 123456') %
                      zhcp_node, vm_definition)

        print("Creating NIC with invalid mac_addr.")
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.guest_create_nic,
                          self.basevm, vdev='5003',
                          mac_addr='123456789012')

        # Start test parameter ip_addr
        print("Creating NIC with management IP.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='6000',
                                     ip_addr='9.60.56.78')
        # Check nic defined in user direct and vswitch table
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        self.assertIn('6000', nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF 6000 TYPE QDIO DEVICES 3') % zhcp_node,
                      vm_definition)
        # Check the management IP is written into hosts table
        ip_in_hosts_table = self.client._get_vm_mgt_ip(self.basevm)
        self.assertEqual(ip_in_hosts_table, '9.60.56.78')

        print("Creating NIC with IP, overwrite the current value in hosts.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='7000',
                                     ip_addr='12.34.56.78')
        # Check the management IP is overwritten to new value
        ip_in_hosts_table = self.client._get_vm_mgt_ip(self.basevm)
        self.assertEqual(ip_in_hosts_table, '12.34.56.78')

        print("Creating NIC with invalid ip_addr.")
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.guest_create_nic,
                          self.basevm, vdev='7003',
                          ip_addr='110.120.255.256')

        # Start test parameter active
        print("Creating NIC to active guest when guest is in off status.")
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_create_nic,
                          self.basevm, vdev='7006',
                          active=True)

        print("Updating guest definition so that it can be started.")
        cmd = ' '.join((
            '/opt/zhcp/bin/smcli Image_Definition_Update_DM',
            "-T %s" % self.basevm,
            "-k 'IPL=VDEV=190'",
            "-k 'LINK=USERID=MAINT VDEV1=0190 MODE=RR'"))
        self.client.run_commands_on_node(zhcp_node, cmd)
        print("Powering on the guest.")
        # Try 5 times to power on the vm.
        for i in range(5):
            try:
                self.sdkapi.guest_start(self.basevm)
            except exception.ZVMXCATInternalError as err:
                err_str = err.format_message()
                if ("Return Code: 396" in err_str and
                        "Reason Code: 59" in err_str):
                    continue
                else:
                    raise
        print("Creating nic to the active guest.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='8000',
                                     active=True, persist=True)
        # Check nic defined in user direct and vswitch table
        nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
        self.assertIn('8000', nic_info.keys())
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        self.assertIn(('%s: NICDEF 8000 TYPE QDIO DEVICES 3') % zhcp_node,
                      vm_definition)
