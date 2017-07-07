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
import random
import unittest
import uuid

from zvmsdk import api
from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import configdrive
from zvmsdk import exception
from zvmsdk import utils as zvmutils


CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKAPITestUtils(object):

    def __init__(self):
        self.api = api.SDKAPI()
        self.zvmclient = zvmclient.get_zvmclient()

    def image_import(self, image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version):
        image_url = ''.join(('file://', image_path))
        remote_host = zvmutils.get_host()
        self.api.image_import(image_url, {'os_version': os_version},
                              remote_host)

    def get_available_test_userid(self):
        exist_list = self.api.host_list_guests()
        test_list = CONF.tests.userid_list.split(' ')
        for uid in test_list:
            if uid in exist_list:
                self.api.guest_delete(uid)
                continue
            else:
                return uid

    def get_available_ip_addr(self):
        ip_list = CONF.tests.ip_addr_list.split(' ')
        vs_info = str(self.zvmclient.virtual_network_vswitch_query_iuo_stats())
        for ip in ip_list:
            if ip not in vs_info:
                return ip

    def generate_mac_addr(self):
        tmp_list = []
        for i in (1, 2, 3):
            tmp_list.append(''.join(random.sample("0123456789abcdef", 2)))

        mac_suffix = ':'.join(tmp_list)
        mac_addr = ':'.join((CONF.tests.mac_user_prefix, mac_suffix))
        return mac_addr

    def guest_deploy(self, userid=None, cpu=1, memory=1024,
                     image_path=CONF.tests.image_path, ip_addr=None,
                     root_disk_size='3g', login_password='password'):
        image_name = os.path.basename(image_path)
        image_name_xcat = '-'.join((CONF.tests.image_os_version,
                                's390x-netboot', image_name.replace('-', '_')))
        if not self.api.image_query(image_name.replace('-', '_')):
            self.image_import()

        if ip_addr is None:
            ip_addr = self.get_available_ip_addr()

        if userid is None:
            userid = self.get_available_test_userid()
        user_profile = CONF.zvm.user_profile
        nic_id = str(uuid.uuid1())
        mac_addr = self.generate_mac_addr()
        nic_info = {'nic_id': nic_id, 'mac_addr': mac_addr}
        vdev = CONF.zvm.default_nic_vdev
        vswitch_name = CONF.tests.vswitch
        remote_host = zvmutils.get_host()
        transportfiles = configdrive.create_config_drive(ip_addr,
                                                CONF.tests.image_os_version)
        disks_list = [{'size': root_disk_size,
                       'is_boot_disk': True,
                       'disk_pool': CONF.zvm.disk_pool}]

        # Create vm in zVM
        self.api.guest_create(userid, cpu, memory, disks_list, user_profile)

        # Setup network for vm
        self.api.guest_create_nic(userid, [nic_info], ip_addr)
        self.api.guest_update_nic_definition(userid, vdev, mac_addr,
                                             vswitch_name)
        self.api.vswitch_grant_user(vswitch_name, userid)

        # Deploy image on vm
        self.api.guest_deploy(userid, image_name_xcat, transportfiles,
                              remote_host)

        # Power on the vm, then put MN's public key into vm
        self.api.guest_start(userid)

        return userid, ip_addr

    def guest_destroy(self, userid):
        self.api.guest_delete(userid)


class SDKAPIGuestTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPIGuestTestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()
        self.sdkutils = SDKAPITestUtils()

    def setUp(self):
        super(SDKAPIGuestTestCase, self).setUp()

        # create test server
        self.userid = self.sdkutils.get_available_test_userid()
        try:
            self.sdkutils.guest_deploy(self.userid)
        finally:
            self.addCleanup(self.sdkutils.guest_destroy, self.userid)

    def test_guest_basic_actions(self):
        userid_list = self.sdkapi.host_list_guests()
        self.assertTrue(self.userid in userid_list)


class SDKAPITestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPITestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()

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
                test_id = uid.upper()
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
        result = self.sdkapi.guest_inspect_cpus('FAKE_ID')
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
                test_id = uid.upper()
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
        result = self.sdkapi.guest_inspect_mem('FAKE_ID')
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
                switch_dict = self.sdkapi.guest_get_nic_vswitch_info(
                                                uid)
                if switch_dict and '' not in switch_dict.values():
                    for key in switch_dict:
                        result = self.sdkapi.guest_get_definition_info(
                                                uid, nic_coupled=key)
                        if result['nic_coupled']:
                            n = n + 1
                            test_id = uid.upper()
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
        result = self.sdkapi.guest_inspect_vnics('FAKE_ID')
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

    def test_image_import_error_path(self):
        """Import a image with xcat internal error"""
        username = CONF.xcat.username
        self.addCleanup(set_conf, 'xcat', 'username', username)
        CONF.xcat.username = 'fakeuser'
        image_fname = str(uuid.uuid1())
        image_fpath = ''.join([CONF.image.temp_path, image_fname])
        os.system('touch %s' % image_fpath)
        url = "file://" + image_fpath
        image_meta = {'os_version': 'rhel7.2'}
        self.assertRaises(exception.ZVMImageError,
                          self.sdkapi.image_import(url, image_meta))
        os.system('rm -f %s' % image_fpath)
