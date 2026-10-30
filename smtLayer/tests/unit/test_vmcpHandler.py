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

from smtLayer import ReqHandle
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import VMCPHandler
from zvmsdk import exception

_SSI_CLUSTER_OUTPUT = """\
SSI Name: TESTSSI
SSI Mode: Stable
Cross-System Timeouts: Enabled
SSI Persistent Data Record (PDR) device: 1111 on VOL001

Slot System ID  State   PDR Heartbeat        Received Heartbeat
   1 SYS1       JOINED  01/02/26 10:00:00 01/02/26 10:00:01
   2 --------   DOWN
"""


class VMCPHandlerTest(base.SMTTestCase):
    """Unit tests for smtLayer/vmcpHandler.py."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.rh.userid = "TESTUSER"
        self.handler = VMCPHandler(self.rh)

    def _patch_run(self, response="", rc=0):
        """Patch VMCPHandler._run to return a canned result."""
        return mock.patch.object(
            self.handler, '_run',
            return_value={"response": response, "overallRC": rc},
        )

    def test_init_stores_rh(self):
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        handler = VMCPHandler(rh)
        self.assertIs(rh, handler._rh)

    @mock.patch('subprocess.check_output', return_value=b"CP output line\n")
    def test_run_success_returns_decoded_output(self, mock_check):
        result = self.handler._run(["query", "userid"])
        self.assertEqual(0, result["overallRC"])
        self.assertEqual("CP output line\n", result["response"])

    @mock.patch('subprocess.check_output', return_value=b"CP output\n")
    def test_run_builds_correct_sudo_command(self, mock_check):
        self.handler._run(["query", "pcif"])
        mock_check.assert_called_once_with(
            ["sudo", "/sbin/vmcp", "query", "pcif"],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_returns_nonzero_rc(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=8, cmd="vmcp", output=b"HCP001E Invalid command\n")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(8, result["overallRC"])
        self.assertEqual("", result["response"])
        self.assertNotIn("output", result)

    @mock.patch('subprocess.check_output')
    def test_run_output_returns_cp_output_on_failure(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=8, cmd="vmcp", output=b"HCP045E User not logged on\n")
        result = self.handler._run(["VMRELOCATE", "MOVE", "X"],
                                   output=True)
        self.assertEqual(8, result["overallRC"])
        self.assertEqual("HCP045E User not logged on\n", result["output"])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_records_msg_0405(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"err\n")
        self.handler._run(["query", "pcif"])
        self.assertNotEqual(0, self.rh.results['overallRC'])

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception_returns_rc_1(self, mock_check):
        mock_check.side_effect = OSError("binary not found")
        result = self.handler._run(["query", "pcif"])
        self.assertEqual(1, result["overallRC"])
        self.assertEqual("", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_tolerated_pattern_matches_returns_rc_0(self, mock_check):
        """A CalledProcessError whose output matches the tolerated pattern
        must be swallowed: overallRC stays 0 and the raw output is returned."""
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="vmcp",
            output=b"HCPabc054E TESTUSER is already logged on\n")
        result = self.handler._run(
            ["xautolog", "TESTUSER"],
            tolerated=r'^HCP\w\w\w054E',
        )
        self.assertEqual(0, result["overallRC"])
        self.assertIn("054E", result["response"])

    @mock.patch('subprocess.check_output')
    def test_run_tolerated_pattern_no_match_returns_failure(self, mock_check):
        """An error whose output does NOT match the tolerated pattern must
        still propagate as a failure."""
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="vmcp",
            output=b"HCPabc025E Cannot XAUTOLOG TESTUSER\n")
        result = self.handler._run(
            ["xautolog", "TESTUSER"],
            tolerated=r'^HCP\w\w\w054E',
        )
        self.assertEqual(1, result["overallRC"])

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

    def test_run_failure_raises(self):
        with self._patch_run("", rc=8):
            with self.assertRaises(exception.SDKSMTRequestFailed) as cm:
                self.handler.query_pcif()
        self.assertIs(self.rh.results, cm.exception.results)

    def test_returns_empty_list_on_empty_output(self):
        with self._patch_run(""):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_pci_function_not_found_raises(self):
        with self._patch_run("A PCI function was not found.\n"):
            with self.assertRaises(exception.SDKSMTRequestFailed) as cm:
                self.handler.query_pcif()
        self.assertIs(self.rh.results, cm.exception.results)
        self.assertNotEqual(0, self.rh.results['overallRC'])

    def test_pci_function_not_found_with_rc_nonzero_is_run_failure(self):
        with self._patch_run("A PCI function was not found.\n", rc=8):
            with self.assertRaises(exception.SDKSMTRequestFailed):
                self.handler.query_pcif()

    def test_pcif_at_end_of_line_skipped(self):
        output = "SOMETHING PCIF\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_missing_state_token_skipped(self):
        output = "PCIF 00000110 FREE NETH\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    def test_no_type_after_state_skipped(self):
        output = "PCIF 00000110 FREE ENABLED\n"
        with self._patch_run(output):
            result = self.handler.query_pcif()
        self.assertEqual([], result)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_activate_already_logged_on_skips_xautolog(self, mock_logged):
        mock_logged.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run() as mock_run:
            result = self.handler.activate("TESTUSER")
            mock_run.assert_not_called()
        self.assertEqual(0, result["overallRC"])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_activate_logged_off_issues_xautolog(self, mock_logged):
        mock_logged.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        with self._patch_run("Command accepted\n", rc=0) as mock_run:
            result = self.handler.activate("TESTUSER")
            mock_run.assert_called_once_with(
                ["xautolog", "TESTUSER"],
                tolerated=mock.ANY,
            )
        self.assertEqual(0, result["overallRC"])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_activate_xautolog_failure_propagates_rc(self, mock_logged):
        mock_logged.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        with self._patch_run("HCP045E TESTUSER not active\n", rc=1):
            result = self.handler.activate("TESTUSER")
        self.assertEqual(1, result["overallRC"])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_activate_isloggedon_failure_still_issues_xautolog(self, mock_logged):
        """When isLoggedOn itself fails the activate path falls through
        and still attempts the XAUTOLOG."""
        mock_logged.return_value = {'overallRC': 1, 'rc': 1, 'rs': 0}
        with self._patch_run("Command accepted\n", rc=0) as mock_run:
            result = self.handler.activate("TESTUSER")
            mock_run.assert_called_once()
        self.assertEqual(0, result["overallRC"])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_activate_hcp054e_tolerated(self, mock_logged):
        """A race-condition HCP054E (already logged on) must be tolerated."""
        mock_logged.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        tolerated_output = "HCPxxx054E TESTUSER is already logged on\n"
        with self._patch_run(tolerated_output, rc=0):
            result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result["overallRC"])

    def test_query_image_performance_computes_memory_in_use(self):
        frames_output = (
            "Storage Frames:\n"
            "Configured=10000000\n"
            "GlobalClearedAvail=1000000\n"
            "LocalClearedAvail=500000\n"
            "GlobalUnclearedAvail=300000\n"
            "LocalUnclearedAvail=200000\n"
        )
        with self._patch_run(frames_output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual(0, result["overallRC"])
        self.assertEqual("MEMORY_IN_USE=8000000", result["response"])

    def test_query_image_performance_computes_memory_in_use_with_multiple_sections(self):
        # Real QUERY FRAMES output on z/VM includes a "Storage Frames Below 2G:"
        # section. query_image_performance must only count the top-level section.
        frames_output = (
            "Storage Frames:\n"
            "  Configured=10000000\n"
            "  GlobalClearedAvail=1000000\n"
            "  LocalClearedAvail=500000\n"
            "  GlobalUnclearedAvail=300000\n"
            "  LocalUnclearedAvail=200000\n"
            "Storage Frames Below 2G:\n"
            "  Configured=524288\n"
            "  GlobalClearedAvail=10000\n"
            "  LocalClearedAvail=5000\n"
            "  GlobalUnclearedAvail=3000\n"
            "  LocalUnclearedAvail=2000\n"
        )
        with self._patch_run(frames_output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual(0, result["overallRC"])
        # Configured (10000000) - (1000000 + 500000 + 300000 + 200000 = 2000000) = 8000000
        self.assertEqual("MEMORY_IN_USE=8000000", result["response"])

    def test_query_image_performance_run_failure_propagates(self):
        with self._patch_run("vmcp: command failed\n", rc=1):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_image_performance_no_free_fields_means_all_used(self):
        output = "Configured=4096\n"
        with self._patch_run(output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual("MEMORY_IN_USE=4096", result["response"])

    def test_query_image_performance_empty_output_returns_zero(self):
        with self._patch_run("", rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual("MEMORY_IN_USE=0", result["response"])

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
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_not_called()
            self.assertEqual(0, self.rh.results['overallRC'])
            self.assertEqual({"response": "", "overallRC": 0}, result)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_no_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER", force=False)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_logged_on_with_force(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER", force=True)
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff", "IMMED"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_guest_is_logged_on_failed_acts_as_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 1, 'rc': 1, 'rs': 1}
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_uses_userid_arg_not_rh_userid(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        self.assertEqual("TESTUSER", self.rh.userid)
        with self._patch_run("", rc=0) as mock_run:
            self.handler.deactivate("OTHERUSR", force=True)
            mock_is_logged_on.assert_called_once_with(self.rh, "OTHERUSR")
            mock_run.assert_called_once_with(
                ["force", "OTHERUSR", "logoff", "IMMED"],
                tolerated=mock.ANY)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_run_returns_failure_rc(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=8) as mock_run:
            result = self.handler.deactivate("TESTUSER")
            mock_is_logged_on.assert_called_once_with(self.rh, "TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=mock.ANY)
            self.assertEqual(8, result['overallRC'])

    def test_ssi_info_not_member_returns_empty_list(self):
        with self._patch_run(
                "This system is not a member of an SSI cluster.\n", rc=0):
            result = self.handler.ssi_info()
        self.assertEqual(0, result["rc"])
        self.assertEqual([], result["response"])

    def test_ssi_info_cluster_header_fields(self):
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        self.assertEqual(0, result["rc"])
        self.assertIn("ssi_name = TESTSSI", lines)
        self.assertIn("ssi_mode = Stable", lines)
        self.assertIn("cross_system_timeouts = Enabled", lines)
        self.assertIn("ssi_pdr = 1111_on_VOL001", lines)

    def test_ssi_info_member_count(self):
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        self.assertIn("output.ssiInfoCount = 2", result["response"])

    def test_ssi_info_active_member_fields(self):
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        self.assertIn("member_slot = 1", lines)
        self.assertIn("member_system_id = SYS1", lines)
        self.assertIn("member_state = JOINED", lines)
        self.assertIn("member_pdr_heartbeat = 01/02/26_10:00:00", lines)
        self.assertIn("member_received_heartbeat = 01/02/26_10:00:01", lines)

    def test_ssi_info_down_member_system_id_mapped_to_na(self):
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        self.assertIn("member_slot = 2", lines)
        self.assertIn("member_system_id = N/A", lines)
        self.assertIn("member_state = DOWN", lines)

    def test_ssi_info_down_member_heartbeats_na(self):
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        slot2_idx = lines.index("member_slot = 2")
        self.assertEqual("member_pdr_heartbeat = N/A",
                         lines[slot2_idx + 3])
        self.assertEqual("member_received_heartbeat = N/A",
                         lines[slot2_idx + 4])

    def test_ssi_info_run_failure_returns_nonzero_rc(self):
        with self._patch_run("", rc=1):
            result = self.handler.ssi_info()
        self.assertEqual(1, result["rc"])

    def test_query_attach_read_write_command(self):
        self.rh.parms = {'vaddr': '1000', 'raddr': '2000', 'mode': 0}
        with self._patch_run("Device 2000 attached to TESTUSER as 1000\n",
                             rc=0) as mock_run:
            result = self.handler.query_attach(self.rh)
            mock_run.assert_called_once_with(
                ["ATTACH", "1000", "TO", "TESTUSER", "AS", "2000"])
        self.assertEqual(0, result["overallRC"])

    def test_query_attach_read_only_appends_readonly_keyword(self):
        self.rh.parms = {'vaddr': '1000', 'raddr': '2000', 'mode': 1}
        with self._patch_run("Device attached readonly\n",
                             rc=0) as mock_run:
            self.handler.query_attach(self.rh)
            mock_run.assert_called_once_with(
                ["ATTACH", "1000", "TO", "TESTUSER", "AS", "2000",
                 "READONLY"])

    def test_query_attach_mode_string_one_treated_as_read_only(self):
        self.rh.parms = {'vaddr': '0A00', 'raddr': '1A00', 'mode': '1'}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_attach(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("READONLY", args)

    def test_query_attach_failure_rc_propagated(self):
        self.rh.parms = {'vaddr': '1000', 'raddr': '2000', 'mode': 0}
        with self._patch_run("HCP040E Device 2000 not found\n", rc=1):
            result = self.handler.query_attach(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_detach_command(self):
        self.rh.parms = {'vaddr': '1000'}
        with self._patch_run("Device 1000 detached\n", rc=0) as mock_run:
            result = self.handler.query_detach(self.rh)
            mock_run.assert_called_once_with(
                ["DETACH", "1000", "FROM", "TESTUSER"],
                tolerated=mock.ANY,
            )
        self.assertEqual(0, result["overallRC"])

    def test_query_detach_already_detached_tolerated(self):
        self.rh.parms = {'vaddr': '1000'}
        tolerated_output = "HCP040E Device 1000 does not exist\n"
        with self._patch_run(tolerated_output, rc=0):
            result = self.handler.query_detach(self.rh)
        self.assertEqual(0, result["overallRC"])

    def test_query_detach_failure_rc_propagated(self):
        self.rh.parms = {'vaddr': '1000'}
        with self._patch_run("HCP999E Detach error\n", rc=1):
            result = self.handler.query_detach(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_relocate_minimal_command(self):
        self.rh.parms = {}
        with self._patch_run("Relocation started\n", rc=0) as mock_run:
            result = self.handler.query_relocate(self.rh)
            mock_run.assert_called_once_with(
                ["VMRELOCATE", "MOVE", "TESTUSER", "SYNCHRONOUS"], output=True)
        self.assertEqual(0, result["overallRC"])

    def test_query_relocate_with_destination(self):
        self.rh.parms = {'dest': 'SYS2'}
        with self._patch_run("Relocation started\n", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("TO", args)
        self.assertIn("SYS2", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_force_options(self):
        self.rh.parms = {
            'dest': 'SYS2',
            'forcearch': True,
            'forcedomain': True,
            'forcestorage': True,
        }
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("FORCE", args)
        self.assertIn("ARCHITECTURE", args)
        self.assertIn("DOMAIN", args)
        self.assertIn("STORAGE", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_immediate(self):
        self.rh.parms = {'immediate': True}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("IMMEDIATE", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_max_total_seconds(self):
        self.rh.parms = {'maxTotal': 120}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXTotal", args)
        self.assertIn("120", args)
        self.assertIn("SEC", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_max_total_nolimit(self):
        self.rh.parms = {'maxTotal': -1}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXTotal", args)
        self.assertIn("NOLIMIT", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_max_quiesce_seconds(self):
        self.rh.parms = {'maxQuiesce': 10}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXQuiesce", args)
        self.assertIn("10", args)
        self.assertIn("SEC", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_max_quiesce_nolimit(self):
        self.rh.parms = {'maxQuiesce': -1}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXQuiesce", args)
        self.assertIn("NOLIMIT", args)
        self.assertIn("SYNCHRONOUS", args)

    def test_query_relocate_all_options_combined(self):
        self.rh.parms = {
            'dest': 'SYS2',
            'forcearch': True,
            'forcedomain': True,
            'forcestorage': True,
            'immediate': True,
            'maxTotal': 120,
            'maxQuiesce': 10,
        }
        with self._patch_run("", rc=0) as mock_run:
            result = self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertEqual(0, result["overallRC"])
        for token in ("TO", "SYS2", "FORCE", "ARCHITECTURE", "DOMAIN",
                      "STORAGE", "IMMEDIATE", "MAXTotal", "120", "SEC",
                      "MAXQuiesce", "10", "SYNCHRONOUS"):
            self.assertIn(token, args)

    def test_query_relocate_failure_rc_propagated(self):
        self.rh.parms = {'dest': 'SYS2'}
        with self._patch_run("HCP2627E Relocation failed\n", rc=1):
            result = self.handler.query_relocate(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_vswitch_details_single_vswitch_nic_stats(self):
        vsw_output = (
            "VSWITCH SYSTEM VSICIC  Type: QDIO  Connected: 1  Maxconn: INFINITE\n"
            "  PERSISTENT  RESTRICTED  NOLEARN  VLAN: UNAWARE\n"
            "  Uplink Ports:\n"
            "  Adapter Connections:\n"
            "  Adapter Owner: TESTUSER  NIC: 1000  Name: NIC1\n"
            "    RX Packets: 100 Discarded: 2 Errors: 1\n"
            "    TX Packets: 200 Discarded: 4 Errors: 2\n"
            "    RX Bytes: 1024 TX Bytes: 2048\n"
        )
        with self._patch_run(vsw_output, rc=0) as mock_run:
            result = self.handler.query_vswitch_details()
            mock_run.assert_called_once_with(["QUERY", "VSWITCH", "DETAILS"])

        self.assertEqual(0, result["rc"])
        parsed = result["response"]
        self.assertEqual(1, parsed["vswitch_count"])
        self.assertEqual(1, len(parsed["vswitches"]))

        vsw = parsed["vswitches"][0]
        self.assertEqual("VSICIC", vsw["vswitch_name"])
        self.assertEqual(1, len(vsw["nics"]))

        nic = vsw["nics"][0]
        self.assertEqual("TESTUSER", nic["userid"])
        self.assertEqual("1000", nic["vdev"])
        self.assertEqual("100", nic["nic_fr_rx"])
        self.assertEqual("2", nic["nic_fr_rx_dsc"])
        self.assertEqual("1", nic["nic_fr_rx_err"])
        self.assertEqual("200", nic["nic_fr_tx"])
        self.assertEqual("4", nic["nic_fr_tx_dsc"])
        self.assertEqual("2", nic["nic_fr_tx_err"])
        self.assertEqual("1024", nic["nic_rx"])
        self.assertEqual("2048", nic["nic_tx"])

    def test_query_vswitch_details_multi_vswitch_and_nics(self):
        multi_output = (
            "VSWITCH SYSTEM VSWITCH1  Type: QDIO  Connected: 2  Maxconn: INFINITE\n"
            "  Adapter Connections:\n"
            "  Adapter Owner: USER1  NIC: 1000  Name: NIC1\n"
            "    RX Packets: 10 Discarded: 0 Errors: 0\n"
            "    TX Packets: 20 Discarded: 0 Errors: 0\n"
            "    RX Bytes: 100 TX Bytes: 200\n"
            "  Adapter Owner: USER2  NIC: 2000  Name: NIC2\n"
            "    RX Packets: 30 Discarded: 1 Errors: 0\n"
            "    TX Packets: 40 Discarded: 0 Errors: 1\n"
            "    RX Bytes: 300 TX Bytes: 400\n"
            "VSWITCH SYSTEM VSWITCH2  Type: QDIO  Connected: 1  Maxconn: INFINITE\n"
            "  Adapter Connections:\n"
            "  Adapter Owner: USER3  NIC: 3000  Name: NIC3\n"
            "    RX Packets: 50 Discarded: 0 Errors: 0\n"
            "    TX Packets: 60 Discarded: 0 Errors: 0\n"
            "    RX Bytes: 500 TX Bytes: 600\n"
        )
        with self._patch_run(multi_output, rc=0):
            result = self.handler.query_vswitch_details()

        parsed = result["response"]
        self.assertEqual(2, parsed["vswitch_count"])
        self.assertEqual(2, len(parsed["vswitches"][0]["nics"]))
        self.assertEqual(1, len(parsed["vswitches"][1]["nics"]))

        vsw1_nic0 = parsed["vswitches"][0]["nics"][0]
        self.assertEqual("USER1", vsw1_nic0["userid"])
        self.assertEqual("1000", vsw1_nic0["vdev"])

        vsw1_nic1 = parsed["vswitches"][0]["nics"][1]
        self.assertEqual("USER2", vsw1_nic1["userid"])
        self.assertEqual("2000", vsw1_nic1["vdev"])
        self.assertEqual("300", vsw1_nic1["nic_rx"])

        vsw2_nic0 = parsed["vswitches"][1]["nics"][0]
        self.assertEqual("VSWITCH2", parsed["vswitches"][1]["vswitch_name"])
        self.assertEqual("USER3", vsw2_nic0["userid"])

    def test_query_vswitch_details_empty_output_returns_empty_list(self):
        with self._patch_run("", rc=0):
            result = self.handler.query_vswitch_details()
        self.assertEqual(0, result["rc"])
        self.assertEqual(0, result["vswitch_count"])
        self.assertEqual([], result["vswitches"])

    def test_query_vswitch_details_run_failure_returns_empty(self):
        with self._patch_run("vmcp: not found\n", rc=1):
            result = self.handler.query_vswitch_details()
        self.assertEqual(1, result["rc"])
        self.assertEqual(0, result["vswitch_count"])
        self.assertEqual([], result["vswitches"])

    def test_query_vswitch_details_nic_default_counters_are_zero_strings(self):
        bare_output = (
            "VSWITCH SYSTEM VSWONLY  Type: QDIO  Connected: 1\n"
            "  Adapter Connections:\n"
            "  Adapter Owner: ZUSER  NIC: 0A00  Name: NIC1\n"
        )
        with self._patch_run(bare_output, rc=0):
            result = self.handler.query_vswitch_details()
        nic = result["response"]["vswitches"][0]["nics"][0]
        for key in ("nic_fr_rx", "nic_fr_rx_dsc", "nic_fr_rx_err",
                    "nic_fr_tx", "nic_fr_tx_dsc", "nic_fr_tx_err",
                    "nic_rx", "nic_tx"):
            self.assertEqual("0", nic[key],
                             msg="%s should default to '0'" % key)


def _make_rh(userid="TESTUSER"):
    """Return a lightweight mock ReqHandle."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.userid = userid
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
    rh.parms = {}
    return rh


