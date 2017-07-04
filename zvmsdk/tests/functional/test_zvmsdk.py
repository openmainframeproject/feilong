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


import os
import unittest
import uuid

from zvmsdk import api
from zvmsdk import config
from zvmsdk import client as zvmclient
from zvmsdk import exception


CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKAPITestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPITestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()
        self.basevm = "nydy0001"
        self.client = zvmclient.get_zvmclient()

    def test_host_get_info(self):
        """Positive test case of host_get_info."""
        host_info = self.sdkapi.host_get_info()
        self.assertTrue(isinstance(host_info.get('disk_available'), int))
        self.assertTrue(isinstance(host_info.get('ipl_time'), unicode))
        self.assertTrue(isinstance(host_info.get('vcpus_used'), int))
        self.assertEqual(host_info.get('hypervisor_type'), 'zvm')
        self.assertTrue(isinstance(host_info.get('disk_total'), int))
        self.assertTrue(isinstance(host_info.get('hypervisor_hostname'),
                                   unicode))
        self.assertTrue(isinstance(host_info.get('memory_mb'), float))
        self.assertTrue(isinstance(host_info.get('cpu_info'), dict))
        self.assertTrue(isinstance(host_info.get('vcpus'), int))
        self.assertTrue(isinstance(host_info.get('hypervisor_version'), int))
        self.assertTrue(isinstance(host_info.get('disk_used'), int))
        self.assertTrue(isinstance(host_info.get('memory_mb_used'), float))

    def test_host_get_info_invalid_host(self):
        """TO test host_get_info when invalid zvm host specified."""
        zvm_host = CONF.zvm.host
        self.addCleanup(set_conf, 'zvm', 'host', zvm_host)

        CONF.zvm.host = 'invalidhost'
        self.assertRaises(exception.SDKBaseException,
                          self.sdkapi.host_get_info)

    def test_host_diskpool_get_info(self):
        """To test host_diskpool_get_info."""
        disk_info = self.sdkapi.host_diskpool_get_info()
        self.assertTrue(isinstance(disk_info.get('disk_available'), int))
        self.assertTrue(isinstance(disk_info.get('disk_total'), int))
        self.assertTrue(isinstance(disk_info.get('disk_used'), int))

    def test_host_diskpool_get_info_with_parameter(self):
        """To test host_diskpool_get_info with disk pool specified."""
        disk_info = self.sdkapi.host_diskpool_get_info('FBA:xcatfba1')
        self.assertTrue(isinstance(disk_info.get('disk_available'), int))
        self.assertTrue(isinstance(disk_info.get('disk_total'), int))
        self.assertTrue(isinstance(disk_info.get('disk_used'), int))

    def test_host_diskpool_get_info_invalid_diskpool(self):
        """To test host_diskpool_get_info with invalid disk pool specified."""
        self.assertRaises(exception.SDKBaseException,
                          self.sdkapi.host_diskpool_get_info,
                          'ECKD:invalidpoolname')

    def test_guest_inspect_cpus(self):
        """ Positive test case of guest_inspect_cpus"""
        guest_list = self.sdkapi.host_list_guests()
        n = 0
        for uid in guest_list:
            if self.sdkapi.guest_get_power_state(uid) == 'on':
                n = n + 1
                test_id = uid
        if n > 0:
            result = self.sdkapi.guest_inspect_cpus(guest_list)
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(len(result), n)
            self.assertTrue(isinstance(
                result[test_id].get('guest_cpus'), int))
            self.assertTrue(isinstance(
                result[test_id].get('used_cpu_time_us'), int))
            self.assertTrue(isinstance(
                result[test_id].get('elapsed_cpu_time_us'), int))
            self.assertTrue(isinstance(
                result[test_id].get('min_cpu_count'), int))
            self.assertTrue(isinstance(
                result[test_id].get('max_cpu_limit'), int))
            self.assertTrue(isinstance(
                result[test_id].get('samples_cpu_in_use'), int))
            self.assertTrue(isinstance(
                result[test_id].get('samples_cpu_delay'), int))
        else:
            result = self.sdkapi.guest_inspect_cpus(guest_list)
            empty_dict = {}
            self.assertEqual(result, empty_dict)

    def test_guest_inspect_cpus_with_nonexist_guest(self):
        """ To test guest_inspect_cpus for a nonexistent guest"""
        result = self.sdkapi.guest_inspect_cpus('fake_id')
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_cpus_with_empty_list(self):
        """ To test guest_inspect_cpus with an empty user list"""
        result = self.sdkapi.guest_inspect_cpus([])
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_mem(self):
        """ Positive test case of guest_inspect_mem"""
        guest_list = self.sdkapi.host_list_guests()
        n = 0
        for uid in guest_list:
            if self.sdkapi.guest_get_power_state(uid) == 'on':
                n = n + 1
                test_id = uid
        if n > 0:
            result = self.sdkapi.guest_inspect_mem(guest_list)
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(len(result), n)
            self.assertTrue(isinstance(
                result[test_id].get('used_mem_kb'), int))
            self.assertTrue(isinstance(
                result[test_id].get('max_mem_kb'), int))
            self.assertTrue(isinstance(
                result[test_id].get('min_mem_kb'), int))
            self.assertTrue(isinstance(
                result[test_id].get('shared_mem_kb'), int))
        else:
            result = self.sdkapi.guest_inspect_mem(guest_list)
            empty_dict = {}
            self.assertEqual(result, empty_dict)

    def test_guest_inspect_mem_with_nonexist_guest(self):
        """ To test guest_inspect_mem for a nonexistent guest"""
        result = self.sdkapi.guest_inspect_mem('fake_id')
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_mem_with_empty_list(self):
        """ To test guest_inspect_mem with an empty user list"""
        result = self.sdkapi.guest_inspect_mem([])
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_vnics(self):
        """ Positive test case of guest_inspect_vnics"""
        guest_list = self.sdkapi.host_list_guests()
        n = 0
        for uid in guest_list:
            if self.sdkapi.guest_get_power_state(uid) == 'on':
                switch_dict = self.sdkapi.guest_get_nic_switch_info(
                                                uid)
                if switch_dict and '' not in switch_dict.values():
                    for key in switch_dict:
                        result = self.sdkapi.guest_get_definition_info(
                                                uid, nic_coupled=key)
                        if result['nic_coupled']:
                            n = n + 1
                            test_id = uid
                            break

        if n > 0:
            result = self.sdkapi.guest_inspect_vnics(guest_list)
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(len(result), n)
            self.assertTrue(isinstance(
                result[test_id][0].get('vswitch_name'), unicode))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_vdev'), unicode))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_rx'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_tx'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_rx_dsc'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_tx_dsc'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_rx_err'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_fr_tx_err'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_rx'), int))
            self.assertTrue(isinstance(
                result[test_id][0].get('nic_tx'), int))
        else:
            result = self.sdkapi.guest_inspect_vnics(guest_list)
            empty_dict = {}
            self.assertEqual(result, empty_dict)

    def test_guest_inspect_vnics_with_nonexist_guest(self):
        """ To test guest_inspect_vnics for a nonexistent guest"""
        result = self.sdkapi.guest_inspect_vnics('fake_id')
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_vnics_with_empty_list(self):
        """ To test guest_inspect_vnics with an empty user list"""
        result = self.sdkapi.guest_inspect_vnics([])
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_image_operations(self):
        """ Import a image, query the existence and then delete it"""
        image_fname = str(uuid.uuid1())
        image_fpath = ''.join([CONF.image.temp_path, image_fname])
        os.system('touch %s' % image_fpath)
        url = "file://" + image_fpath
        image_meta = {'os_version': 'rhel7.2'}
        self.sdkapi.image_import(url, image_meta)

        query_result = self.sdkapi.image_query(image_fname)
        expect_result = ['rhel7.2-s390x-netboot-%s'
                         % image_fname.replace('-', '_')]
        self.assertEqual(query_result, expect_result)

        self.sdkapi.image_delete(query_result[0])
        query_result_after_delete = self.sdkapi.image_query(image_fname)
        expect_result_after_delete = []
        self.assertEqual(query_result_after_delete,
                         expect_result_after_delete)
        os.system('rm -f %s' % image_fpath)

    def test_vswitch_get_list(self):
        """ Positive test case of vswitch_get_list """
        self.sdkapi.vswitch_create("SDKTEST", "1111")
        vswitch_list = self.sdkapi.vswitch_get_list()
        self.assertIsInstance(vswitch_list, list)
        self.assertTrue("SDKTEST" in vswitch_list)
        #clear test environment
        self.sdkapi.vswitch_delete("SDKTEST")

    def _get_vswitch_grant_info(self, vswitch_name):
        vswitch_info = self.client.get_vswitch_info(vswitch_name)
        grant_users = []
        match_key = "     User: "
        for ls in vswitch_info:
            if ls.__contains__(match_key):
                user = ls[ls.find(match_key) + len(match_key):].strip()
                grant_users.append(user)
        return grant_users

    def test_vswitch_grant_revoke(self):
        """ Positive test case of vswitch_grant_user and 
        vswitch_revoke_user """
        # Setup test env
        vswitch_name = "SDKTEST"
        self.sdkapi.vswitch_create(vswitch_name, "1111")
        # grant and check
        self.sdkapi.vswitch_grant_user(vswitch_name, self.basevm)
        authorized_users = self._get_vswitch_grant_info(vswitch_name)
        self.assertIn(self.basevm.upper(), authorized_users)
        # revoke and check
        self.sdkapi.vswitch_revoke_user(vswitch_name, self.basevm)
        authorized_users = self._get_vswitch_grant_info(vswitch_name)
        self.assertNotIn(self.basevm.upper(), authorized_users)
        # Clear test env
        self.sdkapi.vswitch_delete(vswitch_name)

    def test_vswitch_grant_not_exist(self):
        """ Error case of vswitch_grant_user: vswitch not exist """
        # Setup test env
        vswitch_name = "SDKTEST"
        if vswitch_name in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete(vswitch_name)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_grant_user,
                          vswitch_name, self.basevm)

    def test_vswitch_revoke_not_exist(self):
        """ Error case of vswitch_revoke_user: vswitch not exist """
        # Setup test env
        vswitch_name = "SDKTEST"
        if vswitch_name in self.sdkapi.vswitch_get_list():
            self.sdkapi.vswitch_delete(vswitch_name)
        # Test
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.vswitch_revoke_user,
                          vswitch_name, self.basevm)
