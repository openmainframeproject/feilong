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

from zvmsdk import config
from zvmsdk import hostops
from zvmsdk.tests.unit import base

CONF = config.CONF


class SDKHostOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._hostops = hostops.get_hostops()

    @mock.patch.object(hostops.HOSTOps, 'diskpool_get_info')
    @mock.patch.object(hostops.get_hostops()._zvmclient, 'get_host_info')
    def test_get_host_info(self, get_host_info, diskpool_get_info):
        get_host_info.return_value = {
            "zvm_host": "FAKENODE",
            "zhcp": "fakehcp.fake.com",
            "cec_vendor": "FAKE",
            "cec_model": "2097",
            "hypervisor_os": "z/VM 6.1.0",
            "hypervisor_name": "fakenode",
            "architecture": "s390x",
            "lpar_cpu_total": "10",
            "lpar_cpu_used": "10",
            "lpar_memory_total": "16G",
            "lpar_memory_used": "16.0G",
            "lpar_memory_offline": "0",
            "ipl_time": "IPL at 03/13/14 21:43:12 EDT",
            }
        diskpool_get_info.return_value = {
            "disk_total": 406105,
            "disk_used": 367263,
            "disk_available": 38843,
            }
        host_info = self._hostops.get_info()
        get_host_info.assert_called_once_with()
        diskpool = CONF.zvm.disk_pool.split(':')[1]
        diskpool_get_info.assert_called_once_with(diskpool)
        self.assertEqual(host_info['vcpus'], 10)
        self.assertEqual(host_info['hypervisor_version'], 610)
        self.assertEqual(host_info['disk_total'], 406105)

    @mock.patch.object(hostops.get_hostops()._zvmclient, 'get_diskpool_info')
    def test_get_diskpool_info(self, get_diskpool_info):
        get_diskpool_info.return_value = {
            "disk_total": "406105.3 G",
            "disk_used": "367262.6 G",
            "disk_available": "38842.7 G",
            }
        dp_info = self._hostops.diskpool_get_info("fakepool")
        get_diskpool_info.assert_called_once_with("fakepool")
        self.assertEqual(dp_info['disk_total'], 406105)
        self.assertEqual(dp_info['disk_used'], 367263)
        self.assertEqual(dp_info['disk_available'], 38843)
