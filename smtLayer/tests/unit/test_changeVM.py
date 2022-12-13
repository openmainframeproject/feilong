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
