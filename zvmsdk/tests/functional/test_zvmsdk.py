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
