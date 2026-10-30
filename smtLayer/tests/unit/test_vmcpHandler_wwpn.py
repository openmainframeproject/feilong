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

from smtLayer import vmcpHandler
from smtLayer.tests.unit import base

# Real output of 'vmcp "query fcp wwpn"' captured on a z/VM host,
# trimmed to one device per case.
CP_ACTIVE_SYSTEM = (
    "FCP  E800      NPIV WWPN C05076FFE78002D0\n"
    "     CHPID 10  PERM WWPN C05076FFE7801641\n"
    "     ATTACHED TO SYSTEM\n")
CP_FREE = (
    "FCP  E801      NPIV WWPN C05076FFE78002D4\n"
    "     CHPID 10  PERM WWPN C05076FFE7801641\n"
    "     FREE\n")
CP_ACTIVE_GUEST = (
    "FCP  E80A      NPIV WWPN C05076FFE780100C\n"
    "     CHPID 10  PERM WWPN C05076FFE7801641\n"
    "     ATTACHED TO IIMD0057\n")
CP_NO_NPIV = (
    "FCP  E840      NPIV WWPN NONE\n"
    "     CHPID 11  PERM WWPN C05076FFE7802441\n"
    "     FREE\n")
CP_OFFLINE = (
    "FCP  E89D      NPIV WWPN C05076FFE78011B4\n"
    "     CHPID 12  PERM WWPN C05076FFE78026A1\n"
    "     OFFLINE\n")

# The matching output of 'smcli System_WWPN_Query -k OWNER=YES'
SMAPI_ACTIVE_SYSTEM = (
    "FCP device number: E800\n"
    "  Status: Active\n"
    "  NPIV world wide port number: C05076FFE78002D0\n"
    "  Channel path ID: 10\n"
    "  Physical world wide port number: C05076FFE7801641\n"
    "  Owner: SYSTEM")
SMAPI_FREE = (
    "FCP device number: E801\n"
    "  Status: Free\n"
    "  NPIV world wide port number: C05076FFE78002D4\n"
    "  Channel path ID: 10\n"
    "  Physical world wide port number: C05076FFE7801641\n"
    "  Owner: NONE")
SMAPI_ACTIVE_GUEST = (
    "FCP device number: E80A\n"
    "  Status: Active\n"
    "  NPIV world wide port number: C05076FFE780100C\n"
    "  Channel path ID: 10\n"
    "  Physical world wide port number: C05076FFE7801641\n"
    "  Owner: IIMD0057")
SMAPI_NO_NPIV = (
    "FCP device number: E840\n"
    "  Status: Free\n"
    "  NPIV world wide port number: NONE\n"
    "  Channel path ID: 11\n"
    "  Physical world wide port number: C05076FFE7802441\n"
    "  Owner: NONE")
SMAPI_OFFLINE = (
    "FCP device number: E89D\n"
    "  Status: Offline\n"
    "  NPIV world wide port number: C05076FFE78011B4\n"
    "  Channel path ID: 12\n"
    "  Physical world wide port number: C05076FFE78026A1\n"
    "  Owner: NONE")


def _make_rh():
    rh = mock.Mock()
    rh.userid = 'FAKEUSER'
    return rh


