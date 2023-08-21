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
from mock import MagicMock, Mock, patch
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
    @patch('zvmsdk.database.get_fcp_conn', MagicMock())
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
        mock_fcg_mgr.db.get_pchids_of_all_inuse_fcp_devices.return_value = {
            '02E0': '1A01 - 1A03',
            '03FC': '1B02, 1B05'
        }
        mock_fcg_mgr.db.get_pchids_from_all_fcp_templates.return_value = [
            '0A20', '0240', '0260', '03FC', '02E0']
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
        mock_fcg_mgr.db.get_pchids_of_all_inuse_fcp_devices.return_value = {}
        mock_fcg_mgr.db.get_pchids_from_all_fcp_templates.return_value = ['0260', '0240']
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
        # case3: no FCP devices / PCHIDs in any FCP template
        mock_fcg_mgr.db.get_pchids_of_all_inuse_fcp_devices.return_value = {}
        mock_fcg_mgr.db.get_pchids_from_all_fcp_templates.return_value = []
        expect = {'cpc_sn': 'fake_cpc_sn',
                  'cpc_name': 'fake_cpc_name',
                  'hypervisor_hostname': 'fake_zvm',
                  'lpar': 'fake_lpar',
                  "pchids": []}
        result = TEST_MODULE.get_fcp_devices_per_pchid()
        self.assertDictEqual(expect, result)
