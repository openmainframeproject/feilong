#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0
#
#    Copyright 2023, 2023 IBM Corp.
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


import os
import importlib
from importlib.machinery import SourceFileLoader
from mock import call, Mock, patch
from scripts.tests.unit import base

TEST_MODULE = None


#################################################
#            Helper Methods                     #
#################################################

def import_from_file(module_name, file_path):
    """import an python file that doesn't have a .py extension"""
    loader = SourceFileLoader(module_name, file_path)
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#################################################
#            Test Cases                         #
#################################################

class ZvmSdkGetPchidTestCase(base.ScriptsTestCase):

    def setUp(self):
        """Provide any setup necessary for these set of test cases"""
        super(ZvmSdkGetPchidTestCase, self).setUp()
        self.maxDiff = None
        # import zvmsdk-getpchid
        global TEST_MODULE
        # (Pdb) pp TEST_MODULE
        # <module 'getpchid' from '/.../feilong/scripts/zvmsdk-getpchid'>
        TEST_MODULE = import_from_file(
            'getpchid', os.getcwd() + '/scripts/zvmsdk-getpchid')

    def tearDown(self):
        """Provide any tear-down necessary for these set of test cases"""
        super(ZvmSdkGetPchidTestCase, self).tearDown()

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments(self, mock_func):
        """test _parse_arguments"""
        TEST_MODULE._parse_arguments()
        mock_func.assert_called_once()

    @patch('logging.basicConfig')
    def test_setup_logging(self, mock_basicCfg):
        """test setup_logging """
        TEST_MODULE.setup_logging()
        mock_basicCfg.assert_called_once()

    @patch('zvmsdk.volumeop.FCPManager')
    @patch('zvmsdk.utils.get_zhypinfo', Mock())
    @patch('zvmsdk.utils.get_cpc_sn')
    @patch('zvmsdk.utils.get_cpc_name')
    @patch('zvmsdk.utils.get_lpar_name')
    @patch('zvmsdk.utils.get_zvm_name')
    def test_get_fcp_devices_per_pchid(self, mock_zvm_name, mock_lpar_name,
                                       mock_cpc_name, mock_cps_sn, mock_init_fcp_mgr):
        """test get_fcp_devices_per_pchid"""
        # mock fcp_mgr
        mock_fcg_mgr = Mock()
        mock_init_fcp_mgr.return_value = mock_fcg_mgr
        # mock commons
        mock_cps_sn.return_value = 'fake_cpc_sn'
        mock_cpc_name.return_value = 'fake_cpc_name'
        mock_lpar_name.return_value = 'fake_lpar'
        mock_zvm_name.return_value = 'fake_zvm'
        # case1: part of PCHIDs has no inuse FCP
        mock_fcg_mgr.fcp_ops.get_pchid_usage.return_value = (
            ['0A20', '0240', '0260', '03FC', '02E0'],
            {'02E0': '1A01 - 1A03', '03FC': '1B02, 1B05'})
        expect = {'cpc_sn': 'fake_cpc_sn',
                  'cpc_name': 'fake_cpc_name',
                  'hypervisor_hostname': 'fake_zvm',
                  'lpar': 'fake_lpar',
                  "pchids": [
                      {
                          "pchid": "0240",
                          "fcp_devices": "",
                          "fcp_devices_count": 0
                      },
                      {
                          "pchid": "0260",
                          "fcp_devices": "",
                          "fcp_devices_count": 0
                      },
                      {
                          "pchid": "02E0",
                          "fcp_devices": "1A01 - 1A03",
                          "fcp_devices_count": 3
                      },
                      {
                          "pchid": "03FC",
                          "fcp_devices": "1B02, 1B05",
                          "fcp_devices_count": 2
                      },
                      {
                          "pchid": "0A20",
                          "fcp_devices": "",
                          "fcp_devices_count": 0
                      }
                  ]}
        result = TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertDictEqual(expect, result)
        # case2: all PCHIDs without inuse FCP
        mock_fcg_mgr.fcp_ops.get_pchid_usage.return_value = (
            ['0260', '0240'], {})
        expect = {'cpc_sn': 'fake_cpc_sn',
                  'cpc_name': 'fake_cpc_name',
                  'hypervisor_hostname': 'fake_zvm',
                  'lpar': 'fake_lpar',
                  "pchids": [{
                          "pchid": "0240",
                          "fcp_devices": "",
                          "fcp_devices_count": 0
                      },
                      {
                          "pchid": "0260",
                          "fcp_devices": "",
                          "fcp_devices_count": 0
                      }
                  ]}
        result = TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertDictEqual(expect, result)
        # case3: an FCP whose PCHID lookup failed (pchid '') is left out
        mock_fcg_mgr.fcp_ops.get_pchid_usage.return_value = (
            ['', '0240'], {'': '1A05', '0240': '1A01'})
        expect = {'cpc_sn': 'fake_cpc_sn',
                  'cpc_name': 'fake_cpc_name',
                  'hypervisor_hostname': 'fake_zvm',
                  'lpar': 'fake_lpar',
                  "pchids": [{
                          "pchid": "0240",
                          "fcp_devices": "1A01",
                          "fcp_devices_count": 1
                      }
                  ]}
        result = TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertDictEqual(expect, result)
        # case4: no FCP devices / PCHIDs in any FCP template
        mock_fcg_mgr.fcp_ops.get_pchid_usage.return_value = ([], {})
        expect = {'cpc_sn': 'fake_cpc_sn',
                  'cpc_name': 'fake_cpc_name',
                  'hypervisor_hostname': 'fake_zvm',
                  'lpar': 'fake_lpar',
                  "pchids": []}
        result = TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertDictEqual(expect, result)

    @patch('zvmsdk.volumeop.FCPManager')
    @patch('zvmsdk.utils.get_zhypinfo')
    def test_get_fcp_devices_per_pchid_sync_failed(self, mock_zhypinfo,
                                                   mock_init_fcp_mgr):
        """exit non-zero instead of reporting a possibly stale FCP DB"""
        mock_fcp_mgr = Mock()
        mock_fcp_mgr.synced_with_zvm = False
        mock_init_fcp_mgr.return_value = mock_fcp_mgr
        with self.assertRaises(SystemExit) as cm:
            TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertIn('Failed to sync the FCP database with z/VM',
                      str(cm.exception.code))
        mock_fcp_mgr.fcp_ops.get_pchid_usage.assert_not_called()
        mock_zhypinfo.assert_not_called()

    @patch('zvmsdk.utils.execute')
    def test_zvm_userid_state(self, mock_execute):
        """only z/VM's explicit 'Invalid option' reply counts as missing"""
        cases = [
            ((1, 'HCPCQV003E Invalid option - ABCD0001\n'), 'missing'),
            ((0, 'ABCD0001 - DSC\n'), 'exists'),
            ((1, 'HCPCQU045E ABCD0001 not logged on\n'), 'exists'),
            ((1, 'HCPCQU361E LOGOFF/FORCE pending for user ABCD0001\n'),
             'exists'),
            ((1, 'HCPCQV003E Invalid option - ABCD0001X\n'), 'unknown'),
            ((1, 'sudo: a password is required\n'), 'unknown'),
            ((-1, ''), 'unknown')]
        for output, state in cases:
            mock_execute.return_value = output
            self.assertEqual(state, TEST_MODULE._zvm_userid_state('ABCD0001'),
                             output)
        mock_execute.assert_called_with(
            ['sudo', '/sbin/vmcp', 'query', 'ABCD0001'])

    @patch('zvmsdk.utils.get_zvm_name', Mock(return_value='fake_zvm'))
    @patch('zvmsdk.smtclient.get_smtclient')
    @patch('zvmsdk.database.get_db_backend')
    def test_get_held_fcp_devices(self, mock_backend, mock_smtclient):
        """reserved, connected or template rows, per assigner"""
        def row(fcp_id, assigner, reserved, connections, tmpl_id):
            return dict(fcp_id=fcp_id, assigner_id=assigner,
                        reserved=reserved, connections=connections,
                        tmpl_id=tmpl_id)
        mock_backend.return_value.fcp.return_value.get_all.return_value = [
            row('1a01', 'GONE0001', 1, 0, 't1'),
            row('1b01', 'GONE0001', 1, 0, 't1'),
            row('1a02', 'LIVE0001', 1, 2, 't1'),
            # released normally: the assigner alone is kept
            row('1a03', 'OLD00001', 0, 0, ''),
            row('1a04', '', 0, 0, ''),
            row('1a05', '', 1, 0, 't1')]
        mock_smtclient.return_value.get_vm_list.return_value = ['LIVE0001']
        states = {'GONE0001': 'missing', 'LIVE0001': 'exists'}
        with patch.object(TEST_MODULE, '_zvm_userid_state',
                          side_effect=states.get) as mock_state:
            result = TEST_MODULE.get_held_fcp_devices()
        self.assertEqual(
            {'hypervisor_hostname': 'fake_zvm',
             'assigners': [
                 {'userid': 'GONE0001', 'fcp_devices': '1A01, 1B01',
                  'zvm_userid': 'missing', 'guest_of_host': False},
                 {'userid': 'LIVE0001', 'fcp_devices': '1A02',
                  'zvm_userid': None, 'guest_of_host': True}],
             'without_assigner': '1A05'}, result)
        # z/VM is asked only about assigners that aren't guests of the host
        mock_state.assert_called_once_with('GONE0001')
        mock_backend.return_value.fcp.return_value.\
            reset_fcps_of_assigner.assert_not_called()

    @patch('zvmsdk.smtclient.get_smtclient')
    @patch('zvmsdk.database.get_db_backend')
    def test_release_fcp_devices(self, mock_backend, mock_smtclient):
        """release only assigners missing on z/VM and unknown to the host"""
        db = mock_backend.return_value.fcp.return_value
        db.reset_fcps_of_assigner.return_value = 2
        mock_smtclient.return_value.get_vm_list.return_value = ['GUEST001']
        states = {'GONE0001': 'missing', 'GONE0002': 'missing',
                  'LIVE0001': 'exists', 'ODD00001': 'unknown',
                  'GUEST001': 'missing'}
        with patch.object(TEST_MODULE, '_zvm_userid_state',
                          side_effect=states.get):
            # lower case input: assigner_id is stored in upper case
            result = TEST_MODULE.release_fcp_devices(
                ['GONE0001', 'gone0002', 'LIVE0001', 'ODD00001',
                 'guest001'])
        self.assertEqual(
            {'released': {'GONE0001': 2, 'GONE0002': 2},
             'skipped': {'LIVE0001': 'z/VM userid exists',
                         'ODD00001': 'z/VM userid unknown',
                         'GUEST001': 'guest of this host'}}, result)
        self.assertEqual([call('GONE0001'), call('GONE0002')],
                         db.reset_fcps_of_assigner.call_args_list)
