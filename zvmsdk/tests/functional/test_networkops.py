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
        info['uplink_port'] = {}
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
                info['uplink_port'][rdev] = {'vdev': vdev,
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
        self.assertListEqual(['1111.P00'], vsw['uplink_port'].keys())

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
        self.assertListEqual(['1111.P00'], vsw['uplink_port'].keys())
        zhcp_userid = self.client._get_zhcp_userid().upper()
        self.assertListEqual([zhcp_userid.upper()], vsw['authorized_users'])
        self.assertTrue(('ports' in vsw.keys()) and
                        (zhcp_userid in vsw['ports'].keys()))
        self.assertEqual(vsw['ports'][zhcp_userid]['vlanid'], '1000')

    def test_vswitch_create_multiple_rdev(self):
        """ Positive case of vswitch_create: multiple rdev"""
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, rdev='1111 22 33')
        # Test
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertIn('uplink_port', vsw.keys())
        self.assertListEqual(vsw['uplink_port'].keys(),
                             ['1111.P00', '0022.P00', '0033.P00'])

    def test_vswitch_create_existed_change_rdev(self):
        """ Positive case of vswitch_create: existed vswitch with
        different rdev specified """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '1111 0022 333')
        # Test
        self.sdkapi.vswitch_create(vswitch_name, '2222 1111 333')
        vsw = self._get_vswitch_acc_info(vswitch_name)
        self.assertIn('uplink_port', vsw.keys())
        self.assertListEqual(vsw['uplink_port'].keys,
                             ['2222.P00', '1111.P00', '0333.P00'])

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

    def test_vswitch_create_invalid_rdev(self):
        """ Error case of vswitch_create: invalid rdev """
        # Test
        vswitch_name = self.vswitch
        # Default network type is Ethernet, it cann't specify router value
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111 2222 3333 4444')
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())

    def test_vswitch_create_input_error(self):
        """ Error case of vswitch_create: wrong input value """
        # Test
        vswitch_name = self.vswitch
        # Queue_mem should be in range 1-8
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
