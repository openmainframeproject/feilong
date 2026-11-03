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
from smtLayer import powerVM
from smtLayer.tests.unit import base


def _make_rh(userid="TESTUSER"):
    """Return a lightweight mock ReqHandle."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.userid = userid
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
    # Ensure 'maxQueries' is absent so the waitForVMState block is skipped.
    rh.parms = {}
    return rh


_VMCP_HANDLER = 'smtLayer.powerVM.VMCPHandler'
_INVOKE_SMCLI = 'smtLayer.powerVM.invokeSMCLI'
_WAIT_FOR_VM = 'smtLayer.powerVM.waitForVMState'


class DeactivateVmcpBranchTest(base.SMTTestCase):
    """
    Tests for the use_smapi=False (vmcp) deactivation branch in
    powerVM.deactivate (lines 257-262).
    """

    def setUp(self):
        super().setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    def _set_use_smapi(self, value):
        config.CONF.zvm['use_smapi'] = value

    # ------------------------------------------------------------------
    # Scenario 1: use_smapi=False, deactivate succeeds (overallRC=0)
    # ------------------------------------------------------------------
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_deactivate_success_no_error_path(self, mock_handler_cls):
        """
        When use_smapi is False and deactivate succeeds (overallRC=0),
        rh.printLn and rh.updateResults must NOT be called for the
        deactivation failure path.
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.deactivate(rh)

        # VMCPHandler constructed with rh, deactivate called with force=True.
        mock_handler_cls.assert_called_once_with(rh)
        mock_handler_instance.deactivate.assert_called_once_with(
            rh.userid, force=True)

        # No error printing or result propagation on success.
        rh.printLn.assert_not_called()
        rh.updateResults.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 2: use_smapi=False, deactivate fails (overallRC!=0)
    # ------------------------------------------------------------------
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_deactivate_failure_prints_and_updates_results(
            self, mock_handler_cls):
        """
        When use_smapi is False and deactivate fails (overallRC!=0),
        rh.printLn("ES", response) and rh.updateResults(results) must be
        called with the failure results captured from rh.results.
        """
        self._set_use_smapi(False)

        error_results = {
            'overallRC': 4, 'response': 'HCP045E TESTUSER not logged on'}
        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = error_results

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.deactivate(rh)

        rh.printLn.assert_called_once_with("ES", error_results['response'])
        rh.updateResults.assert_called_with(error_results)

    # ------------------------------------------------------------------
    # Scenario 3: use_smapi=False — invokeSMCLI never called
    # ------------------------------------------------------------------
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_branch_does_not_call_smcli(
            self, mock_handler_cls, mock_smcli):
        """
        When use_smapi is False, Image_Deactivate via invokeSMCLI must
        never be called.
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.deactivate(rh)

        mock_smcli.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 4: use_smapi=False — VMCPHandler constructed with rh
    # ------------------------------------------------------------------
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_handler_constructed_with_rh(self, mock_handler_cls):
        """
        VMCPHandler must be instantiated with the request handle (rh),
        not any other object.
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.deactivate(rh)

        mock_handler_cls.assert_called_once_with(rh)

    # ------------------------------------------------------------------
    # Scenario 5: use_smapi=True — VMCPHandler never instantiated
    # ------------------------------------------------------------------
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_smapi_path_does_not_use_vmcp_handler(
            self, mock_handler_cls, mock_smcli):
        """
        When use_smapi is True, the SMAPI path is taken and VMCPHandler
        must never be instantiated.
        """
        self._set_use_smapi(True)

        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        rh = _make_rh()
        powerVM.deactivate(rh)

        mock_handler_cls.assert_not_called()
        mock_smcli.assert_called_once_with(
            rh, "Image_Deactivate", mock.ANY)


