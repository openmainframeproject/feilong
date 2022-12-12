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

from smtLayer import changeVM
from smtLayer import ReqHandle
from smtLayer.tests.unit import base


class SMTChangeVMTestCase(base.SMTTestCase):
    """Test cases for makeVM.py in smtLayer."""

    @mock.patch.object(changeVM, 'invokeSMCLI')
    def test_adddevno(self, msmcli):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())

        parms = {'vaddr': '1000', 'rdev': 'ABCD', 'mode': 'MR'}
        rh.parms = parms
        rh.userid = "user1"
        changeVM.adddevno(rh)

        msmcli.assert_called_once_with(rh, 'Image_Disk_Create_DM',
            ['-T', 'user1', '-v', '1000', '-t', '3390', '-a', 'DEVNO',
             '-r', 'ABCD', '-u', '1', '-z', '1', '-f', '1', '-m', 'MR'],
            hideInLog=[])

        self.assertEqual(rh.results['overallRC'], 0)
