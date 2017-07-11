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
        vsw_info = self.client.query_vswitch(vswitch_name)
        self.assertIn(self.basevm.upper(), vsw_info['authorized_users'])
        # revoke and check
        self.sdkapi.vswitch_revoke_user(vswitch_name, self.basevm)
        vsw_info = self.client.query_vswitch(vswitch_name)
        self.assertNotIn(self.basevm.upper(), vsw_info['authorized_users'])

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
        vsw = self.client.query_vswitch(vswitch_name)
        self.assertIn(self.basevm.upper(), vsw['authorized_users'])
        self.assertEqual(
            vsw['authorized_users'][self.basevm.upper()].vlan_count, 1)
        self.assertListEqual(
            vsw['authorized_users'][self.basevm.upper()].vlan_ids,
            ['1000'])

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
        self.sdkapi.vswitch_create(vswitch_name, rdev='1111',
                                   controller='FAKEVMID', connection='CONNECT',
                                   network_type='IP', router='NONrouter',
                                   vid='UNAWARE', port_type='ACCESS',
                                   gvrp='NOGVRP', queue_mem=3, native_vid=1,
                                   persist=False)
        vsw = self.client.query_vswitch(vswitch_name)
        self.assertEqual(vsw['switch_name'], vswitch_name)
        self.assertEqual(vsw['transport_type'], 'IP')
        self.assertEqual(vsw['port_type'], 'ACCESS')
        self.assertEqual(vsw['queue_memory_limit'], '3')
        self.assertEqual(vsw['vlan_awareness'], 'UNAWARE')
        self.assertEqual(vsw['gvrp_request_attribute'], 'NOGVRP')
        self.assertEqual(vsw['user_port_based'], 'USERBASED')
        self.assertDictEqual(vsw['authorized_users'], {})
        self.assertIn('1111', vsw['real_devices'].keys())

    def test_vswitch_create_vlan_aware(self):
        """ Positive case of vswitch_create: Vlan aware"""
        # Test
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, rdev='1111,2222',
                                   controller='FAKEVMID',
                                   connection='DISCONnect',
                                   network_type='ETHERNET', router='PRIrouter',
                                   vid=1000, port_type='TRUNK',
                                   gvrp='GVRP', queue_mem=5, native_vid=1,
                                   persist=True)
        vsw = self.client.query_vswitch(vswitch_name)
        self.assertEqual(vsw['switch_name'], vswitch_name)
        self.assertEqual(vsw['transport_type'], 'ETHERNET')
        self.assertEqual(vsw['port_type'], 'TRUNK')
        self.assertEqual(vsw['queue_memory_limit'], '5')
        self.assertEqual(vsw['vlan_awareness'], 'AWARE')
        self.assertEqual(vsw['vlan_id'], '1000')
        self.assertEqual(vsw['native_vlan_id'], '0001')
        self.assertEqual(vsw['routing_value'], 'NA')
        self.assertEqual(vsw['gvrp_request_attribute'], 'GVRP')
        self.assertEqual(vsw['user_port_based'], 'USERBASED')
        self.assertDictEqual(vsw['authorized_users'], {})
        self.assertListEqual(sorted(['1111', '2222']),
                             sorted(vsw['real_devices'].keys()))

    def test_vswitch_create_multiple_rdev(self):
        """ Positive case of vswitch_create: multiple rdev"""
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, rdev='1111 22 33')
        # Test
        vsw = self.client.query_vswitch(vswitch_name)
        self.assertListEqual(sorted(['1111', '0022', '0033']),
                             sorted(vsw['real_devices'].keys()))

    def test_vswitch_create_existed(self):
        """ Error case of vswitch_create: vswitch already existed """
        # Setup test env
        vswitch_name = self.vswitch
        self.sdkapi.vswitch_create(vswitch_name, '11 0022 333')
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111')

    def test_vswitch_create_long_name(self):
        """ Error case of vswitch_create: name length > 8 """
        # Test
        vswitch_name = "TESTLONGVSWNAME"
        # vswitch name length should be <=8
        self.assertRaises(exception.ZVMInvalidInput,
                          self.sdkapi.vswitch_create,
                          vswitch_name, '1111')
        self.assertNotIn(vswitch_name, self.sdkapi.vswitch_get_list())

    def test_vswitch_create_invalid_rdev(self):
        """ Error case of vswitch_create: invalid rdev """
        # Test
        vswitch_name = self.vswitch
        # only support at most three rdevs
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
