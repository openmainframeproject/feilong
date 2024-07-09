#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8

# Copyright 2018 IBM Corp.
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

from smtLayer import vmUtils
from smtLayer import ReqHandle
from smtLayer.tests.unit import base


class SMTvmUtilsTestCase(base.SMTTestCase):
    """Test cases for vmUtils.py in smtLayer."""

    def test_getVM_directory_py3(self):
        rh = ReqHandle.ReqHandle(captureLogs=False)
        with mock.patch('subprocess.check_output') as exec_cmd:
            # subprocess.check_output returns bytes in py3
            exec_cmd.return_value = (
                b"0 0 0 (details) None\n"
                b"USER T9572493 LBYONLY 2048m 64G G\nINCLUDE ZCCDFLT\n"
                b"COMMAND DEF STOR RESERVED 63488M\n"
                b"CPU 00 BASE\nIPL 0100\nLOGONBY MAINT\nMACHINE ESA 32\n"
                b"MDISK 0100 3390 48697 5500 OMB1B6 MR\n"
                b"*DVHOPT LNK0 LOG1 RCM1 SMS0 NPW1 LNGAMENG PWC20180808 "
                b"CRC\xf3:\n")
            expected_resp = (
                u"USER T9572493 LBYONLY 2048m 64G G\nINCLUDE ZCCDFLT\n"
                u"COMMAND DEF STOR RESERVED 63488M\nCPU 00 BASE\nIPL 0100\n"
                u"LOGONBY MAINT\nMACHINE ESA 32\n"
                u"MDISK 0100 3390 48697 5500 OMB1B6 MR\n"
                u"*DVHOPT LNK0 LOG1 RCM1 SMS0 NPW1 LNGAMENG PWC20180808 "
                u"CRC\ufffd:\n")
            res = vmUtils.invokeSMCLI(rh, "Image_Query_DM", ['-T', 'fakeuid'])
            self.assertEqual(res['response'], expected_resp)
            exec_cmd.assert_called_once_with(
                ['sudo', '/opt/zthin/bin/smcli', 'Image_Query_DM',
                 '--addRCheader', '-T', 'fakeuid',
                 '--timeout', '240'], close_fds=True)
