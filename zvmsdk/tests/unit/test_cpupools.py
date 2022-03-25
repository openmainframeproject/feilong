# Copyright 2017 IBM Corp.
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

import zvmsdk.cpupoolops as cpop
import zvmsdk.exception as exception
import zvmsdk.utils as zvmutils
from zvmsdk.tests.unit import base


class ZVMCpuPOOLVMCPTestCases(base.SDKTestCase):
    @classmethod
    def setUpClass(cls):
        super(ZVMCpuPOOLVMCPTestCases, cls).setUpClass()
        cls.cpop = cpop.CpupoolVMCPOPS()

    def test_validate_cpupool_name(self):
        self.cpop._validate_cpupool_name("NAME1")

        self.assertRaises(exception.SDKInvalidInputFormat,
            self.cpop._validate_cpupool_name, "")
        self.assertRaises(exception.SDKInvalidInputFormat,
            self.cpop._validate_cpupool_name, "NAMENAME1")

    def test_validate_and_get_limittype(self):
        t = self.cpop._validate_and_get_limittype("LIMIT")
        self.assertEqual("LIMIT", t)

        t = self.cpop._validate_and_get_limittype("")
        self.assertEqual("NOLIM", t)

        self.assertRaises(exception.SDKInvalidInputFormat,
            self.cpop._validate_and_get_limittype, "DUMMY")

    def test_validate_and_get_cputype(self):
        t = self.cpop._validate_and_get_cputype("CP")
        self.assertEqual("CP", t)

        t = self.cpop._validate_and_get_cputype("")
        self.assertEqual("IFL", t)

        self.assertRaises(exception.SDKInvalidInputFormat,
            self.cpop._validate_and_get_cputype, "DUMMY")

    @mock.patch.object(zvmutils, 'vmcp')
    def test_exec_vmcp_handle_ret(self, vmcp):
        cmd = "q userid"

        vmcp.return_value = (0, "ok")
        self.cpop._exec_vmcp_handle_ret(cmd)

        vmcp.return_value = (1, "error orrur")
        self.assertRaises(exception.ZVMVMCPExecutionFail,
            self.cpop._exec_vmcp_handle_ret, cmd)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_create(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.create('p1')

        exp = "DEFINE RESPOOL p1 CPU NOLIM TYPE IFL"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_create_with_cap(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.create('p1', limittype='CAP', limit='2.5')

        exp = "DEFINE RESPOOL p1 CPU CAP 2.5 TYPE IFL"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_create_with_nolimit(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.create('p1', limittype='NOLIM')

        exp = "DEFINE RESPOOL p1 CPU NOLIM TYPE IFL"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_create_with_cpu(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.create('p1', cputype='CP')

        exp = "DEFINE RESPOOL p1 CPU NOLIM TYPE CP"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_create_with_limit_cpu(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.create('p1', limittype='LIMIT', limit="40%",
                         cputype='IFL')

        exp = "DEFINE RESPOOL p1 CPU LIMIT 40% TYPE IFL"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_delete(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.delete('POOL1')

        exp = "DELETE CPUPOOL POOL1"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_add(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.add('VM1', 'POOL1')

        exp = "SCH VM1 POOL1"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_remove(self, vmcp):
        vmcp.return_value = 0, ""
        self.cpop.remove('VM1')

        exp = "SCH VM1 NOPOOL"
        vmcp.assert_called_once_with(exp)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_all_res(self, vmcp):
        mret = '''Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   CP   NoLimit  ----       2
        POOL2CPU    2.00 Cores   IFL  NoLimit  ----       3'''

        vmcp.return_value = 0, mret
        out = self.cpop.get_all()

        exp = "QUERY CPUPOOL "
        vmcp.assert_called_once_with(exp)

        exp = [{'name': 'POOL1', 'cpu': '1.00 Cores',
                'type': 'CP', 'storage': 'NoLimit',
                'trim': "----", 'members': '2'},
               {'name': 'POOL2CPU', 'cpu': '2.00 Cores',
                'type': 'IFL', 'storage': 'NoLimit',
                'trim': "----", 'members': '3'}]
        self.assertEqual(exp, out)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_no_input_member(self, vmcp):
        mret = '''Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   CP   NoLimit  ----       2'''

        vmcp.return_value = 0, mret

        detail, members = self.cpop.get('POOL1')

        exp = "QUERY CPUPOOL POOL1"
        vmcp.assert_called_once_with(exp)

        exp_detail = {'name': 'POOL1', 'cpu': '1.00 Cores',
                      'type': 'CP', 'storage': 'NoLimit',
                      'trim': "----", 'members': '2'}
        self.assertEqual(1, len(detail))
        self.assertDictEqual(exp_detail, detail[0])

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_no_output_member(self, vmcp):
        mret = '''Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   CP   NoLimit  ----       2
        Resource pool POOL1 has no members'''

        vmcp.return_value = 0, mret

        detail, members = self.cpop.get('POOL1', including_members=True)

        exp = "QUERY CPUPOOL POOL1 MEMBERS"
        vmcp.assert_called_once_with(exp)

        exp_detail = {'name': 'POOL1', 'cpu': '1.00 Cores',
                      'type': 'CP', 'storage': 'NoLimit',
                      'trim': "----", 'members': '2'}
        self.assertEqual(1, len(detail))
        self.assertDictEqual(exp_detail, detail[0])
        self.assertEqual([], members)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_including_members(self, vmcp):
        mret = '''Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   CP   NoLimit  ----       2
        The following users are members of resource pool POOL1:
        MYTEST1
        MYTEST2'''
        vmcp.return_value = 0, mret

        detail, members = self.cpop.get('POOL1', including_members=True)

        exp = "QUERY CPUPOOL POOL1 MEMBERS"
        vmcp.assert_called_once_with(exp)

        exp_detail = {'name': 'POOL1', 'cpu': '1.00 Cores',
                      'type': 'CP', 'storage': 'NoLimit',
                      'trim': "----", 'members': '2'}
        self.assertEqual(1, len(detail))
        self.assertDictEqual(exp_detail, detail[0])
        self.assertEqual(['MYTEST1', 'MYTEST2'], members)

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_pool_from_vm_not_found(self, vmcp):
        mret = 'User SJICIC94 is not in a resource pool'
        vmcp.return_value = 0, mret

        ret = self.cpop.get_pool_from_vm('SJICIC94')
        exp = "QUERY CPUPOOL USER SJICIC94"
        vmcp.assert_called_once_with(exp)

        self.assertEqual(0, len(ret))

    @mock.patch.object(zvmutils, 'vmcp')
    def test_get_pool_from_vm_found(self, vmcp):
        mret = 'User SJICIC94 is in resource pool POOL1'
        vmcp.return_value = 0, mret

        ret = self.cpop.get_pool_from_vm('SJICIC94')
        exp = "QUERY CPUPOOL USER SJICIC94"
        vmcp.assert_called_once_with(exp)

        self.assertEqual('POOL1', ret)


class ZVMCpuPOOLTestCases(base.SDKTestCase):
    @classmethod
    def setUpClass(cls):
        super(ZVMCpuPOOLTestCases, cls).setUpClass()
        cls.ops = cpop.get_cpupoolops()

    def test_get_cpupool_ops_type(self):
        self.assertEqual(cpop.CpupoolVMCPOPS, type(self.ops))
