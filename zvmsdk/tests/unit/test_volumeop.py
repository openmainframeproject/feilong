# Copyright 2017, 2021 IBM Corp.
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
import shutil
from mock import call, Mock

from zvmsdk import database
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import volumeop
from zvmsdk.tests.unit import base


class TestVolumeConfiguratorAPI(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVolumeConfiguratorAPI, cls).setUpClass()
        cls.configurator = volumeop.VolumeConfiguratorAPI()

    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd_direct")
    def test_get_status_code_from_systemctl(self, execute_cmd):
        line1 = ('(Error) ULTVMU0316E On CBM54008, command sent through IUCV '
                 'failed. cmd: systemctl status zvmguestconfigure, rc: 8, rs: '
                 '3, out: zvmguestconfigure.service - Activation engine '
                 'for configuring zLinux os when it start up')
        line2 = ('Loaded: loaded (/etc/systemd/system/zvmguest configure.'
                 'service; enabled; vendor preset: disabled)')
        line3 = ('   Active: failed (Result: exit-code) since Thu '
                 '2020-12-17 05:19:09 EST; 8s ago')
        line4 = ('  Process: 187837 ExecStart=/usr/bin/zvmguestcon'
                 'figure start (code=exited, status=1/FAILURE)')
        # from this line on, we wont process them
        line5 = ' Main PID: 187837 (code=exited, status=1/FAILURE)'
        line6 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                 'zvmguestconfigure[187837]: remove WWPN 0x500507680b22bac6 '
                 'in zfcp.conf')
        line7 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                 'zvmguestconfigure[187837]: remove WWPN 0x500507680b22bac7 '
                 'in zfcp.conf')
        line8 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                 'zvmguestconfigure[187837]: remove WWPN 0x500507680d060027 '
                 'in zfcp.conf')
        line9 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                 'zvmguestconfigure[187837]: remove WWPN 0x500507680d120027 '
                 'in zfcp.conf')
        line10 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                  'zvmguestconfigure[187837]: remove WWPN 0x500507680d760027 '
                  'in zfcp.conf')
        line11 = ('ERROR: Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                  'zvmguestconfigure[187837]: remove WWPN 0x500507680d820027 '
                  'in zfcp.conf')
        line12 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com '
                  'zvmguestconfigure[187837]: zvmguestconfigure has '
                  'successfully processed the reader files with exit_code: 1.')
        line13 = ("Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com systemd[1]"
                  ": zvmguestconfigure.service: Main process exited, "
                  "code=exited, status=1/FAILURE")
        line14 = ("Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com systemd[1]"
                  ": zvmguestconfigure.service: Failed with result "
                  "'exit-code'.")
        line15 = ('Dec 17 05:19:09 rhel82-bfv.boeblingen.de.ibm.com systemd[1]'
                  ': Failed to start Activation engine for configuring zLinux '
                  'os when it start up.')
        line16 = 'Return code 8, Reason code 3.'
        output = {'overallRC': 2, 'rc': 8, 'rs': 3, 'errno': 0, 'strError': '',
                  'response': [line1, line2, line3, line4, line5, '', line6,
                               line7, line8, line9, line10, line11, line12,
                               line13, line14, line15, '', line16],
                  'logEntries': []}
        execute_cmd.return_value = output
        assigner_id = 'userid1'
        command = 'fake command'
        code = self.configurator._get_status_code_from_systemctl(assigner_id,
                                                                 command)
        self.assertEqual(code, 1)

    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd_direct")
    @mock.patch.object(dist.rhel7, "create_active_net_interf_cmd")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "_get_status_code_from_systemctl")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "configure_volume_attach")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI.check_IUCV_is_ready")
    def test_config_attach_reachable_but_exception(self, is_reachable,
                                                   config_attach,
                                                   get_status_code,
                                                   restart_zvmguestconfigure,
                                                   execute_cmd, get_dist):
        """config_attach has almost same logic with config_detach
        so only write UT cases of config_attach"""
        fcp_list = ['1a11', '1b11']
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'

        get_dist.return_value = dist.rhel7
        config_attach.return_value = None
        is_reachable.return_value = True
        get_status_code.return_value = 1
        execute_cmd.return_value = {'rc': 3}
        active_cmds = 'systemctl start zvmguestconfigure.service'
        restart_zvmguestconfigure.return_value = active_cmds
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.configurator.config_attach,
                          fcp_list, assigner_id, target_wwpns,
                          target_lun, multipath,
                          os_version, mount_point)
        get_dist.assert_called_once_with(os_version)
        restart_zvmguestconfigure.assert_called_once_with()
        execute_cmd.assert_called_once_with(assigner_id, active_cmds)

    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd_direct")
    @mock.patch.object(dist.rhel7, "create_active_net_interf_cmd")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "_get_status_code_from_systemctl")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "configure_volume_attach")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI.check_IUCV_is_ready")
    def test_config_attach_reachable(self, is_reachable, config_attach,
                                     get_status_code,
                                     restart_zvmguestconfigure, execute_cmd,
                                     get_dist):
        fcp_list = ['1a11', '1b11']
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'

        get_dist.return_value = dist.rhel7
        config_attach.return_value = None
        is_reachable.return_value = True
        get_status_code.return_value = 1
        execute_cmd.return_value = {'rc': 0}
        active_cmds = 'systemctl start zvmguestconfigure.service'
        restart_zvmguestconfigure.return_value = active_cmds
        self.configurator.config_attach(fcp_list, assigner_id, target_wwpns,
                                        target_lun, multipath, os_version,
                                        mount_point)
        get_dist.assert_called_once_with(os_version)
        restart_zvmguestconfigure.assert_called_once_with()
        execute_cmd.assert_called_once_with(assigner_id,
                                            active_cmds)

    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "configure_volume_attach")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI.check_IUCV_is_ready")
    def test_config_attach_not_reachable(self, is_reachable, config_attach,
                                         get_dist):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        is_reachable.return_value = False
        get_dist.return_value = dist.rhel7
        config_attach.return_value = None

        self.configurator.config_attach(fcp, assigner_id, target_wwpns,
                                        target_lun, multipath, os_version,
                                        mount_point)
        get_dist.assert_called_once_with(os_version)

    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd")
    def test_check_IUCV_is_ready(self, execute_cmd):
        assigner_id = 'fakeid'
        execute_cmd.return_value = ''

        ret = self.configurator.check_IUCV_is_ready(assigner_id)
        execute_cmd.assert_called_once_with(assigner_id, 'pwd')
        self.assertEqual(ret, True)

    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd")
    def test_check_IUCV_is_ready_not_ready(self, execute_cmd):
        # case: not ready, but can continue
        assigner_id = 'fakeid'
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        execute_cmd.side_effect = exception.SDKSMTRequestFailed(
            results, 'fake error contains other things')

        ret = self.configurator.check_IUCV_is_ready(assigner_id)
        execute_cmd.assert_called_once_with(assigner_id, 'pwd')
        self.assertEqual(ret, False)

    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd")
    def test_check_IUCV_is_ready_raise_excetion(self, execute_cmd):
        # case: not ready, must raise exception
        assigner_id = 'fakeid'
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        execute_cmd.side_effect = exception.SDKSMTRequestFailed(
            results, 'fake error contains UNAUTHORIZED_ERROR')

        self.assertRaises(exception.SDKVolumeOperationError,
                          self.configurator.check_IUCV_is_ready,
                          assigner_id)

    def test_config_force_attach(self):
        pass

    def test_config_force_detach(self):
        pass

    @mock.patch("zvmsdk.smtclient.SMTClient.punch_file")
    @mock.patch.object(shutil, "rmtree")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI._create_file")
    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.dist.rhel7.get_volume_attach_configuration_cmds")
    def test_config_attach_active(self, get_attach_cmds, get_dist,
                                  create_file, rmtree, punch_file):
        fcp_list = ['1a11', '1b11']
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        config_file = '/tm/userid1xxx/attach_volume.sh'
        config_file_path = '/tm/userid1xxx/'
        linuxdist = dist.rhel7()
        get_dist.return_value = linuxdist
        create_file.return_value = (config_file, config_file_path)
        rmtree.return_value = None
        self.configurator.configure_volume_attach(fcp_list, assigner_id,
                                                  target_wwpns, target_lun,
                                                  multipath, os_version,
                                                  mount_point, linuxdist)
        get_attach_cmds.assert_called_once_with(' '.join(fcp_list),
                                                ' '.join(target_wwpns),
                                                target_lun, multipath,
                                                mount_point)
        punch_file.assert_called_once_with(assigner_id, config_file, 'X')

    @mock.patch("zvmsdk.smtclient.SMTClient.punch_file")
    @mock.patch.object(shutil, "rmtree")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI._create_file")
    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.dist.rhel7.get_volume_detach_configuration_cmds")
    def test_config_detach_active(self, get_detach_cmds, get_dist,
                                  create_file, rmtree, punch_file):
        fcp_list = ['1a11', '1b11']
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        connections = 2
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        config_file = '/tm/userid1xxx/attach_volume.sh'
        config_file_path = '/tm/userid1xxx/'
        linuxdist = dist.rhel7()
        get_dist.return_value = linuxdist
        create_file.return_value = (config_file, config_file_path)
        rmtree.return_value = None
        self.configurator.configure_volume_detach(fcp_list, assigner_id,
                                                  target_wwpns, target_lun,
                                                  multipath, os_version,
                                                  mount_point, linuxdist,
                                                  connections)
        get_detach_cmds.assert_called_once_with(' '.join(fcp_list),
                                                ' '.join(target_wwpns),
                                                target_lun, multipath,
                                                mount_point, connections)
        punch_file.assert_called_once_with(assigner_id, config_file, 'X')


