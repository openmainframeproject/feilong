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

from zvmsdk import exception
from zvmsdk import monitor
from zvmsdk.tests.unit import base

CPUMEM_SAMPLE1 = {
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
            'min_memory': '0 KB',
            'shared_memory': '5222192 KB',
            }
CPUMEM_SAMPLE2 = {
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
            'min_memory': '0 KB',
            'shared_memory': '5222190 KB',
            }
CPU_KEYS = ['guest_cpus', 'used_cpu_time_us', 'elapsed_cpu_time_us',
            'min_cpu_count', 'max_cpu_limit', 'samples_cpu_in_use',
            'samples_cpu_delay']
MEM_KEYS = ['used_mem_kb', 'max_mem_kb', 'min_mem_kb', 'shared_mem_kb']

SMCLI_VSW_NIC_DATA = {'vswitches': [
            {'vswitch_name': 'TESTVSW1',
                'nics': [
                    {'nic_fr_rx_dsc': '0',
                     'nic_fr_rx_err': '0',
                     'nic_fr_tx_err': '4',
                     'userid': 'USERID1',
                     'nic_rx': '103024058',
                     'nic_fr_rx': '573952',
                     'nic_fr_tx': '548780',
                     'vdev': '0600',
                     'nic_fr_tx_dsc': '0',
                     'nic_tx': '102030890'},
                    {'nic_fr_rx_dsc': '0',
                     'nic_fr_rx_err': '0',
                     'nic_fr_tx_err': '4',
                     'userid': 'USERID2',
                     'nic_rx': '3111714',
                     'nic_fr_rx': '17493',
                     'nic_fr_tx': '16886',
                     'vdev': '0600',
                     'nic_fr_tx_dsc': '0',
                     'nic_tx': '3172646'}]},
            {'vswitch_name': 'TESTVSW2',
                'nics': [
                    {'nic_fr_rx_dsc': '0',
                     'nic_fr_rx_err': '0',
                     'nic_fr_tx_err': '0',
                     'userid': 'USERID1',
                     'nic_rx': '4684435',
                     'nic_fr_rx': '34958',
                     'nic_fr_tx': '16211',
                     'vdev': '1000',
                     'nic_fr_tx_dsc': '0',
                     'nic_tx': '3316601'},
                    {'nic_fr_rx_dsc': '0',
                     'nic_fr_rx_err': '0',
                     'nic_fr_tx_err': '0',
                     'userid': 'USERID2',
                     'nic_rx': '3577163',
                     'nic_fr_rx': '27211',
                     'nic_fr_tx': '12344',
                     'vdev': '1000',
                     'nic_fr_tx_dsc': '0',
                     'nic_tx': '2515045'}]}],
            'vswitch_count': 2}

INST_NICS_SAMPLE1 = [
            {'nic_fr_rx': 573952,
             'nic_fr_rx_dsc': 0,
             'nic_fr_rx_err': 0,
             'nic_fr_tx': 548780,
             'nic_fr_tx_dsc': 0,
             'nic_fr_tx_err': 4,
             'nic_rx': 103024058,
             'nic_tx': 102030890,
             'nic_vdev': '0600',
             'vswitch_name': 'TESTVSW1'},
            {'nic_fr_rx': 34958,
             'nic_fr_rx_dsc': 0,
             'nic_fr_rx_err': 0,
             'nic_fr_tx': 16211,
             'nic_fr_tx_dsc': 0,
             'nic_fr_tx_err': 0,
             'nic_rx': 4684435,
             'nic_tx': 3316601,
             'nic_vdev': '1000',
             'vswitch_name': 'TESTVSW2'}
        ]
