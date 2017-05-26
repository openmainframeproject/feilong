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

import time
from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
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
        self._zvmclient = zvmclient.get_zvmclient()

    def inspect_cpus(self, uid_list):
        cpumem_data = self._get_inspect_data('cpumem', uid_list)
        # construct and return final result
        cpu_data = {}
        for uid in uid_list:
            if uid in cpumem_data:
                with zvmutils.expect_invalid_xcat_resp_data():
                    user_data = cpumem_data[uid]
                    guest_cpus = int(user_data['guest_cpus'])
                    used_cpu_time = user_data['used_cpu_time']
                    used_cpu_time = int(used_cpu_time.partition(' ')[0])
                    elapsed_cpu_time = int(
                        user_data['elapsed_cpu_time'].partition(' ')[0])

                cpu_data[uid] = {
                    'guest_cpus': guest_cpus,
                    'used_cpu_time_us': used_cpu_time,
                    'elapsed_cpu_time_us': elapsed_cpu_time,
                    'min_cpu_count': int(user_data['min_cpu_count']),
                    'max_cpu_limit': int(user_data['max_cpu_limit']),
                    'samples_cpu_in_use': int(user_data['samples_cpu_in_use']),
                    'samples_cpu_delay': int(user_data['samples_cpu_delay'])
                    }

        return cpu_data

    def _cache_enabled(self):
        return CONF.monitor.cache_interval > 0

    def _get_inspect_data(self, type, uid_list):
        inspect_data = {}
        update_needed = False
        for uid in uid_list:
            cache_data = self._cache.get(type, uid)
            if cache_data is not None:
                inspect_data[uid] = cache_data
            else:
                try:
                    if self._zvmclient.get_power_state(uid) == 'on':
                        update_needed = True
                        inspect_data = {}
                        break
                    else:
                        # Skip the guest that is in 'off' state
                        continue
                except exception.ZVMVirtualMachineNotExist:
                    # Skip the guest that does not exist, ignore this exception
                    LOG.info('Guest %s does not exist.' % uid)
                    continue

        # If all data are found in cache, just return
        if not update_needed:
            return inspect_data

        # Call client to query latest data
        if self._cache_enabled():
            rdata = self._zvmclient.image_performance_query(
                self._zvmclient.get_vm_list())
            self._cache.refresh(type, rdata)
        else:
            rdata = self._zvmclient.image_performance_query(uid_list)

        return rdata


class MeteringCache(object):
    """Cache for metering data."""

    def __init__(self, types):
        self._cache = {}
        self._types = types
        self._reset(types)

    def _reset(self, types):
        for type in types:
            self._cache[type] = {'expiration': time.time(),
                                'data': {},
                                }

    def _get_ctype_cache(self, ctype):
        return self._cache[ctype]

    def set(self, ctype, data):
        """Set or update cache content.

        @ctype:    cache type.
        @data:    cache data.
        """
        target_cache = self._get_ctype_cache(ctype)
        target_cache['data'][data['userid']] = data

    def get(self, ctype, userid):
        target_cache = self._get_ctype_cache(ctype)
        if(time.time() > target_cache['expiration']):
            return None
        else:
            return target_cache['data'].get(userid.upper(), None)

    def delete(self, ctype, userid):
        uid = userid.upper()
        target_cache = self._get_ctype_cache(ctype)
        if uid in target_cache['data']:
            del target_cache['data'][uid]

    def clear(self, ctype='all'):
        if ctype == 'all':
            self._reset()
        else:
            target_cache = self._get_ctype_cache(ctype)
            target_cache['data'] = {}

    def refresh(self, ctype, data):
        self.clear(ctype)
        target_cache = self._get_ctype_cache(ctype)
        target_cache['expiration'] = (time.time() +
                                        float(CONF.monitor.cache_interval))
        for d in data.values():
            self.set(ctype, d)
