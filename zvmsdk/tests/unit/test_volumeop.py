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

from zvmsdk import database
from zvmsdk import exception
from zvmsdk import volumeop
from zvmsdk.tests.unit import base


class TestVolumeConfiguratorAPI(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVolumeConfiguratorAPI, cls).setUpClass()
        cls.configurator = volumeop.VolumeConfiguratorAPI()

    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI.config_attach_active")
    @mock.patch("zvmsdk.vmops.VMOps.is_reachable")
    def test_config_attach_reachable(self, is_reachable, attach_active):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpn = '1111'
        target_lun = '2222'
        multipath = ''
        os_version = 'rhel7'
        mount_point = '/dev/sdz'

        is_reachable.return_value = True

        self.configurator.config_attach(fcp, assigner_id, target_wwpn,
                                        target_lun, multipath, os_version,
                                        mount_point)
        attach_active.assert_called_once_with(fcp, assigner_id, target_wwpn,
                                              target_lun, multipath,
                                              os_version, mount_point)

    @mock.patch("zvmsdk.volumeop.VolumeConfiguratorAPI.config_attach_inactive")
    @mock.patch("zvmsdk.vmops.VMOps.is_reachable")
    def test_config_attach_not_reachable(self, is_reachable, attach_inactive):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpn = '1111'
        target_lun = '2222'
        multipath = ''
        os_version = 'rhel7'
        mount_point = '/dev/sdz'

        is_reachable.return_value = False

        self.configurator.config_attach(fcp, assigner_id, target_wwpn,
                                        target_lun, multipath, os_version,
                                        mount_point)
        attach_inactive.assert_called_once_with(fcp, assigner_id, target_wwpn,
                                              target_lun, multipath,
                                              os_version, mount_point)

    def test_config_force_attach(self):
        pass

    def test_config_force_detach(self):
        pass

    @mock.patch("zvmsdk.dist.LinuxDist.config_volume_attach_active")
    def test_config_attach_active(self, dist_attach_active):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpn = '1111'
        target_lun = '2222'
        multipath = ''
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        self.configurator.config_attach_active(fcp, assigner_id,
                                               target_wwpn, target_lun,
                                               multipath, os_version,
                                               mount_point)
        dist_attach_active.assert_called_once_with(fcp, assigner_id,
                                                   target_wwpn, target_lun,
                                                   multipath, mount_point)

    @mock.patch("zvmsdk.dist.LinuxDist.config_volume_detach_active")
    def test_config_detach_active(self, dist_detach_active):
        fcp = 'bfc3'
        assigner_id = 'userid1'
        target_wwpn = '1111'
        target_lun = '2222'
        multipath = ''
        os_version = 'rhel7'
        mount_point = '/dev/sdz'
        self.configurator.config_detach_active(fcp, assigner_id,
                                               target_wwpn, target_lun,
                                               multipath, os_version,
                                               mount_point)
        dist_detach_active.assert_called_once_with(fcp, assigner_id,
                                                   target_wwpn, target_lun,
                                                   multipath, mount_point)


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
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f14'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_dash(self):
        fcp_list = "1f10-1f14"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f14'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_dash(self):
        fcp_list = "1f10;1f11-1f13;1f17"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f17'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_2dash(self):
        fcp_list = "1f10;1f11-1f13;1f17-1f1a;1f02"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f17',
                        '1f18', '1f19', '1f1a', '1f02'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_init_fcp_pool(self, mock_get):
        fcp_list = ['opnstk1: FCP device number: B83D',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: 20076D8500005182',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: 20076D8500005181',
            'opnstk1: FCP device number: B83E',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: 20076D8500005183',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: 20076D8500005185']

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
            'opnstk1:   NPIV world wide port number: 20076D8500005182',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: 20076D8500005181',
            'opnstk1: FCP device number: B83E',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: 20076D8500005183',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: 20076D8500005185',
            'opnstk1: FCP device number: B83F',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: 20076D8500005187',
            'opnstk1:   Channel path ID: 50',
            'opnstk1:   Physical world wide port number: 20076D8500005188']

        mock_get.return_value = fcp_list
        fake_userid = 'fakeuser'

        self.fcpops._init_fcp_pool('b83d-b83f', fake_userid)

        self.db_op.new('b83c')
        self.db_op.new('b83d')
        self.db_op.new('b83e')

        try:
            self.fcpops._sync_db_fcp_list()
            mock_add.assert_called_once_with('b83f')
            mock_report.assert_called_once_with('b83c')
        finally:
            self.db_op.delete('b83d')
            self.db_op.delete('b83e')
            self.db_op.delete('b83f')
            self.db_op.delete('b83c')

    def test_find_and_reserve_fcp_new(self):
        # create 2 FCP
        self.db_op.new('b83c')
        self.db_op.new('b83d')

        # find FCP for user and FCP not exist, should allocate them
        try:
            fcp1 = self.fcpops.find_and_reserve_fcp('dummy1')
            fcp2 = self.fcpops.find_and_reserve_fcp('dummy2')

            self.assertEqual('b83c', fcp1)
            self.assertEqual('b83d', fcp2)

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'', 0, 1, u'')]
            self.assertEqual(expected, fcp_list)

            fcp_list = self.db_op.get_from_fcp('b83d')
            expected = [(u'b83d', u'', 0, 1, u'')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('b83c')
            self.db_op.delete('b83d')

    def test_find_and_reserve_fcp_old(self):
        self.db_op = database.FCPDbOperator()
        # create 2 FCP
        self.db_op.new('b83c')
        self.db_op.new('b83d')

        # find FCP for user and FCP not exist, should allocate them
        try:
            fcp1 = self.fcpops.find_and_reserve_fcp('user1')
            self.assertEqual('b83c', fcp1)
            self.fcpops.increase_fcp_usage('b83c', 'user1')

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 1, 1, u'')]
            self.assertEqual(expected, fcp_list)

            # After usage, we need find b83d now
            fcp2 = self.fcpops.find_and_reserve_fcp('user2')
            self.assertEqual('b83d', fcp2)
            fcp_list = self.db_op.get_from_fcp('b83d')
            expected = [(u'b83d', u'', 0, 1, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.increase_fcp_usage('b83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 2, 1, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('b83c', 'user1')
            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 1, 1, u'')]
            self.assertEqual(expected, fcp_list)

            self.fcpops.decrease_fcp_usage('b83c')
            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 0, 1, u'')]
            self.assertEqual(expected, fcp_list)

            # unreserve makes this fcp free
            self.fcpops.unreserve_fcp('b83c')
            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 0, 0, u'')]
            self.assertEqual(expected, fcp_list)

            fcp3 = self.fcpops.find_and_reserve_fcp('user3')
            self.assertEqual('b83c', fcp3)
            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'user1', 0, 1, u'')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('b83c')
            self.db_op.delete('b83d')

    def test_find_and_reserve_fcp_exception(self):
        # no FCP at all

        # find FCP for user and FCP not exist, should alloca
        fcp = self.fcpops.find_and_reserve_fcp('user1')
        self.assertIsNone(fcp)


