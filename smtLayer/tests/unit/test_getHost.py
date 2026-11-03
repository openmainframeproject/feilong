#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

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

from unittest import mock
from smtLayer import ReqHandle
from smtLayer import getHost
from smtLayer.tests.unit import base
from zvmsdk import config


class SMTGetHostTestCase(base.SMTTestCase):
    """Test cases for getHost.py in smtLayer."""

    def test_getDiskPoolSpace9336(self):
        parts = ['v1', '9336-32', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390(self):
        parts = ['v1', '3390-09', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    def test_getDiskPoolSpace9336Unknown(self):
        parts = ['v1', '????', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390Unknown(self):
        parts = ['v1', '????', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    def test_getDiskPoolSpace9336UnknownWithFlag(self):
        parts = ['v1', '9336-?', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390UnknownWithFlag(self):
        parts = ['v1', '3390-?', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    @mock.patch('smtLayer.getHost.config.CONF')
    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_without_STANDBY(self, fake_smcli, mock_conf):
        mock_conf.zvm.use_smapi = True
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 PARKED IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value1:", ret_total, ret_used)
        self.assertEqual(4, ret_total)
        self.assertEqual(4, ret_used)

    @mock.patch('smtLayer.getHost.config.CONF')
    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_with_STANDBY(self, fake_smcli, mock_conf):
        mock_conf.zvm.use_smapi = True
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 STANDBY IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value2:", ret_total, ret_used)
        self.assertEqual(4, ret_total)
        self.assertEqual(3, ret_used)

    @mock.patch('smtLayer.getHost.config.CONF')
    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_no_CPU(self, fake_smcli, mock_conf):
        mock_conf.zvm.use_smapi = True
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS TYPE CORE_ID\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value3:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    @mock.patch('smtLayer.getHost.config.CONF')
    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_noTypebutOOO(self, fake_smcli, mock_conf):
        mock_conf.zvm.use_smapi = True
        fake_smcli.return_value = {
            'overallRC': 0, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'Partition mode: Z/VM\n\n'
                        'ADDRESS STATUS OOO CORE_ID\n'
                        '0000 MASTER-PROCESSOR CP 0000\n'
                        '0002 ALTERNATE IFL 0001\n'
                        '0003 PARKED IFL 0001\n'
                        '0004 STANDBY IFL 0002\n',
            'strError': ''
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value4:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    @mock.patch('smtLayer.getHost.config.CONF')
    @mock.patch.object(getHost, 'invokeSMCLI')
    def test_getCPUCount_with_overallRC_error(self, fake_smcli, mock_conf):
        mock_conf.zvm.use_smapi = True
        fake_smcli.return_value = {
            'overallRC': 24, 'rc': 0,
            'rs': 0, 'errno': 0,
            'response': 'SMAPI API failed\n',
            'strError': 'Input error'
        }
        rh = ReqHandle.ReqHandle(captureLogs=False,
                                smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        print("return value5:", ret_total, ret_used)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    # --- VMCP path tests for getCPUCount ---

    @mock.patch('smtLayer.getHost.VMCPHandler')
    @mock.patch('smtLayer.getHost.config.CONF')
    def test_getCPUCount_vmcp_path(self, mock_conf, mock_vmcp_cls):
        mock_conf.zvm.use_smapi = False
        mock_instance = mock.Mock()
        mock_instance.get_cpu_count.return_value = (4, 3)
        mock_vmcp_cls.return_value = mock_instance
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        self.assertEqual(4, ret_total)
        self.assertEqual(3, ret_used)
        mock_instance.get_cpu_count.assert_called_once_with()

    @mock.patch('smtLayer.getHost.VMCPHandler')
    @mock.patch('smtLayer.getHost.config.CONF')
    def test_getCPUCount_vmcp_path_fails(self, mock_conf, mock_vmcp_cls):
        mock_conf.zvm.use_smapi = False
        mock_instance = mock.Mock()
        mock_instance.get_cpu_count.return_value = (0, 0)
        mock_vmcp_cls.return_value = mock_instance
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        ret_total, ret_used = getHost.getCPUCount(rh)
        self.assertEqual(0, ret_total)
        self.assertEqual(0, ret_used)

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch('smtLayer.getHost.VMCPHandler')
    @mock.patch('smtLayer.getHost.invokeSMCLI')
    @mock.patch('smtLayer.getHost.config.CONF')
    def test_getFcpDevices_vmcp_path(self, mock_conf, mock_smcli,
                                     mock_vmcp_cls, mock_print):
        mock_conf.zvm.use_smapi = False
        mock_vmcp_cls.return_value.query_fcp_formatted.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': 'FCP device number: E800'}
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.assertEqual(0, getHost.getFcpDevices(rh))
        mock_smcli.assert_not_called()
        mock_print.assert_called_once_with('N', 'FCP device number: E800')

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch('smtLayer.getHost.VMCPHandler')
    @mock.patch('smtLayer.getHost.invokeSMCLI')
    @mock.patch('smtLayer.getHost.config.CONF')
    def test_getFcpDevices_vmcp_path_fails(self, mock_conf, mock_smcli,
                                           mock_vmcp_cls, mock_print):
        mock_conf.zvm.use_smapi = False
        mock_vmcp_cls.return_value.query_fcp_formatted.return_value = {
            'overallRC': 1, 'rc': 4, 'rs': 28, 'errno': 0,
            'strError': '', 'response': ''}
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.assertEqual(1, getHost.getFcpDevices(rh))
        mock_smcli.assert_not_called()

    @mock.patch.object(ReqHandle.ReqHandle, 'printLn')
    @mock.patch('smtLayer.getHost.VMCPHandler')
    @mock.patch('smtLayer.getHost.invokeSMCLI')
    @mock.patch('smtLayer.getHost.config.CONF')
    def test_getFcpDevices_smapi_path(self, mock_conf, mock_smcli,
                                      mock_vmcp_cls, mock_print):
        mock_conf.zvm.use_smapi = True
        mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0,
            'strError': '', 'response': 'FCP device number: E800'}
        rh = ReqHandle.ReqHandle(captureLogs=False, smt=mock.Mock())
        self.assertEqual(0, getHost.getFcpDevices(rh))
        mock_smcli.assert_called_once_with(
            rh, 'System_WWPN_Query', ['-T', 'dummy'])
        mock_vmcp_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Minimal /proc/sysinfo content that satisfies getGeneralInfo's parser so
# none of the "no info" error paths are triggered.
# ---------------------------------------------------------------------------
_SYSINFO = (
    "LPAR CPUs Total:        4\n"
    "LPAR CPUs Configured:   4\n"
    "Type:                   2964\n"
    "Manufacturer:           IBM\n"
    "VM00 Control Program:   z/VM 7.2\n"
)

# Smapi success return used for both System_Information_Query and
# System_Performance_Information_Query in the smapi (use_smapi=True) path.
_SMCLI_PERF_OK = {
    'overallRC': 0, 'rc': 0, 'rs': 0,
    'response': 'MEMORY_IN_USE=12345\n',
}


def _make_rh():
    """Return a mock ReqHandle that satisfies getGeneralInfo."""
    rh = mock.MagicMock()
    rh.printSysLog = mock.MagicMock()
    rh.printLn = mock.MagicMock()
    rh.updateResults = mock.MagicMock()
    rh.results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
    return rh


class GetGeneralInfoVmcpBranchTest(base.SMTTestCase):
    """
    Tests for the use_smapi=False (vmcp) storage/ipl branch in
    getHost.getGeneralInfo (lines 571-576).
    """

    def setUp(self):
        super().setUp()
        self._orig_use_smapi = config.CONF.zvm['use_smapi']
        # Patch the heavy infrastructure that surrounds the target branch.
        self._patches = []

        # subprocess.check_output – used for "vmcp query userid"
        p = mock.patch('smtLayer.getHost.subprocess.check_output',
                       return_value=b'LXUSR AT LXHOST')
        self._mock_subproc = p.start()
        self._patches.append(p)

        # /proc/sysinfo open()
        p = mock.patch('builtins.open',
                       mock.mock_open(read_data=_SYSINFO))
        self._mock_open = p.start()
        self._patches.append(p)

        # getCPUCount – irrelevant for the target branch
        p = mock.patch.object(getHost, 'getCPUCount', return_value=(4, 4))
        self._mock_cpu = p.start()
        self._patches.append(p)

        # os.uname – returns a tuple; index [4] is the arch string
        p = mock.patch('smtLayer.getHost.os.uname',
                       return_value=('', '', '', '', 's390x'))
        self._mock_uname = p.start()
        self._patches.append(p)

        # invokeSMCLI – only needed for System_Performance_Information_Query
        # in the vmcp path (storage/ipl come from VMCPHandler, not SMCLI).
        p = mock.patch.object(getHost, 'invokeSMCLI',
                              return_value=_SMCLI_PERF_OK)
        self._mock_smcli = p.start()
        self._patches.append(p)

        # VMCPHandler – the class instantiated at the top of getGeneralInfo
        p = mock.patch.object(getHost, 'VMCPHandler')
        self._mock_handler_cls = p.start()
        self._patches.append(p)
        self._mock_handler = self._mock_handler_cls.return_value

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        config.CONF.zvm['use_smapi'] = self._orig_use_smapi
        super().tearDown()

    def _set_use_smapi(self, value):
        config.CONF.zvm['use_smapi'] = value

    # ------------------------------------------------------------------
    # Scenario 1: use_smapi=False — query_cplevel and query_storage called
    # ------------------------------------------------------------------
    def test_vmcp_branch_calls_query_cplevel_and_query_storage(self):
        """
        When use_smapi is False, getGeneralInfo must call
        handler.query_cplevel() and handler.query_storage() to populate
        ipl, lparMemTotal, and lparMemStandby.
        """
        self._set_use_smapi(False)
        self._mock_handler.query_cplevel.return_value = \
            "IPL at 01/15/24 08:30:00 EST"
        self._mock_handler.query_storage.return_value = {
            "lparMemTotal": "65536M",
            "lparMemStandby": "0",
        }

        rh = _make_rh()
        getHost.getGeneralInfo(rh)

        self._mock_handler.query_cplevel.assert_called_once()
        self._mock_handler.query_storage.assert_called_once()

    # ------------------------------------------------------------------
    # Scenario 2: lparMemTotal and lparMemStandby taken from query_storage
    # ------------------------------------------------------------------
    def test_vmcp_branch_populates_lpar_memory_from_query_storage(self):
        """
        The values returned by query_storage must appear verbatim in the
        output line written via rh.printLn.
        """
        self._set_use_smapi(False)
        self._mock_handler.query_cplevel.return_value = ""
        self._mock_handler.query_storage.return_value = {
            "lparMemTotal": "32768M",
            "lparMemStandby": "4096M",
        }

        rh = _make_rh()
        getHost.getGeneralInfo(rh)

        # Collect every string passed to printLn and check the memory lines.
        combined = "\n".join(
            str(call) for call in rh.printLn.call_args_list)
        self.assertIn("32768M", combined)
        self.assertIn("4096M", combined)

    # ------------------------------------------------------------------
    # Scenario 3: ipl value taken from query_cplevel
    # ------------------------------------------------------------------
    def test_vmcp_branch_populates_ipl_from_query_cplevel(self):
        """
        The IPL string returned by query_cplevel must appear in the output
        written via rh.printLn.
        """
        self._set_use_smapi(False)
        expected_ipl = "IPL at 06/01/25 12:00:00 UTC"
        self._mock_handler.query_cplevel.return_value = expected_ipl
        self._mock_handler.query_storage.return_value = {
            "lparMemTotal": "65536M",
            "lparMemStandby": "0",
        }

        rh = _make_rh()
        getHost.getGeneralInfo(rh)

        combined = "\n".join(
            str(call) for call in rh.printLn.call_args_list)
        self.assertIn(expected_ipl, combined)

    # ------------------------------------------------------------------
    # Scenario 4: use_smapi=False — invokeSMCLI NOT called for storage
    # ------------------------------------------------------------------
    def test_vmcp_branch_does_not_call_smcli_for_storage(self):
        """
        When use_smapi is False, System_Information_Query must NOT be
        invoked (storage/ipl come from VMCPHandler exclusively).
        """
        self._set_use_smapi(False)
        self._mock_handler.query_cplevel.return_value = ""
        self._mock_handler.query_storage.return_value = {
            "lparMemTotal": "65536M",
            "lparMemStandby": "0",
        }

        rh = _make_rh()
        getHost.getGeneralInfo(rh)

        called_apis = [
            call.args[1]
            for call in self._mock_smcli.call_args_list
        ]
        self.assertNotIn("System_Information_Query", called_apis)

    # ------------------------------------------------------------------
    # Scenario 5: use_smapi=True — VMCPHandler.query_storage NOT called
    # ------------------------------------------------------------------
    def test_smapi_branch_does_not_call_vmcp_storage(self):
        """
        When use_smapi is True, the SMAPI path is taken; query_storage
        and query_cplevel must NOT be called.
        """
        self._set_use_smapi(True)
        # Provide a valid System_Information_Query response so the smapi
        # path can parse memory without errors.
        self._mock_smcli.return_value = {
            'overallRC': 0, 'rc': 0, 'rs': 0,
            'response': (
                'STORAGE=TOTAL=65536M ONLINE=65536M STANDBY=0 RESERVED=0\n'
                'MEMORY_IN_USE=12345\n'
            ),
        }

        rh = _make_rh()
        getHost.getGeneralInfo(rh)

        self._mock_handler.query_storage.assert_not_called()
        self._mock_handler.query_cplevel.assert_not_called()
