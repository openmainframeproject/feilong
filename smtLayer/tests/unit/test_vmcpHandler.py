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

import subprocess
from unittest import mock

from smtLayer import msgs
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import VMCPHandler


def _make_rh():
    """Return a lightweight mock ReqHandle."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.userid = "TESTUSER"
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': []}
    return rh


class VMCPHandlerTest(base.SMTTestCase):

    def test_init_stores_rh(self):
        rh = _make_rh()
        handler = VMCPHandler(rh)
        self.assertIs(rh, handler._rh)

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('subprocess.check_output', return_value=b"OK OUTPUT\n")
    def test_run_success_rc_0(self, _mock):
        result = self.handler._run(["query", "userid"])
        self.assertEqual(0, result["overallRC"])
        self.assertEqual("OK OUTPUT\n", result["response"])

    @mock.patch('subprocess.check_output', return_value=b"")
    def test_run_builds_correct_command(self, mock_check):
        self.handler._run(["query", "pcif"])
        mock_check.assert_called_once_with(
            ["sudo", "/sbin/vmcp", "query", "pcif"],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_returns_nonzero_rc(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=8, cmd="vmcp", output=b"error")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(8, result["overallRC"])
        self.assertEqual("", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_updates_results(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"err")
        self.handler._run(["query", "pcif"])
        self.rh.updateResults.assert_called_once_with(msgs.msg['0405'][0])

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception_returns_rc_1(self, mock_check):
        mock_check.side_effect = OSError("not found")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(1, result["overallRC"])
        self.assertEqual("", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception_updates_results(self, mock_check):
        mock_check.side_effect = RuntimeError("boom")
        self.handler._run(["query", "pcif"])
        self.rh.updateResults.assert_called_once_with(msgs.msg['0421'][0])

    def _patch_run(self, response, rc=0):
        return mock.patch.object(
            self.handler, '_run',
            return_value={"response": response, "overallRC": rc},
        )

    def test_query_storage_success(self):
        output = "STORAGE = 65536M  STANDBY = 0  REMAINDER = 0"
        with self._patch_run(output, rc=0) as mock_run:
            result = self.handler.query_storage()
            mock_run.assert_called_once_with(["query", "storage"])
            self.assertEqual("65536M", result["lparMemTotal"])
            self.assertEqual("0", result["lparMemStandby"])

    def test_query_storage_missing_standby(self):
        output = "STORAGE = 32G"
        with self._patch_run(output, rc=0):
            result = self.handler.query_storage()
            self.assertEqual("32G", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_storage_malformed_output(self):
        output = "STORAGE"
        with self._patch_run(output, rc=0):
            result = self.handler.query_storage()
            self.assertEqual("no info", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_storage_error_rc(self):
        with self._patch_run("", rc=1):
            result = self.handler.query_storage()
            self.assertEqual("no info", result["lparMemTotal"])
            self.assertEqual("no info", result["lparMemStandby"])

    def test_query_cplevel_success(self):
        output = "z/VM Version 7 Release 2.0 00/00/00 (64-bit)\nIPL at 01/15/24 08:30:00 EST\n"
        with self._patch_run(output, rc=0) as mock_run:
            ipl = self.handler.query_cplevel()
            mock_run.assert_called_once_with(["query", "cplevel"])
            self.assertEqual("IPL at 01/15/24 08:30:00 EST", ipl)

    def test_query_cplevel_no_ipl_line(self):
        output = "z/VM Version 7 Release 2.0 00/00/00 (64-bit)\n"
        with self._patch_run(output, rc=0):
            ipl = self.handler.query_cplevel()
            self.assertEqual("", ipl)

    def test_query_cplevel_error_rc(self):
        with self._patch_run("", rc=1):
            ipl = self.handler.query_cplevel()
            self.assertEqual("", ipl)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_not_logged_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        with self._patch_run("", rc=0) as mock_run:
            rc = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_not_called()
            self.rh.updateResults.assert_called_once_with(
                {'overallRC': 0, 'rc': 0, 'rs': 0})
            self.assertEqual(0, rc)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_no_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            rc = self.handler.deactivate("TESTUSER", force=False)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(["force", "TESTUSER", "logoff"])
            self.assertEqual(0, rc)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_with_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            rc = self.handler.deactivate("TESTUSER", force=True)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(["force", "TESTUSER", "logoff", "IMMED"])
            self.assertEqual(0, rc)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_is_logged_on_failed_acts_as_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 1, 'rc': 1, 'rs': 1}
        with self._patch_run("", rc=0) as mock_run:
            rc = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(["force", "TESTUSER", "logoff"])
            self.assertEqual(0, rc)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_run_returns_failure_rc(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=8) as mock_run:
            rc = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(["force", "TESTUSER", "logoff"])
            self.assertEqual(8, rc)
