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
from smtLayer.vmcpHandler import VMCPHandler
from zvmsdk import config


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


class GetHostVmcpTestCase(base.SMTTestCase):
    """Test cases for VMCP memory queries (use_smapi=False) in getHost.getGeneralInfo."""

    SYSINFO = (
        "LPAR CPUs Total:        4\n"
        "LPAR CPUs Configured:   4\n"
        "Type:                   2964\n"
        "Manufacturer:           IBM\n"
        "VM00 Control Program:   z/VM 7.2\n"
    )

    SUBPROC_USERID_OUTPUT = b'LXUSR AT LXHOST'
    UNAME_OUTPUT = ('', '', '', '', 's390x')
    CPU_COUNT = (4, 4)

    SMCLI_INFO = {
        'overallRC': 0, 'rc': 0, 'rs': 0,
        'response': 'STORAGE= ONLINE=1024M STANDBY=0M\n'
                    'IPL_TIME= 00:00:00 2026-01-01 UTC\n',
    }

    MEMORY_IN_USE_SUCCESS_RESP = {
        'overallRC': 0,
        'response': 'MEMORY_IN_USE=1048576'
    }

    MEMORY_IN_USE_FAILURE_RESP = {
        'overallRC': 1,
        'response': 'vmcp query frames failed'
    }

    def setUp(self):
        super().setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = False
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())

        self._patches = []
        p = mock.patch('smtLayer.getHost.subprocess.check_output',
                       return_value=self.SUBPROC_USERID_OUTPUT)
        self._patches.append(p)
        p.start()

        p = mock.patch('builtins.open', mock.mock_open(read_data=self.SYSINFO))
        self._patches.append(p)
        p.start()

        p = mock.patch.object(getHost, 'getCPUCount', return_value=self.CPU_COUNT)
        self._patches.append(p)
        p.start()

        p = mock.patch('smtLayer.getHost.os.uname',
                       return_value=self.UNAME_OUTPUT)
        self._patches.append(p)
        p.start()

        # System_Information_Query (for storage / ipl headers)
        p = mock.patch.object(getHost, 'invokeSMCLI', return_value=self.SMCLI_INFO)
        self._patches.append(p)
        p.start()

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @mock.patch.object(getHost.generalUtils, 'getSizeFromPage', return_value='4G')
    @mock.patch.object(VMCPHandler, 'query_image_performance')
    def test_getGeneralInfo_vmcp_memory_in_use_success(self, mock_perf, mock_get_size):
        """getGeneralInfo fetches memory in use via VMCPHandler."""
        mock_perf.return_value = self.MEMORY_IN_USE_SUCCESS_RESP

        getHost.getGeneralInfo(self.rh)

        mock_perf.assert_called_once_with(self.rh)
        mock_get_size.assert_called_once_with(self.rh, '1048576')
        self.assertEqual(0, self.rh.results['overallRC'])

    @mock.patch.object(VMCPHandler, 'query_image_performance')
    def test_getGeneralInfo_vmcp_memory_in_use_failure(self, mock_perf):
        """getGeneralInfo handles VMCP performance query failure."""
        mock_perf.return_value = self.MEMORY_IN_USE_FAILURE_RESP

        getHost.getGeneralInfo(self.rh)

        mock_perf.assert_called_once_with(self.rh)
        self.assertEqual(1, self.rh.results['overallRC'])
