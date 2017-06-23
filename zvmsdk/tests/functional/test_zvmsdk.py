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


import unittest

from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception


CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKAPITestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPITestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()

    def test_host_get_info(self):
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
        zvm_host = CONF.zvm.host
        self.addCleanup(set_conf, 'zvm', 'host', zvm_host)

        CONF.zvm.host = 'invalidhost'
        self.assertRaises(exception.SDKBaseException,
                          self.sdkapi.host_get_info)

    def test_host_diskpool_get_info(self):
        disk_info = self.sdkapi.host_diskpool_get_info()
        self.assertTrue(isinstance(disk_info.get('disk_available'), int))
        self.assertTrue(isinstance(disk_info.get('disk_total'), int))
        self.assertTrue(isinstance(disk_info.get('disk_used'), int))

    def test_host_diskpool_get_info_with_parameter(self):
        disk_info = self.sdkapi.host_diskpool_get_info('FBA:xcatfba1')
        self.assertTrue(isinstance(disk_info.get('disk_available'), int))
        self.assertTrue(isinstance(disk_info.get('disk_total'), int))
        self.assertTrue(isinstance(disk_info.get('disk_used'), int))

    def test_host_diskpool_get_info_invalid_diskpool(self):
        self.assertRaises(exception.SDKBaseException,
                          self.sdkapi.host_diskpool_get_info,
                          'ECKD:invalidpoolname')

    def test_guest_inspect_cpus(self):
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
        result = self.sdkapi.guest_inspect_cpus('fake_id')
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_cpus_with_empty_list(self):
        result = self.sdkapi.guest_inspect_cpus([])
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_mem(self):
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
        result = self.sdkapi.guest_inspect_mem('fake_id')
        empty_dict = {}
        self.assertEqual(result, empty_dict)

    def test_guest_inspect_mem_with_empty_list(self):
        result = self.sdkapi.guest_inspect_mem([])
        empty_dict = {}
        self.assertEqual(result, empty_dict)
