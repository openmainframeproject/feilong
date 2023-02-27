#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2018 IBM Corp.
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

from unittest import mock
from smtLayer import ReqHandle
from smtLayer import getHost
from smtLayer.tests.unit import base


class SMTGetHostTestCase(base.SMTTestCase):
    """Test cases for getHost.py in smtLayer."""

    def test_getDiskPoolSpace9336(self):
        parts = ['v1', '9336-32', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390(self):
        parts = ['v1', '3390-09', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    def test_getDiskPoolSpace9336Unknown(self):
        parts = ['v1', '????', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390Unknown(self):
        parts = ['v1', '????', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    def test_getDiskPoolSpace9336UnknownWithFlag(self):
        parts = ['v1', '9336-?', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390UnknownWithFlag(self):
        parts = ['v1', '3390-?', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_without_STANDBY(self, fake_smcli):
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 PARKED IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value1:", ret_total, ret_used)
        self.assertEqual(4, ret_total)
        self.assertEqual(4, ret_used)

    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_with_STANDBY(self, fake_smcli):
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 STANDBY IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value2:", ret_total, ret_used)
        self.assertEqual(4, ret_total)
        self.assertEqual(3, ret_used)

    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_no_CPU(self, fake_smcli):
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value3:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_noTypebutOOO(self, fake_smcli):
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS OOO CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 STANDBY IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value4:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_with_overallRC_error(self, fake_smcli):
        fake_smcli.return_value = {
            'overallRC': 24, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'SMAPI API failed\n',
            'strError': 'Input error'
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value5:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)