class TestFCP(base.SDKTestCase):

    def test_parse_normal(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Free',
                'opnstk1:   NPIV world wide port number: NONE',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181',
                'Owner: NONE']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertEqual('free', fcp._dev_status)
        self.assertIsNone(fcp._npiv_port)
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())
        self.assertEqual('NONE', fcp.get_owner().upper())

    def test_parse_npiv(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Active',
                'opnstk1:   NPIV world wide port number: 20076D8500005182',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181',
                'Owner: UNIT0001']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertEqual('active', fcp._dev_status)
        self.assertEqual('20076D8500005182', fcp._npiv_port.upper())
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())
        self.assertEqual('UNIT0001', fcp.get_owner().upper())


class TestFCPManager(base.SDKTestCase):

    @classmethod
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUpClass(cls):
        super(TestFCPManager, cls).setUpClass()
        cls.fcpops = volumeop.FCPManager()
        cls.db_op = database.FCPDbOperator()

    def test_expand_fcp_list_normal(self):
        fcp_list = "1f10;1f11;1f12;1f13;1f14"
        expected = {0: set(['1f10']),
                    1: set(['1f11']),
                    2: set(['1f12']),
                    3: set(['1f13']),
                    4: set(['1f14'])}

        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_dash(self):
        fcp_list = "1f10-1f14"
        expected = {0: set(['1f10', '1f11', '1f12', '1f13', '1f14'])}
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_dash(self):
        fcp_list = "1f10;1f11-1f13;1f17"
        expected = {0: set(['1f10']),
                    1: set(['1f11', '1f12', '1f13']),
                    2: set(['1f17'])}
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_2dash(self):
        fcp_list = "1f10;1f11-1f13;1f17-1f1a;1f02"
        expected = {0: set(['1f10']),
                    1: set(['1f11', '1f12', '1f13']),
                    2: set(['1f17', '1f18', '1f19', '1f1a']),
                    3: set(['1f02'])}
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_uncontinuous_equal_count(self):
        fcp_list = "5c70-5c71,5c73-5c74;5d70-5d71,5d73-5d74"
        expected = {0: set(['5c70', '5c71', '5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74'])}
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_4_uncontinuous_equal_count(self):
        fcp_list = "5c70-5c71,5c73-5c74;5d70-5d71,\
            5d73-5d74;1111-1112,1113-1114;2211-2212,2213-2214"
        expected = {0: set(['5c70', '5c71', '5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74']),
                    2: set(['1111', '1112', '1113', '1114']),
                    3: set(['2211', '2212', '2213', '2214']),
                   }
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_uncontinuous_not_equal_count(self):
        fcp_list = "5c73-5c74;5d70-5d71,5d73-5d74"
        expected = {0: set(['5c73', '5c74']),
                    1: set(['5d70', '5d71', '5d73', '5d74'])}
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_fcp_info_by_status")
    def test_get_all_fcp_info(self, get_fcp_info):
        get_fcp_info.return_value = []
        self.fcpops._get_all_fcp_info('dummy1')
        get_fcp_info.assert_called_once_with('dummy1', None)

    def test_add_fcp_for_assigner(self):
        # create 2 FCP
        self.db_op.new('a83c', 0)
        self.db_op.new('a83d', 0)
        self.db_op.new('a83e', 0)
        self.db_op.new('a83f', 0)

        # find FCP for user and FCP not exist, should allocate them
        try:
            flag1 = self.fcpops.add_fcp_for_assigner('a83c', 'dummy1')
            flag2 = self.fcpops.add_fcp_for_assigner('a83d', 'dummy2')

            flag1 = self.fcpops.add_fcp_for_assigner('a83e', 'dummy1')
            flag2 = self.fcpops.add_fcp_for_assigner('a83f', 'dummy2')

            self.assertEqual(True, flag1)
            self.assertEqual(True, flag2)

            fcp_list = self.db_op.get_from_fcp('a83c')
            expected = [(u'a83c', u'dummy1', 1, 0, 0, u'', '', '')]
            self.assertEqual(expected, fcp_list)

            fcp_list = self.db_op.get_from_fcp('a83d')
            expected = [(u'a83d', u'dummy2', 1, 0, 0, u'', '', '')]
            self.assertEqual(expected, fcp_list)

            connections = self.db_op.get_connections_from_assigner('dummy1')
            self.assertEqual(2, connections)

            connections = self.db_op.get_connections_from_assigner('dummy2')
            self.assertEqual(2, connections)

        finally:
            self.db_op.delete('a83c')
            self.db_op.delete('a83d')
            self.db_op.delete('a83e')
            self.db_op.delete('a83f')

    def test_find_and_reserve_fcp_new(self):
        # create 2 FCP
        self.db_op.new('b83c', 0)
        self.db_op.new('b83d', 0)

        # find FCP for user and FCP not exist, should allocate them
        try:
            fcp1 = self.fcpops.find_and_reserve_fcp('dummy1')
            fcp2 = self.fcpops.find_and_reserve_fcp('dummy2')

            self.assertEqual('b83c', fcp1)
            self.assertEqual('b83d', fcp2)

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'', 0, 1, 0, u'', '', '')]
            self.assertEqual(expected, fcp_list)

            fcp_list = self.db_op.get_from_fcp('b83d')
            expected = [(u'b83d', u'', 0, 1, 0, u'', '', '')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('b83c')
            self.db_op.delete('b83d')

    def test_find_and_reserve_fcp_old(self):
        self.db_op = database.FCPDbOperator()
        # create 2 FCP
        self.db_op.new('c83c', 0)
        self.db_op.new('c83d', 0)

        # find FCP for user and FCP not exist, should allocate them
        try:
            fcp1 = self.fcpops.find_and_reserve_fcp('user1')
            self.assertEqual('c83c', fcp1)
            self.fcpops.increase_fcp_usage('c83c', 'user1')

            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 1, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            # After usage, we need find c83d now
            fcp2 = self.fcpops.find_and_reserve_fcp('user2')
            self.assertEqual('c83d', fcp2)
            fcp_list = self.db_op.get_from_fcp('c83d')
            expected = [('c83d', '', 0, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.increase_fcp_usage('c83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 2, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('c83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 1, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('c83c')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 0, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            # unreserve makes this fcp free
            self.fcpops.unreserve_fcp('c83c')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 0, 0, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)

            fcp3 = self.fcpops.find_and_reserve_fcp('user3')
            self.assertEqual('c83c', fcp3)
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [('c83c', 'user1', 0, 1, 0, '', '', '')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('c83c')
            self.db_op.delete('c83d')

    def test_find_and_reserve_fcp_exception(self):
        # no FCP at all

        # find FCP for user and FCP not exist, should alloca
        fcp = self.fcpops.find_and_reserve_fcp('user1')
        self.assertIsNone(fcp)

    @mock.patch("zvmsdk.database.FCPDbOperator."
                "get_reserved_fcps_from_assigner")
    def test_get_available_fcp_reserve_false(self, get_from_assigner):
        """test reserve == False.
        no matter what connections is, the output will be same."""
        base.set_conf('volume', 'get_fcp_pair_with_same_index', 0)
        # case1: get_from_assigner return []
        get_from_assigner.return_value = []
        result = self.fcpops.get_available_fcp('user1', False)
        self.assertEqual([], result)
        # case2: get_from_assigner return ['1234', '5678']
        get_from_assigner.return_value = [('1234', '', 0, 0, 0, ''),
                                          ('5678', '', 0, 0, 0, '')]
        result = self.fcpops.get_available_fcp('user1', False)
        expected = ['1234', '5678']
        self.assertEqual(expected, result)

    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm", Mock())
    @mock.patch("zvmsdk.database.FCPDbOperator.get_path_count")
    @mock.patch("zvmsdk.database.FCPDbOperator.assign")
    @mock.patch("zvmsdk.database.FCPDbOperator.get_fcp_pair")
    @mock.patch("zvmsdk.database.FCPDbOperator."
                "get_allocated_fcps_from_assigner")
    def test_get_available_fcp_reserve_true(self, get_allocated,
                                            get_fcp_pair, assign,
                                            get_path_count):
        """test reserve == True"""
        base.set_conf('volume', 'get_fcp_pair_with_same_index', 0)
        # case1: get_allocated return []
        get_allocated.return_value = []
        get_fcp_pair.return_value = ['1234', '5678']
        expected = ['1234', '5678']
        result = self.fcpops.get_available_fcp('user1', True)
        assign.assert_has_calls([mock.call('1234', 'USER1',
                                           update_connections=False),
                                 mock.call('5678', 'USER1',
                                           update_connections=False)])
        self.assertEqual(expected, result)
        # case2: get_allocated return ['c83c', 'c83d']
        get_allocated.return_value = [('c83c', 'user1', 0, 0, 0, ''),
                                      ('c83d', 'user1', 0, 0, 0, '')]
        get_path_count.return_value = 2
        result = self.fcpops.get_available_fcp('user1', True)
        expected = ['c83c', 'c83d']
        self.assertEqual(expected, result)

    def test_get_fcp_dict_in_fcp_list(self):

        fcp_list = "1a01-1a03,1a06;1b01,1b03-1b05"
        expected_fcp_dict = {
            '1a01': 0, '1a02': 0, '1a03': 0, '1a06': 0,
            '1b01': 1, '1b03': 1, '1b04': 1, '1b05': 1,
        }
        fcp_dict = self.fcpops.get_fcp_dict_in_fcp_list(fcp_list)
        self.assertEqual(fcp_dict, expected_fcp_dict)

    def test_get_fcp_dict_in_db(self):

        expected_fcp_dict = {
            '1a01': ('1a01', '', 1, 1, 0, '', '20076D8500005182',
                     '20076D8500005181'),
            '1a02': ('1a02', '', 2, 1, 0, '', '', ''),
            '1b01': ('1b01', '', 1, 1, 1, '', '', ''),
            '1b03': ('1b03', '', 0, 0, 1, '', '', '')
        }
        try:
            self.db_op.new('1a01', 0)
            self.db_op.new('1a02', 0)
            self.db_op.new('1b01', 1)
            self.db_op.new('1b03', 1)
            self.db_op.increase_usage('1a01')
            self.db_op.reserve('1a01')
            self.db_op.increase_usage('1a02')
            self.db_op.increase_usage('1a02')
            self.db_op.reserve('1a02')
            self.db_op.increase_usage('1b01')
            self.db_op.reserve('1b01')
            self.db_op.update_wwpns_of_fcp('1a01', '20076D8500005182',
                                           '20076D8500005181')
            fcp_dict = self.fcpops.get_fcp_dict_in_db()
            self.assertEqual(fcp_dict, expected_fcp_dict)
        finally:
            self.db_op.delete('1a01')
            self.db_op.delete('1a02')
            self.db_op.delete('1b01')
            self.db_op.delete('1b03')

    @mock.patch("zvmsdk.utils.get_smt_userid", mock.Mock())
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_get_fcp_dict_in_zvm(self, mock_zvm_fcp_info):

        raw_fcp_info_from_zvm = [
            'opnstk1: FCP device number: 1A01',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: 20076D8500005182',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: NONE',
            'opnstk1: FCP device number: 1B03',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: ',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005185',
            'Owner: UNIT0001']
        mock_zvm_fcp_info.return_value = raw_fcp_info_from_zvm
        expected_fcp_dict_keys = {
            '1a01', '1b03'}
        fcp_dict = self.fcpops.get_fcp_dict_in_zvm()
        self.assertEqual(expected_fcp_dict_keys, set(fcp_dict.keys()))
        self.assertTrue(
            all([isinstance(v, volumeop.FCP)
                for v in list(fcp_dict.values())]))

    @mock.patch("zvmsdk.database.FCPDbOperator.new")
    @mock.patch("zvmsdk.database.FCPDbOperator.delete")
    @mock.patch("zvmsdk.database.FCPDbOperator.update_path_of_fcp")
    @mock.patch("zvmsdk.volumeop.FCPManager.get_fcp_dict_in_fcp_list")
    @mock.patch("zvmsdk.volumeop.FCPManager.get_fcp_dict_in_db")
    def test_sync_db_with_fcp_list(self,
                                   fcp_dict_in_db, fcp_dict_in_fcp_list,
                                   fcp_update_path, fcp_delete, fcp_new):

        fcp_dict_in_db.return_value = {
            # inter_set:
            '1a01': ('1a01', '', 1, 1, 0, ''),
            '1a02': ('1a02', '', 2, 1, 2, ''),
            '1a03': ('1a03', '', 2, 1, 3, ''),
            # del_fcp_set
            '1b05': ('1a05', '', 0, 1, 3, ''),
            '1b06': ('1a06', '', 1, 1, 3, ''),
            '1b01': ('1b01', '', 0, 0, 2, ''),
            '1b03': ('1b03', '', 0, 0, 1, '')
        }
        fcp_dict_in_fcp_list.return_value = {
            # inter_set:
            '1a01': 0,
            '1a02': 3,
            '1a03': 2,
            # add_fcp_set
            '1a04': 0,
            '1b04': 1,
        }
        self.fcpops._sync_db_with_fcp_list()
        # Update FCP path if path changed
        expected_calls = [call('1a02', 3), call('1a03', 2)]
        fcp_update_path.call_count == 2
        fcp_update_path.assert_has_calls(expected_calls, any_order=True)
        # Delete FCP from DB if connections=0 and reserve=0
        expected_calls = [call('1b01'), call('1b03')]
        fcp_delete.call_count == 2
        fcp_delete.assert_has_calls(expected_calls, any_order=True)
        # Add new FCP into DB
        expected_calls = [call('1a04', 0), call('1b04', 1)]
        fcp_new.call_count == 2
        fcp_new.assert_has_calls(expected_calls, any_order=True)

    @mock.patch("zvmsdk.utils.get_smt_userid", Mock())
    @mock.patch("zvmsdk.database.FCPDbOperator.update_wwpns_of_fcp")
    @mock.patch("zvmsdk.database.FCPDbOperator.update_comment_of_fcp")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.volumeop.FCPManager.get_fcp_dict_in_db")
    def test_sync_db_with_zvm(self, fcp_dict_in_db,
                              mock_zvm_fcp_info, fcp_update_comment,
                              fcp_update_wwpns):

        fcp_dict_in_db.return_value = {
            # inter_set:
            '1a01': ('1a01', '', 1, 1, 0, '', '20076D8500005182',
                     '20076D8500005181'),
            '1a02': ('1a02', '', 2, 1, 2, '', None, None),
            '1a03': ('1a03', '', 2, 1, 3, '', None, None),
            # del_fcp_set
            '1b05': ('1a05', '', 0, 1, 3, '', None, None),
            '1b06': ('1a06', '', 1, 1, 3, '', '20076D8500005187',
                     '20076D8500005185'),
            '1b01': ('1b01', '', 0, 0, 2, '', None, None),
            '1b03': ('1b03', '', 0, 0, 1, '', None, None)
        }
        raw_fcp_info_from_zvm = [
            'opnstk1: FCP device number: 1A01',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: 20076D8500005182',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: NONE',
            'opnstk1: FCP device number: 1A02',
            'opnstk1:   Status: Offline',
            'opnstk1:   NPIV world wide port number: 20076D8500005183',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005185',
            'Owner: NONE',
            'opnstk1: FCP device number: 1A03',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: 20076D8500005184',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: UNIT0001',
            'opnstk1: FCP device number: 1B03',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: 20076D8500005185',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005185',
            'Owner: UNIT0001',
            'opnstk1: FCP device number: 1B01',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: 20076D8500005186',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: NONE',
            'opnstk1: FCP device number: 1B06',
            'opnstk1:   Status: Offline',
            'opnstk1:   NPIV world wide port number: 20076D8500005187',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005185',
            'Owner: UNIT0002'
        ]
        mock_zvm_fcp_info.return_value = raw_fcp_info_from_zvm
        self.fcpops._sync_db_with_zvm()
        # Update FCP path if path changed
        expected_calls = [
            # Free FCP
            call('1a01', {'state': 'free', 'owner': 'NONE'}),
            call('1b01', {'state': 'free', 'owner': 'NONE'}),
            # Active FCP
            call('1a03', {'state': 'active', 'owner': 'UNIT0001'}),
            call('1b03', {'state': 'active', 'owner': 'UNIT0001'}),
            # Offline FCP
            call('1a02', {'state': 'offline', 'owner': 'NONE'}),
            call('1b06', {'state': 'offline', 'owner': 'UNIT0002'}),
            # NotFound FCP
            call('1b05', {'state': 'notfound'})
        ]
        fcp_update_comment.call_count == 7
        fcp_update_comment.assert_has_calls(expected_calls, any_order=True)
        # wwpns of 1a01 and 1b05 was set and 1b05 not exist in zvm
        expected_wwpns_calls = [
            # Free FCP
            call('1b01', '20076d8500005186', '20076d8500005181'),
            # Active FCP
            call('1a03', '20076d8500005184', '20076d8500005181'),
            call('1b03', '20076d8500005185', '20076d8500005185'),
            # Offline FCP
            call('1a02', '20076d8500005183', '20076d8500005185'),
        ]
        fcp_update_wwpns.call_count == 6
        fcp_update_wwpns.assert_has_calls(expected_wwpns_calls,
                                          any_order=True)


class TestFCPVolumeManager(base.SDKTestCase):

    @classmethod
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUpClass(cls):
        super(TestFCPVolumeManager, cls).setUpClass()
        cls.volumeops = volumeop.FCPVolumeManager()
        cls.db_op = database.FCPDbOperator()

    # tearDownClass deleted to work around bug of 'no such table:fcp'

    @mock.patch("zvmsdk.utils.get_lpar_name")
    def test_get_volume_connector(self, get_lpar_name):
        get_lpar_name.return_value = "fakehost"
        base.set_conf('volume', 'fcp_list', 'b83c')
        # assign FCP
        self.db_op.new('b83c', 0)
        # set connections to 1 and assigner_id to b83c
        self.db_op.assign('b83c', 'fakeuser')
        # set reserved to 1
        self.db_op.reserve('b83c')
        # set wwpns value
        self.db_op.update_wwpns_of_fcp('b83c', '2007123400001234',
                                       '20076d8500005181')

        try:
            connections = self.volumeops.get_volume_connector('fakeuser',
                                                              False)
            expected = {'zvm_fcp': ['b83c'],
                        'wwpns': ['2007123400001234'],
                        'phy_to_virt_initiators': {'2007123400001234':
                            '20076d8500005181'},
                        'host': 'fakehost_fakeuser',
                        'fcp_paths': 1}
            self.assertEqual(expected, connections)

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'fakeuser', 1, 1, 0, u'',
                         '2007123400001234', '20076d8500005181')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('b83c')

    @mock.patch("zvmsdk.smtclient.SMTClient.volume_refresh_bootmap")
    def test_volume_refresh_bootmap(self, mock_volume_refresh_bootmap):
        fcpchannels = ['5d71']
        wwpns = ['5005076802100c1b', '5005076802200c1b']
        lun = '0000000000000000'
        res = self.volumeops.volume_refresh_bootmap(fcpchannels, wwpns, lun)
        mock_volume_refresh_bootmap.assert_has_calls(res)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    def test_attach(self, mock_dedicate, mock_add_disk, mock_check,
                    mock_fcp_info):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'false',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['c123', 'd123'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: C123',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        self.db_op = database.FCPDbOperator()
        wwpns = ['20076d8500005182', '20076d8500005183']
        self.db_op.delete('c123')
        self.db_op.delete('d123')
        self.db_op.new('c123', 0)
        self.db_op.new('d123', 1)

        try:
            self.volumeops.attach(connection_info)
            mock_dedicate.assert_has_calls([mock.call('c123', 'USER1'),
                                            mock.call('d123', 'USER1')])
            mock_add_disk.assert_has_calls([mock.call(['c123', 'd123'],
                                                      'USER1', wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz')])
        finally:
            self.db_op.delete('c123')
            self.db_op.delete('d123')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    def test_root_volume_attach(self, mock_dedicate, mock_add_disk, mock_check,
                                mock_fcp_info):

        connection_info = {'platform': 's390x',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'false',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['c123', 'd123'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1',
                           'is_root_volume': True}
        fcp_list = ['opnstk1: FCP device number: C123',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: 20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        base.set_conf('volume', 'fcp_list', 'c123;d123')
        # base.set_conf('volume', 'fcp_list', 'd123')
        self.db_op = database.FCPDbOperator()
        self.db_op.new('c123', 0)
        self.db_op.new('d123', 1)

        try:
            self.volumeops.attach(connection_info)
            self.assertFalse(mock_dedicate.called)
            self.assertFalse(mock_add_disk.called)
        finally:
            self.db_op.delete('c123')
            self.db_op.delete('d123')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    def test_attach_no_dedicate(self, mock_dedicate, mock_add_disk,
                                mock_check, mock_fcp_info):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'false',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['c123', 'd123'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: C123',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        wwpns = ['20076d8500005182', '20076d8500005183']
        self.db_op = database.FCPDbOperator()
        self.db_op.new('c123', 0)
        # assign will set connections to 1
        self.db_op.assign('c123', 'USER1')

        self.db_op.new('d123', 1)
        self.db_op.assign('d123', 'USER1')

        # set connections to 2
        self.db_op.increase_usage('c123')
        self.db_op.increase_usage('d123')

        try:
            self.volumeops.attach(connection_info)
            self.assertFalse(mock_dedicate.called)
            mock_add_disk.assert_has_calls([mock.call(['c123', 'd123'],
                                                      'USER1', wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz')])

        finally:
            self.db_op.delete('c123')
            self.db_op.delete('d123')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._rollback_dedicated_fcp")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    @mock.patch("zvmsdk.volumeop.FCPManager.add_fcp_for_assigner")
    def test_attach_rollback(self, mock_fcp_assigner,
                             mock_dedicate, mock_rollback,
                             mock_check, mock_fcp_info):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'false',
                           'target_wwpn': ['20076D8500005182'],
                           'target_lun': '2222',
                           'zvm_fcp': ['e83c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: E83C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        mock_fcp_assigner.return_value = True
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        mock_dedicate.side_effect = exception.SDKSMTRequestFailed(
            results, 'fake error')
        self.assertRaises(exception.SDKBaseException,
                          self.volumeops.attach,
                          connection_info)
        calls = [mock.call(['e83c'], 'USER1', all_fcp_list=['e83c'])]
        mock_rollback.assert_has_calls(calls)

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager.get_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disks")
    @mock.patch("zvmsdk.volumeop.FCPManager.increase_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPManager.decrease_fcp_usage")
    def test_detach_rollback(self, mock_decrease, mock_remove_disk,
                             mock_increase, mock_add_disk, mock_check,
                             mock_fcp_info, get_fcp_usage):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'False',
                           'target_wwpn': ['20076D8500005182'],
                           'target_lun': '2222',
                           'zvm_fcp': ['f83c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: F83C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE']
        get_fcp_usage.return_value = ('user1', 0, 0)
        mock_fcp_info.return_value = fcp_list
        # this return does not matter
        mock_check.return_value = True
        mock_decrease.return_value = 0
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        mock_remove_disk.side_effect = exception.SDKSMTRequestFailed(
            results, 'fake error')
        self.assertRaises(exception.SDKBaseException,
                          self.volumeops.detach,
                          connection_info)
        # because no fcp dedicated
        mock_add_disk.assert_called_once_with(['f83c'], 'USER1',
                                              ['20076d8500005182'], '2222',
                                              False, 'rhel7', '/dev/sdz')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager.get_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    def test_detach_need_rollback(self, mock_remove_disk, mock_add_disk,
                                  mock_check, mock_fcp_info, get_fcp_usage):
        """Test need_rollback dict was set correctly.
        """
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'False',
                           'target_wwpn': ['20076D8500005181',
                                           '20076D8500005182'],
                           'target_lun': '2222',
                           'zvm_fcp': ['f83c', 'f84c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: F83C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005181',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: F84C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005182',
                    'Owner: NONE']
        # increase connections of f83c to 1
        # left connections of f84c to 0
        self.db_op.new('f83c', 0)
        self.db_op.new('f84c', 1)
        self.db_op.increase_usage('f83c')
        try:
            get_fcp_usage.return_value = ('use1', 0, 0)
            mock_fcp_info.return_value = fcp_list
            # this return does not matter
            mock_check.return_value = True
            results = {'rs': 0, 'errno': 0, 'strError': '',
                       'overallRC': 1, 'logEntries': [], 'rc': 0,
                       'response': ['fake response']}
            mock_remove_disk.side_effect = exception.SDKSMTRequestFailed(
                results, 'fake error')
            self.assertRaises(exception.SDKBaseException,
                              self.volumeops.detach,
                              connection_info)
            # get_fcp_usage should only called once on f83c
            get_fcp_usage.assert_called_once_with('f83c')
            # because no fcp dedicated
            mock_add_disk.assert_called_once_with(['f83c', 'f84c'], 'USER1',
                                                  ['20076d8500005181',
                                                   '20076d8500005182'], '2222',
                                                  False, 'rhel7', '/dev/sdz')
        finally:
            self.db_op.delete('f83c')
            self.db_op.delete('f84c')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach(self, mock_undedicate, mock_remove_disk, mock_check,
                    mock_fcp_info):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'True',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['183c', '283c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        fcp_list = ['opnstk1: FCP device number: 183C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: 20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: 283C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        wwpns = ['20076d8500005182', '20076d8500005183']
        self.db_op = database.FCPDbOperator()
        self.db_op.new('183c', 0)
        self.db_op.assign('183c', 'USER1')

        self.db_op.new('283c', 1)
        # assign will set the connections to 1
        self.db_op.assign('283c', 'USER1')

        try:
            self.volumeops.detach(connection_info)
            mock_undedicate.assert_has_calls([mock.call('183c', 'USER1'),
                                              mock.call('283c', 'USER1')])
            mock_remove_disk.assert_has_calls([mock.call(['183c', '283c'],
                                                         'USER1', wwpns,
                                                         '2222', True, 'rhel7',
                                                         '/dev/sdz', 0)])
            res1 = self.db_op.is_reserved('183c')
            res2 = self.db_op.is_reserved('283c')
            self.assertFalse(res1)
            self.assertFalse(res2)
        finally:
            self.db_op.delete('183c')
            self.db_op.delete('283c')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_root_volume_detach(self, mock_undedicate, mock_remove_disk,
                                mock_check, mock_fcp_info):

        connection_info = {'platform': 's390x',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'True',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['183c', '283c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1',
                           'is_root_volume': True}
        fcp_list = ['opnstk1: FCP device number: 183C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: 20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: 283C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        base.set_conf('volume', 'fcp_list', '183c')
        base.set_conf('volume', 'fcp_list', '283c')
        self.db_op = database.FCPDbOperator()
        self.db_op.new('183c', 0)
        self.db_op.assign('183c', 'USER1')

        self.db_op.new('283c', 1)
        # assign will set the connections to 1
        self.db_op.assign('283c', 'USER1')

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            self.assertFalse(mock_remove_disk.called)
        finally:
            self.db_op.delete('183c')
            self.db_op.delete('283c')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_update_connections_only_detach(self, mock_undedicate,
            mock_remove_disk, mock_check, mock_fcp_info):

        connection_info = {'platform': 's390x',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'True',
                           'target_wwpn': ['20076D8500005182',
                                           '20076D8500005183'],
                           'target_lun': '2222',
                           'zvm_fcp': ['183c', '283c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1',
                           'update_connections_only': True}
        fcp_list = ['opnstk1: FCP device number: 183C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: 20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'Owner: NONE',
                    'opnstk1: FCP device number: 283C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'Owner: UNIT0001']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        base.set_conf('volume', 'fcp_list', '183c')
        base.set_conf('volume', 'fcp_list', '283c')
        self.db_op = database.FCPDbOperator()
        self.db_op.new('183c', 0)
        self.db_op.assign('183c', 'USER1')

        self.db_op.new('283c', 1)
        # assign will set the connections to 1
        self.db_op.assign('283c', 'USER1')

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            self.assertFalse(mock_remove_disk.called)
        finally:
            self.db_op.delete('183c')
            self.db_op.delete('283c')

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach_no_undedicate(self, mock_undedicate, mock_remove_disk,
                                  mock_check):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': 'False',
                           'target_wwpn': ['1111'],
                           'target_lun': '2222',
                           'zvm_fcp': ['283c'],
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        mock_check.return_value = True
        self.db_op = database.FCPDbOperator()
        self.db_op.new('283c', 0)
        self.db_op.assign('283c', 'user1')
        self.db_op.increase_usage('283c')

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            mock_remove_disk.assert_called_once_with(['283c'], 'USER1',
                                                     ['1111'], '2222',
                                                     False, 'rhel7',
                                                     '/dev/sdz', 1)
        finally:
            self.db_op.delete('283c')

    def test_get_all_fcp_usage_empty(self):
        empty_usage0 = {}
        empty_usage1 = {'raw': {}}
        empty_usage2 = {'statistics': {}}
        ret0 = self.volumeops.get_all_fcp_usage(statistics=False)
        ret1 = self.volumeops.get_all_fcp_usage('dummy')
        ret2 = self.volumeops.get_all_fcp_usage()
        ret3 = self.volumeops.get_all_fcp_usage('dummy', raw=False)
        self.assertDictEqual(ret0, empty_usage0)
        self.assertDictEqual(ret1, empty_usage1)
        self.assertDictEqual(ret2, empty_usage2)
        self.assertDictEqual(ret3, empty_usage1)

    def test_get_all_fcp_usage_raw(self):
        """Test the raw usage will be set correctly."""
        self.db_op = database.FCPDbOperator()
        self.db_op.new('283c', 0)
        self.db_op.new('383c', 0)
        self.db_op.new('483c', 1)
        # set reserved to 1
        self.db_op.reserve('283c')
        # set connections to 1 and set userid
        self.db_op.assign('283c', 'user1')
        # set connections to 2
        self.db_op.increase_usage('283c')
        try:
            ret = self.volumeops.get_all_fcp_usage(raw=True)
            # case 1: specify raw=true and let statistics keep default value
            raw_usage = ret['raw']
            statistic_usage = ret['statistics']
            # there are 2 FCPs on path 0
            self.assertEqual(len(raw_usage[0]), 2)
            # there is 1 FCP on path 1
            self.assertEqual(len(raw_usage[1]), 1)
            # path 0 status verify
            self.assertTrue('283c' in raw_usage[0][0] or
                            '383c' in raw_usage[0][1])
            # path 1 status verify
            self.assertTrue('483c' in raw_usage[1][0])
            expected_statistics = {0: {'available': [],
                                       'allocated': ['283c'],
                                       'unallocated_but_active': [],
                                       'allocated_but_free': [],
                                       'notfound': [],
                                       'offline': []},
                                   1: {'available': [],
                                       'allocated': [],
                                       'unallocated_but_active': [],
                                       'allocated_but_free': [],
                                       'notfound': [],
                                       'offline': []}}
            self.assertDictEqual(expected_statistics, statistic_usage)
            # case 2: userid was specified
            # in this case, the raw should set to true and
            # statistics set to false
            ret = self.volumeops.get_all_fcp_usage(
                    assigner_id='user1')
            raw_usage = ret['raw']
            self.assertNotIn('statistics', ret)
            self.assertEqual(len(ret), 1)
            self.assertTrue('283c' in raw_usage[0][0])
        finally:
            self.db_op.delete('283c')
            self.db_op.delete('383c')
            self.db_op.delete('483c')

    def test_get_all_fcp_usage_statistics(self):
        """Test the raw usage will be set correctly."""
        self.db_op = database.FCPDbOperator()
        self.db_op.new('183c', 0)
        self.db_op.new('283c', 0)
        self.db_op.new('383c', 0)
        self.db_op.new('483c', 0)
        self.db_op.new('583c', 1)
        self.db_op.new('683c', 1)
        self.db_op.new('783c', 1)
        self.db_op.new('883c', 1)
        comment_state_free = {'state': 'free'}
        comment_owner_active = {'owner': 'fakeuser', 'state': 'active'}
        comment_state_offline = {'state': 'offline'}
        comment_state_notfound = {'state': 'notfound'}
        try:
            # case A: (reserve = 0 and conn = 0 and state = free)
            self.db_op.update_comment_of_fcp('183c', comment_state_free)
            self.db_op.update_comment_of_fcp('183c', comment_state_free)
            # B: (reserve = 1 and conn != 0)
            self.db_op.reserve('283c')
            self.db_op.increase_usage('283c')
            # C: (reserve = 1, conn = 0)
            self.db_op.reserve('383c')
            # D: (reserve = 0 and conn != 0)
            self.db_op.increase_usage('483c')
            # E: (reserve = 0, conn = 0, state = active)
            self.db_op.update_comment_of_fcp('583c', comment_owner_active)
            # F: (conn != 0, state = free)
            self.db_op.increase_usage('683c')
            self.db_op.update_comment_of_fcp('683c', comment_state_free)
            # G: (state = notfound)
            self.db_op.update_comment_of_fcp('783c', comment_state_notfound)
            # H: (state = offline)
            self.db_op.update_comment_of_fcp('883c', comment_state_offline)
            # extra case 1: B + G
            self.db_op.update_comment_of_fcp('283c', comment_state_notfound)
            # extra case 2: C + H
            self.db_op.update_comment_of_fcp('383c', comment_state_offline)
            # extra case 3: D + G
            self.db_op.update_comment_of_fcp('483c', comment_state_notfound)
            ret = self.volumeops.get_all_fcp_usage(statistics=True, raw=False)
            # raw data should not in ret value
            self.assertNotIn('raw', ret)
            statistic_usage = ret['statistics']
            expected_usage = {0: {"available": ['183c'],
                                  "allocated": ['283c'],
                                  "unallocated_but_active": [],
                                  "allocated_but_free": [],
                                  "notfound": ['283c', '483c'],
                                  "offline": ['383c']},
                              1: {"available": [],
                                  "allocated": [],
                                  "unallocated_but_active": [
                                      ('583c', 'fakeuser')],
                                  "allocated_but_free": ['683c'],
                                  "notfound": ['783c'],
                                  "offline": ['883c']}}
            # path 1 status
            self.assertIn('183c', statistic_usage[0]['available'])
            self.assertIn('283c', statistic_usage[0]['allocated'])
            self.assertEqual([], statistic_usage[0]['unallocated_but_active'])
            self.assertEqual([], statistic_usage[0]['allocated_but_free'])
            self.assertIn('283c', statistic_usage[0]['notfound'])
            self.assertIn('483c', statistic_usage[0]['notfound'])
            self.assertIn('383c', statistic_usage[0]['offline'])
            # path 2 status
            self.assertEqual([], statistic_usage[1]['available'])
            self.assertEqual([], statistic_usage[1]['allocated'])
            self.assertIn(('583c', 'fakeuser'),
                          statistic_usage[1]['unallocated_but_active'])
            self.assertIn('683c', statistic_usage[1]['allocated_but_free'])
            self.assertIn('783c', statistic_usage[1]['notfound'])
            self.assertIn('883c', statistic_usage[1]['offline'])
            # overall status
            self.assertDictEqual(statistic_usage, expected_usage)
        finally:
            self.db_op.delete('183c')
            self.db_op.delete('283c')
            self.db_op.delete('383c')
            self.db_op.delete('483c')
            self.db_op.delete('583c')
            self.db_op.delete('683c')
            self.db_op.delete('783c')
            self.db_op.delete('883c')

    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm")
    def test_get_all_fcp_usage_sync_with_zvm(self, mock_sync_db_with_zvm):
        self.volumeops.get_all_fcp_usage(sync_with_zvm=True)
        mock_sync_db_with_zvm.assert_called_once()

    def test_get_fcp_usage(self):
        self.db_op = database.FCPDbOperator()
        self.db_op.new('283c', 0)
        # set reserved to 1
        self.db_op.reserve('283c')
        self.db_op.assign('283c', 'user1')
        # set connections to 2
        self.db_op.increase_usage('283c')
        try:
            userid, reserved, conns = self.volumeops.get_fcp_usage('283c')
            self.assertEqual(userid, 'user1')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 2)
        finally:
            self.db_op.delete('283c')

    def test_set_fcp_usage(self):
        self.db_op = database.FCPDbOperator()
        self.db_op.new('283c', 0)
        # set reserved to 1
        self.db_op.reserve('283c')
        self.db_op.assign('283c', 'user1')
        # set connections to 2
        self.db_op.increase_usage('283c')
        try:
            # change reserved to 0 and connections to 3
            self.volumeops.set_fcp_usage('283c', 'user2', 0, 3)
            userid, reserved, conns = self.volumeops.get_fcp_usage('283c')
            self.assertEqual(userid, 'user2')
            self.assertEqual(reserved, 0)
            self.assertEqual(conns, 3)
        finally:
            self.db_op.delete('283c')