class VMCPHandlerRunForTestCase(base.SMTTestCase):
    """Tests for VMCPHandler._run_for()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('subprocess.check_output')
    def test_run_for_success(self, mock_co):
        mock_co.return_value = b'NIC 0600 TYPE QDIO\n'
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(0, result['overallRC'])
        self.assertEqual(0, result['rc'])
        self.assertIn('NIC', result['response'])
        mock_co.assert_called_once_with(
            ['sudo', '/sbin/vmcp',
             'FOR TESTUSER CMD DEFINE NIC 0600 TYPE QDIO'],
            close_fds=True, stderr=subprocess.STDOUT)

    @mock.patch('subprocess.check_output')
    def test_run_for_calledprocesserror(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b'HCP045E')
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(1, result['overallRC'])
        self.assertEqual(1, result['rc'])
        self.assertEqual('HCP045E', result['strError'])

    @mock.patch('subprocess.check_output')
    def test_run_for_generic_exception(self, mock_co):
        mock_co.side_effect = OSError('vmcp not found')
        result = self.handler._run_for('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('vmcp not found', result['strError'])


class VMCPHandlerGetCPUCountTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.get_cpu_count()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_success(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': (
                'PROCESSOR 0000 MASTER IFL  CORE 0000\n'
                'PROCESSOR 0001 ALTERNATE IFL CORE 0001\n'
                'PROCESSOR 0002 PARKED IFL CORE 0002\n'
                'PROCESSOR 0003 STANDBY IFL CORE 0003\n'
                'PROCESSOR 0004 MASTER CP CORE 0004\n'
            )
        }
        total, use = self.handler.get_cpu_count()
        self.assertEqual(5, total)
        self.assertEqual(4, use)

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_failure(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        total, use = self.handler.get_cpu_count()
        self.assertEqual(0, total)
        self.assertEqual(0, use)


class VMCPHandlerPurgeRDRTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.purge_reader()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_purge_reader_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': '0001 FILES PURGED'}
        result = self.handler.purge_reader()
        mock_run.assert_called_once_with(['PURGE', 'TESTUSER', 'RDR', 'ALL'])
        self.assertEqual(0, result['overallRC'])


class VMCPHandlerCreateNICTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.create_nic_for_guest()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_success(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 0, 'response': ''}
        mock_run.return_value = {'overallRC': 0, 'response': 'NIC 0600'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(0, result['overallRC'])
        mock_run_for.assert_called_once_with('TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        mock_run.assert_called_once_with(['QUERY', 'NIC', 'USERID', 'TESTUSER', '0600'])

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_define_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 1, 'response': 'HCP001E'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(1, result['overallRC'])
        mock_run.assert_not_called()

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_verify_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 0, 'response': ''}
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP040E'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(2, result['overallRC'])
        self.assertTrue(result['nic_not_created'])


class VMCPHandlerAddDiskTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.add_disk()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_add_disk_success(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 0, 'response': 'DASD 0100 LINKED'}
        mock_run.return_value = {'overallRC': 0, 'response': 'MDISK 0100 3390'}
        result = self.handler.add_disk('0100', 'MR')
        self.assertEqual(0, result['overallRC'])
        mock_run_for.assert_called_once_with('TESTUSER', 'LINK * 0100 0100 MR')
        mock_run.assert_called_once_with(
            ['QUERY', 'MDISK', 'USERID', 'TESTUSER', '0100', 'DETAILS'])

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_add_disk_link_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 1, 'response': 'HCP001E'}
        result = self.handler.add_disk('0100', 'MR')
        self.assertEqual(1, result['overallRC'])
        mock_run.assert_not_called()

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_add_disk_verify_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'overallRC': 0, 'response': ''}
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP040E'}
        result = self.handler.add_disk('0100', 'MR')
        self.assertEqual(2, result['overallRC'])
        self.assertTrue(result['disk_not_linked'])


class VMCPHandlerQueryFCPTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_fcp_formatted()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_fcp_formatted_success(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': (
                'FCP 1A00 NPIV WWPN C05076DE00000001\n'
                'CHPID 20 PERM WWPN C05076DE00000002\n'
                'ATTACHED TO USER1\n'
                'FCP 1A01 NPIV WWPN C05076DE00000003\n'
                'CHPID 21 PERM WWPN C05076DE00000004\n'
                'FREE\n'
            )
        }
        result = self.handler.query_fcp_formatted()
        self.assertEqual(0, result['overallRC'])
        self.assertIn('FCP device number: 1A00', result['response'])
        self.assertIn('Status: Active', result['response'])
        self.assertIn('Owner: USER1', result['response'])
        self.assertIn('FCP device number: 1A01', result['response'])
        self.assertIn('Status: Free', result['response'])
        self.assertIn('Owner: NONE', result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_fcp_formatted_failure(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        result = self.handler.query_fcp_formatted()
        self.assertEqual(1, result['overallRC'])
        self.assertEqual(4, result['rc'])
        self.assertEqual(28, result['rs'])


class VMCPHandlerQueryOSATestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_osa()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_success(self, mock_run):
        mock_run.side_effect = [
            {
                'overallRC': 0,
                'response': 'OSA  3000 ATTACHED TO SYSTEM   3000 DEVTYPE OSH CHPID 70\n'
            },
            {
                'overallRC': 0,
                'response': 'OSA 3004 FREE, OSA 3005 FREE\n'
            }
        ]
        result = self.handler.query_osa()
        self.assertIn('OSA', result)
        self.assertEqual([('SYSTEM', '3000')], result['OSA']['ATTACHED'])
        self.assertIn('3004', result['OSA']['FREE'])
        self.assertIn('3005', result['OSA']['FREE'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_free_query_fails(self, mock_run):
        mock_run.side_effect = [
            {
                'overallRC': 0,
                'response': 'OSA  3000 ATTACHED TO SYSTEM   3000 DEVTYPE OSH CHPID 70\n'
            },
            {'overallRC': 1, 'response': ''}
        ]
        result = self.handler.query_osa()
        self.assertIn('OSA', result)
        self.assertEqual(1, len(result['OSA']['ATTACHED']))
        self.assertEqual([], result['OSA']['FREE'])