class TestFCPVolumeManager(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestFCPVolumeManager, cls).setUpClass()
        cls.volumeops = volumeop.FCPVolumeManager()
        cls.db_op = database.FCPDbOperator()

    # tearDownClass deleted to work around bug of 'no such table:fcp'

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_get_volume_connector(self, get_fcp_info):
        fcp_info = ['opnstk1: FCP device number: B83C',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: 2007123400001234',
            'opnstk1:   Channel path ID: 59',
            'opnstk1:   Physical world wide port number: 20076D8500005181']

        get_fcp_info.return_value = fcp_info
        base.set_conf('zvm', 'zvm_host', 'fakehost')
        base.set_conf('volume', 'fcp_list', 'b83c')
        # assign FCP
        self.db_op.new('b83c')

        try:
            connections = self.volumeops.get_volume_connector('fakeuser')
            expected = {'zvm_fcp': ['b83c'],
                        'wwpns': ['2007123400001234'],
                        'host': 'fakehost'}
            self.assertEqual(expected, connections)

            fcp_list = self.db_op.get_from_fcp('b83c')
            expected = [(u'b83c', u'', 0, 0, u'')]
            self.assertEqual(expected, fcp_list)
        finally:
            self.db_op.delete('b83c')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    def test_attach(self, mock_dedicate, mock_add_disk):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        self.db_op = database.FCPDbOperator()
        self.db_op.new('b83c')

        try:
            self.volumeops.attach(connection_info)
            mock_dedicate.assert_called_once_with('b83c', 'USER1')
            mock_add_disk.assert_called_once_with('b83c', 'USER1', '1111',
                                                  '2222', False, 'rhel7',
                                                  '/dev/sdz')
        finally:
            self.db_op.delete('b83c')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    def test_attach_no_dedicate(self, mock_dedicate, mock_add_disk):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        self.db_op = database.FCPDbOperator()
        self.db_op.new('b83c')
        self.db_op.assign('b83c', 'user1')
        self.db_op.increase_usage('b83c')

        try:
            self.volumeops.attach(connection_info)
            self.assertFalse(mock_dedicate.called)
            mock_add_disk.assert_called_once_with('b83c', 'USER1', '1111',
                                                  '2222', False, 'rhel7',
                                                  '/dev/sdz')
        finally:
            self.db_op.delete('b83c')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._dedicate_fcp")
    @mock.patch("zvmsdk.volumeop.FCPManager.decrease_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPManager.increase_fcp_usage")
    def test_attach_rollback(self, mock_increase, mock_decrease,
                             mock_dedicate, mock_undedicate):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        mock_increase.return_value = True
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        mock_dedicate.side_effect = exception.SDKSMUTRequestFailed(
            results, 'fake error')
        # return value of decreate must bigger than 1
        mock_decrease.return_value = 0
        self.assertRaises(exception.SDKBaseException,
                          self.volumeops.attach,
                          connection_info)
        mock_undedicate.assert_called_once_with('b83c', 'USER1')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._add_disk")
    @mock.patch("zvmsdk.volumeop.FCPManager.increase_fcp_usage")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
    @mock.patch("zvmsdk.volumeop.FCPManager.decrease_fcp_usage")
    def test_detach_rollback(self, mock_decrease, mock_remove_disk,
                             mock_increase, mock_add_disk):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        # this return does not matter
        mock_decrease.return_value = 0
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        mock_remove_disk.side_effect = exception.SDKSMUTRequestFailed(
            results, 'fake error')
        self.assertRaises(exception.SDKBaseException,
                          self.volumeops.detach,
                          connection_info)
        mock_increase.assert_called_once_with('b83c', 'USER1')
        mock_add_disk.assert_called_once_with('b83c', 'USER1', '1111',
                                              '2222', False, 'rhel7',
                                              '/dev/sdz')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach(self, mock_undedicate, mock_remove_disk):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        self.db_op = database.FCPDbOperator()
        self.db_op.new('b83c')
        self.db_op.assign('b83c', 'user1')

        try:
            self.volumeops.detach(connection_info)
            mock_remove_disk.assert_called_once_with('b83c', 'USER1', '1111',
                                                     '2222', False, 'rhel7',
                                                     '/dev/sdz')
            mock_undedicate.assert_called_once_with('b83c', 'USER1')
        finally:
            self.db_op.delete('b83c')

    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disk")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach_no_undedicate(self, mock_undedicate, mock_remove_disk):

        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'mount_point': '/dev/sdz',
                           'assigner_id': 'user1'}
        self.db_op = database.FCPDbOperator()
        self.db_op.new('b83c')
        self.db_op.assign('b83c', 'user1')
        self.db_op.increase_usage('b83c')

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            mock_remove_disk.assert_called_once_with('b83c', 'USER1', '1111',
                                                     '2222', False, 'rhel7',
                                                     '/dev/sdz')
        finally:
            self.db_op.delete('b83c')
