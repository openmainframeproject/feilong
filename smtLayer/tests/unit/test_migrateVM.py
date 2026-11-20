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

import mock

from zvmsdk import config
from smtLayer import migrateVM
from smtLayer import ReqHandle
from smtLayer.tests.unit import base


def _make_rh():
    rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
    rh.userid = "TESTUSER"
    rh.parms = {'dest': 'TARGETSYS'}
    return rh


class MoveVMTestCase(base.SMTTestCase):
    """Tests for migrateVM.moveVM() covering both VMCP and SMAPI paths."""

    def setUp(self):
        super(MoveVMTestCase, self).setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']

    def tearDown(self):
        super(MoveVMTestCase, self).tearDown()
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi

    def _set_use_smapi(self, value):
        config.CONF.zvm['use_smapi'] = value

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(migrateVM, 'VMCPHandler')
    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_vmcp_path_success(self, mock_smcli, mock_vmcp_cls, mock_print):
        self._set_use_smapi(False)
        mock_instance = mock.MagicMock()
        mock_vmcp_cls.return_value = mock_instance
        mock_instance.relocate_vm.return_value = {
            'overallRC': 0, 'response': 'Relocation complete', 'output': ''}

        rh = _make_rh()
        rc = migrateVM.moveVM(rh)

        self.assertEqual(0, rc)
        self.assertEqual(0, rh.results['overallRC'])
        mock_instance.relocate_vm.assert_called_once_with()
        mock_smcli.assert_not_called()

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(migrateVM, 'VMCPHandler')
    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_vmcp_path_fails_hcp045e_user_not_logged_on(
            self, mock_smcli, mock_vmcp_cls, mock_print):
        self._set_use_smapi(False)
        mock_instance = mock.MagicMock()
        mock_vmcp_cls.return_value = mock_instance
        mock_instance.relocate_vm.return_value = {
            'overallRC': 1, 'rc': 1, 'rs': 0,
            'response': 'HCP045E User not logged on',
            'output': 'HCP045E User not logged on'
        }

        rh = _make_rh()
        rc = migrateVM.moveVM(rh)

        # HCP045E is mapped to msg 0418 (userid not logged on), rc 99.
        self.assertEqual(99, rc)
        self.assertEqual(418, rh.results['rs'])
        mock_smcli.assert_not_called()

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(migrateVM, 'VMCPHandler')
    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_vmcp_path_fails_other_hcp_codes(
            self, mock_smcli, mock_vmcp_cls, mock_print):
        self._set_use_smapi(False)
        mock_instance = mock.MagicMock()
        mock_vmcp_cls.return_value = mock_instance
        mock_instance.relocate_vm.return_value = {
            'overallRC': 1, 'rc': 1, 'rs': 0,
            'response': 'HCP1234E System error',
            'output': 'HCP1234E System error'
        }

        rh = _make_rh()
        rc = migrateVM.moveVM(rh)

        self.assertEqual(1, rc)
        mock_smcli.assert_not_called()

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(migrateVM, 'VMCPHandler')
    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_smapi_path_success(
            self, mock_smcli, mock_vmcp_cls, mock_print):
        self._set_use_smapi(True)
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': 'OK'}

        rh = _make_rh()
        rc = migrateVM.moveVM(rh)

        self.assertEqual(0, rc)
        mock_vmcp_cls.assert_not_called()
        self.assertEqual(1, mock_smcli.call_count)
        self.assertEqual('VMRELOCATE', mock_smcli.call_args[0][1])

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch.object(migrateVM, 'VMCPHandler')
    @mock.patch.object(migrateVM, 'invokeSMCLI')
    def test_moveVM_smapi_path_fails(
            self, mock_smcli, mock_vmcp_cls, mock_print):
        self._set_use_smapi(True)
        mock_smcli.return_value = {
            'overallRC': 8, 'rc': 8, 'rs': 3000,
            'response': '0045 User not logged on'}

        rh = _make_rh()
        rc = migrateVM.moveVM(rh)

        self.assertNotEqual(0, rc)
        mock_vmcp_cls.assert_not_called()
