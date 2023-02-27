#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2018 IBM Corp.
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


from zvmsdk import config
from zvmsdk.tests.unit import base


CONFOPTS = config.CONFOPTS


class ZVMConfigTestCases(base.SDKTestCase):

    def test_check_zvm_disk_pool_fba(self):
        CONFOPTS._check_zvm_disk_pool('fba:pool1')

    def test_check_zvm_disk_pool_eckd(self):
        CONFOPTS._check_zvm_disk_pool('eCKD:pool1')

    def test_check_zvm_disk_pool_err1(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_zvm_disk_pool, 'fbapool1')

    def test_check_zvm_disk_pool_err2(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_zvm_disk_pool, 'ECKD:')

    def test_check_user_default_max_memory(self):
        CONFOPTS._check_user_default_max_memory('30G')
        CONFOPTS._check_user_default_max_memory('1234M')

    def test_check_user_default_max_memory_err1(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_memory, '12.0G')

    def test_check_user_default_max_memory_err2(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_memory, '12')

    def test_check_user_default_max_memory_err3(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_memory, '12345M')

    def test_check_user_default_max_reserved_memory(self):
        CONFOPTS._check_user_default_max_reserved_memory('30G')
        CONFOPTS._check_user_default_max_reserved_memory('1234M')

    def test_check_user_default_max_reserved_err1(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_reserved_memory,
                          '12.0G')

    def test_check_user_default_max_reserved_memory_err2(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_reserved_memory,
                          '12')

    def test_check_user_default_max_reserved_memory_err3(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_reserved_memory,
                          '12345M')

    def test_check_user_default_max_cpu(self):
        CONFOPTS._check_user_default_max_cpu(1)

    def test_check_user_default_max_cpu_err(self):
        self.assertRaises(config.OptFormatError,
                          CONFOPTS._check_user_default_max_cpu, 65)
