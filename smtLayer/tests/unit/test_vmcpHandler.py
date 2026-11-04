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

import re
import subprocess
from unittest import mock

from smtLayer import msgs
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import (
    ALREADY_LOGGED_ON_PATTERN,
    NOT_ATTACHED_PATTERN,
    NOT_LOGGED_ON_PATTERN,
    VMCPHandler)
from zvmsdk import exception


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
    def test_run_output_true_survives_invalid_utf8(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b"HCP045E \xff not logged on")
        result = self.handler._run(["query", "userid"], output=True)
        self.assertEqual(1, result["overallRC"])
        self.assertIn("HCP045E", result["output"])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_updates_results(self, mock_check):
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"err")
        self.handler._run(["query", "pcif"])
        self.rh.updateResults.assert_called_once_with(msgs.msg['0405'][0])

    @mock.patch('subprocess.check_output')
    def test_run_called_process_error_message_is_decoded(self, mock_check):
        # Invalid UTF-8 byte must not break decoding.
        mock_check.side_effect = subprocess.CalledProcessError(
            returncode=4, cmd="vmcp", output=b"HCP err \xff")
        self.handler._run(["query", "pcif"])
        printed = self.rh.printLn.call_args[0][1]
        self.assertIn("HCP err", printed)
        self.assertNotIn("b'", printed)

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

    def test_run_failure_raises(self):
        # _run() records the failure in rh.results; query_pcif raises.
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
        self.rh.updateResults.assert_called_once_with(msgs.msg['0405'][0])

    def test_pci_function_not_found_with_rc_nonzero_is_run_failure(self):
        # A failing vmcp raises as a run failure; the "not found" handling
        # (which records msg 0405 itself) is not applied.
        with self._patch_run("A PCI function was not found.\n", rc=8):
            with self.assertRaises(exception.SDKSMTRequestFailed):
                self.handler.query_pcif()
        self.rh.updateResults.assert_not_called()

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
            self.rh.updateResults.assert_called_once_with(
                {'overallRC': 0, 'rc': 0, 'rs': 0})
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

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_tolerates_not_logged_on(self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        with self._patch_run("", rc=0) as mock_run:
            self.handler.deactivate("TESTUSER")
            mock_run.assert_called_once_with(
                ["force", "TESTUSER", "logoff"],
                tolerated=NOT_LOGGED_ON_PATTERN)

    def test_not_logged_on_pattern_matches_expected_messages(self):
        # HCP045E / HCP361E mean the guest is already logged off.
        for msg in ("HCPCMD045E TESTUSER not logged on",
                    "HCPUSR361E TESTUSER not logged on",
                    "HCPFRC045E TESTUSER not logged on"):
            self.assertTrue(re.search(NOT_LOGGED_ON_PATTERN, msg), msg)
        self.assertIsNone(re.search(NOT_LOGGED_ON_PATTERN,
                                    "HCPCMD054E TESTUSER already logged on"))

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    def test_deactivate_failure_already_recorded_not_overwritten(
            self, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        self.rh.results['overallRC'] = 99
        with self._patch_run("", rc=1):
            result = self.handler.deactivate("TESTUSER")
            self.assertEqual(1, result['overallRC'])
            self.rh.updateResults.assert_not_called()


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
                'PROCESSOR 0001 ALTERNATE IFL  CORE 0000\n'
                'PROCESSOR 0002 PARKED IFL  CORE 0001\n'
                'PROCESSOR 0003 STANDBY IFL  CORE 0001\n'
                'PARTITION MODE LINUX-ONLY\n'
            )
        }
        total, used = self.handler.get_cpu_count()
        self.assertEqual(4, total)
        self.assertEqual(3, used)
        mock_run.assert_called_once_with(['QUERY', 'PROCESSORS', 'EXPANDED'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_vmcp_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        total, used = self.handler.get_cpu_count()
        self.assertEqual(0, total)
        self.assertEqual(0, used)

    @mock.patch.object(VMCPHandler, '_run')
    def test_get_cpu_count_no_processors(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': 'PARTITION MODE: Z/VM\n'
        }
        total, used = self.handler.get_cpu_count()
        self.assertEqual(0, total)
        self.assertEqual(0, used)


class VMCPHandlerPurgeReaderTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.purge_reader()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_purge_reader_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': ''}
        result = self.handler.purge_reader()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['PURGE', 'TESTUSER', 'RDR', 'ALL'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_purge_reader_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.purge_reader()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerCreateNICTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.create_nic_for_guest()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_success(self, mock_run_for, mock_run):
        mock_run_for.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': 'NIC 0600 DEFINED'
        }
        mock_run.return_value = {'overallRC': 0, 'response': 'NIC 0600 TYPE QDIO'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(0, result['overallRC'])
        mock_run_for.assert_called_once_with(
            'TESTUSER', 'DEFINE NIC 0600 TYPE QDIO')
        mock_run.assert_called_once_with(
            ['QUERY', 'NIC', 'USERID', 'TESTUSER', '0600'])

    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_define_fails(self, mock_run_for):
        mock_run_for.return_value = {
            'overallRC': 1, 'rc': 1, 'rs': 0, 'errno': 0,
            'strError': 'HCP045E', 'response': 'HCP045E'
        }
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(1, result['overallRC'])

    @mock.patch.object(VMCPHandler, '_run')
    @mock.patch.object(VMCPHandler, '_run_for')
    def test_create_nic_verify_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': ''
        }
        mock_run.return_value = {'overallRC': 1, 'response': 'NIC not found'}
        result = self.handler.create_nic_for_guest('TESTUSER', '0600')
        self.assertEqual(2, result['overallRC'])
        self.assertTrue(result.get('nic_not_created'))


class VMCPHandlerQueryOSATestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_osa()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_attached_and_free(self, mock_run):
        mock_run.side_effect = [
            {
                'overallRC': 0,
                'response': (
                    'OSA  3000 ATTACHED TO SYSTEM   3000 DEVTYPE OSH         CHPID 70 OSH TRACESIZE 0008\n'
                    'OSA  3001 ATTACHED TO SYSTEM   3001 DEVTYPE OSH         CHPID 70 OSH TRACESIZE 0008\n'
                )
            },
            {
                'overallRC': 0,
                'response': 'OSA   3002 FREE    , OSA   3003 FREE    , OSA   3004 FREE\n'
            }
        ]
        result = self.handler.query_osa()
        self.assertIn('OSA', result)
        self.assertEqual(2, len(result['OSA']['ATTACHED']))
        self.assertIn(('SYSTEM', '3000'), result['OSA']['ATTACHED'])
        self.assertIn(('SYSTEM', '3001'), result['OSA']['ATTACHED'])
        self.assertIn('3002', result['OSA']['FREE'])
        self.assertIn('3003', result['OSA']['FREE'])
        self.assertIn('3004', result['OSA']['FREE'])
        mock_run.assert_any_call(['QUERY', 'OSA'])
        mock_run.assert_any_call(['QUERY', 'OSA', 'FREE'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_query_osa_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        result = self.handler.query_osa()
        self.assertEqual({}, result)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_no_osa(self, mock_run):
        mock_run.side_effect = [
            {'overallRC': 0, 'response': ''},
            {'overallRC': 0, 'response': ''}
        ]
        result = self.handler.query_osa()
        self.assertEqual({}, result)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_osa_free_fails_gracefully(self, mock_run):
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


class VMCPHandlerQueryAttachTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.attach_device()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {'vaddr': '1A00', 'raddr': '2B00', 'mode': '0'}
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_read_write(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 2B00 attached to TESTUSER as 1A00'}
        result = self.handler.attach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(['ATTACH', '2B00', 'TO', 'TESTUSER', 'AS', '1A00'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_read_only(self, mock_run):
        self.rh.parms['mode'] = '1'
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 2B00 attached to TESTUSER as 1A00'}
        result = self.handler.attach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(['ATTACH', '2B00', 'TO', 'TESTUSER', 'AS', '1A00', 'READONLY'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_attach_device_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP022E Device 2B00 does not exist'}
        result = self.handler.attach_device()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryDetachTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.detach_device()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {'vaddr': '1A00'}
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Device 1A00 detached'}
        result = self.handler.detach_device()
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['FOR', 'TESTUSER', 'CMD', 'DETACH', '1A00'],
            tolerated=NOT_ATTACHED_PATTERN
        )

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_tolerated_already_detached(self, mock_run):
        # Tolerated failure returns overallRC=0
        mock_run.return_value = {'overallRC': 0, 'response': 'HCP040E Device 1A00 does not exist'}
        result = self.handler.detach_device()
        self.assertEqual(0, result['overallRC'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_detach_device_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP003E Invalid option'}
        result = self.handler.detach_device()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryImagePerformanceTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_image_performance()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_single_section(self, mock_run):
        output = (
            "Configured=1000000 Offline=0 Standby=0\n"
            "GlobalClearedAvail=100000 GlobalUnclearedAvail=200000\n"
            "LocalClearedAvail=50000 LocalUnclearedAvail=50000\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.query_image_performance()
        self.assertEqual(0, result['overallRC'])
        # memory_in_use = 1000000 - (100000 + 200000 + 50000 + 50000) = 600000
        self.assertEqual("MEMORY_IN_USE=600000", result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_multi_section(self, mock_run):
        # Realistic multi-section QUERY FRAMES output (<2G and >2G)
        output = (
            "Storage below 2G:\n"
            "Configured=524288 Offline=0 Standby=0\n"
            "GlobalClearedAvail=50000 GlobalUnclearedAvail=100000\n"
            "LocalClearedAvail=25000 LocalUnclearedAvail=25000\n"
            "Storage above 2G:\n"
            "Configured=1572864 Offline=0 Standby=0\n"
            "GlobalClearedAvail=150000 GlobalUnclearedAvail=300000\n"
            "LocalClearedAvail=75000 LocalUnclearedAvail=75000\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.query_image_performance()
        self.assertEqual(0, result['overallRC'])
        # Total configured = 524288 + 1572864 = 2097152
        # Total free = (50000 + 150000) + (100000 + 300000) + (25000 + 75000) + (25000 + 75000) = 800000
        # memory_in_use = 2097152 - 800000 = 1297152
        self.assertEqual("MEMORY_IN_USE=1297152", result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_image_performance_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.query_image_performance()
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('HCP error', result['response'])


class VMCPHandlerSSIInfoTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.ssi_info()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_not_in_cluster(self, mock_run):
        mock_run.return_value = {
            'overallRC': 0,
            'response': 'This system is not a member of an SSI cluster.\n'
        }
        result = self.handler.ssi_info()
        self.assertEqual(0, result['rc'])
        self.assertEqual([], result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_joined_cluster(self, mock_run):
        output = (
            "SSI Name: ICIC2SSI\n"
            "SSI Mode: Stable\n"
            "Cross-System Timeouts: Enabled\n"
            "SSI Persistent Data Record (PDR) device: IAS7CM on 139E\n"
            "Slot  System    State      PDR Heartbeat        Received Heartbeat\n"
            " 1    BOEIAAS7  Joined     12/28/21 05:10:21    12/28/21 05:10:21\n"
            " 2    BOEIAAS8  Joined     12/28/21 05:10:36    12/28/21 05:10:36\n"
            " 3    --------  Down\n"
            " 4    --------  Down\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.ssi_info()
        self.assertEqual(0, result['rc'])
        expected = [
            'ssi_name = ICIC2SSI',
            'ssi_mode = Stable',
            'ssi_pdr = IAS7CM_on_139E',
            'cross_system_timeouts = Enabled',
            'output.ssiInfoCount = 4',
            '',
            'member_slot = 1',
            'member_system_id = BOEIAAS7',
            'member_state = Joined',
            'member_pdr_heartbeat = 12/28/21_05:10:21',
            'member_received_heartbeat = 12/28/21_05:10:21',
            '',
            'member_slot = 2',
            'member_system_id = BOEIAAS8',
            'member_state = Joined',
            'member_pdr_heartbeat = 12/28/21_05:10:36',
            'member_received_heartbeat = 12/28/21_05:10:36',
            '',
            'member_slot = 3',
            'member_system_id = N/A',
            'member_state = Down',
            'member_pdr_heartbeat = N/A',
            'member_received_heartbeat = N/A',
            '',
            'member_slot = 4',
            'member_system_id = N/A',
            'member_state = Down',
            'member_pdr_heartbeat = N/A',
            'member_received_heartbeat = N/A',
            ''
        ]
        self.assertEqual(expected, result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_ssi_info_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP error'}
        result = self.handler.ssi_info()
        self.assertEqual(1, result['rc'])


class VMCPHandlerQueryRelocateTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.relocate_vm()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.rh.parms = {
            'dest': 'TARGETSYS',
            'forcearch': True,
            'forcedomain': True,
            'forcestorage': True,
            'immediate': True,
            'maxTotal': 100,
            'maxQuiesce': 10
        }
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_success(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': 'Relocation complete', 'output': ''}
        result = self.handler.relocate_vm()
        self.assertEqual(0, result['overallRC'])
        expected_args = [
            'VMRELOCATE', 'MOVE', 'TESTUSER',
            'TO', 'TARGETSYS',
            'FORCE', 'ARCHITECTURE', 'DOMAIN', 'STORAGE',
            'IMMEDIATE',
            'MAXTotal', '100', 'SEC',
            'MAXQuiesce', '10', 'SEC'
        ]
        mock_run.assert_called_once_with(expected_args, output=True)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_nolimit(self, mock_run):
        self.rh.parms = {
            'dest': 'TARGETSYS',
            'maxTotal': -1,
            'maxQuiesce': -1
        }
        mock_run.return_value = {'overallRC': 0, 'response': 'Relocation complete', 'output': ''}
        result = self.handler.relocate_vm()
        self.assertEqual(0, result['overallRC'])
        expected_args = [
            'VMRELOCATE', 'MOVE', 'TESTUSER',
            'TO', 'TARGETSYS',
            'MAXTotal', 'NOLIMIT',
            'MAXQuiesce', 'NOLIMIT'
        ]
        mock_run.assert_called_once_with(expected_args, output=True)

    @mock.patch.object(VMCPHandler, '_run')
    def test_relocate_vm_fails(self, mock_run):
        mock_run.return_value = {
            'overallRC': 1,
            'response': 'HCP045E TESTUSER not logged on',
            'output': 'HCP045E TESTUSER not logged on'
        }
        result = self.handler.relocate_vm()
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerActivateTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.activate()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_already_logged_on(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])
        self.assertEqual("", result['response'])
        mock_run.assert_not_called()

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_logged_off_xautolog_success(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 0, 'response': 'Command accepted'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])
        mock_run.assert_called_once_with(
            ['xautolog', 'TESTUSER'],
            tolerated=ALREADY_LOGGED_ON_PATTERN
        )

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_tolerated_already_logged_on(self, mock_run, mock_is_logged_on):
        # When XAUTOLOG returns HCP054E, tolerated failure returns overallRC=0
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 0, 'response': 'HCP054E Already logged on'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(0, result['overallRC'])

    @mock.patch('smtLayer.vmUtils.isLoggedOn')
    @mock.patch.object(VMCPHandler, '_run')
    def test_activate_fails(self, mock_run, mock_is_logged_on):
        mock_is_logged_on.return_value = {'overallRC': 0, 'rc': 0, 'rs': 1}
        mock_run.return_value = {'overallRC': 1, 'response': 'HCP022E User does not exist'}
        result = self.handler.activate("TESTUSER")
        self.assertEqual(1, result['overallRC'])


class VMCPHandlerQueryVSwitchDetailsTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_vswitch_details()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = VMCPHandler(self.rh)

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_success(self, mock_run):
        output = (
            "VSWITCH SYSTEM VSICIC Type: QDIO Connected: 1 Maxconn: INFINITE\n"
            "  PERSISTENT RESTRICTED NONROUTER MACPROTECT UNSPECIFIED\n"
            "Adapter Connections:\n"
            "  Adapter Owner: USER01 NIC: 0600 Name: UNASSIGNED\n"
            "    RX Packets: 100 Discarded: 2 Errors: 0\n"
            "    TX Packets: 200 Discarded: 4 Errors: 1\n"
            "    RX Bytes: 1024 TX Bytes: 2048\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        response = result['response']
        self.assertEqual(1, response['vswitch_count'])
        self.assertEqual(1, len(response['vswitches']))
        vsw = response['vswitches'][0]
        self.assertEqual('VSICIC', vsw['vswitch_name'])
        self.assertEqual(1, len(vsw['nics']))
        nic = vsw['nics'][0]
        self.assertEqual('USER01', nic['userid'])
        self.assertEqual('0600', nic['vdev'])
        self.assertEqual('100', nic['nic_fr_rx'])
        self.assertEqual('2', nic['nic_fr_rx_dsc'])
        self.assertEqual('0', nic['nic_fr_rx_err'])
        self.assertEqual('200', nic['nic_fr_tx'])
        self.assertEqual('4', nic['nic_fr_tx_dsc'])
        self.assertEqual('1', nic['nic_fr_tx_err'])
        self.assertEqual('1024', nic['nic_rx'])
        self.assertEqual('2048', nic['nic_tx'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_multiple_vswitches(self, mock_run):
        output = (
            "VSWITCH SYSTEM VSW1 Type: QDIO Connected: 1\n"
            "Adapter Connections:\n"
            "  Adapter Owner: USER01 NIC: 0600\n"
            "    RX Packets: 10 Discarded: 0 Errors: 0\n"
            "    TX Packets: 20 Discarded: 0 Errors: 0\n"
            "    RX Bytes: 100 TX Bytes: 200\n"
            "VSWITCH SYSTEM VSW2 Type: QDIO Connected: 1\n"
            "Adapter Connections:\n"
            "  Adapter Owner: USER02 NIC: 0700\n"
            "    RX Packets: 30 Discarded: 1 Errors: 0\n"
            "    TX Packets: 40 Discarded: 2 Errors: 0\n"
            "    RX Bytes: 300 TX Bytes: 400\n"
        )
        mock_run.return_value = {'overallRC': 0, 'response': output}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        response = result['response']
        self.assertEqual(2, response['vswitch_count'])
        self.assertEqual('VSW1', response['vswitches'][0]['vswitch_name'])
        self.assertEqual('VSW2', response['vswitches'][1]['vswitch_name'])

    @mock.patch('subprocess.check_output', return_value=b"")
    def test_query_vswitch_details_command_has_buffer_option(
            self, mock_check):
        self.handler.query_vswitch_details()
        mock_check.assert_called_once_with(
            ["sudo", "/sbin/vmcp", "--buffer=1M",
             "QUERY", "VSWITCH", "DETAILS"],
            close_fds=True,
            stderr=subprocess.STDOUT,
        )

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_no_vswitches(self, mock_run):
        mock_run.return_value = {'overallRC': 0, 'response': ''}
        result = self.handler.query_vswitch_details()
        self.assertEqual(0, result['rc'])
        self.assertEqual({'vswitch_count': 0, 'vswitches': []},
                         result['response'])

    @mock.patch.object(VMCPHandler, '_run')
    def test_query_vswitch_details_fails(self, mock_run):
        mock_run.return_value = {'overallRC': 1, 'response': ''}
        result = self.handler.query_vswitch_details()
        self.assertEqual(1, result['rc'])
        self.assertEqual(0, result['response']['vswitch_count'])
        self.assertEqual([], result['response']['vswitches'])
