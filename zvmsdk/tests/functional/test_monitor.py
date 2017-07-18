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


class SDKAPIMonitorTestCase(base.SDKAPIBaseTestCase):

    def test_guest_inspect_cpus(self):
        """ Positive test case of guest_inspect_cpus"""
        guest_list = self.sdkapi.guests_list()
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
        guest_list = self.sdkapi.guests_list()
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
        guest_list = self.sdkapi.guests_list()
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
