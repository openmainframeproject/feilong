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

from zvmsdk import config
from zvmsdk.tests.unit import base


class SDKConfigTestCase(base.SDKTestCase):
    """Testcases for Config param"""
    def setUp(self):
        super(SDKConfigTestCase, self).setUp()
        self.conf = config.ConfigOpts()

    def test_validate_conf(self):
        self.assertEqual(True, self.conf._check_zvm_disk_pool('FBA:p1'))

        self.assertEqual(True, self.conf._check_zvm_disk_pool('EcKD:p2'))
