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

from zvmsdk import config
from smtLayer import deleteVM
from smtLayer.tests.unit import base


def _make_rh(userid="TESTUSER"):
    """Return a lightweight mock ReqHandle."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.userid = userid
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
    return rh


# ---------------------------------------------------------------------------
# Helpers: patch targets
# ---------------------------------------------------------------------------
_IS_LOGGED_ON = 'smtLayer.deleteVM.isLoggedOn'
_INVOKE_SMCLI = 'smtLayer.deleteVM.invokeSMCLI'
_PURGE_READER = 'smtLayer.deleteVM.purgeReader'
_VMCP_HANDLER = 'smtLayer.deleteVM.VMCPHandler'


class DeleteMachineVmcpBranchTest(base.SMTTestCase):
    """
    Tests for the use_smapi=False (vmcp) deactivation branch in
    deleteVM.deleteMachine (lines 104-109).
    """

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        # Save the original value and restore it after each test.
        self._orig_use_smapi = config.CONF.zvm['use_smapi']

    def tearDown(self):
        super().tearDown()
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi

    def _set_use_smapi(self, value):
        """Helper: set config.CONF.zvm.use_smapi for the duration of a test."""
        config.CONF.zvm['use_smapi'] = value

    # ------------------------------------------------------------------
    # Scenario 1: guest is ON, use_smapi=False, deactivate succeeds (rc=0)
    # ------------------------------------------------------------------
    @mock.patch(_PURGE_READER)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    @mock.patch(_IS_LOGGED_ON)
    def test_vmcp_deactivate_success_proceeds_to_delete(
            self, mock_logged_on, mock_handler_cls,
            mock_smcli, mock_purge):
        """
        When use_smapi is False and deactivate succeeds (overallRC=0),
        deleteMachine must NOT call printLn/updateResults for the
        deactivation failure path and must continue to Image_Delete_DM.
        """
        self._set_use_smapi(False)

        # Guest is powered on.
        mock_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}

        # VMCPHandler.deactivate returns a dict with overallRC=0.
        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}
        self.rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        # purgeReader and Image_Delete_DM both succeed.
        mock_purge.return_value = {'overallRC': 0}
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        deleteVM.deleteMachine(self.rh)

        # VMCPHandler constructed with rh, deactivate called with force=True.
        mock_handler_cls.assert_called_once_with(self.rh)
        mock_handler_instance.deactivate.assert_called_once_with(
            self.rh.userid, force=True)

        # No error printing for the deactivation path.
        self.rh.printLn.assert_not_called()

        # Image_Delete_DM must have been invoked.
        mock_smcli.assert_called_once_with(
            self.rh, "Image_Delete_DM", mock.ANY)

    # ------------------------------------------------------------------
    # Scenario 2: guest is ON, use_smapi=False, deactivate fails (rc!=0)
    # ------------------------------------------------------------------
    @mock.patch(_PURGE_READER)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    @mock.patch(_IS_LOGGED_ON)
    def test_vmcp_deactivate_failure_prints_and_updates_results(
            self, mock_logged_on, mock_handler_cls,
            mock_smcli, mock_purge):
        """
        When use_smapi is False and deactivate fails (overallRC!=0),
        deleteMachine must call rh.printLn("ES", ...) and
        rh.updateResults(results) with the failure results, and must NOT
        proceed to Image_Delete_DM.
        """
        self._set_use_smapi(False)

        # Guest is powered on.
        mock_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}

        # VMCPHandler.deactivate returns a dict reflecting failure.
        error_results = {
            'overallRC': 4, 'response': 'HCP045E TESTUSER not logged on'}
        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = error_results
        self.rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        mock_purge.return_value = {'overallRC': 0}

        deleteVM.deleteMachine(self.rh)

        # Error must be printed with the response from the returned dict.
        self.rh.printLn.assert_called_once_with(
            "ES", error_results['response'])

        # Results must be propagated with the returned dict.
        self.rh.updateResults.assert_called_with(error_results)

        # Image_Delete_DM must NOT be called when deactivation failed.
        mock_smcli.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 3: guest is OFF — vmcp branch is never entered
    # ------------------------------------------------------------------
    @mock.patch(_PURGE_READER)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    @mock.patch(_IS_LOGGED_ON)
    def test_vmcp_branch_skipped_when_guest_is_off(
            self, mock_logged_on, mock_handler_cls,
            mock_smcli, mock_purge):
        """
        When the guest is already powered off, the deactivation block
        (including VMCPHandler) must not be entered regardless of use_smapi.
        """
        self._set_use_smapi(False)

        # Guest is off (rs != 0).
        mock_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}

        mock_purge.return_value = {'overallRC': 0}
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        deleteVM.deleteMachine(self.rh)

        # VMCPHandler must not be instantiated at all.
        mock_handler_cls.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 4: isLoggedOn fails — treated as "on", vmcp branch runs
    # ------------------------------------------------------------------
    @mock.patch(_PURGE_READER)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    @mock.patch(_IS_LOGGED_ON)
    def test_vmcp_deactivate_called_when_logged_on_check_fails(
            self, mock_logged_on, mock_handler_cls,
            mock_smcli, mock_purge):
        """
        When isLoggedOn itself fails (overallRC!=0), the code treats the
        guest as powered on and must still enter the vmcp deactivation branch.
        """
        self._set_use_smapi(False)

        mock_logged_on.return_value = {'overallRC': 1, 'rc': 8, 'rs': 0}

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}
        self.rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        mock_purge.return_value = {'overallRC': 0}
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        deleteVM.deleteMachine(self.rh)

        mock_handler_cls.assert_called_once_with(self.rh)
        mock_handler_instance.deactivate.assert_called_once_with(
            self.rh.userid, force=True)

    # ------------------------------------------------------------------
    # Scenario 5: use_smapi=True — VMCPHandler must NOT be used at all
    # ------------------------------------------------------------------
    @mock.patch(_PURGE_READER)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    @mock.patch(_IS_LOGGED_ON)
    def test_smapi_path_does_not_use_vmcp_handler(
            self, mock_logged_on, mock_handler_cls,
            mock_smcli, mock_purge):
        """
        When use_smapi=True the SMAPI (invokeSMCLI) path is taken and
        VMCPHandler must never be instantiated.
        """
        self._set_use_smapi(True)

        mock_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}

        mock_purge.return_value = {'overallRC': 0}
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        deleteVM.deleteMachine(self.rh)

        mock_handler_cls.assert_not_called()
        # invokeSMCLI must be called (Image_Deactivate + Image_Delete_DM).
        self.assertTrue(mock_smcli.called)
