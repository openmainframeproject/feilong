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

import zvmsdk.utils as zvmutils
from zvmsdk.tests.unit import base


class ZVMUtilsTestCases(base.SDKTestCase):
    def test_convert_to_mb(self):
        self.assertEqual(2355.2, zvmutils.convert_to_mb('2.3G'))
        self.assertEqual(20, zvmutils.convert_to_mb('20M'))
        self.assertEqual(1153433.6, zvmutils.convert_to_mb('1.1T'))

    @mock.patch.object(zvmutils, 'get_smt_userid')
    def test_get_namelist(self, gsu):
        gsu.return_value = 'TUID'
        self.assertEqual('TSTNLIST', zvmutils.get_namelist())

        base.set_conf('zvm', 'namelist', None)
        gsu.return_value = 'TUID'
        self.assertEqual('NL00TUID', zvmutils.get_namelist())

        gsu.return_value = 'TESTUSER'
        self.assertEqual('NLSTUSER', zvmutils.get_namelist())
        base.set_conf('zvm', 'namelist', 'TSTNLIST')