class ResetVmcpBranchTest(base.SMTTestCase):
    """
    Tests for the use_smapi=False (vmcp) deactivation branch in
    powerVM.reset (lines 607-612).

    Note: reset calls deactivate(rh.userid) without force=True, unlike
    powerVM.deactivate which passes force=True.
    Post-branch calls to waitForVMState and Image_Activate are patched
    out so each test targets only the lines 607-612 block.
    """

    def setUp(self):
        super().setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    def _set_use_smapi(self, value):
        config.CONF.zvm['use_smapi'] = value

    # ------------------------------------------------------------------
    # Scenario 1: use_smapi=False, deactivate succeeds (overallRC=0)
    # ------------------------------------------------------------------
    @mock.patch(_WAIT_FOR_VM)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_reset_deactivate_success_no_error_path(
            self, mock_handler_cls, mock_smcli, mock_wait):
        """
        When use_smapi is False and deactivate succeeds (overallRC=0),
        rh.printLn and rh.updateResults must NOT be called for the
        deactivation failure path.
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        # waitForVMState and Image_Activate succeed so the function exits
        # cleanly without entering any other error path.
        mock_wait.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                  'response': ''}
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        powerVM.reset(rh)

        # VMCPHandler constructed with rh; deactivate called WITHOUT force.
        mock_handler_cls.assert_called_once_with(rh)
        mock_handler_instance.deactivate.assert_called_once_with(rh.userid)

        # No error printing or result propagation on success.
        rh.printLn.assert_not_called()
        rh.updateResults.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 2: use_smapi=False, deactivate called without force flag
    # ------------------------------------------------------------------
    @mock.patch(_WAIT_FOR_VM)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_reset_deactivate_called_without_force(
            self, mock_handler_cls, mock_smcli, mock_wait):
        """
        reset uses a soft logoff — deactivate must be called without
        force=True (unlike powerVM.deactivate which passes force=True).
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        mock_wait.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                  'response': ''}
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        powerVM.reset(rh)

        # Must be called with only the userid — no force keyword.
        mock_handler_instance.deactivate.assert_called_once_with(rh.userid)
        args, kwargs = mock_handler_instance.deactivate.call_args
        self.assertNotIn('force', kwargs)

    # ------------------------------------------------------------------
    # Scenario 3: use_smapi=False, deactivate fails (overallRC!=0)
    # ------------------------------------------------------------------
    @mock.patch(_WAIT_FOR_VM)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_reset_deactivate_failure_prints_and_updates_results(
            self, mock_handler_cls, mock_smcli, mock_wait):
        """
        When use_smapi is False and deactivate fails (overallRC!=0),
        rh.printLn("ES", response) and rh.updateResults(results) must be
        called with the failure results captured from rh.results.
        """
        self._set_use_smapi(False)

        error_results = {
            'overallRC': 4, 'response': 'HCP045E TESTUSER not logged on'}
        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = error_results

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        # waitForVMState and Image_Activate are skipped because overallRC!=0
        # after deactivation, but patch them to be safe.
        mock_wait.return_value = error_results
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        powerVM.reset(rh)

        rh.printLn.assert_called_once_with("ES", error_results['response'])
        rh.updateResults.assert_called_with(error_results)

    # ------------------------------------------------------------------
    # Scenario 4: use_smapi=False — invokeSMCLI not called for deactivation
    # ------------------------------------------------------------------
    @mock.patch(_WAIT_FOR_VM)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_reset_branch_does_not_call_smcli_for_deactivation(
            self, mock_handler_cls, mock_smcli, mock_wait):
        """
        When use_smapi is False, Image_Deactivate via invokeSMCLI must
        never be called for the logoff step.
        """
        self._set_use_smapi(False)

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        mock_wait.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                  'response': ''}
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        powerVM.reset(rh)

        called_apis = [call.args[1] for call in mock_smcli.call_args_list]
        self.assertNotIn("Image_Deactivate", called_apis)

    # ------------------------------------------------------------------
    # Scenario 5: use_smapi=True — VMCPHandler never instantiated
    # ------------------------------------------------------------------
    @mock.patch(_WAIT_FOR_VM)
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_VMCP_HANDLER)
    def test_smapi_reset_path_does_not_use_vmcp_handler(
            self, mock_handler_cls, mock_smcli, mock_wait):
        """
        When use_smapi is True, the SMAPI path is taken and VMCPHandler
        must never be instantiated.
        """
        self._set_use_smapi(True)

        mock_wait.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                  'response': ''}
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        rh = _make_rh()
        powerVM.reset(rh)

        mock_handler_cls.assert_not_called()
        called_apis = [call.args[1] for call in mock_smcli.call_args_list]
        self.assertIn("Image_Deactivate", called_apis)


_EXEC_CMD_IUCV = 'smtLayer.powerVM.execCmdThruIUCV'


