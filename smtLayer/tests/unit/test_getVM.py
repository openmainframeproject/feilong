#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2021 IBM Corp.
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

from smtLayer import getVM
from smtLayer.tests.unit import base


class SMTGetVMTestCase(base.SMTTestCase):
    """Test cases for getHost.py in smtLayer."""
    def test_extract_fcp_data(self):
        rh = mock.Mock()
        # the last record 1B10 is not complete
        # should stop there
        # and skip the empty line and the line contains #
        fake_response = ['FCP device number: 1B0E',
                         'Status: Free',
                         'NPIV world wide port number: C05076DE330005EA',
                         'Channel path ID: 27',
                         'Physical world wide port number: C05076DE33002E41',
                         'Owner: NONE',
                         'FCP device number: 1B0F',
                         'Status: Free',
                         'NPIV world wide port number: C05076DE330005EB',
                         'Channel path ID: 27',
                         'Physical world wide port number:',
                         'Owner: turns',
                         '#',
                         '',
                         'FCP device number: 1B10']
        raw_data = '\n'.join(fake_response)
        ret = getVM.extract_fcp_data(rh, raw_data, 'free')
        self.assertEqual(ret, '\n'.join(fake_response[0:12]))

    def _fcpinfo(self, use_smapi, results):
        from smtLayer import ReqHandle
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        rh.userid = 'FAKEUSER'
        rh.parms['status'] = 'all'
        with mock.patch.object(getVM, 'config') as mock_conf, \
                mock.patch.object(getVM, 'VMCPHandler') as mock_vmcp_cls, \
                mock.patch.object(getVM, 'invokeSMCLI') as mock_smcli, \
                mock.patch.object(ReqHandle.ReqHandle, 'printLn') as pl:
            mock_conf.CONF.zvm.use_smapi = use_smapi
            mock_vmcp_cls.return_value.query_fcp_formatted.return_value = \
                results
            mock_smcli.return_value = results
            rc = getVM.fcpinfo(rh)
        return rc, mock_vmcp_cls, mock_smcli, pl

    def test_fcpinfo_vmcp_path(self):
        results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
                   'strError': '',
                   'response': '\n'.join([
                       'FCP device number: E89D', '  Status: Offline',
                       '  NPIV world wide port number: C05076FFE78011B4',
                       '  Channel path ID: 12',
                       '  Physical world wide port number: C05076FFE78026A1',
                       '  Owner: NONE'])}
        rc, vmcp, smcli, pl = self._fcpinfo(False, results)
        self.assertEqual(0, rc)
        vmcp.assert_called_once()
        smcli.assert_not_called()
        self.assertIn('Status: Offline', pl.call_args[0][1])

    def test_fcpinfo_vmcp_path_no_fcp_devices(self):
        results = {'overallRC': 1, 'rc': 4, 'rs': 28, 'errno': 0,
                   'strError': '', 'response': ''}
        rc, vmcp, smcli, pl = self._fcpinfo(False, results)
        # rc 4 / rs 28 means no FCP devices: reported as success
        self.assertEqual(0, rc)
        smcli.assert_not_called()

    def test_fcpinfo_smapi_path(self):
        results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
                   'strError': '', 'response': ''}
        rc, vmcp, smcli, pl = self._fcpinfo(True, results)
        self.assertEqual(0, rc)
        vmcp.assert_not_called()
        smcli.assert_called_once()
        self.assertEqual('System_WWPN_Query', smcli.call_args[0][1])
        self.assertEqual(['-T', 'FAKEUSER', '-k OWNER=YES'],
                         smcli.call_args[0][2])

    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_success(self, mock_exec):
        rh = mock.Mock()
        rh.userid = 'TESTUSER'
        rh.parms = {'pcif': '00000110'}
        rh.results = {'overallRC': 0}

        mock_exec.return_value = {'overallRC': 0, 'response': 'enc110\n'}

        rc = getVM.getNethIntInfo(rh)
        self.assertEqual(0, rc)
        rh.updateResults.assert_called_with({
            'overallRC': 0, 'rc': 0, 'rs': 0, 'response': 'enc110'
        })
        expected_cmd = (
            'for dev in /sys/bus/pci/devices/*; do '
            'f="$dev/function_id"; '
            '[ -f "$f" ] || continue; '
            'v=$(cat "$f" 2>/dev/null) || continue; '
            '[ "$(( v ))" -eq 272 ] 2>/dev/null || continue; '
            'ls "$dev/net" 2>/dev/null; break; done; true'
        )
        mock_exec.assert_called_once_with(rh, 'TESTUSER', expected_cmd)

    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_invalid_pcif(self, mock_exec):
        rh = mock.Mock()
        rh.userid = 'TESTUSER'
        rh.parms = {'pcif': 'invalid_pcif'}
        rh.results = {'overallRC': 4}

        rc = getVM.getNethIntInfo(rh)
        self.assertEqual(4, rc)
        rh.updateResults.assert_called_with({'overallRC': 4, 'rc': 4, 'rs': 99})
        mock_exec.assert_not_called()

    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_unsafe_pcif(self, mock_exec):
        for bad in ('-1', '0x110', '110; reboot', ' 110', '123456789', ''):
            rh = mock.Mock()
            rh.userid = 'TESTUSER'
            rh.parms = {'pcif': bad}
            rh.results = {'overallRC': 4}

            rc = getVM.getNethIntInfo(rh)
            self.assertEqual(4, rc, bad)
        mock_exec.assert_not_called()

    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_pcif_not_found(self, mock_exec):
        rh = mock.Mock()
        rh.userid = 'TESTUSER'
        rh.parms = {'pcif': '00000110'}
        rh.results = {'overallRC': 4}

        mock_exec.return_value = {'overallRC': 0, 'response': ''}

        rc = getVM.getNethIntInfo(rh)
        self.assertEqual(4, rc)
        rh.updateResults.assert_called_with({'overallRC': 4, 'rc': 4, 'rs': 99})

    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_exec_failed(self, mock_exec):
        rh = mock.Mock()
        rh.userid = 'TESTUSER'
        rh.parms = {'pcif': '00000110'}
        mock_exec.return_value = {'overallRC': 1, 'response': 'IUCV error'}

        rc = getVM.getNethIntInfo(rh)
        self.assertEqual(1, rc)
        rh.updateResults.assert_called_with({'overallRC': 1, 'response': 'IUCV error'})

    # ------------------------------------------------------------------
    # parseCmdline — positional operand wiring
    # ------------------------------------------------------------------
    def test_parseCmdline_nethinterfaceinfo_populates_pcif(self):
        """parseCmdline stores the 4th token in parms['pcif'] for NETHINTERFACEINFO."""
        rh = mock.Mock()
        rh.totalParms = 4
        rh.request = ['getvm', 'TESTVM', 'NETHINTERFACEINFO', '00000110']
        rh.results = {'overallRC': 0}
        rh.subfunction = 'NETHINTERFACEINFO'
        rh.argPos = 3
        rh.parms = {}

        getVM.parseCmdline(rh)

        self.assertEqual(rh.parms['pcif'], '00000110')

    def test_parseCmdline_fcpinfo_populates_status(self):
        """parseCmdline stores the 4th token in parms['status'] for FCPINFO."""
        rh = mock.Mock()
        rh.totalParms = 4
        rh.request = ['getvm', 'TESTVM', 'FCPINFO', 'free']
        rh.results = {'overallRC': 0}
        rh.subfunction = 'FCPINFO'
        rh.argPos = 3
        rh.parms = {}

        getVM.parseCmdline(rh)

        self.assertEqual(rh.parms['status'], 'free')

    # ------------------------------------------------------------------
    # getNethIntInfo — sysfs directory empty (no interface file)
    # ------------------------------------------------------------------
    @mock.patch('smtLayer.getVM.execCmdThruIUCV')
    def test_get_neth_int_info_sysfs_empty(self, mock_exec):
        """ls /sys/.../net succeeds but returns only whitespace → rc 4."""
        rh = mock.Mock()
        rh.userid = 'TESTUSER'
        rh.parms = {'pcif': '00000110'}
        rh.results = {'overallRC': 0}

        # updateResults must actually update rh.results so the return path
        # sees the correct overallRC.
        def _update_results(d):
            rh.results.update(d)
        rh.updateResults.side_effect = _update_results

        mock_exec.return_value = {'overallRC': 0, 'response': '   \n'}

        rc = getVM.getNethIntInfo(rh)
        self.assertEqual(4, rc)
        rh.updateResults.assert_called_with({'overallRC': 4, 'rc': 4, 'rs': 99})
