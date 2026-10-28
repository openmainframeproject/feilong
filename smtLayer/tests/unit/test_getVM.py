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
