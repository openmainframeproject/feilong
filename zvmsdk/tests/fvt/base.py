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
import os
import unittest

from zvmsdk import config
from zvmsdk import smtclient
from zvmsdk.tests.fvt import api_sample
from zvmsdk.tests.fvt import test_utils


config.load_config()
CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class ZVMConnectorBaseTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(ZVMConnectorBaseTestCase, self).__init__(methodName)
        self.longMessage = True
        self.start_position = 0
        self.apibase = api_sample.APITestBase()
        self._smtclient = smtclient.get_smtclient()
        self.client = test_utils.TestzCCClient()
        self.utils = test_utils.ZVMConnectorTestUtils()

    @classmethod
    def setUpClass(cls):
        super(ZVMConnectorBaseTestCase, cls).setUpClass()
        cls.client = test_utils.TestzCCClient()
        cls.utils = test_utils.ZVMConnectorTestUtils()

    def setUp(self):
        super(ZVMConnectorBaseTestCase, self).setUp()
        self.record_logfile_position()

    def set_conf(self, section, opt, value):
        old_value = CONF[section][opt]
        CONF[section][opt] = value
        self.addCleanup(set_conf, section, opt, old_value)

    def record_logfile_position(self):
        """record a position of log file.
           calling get_log() will later get the cotent between this
           position and end of log file.
        """
        log_file = os.path.join(CONF.logging.log_dir, 'zvmsdk.log')
        with open(log_file) as file_:
            # go the end of log file
            file_.seek(0, 2)
            # record current position
            self.start_position = file_.tell()

    def get_log(self):
        log_file = os.path.join(CONF.logging.log_dir, 'zvmsdk.log')
        log_info = []
        with open(log_file) as file_:
            # no update, return none
            current_position = file_.tell()
            # seek to the record position
            file_.seek(self.start_position)
            if current_position == self.start_position:
                return None
            # read from the record position to EOF
            while True:
                lines = file_.readlines()
                if not lines:
                    break
                else:
                    log_info.extend(lines)
        log = ''.join(log_info)
        sep = '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n'
        header = 'Messages in log file:\n'
        return header + sep + log

    def assertEqual(self, first, second, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertEqual(first, second,
                                                          msg=log_info)

    def assertNotEqual(self, first, second, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertNotEqual(first, second,
                                                             msg=log_info)

    def assertTrue(self, expr, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertTrue(expr,
                                                         msg=log_info)

    def assertFalse(self, expr, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertFalse(expr,
                                                          msg=log_info)

    def assertListEqual(self, list1, list2, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertListEqual(list1, list2,
                                                          msg=log_info)

    def assertDictEqual(self, d1, d2, msg=None):
        log_info = self.get_log()
        super(ZVMConnectorBaseTestCase, self).assertDictEqual(d1, d2,
                                                          msg=log_info)
