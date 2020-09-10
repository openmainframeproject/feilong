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
import shutil

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

    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd")
    @mock.patch.object(dist.rhel7, "create_active_net_interf_cmd")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "configure_volume_attach")
    @mock.patch("zvmsdk.vmops.VMOps.is_reachable")
    def test_config_attach_reachable(self, is_reachable, config_attach,
                                     restart_zvmguestconfigure, execute_cmd,
                                     get_dist):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        new = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'

        get_dist.return_value = dist.rhel7
        config_attach.return_value = None
        is_reachable.return_value = True
        active_cmds = 'systemctl start zvmguestconfigure.service'
        restart_zvmguestconfigure.return_value = active_cmds
        need_restart = True
        self.configurator.config_attach(fcp, assigner_id, target_wwpns,
                                        target_lun, multipath, os_version,
                                        mount_point, new, need_restart)
        get_dist.assert_called_once_with(os_version)
        restart_zvmguestconfigure.assert_called_once_with()
        execute_cmd.assert_called_once_with(assigner_id,
                                            active_cmds)

    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI."
                "configure_volume_attach")
    @mock.patch("zvmsdk.vmops.VMOps.is_reachable")
    def test_config_attach_not_reachable(self, is_reachable, config_attach,
                                         get_dist):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        new = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        is_reachable.return_value = False
        get_dist.return_value = dist.rhel7
        config_attach.return_value = None
        need_restart = False

        self.configurator.config_attach(fcp, assigner_id, target_wwpns,
                                        target_lun, multipath, os_version,
                                        mount_point, new, need_restart)
        get_dist.assert_called_once_with(os_version)

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
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpns = ['1111', '1112']
        target_lun = '2222'
        multipath = True
        new = True
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        config_file = '/tm/userid1xxx/attach_volume.sh'
        config_file_path = '/tm/userid1xxx/'
        linuxdist = dist.rhel7()
        get_dist.return_value = linuxdist
        create_file.return_value = (config_file, config_file_path)
        rmtree.return_value = None
        self.configurator.configure_volume_attach(fcp, assigner_id,
                                                  target_wwpns, target_lun,
                                                  multipath, os_version,
                                                  mount_point, linuxdist,
                                                  new)
        get_attach_cmds.assert_called_once_with(fcp, target_wwpns, target_lun,
                                                multipath, mount_point, True)
        punch_file.assert_called_once_with(assigner_id, config_file, 'X')

    @mock.patch("zvmsdk.smtclient.SMTClient.punch_file")
    @mock.patch.object(shutil, "rmtree")
    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI._create_file")
    @mock.patch("zvmsdk.dist.LinuxDistManager.get_linux_dist")
    @mock.patch("zvmsdk.dist.rhel7.get_volume_detach_configuration_cmds")
    def test_config_detach_active(self, get_detach_cmds, get_dist,
                                  create_file, rmtree, punch_file):
        fcp = 'bfc3'
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
        self.configurator.configure_volume_detach(fcp, assigner_id,
                                                  target_wwpns, target_lun,
                                                  multipath, os_version,
                                                  mount_point, linuxdist,
                                                  connections)
        get_detach_cmds.assert_called_once_with(fcp, target_wwpns, target_lun,
                                                multipath, mount_point,
                                                connections)
        punch_file.assert_called_once_with(assigner_id, config_file, 'X')


class TestFCP(base.SDKTestCase):

    def test_parse_normal(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Free',
                'opnstk1:   NPIV world wide port number: NONE',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertIsNone(fcp._npiv_port)
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())

    def test_parse_npiv(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Free',
                'opnstk1:   NPIV world wide port number: 20076D8500005182',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertEqual('20076D8500005182', fcp._npiv_port.upper())
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())


