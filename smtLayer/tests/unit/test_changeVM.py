#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2022 IBM Corp.
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

from mock import Mock, call, patch
from smtLayer import changeVM, ReqHandle
from smtLayer.tests.unit import base
from smtLayer.vmcpHandler import VMCPHandler
from zvmsdk import config


class SMTChangeVMTestCase(base.SMTTestCase):
    """Test cases for changeVM.py in smtLayer."""

    @staticmethod
    def mock_reset(*args):
        """Reset mock objects in args"""
        for m in args:
            if isinstance(m, Mock):
                m.reset_mock()

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    def test_undedicate(self, mock_logon, mock_smcli, mock_print):
        """Test undedicate()"""
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=Mock())
        rh.parms['vaddr'] = 'fake_vaddr'
        parms = [
            "-T", rh.userid,
            "-v", rh.parms['vaddr']]

        # case1:
        # Image_Device_Undedicate_DM:
        #   overallRC != 0 and not (rc == 404 and rs == 8)
        mock_smcli.return_value = {
            'overallRC': 8,
            'rc': 400,
            'rs': 9,
            'errno': 0,
            'strError': '',
            'response': ['fake_resp'],
            'logEntries': []
        }
        results = changeVM.undedicate(rh)
        # verify
        mock_smcli.assert_called_once_with(
            rh, "Image_Device_Undedicate_DM", parms, hideInLog=[])
        mock_print.assert_called_once_with(
            "ES", ['fake_resp'])
        mock_logon.assert_not_called()
        self.assertEqual(results, 8)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

        # case2: VM not logged on
        # Image_Device_Undedicate_DM:
        #   overallRC != 0 and (rc == 404 and rs == 8)
        mock_smcli.return_value = {
            'overallRC': 8,
            'rc': 404,
            'rs': 8,
            'errno': 0,
            'strError': '',
            'response': ['fake_resp'],
            'logEntries': []
        }
        mock_logon.return_value = {
            'overallRC': 0,
            'rc': 0,
            'rs': 1
        }
        results = changeVM.undedicate(rh)
        # verify
        mock_smcli.assert_called_once_with(
            rh, "Image_Device_Undedicate_DM", parms, hideInLog=[])
        mock_logon.assert_called_once_with(rh, rh.userid)
        mock_print.assert_called_once_with(
            "ES", ['fake_resp'])
        self.assertEqual(results, 8)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

        # case3: VM logged on
        # Image_Device_Undedicate_DM:
        #   overallRC != 0 and (rc == 404 and rs == 8)
        # Image_Device_Undedicate:
        #   overallRC != 0
        mock_smcli.side_effect = [
            {'overallRC': 8,
             'rc': 404,
             'rs': 8,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp'],
             'logEntries': []},
            {'overallRC': 8,
             'rc': 204,
             'rs': 8,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp2'],
             'logEntries': []}]
        mock_logon.return_value = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0
        }
        results = changeVM.undedicate(rh)
        # verify
        expected_calls = [call(rh, "Image_Device_Undedicate_DM", parms, hideInLog=[]),
                          call(rh, "Image_Device_Undedicate", parms)]
        self.assertEqual(mock_smcli.mock_calls, expected_calls)
        mock_logon.assert_called_once_with(rh, rh.userid)
        mock_print.assert_called_once_with(
            "ES", ['fake_resp2'])
        self.assertEqual(results, 8)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

        # case4: VM logged on
        # Image_Device_Undedicate_DM:
        #   overallRC != 0 and (rc == 404 and rs == 8)
        # Image_Device_Undedicate:
        #   overallRC == 0
        mock_smcli.side_effect = [
            {'overallRC': 8,
             'rc': 404,
             'rs': 8,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp'],
             'logEntries': []},
            {'overallRC': 0,
             'rc': 0,
             'rs': 0,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp2'],
             'logEntries': []}]
        mock_logon.return_value = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0
        }
        results = changeVM.undedicate(rh)
        # verify
        expected_calls = [call(rh, "Image_Device_Undedicate_DM", parms, hideInLog=[]),
                          call(rh, "Image_Device_Undedicate", parms)]
        self.assertEqual(mock_smcli.mock_calls, expected_calls)
        mock_logon.assert_called_once_with(rh, rh.userid)
        mock_print.assert_called_once_with(
            "N", "UnDedicated device fake_vaddr from the active configuration.")
        self.assertEqual(results, 0)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

        # case5: VM logged on
        # Image_Device_Undedicate_DM:
        #   overallRC == 0
        # Image_Device_Undedicate:
        #   overallRC == 0
        mock_smcli.side_effect = [
            {'overallRC': 0,
             'rc': 0,
             'rs': 0,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp'],
             'logEntries': []},
            {'overallRC': 0,
             'rc': 0,
             'rs': 0,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp2'],
             'logEntries': []}]
        mock_logon.return_value = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0
        }
        results = changeVM.undedicate(rh)
        # verify
        expected_calls = [call(rh, "Image_Device_Undedicate_DM", parms, hideInLog=[]),
                          call(rh, "Image_Device_Undedicate", parms)]
        self.assertEqual(mock_smcli.mock_calls, expected_calls)
        mock_logon.assert_called_once_with(rh, rh.userid)
        mock_print.assert_called_once_with(
            "N", "UnDedicated device fake_vaddr from the active configuration.")
        self.assertEqual(results, 0)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

        # case6: VM logged on
        # Image_Device_Undedicate_DM:
        #   overallRC == 0
        # Image_Device_Undedicate:
        #   overallRC != 0
        mock_smcli.side_effect = [
            {'overallRC': 0,
             'rc': 0,
             'rs': 0,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp'],
             'logEntries': []},
            {'overallRC': 8,
             'rc': 204,
             'rs': 8,
             'errno': 0,
             'strError': '',
             'response': ['fake_resp2'],
             'logEntries': []}]
        mock_logon.return_value = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0
        }
        results = changeVM.undedicate(rh)
        # verify
        expected_calls = [call(rh, "Image_Device_Undedicate_DM", parms, hideInLog=[]),
                          call(rh, "Image_Device_Undedicate", parms)]
        self.assertEqual(mock_smcli.mock_calls, expected_calls)
        mock_logon.assert_called_once_with(rh, rh.userid)
        mock_print.assert_called_once_with(
            "ES", ['fake_resp2'])
        self.assertEqual(results, 8)
        # cleanup
        self.mock_reset(mock_smcli, mock_logon, mock_print)
        rh.updateResults({}, reset=2)

    def _add_disk_rh(self):
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=Mock())
        rh.userid = 'FAKEUSER'
        rh.parms['vaddr'] = '0100'
        rh.parms['diskPool'] = 'POOL1'
        rh.parms['diskSize'] = '100'
        # the active configuration is only updated after installFS
        rh.parms['fileSystem'] = 'ext4'
        rh.parms['mode'] = 'MR'
        return rh

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(changeVM, 'VMCPHandler')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    @patch.object(changeVM, 'installFS')
    @patch.object(changeVM.generalUtils, 'cvtToCyl')
    @patch.object(changeVM, 'config')
    def _test_add_disk_active(self, func, disk_type, use_smapi,
                              mock_conf, mock_cvt, mock_fs, mock_logon,
                              mock_smcli, mock_vmcp_cls, mock_print):
        mock_conf.CONF.zvm.use_smapi = use_smapi
        mock_cvt.return_value = ({'overallRC': 0}, 100)
        mock_logon.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        mock_fs.return_value = {'overallRC': 0, 'rc': 0, 'rs': 0}
        ok = {'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
              'strError': '', 'response': []}
        mock_smcli.return_value = ok
        mock_vmcp_cls.return_value.add_disk.return_value = ok
        rh = self._add_disk_rh()

        self.assertEqual(0, func(rh))
        return rh, mock_smcli, mock_vmcp_cls

    def test_add3390_active_vmcp_path(self):
        rh, smcli, vmcp = self._test_add_disk_active(
            changeVM.add3390, '3390', False)
        vmcp.assert_called_once_with(rh)
        vmcp.return_value.add_disk.assert_called_once_with('0100', 'MR')
        # only the directory entry call uses SMAPI
        self.assertEqual(1, smcli.call_count)
        self.assertEqual('Image_Disk_Create_DM', smcli.call_args[0][1])

    def test_add3390_active_smapi_path(self):
        rh, smcli, vmcp = self._test_add_disk_active(
            changeVM.add3390, '3390', True)
        vmcp.assert_not_called()
        self.assertEqual(2, smcli.call_count)
        self.assertEqual('Image_Disk_Create', smcli.call_args[0][1])
        self.assertEqual(["-T", "FAKEUSER", "-v", "0100", "-m", "MR"],
                         smcli.call_args[0][2])

    def test_add9336_active_vmcp_path(self):
        rh, smcli, vmcp = self._test_add_disk_active(
            changeVM.add9336, '9336', False)
        vmcp.assert_called_once_with(rh)
        vmcp.return_value.add_disk.assert_called_once_with('0100', 'MR')
        self.assertEqual(1, smcli.call_count)

    def test_add9336_active_smapi_path(self):
        rh, smcli, vmcp = self._test_add_disk_active(
            changeVM.add9336, '9336', True)
        vmcp.assert_not_called()
        self.assertEqual(2, smcli.call_count)
        self.assertEqual(["-T", "FAKEUSER", "-v", "0100", "-m", "MR"],
                         smcli.call_args[0][2])