INST_NICS_SAMPLE2 = [
            {'nic_fr_rx': 17493,
             'nic_fr_rx_dsc': 0,
             'nic_fr_rx_err': 0,
             'nic_fr_tx': 16886,
             'nic_fr_tx_dsc': 0,
             'nic_fr_tx_err': 4,
             'nic_rx': 3111714,
             'nic_tx': 3172646,
             'nic_vdev': '0600',
             'vswitch_name': 'TESTVSW1'},
            {'nic_fr_rx': 27211,
             'nic_fr_rx_dsc': 0,
             'nic_fr_rx_err': 0,
             'nic_fr_tx': 12344,
             'nic_fr_tx_dsc': 0,
             'nic_fr_tx_err': 0,
             'nic_rx': 3577163,
             'nic_tx': 2515045,
             'nic_vdev': '1000',
             'vswitch_name': 'TESTVSW2'}
        ]


class SDKMonitorTestCase(base.SDKTestCase):
    def setUp(self):
        self._monitor = monitor.ZVMMonitor()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_get_inspect_data_cache_hit_single(self, cache_enabled,
                                                       get_ps, cache_get):
        cache_get.return_value = CPUMEM_SAMPLE1
        rdata = self._monitor._get_inspect_data('cpumem', ['userid1'])
        self.assertEqual(rdata.keys(), ['USERID1'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPUMEM_SAMPLE1.keys()))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(rdata['USERID1']['shared_memory'], '5222192 KB')
        get_ps.assert_not_called()
        cache_enabled.assert_not_called()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_get_inspect_data_cache_hit_multi(self, cache_enabled,
                                                       get_ps, cache_get):
        cache_get.side_effect = [CPUMEM_SAMPLE1,
            CPUMEM_SAMPLE2]
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), ['USERID1', 'USERID2'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPUMEM_SAMPLE1.keys()))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(rdata['USERID1']['shared_memory'], '5222192 KB')
        self.assertEqual(rdata['USERID2']['guest_cpus'], '3')
        self.assertEqual(rdata['USERID2']['used_cpu_time'], '14293629 uS')
        self.assertEqual(rdata['USERID2']['used_memory'], '305020 KB')
        self.assertEqual(rdata['USERID2']['shared_memory'], '5222190 KB')
        get_ps.assert_not_called()
        cache_enabled.assert_not_called()

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_update_cpumem_data')
    def test_private_get_inspect_data_cache_miss_single(self,
                                                        update_cpumem_data,
                                                        get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'on'
        update_cpumem_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor._get_inspect_data('cpumem', ['userid1'])
        get_ps.assert_called_once_with('userid1')
        update_cpumem_data.assert_called_once_with(['userid1'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPUMEM_SAMPLE1.keys()))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_update_cpumem_data')
    def test_private_get_inspect_data_cache_miss_multi(self,
                                                        update_cpumem_data,
                                                        get_ps, cache_get):
        cache_get.side_effect = [{
            'userid': 'USERID1',
            'guest_cpus': '1',
            'used_cpu_time': '7185838 uS',
            'elapsed_cpu_time': '35232895 uS',
            'min_cpu_count': '2',
            'max_cpu_limit': '10000',
            'samples_cpu_in_use': '0',
            'samples_cpu_delay': '0',
            'used_memory': '390232 KB',
            'max_memory': '2097152 KB',
            'min_memory': '0 KB',
            'shared_memory': '4222192 KB',
            }, None]
        get_ps.return_value = 'on'
        update_cpumem_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1', 'userid2'])
        get_ps.assert_called_once_with('userid2')
        update_cpumem_data.assert_called_once_with(['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPUMEM_SAMPLE1.keys()))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(rdata['USERID1']['shared_memory'], '5222192 KB')

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_update_cpumem_data')
    def test_private_get_inspect_data_guest_off(self,
                                                update_cpumem_data,
                                                get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'off'
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1'])
        get_ps.assert_called_once_with('userid1')
        update_cpumem_data.assert_not_called()
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_update_cpumem_data')
    def test_private_get_inspect_data_guest_not_exist(self,
                                                      update_cpumem_data,
                                                      get_ps, cache_get):
        cache_get.return_value = None
        get_ps.side_effect = exception.ZVMVirtualMachineNotExist(
            userid='userid1', zvm_host='dummy')
        rdata = self._monitor._get_inspect_data('cpumem',
                                                ['userid1'])
        get_ps.assert_called_once_with('userid1')
        update_cpumem_data.assert_not_called()
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.MeteringCache, 'get')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_power_state')
    @mock.patch.object(monitor.ZVMMonitor, '_update_nic_data')
    def test_private_get_inspect_data_vnics(self,
                                            update_nic_data,
                                            get_ps, cache_get):
        cache_get.return_value = None
        get_ps.return_value = 'on'
        update_nic_data.return_value = {'USERID1': INST_NICS_SAMPLE1,
                                        'USERID2': INST_NICS_SAMPLE2
                                        }
        rdata = self._monitor._get_inspect_data('vnics',
                                                ['USERID1'])
        get_ps.assert_called_once_with('USERID1')
        update_nic_data.assert_called_once_with()
        self.assertEqual(rdata, {'USERID1': INST_NICS_SAMPLE1,
                                 'USERID2': INST_NICS_SAMPLE2
                                 })

    @mock.patch.object(monitor.get_monitor()._zvmclient,
                       'image_performance_query')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_vm_list')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_update_cpumem_data_cache_enabled(self, cache_enabled,
                                               get_vm_list,
                                               image_performance_query):
        cache_enabled.return_value = True
        get_vm_list.return_value = ['userid1', 'userid2']
        image_performance_query.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor._update_cpumem_data(['userid1'])
        image_performance_query.assert_called_once_with(['userid1', 'userid2'])
        get_vm_list.assert_called_once_with()
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(
        self._monitor._cache._cache['cpumem']['data']['USERID2']['guest_cpus'],
        '3')

    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    @mock.patch.object(monitor.get_monitor()._zvmclient,
                       'image_performance_query')
    @mock.patch.object(monitor.get_monitor()._zvmclient, 'get_vm_list')
    def test_private_update_cpumem_data_cache_disabled(self, get_vm_list,
                                                image_perform_query,
                                                cache_enabled):
        cache_enabled.return_value = False
        image_perform_query.return_value = {
            'USERID1': CPUMEM_SAMPLE1
            }
        rdata = self._monitor._update_cpumem_data(['userid1'])
        get_vm_list.assert_not_called()
        image_perform_query.assert_called_once_with(['userid1'])
        self.assertEqual(rdata.keys(), ['USERID1'])
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPUMEM_SAMPLE1.keys()))
        self.assertEqual(rdata['USERID1']['guest_cpus'], '1')
        self.assertEqual(rdata['USERID1']['used_cpu_time'], '6185838 uS')
        self.assertEqual(rdata['USERID1']['used_memory'], '290232 KB')
        self.assertEqual(
        self._monitor._cache._cache['cpumem']['data'].keys(), [])

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_single(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_cpus(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPU_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 6185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_multi(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_cpus(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPU_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 6185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)
        self.assertEqual(rdata['USERID2']['guest_cpus'], 3)
        self.assertEqual(rdata['USERID2']['used_cpu_time_us'], 14293629)
        self.assertEqual(rdata['USERID2']['elapsed_cpu_time_us'], 4868976371)
        self.assertEqual(rdata['USERID2']['min_cpu_count'], 3)
        self.assertEqual(rdata['USERID2']['max_cpu_limit'], 10000)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_single_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_cpus(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_cpus_multi_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1
            }
        rdata = self._monitor.inspect_cpus(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(CPU_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['guest_cpus'], 1)
        self.assertEqual(rdata['USERID1']['used_cpu_time_us'], 6185838)
        self.assertEqual(rdata['USERID1']['elapsed_cpu_time_us'], 35232895)
        self.assertEqual(rdata['USERID1']['min_cpu_count'], 2)
        self.assertEqual(rdata['USERID1']['max_cpu_limit'], 10000)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_mem_single(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_mem(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(MEM_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['used_mem_kb'], 290232)
        self.assertEqual(rdata['USERID1']['max_mem_kb'], 2097152)
        self.assertEqual(rdata['USERID1']['min_mem_kb'], 0)
        self.assertEqual(rdata['USERID1']['shared_mem_kb'], 5222192)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_mem_multi(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1,
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_mem(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1', 'USERID2']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(MEM_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['used_mem_kb'], 290232)
        self.assertEqual(rdata['USERID1']['max_mem_kb'], 2097152)
        self.assertEqual(rdata['USERID1']['min_mem_kb'], 0)
        self.assertEqual(rdata['USERID1']['shared_mem_kb'], 5222192)
        self.assertEqual(rdata['USERID2']['used_mem_kb'], 305020)
        self.assertEqual(rdata['USERID2']['max_mem_kb'], 2097152)
        self.assertEqual(rdata['USERID2']['min_mem_kb'], 0)
        self.assertEqual(rdata['USERID2']['shared_mem_kb'], 5222190)

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_mem_single_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID2': CPUMEM_SAMPLE2
            }
        rdata = self._monitor.inspect_mem(['userid1'])
        _get_inspect_data.assert_called_once_with('cpumem', ['userid1'])
        self.assertEqual(rdata, {})

    @mock.patch.object(monitor.ZVMMonitor, '_get_inspect_data')
    def test_inspect_mem_multi_off_or_not_exist(self, _get_inspect_data):
        _get_inspect_data.return_value = {
            'USERID1': CPUMEM_SAMPLE1
            }
        rdata = self._monitor.inspect_mem(['userid1', 'userid2'])
        _get_inspect_data.assert_called_once_with('cpumem',
                                                  ['userid1', 'userid2'])
        self.assertEqual(sorted(rdata.keys()), sorted(['USERID1']))
        self.assertEqual(sorted(rdata['USERID1'].keys()),
                         sorted(MEM_KEYS)
                         )
        self.assertEqual(rdata['USERID1']['used_mem_kb'], 290232)
        self.assertEqual(rdata['USERID1']['max_mem_kb'], 2097152)
        self.assertEqual(rdata['USERID1']['min_mem_kb'], 0)
        self.assertEqual(rdata['USERID1']['shared_mem_kb'], 5222192)

    @mock.patch.object(monitor.get_monitor()._zvmclient,
                       'virtual_network_vswitch_query_iuo_stats')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_update_nic_data(self, cache_enabled, smcli_iuo_query):
        smcli_iuo_query.return_value = SMCLI_VSW_NIC_DATA
        cache_enabled.return_value = True
        nics_dict = self._monitor._update_nic_data()
        self.assertEqual(sorted(["USERID1", "USERID2"]),
                         sorted(nics_dict.keys()))
        self.assertEqual(nics_dict['USERID1'], INST_NICS_SAMPLE1)
        self.assertEqual(nics_dict['USERID2'], INST_NICS_SAMPLE2)
        self.assertEqual(self._monitor._cache.get('vnics', 'USERID1'),
                         INST_NICS_SAMPLE1)
        self.assertEqual(self._monitor._cache.get('vnics', 'USERID2'),
                         INST_NICS_SAMPLE2)

    @mock.patch.object(monitor.get_monitor()._zvmclient,
                       'virtual_network_vswitch_query_iuo_stats')
    @mock.patch.object(monitor.ZVMMonitor, '_cache_enabled')
    def test_private_update_nic_data_cache_disabled(self, cache_enabled,
                                                    smcli_iuo_query):
        smcli_iuo_query.return_value = SMCLI_VSW_NIC_DATA
        cache_enabled.return_value = False
        nics_dict = self._monitor._update_nic_data()
        self.assertEqual(sorted(["USERID1", "USERID2"]),
                         sorted(nics_dict.keys()))
        self.assertEqual(self._monitor._cache.get('vnics', 'USERID1'),
                         None)
        self.assertEqual(self._monitor._cache.get('vnics', 'USERID2'),
                         None)
