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

import mock

import zvmsdk.client as zvmclient
from zvmsdk import exception
from zvmsdk import monitor
from zvmsdk.tests.unit import base


class SDKMonitorTestCase(base.SDKTestCase):
    def setUp(self):
        self._monitor = monitor.get_monitor()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_get_inspect_data_cache_hit_single(self, cache_enabled,
                                                       get_ps, cache_get):
        cache_get.return_value = {
            'userid': 'USERID1',
            'guest_cpus': '1',
            'used_cpu_time': '6185838 uS',
            'elapsed_cpu_time': '35232895 uS',
            'min_cpu_count': '2',
            'max_cpu_limit': '10000',
            'samples_cpu_in_use': '0',
            'samples_cpu_delay': '0',
            'used_memory': '290232 KB',
            'max_memory': '2097152 KB',
            }
        rdata = self._monitor._get_inspect_data('cpumem', ['userid1'])
        self.assertEqual(rdata.keys(), ['USERID1'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['userid', 'guest_cpus',
                                 'used_cpu_time', 'elapsed_cpu_time',
                                 'min_cpu_count', 'max_cpu_limit',
                                 'samples_cpu_in_use',
                                 'samples_cpu_delay',
                                 'used_memory', 'max_memory']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        get_ps.assert_not_called()
        cache_enabled.assert_not_called()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_get_inspect_data_cache_hit_multi(self, cache_enabled,
                                                       get_ps, cache_get):
        cache_get.side_effect = [{
            'userid': 'USERID1',
            'guest_cpus': '1',
            'used_cpu_time': '6185838 uS',
            'elapsed_cpu_time': '35232895 uS',
            'min_cpu_count': '2',
            'max_cpu_limit': '10000',
            'samples_cpu_in_use': '0',
            'samples_cpu_delay': '0',
            'used_memory': '290232 KB',
            'max_memory': '2097152 KB',
            },
            {
            'userid': 'USERID2',
            'guest_cpus': '3',
            'used_cpu_time': '14293629 uS',
            'elapsed_cpu_time': '4868976371 uS',
            'min_cpu_count': '3',
            'max_cpu_limit': '10000',
            'samples_cpu_in_use': '0',
            'samples_cpu_delay': '0',
            'used_memory': '305020 KB',
            'max_memory': '2097152 KB',
            }]
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), ['USERID1', 'USERID2'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['userid', 'guest_cpus',
                                 'used_cpu_time', 'elapsed_cpu_time',
                                 'min_cpu_count', 'max_cpu_limit',
                                 'samples_cpu_in_use',
                                 'samples_cpu_delay',
                                 'used_memory', 'max_memory']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(rdata['USERID2']['guest_cpus'], '3')
        self.assertEqual(rdata['USERID2']['used_cpu_time'], '14293629 uS')
        self.assertEqual(rdata['USERID2']['used_memory'], '305020 KB')
        get_ps.assert_not_called()
        cache_enabled.assert_not_called()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(zvmclient.XCATClient, 'image_performance_query')
    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_private_get_inspect_data_cache_miss_single(self, get_vm_list,
                                                        image_perform_query,
                                                        cache_enabled,
                                                        get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'on'
        cache_enabled.return_value = True
        image_perform_query.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '6185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '290232 KB',
                'max_memory': '2097152 KB',
                },
            'USERID2': {
                'userid': 'USERID2',
                'guest_cpus': '3',
                'used_cpu_time': '14293629 uS',
                'elapsed_cpu_time': '4868976371 uS',
                'min_cpu_count': '3',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '305020 KB',
                'max_memory': '2097152 KB',
                }
            }
        get_vm_list.return_value = ['userid1', 'userid2']
        rdata = self._monitor._get_inspect_data('cpumem', ['userid1'])
        get_ps.assert_called_once_with('userid1')
        get_vm_list.assert_called_once_with()
        image_perform_query.assert_called_once_with(['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['userid', 'guest_cpus',
                                 'used_cpu_time', 'elapsed_cpu_time',
                                 'min_cpu_count', 'max_cpu_limit',
                                 'samples_cpu_in_use',
                                 'samples_cpu_delay',
                                 'used_memory', 'max_memory']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(
        self._monitor._cache._cache['cpumem']['data']['USERID2']['guest_cpus'],
        '3')

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(zvmclient.XCATClient, 'image_performance_query')
    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_private_get_inspect_data_cache_miss_multi(self, get_vm_list,
                                                        image_perform_query,
                                                        cache_enabled,
                                                        get_ps, cache_get):
        cache_get.side_effect = [{
            'userid': 'USERID1',
            'guest_cpus': '1',
            'used_cpu_time': '6185838 uS',
            'elapsed_cpu_time': '35232895 uS',
            'min_cpu_count': '2',
            'max_cpu_limit': '10000',
            'samples_cpu_in_use': '0',
            'samples_cpu_delay': '0',
            'used_memory': '290232 KB',
            'max_memory': '2097152 KB',
            }, None]
        get_ps.return_value = 'on'
        cache_enabled.return_value = True
        image_perform_query.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                },
            'USERID2': {
                'userid': 'USERID2',
                'guest_cpus': '4',
                'used_cpu_time': '14293629 uS',
                'elapsed_cpu_time': '4868976371 uS',
                'min_cpu_count': '4',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '305020 KB',
                'max_memory': '2097152 KB',
                }
            }
        get_vm_list.return_value = ['userid1', 'userid2']
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1', 'userid2'])
        get_ps.assert_called_once_with('userid2')
        get_vm_list.assert_called_once_with()
        image_perform_query.assert_called_once_with(['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['userid', 'guest_cpus',
                                 'used_cpu_time', 'elapsed_cpu_time',
                                 'min_cpu_count', 'max_cpu_limit',
                                 'samples_cpu_in_use',
                                 'samples_cpu_delay',
                                 'used_memory', 'max_memory']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '7185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '390232 KB')
        self.assertEqual(
        self._monitor._cache._cache['cpumem']['data']['USERID2']['guest_cpus'],
        '4')

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(zvmclient.XCATClient, 'image_performance_query')
    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_private_get_inspect_data_cache_disabled(self, get_vm_list,
                                                        image_perform_query,
                                                        cache_enabled,
                                                        get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'on'
        cache_enabled.return_value = False
        image_perform_query.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                }
            }
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1'])
        get_ps.assert_called_once_with('userid1')
        get_vm_list.assert_not_called()
        image_perform_query.assert_called_once_with(['userid1'])
        self.assertEqual(rdata.keys(), ['USERID1'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['userid', 'guest_cpus',
                                 'used_cpu_time', 'elapsed_cpu_time',
                                 'min_cpu_count', 'max_cpu_limit',
                                 'samples_cpu_in_use',
                                 'samples_cpu_delay',
                                 'used_memory', 'max_memory']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '7185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '390232 KB')
        self.assertEqual(
        self._monitor._cache._cache['cpumem']['data'].keys(), [])

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(zvmclient.XCATClient, 'image_performance_query')
    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_private_get_inspect_data_guest_off(self, get_vm_list,
                                                        image_perform_query,
                                                        cache_enabled,
                                                        get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'off'
        cache_enabled.return_value = True
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1'])
        get_ps.assert_called_once_with('userid1')
        cache_enabled.assert_not_called()
        get_vm_list.assert_not_called()
        image_perform_query.assert_not_called()
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(zvmclient.XCATClient, 'image_performance_query')
    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_private_get_inspect_data_guest_not_exist(self, get_vm_list,
                                                        image_perform_query,
                                                        cache_enabled,
                                                        get_ps, cache_get):
        cache_get.return_value = None
        get_ps.side_effect = exception.ZVMVirtualMachineNotExist(msg='msg')
        cache_enabled.return_value = True
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1'])
        get_ps.assert_called_once_with('userid1')
        cache_enabled.assert_not_called()
        get_vm_list.assert_not_called()
        image_perform_query.assert_not_called()
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_single(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                },
            'USERID2': {
                'userid': 'USERID2',
                'guest_cpus': '4',
                'used_cpu_time': '14293629 uS',
                'elapsed_cpu_time': '4868976371 uS',
                'min_cpu_count': '4',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '305020 KB',
                'max_memory': '2097152 KB',
                }
            }
        rdata = self._monitor.inspect_cpus(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['guest_cpus', 'used_cpu_time_us',
                                 'elapsed_cpu_time_us', 'min_cpu_count',
                                 'max_cpu_limit', 'samples_cpu_in_use',
                                 'samples_cpu_delay'
                                 ])
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 7185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_multi(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                },
            'USERID2': {
                'userid': 'USERID2',
                'guest_cpus': '4',
                'used_cpu_time': '14293629 uS',
                'elapsed_cpu_time': '4868976371 uS',
                'min_cpu_count': '4',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '305020 KB',
                'max_memory': '2097152 KB',
                }
            }
        rdata = self._monitor.inspect_cpus(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['guest_cpus', 'used_cpu_time_us',
                                 'elapsed_cpu_time_us', 'min_cpu_count',
                                 'max_cpu_limit', 'samples_cpu_in_use',
                                 'samples_cpu_delay'
                                 ])
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 7185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)
        self.assertEqual(rdata['USERID2']['guest_cpus'], 4)
        self.assertEqual(rdata['USERID2']['used_cpu_time_us'], 14293629)
        self.assertEqual(rdata['USERID2']['elapsed_cpu_time_us'], 4868976371)
        self.assertEqual(rdata['USERID2']['min_cpu_count'], 4)
        self.assertEqual(rdata['USERID2']['max_cpu_limit'], 10000)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_single_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID2': {
                'userid': 'USERID2',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                }
            }
        rdata = self._monitor.inspect_cpus(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_multi_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': {
                'userid': 'USERID1',
                'guest_cpus': '1',
                'used_cpu_time': '7185838 uS',
                'elapsed_cpu_time': '35232895 uS',
                'min_cpu_count': '2',
                'max_cpu_limit': '10000',
                'samples_cpu_in_use': '0',
                'samples_cpu_delay': '0',
                'used_memory': '390232 KB',
                'max_memory': '3097152 KB',
                }
            }
        rdata = self._monitor.inspect_cpus(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(['guest_cpus', 'used_cpu_time_us',
                                 'elapsed_cpu_time_us', 'min_cpu_count',
                                 'max_cpu_limit', 'samples_cpu_in_use',
                                 'samples_cpu_delay'
                                 ])
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 7185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)
