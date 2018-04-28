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

from smutLayer import makeVM
from smutLayer import ReqHandle
from smutLayer.tests.unit import base


class SMUTMakeVMTestCase(base.SMUTTestCase):
    """Test cases for makeVM.py in smutLayer."""

    def test_getReservedMemSize(self):
        rh = mock.Mock()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0}
        gap = makeVM.getReservedMemSize(rh, '1024M', '128g')
        self.assertEqual(gap, '130048M')

    def test_getReservedMemSize_invalid_suffix(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smut=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '1024M', '128T')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 4)
        self.assertEqual(rh.results['rc'], 4)
        self.assertEqual(rh.results['rs'], 205)

    def test_getReservedMemSize_max_less_than_initial(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smut=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '64G', '32G')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 4)
        self.assertEqual(rh.results['rc'], 4)
        self.assertEqual(rh.results['rs'], 206)

    def test_getReservedMemSize_equal_size(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smut=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '1024M', '1G')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 0)

    def test_getReservedMemSize_gap_G(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smut=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '512m', '9999G')
        self.assertEqual(gap, '9998G')
        self.assertEqual(rh.results['overallRC'], 0)
