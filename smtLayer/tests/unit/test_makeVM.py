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

from smtLayer import makeVM
from smtLayer import ReqHandle
from smtLayer.tests.unit import base


class SMTMakeVMTestCase(base.SMTTestCase):
    """Test cases for makeVM.py in smtLayer."""

    def test_getReservedMemSize(self):
        rh = mock.Mock()
        rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0}
        gap = makeVM.getReservedMemSize(rh, '1024M', '128g')
        self.assertEqual(gap, '65536M')

    def test_getReservedMemSize_invalid_suffix(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '1024M', '128T')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 4)
        self.assertEqual(rh.results['rc'], 4)
        self.assertEqual(rh.results['rs'], 205)

    def test_getReservedMemSize_max_less_than_initial(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '64G', '32G')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 4)
        self.assertEqual(rh.results['rc'], 4)
        self.assertEqual(rh.results['rs'], 206)

    def test_getReservedMemSize_equal_size(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '1024M', '1G')
        self.assertEqual(gap, '0M')
        self.assertEqual(rh.results['overallRC'], 0)

    # default maximum reserved memory is 128G=131072M
    def test_getReservedMemSize_max_reserved(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '512m', '256G')
        self.assertEqual(gap, '65536M')
        self.assertEqual(rh.results['overallRC'], 0)

    # As default maximum reserved memory is 128G,
    # which can't exceed 9999999M, so this case will
    # return 131072M. If future the maximum reserved
    # memory limit is not there, recover this case.
    def test_getReservedMemSize_gap_G(self):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        gap = makeVM.getReservedMemSize(rh, '512m', '9999G')
        # self.assertEqual(gap, '9998G')
        self.assertEqual(gap, '65536M')
        self.assertEqual(rh.results['overallRC'], 0)

    @mock.patch("os.write")
    def test_create_VM_cpu_4(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:1G', 'cpuCnt': 4}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'COMMAND DEFINE CPU 01 TYPE IFL\n'
                                    b'COMMAND DEFINE CPU 02 TYPE IFL\n'
                                    b'COMMAND DEFINE CPU 03 TYPE IFL\n'
                                    b'MDISK 0102 FB-512 V-DISK 2097152 MWV\n')

    @mock.patch("os.write")
    def test_create_VM_swap_1G(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:1G'}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'MDISK 0102 FB-512 V-DISK 2097152 MWV\n')

    @mock.patch("os.write")
    def test_create_VM_swap_2G(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:2G'}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'MDISK 0102 FB-512 V-DISK 4194296 MWV\n')

    @mock.patch("os.write")
    def test_create_VM_swap_2048M(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:2048M'}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'MDISK 0102 FB-512 V-DISK 4194296 MWV\n')

    @mock.patch("os.write")
    def test_create_VM_swap_4096M(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:4096M'}
        rh.parms = parms
        rs = makeVM.createVM(rh)
        self.assertEqual(4, rs)

    @mock.patch("os.write")
    def test_create_VM_swap_256M(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'vdisk': '0102:256M'}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'MDISK 0102 FB-512 V-DISK 524288 MWV\n')

    @mock.patch("os.write")
    def test_create_VM_STOR_RESERVED_positive(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '4G',
                 'privClasses': 'G', 'setReservedMem': ''}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 4G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'COMMAND DEF STOR RESERVED 3072M\n')

    @mock.patch("os.write")
    def test_create_VM_STOR_RESERVED_0M(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1G', 'maxMemSize': '1G',
                 'privClasses': 'G', 'setReservedMem': ''}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1G 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'COMMAND DEF STOR RESERVED 0M\n')

    @mock.patch("os.write")
    def test_create_VM_STOR_RESERVED_0M_diff_unit(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1024M', 'maxMemSize': '1G',
                 'privClasses': 'G', 'setReservedMem': ''}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1024M 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'COMMAND DEF STOR RESERVED 0M\n')

    @mock.patch("os.write")
    def test_create_with_profile(self, write):
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                 smt=mock.Mock())
        parms = {'pw': 'pwd', 'priMemSize': '1024M', 'maxMemSize': '1G',
                 'privClasses': 'G',
                 'comment': 'comment1$@$@$this is comment2$@$@$'}
        rh.parms = parms
        makeVM.createVM(rh)
        write.assert_called_with(mock.ANY, b'USER  pwd 1024M 1G G\n'
                                    b'COMMAND SET VCONFIG MODE LINUX\n'
                                    b'COMMAND DEFINE CPU 00 TYPE IFL\n'
                                    b'* COMMENT1\n'
                                    b'* THIS IS COMMENT2\n')
