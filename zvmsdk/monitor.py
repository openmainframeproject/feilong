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

import threading
import time

from zvmsdk import config
from zvmsdk import log
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils

_MONITOR = None
CONF = config.CONF
LOG = log.LOG


def get_monitor():
    global _MONITOR
    if _MONITOR is None:
        _MONITOR = ZVMMonitor()
    return _MONITOR


class ZVMMonitor(object):
    """Monitor support for ZVM"""
    _TYPES = ('cpumem', 'vnics')

    def __init__(self):
        self._cache = MeteringCache(self._TYPES)
        self._smutclient = smutclient.get_smutclient()

    def inspect_stats(self, uid_list):
        cpumem_data = self._get_inspect_data('cpumem', uid_list)
        # construct and return final result
        stats_data = {}
        for uid in uid_list:
            uid = uid.upper()
            if uid in cpumem_data:
                with zvmutils.expect_invalid_resp_data():
                    user_data = cpumem_data[uid]
                    guest_cpus = int(user_data['guest_cpus'])
                    used_cpu_time = user_data['used_cpu_time']
                    used_cpu_time = int(used_cpu_time.partition(' ')[0])
                    elapsed_cpu_time = int(
                        user_data['elapsed_cpu_time'].partition(' ')[0])
                    used_mem = int(user_data['used_memory'].partition(' ')[0])
                    max_mem = int(user_data['max_memory'].partition(' ')[0])
                    min_mem = int(user_data['min_memory'].partition(' ')[0])
                    shared_mem = int(
                        user_data['shared_memory'].partition(' ')[0])

                stats_data[uid] = {
                    'guest_cpus': guest_cpus,
                    'used_cpu_time_us': used_cpu_time,
                    'elapsed_cpu_time_us': elapsed_cpu_time,
                    'min_cpu_count': int(user_data['min_cpu_count']),
                    'max_cpu_limit': int(user_data['max_cpu_limit']),
                    'samples_cpu_in_use': int(user_data['samples_cpu_in_use']),
                    'samples_cpu_delay': int(user_data['samples_cpu_delay']),
                    'used_mem_kb': used_mem,
                    'max_mem_kb': max_mem,
                    'min_mem_kb': min_mem,
                    'shared_mem_kb': shared_mem
                    }

        return stats_data

    def inspect_vnics(self, uid_list):
        vnics = self._get_inspect_data('vnics', uid_list)
        # construct and return final result
        target_vnics = {}
        for uid in uid_list:
            uid = uid.upper()
            if uid in vnics:
                with zvmutils.expect_invalid_resp_data():
                    target_vnics[uid] = vnics[uid]

        return target_vnics

    def _cache_enabled(self):
        return CONF.monitor.cache_interval > 0

    def _get_inspect_data(self, type, uid_list):
        inspect_data = {}
        update_needed = False
        for uid in uid_list:
            if not zvmutils.valid_userid(uid):
                continue
            cache_data = self._cache.get(type, uid.upper())
            if cache_data is not None:
                inspect_data[uid.upper()] = cache_data
            else:
                if self._smutclient.get_power_state(uid) == 'on':
                    update_needed = True
                    inspect_data = {}
                    break

        # If all data are found in cache, just return
        if not update_needed:
            return inspect_data

        # Call client to query latest data
        rdata = {}
        if type == 'cpumem':
            rdata = self._update_cpumem_data(uid_list)
        elif type == 'vnics':
            rdata = self._update_nic_data()

        return rdata

    def _update_cpumem_data(self, uid_list):
        rdata = {}
        if self._cache_enabled():
            rdata = self._smutclient.image_performance_query(
                self._smutclient.get_vm_list())
            self._cache.refresh('cpumem', rdata)
        else:
            rdata = self._smutclient.image_performance_query(uid_list)

        return rdata

    def _update_nic_data(self):
        nics = {}
        vsw_dict = self._smutclient.virtual_network_vswitch_query_iuo_stats()
        with zvmutils.expect_invalid_resp_data():
            for vsw in vsw_dict['vswitches']:
                for nic in vsw['nics']:
                    userid = nic['userid'].upper()
                    nic_entry = {
                        'vswitch_name': vsw['vswitch_name'],
                        'nic_vdev': nic['vdev'],
                        'nic_fr_rx': int(nic['nic_fr_rx']),
                        'nic_fr_tx': int(nic['nic_fr_tx']),
                        'nic_fr_rx_dsc': int(nic['nic_fr_rx_dsc']),
                        'nic_fr_tx_dsc': int(nic['nic_fr_tx_dsc']),
                        'nic_fr_rx_err': int(nic['nic_fr_rx_err']),
                        'nic_fr_tx_err': int(nic['nic_fr_tx_err']),
                        'nic_rx': int(nic['nic_rx']),
                        'nic_tx': int(nic['nic_tx'])}
                    if nics.get(userid, None) is None:
                        nics[userid] = [nic_entry]
                    else:
                        nics[userid].append(nic_entry)
        # Update cache if enabled
        if self._cache_enabled():
            self._cache.refresh('vnics', nics)

        return nics


class MeteringCache(object):
    """Cache for metering data."""

    def __init__(self, types):
        self._cache = {}
        self._types = types
        self._lock = threading.RLock()
        self._reset(types)

    def _reset(self, types):
        with zvmutils.acquire_lock(self._lock):
            for type in types:
                self._cache[type] = {'expiration': time.time(),
                                    'data': {},
                                    }

    def _get_ctype_cache(self, ctype):
        return self._cache[ctype]

    def set(self, ctype, key, data):
        """Set or update cache content.

        :param ctype: cache type
        :param key: the key to be set value
        :param data: cache data
        """
        with zvmutils.acquire_lock(self._lock):
            target_cache = self._get_ctype_cache(ctype)
            target_cache['data'][key] = data

    def get(self, ctype, key):
        with zvmutils.acquire_lock(self._lock):
            target_cache = self._get_ctype_cache(ctype)
            if(time.time() > target_cache['expiration']):
                return None
            else:
                return target_cache['data'].get(key, None)

    def delete(self, ctype, key):
        with zvmutils.acquire_lock(self._lock):
            target_cache = self._get_ctype_cache(ctype)
            if key in target_cache['data']:
                del target_cache['data'][key]

    def clear(self, ctype='all'):
        with zvmutils.acquire_lock(self._lock):
            if ctype == 'all':
                self._reset()
            else:
                target_cache = self._get_ctype_cache(ctype)
                target_cache['data'] = {}

    def refresh(self, ctype, data):
        with zvmutils.acquire_lock(self._lock):
            self.clear(ctype)
            target_cache = self._get_ctype_cache(ctype)
            target_cache['expiration'] = (time.time() +
                                            float(CONF.monitor.cache_interval))
            for (k, v) in data.items():
                self.set(ctype, k, v)
