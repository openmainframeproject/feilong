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
from smtLayer import migrateVM, msgs, ReqHandle
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import VMCPHandler
from zvmsdk import config


class MigrateVMVmcpTestCase(base.SMTTestCase):
    """Test cases for VMCP live migration (use_smapi=False) in migrateVM.moveVM."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.rh.userid = "TESTUSER"
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = False

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(VMCPHandler, 'query_relocate')
    def test_moveVM_vmcp_success(self, mock_relocate, mock_print):
        """moveVM via VMCP succeeds and prints success message."""
        mock_relocate.return_value = {
            'overallRC': 0,
            'response': 'Relocation started\n'
        }

        migrateVM.moveVM(self.rh)

        mock_relocate.assert_called_once_with(self.rh)
        mock_print.assert_called_once_with(
            "N", "VMRELOCATE move is success : TESTUSER.")
        self.assertEqual(0, self.rh.results['overallRC'])

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(VMCPHandler, 'query_relocate')
    def test_moveVM_vmcp_user_not_logged_on(self, mock_relocate, mock_print):
        """moveVM via VMCP detects HCP045E and emits msg 0418."""
        mock_relocate.return_value = {
            'overallRC': 8,
            'response': 'HCP045E User TESTUSER not logged on',
            'output': 'HCP045E User TESTUSER not logged on\n'
        }

        migrateVM.moveVM(self.rh)

        mock_relocate.assert_called_once_with(self.rh)
        expected_msg = msgs.msg['0418'][1] % ("MIG", "TESTUSER")
        mock_print.assert_any_call("ES", expected_msg)
        self.assertEqual(msgs.msg['0418'][0]['overallRC'], self.rh.results['overallRC'])

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(VMCPHandler, 'query_relocate')
    def test_moveVM_vmcp_failure_with_error_codes(self, mock_relocate, mock_print):
        """moveVM via VMCP parses HCP message codes and emits msg 0420."""
        mock_relocate.return_value = {
            'overallRC': 8,
            'response': 'Relocation failed',
            'output': 'HCP2627E Relocation error\nHCP2628E Domain error\n'
        }

        migrateVM.moveVM(self.rh)

        mock_relocate.assert_called_once_with(self.rh)
        expected_msg = msgs.msg['0420'][1] % (
            "MIG", "VMRELOCATE Move", "TESTUSER", "HCP2627E HCP2628E")
        mock_print.assert_any_call("ES", expected_msg)


class SMTMigrateVMTestCase(base.SMTTestCase):
    """Test cases for SMCLI live migration (use_smapi=True) in migrateVM.py."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.rh.userid = "TESTUSER"
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = True

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_smcli_success(self, mock_smcli):
        mock_smcli.return_value = {'overallRC': 0, 'response': 'ok'}
        migrateVM.moveVM(self.rh)
        mock_smcli.assert_called_once()
        self.assertEqual(0, self.rh.results['overallRC'])
