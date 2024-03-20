#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2023 IBM Corp.
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
import time

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smtclient
from zvmsdk import utils as zvmutils


_HOSTOPS = None
CONF = config.CONF
LOG = log.LOG


def get_hostops():
    global _HOSTOPS
    if _HOSTOPS is None:
        _HOSTOPS = HOSTOps()
    return _HOSTOPS


class HOSTOps(object):
    def __init__(self):
        self._smtclient = smtclient.get_smtclient()
        self._volume_infos = {}
        self._volumes = None
        self.cache_expiration = time.time()
        self.disk_pool = None

    def get_info(self):
        inv_info = self._smtclient.get_host_info()
        host_info = {}

        with zvmutils.expect_invalid_resp_data(inv_info):
            host_info['zcc_userid'] = inv_info['zcc_userid']
            host_info['vcpus'] = int(inv_info['lpar_cpu_total'])
            host_info['vcpus_used'] = int(inv_info['lpar_cpu_used'])
            host_info['cpu_info'] = {}
            host_info['cpu_info'] = {'architecture': const.ARCHITECTURE,
                                     'cec_model': inv_info['cec_model'], }
            mem_mb = zvmutils.convert_to_mb(inv_info['lpar_memory_total'])
            host_info['memory_mb'] = mem_mb
            mem_mb_used = zvmutils.convert_to_mb(inv_info['lpar_memory_used'])
            host_info['memory_mb_used'] = mem_mb_used
            host_info['hypervisor_type'] = const.HYPERVISOR_TYPE
            verl = inv_info['hypervisor_os'].split()[1].split('.')
            version = int(''.join(verl))
            host_info['hypervisor_version'] = version
            host_info['ipl_time'] = inv_info['ipl_time']
            # add hypervisor hostname suffix if file
            # /opt/.zvmsdk_hypervisor_hostname_suffix exists
            suffix_file = '/'.join(('/opt',
                                    const.HYPERVISOR_HOSTNAME_SUFFIX_FILE))
            if os.path.exists(suffix_file):
                with open(suffix_file, 'r') as f:
                    lines = f.readlines()
                    suffix = lines[0].strip('\n ') if lines else ''
                host_info['zvm_host'] = '.'.join(
                            (inv_info['zvm_host'], suffix)).strip('.')
                host_info['hypervisor_hostname'] = '.'.join(
                            (inv_info['hypervisor_name'], suffix)).strip('.')
            else:
                host_info['zvm_host'] = inv_info['zvm_host']
                host_info['hypervisor_hostname'] = inv_info['hypervisor_name']

        disk_pool = CONF.zvm.disk_pool
        if disk_pool is None:
            dp_info = {'disk_total': 0, 'disk_used': 0, 'disk_available': 0}
        else:
            diskpool_name = disk_pool.split(':')[1]
            dp_info = self.diskpool_get_info(diskpool_name)
        host_info.update(dp_info)

        return host_info

    def guest_list(self):
        guest_list = self._smtclient.get_all_user_direct()
        with zvmutils.expect_invalid_resp_data(guest_list):
            # If the z/VM is an SSI cluster member, it could get
            # guests on other z/VMs in the same SSI cluster, need
            # get rid of these guests.
            if self._smtclient.host_get_ssi_info():
                new_guest_list = []
                for userid in guest_list:
                    if not zvmutils.check_userid_on_others(userid):
                        new_guest_list.append(userid)
                guest_list = new_guest_list
            return guest_list

    def _cache_enabled(self):
        return CONF.monitor.cache_interval > 0

    def diskpool_get_volumes(self, disk_pool):
        pool_name = disk_pool.split(':')[1].upper()
        if self._cache_enabled():
            if (time.time() > self.cache_expiration):
                self._volumes = None
            if self._volumes:
                if disk_pool == self.disk_pool:
                    return self._volumes
            self._volumes = self._smtclient.get_diskpool_volumes(pool_name)
            self.cache_expiration = time.time() + \
                float(CONF.monitor.cache_interval * 10)
            self.disk_pool = disk_pool
            return self._volumes
        else:
            self._volumes = self._smtclient. \
                get_diskpool_volumes(pool_name)
            self.disk_pool = disk_pool
            return self._volumes

    def get_volume_info(self, volume_name):
        update_needed = False
        with zvmutils.expect_invalid_resp_data():
            if self._volume_infos is not None:
                volume_info = self._volume_infos.get(volume_name)
                if not volume_info:
                    update_needed = True
                else:
                    return volume_info
            else:
                update_needed = True
            if update_needed:
                # results of get_volume_info() is the format like:
                # {'IAS100': { 'volume_type': '3390-54',
                # 'volume_size': '60102'},
                # 'IAS101': { 'volume_type': '3390-09',
                # 'volume_size': '60102'}}
                self._volume_infos = self._smtclient.get_volume_info()
                volume_info = self._volume_infos.get(volume_name)
                if not volume_info:
                    msg = ("Not found the volume info for the"
                           " volume %(volume)s: make sure the volume"
                           " is in the disk_pool configured for sdkserver.") \
                          % {'volume': volume_name}
                    raise exception.ZVMNotFound(msg=msg)
                else:
                    return volume_info

    def diskpool_get_info(self, pool, details=False):
        dp_info = self._smtclient.get_diskpool_info(pool, details)
        with zvmutils.expect_invalid_resp_data(dp_info):
            if not details:
                for k in list(dp_info.keys()):
                    s = dp_info[k].strip().upper()
                    if s.endswith('G'):
                        sl = s[:-1].split('.')
                        n1, n2 = int(sl[0]), int(sl[1])
                        if n2 >= 5:
                            n1 += 1
                        dp_info[k] = n1
                    elif s.endswith('M'):
                        n_mb = int(s[:-3])
                        n_gb, n_ad = n_mb // 1024, n_mb % 1024
                        if n_ad >= 512:
                            n_gb += 1
                        dp_info[k] = n_gb
                    else:
                        exp = "ending with a 'G' or 'M'"
                        errmsg = ("Invalid diskpool size format: %(invalid)s; "
                            "Expected: %(exp)s") % {'invalid': s, 'exp': exp}
                        LOG.error(errmsg)
                        raise exception.SDKInternalError(msg=errmsg)
        return dp_info

    def host_get_ssi_info(self):
        return self._smtclient.host_get_ssi_info()