class SoftDeactivateVmcpBranchTest(base.SMTTestCase):
    """
    Tests for the use_smapi=False (vmcp) deactivation branch in
    powerVM.softDeactivate (lines 811-816).

    execCmdThruIUCV is patched so the pre-branch IUCV ping/shutdown
    calls are bypassed. rh.parms={} keeps the post-branch waitForVMState
    block from running, keeping every test scoped to lines 811-816.
    Like powerVM.reset, deactivate is called without force=True.
    """

    def setUp(self):
        super().setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    def _set_use_smapi(self, value):
        config.CONF.zvm['use_smapi'] = value

    # ------------------------------------------------------------------
    # Scenario 1: use_smapi=False, deactivate succeeds (overallRC=0)
    # ------------------------------------------------------------------
    @mock.patch(_EXEC_CMD_IUCV)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_softdeactivate_success_no_error_path(
            self, mock_handler_cls, mock_iucv):
        """
        When use_smapi is False and deactivate succeeds (overallRC=0),
        rh.printLn and rh.updateResults must NOT be called for the
        deactivation failure path.
        """
        self._set_use_smapi(False)

        # IUCV ping fails → treated as unreachable, skips shutdown branch.
        mock_iucv.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0,
                                  'response': ''}

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.softDeactivate(rh)

        # VMCPHandler constructed with rh; deactivate called WITHOUT force.
        mock_handler_cls.assert_called_once_with(rh)
        mock_handler_instance.deactivate.assert_called_once_with(rh.userid)

        # No error printing or result propagation on success.
        rh.printLn.assert_not_called()
        rh.updateResults.assert_not_called()

    # ------------------------------------------------------------------
    # Scenario 2: use_smapi=False, deactivate called without force flag
    # ------------------------------------------------------------------
    @mock.patch(_EXEC_CMD_IUCV)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_softdeactivate_called_without_force(
            self, mock_handler_cls, mock_iucv):
        """
        softDeactivate uses a soft logoff — deactivate must be called
        without force=True.
        """
        self._set_use_smapi(False)

        mock_iucv.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0,
                                  'response': ''}

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.softDeactivate(rh)

        # Called with only the userid — no force keyword.
        mock_handler_instance.deactivate.assert_called_once_with(rh.userid)
        _, kwargs = mock_handler_instance.deactivate.call_args
        self.assertNotIn('force', kwargs)

    # ------------------------------------------------------------------
    # Scenario 3: use_smapi=False, deactivate fails (overallRC!=0)
    # ------------------------------------------------------------------
    @mock.patch(_EXEC_CMD_IUCV)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_softdeactivate_failure_prints_and_updates_results(
            self, mock_handler_cls, mock_iucv):
        """
        When use_smapi is False and deactivate fails (overallRC!=0),
        rh.printLn("ES", response) and rh.updateResults(results) must be
        called with the failure results captured from rh.results.
        """
        self._set_use_smapi(False)

        mock_iucv.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0,
                                  'response': ''}

        error_results = {
            'overallRC': 4, 'response': 'HCP045E TESTUSER not logged on'}
        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = error_results

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.softDeactivate(rh)

        rh.printLn.assert_called_once_with("ES", error_results['response'])
        rh.updateResults.assert_called_with(error_results)

    # ------------------------------------------------------------------
    # Scenario 4: use_smapi=False — invokeSMCLI not called for logoff
    # ------------------------------------------------------------------
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_EXEC_CMD_IUCV)
    @mock.patch(_VMCP_HANDLER)
    def test_vmcp_softdeactivate_does_not_call_smcli_for_logoff(
            self, mock_handler_cls, mock_iucv, mock_smcli):
        """
        When use_smapi is False, Image_Deactivate via invokeSMCLI must
        never be called for the logoff step.
        """
        self._set_use_smapi(False)

        mock_iucv.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0,
                                  'response': ''}

        mock_handler_instance = mock.MagicMock()
        mock_handler_cls.return_value = mock_handler_instance
        mock_handler_instance.deactivate.return_value = {
            'overallRC': 0, 'response': ''}

        rh = _make_rh()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}

        powerVM.softDeactivate(rh)

        called_apis = [call.args[1] for call in mock_smcli.call_args_list]
        self.assertNotIn("Image_Deactivate", called_apis)

    # ------------------------------------------------------------------
    # Scenario 5: use_smapi=True — VMCPHandler never instantiated
    # ------------------------------------------------------------------
    @mock.patch(_INVOKE_SMCLI)
    @mock.patch(_EXEC_CMD_IUCV)
    @mock.patch(_VMCP_HANDLER)
    def test_smapi_softdeactivate_path_does_not_use_vmcp_handler(
            self, mock_handler_cls, mock_iucv, mock_smcli):
        """
        When use_smapi is True, the SMAPI path is taken and VMCPHandler
        must never be instantiated.
        """
        self._set_use_smapi(True)

        mock_iucv.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0,
                                  'response': ''}
        mock_smcli.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0,
                                   'response': ''}

        rh = _make_rh()
        powerVM.softDeactivate(rh)

        mock_handler_cls.assert_not_called()
        called_apis = [call.args[1] for call in mock_smcli.call_args_list]
        self.assertIn("Image_Deactivate", called_apis)
