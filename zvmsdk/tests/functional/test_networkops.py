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
        self.vswitch = "VSWTEST"
        # Delete test vswitch to make test env more stable
        self.sdkapi.vswitch_delete(self.vswitch)

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
            vsw['authorized_users'][self.basevm.upper()]['vlan_count'], '1')
        self.assertListEqual(
            vsw['authorized_users'][self.basevm.upper()]['vlan_ids'],
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
        self.assertEqual(vsw['port_type'], 'NONE')
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


class SDKNICTestCase(base.SDKAPIBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(SDKNICTestCase, self).__init__(methodName)
        self.basevm = "NICTEST"
        self.client = zvmclient.get_zvmclient()
        self.vswitch = "VSWTEST"
        # Delete test vm/vsw before run cases to make test env more stable
        self.sdkapi.guest_delete(self.basevm)
        self.sdkapi.vswitch_delete(self.vswitch)

    def setUp(self):
        super(SDKNICTestCase, self).setUp()
        self.sdkapi.guest_create(self.basevm, 1, 1024)
        self.addCleanup(self.sdkapi.guest_delete, self.basevm)

    def _activate_vm(self, userid):
        """ Add IPL entry to VM and then Power on the VM. """
        zhcp_node = self.client._get_hcp_info()['nodename']
        cmd = ' '.join((
            '/opt/zhcp/bin/smcli Image_Definition_Update_DM',
            "-T %s" % userid,
            "-k 'IPL=VDEV=190'",
            "-k 'LINK=USERID=MAINT VDEV1=0190 MODE=RR'"))
        self.client.run_commands_on_node(zhcp_node, cmd)
        print("Powering on the guest.")
        # Try 5 times to power on the vm.
        for i in range(5):
            try:
                self.sdkapi.guest_start(userid)
            except exception.ZVMXCATInternalError as err:
                err_str = err.format_message()
                if ("Return Code: 396" in err_str and
                        "Reason Code: 59" in err_str):
                    continue
                else:
                    raise

    def _check_nic(self, vdev, mac=None, vsw=None, devices=3):
        """ Check nic status.
        Returns a bool value to indicate whether the nic is defined in user and
        a string value of the vswitch that the nic is attached to.
        """
        # Construct the expected NIC definition entry
        zhcp_node = self.client._get_hcp_info()['nodename']
        nic_entry = ('%s: NICDEF %s TYPE QDIO') % (zhcp_node, vdev)
        if vsw is not None:
            nic_entry += (" LAN SYSTEM %s") % vsw
        nic_entry += (" DEVICES %d") % devices
        if mac is not None:
            nic_entry += (" MACID %s") % mac
        # Check definition
        cmd = ("/opt/zhcp/bin/smcli Image_Query_DM -T %s" % self.basevm)
        vm_definition = self.client.run_commands_on_node(zhcp_node, cmd)
        if nic_entry not in vm_definition:
            return False, ""
        else:
            # Continue to check the nic info defined in vswitch table
            nic_info = self.sdkapi.guest_get_nic_vswitch_info(self.basevm)
            if vdev not in nic_info.keys():
                # NIC defined in user direct, but not in switch table
                return False, ""
            else:
                # NIC defined and added in switch table
                return True, nic_info[vdev]

    def test_guest_create_nic(self):
        """ Test each parameter of guest_create_nic. """

        print("Creating NIC with default vdev, not active.")
        self.sdkapi.guest_create_nic(self.basevm, persist=True)
        nic_defined, vsw = self._check_nic(CONF.zvm.default_nic_vdev)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Creating NIC with fixed vdev.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='3000')
        nic_defined, vsw = self._check_nic('3000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Creating NIC without vdev, should use max_vdev+3 as default.")
        self.sdkapi.guest_create_nic(self.basevm)
        nic_defined, vsw = self._check_nic('3003')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

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
        nic_defined, vsw = self._check_nic('5000', mac='123456')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

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
        nic_defined, vsw = self._check_nic('6000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")
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

        # Activate the VM
        print("Activating the VM.")
        self._activate_vm(self.basevm)
        print("Creating nic to the active guest.")
        self.sdkapi.guest_create_nic(self.basevm, vdev='8000',
                                     active=True, persist=True)
        # Check nic defined in user direct and vswitch table
        nic_defined, vsw = self._check_nic('8000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

    def test_nic_couple_uncouple_delete(self):
        """ Test couple/uncouple/delete NIC. """
        vswitch = self.vswitch
        vswitch2 = 'VSWTEST2'
        vm = self.basevm
        self.sdkapi.vswitch_create(vswitch)
        self.sdkapi.vswitch_create(vswitch2)
        self.addCleanup(self.sdkapi.vswitch_delete, vswitch)
        self.addCleanup(self.sdkapi.vswitch_delete, vswitch2)

        print("Couple/uncouple/delete, inactive mode.")
        print("Creating NIC with fixed vdev.")
        self.sdkapi.guest_create_nic(vm, vdev='1000')
        # Check nic defined in user direct and not coupled to vswitch
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Coupling with active=True on an off-state VM.")
        # The active should fail and rollback the user direct and switch table
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_couple_to_vswitch,
                          vm, '1000', vswitch, active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, '')

        print("Coupling NIC to VSWITCH.")
        self.sdkapi.guest_nic_couple_to_vswitch(vm, '1000', vswitch)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Coupling NIC to VSWITCH second time, same vswitch, supported.")
        self.sdkapi.guest_nic_couple_to_vswitch(vm, '1000', vswitch)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Coupling NIC to VSWITCH, to different vswitch, not supported.")
        # Should still be coupled to original vswitch
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_couple_to_vswitch,
                          vm, '1000', vswitch2)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Uncoupling with active=True on an off-state VM.")
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_uncouple_from_vswitch,
                          vm, '1000', active=True)
        # The NIC shoule be uncoupled in user direct and switch table
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Uncoupling NIC from VSWITCH the second time.")
        self.sdkapi.guest_nic_uncouple_from_vswitch(vm, '1000')
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Deleting NIC.")
        self.sdkapi.guest_delete_nic(vm, '1000')
        nic_defined, vsw = self._check_nic('1000')
        self.assertNotTrue(nic_defined)

        print("Deleting NIC not existed.")
        self.sdkapi.guest_delete_nic(vm, '1000')

        print("Positive case of Couple/uncouple/delete, active mode.")
        print("Activating the VM.")
        self._activate_vm(vm)
        print("Creating NIC with fixed vdev.")
        self.sdkapi.guest_create_nic(vm, vdev='1000', active=True)
        # Check nic defined in user direct and not coupled to vswitch
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Unauthorized to couple NIC in active mode.")
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_couple_to_vswitch,
                          vm, '1000', vswitch, active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Authorizing VM to couple to vswitch.")
        self.sdkapi.vswitch_grant_user(vswitch, vm)

        print("Coupling NIC to an unexisted vswitch.")
        # active should rollback user direct and raise exception
        if "VSWNONE" in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete("SDKNONE")
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_couple_to_vswitch,
                          vm, '1000', "VSWNONE", active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Coupling NIC to VSWITCH.")
        self.sdkapi.guest_nic_couple_to_vswitch(vm, '1000', vswitch,
                                                active=True)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Coupling NIC to VSWITCH second time, same vswitch, supported.")
        self.sdkapi.guest_nic_couple_to_vswitch(vm, '1000', vswitch,
                                                active=True)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Coupling NIC to VSWITCH, to different vswitch, not supported.")
        # Should still be coupled to original vswitch
        self.sdkapi.vswitch_grant_user(vswitch2, vm)
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_nic_couple_to_vswitch,
                          vm, '1000', vswitch2, active=True)
        nic_defined, vsw = self._check_nic('1000', vsw=vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, vswitch)

        print("Uncoupling NIC from VSWITCH.")
        self.sdkapi.guest_nic_uncouple_from_vswitch(vm, '1000', active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Uncoupling NIC from VSWITCH the second time.")
        self.sdkapi.guest_nic_uncouple_from_vswitch(vm, '1000', active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertTrue(nic_defined)
        self.assertEqual(vsw, "")

        print("Deleting NIC.")
        self.sdkapi.guest_delete_nic(vm, '1000', active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertNotTrue(nic_defined)

        print("Deleting NIC not existed.")
        self.sdkapi.guest_delete_nic(vm, '1000', active=True)
        nic_defined, vsw = self._check_nic('1000')
        self.assertNotTrue(nic_defined)
