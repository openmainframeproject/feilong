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

    def test_attached_enabled_line(self):
        output = "PCIF 00000110 ATTACHED TO MALR003F 00000110 ENABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(1, len(result))
        self.assertEqual({"pcif": "00000110", "status": "ATTACHED",
                          "userid": "MALR003F", "state": "ENABLED",
                          "type": "NETH"}, result[0])

    def test_free_enabled_line(self):
        output = "PCIF 00000120 FREE ENABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(1, len(result))
        self.assertEqual({"pcif": "00000120", "status": "FREE",
                          "userid": "", "state": "ENABLED",
                          "type": "NETH"}, result[0])

    def test_attached_disabled_line(self):
        output = "PCIF 00000130 ATTACHED TO TESTVM 00000130 DISABLED NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        entry = result[0]
        self.assertEqual("DISABLED", entry["state"])
        self.assertEqual("TESTVM", entry["userid"])

    def test_multiple_lines_all_returned(self):
        output = (
            "PCIF 00000110 ATTACHED TO VM001 00000110 ENABLED NETH\n"
            "PCIF 00000120 FREE ENABLED NETH\n"
            "PCIF 00000130 FREE DISABLED NETH\n"
        )
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual(3, len(result))

    def test_calls_run_with_query_pcif_args(self):
        with self._patch_run("") as mock_run:
            self.handler.query_pcif()
        mock_run.assert_called_once_with(["query", "pcif"])

    def test_returns_empty_list_when_run_fails(self):
        with self._patch_run("", rc=8):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_returns_empty_list_on_empty_output(self):
        with self._patch_run(""):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_pcif_at_end_of_line_skipped(self):
        # no device number after PCIF
        output = "SOMETHING PCIF\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_missing_state_token_skipped(self):
        # no ENABLED / DISABLED
        output = "PCIF 00000110 FREE NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_no_type_after_state_skipped(self):
        # ENABLED is the last token
        output = "PCIF 00000110 FREE ENABLED\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)