class VMCPHandlerRunTestCase(base.SMTTestCase):
    """Tests for VMCPHandler._run() and VMCPHandler._run_for()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = vmcpHandler.VMCPHandler(self.rh)

    @mock.patch('subprocess.check_output')
    def test_run_success(self, mock_co):
        mock_co.return_value = b'FCP  E800\n'
        result = self.handler._run(['QUERY', 'FCP', 'WWPN'])
        self.assertEqual(0, result['overallRC'])
        self.assertEqual('FCP  E800\n', result['response'])
        mock_co.assert_called_once_with(
            ['sudo', '/sbin/vmcp', 'QUERY', 'FCP', 'WWPN'],
            close_fds=True, stderr=subprocess.STDOUT)

    @mock.patch('subprocess.check_output')
    def test_run_calledprocesserror(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd='vmcp', output=b'HCP045E')
        result = self.handler._run(['QUERY', 'FCP', 'WWPN'])
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('', result['response'])
        self.rh.updateResults.assert_called_once()

    @mock.patch('subprocess.check_output')
    def test_run_generic_exception(self, mock_co):
        mock_co.side_effect = OSError('vmcp not found')
        result = self.handler._run(['QUERY', 'FCP', 'WWPN'])
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('', result['response'])
        self.rh.updateResults.assert_called_once()

    @mock.patch('subprocess.check_output')
    def test_run_for_success(self, mock_co):
        mock_co.return_value = b'ok\n'
        result = self.handler._run_for('FAKEUSER', 'LINK * 0100 0100 W')
        self.assertEqual(0, result['overallRC'])
        self.assertEqual(0, result['rc'])
        self.assertEqual('ok\n', result['response'])
        mock_co.assert_called_once_with(
            ['sudo', '/sbin/vmcp', 'FOR FAKEUSER CMD LINK * 0100 0100 W'],
            close_fds=True, stderr=subprocess.STDOUT)

    @mock.patch('subprocess.check_output')
    def test_run_for_calledprocesserror(self, mock_co):
        mock_co.side_effect = subprocess.CalledProcessError(
            returncode=2, cmd='vmcp', output=b'HCP045E')
        result = self.handler._run_for('FAKEUSER', 'LINK * 0100 0100 W')
        self.assertEqual(2, result['overallRC'])
        self.assertEqual(2, result['rc'])
        self.assertEqual('HCP045E', result['response'])
        self.assertEqual('HCP045E', result['strError'])

    @mock.patch('subprocess.check_output')
    def test_run_for_generic_exception(self, mock_co):
        mock_co.side_effect = OSError('vmcp not found')
        result = self.handler._run_for('FAKEUSER', 'LINK * 0100 0100 W')
        self.assertEqual(1, result['overallRC'])
        self.assertEqual('', result['response'])
        self.assertEqual('vmcp not found', result['strError'])


class VMCPHandlerQueryFcpFormattedTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.query_fcp_formatted()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = vmcpHandler.VMCPHandler(self.rh)

    def _query(self, cp_output):
        with mock.patch.object(
                self.handler, '_run',
                return_value={'response': cp_output, 'overallRC': 0}):
            return self.handler.query_fcp_formatted()

    def test_active_attached_to_system(self):
        result = self._query(CP_ACTIVE_SYSTEM)
        self.assertEqual(0, result['overallRC'])
        self.assertEqual(SMAPI_ACTIVE_SYSTEM, result['response'])

    def test_active_attached_to_guest(self):
        result = self._query(CP_ACTIVE_GUEST)
        self.assertEqual(SMAPI_ACTIVE_GUEST, result['response'])

    def test_free(self):
        result = self._query(CP_FREE)
        self.assertEqual(SMAPI_FREE, result['response'])

    def test_offline(self):
        result = self._query(CP_OFFLINE)
        self.assertEqual(SMAPI_OFFLINE, result['response'])

    def test_unknown_state_is_not_free(self):
        # a state that is not known must never be reported as Free
        unknown = (
            "FCP  E89D      NPIV WWPN C05076FFE78011B4\n"
            "     CHPID 12  PERM WWPN C05076FFE78026A1\n"
            "     SOMETHING NEW\n")
        result = self._query(unknown)
        self.assertEqual(SMAPI_OFFLINE, result['response'])

    def test_no_npiv(self):
        result = self._query(CP_NO_NPIV)
        self.assertEqual(SMAPI_NO_NPIV, result['response'])

    def test_all_states_in_one_output(self):
        cp_output = (CP_ACTIVE_SYSTEM + CP_FREE + CP_ACTIVE_GUEST +
                     CP_NO_NPIV + CP_OFFLINE)
        expected = '\n'.join([SMAPI_ACTIVE_SYSTEM, SMAPI_FREE,
                              SMAPI_ACTIVE_GUEST, SMAPI_NO_NPIV,
                              SMAPI_OFFLINE])
        result = self._query(cp_output)
        self.assertEqual(expected, result['response'])

    def test_empty_output(self):
        result = self._query('')
        self.assertEqual(0, result['overallRC'])
        self.assertEqual('', result['response'])

    def test_vmcp_failure(self):
        with mock.patch.object(
                self.handler, '_run',
                return_value={'response': '', 'overallRC': 1}):
            result = self.handler.query_fcp_formatted()
        self.assertEqual(1, result['overallRC'])
        self.assertEqual(4, result['rc'])
        self.assertEqual(28, result['rs'])


class VMCPHandlerAddDiskTestCase(base.SMTTestCase):
    """Tests for VMCPHandler.add_disk()"""

    def setUp(self):
        super().setUp()
        self.rh = _make_rh()
        self.handler = vmcpHandler.VMCPHandler(self.rh)

    @mock.patch.object(vmcpHandler.VMCPHandler, '_run')
    @mock.patch.object(vmcpHandler.VMCPHandler, '_run_for')
    def test_add_disk_success(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'response': '', 'overallRC': 0}
        mock_run.return_value = {'response': 'MDISK 0100', 'overallRC': 0}
        result = self.handler.add_disk('0100', 'W')
        self.assertEqual(0, result['overallRC'])
        self.assertEqual('MDISK 0100', result['response'])
        mock_run_for.assert_called_once_with(
            'FAKEUSER', 'LINK * 0100 0100 W')
        mock_run.assert_called_once_with(
            ['QUERY', 'MDISK', 'USERID', 'FAKEUSER', '0100', 'DETAILS'])

    @mock.patch.object(vmcpHandler.VMCPHandler, '_run')
    @mock.patch.object(vmcpHandler.VMCPHandler, '_run_for')
    def test_add_disk_link_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'response': 'HCP045E', 'overallRC': 2}
        result = self.handler.add_disk('0100', 'W')
        self.assertEqual(2, result['overallRC'])
        mock_run.assert_not_called()

    @mock.patch.object(vmcpHandler.VMCPHandler, '_run')
    @mock.patch.object(vmcpHandler.VMCPHandler, '_run_for')
    def test_add_disk_verify_fails(self, mock_run_for, mock_run):
        mock_run_for.return_value = {'response': '', 'overallRC': 0}
        mock_run.return_value = {'response': 'not found', 'overallRC': 1}
        result = self.handler.add_disk('0100', 'W')
        self.assertEqual(2, result['overallRC'])
        self.assertTrue(result['disk_not_linked'])
