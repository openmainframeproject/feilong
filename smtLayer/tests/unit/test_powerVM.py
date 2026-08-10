#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2026 IBM Corp.
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
from smtLayer import powerVM, ReqHandle
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import VMCPHandler
from zvmsdk import config


class PowerVMVmcpTestCase(base.SMTTestCase):
    """Test cases for VMCP power operations (use_smapi=False) in powerVM.py."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.rh.userid = "TESTUSER"
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = False

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @mock.patch.object(VMCPHandler, 'activate')
    def test_activate_vmcp_success(self, mock_activate):
        """Guest activation via VMCP (XAUTOLOG) succeeds."""
        mock_activate.return_value = {'overallRC': 0, 'response': 'Command accepted'}

        rc = powerVM.activate(self.rh)

        mock_activate.assert_called_once_with("TESTUSER")
        self.assertEqual(0, rc)

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(VMCPHandler, 'activate')
    def test_activate_vmcp_failure(self, mock_activate, mock_print):
        """Guest activation via VMCP fails and returns non-zero rc."""
        mock_activate.return_value = {
            'overallRC': 1,
            'response': 'HCP025E Cannot XAUTOLOG TESTUSER'
        }

        rc = powerVM.activate(self.rh)

        mock_activate.assert_called_once_with("TESTUSER")
        mock_print.assert_called_once_with("ES", "HCP025E Cannot XAUTOLOG TESTUSER")
        self.assertEqual(1, rc)

    @mock.patch.object(powerVM, 'waitForOSState')
    @mock.patch.object(VMCPHandler, 'activate')
    def test_activate_vmcp_with_wait_desired_state(self, mock_activate, mock_wait):
        """Guest activation via VMCP with maxQueries polling state."""
        self.rh.parms = {'maxQueries': 10, 'poll': 2, 'desiredState': 'up'}
        mock_activate.return_value = {'overallRC': 0, 'response': ''}
        mock_wait.return_value = {'overallRC': 0}

        rc = powerVM.activate(self.rh)

        mock_activate.assert_called_once_with("TESTUSER")
        mock_wait.assert_called_once_with(
            self.rh, "TESTUSER", "up", maxQueries=10, sleepSecs=2)
        self.assertEqual(0, rc)

    @mock.patch.object(VMCPHandler, 'activate')
    @mock.patch.object(powerVM, 'waitForVMState')
    @mock.patch.object(powerVM, 'invokeSMCLI')
    def test_reset_vmcp_success(self, mock_smcli, mock_wait, mock_activate):
        """Reset via VMCP (deactivate SMCLI -> wait -> VMCP activate)."""
        mock_smcli.return_value = {'overallRC': 0}
        mock_wait.return_value = {'overallRC': 0}
        mock_activate.return_value = {'overallRC': 0, 'response': ''}

        rc = powerVM.reset(self.rh)

        mock_smcli.assert_called_once_with(self.rh, "Image_Deactivate", ["-T", "TESTUSER"])
        mock_activate.assert_called_once_with("TESTUSER")
        self.assertEqual(0, rc)

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(VMCPHandler, 'activate')
    @mock.patch.object(powerVM, 'waitForVMState')
    @mock.patch.object(powerVM, 'invokeSMCLI')
    def test_reset_vmcp_activate_failure(self, mock_smcli, mock_wait,
                                         mock_activate, mock_print):
        """Reset via VMCP when reactivating the user fails."""
        mock_smcli.return_value = {'overallRC': 0}
        mock_wait.return_value = {'overallRC': 0}
        mock_activate.return_value = {
            'overallRC': 8,
            'response': 'HCP025E Cannot XAUTOLOG TESTUSER'
        }

        rc = powerVM.reset(self.rh)

        mock_activate.assert_called_once_with("TESTUSER")
        mock_print.assert_called_once_with("ES", "HCP025E Cannot XAUTOLOG TESTUSER")
        self.assertEqual(8, rc)


class SMTPowerVMTestCase(base.SMTTestCase):
    """Test cases for SMCLI power operations (use_smapi=True) in powerVM.py."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.rh.userid = "TESTUSER"
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = True

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @mock.patch.object(powerVM, 'invokeSMCLI')
    def test_activate_smcli_success(self, mock_smcli):
        mock_smcli.return_value = {'overallRC': 0, 'response': ''}
        rc = powerVM.activate(self.rh)
        mock_smcli.assert_called_once_with(self.rh, "Image_Activate", ["-T", "TESTUSER"])
        self.assertEqual(0, rc)