class ChangeVMVmcpTestCase(base.SMTTestCase):
    """Test cases for VMCP paths (use_smapi=False) in changeVM.py."""

    def setUp(self):
        super().setUp()
        self.rh = ReqHandle.ReqHandle(captureLogs=False, smt=Mock())
        self.rh.userid = "TESTUSER"
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        config.CONF.zvm['use_smapi'] = False

    def tearDown(self):
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(VMCPHandler, 'query_attach')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    def test_dedicate_vmcp_success(self, mock_logon, mock_smcli,
                                  mock_attach, mock_print):
        """Dedicate on active configuration via VMCP succeeds."""
        self.rh.parms = {'vaddr': '1000', 'raddr': '2000', 'mode': '0'}
        mock_smcli.return_value = {'overallRC': 0, 'response': ['ok']}
        mock_logon.return_value = {'overallRC': 0, 'rs': 0}
        mock_attach.return_value = {'overallRC': 0, 'response': 'Device attached'}

        rc = changeVM.dedicate(self.rh)

        mock_attach.assert_called_once_with(self.rh)
        mock_print.assert_called_once_with(
            "N", "Dedicated device 1000 to the active configuration.")
        self.assertEqual(0, rc)

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(VMCPHandler, 'query_attach')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    def test_dedicate_vmcp_failure(self, mock_logon, mock_smcli,
                                  mock_attach, mock_print):
        """Dedicate on active configuration via VMCP fails."""
        self.rh.parms = {'vaddr': '1000', 'raddr': '2000', 'mode': '0'}
        mock_smcli.return_value = {'overallRC': 0, 'response': ['ok']}
        mock_logon.return_value = {'overallRC': 0, 'rs': 0}
        mock_attach.return_value = {'overallRC': 1, 'response': 'HCP040E Device not found'}

        rc = changeVM.dedicate(self.rh)

        mock_attach.assert_called_once_with(self.rh)
        mock_print.assert_called_once_with("ES", "HCP040E Device not found")
        self.assertEqual(1, rc)

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(VMCPHandler, 'query_detach')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    def test_undedicate_vmcp_success(self, mock_logon, mock_smcli,
                                    mock_detach, mock_print):
        """Undedicate on active configuration via VMCP succeeds."""
        self.rh.parms = {'vaddr': '1000'}
        mock_smcli.return_value = {'overallRC': 0, 'response': ['ok']}
        mock_logon.return_value = {'overallRC': 0, 'rs': 0}
        mock_detach.return_value = {'overallRC': 0, 'response': 'Device detached'}

        rc = changeVM.undedicate(self.rh)

        mock_detach.assert_called_once_with(self.rh)
        mock_print.assert_called_once_with(
            "N", "UnDedicated device 1000 from the active configuration.")
        self.assertEqual(0, rc)

    @patch.object(ReqHandle.ReqHandle, 'printLn')
    @patch.object(VMCPHandler, 'query_detach')
    @patch.object(changeVM, 'invokeSMCLI')
    @patch.object(changeVM, 'isLoggedOn')
    def test_undedicate_vmcp_failure(self, mock_logon, mock_smcli,
                                    mock_detach, mock_print):
        """Undedicate on active configuration via VMCP fails."""
        self.rh.parms = {'vaddr': '1000'}
        mock_smcli.return_value = {'overallRC': 0, 'response': ['ok']}
        mock_logon.return_value = {'overallRC': 0, 'rs': 0}
        mock_detach.return_value = {'overallRC': 1, 'response': 'HCP040E Device not found'}

        rc = changeVM.undedicate(self.rh)

        mock_detach.assert_called_once_with(self.rh)
        mock_print.assert_called_once_with("ES", "HCP040E Device not found")
        self.assertEqual(1, rc)
