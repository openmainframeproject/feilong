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
        # Real vmcp QUERY FRAMES output (z/VM 7.2).
        # Two GlobalUnclearedAvail lines exercise the findall accumulation.
        # Expected: 10000000 - (1000000+500000+200000+300000+100000) = 7900000
        frames_output = (
            "Storage Frames:\n"
            "Configured=10000000\n"
            "GlobalClearedAvail=1000000\n"
            "LocalClearedAvail=500000\n"
            "LocalUnclearedAvail=200000\n"
            "GlobalUnclearedAvail=300000\n"
            "GlobalUnclearedAvail=100000\n"
        )
        with self._patch_run(frames_output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual(0, result["overallRC"])
        self.assertEqual("MEMORY_IN_USE=7900000", result["response"])

    def test_query_image_performance_run_failure_propagates(self):
        with self._patch_run("vmcp: command failed\n", rc=1):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_image_performance_no_free_fields_means_all_used(self):
        """If none of the avail fields are present, free_frames stays 0
        so MEMORY_IN_USE equals Configured."""
        output = "Configured=4096\n"
        with self._patch_run(output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual("MEMORY_IN_USE=4096", result["response"])

    def test_query_image_performance_empty_output_returns_zero(self):
        """Totally empty output: both configured and free default to 0."""
        with self._patch_run("", rc=0):
            result = self.handler.query_image_performance(self.rh)
        self.assertEqual("MEMORY_IN_USE=0", result["response"])

    def test_query_image_performance_multiple_global_uncleared(self):
        """findall must accumulate every GlobalUnclearedAvail line."""
        output = (
            "Configured=1000\n"
            "GlobalUnclearedAvail=100\n"
            "GlobalUnclearedAvail=200\n"
        )
        with self._patch_run(output, rc=0):
            result = self.handler.query_image_performance(self.rh)
        # 1000 - 300 = 700
        self.assertEqual("MEMORY_IN_USE=700", result["response"])

    def test_ssi_info_not_member_returns_empty_list(self):
        # Real vmcp QUERY SSI output when the host has no SSI cluster.
        with self._patch_run(
                "This system is not a member of an SSI cluster.\n", rc=0):
            result = self.handler.ssi_info()
        self.assertEqual(0, result["rc"])
        self.assertEqual([], result["response"])

    def test_ssi_info_cluster_header_fields(self):
        # Verifies SSI name, mode, PDR device, and cross-system timeouts.
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
        # Joined member: real heartbeat timestamps must be preserved as-is.
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        self.assertIn("member_slot = 1", lines)
        self.assertIn("member_system_id = SYS1", lines)
        self.assertIn("member_state = JOINED", lines)
        self.assertIn("member_pdr_heartbeat = 01/02/26_10:00:00", lines)
        self.assertIn("member_received_heartbeat = 01/02/26_10:00:01", lines)

    def test_ssi_info_down_member_system_id_mapped_to_na(self):
        # '--------' system-id must be normalised to 'N/A'.
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        self.assertIn("member_slot = 2", lines)
        self.assertIn("member_system_id = N/A", lines)
        self.assertIn("member_state = DOWN", lines)

    def test_ssi_info_down_member_heartbeats_na(self):
        # DOWN member has no timestamps; both heartbeat fields must be 'N/A'.
        with self._patch_run(_SSI_CLUSTER_OUTPUT, rc=0):
            result = self.handler.ssi_info()
        lines = result["response"]
        # The DOWN entry follows "member_slot = 2"
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
        """mode may arrive as the string '1' — must still add READONLY."""
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
                ["DETACH", "1000", "FROM", "TESTUSER"])
        self.assertEqual(0, result["overallRC"])

    def test_query_detach_failure_rc_propagated(self):
        self.rh.parms = {'vaddr': '1000'}
        with self._patch_run("HCP040E Device not found\n", rc=1):
            result = self.handler.query_detach(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_relocate_minimal_command(self):
        """No optional parms → only VMRELOCATE MOVE <userid>."""
        self.rh.parms = {}
        with self._patch_run("Relocation started\n", rc=0) as mock_run:
            result = self.handler.query_relocate(self.rh)
            mock_run.assert_called_once_with(
                ["VMRELOCATE", "MOVE", "TESTUSER"], output=True)
        self.assertEqual(0, result["overallRC"])

    def test_query_relocate_with_destination(self):
        self.rh.parms = {'dest': 'SYS2'}
        with self._patch_run("Relocation started\n", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("TO", args)
        self.assertIn("SYS2", args)

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

    def test_query_relocate_immediate(self):
        self.rh.parms = {'immediate': True}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("IMMEDIATE", args)

    def test_query_relocate_max_total_seconds(self):
        self.rh.parms = {'maxTotal': 120}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXTotal", args)
        self.assertIn("120", args)
        self.assertIn("SEC", args)

    def test_query_relocate_max_total_nolimit(self):
        self.rh.parms = {'maxTotal': -1}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXTotal", args)
        self.assertIn("NOLIMIT", args)

    def test_query_relocate_max_quiesce_seconds(self):
        self.rh.parms = {'maxQuiesce': 10}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXQuiesce", args)
        self.assertIn("10", args)
        self.assertIn("SEC", args)

    def test_query_relocate_max_quiesce_nolimit(self):
        self.rh.parms = {'maxQuiesce': -1}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.query_relocate(self.rh)
            args = mock_run.call_args[0][0]
        self.assertIn("MAXQuiesce", args)
        self.assertIn("NOLIMIT", args)

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
                      "MAXQuiesce", "10"):
            self.assertIn(token, args)

    def test_query_relocate_failure_rc_propagated(self):
        self.rh.parms = {'dest': 'SYS2'}
        with self._patch_run("HCP2627E Relocation failed\n", rc=1):
            result = self.handler.query_relocate(self.rh)
        self.assertEqual(1, result["overallRC"])

    def test_query_vswitch_details_single_vswitch_nic_stats(self):
        # Real vmcp QUERY VSWITCH DETAILS output (one vswitch, one NIC).
        # Every NIC counter field is verified against the raw CP output.
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
        # Two vswitches: first has two NICs, second has one NIC.
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
        """A NIC section with no RX/TX lines must leave all counters at '0'."""
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
                             msg=f"{key} should default to '0'")