class TestFCPManager(base.SDKTestCase):

    @classmethod
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

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_init_fcp_pool(self, mock_get):
        fcp_list = ['opnstk1: FCP device number: B83D',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'opnstk1: FCP device number: B83E',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']

        mock_get.return_value = fcp_list
        fake_userid = 'fakeuser'

        self.fcpops._init_fcp_pool('b83d-b83f', fake_userid)
        self.assertEqual(2, len(self.fcpops._fcp_pool))
        self.assertTrue('b83d' in self.fcpops._fcp_pool)
        self.assertTrue('b83e' in self.fcpops._fcp_pool)
        # note b83f is not in fcp_list
        self.assertFalse('b83f' in self.fcpops._fcp_pool)

        npiv = self.fcpops._fcp_pool['b83d']._npiv_port.upper()
        physical = self.fcpops._fcp_pool['b83d']._physical_port.upper()
        self.assertEqual('20076D8500005182', npiv)
        self.assertEqual('20076D8500005181', physical)
        self.assertEqual('59', self.fcpops._fcp_pool['b83d']._chpid.upper())

        npiv = self.fcpops._fcp_pool['b83e']._npiv_port.upper()
        physical = self.fcpops._fcp_pool['b83e']._physical_port.upper()
        self.assertEqual('20076D8500005183', npiv)
        self.assertEqual('20076D8500005185', physical)
        self.assertEqual('50', self.fcpops._fcp_pool['b83e']._chpid.upper())

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.volumeop.FCPManager._report_orphan_fcp")
    @mock.patch("zvmsdk.volumeop.FCPManager._add_fcp")
    def test_sync_db_fcp_list(self, mock_add, mock_report, mock_get):

        fcp_list = ['opnstk1: FCP device number: B83D',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005181',
                    'opnstk1: FCP device number: B83E',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'opnstk1: FCP device number: B83F',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'opnstk1: FCP device number: C83D',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'opnstk1: FCP device number: C83E',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185',
                    'opnstk1: FCP device number: C83F',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005187',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005188']

        mock_get.return_value = fcp_list
        fake_userid = 'fakeuser'
        self.fcpops._init_fcp_pool('b83d-b83f;c83d-c83f', fake_userid)

        self.db_op.new('b83c', 0)
        self.db_op.new('b83d', 0)
        self.db_op.new('b83e', 0)
        self.db_op.new('c83d', 1)
        self.db_op.new('c83e', 1)
        self.db_op.new('c83f', 1)

        try:
            self.fcpops._sync_db_fcp_list()
            # b83c is not in fcp_list
            mock_report.assert_called_once_with('b83c')
            # b83f is not in DB
            mock_add.assert_called_once_with('b83f', 0)
        finally:
            self.db_op.delete('b83c')
            self.db_op.delete('b83d')
            self.db_op.delete('b83e')
            self.db_op.delete('b83f')
            self.db_op.delete('c83d')
            self.db_op.delete('c83e')
            self.db_op.delete('c83f')

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
            expected = [(u'a83c', u'dummy1', 1, 0, 0, u'')]
            self.assertEqual(expected, fcp_list)

            fcp_list = self.db_op.get_from_fcp('a83d')
            expected = [(u'a83d', u'dummy2', 1, 0, 0, u'')]
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
            expected = [(u'b83c', u'', 0, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            fcp_list = self.db_op.get_from_fcp('b83d')
            expected = [(u'b83d', u'', 0, 1, 0, u'')]
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
            expected = [(u'c83c', u'user1', 1, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            # After usage, we need find c83d now
            fcp2 = self.fcpops.find_and_reserve_fcp('user2')
            self.assertEqual('c83d', fcp2)
            fcp_list = self.db_op.get_from_fcp('c83d')
            expected = [(u'c83d', u'', 0, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.increase_fcp_usage('c83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [(u'c83c', u'user1', 2, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('c83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [(u'c83c', u'user1', 1, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('c83c')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [(u'c83c', u'user1', 0, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)

            # unreserve makes this fcp free
            self.fcpops.unreserve_fcp('c83c')
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [(u'c83c', u'user1', 0, 0, 0, u'')]
            self.assertEqual(expected, fcp_list)

            fcp3 = self.fcpops.find_and_reserve_fcp('user3')
            self.assertEqual('c83c', fcp3)
            fcp_list = self.db_op.get_from_fcp('c83c')
            expected = [(u'c83c', u'user1', 0, 1, 0, u'')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('c83c')
            self.db_op.delete('c83d')

    def test_find_and_reserve_fcp_exception(self):
        # no FCP at all

        # find FCP for user and FCP not exist, should alloca
        fcp = self.fcpops.find_and_reserve_fcp('user1')
        self.assertIsNone(fcp)

    def test_get_available_fcp(self):
        self.db_op.new('c83c', 0)
        self.db_op.new('c83d', 1)

        try:
            result = self.fcpops.get_available_fcp('user1')
            expected = ['c83c', 'c83d']
            self.assertEqual(expected, result)
        finally:
            self.db_op.delete('c83c')
            self.db_op.delete('c83d')


class TestFCPVolumeManager(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestFCPVolumeManager, cls).setUpClass()
        cls.volumeops = volumeop.FCPVolumeManager()
        cls.db_op = database.FCPDbOperator()

    # tearDownClass deleted to work around bug of 'no such table:fcp'

    @mock.patch("zvmsdk.smtclient.SMTClient.get_host_info")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_get_volume_connector(self, get_fcp_info, get_host_info):
        fcp_info = ['fakehost: FCP device number: B83C',
                    'fakehost:   Status: Free',
                    'fakehost:   NPIV world wide port number: '
                    '2007123400001234',
                    'fakehost:   Channel path ID: 59',
                    'fakehost:   Physical world wide port number: '
                    '20076D8500005181']

        get_fcp_info.return_value = fcp_info
        get_host_info.return_value = {'zvm_host': 'fakehost'}
        base.set_conf('volume', 'fcp_list', 'b83c')
        # assign FCP
        self.db_op.new('b83c', 0)
        self.db_op.assign('b83c', 'fakeuser')

        try:
            connections = self.volumeops.get_volume_connector('fakeuser',
                                                              False)
            expected = {'zvm_fcp': ['b83c'],
                        'wwpns': ['2007123400001234'],
                        'host': 'fakehost'}
            self.assertEqual(expected, connections)

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'fakeuser', 1, 0, 0, u'')]
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
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
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
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']
        mock_fcp_info.return_value = fcp_list
        self.db_op = database.FCPDbOperator()
        wwpns = ['20076D8500005182', '20076D8500005183']
        self.db_op.new('c123', 0)
        self.db_op.new('d123', 1)

        try:
            self.volumeops.attach(connection_info)
            mock_dedicate.assert_has_calls([mock.call('c123', 'USER1'),
                                            mock.call('d123', 'USER1')])
            mock_add_disk.assert_has_calls([mock.call('c123', 'USER1',
                                                      wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz', True, False),
                                            mock.call('d123', 'USER1',
                                                      wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz', True, True)])
        finally:
            self.db_op.delete('c123')
            self.db_op.delete('d123')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
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
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']
        mock_fcp_info.return_value = fcp_list
        base.set_conf('volume', 'fcp_list', 'c123')
        base.set_conf('volume', 'fcp_list', 'd123')
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
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
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
                    'opnstk1: FCP device number: D123',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        wwpns = ['20076D8500005182', '20076D8500005183']
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
            mock_add_disk.assert_has_calls([mock.call('c123', 'USER1',
                                                      wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz', False,
                                                      False),
                                            mock.call('d123', 'USER1',
                                                      wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz', False,
                                                      True)])

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
                    '20076D8500005181']
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
        calls = [mock.call(['e83c'], 'USER1'),
                 mock.call([], 'USER1', all_fcp_list=['e83c'])]
        mock_rollback.assert_has_calls(calls)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
    @mock.patch("zvmsdk.volumeop.FCPManager.increase_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
    @mock.patch("zvmsdk.volumeop.FCPManager.decrease_fcp_usage")
    def test_detach_rollback(self, mock_decrease, mock_remove_disk,
                             mock_increase, mock_add_disk, mock_check,
                             mock_fcp_info):
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
                    '20076D8500005181']
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

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
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
                    'opnstk1: FCP device number: 283C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    '20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        wwpns = ['20076D8500005182', '20076D8500005183']
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
            mock_remove_disk.assert_has_calls([mock.call('183c', 'USER1',
                                                         wwpns,
                                                         '2222', True, 'rhel7',
                                                         '/dev/sdz', 0, False),
                                               mock.call('283c', 'USER1',
                                                         wwpns,
                                                         '2222', True, 'rhel7',
                                                         '/dev/sdz', 0, True)])
            res1 = self.db_op.is_reserved('183c')
            res2 = self.db_op.is_reserved('283c')
            self.assertFalse(res1)
            self.assertFalse(res2)
        finally:
            self.db_op.delete('183c')
            self.db_op.delete('283c')

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
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
                    'opnstk1: FCP device number: 283C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: '
                    '20076D8500005185']
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
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
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
            mock_remove_disk.assert_called_once_with('283c', 'USER1', ['1111'],
                                                     '2222', False, 'rhel7',
                                                     '/dev/sdz', 1, True)
        finally:
            self.db_op.delete('283c')
