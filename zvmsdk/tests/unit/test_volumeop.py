# Copyright 2017, 2022 IBM Corp.
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
import uuid

from zvmsdk import config
from zvmsdk import database
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import volumeop
from zvmsdk.tests.unit import base


class TestVolumeOperatorAPI(base.SDKTestCase):

    def setUp(self):
        super(TestVolumeOperatorAPI, self).setUp()
        self.operator = volumeop.VolumeOperatorAPI()

    @mock.patch("zvmsdk.volumeop.FCPManager.edit_fcp_template")
    def test_edit_fcp_template(self, mock_edit_tmpl):
        """ Test edit_fcp_template """
        tmpl_id = 'fake_id'
        kwargs = {
            'name': 'new_name',
            'description': 'new_desc',
            'fcp_devices': '1A00-1A03;1B00-1B03',
            'host_default': False,
            'default_sp_list': ['sp1'],
            'min_fcp_paths_count': 2}
        self.operator.edit_fcp_template(tmpl_id, **kwargs)
        mock_edit_tmpl.assert_called_once_with(tmpl_id, **kwargs)

    @mock.patch("zvmsdk.volumeop.FCPManager.get_fcp_templates")
    def test_get_fcp_templates(self, mock_get_tmpl):
        """ Test get_fcp_templates in VolumeOperator"""
        tmpl_list = ['fake_id']
        assigner_id = 'fake_user'
        host_default = True
        default_sp_list = ['fake_sp']
        self.operator.get_fcp_templates(template_id_list=tmpl_list,
                                        assigner_id=assigner_id,
                                        default_sp_list=default_sp_list,
                                        host_default=host_default)
        mock_get_tmpl.assert_called_once_with(tmpl_list,
                                              assigner_id,
                                              default_sp_list,
                                              host_default)

    @mock.patch("zvmsdk.volumeop.FCPManager.get_fcp_templates_details")
    def test_get_fcp_templates_details(self, mock_get_tmpl_details):
        """ Test get_fcp_templates_details in VolumeOperator"""
        tmpl_list = ['fake_id']
        self.operator.get_fcp_templates_details(template_id_list=tmpl_list,
                                        raw=True, statistics=True,
                                        sync_with_zvm=False)
        mock_get_tmpl_details.assert_called_once_with(tmpl_list, raw=True,
                                                      statistics=True,
                                                      sync_with_zvm=False)

    @mock.patch("zvmsdk.volumeop.FCPManager.delete_fcp_template")
    def test_delete_fcp_template(self, mock_delete_tmpl):
        """ Test delete_fcp_template in VolumeOperator"""
        tmpl_id = 'fake_id'
        self.operator.delete_fcp_template(tmpl_id)
        mock_delete_tmpl.assert_called_once_with(tmpl_id)


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
        execute_cmd.assert_called_once_with(assigner_id, active_cmds,
                                            timeout=1800)

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
                                            active_cmds,
                                            timeout=1800)

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
        self.assertEqual('b83d', fcp.get_dev_no())
        self.assertEqual('free', fcp.get_dev_status())
        self.assertEqual('none', fcp.get_npiv_port())
        self.assertEqual('59', fcp.get_chpid())
        self.assertEqual('20076d8500005181', fcp.get_physical_port())
        self.assertEqual('none', fcp.get_owner())
        self.assertEqual(('b83d', 'none', '20076d8500005181', '59',
                          'free', 'none'),
                         fcp.to_tuple())

    def test_parse_npiv(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Active',
                'opnstk1:   NPIV world wide port number: 20076D8500005182',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181',
                'Owner: UNIT0001']
        fcp = volumeop.FCP(info)
        self.assertEqual('b83d', fcp.get_dev_no())
        self.assertEqual('active', fcp.get_dev_status())
        self.assertEqual('20076d8500005182', fcp.get_npiv_port())
        self.assertEqual('59', fcp.get_chpid())
        self.assertEqual('20076d8500005181', fcp.get_physical_port())
        self.assertEqual('unit0001', fcp.get_owner())
        self.assertEqual(('b83d', '20076d8500005182', '20076d8500005181',
                          '59', 'active', 'unit0001'),
                         fcp.to_tuple())


class TestFCPManager(base.SDKTestCase):

    @classmethod
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUpClass(cls):
        super(TestFCPManager, cls).setUpClass()
        cls.fcpops = volumeop.FCPManager()
        cls.db_op = database.FCPDbOperator()
        cls.fcp_vol_mgr = TestFCPVolumeManager()

    def _insert_data_into_fcp_table(self, fcp_info_list):
        # insert data into all columns of fcp table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp "
                             "(fcp_id, assigner_id, connections, "
                             "reserved, wwpn_npiv, wwpn_phy, chpid, "
                             "state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)

    def _insert_data_into_template_table(self, templates_info):
        # insert data into all columns of template table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template "
                             "(id, name, description, is_default) "
                             "VALUES (?, ?, ?, ?)", templates_info)

    def _delete_from_template_table(self, template_id_list):
        # delete templates record from template and template_sp_mapping
        templates_id = [(tmpl_id,) for tmpl_id in template_id_list]
        with database.get_fcp_conn() as conn:
            conn.executemany("DELETE FROM template "
                             "WHERE id=?", templates_id)
            conn.executemany("DELETE FROM template_sp_mapping "
                             "WHERE tmpl_id=?", templates_id)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_fcp_info_by_status")
    def test_get_all_fcp_info(self, get_fcp_info):
        """Test get_all_fcp_info"""
        get_fcp_info.return_value = []
        self.fcpops._get_all_fcp_info('dummy1')
        get_fcp_info.assert_called_once_with('dummy1', None)

    def test_add_fcp_for_assigner(self):
        """Test add_fcp_for_assigner"""
        # create 2 FCP records
        # a83c: connections == 0, reserved == 0
        # a83d: connections == 2, reserved == 1
        # pre create data in FCP DB for test
        template_id = ''
        fcp_info_list = [('a83c', 'user1', 0, 0, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('a83d', 'user2', 2, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # remove dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # find FCP for user and FCP not exist, should allocate them
        try:
            flag1 = self.fcpops.add_fcp_for_assigner('a83c', 'dummy1')
            self.assertEqual(True, flag1)

            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('a83c')
            self.assertEqual('dummy1', userid)
            self.assertEqual(1, conn)
            self.assertEqual(0, reserved)
            self.assertEqual(template_id, tmpl_id)

            flag2 = self.fcpops.add_fcp_for_assigner('a83d', 'user2')
            self.assertEqual(False, flag2)

            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('a83d')
            self.assertEqual('user2', userid)
            self.assertEqual(3, conn)
            self.assertEqual(1, reserved)
            self.assertEqual(template_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_fcp_dict_in_db(self):
        """Test get_fcp_dict_in_db"""
        # create 2 FCP records
        # a83c: connections == 0, reserved == 0
        # a83d: connections == 2, reserved == 1
        # pre create data in FCP DB for test
        template_id = ''
        fcp_info_list = [('1a01', 'user1', 0, 0, 'c05076de33000a01',
                          'c05076de3300264a', '27', 'active', 'owner1',
                          template_id),
                         ('1a02', 'user1', 0, 1, 'c05076de33000a02',
                          'c05076de3300264a', '27', 'active', 'owner1',
                          template_id),
                         ('1b01', 'user2', 1, 1, 'c05076de33000b01',
                          'c05076de3300264b', '27', 'active', 'owner1',
                          template_id),
                         ('1b03', 'user2', 2, 1, 'c05076de33000b03',
                          'c05076de3300264b', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # remove dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            fcp_dict = self.fcpops.get_fcp_dict_in_db()
            info_1a02 = fcp_dict['1a02']
            info_1b03 = fcp_dict['1b03']
            self.assertEqual(info_1a02['connections'], 0)
            self.assertEqual(info_1a02['reserved'], 1)
            self.assertEqual(info_1b03['connections'], 2)
            self.assertEqual(info_1b03['reserved'], 1)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_reserve_fcp_devices_with_existed_reserved_fcp(self):
        template_id = "fake_fcp_template_00"
        assinger_id = "wxy0001"
        sp_name = "fake_sp_name"
        fcp_info_list = [('1a10', assinger_id, 1, 1, 'c05076de3300a83c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('1b10', assinger_id, 1, 1, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id),
                         ('1a11', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id),
                         ('1b11', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)
                         ]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('1a10', template_id, 0),
                        ('1b10', template_id, 1)]
        self.fcp_vol_mgr._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert data into template table to add a default template
        templates = [(template_id, 'name1', 'desc1', 1)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)

        template_sp_mapping = [(sp_name, template_id)]
        self.fcp_vol_mgr._insert_data_into_template_sp_mapping_table(template_sp_mapping)

        try:
            available_list, fcp_tmpl_id = self.fcpops.reserve_fcp_devices(
                assinger_id, template_id, sp_name)
            expected_fcp_list = [('1a10', 'c05076de3300a83c', 'c05076de33002641'),
                                 ('1b10', 'c05076de3300b83c', 'c05076de33002641')]
            actual_fcp_list = []
            for fcp in available_list:
                fcp_id, wwpn_npiv, wwpn_phy = fcp
                actual_fcp_list.append((fcp_id, wwpn_npiv, wwpn_phy))
            self.assertEqual(template_id, fcp_tmpl_id)
            self.assertEqual(expected_fcp_list, actual_fcp_list)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self._delete_from_template_table(template_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm", mock.Mock())
    def test_reserve_fcp_devices_without_existed_reserved_fcp(self):
        """
        reserve fcp devices for the assigner which hasn't reserved any
        fcp devices before
        """
        template_id = "fake_fcp_template_00"
        assinger_id = "wxy0001"
        sp_name = "fake_sp_name"
        fcp_info_list = [('1a10', '', 0, 0, 'c05076de3300a83c',
                          'c05076de33002641', '27', 'free', '',
                          ''),
                         ('1b10', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'free', '',
                          ''),
                         ('1a11', '', 0, 0, 'c05076de3300c83c',
                          'c05076de33002641', '27', 'free', '',
                          ''),
                         ('1b11', '', 0, 0, 'c05076de3300d83c',
                          'c05076de33002641', '27', 'free', '',
                          '')
                         ]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('1a10', template_id, 0),
                        ('1b10', template_id, 1)]
        self.fcp_vol_mgr._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert data into template table to add a default template
        templates = [(template_id, 'name1', 'desc1', 1)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)

        template_sp_mapping = [(sp_name, template_id)]
        self.fcp_vol_mgr._insert_data_into_template_sp_mapping_table(template_sp_mapping)
        config.CONF.volume.get_fcp_pair_with_same_index = 1
        try:
            available_list, fcp_tmpl_id = self.fcpops.reserve_fcp_devices(
                assinger_id, template_id, sp_name)
            actual_fcp_list = []
            for fcp in available_list:
                fcp_id, wwpn_npiv, wwpn_phy = fcp
                actual_fcp_list.append((fcp_id, wwpn_npiv, wwpn_phy))
            self.assertEqual(template_id, fcp_tmpl_id)
            self.assertEqual(2, len(actual_fcp_list))
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self._delete_from_template_table(template_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_reserve_fcp_devices_without_default_template(self):
        """
        Not specify template id, and no sp default template and
        no host default template, should raise error
        """
        template_id = None
        assinger_id = "wxy0001"
        sp_name = "fake_sp_name"

        # insert data into template table to add a default template
        templates = [('0001', 'name1', 'desc1', 0)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)
        try:
            self.assertRaisesRegex(exception.SDKVolumeOperationError,
                                   "No FCP template is specified and no "
                                   "default FCP template is found.",
                                   self.fcpops.reserve_fcp_devices,
                                   assinger_id, template_id, sp_name)
        finally:
            self._delete_from_template_table(template_id_list)

    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm", mock.Mock())
    @mock.patch("zvmsdk.database.FCPDbOperator.get_allocated_fcps_from_assigner")
    @mock.patch("zvmsdk.database.FCPDbOperator.get_fcp_devices")
    def test_reserve_fcp_devices_without_free_fcp_device(self, mocked_get_fcp_devices, mocked_get_allocated_fcps):
        config.CONF.volume.get_fcp_pair_with_same_index = None
        mocked_get_fcp_devices.return_value = []
        mocked_get_allocated_fcps.return_value = []
        template_id = "fake_fcp_template_00"
        assinger_id = "wxy0001"
        sp_name = "fake_sp_name"
        available_list, fcp_tmpl_id = self.fcpops.reserve_fcp_devices(
            assinger_id, template_id, sp_name)
        self.assertEqual(template_id, fcp_tmpl_id)
        self.assertEqual(0, len(available_list))

    def test_unreserve_fcp_devices_without_fcp_template(self):
        """
        if not specify fcp_template_id when calling unreserve_fcp_devices,
        error will be raised
        """
        assigner_id = "test_assigner"
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               "fcp_template_id is not specified while "
                               "releasing FCP devices",
                               self.fcpops.unreserve_fcp_devices,
                               assigner_id, None)

    def test_unreserve_fcp_devices_return_empty_array(self):
        """If not found any fcp devices to release, return empty array"""
        template_id = "fake_fcp_template_00"
        assinger_id = "wxy0001"
        fcp_info_list = [('1a10', assinger_id, 0, 0, 'c05076de3300a83c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('1b10', assinger_id, 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id),
                         ('1a11', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id),
                         ('1b11', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)
                         ]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('1a10', template_id, 0),
                        ('1b10', template_id, 1)]
        self.fcp_vol_mgr._insert_data_into_template_fcp_mapping_table(
            template_fcp)

        try:
            res = self.fcpops.unreserve_fcp_devices(assinger_id, template_id)
            self.assertEqual(len(res), 0)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_valid_fcp_devcie_wwpn(self):
        assigner_id = 'test_assigner_1'
        fcp_list_1 = [('1a10', '', ''), ('1b10', 'wwpn_npiv_0', 'wwpn_phy_0')]
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               "NPIV WWPN of FCP device 1a10 not found",
                               self.fcpops._valid_fcp_devcie_wwpn,
                               fcp_list_1, assigner_id)

        fcp_list_2 = [('1a10', 'wwpn_npiv_0', ''), ('1b10', 'wwpn_npiv_0', 'wwpn_phy_0')]
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               "Physical WWPN of FCP device 1a10 not found",
                               self.fcpops._valid_fcp_devcie_wwpn,
                               fcp_list_2, assigner_id)

    @mock.patch("zvmsdk.utils.get_smt_userid", mock.Mock())
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_get_fcp_dict_in_zvm(self, mock_zvm_fcp_info):
        """Test get_fcp_dict_in_zvm"""
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

    @mock.patch("zvmsdk.volumeop.FCPManager."
                "sync_fcp_table_with_zvm")
    @mock.patch("zvmsdk.volumeop.FCPManager."
                "get_fcp_dict_in_zvm")
    def test_sync_db_with_zvm(self, fcp_dict_in_zvm,
                              sync_fcp_table_with_zvm):
        """Test sync_db_with_zvm"""
        zvm_fcp_dict = {
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
        fcp_dict_in_zvm.return_value = zvm_fcp_dict
        self.fcpops._sync_db_with_zvm()
        fcp_dict_in_zvm.assert_called_once()
        sync_fcp_table_with_zvm.assert_called_once_with(zvm_fcp_dict)

    def test_sync_fcp_table_with_zvm(self):
        """Test sync_fcp_table_with_zvm"""
        # fcp info in original database
        template_id = ''
        fcp_info_list = [('1a01', 'user1', 0, 0, 'c05076de33000001',
                          'c05076de3300264a', '27', 'active', 'owner1',
                          template_id),
                         ('1a02', 'user1', 0, 0, 'c05076de33000002',
                          'c05076de3300264a', '27', 'active', 'owner1',
                          template_id),
                         ('1b01', 'user2', 1, 1, 'c05076de33000003',
                          'c05076de3300264b', '27', 'active', 'owner1',
                          template_id),
                         ('1b03', 'unit0001', 2, 1, 'c05076de33000004',
                          'c05076de3300264b', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # remove dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # fcp info in zvm
        # 1a01: is in zvm, but wwpns,state,owner are changed
        #       should update these columns
        # 1a02: is not found in zvm, should be remove from db
        # 1b01: is in zvm, wwpn is changed, but in use(connections != 0)
        #       so should not update its NPIV wwpns
        #       physical WWPN will change
        # 1b02: is new in zvm, should add to db
        # 1b03: is in zvm, owner and chpid are changed
        #       should be updated
        fcp_info_in_zvm = [
            'opnstk1: FCP device number: 1A01',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: c05076de33000A01',
            'opnstk1:   Channel path ID: 27',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: NONE',
            'opnstk1: FCP device number: 1B01',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: c05076de33000B01',
            'opnstk1:   Channel path ID: 27',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: OWNER1',
            'opnstk1: FCP device number: 1B02',
            'opnstk1:   Status: Free',
            'opnstk1:   NPIV world wide port number: c05076de33000B02',
            'opnstk1:   Channel path ID: 27',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005181',
            'Owner: NONE',
            'opnstk1: FCP device number: 1B03',
            'opnstk1:   Status: Active',
            'opnstk1:   NPIV world wide port number: c05076de33000B03',
            'opnstk1:   Channel path ID: 30',
            'opnstk1:   Physical world wide port number: '
            '20076D8500005185',
            'Owner: UNIT0001']
        fcp_dict_in_zvm = {
            '1a01': volumeop.FCP(fcp_info_in_zvm[0:6]),
            '1b01': volumeop.FCP(fcp_info_in_zvm[6:12]),
            '1b02': volumeop.FCP(fcp_info_in_zvm[12:18]),
            '1b03': volumeop.FCP(fcp_info_in_zvm[18:24]),
        }
        fcp_info_in_db_expected = {
            '1a01': ('1a01', 'user1', 0, 0, 'c05076de33000a01',
                     '20076d8500005181', '27', 'free', 'none',
                     template_id),
            '1b01': ('1b01', 'user2', 1, 1, 'c05076de33000003',
                     '20076d8500005181', '27', 'active', 'owner1',
                     template_id),
            '1b02': ('1b02', '', 0, 0, 'c05076de33000b02',
                     '20076d8500005181', '27', 'free', 'none',
                     template_id),
            '1b03': ('1b03', 'unit0001', 2, 1, 'c05076de33000004',
                     '20076d8500005185', '30', 'active', 'unit0001',
                     template_id)
        }
        try:
            self.fcpops.sync_fcp_table_with_zvm(fcp_dict_in_zvm)
            fcp_info_in_db_new = self.fcpops.get_fcp_dict_in_db()
            # because not return value is sqlite3.Row object
            # so need to comare them one by one
            self.assertEqual(fcp_info_in_db_new.keys(),
                             fcp_info_in_db_expected.keys())
            for fcp_id in fcp_info_in_db_new:
                self.assertEqual(tuple(fcp_info_in_db_new[fcp_id]),
                                 fcp_info_in_db_expected[fcp_id])
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch.object(uuid, 'uuid1')
    def test_create_fcp_template(self, get_uuid):
        """Test create_fcp_template"""
        # there is already a default template:
        # fakehos1-1111-1111-1111-111111111111
        templates = [('fakehos1-1111-1111-1111-111111111111', 'name1',
                      'desc1', 1),
                     ('fakehos2-1111-1111-1111-111111111111', 'name2',
                      'desc2', 0)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)
        # parameters of new template
        new_template_id = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        template_id_list.append(new_template_id)
        get_uuid.return_value = new_template_id
        name = "test template"
        description = "test create_fcp_template"
        fcp_devices = "1a00-1a01, 1a03;1b01, 1b03-1b04"
        fcp_id_list = ['1a00', '1a01', '1a03', '1b01', '1b03', '1b04']
        host_default = True
        default_sp_list = ['sp1', 'sp2']
        expected_templates_info = {
            'fakehos1-1111-1111-1111-111111111111': {
                "id": "fakehos1-1111-1111-1111-111111111111",
                "name": "name1",
                "description": "desc1",
                "host_default": False,
                "storage_providers": [],
                'min_fcp_paths_count': 0
            },
            'fakehos2-1111-1111-1111-111111111111': {
                "id": "fakehos2-1111-1111-1111-111111111111",
                "name": "name2",
                "description": "desc2",
                "host_default": False,
                "storage_providers": [],
                'min_fcp_paths_count': 0
            },
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c': {
                "id": "ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c",
                "name": "test template",
                "description": "test create_fcp_template",
                "host_default": True,
                "storage_providers": ['sp1', 'sp2'],
                'min_fcp_paths_count': 2,
            },
        }
        try:
            ret = self.fcpops.create_fcp_template(name,
                                                  description,
                                                  fcp_devices,
                                                  host_default,
                                                  default_sp_list)
            self.assertEqual(ret['fcp_template']['name'], name)
            self.assertEqual(ret['fcp_template']['description'], description)
            self.assertEqual(ret['fcp_template']['host_default'], host_default)
            self.assertEqual(ret['fcp_template']['storage_providers'], default_sp_list)
            # check content in database
            all_templates_info = self.fcpops.get_fcp_templates(
                template_id_list)
            for tmpl in all_templates_info['fcp_templates']:
                self.assertDictEqual(tmpl, expected_templates_info[tmpl['id']])
        finally:
            self._delete_from_template_table(template_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list,
                                                     new_template_id)
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_create_fcp_template_with_error(self):
        name = 'test_fcp_tmpl'
        description = 'test-desc'
        fcp_devices = '1a10;1b10'
        min_fcp_paths_count = 4
        self.assertRaisesRegex(exception.SDKConflictError,
                               'min_fcp_paths_count 4 is larger than fcp device path count 2',
                               self.fcpops.create_fcp_template,
                               name, description, fcp_devices,
                               min_fcp_paths_count=min_fcp_paths_count)

    @mock.patch("zvmsdk.database.FCPDbOperator.edit_fcp_template")
    def test_edit_fcp_template(self, mock_db_edit_tmpl):
        """ Test edit_fcp_template """
        tmpl_id = 'fake_id'
        kwargs = {
            'name': 'new_name',
            'description': 'new_desc',
            'fcp_devices': '1A00-1A03;1B00-1B03',
            'host_default': False,
            'default_sp_list': ['sp1'],
            'min_fcp_paths_count': 2}
        self.fcpops.edit_fcp_template(tmpl_id, **kwargs)
        mock_db_edit_tmpl.assert_called_once_with(tmpl_id, **kwargs)

    def test_update_template_fcp_raw_usage(self):
        raw = ('fcp_id_1', 'tmpl_id_1', 0, 'assigner_id', 1, 0,
            'wwpn_npiv', 'wwpn_phy', 'chpid', 'state', 'owner', '')
        expected = {
            'tmpl_id_1': {
                0: [('fcp_id_1', 'tmpl_id_1', 'assigner_id', 1, 0,
                    'wwpn_npiv', 'wwpn_phy', 'chpid', 'state', 'owner', '')]}}
        result = self.fcpops._update_template_fcp_raw_usage({}, raw)
        self.assertDictEqual(result, expected)

    def test_get_fcp_templates(self):
        """ Test get_fcp_templates in FCPManager"""
        try:
            # prepare test data
            template_id_1 = 'template_id_1'
            template_id_2 = 'template_id_2'
            templates = [(template_id_1, 'name1', 'desc1', 1),
                         (template_id_2, 'name2', 'desc2', 0)]
            self._delete_from_template_table([template_id_1, template_id_2])
            self._insert_data_into_template_table(templates)
            template_sp_mapping = [('sp1', template_id_1), ('sp2', template_id_2)]
            self.fcp_vol_mgr._insert_data_into_template_sp_mapping_table(template_sp_mapping)

            fcp_info_list_2 = [
                            # allocated
                            ('1b00', 'user2', 1, 1, 'c05076de3300c83c',
                            'c05076de33002641', '27', 'active', '',
                            template_id_2),
                            # unallocated_but_active
                            ('1b01', '', 0, 0, 'c05076de3300d83c',
                            'c05076de33002641', '35', 'active', 'owner2',
                            '')]
            fcp_id_list_2 = [fcp_info[0] for fcp_info in fcp_info_list_2]
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_2)
            self._insert_data_into_fcp_table(fcp_info_list_2)
            # case1: get by template_id_list
            result_1 = self.fcpops.get_fcp_templates([template_id_1])
            expected_1 = {
                "fcp_templates": [
                    {
                    "id": template_id_1,
                    "name": "name1",
                    "description": "desc1",
                    "host_default": True,
                    "storage_providers": ["sp1"],
                    'min_fcp_paths_count': 0
                    }]}
            self.assertDictEqual(result_1, expected_1)

            # case2: get by assigner_id
            expected_2 = {
                "fcp_templates": [
                    {
                    "id": template_id_2,
                    "name": "name2",
                    "description": "desc2",
                    "host_default": False,
                    "storage_providers": ["sp2"],
                    'min_fcp_paths_count': 0
                    }]}
            result_2 = self.fcpops.get_fcp_templates(assigner_id='user2')
            self.assertDictEqual(result_2, expected_2)

            # case3: get by host_default=True
            result_3 = self.fcpops.get_fcp_templates(host_default=True)
            self.assertDictEqual(result_3, expected_1)

            # # case4: get by host_default=False
            result_4 = self.fcpops.get_fcp_templates(host_default=False)
            self.assertDictEqual(result_4, expected_2)

            # case5: get by default_sp_list=['sp1']
            result_5 = self.fcpops.get_fcp_templates(default_sp_list=['sp1'])
            self.assertDictEqual(result_5, expected_1)

            # case6: get by default_sp_list=['all']
            expected_all = {
                "fcp_templates": [
                    {
                        "id": template_id_1,
                        "name": "name1",
                        "description": "desc1",
                        "host_default": True,
                        "storage_providers": ["sp1"],
                        'min_fcp_paths_count': 0
                    },
                    {
                        "id": template_id_2,
                        "name": "name2",
                        "description": "desc2",
                        "host_default": False,
                        "storage_providers": ["sp2"],
                        'min_fcp_paths_count': 0
                    }]}
            result_6 = self.fcpops.get_fcp_templates(default_sp_list=['all'])
            self.assertDictEqual(result_6, expected_all)

            # case7: without any parameter, will get all templates
            result_7 = self.fcpops.get_fcp_templates()
            self.assertDictEqual(result_7, expected_all)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_2)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list_2, template_id_2)
            self._delete_from_template_table([template_id_1, template_id_2])

    @mock.patch(
        "zvmsdk.volumeop.FCPManager._update_template_fcp_raw_usage")
    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm")
    def test_get_fcp_templates_details(self, mock_sync, mock_raw):
        """ Test get_fcp_templates_details in FCPManager"""
        try:
            self.maxDiff = None
            # prepare test data
            template_id_1 = 'template_id_1'
            template_id_2 = 'template_id_2'
            templates = [(template_id_1, 'name1', 'desc1', 1),
                         (template_id_2, 'name2', 'desc2', 0)]
            self._delete_from_template_table([template_id_1, template_id_2])
            self._insert_data_into_template_table(templates)
            template_sp_mapping = [('sp1', template_id_1), ('sp2', template_id_2)]
            self.fcp_vol_mgr._insert_data_into_template_sp_mapping_table(template_sp_mapping)

            fcp_info_list_1 = [
                            # available
                            ('1a00', '', 0, 0, 'c05076de3300a83c',
                            'c05076de33002641', '27', 'free', '',
                            '')
                            ]
            fcp_info_list_2 = [
                            # allocated
                            ('1b00', 'user2', 1, 1, 'c05076de3300c83c',
                            'c05076de33002641', '27', 'active', '',
                            template_id_2),
                            # unallocated_but_active
                            ('1b01', '', 0, 0, 'c05076de3300d83c',
                            'c05076de33002641', '35', 'active', 'owner2',
                            '')]
            fcp_id_list_1 = [fcp_info[0] for fcp_info in fcp_info_list_1]
            fcp_id_list_2 = [fcp_info[0] for fcp_info in fcp_info_list_2]
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_1)
            self._insert_data_into_fcp_table(fcp_info_list_1)
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_2)
            self._insert_data_into_fcp_table(fcp_info_list_2)
            template_fcp = [('1a00', template_id_1, 0),
                            ('1x00', template_id_1, 1),
                            ('1b00', template_id_2, 0),
                            ('1b01', template_id_2, 1)]
            fcp_id_list_1.append('1x00')
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list_1, template_id_1)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list_2, template_id_2)
            self.fcp_vol_mgr._insert_data_into_template_fcp_mapping_table(template_fcp)

            # case1: test get_fcp_templates_details without input parameter
            expected_1 = {
                "id": template_id_1,
                "name": "name1",
                "description": "desc1",
                "host_default": True,
                "storage_providers": ["sp1"],
                'min_fcp_paths_count': 2,
                "statistics": {
                    0: {
                            "total": "1A00",
                            "total_count": 1,
                            "single_fcp": "1A00",
                            "range_fcp": "",
                            "available": "1A00",
                            "available_count": 1,
                            "allocated": "",
                            "reserve_only": "",
                            "connection_only": "",
                            "unallocated_but_active": {},
                            "allocated_but_free": "",
                            "notfound": "",
                            "offline": "",
                            "CHPIDs": {"27": "1A00"}},
                    1: {
                            "total": "1X00",
                            "total_count": 1,
                            "single_fcp": "1X00",
                            "range_fcp": "",
                            "available": "",
                            "available_count": 0,
                            "allocated": "",
                            "reserve_only": "",
                            "connection_only": "",
                            "unallocated_but_active": {},
                            "allocated_but_free": "",
                            "notfound": "1X00",
                            "offline": "",
                            "CHPIDs": {}}
                }
                }
            expected_2 = {
                "id": template_id_2,
                "name": "name2",
                "description": "desc2",
                "host_default": False,
                "storage_providers": ["sp2"],
                'min_fcp_paths_count': 2,
                "statistics": {
                    0: {
                            "total": "1B00",
                            "total_count": 1,
                            "single_fcp": "1B00",
                            "range_fcp": "",
                            "available": "",
                            "available_count": 0,
                            "allocated": "1B00",
                            "reserve_only": "",
                            "connection_only": "",
                            "unallocated_but_active": {},
                            "allocated_but_free": "",
                            "notfound": "",
                            "offline": "",
                            "CHPIDs": {"27": "1B00"}},
                    1: {
                            "total": "1B01",
                            "total_count": 1,
                            "single_fcp": "1B01",
                            "range_fcp": "",
                            "available": "",
                            "available_count": 0,
                            "allocated": "",
                            "reserve_only": "",
                            "connection_only": "",
                            "unallocated_but_active": {"1B01": "owner2"},
                            "allocated_but_free": "",
                            "notfound": "",
                            "offline": "",
                            "CHPIDs": {"35": "1B01"}
                    }
                }
            }
            expected_all = {
                "fcp_templates": [expected_1, expected_2]}
            result_all = self.fcpops.get_fcp_templates_details(raw=False,
                                                             statistics=True,
                                                             sync_with_zvm=False)
            mock_sync.assert_not_called()
            self.assertDictEqual(result_all, expected_all)

            # case2: get_fcp_templates_details by template_id_list
            result = self.fcpops.get_fcp_templates_details(template_id_list=[template_id_1],
                                                             raw=False,
                                                             statistics=True,
                                                             sync_with_zvm=False)
            expected = {'fcp_templates': [expected_1]}
            self.assertDictEqual(result, expected)

            # case3: get_fcp_templates_details with raw=True and sync_with_zvm=True
            self.fcpops.get_fcp_templates_details(template_id_list=[template_id_1],
                                                    raw=True,
                                                    statistics=True,
                                                    sync_with_zvm=True)
            mock_raw.assert_called()
            mock_sync.assert_called()
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_1)
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list_2)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list_1, template_id_1)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list_2, template_id_2)
            self._delete_from_template_table([template_id_1, template_id_2])

    def test_update_template_fcp_statistics_usage(self):
        self.maxDiff = None
        statistics_usage = {}
        # raw_item format
        # (fcp_id|tmpl_id|path|assigner_id|connections|
        # reserved|wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)
        raw_items = [('1a01', 'tmpl_id_1', '0', '', 2,
                    1, 'wwpn_npiv', 'wwpn_phy', '27', 'active',
                    'owner1', 'tmpl_id_1'),
                    ('1a02', 'tmpl_id_1', '0', '', 0,
                    0, 'wwpn_npiv', 'wwpn_phy', '32', 'free',
                    '', ''),
                    ('1b01', 'tmpl_id_1', '1', '', 0,
                    0, 'wwpn_npiv', 'wwpn_phy', '27', 'active',
                    'assigner_id_1', ''),
                    ('1b02', 'tmpl_id_1', '1', '', 0,
                    0, 'wwpn_npiv', 'wwpn_phy', '32', 'active',
                    'assigner_id_2', ''),
                    ('1c03', 'tmpl_id_2', '0', '', 0,
                    1, 'wwpn_npiv', 'wwpn_phy', '25', 'free',
                    '', ''),
                    ('1c05', 'tmpl_id_2', '0', '', 1,
                    0, 'wwpn_npiv', 'wwpn_phy', '25', 'free',
                    '', ''),
                    ('1c06', 'tmpl_id_2', '0', '', 1,
                    1, 'wwpn_npiv', 'wwpn_phy', '26', 'free',
                    '', ''),
                    ('1d05', 'tmpl_id_2', '1', '', None,
                    '', '', '', '', '', '', ''),
                    ('1d06', 'tmpl_id_2', '1', '', 0,
                    0, 'wwpn_npiv', 'wwpn_phy', '', 'notfound',
                    '', ''),
                    ('1e09', 'tmpl_id_3', '0', '', 0,
                    0, 'wwpn_npiv', 'wwpn_phy', '30', 'offline',
                    '', '')]
        for raw in raw_items:
            self.fcpops._update_template_fcp_statistics_usage(
                statistics_usage, raw)
        expected = {
            'tmpl_id_1': {
                '0': {
                    "total": ['1A01', '1A02'],
                    "total_count": 0,
                    "single_fcp": [],
                    "range_fcp": [],
                    "available": ['1A02'],
                    "available_count": 0,
                    "allocated": ['1A01'],
                    "reserve_only": [],
                    "connection_only": [],
                    "unallocated_but_active": {},
                    "allocated_but_free": [],
                    "notfound": [],
                    "offline": [],
                    "CHPIDs": {'27': ['1A01'],
                               '32': ['1A02']}},
                '1': {
                    "total": ['1B01', '1B02'],
                    "total_count": 0,
                    "single_fcp": [],
                    "range_fcp": [],
                    "available": [],
                    "available_count": 0,
                    "allocated": [],
                    "reserve_only": [],
                    "connection_only": [],
                    "unallocated_but_active": {
                        '1B01': 'assigner_id_1',
                        '1B02': 'assigner_id_2'},
                    "allocated_but_free": [],
                    "notfound": [],
                    "offline": [],
                    "CHPIDs": {'27': ['1B01'],
                               '32': ['1B02']}}
                               },
            'tmpl_id_2': {
                '0': {
                    "total": ['1C03', '1C05', '1C06'],
                    "total_count": 0,
                    "single_fcp": [],
                    "range_fcp": [],
                    "available": [],
                    "available_count": 0,
                    "allocated": ['1C06'],
                    "reserve_only": ['1C03'],
                    "connection_only": ['1C05'],
                    "unallocated_but_active": {},
                    "allocated_but_free": ['1C05', '1C06'],
                    "notfound": [],
                    "offline": [],
                    "CHPIDs": {'25': ['1C03', '1C05'],
                               '26': ['1C06']}},
                '1': {
                    "total": ['1D05', '1D06'],
                    "total_count": 0,
                    "single_fcp": [],
                    "range_fcp": [],
                    "available": [],
                    "available_count": 0,
                    "allocated": [],
                    "reserve_only": [],
                    "connection_only": [],
                    "unallocated_but_active": {},
                    "allocated_but_free": [],
                    "notfound": ['1D05', '1D06'],
                    "offline": [],
                    "CHPIDs": {}}
                    },
            'tmpl_id_3': {
                '0': {
                    "total": ['1E09'],
                    "total_count": 0,
                    "single_fcp": [],
                    "range_fcp": [],
                    "available": [],
                    "available_count": 0,
                    "allocated": [],
                    "reserve_only": [],
                    "connection_only": [],
                    "unallocated_but_active": {},
                    "allocated_but_free": [],
                    "notfound": [],
                    "offline": ['1E09'],
                    "CHPIDs": {'30': ['1E09']}}}
                    }
        self.assertDictEqual(statistics_usage, expected)

    @mock.patch("zvmsdk.database.FCPDbOperator.delete_fcp_template")
    def test_delete_fcp_template(self, mock_db_delete_tmpl):
        """ Test delete_fcp_template in FCPManager"""
        self.fcpops.delete_fcp_template('tmpl_id')
        mock_db_delete_tmpl.assert_called_once_with('tmpl_id')


class TestFCPVolumeManager(base.SDKTestCase):

    @classmethod
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUpClass(cls):
        super(TestFCPVolumeManager, cls).setUpClass()
        cls.volumeops = volumeop.FCPVolumeManager()
        cls.db_op = database.FCPDbOperator()

    # tearDownClass deleted to work around bug of 'no such table:fcp'
    def _insert_data_into_fcp_table(self, fcp_info_list):
        # insert data into all columns of fcp table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp "
                             "(fcp_id, assigner_id, connections, "
                             "reserved, wwpn_npiv, wwpn_phy, chpid, "
                             "state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)

    def _insert_data_into_template_table(self, templates_info):
        # insert data into all columns of template table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template "
                             "(id, name, description, is_default) "
                             "VALUES (?, ?, ?, ?)", templates_info)

    def _insert_data_into_template_fcp_mapping_table(self,
                                                     template_fcp_mapping):
        # insert data into all columns of template_fcp_mapping table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template_fcp_mapping "
                             "(fcp_id, tmpl_id, path) "
                             "VALUES (?, ?, ?)", template_fcp_mapping)

    def _insert_data_into_template_sp_mapping_table(self,
                                                    template_sp_mapping):
        # insert data into all columns of template_sp_mapping table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template_sp_mapping "
                             "(sp_name, tmpl_id) "
                             "VALUES (?, ?)", template_sp_mapping)

    def _delete_from_template_table(self, template_id_list):
        templates_id = [(tmpl_id,) for tmpl_id in template_id_list]
        with database.get_fcp_conn() as conn:
            conn.executemany("DELETE FROM template "
                             "WHERE id=?", templates_id)

    @mock.patch("zvmsdk.utils.get_smt_userid")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.get_lpar_name")
    def test_get_volume_connector_unreserve(self, get_lpar_name,
                                            get_all_fcp_info,
                                            get_smt_userid):
        """Test get_volume_connector when reserve parameter is False"""
        get_lpar_name.return_value = "fakehos1"
        get_smt_userid.return_value = "fakesmt"
        fcp_list = ['opnstk1: FCP device number: A83C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    'C05076DE3300A83C',
                    'opnstk1:   Channel path ID: 27',
                    'opnstk1:   Physical world wide port number: '
                    'C05076DE33002641',
                    'Owner: FAKEUSER',
                    'opnstk1: FCP device number: B83C',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: '
                    'C05076DE3300B83C',
                    'opnstk1:   Channel path ID: 27',
                    'opnstk1:   Physical world wide port number: '
                    'C05076DE33002641',
                    'Owner: FAKEUSER']
        get_all_fcp_info.return_value = fcp_list
        # insert data into fcp table
        template_id = 'fakehos1-1111-1111-1111-111111111111'
        fcp_info_list = [('a83c', 'fakeuser', 0, 1, 'c05076de3300a83c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('b83c', 'fakeuser', 0, 1, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('a83c', template_id, 0),
                        ('b83c', template_id, 1)]
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert data into template table to add a default template
        templates = [('fakehos1-1111-1111-1111-111111111111', 'name1',
                      'desc1', 1),
                     ('fakehos2-1111-1111-1111-111111111111', 'name2',
                      'desc2', 0)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)
        try:
            connector = self.volumeops.get_volume_connector(
                'fakeuser', False, fcp_template_id=template_id)
            expected = {'zvm_fcp': ['a83c', 'b83c'],
                        'wwpns': ['c05076de3300a83c', 'c05076de3300b83c'],
                        'phy_to_virt_initiators': {
                            'c05076de3300a83c': 'c05076de33002641',
                            'c05076de3300b83c': 'c05076de33002641'
                            },
                        'host': 'fakehos1_fakeuser',
                        'fcp_paths': 2,
                        'fcp_template_id': template_id}
            self.assertDictEqual(expected, connector)

            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('b83c')
            self.assertEqual('fakeuser', userid)
            self.assertEqual(0, conn)
            self.assertEqual(0, reserved)
            # because reserve is False, so tmpl_id set to ''
            self.assertEqual('', tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
            self._delete_from_template_table(template_id_list)

    @mock.patch("zvmsdk.utils.get_smt_userid")
    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.get_lpar_name")
    def test_get_volume_connector_reserve(self, get_lpar_name,
                                          get_all_fcp_info,
                                          get_smt_userid):
        """Test get_volume_connector when reserve parameter is True"""
        get_lpar_name.return_value = "fakehos1"
        get_smt_userid.return_value = "fakesmt"
        fcp_list = ['opnstk1: FCP device number: A83C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    'C05076DE3300A83C',
                    'opnstk1:   Channel path ID: 27',
                    'opnstk1:   Physical world wide port number: '
                    'C05076DE33002641',
                    'Owner: NONE',
                    'opnstk1: FCP device number: B83C',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: '
                    'C05076DE3300B83C',
                    'opnstk1:   Channel path ID: 27',
                    'opnstk1:   Physical world wide port number: '
                    'C05076DE33002641',
                    'Owner: NONE']
        get_all_fcp_info.return_value = fcp_list
        # insert data into fcp table
        template_id = 'fakehos1-1111-1111-1111-111111111111'
        # in database, the state in active, but in zvm it is free
        # get_volume_connector should be able to get them
        fcp_info_list = [('a83c', '', 0, 0, 'c05076de3300a83c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('b83c', '', 0, 0, 'c05076de3300b83c',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('a83c', template_id, 0),
                        ('b83c', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert data into template table to add a default template
        templates = [('fakehos1-1111-1111-1111-111111111111', 'name1',
                      'desc1', 1),
                     ('fakehos2-1111-1111-1111-111111111111', 'name2',
                      'desc2', 0)]
        template_id_list = [tmpl[0] for tmpl in templates]
        self._insert_data_into_template_table(templates)
        try:
            connector = self.volumeops.get_volume_connector('fakeuser',
                                                            True)
            expected = {'zvm_fcp': ['a83c', 'b83c'],
                        'wwpns': ['c05076de3300a83c', 'c05076de3300b83c'],
                        'phy_to_virt_initiators': {
                            'c05076de3300a83c': 'c05076de33002641',
                            'c05076de3300b83c': 'c05076de33002641'
                            },
                        'host': 'fakehos1_fakeuser',
                        'fcp_paths': 2,
                        'fcp_template_id': template_id}
            self.assertDictEqual(expected, connector)

            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('b83c')
            self.assertEqual('FAKEUSER', userid)
            self.assertEqual(0, conn)
            self.assertEqual(1, reserved)
            self.assertEqual(template_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
            self._delete_from_template_table(template_id_list)

    def test_get_volume_connector_reserve_with_error(self):
        """The specified FCP template doesn't exist, should raise error."""
        assigner_id = 'fakeuser'
        fcp_template_id = '0001'
        sp_name = 'v7k60'
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               "fcp_template_id 0001 doesn't exist.",
                               self.volumeops.get_volume_connector,
                               assigner_id, True, fcp_template_id, sp_name)

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
        # insert data into tempalte
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('c123', '', 0, 0, '20076D8500005182',
                          '20076D8500005181', '27', 'active', 'owner1',
                          template_id),
                         ('d123', '', 0, 0, '20076D8500005183',
                          '20076D8500005181', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        wwpns = ['20076d8500005182', '20076d8500005183']
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert data into template_fcp_mapping table
        template_fcp = [('c123', template_id, 0),
                        ('d123', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)

        try:
            self.volumeops.attach(connection_info)
            mock_dedicate.assert_has_calls([mock.call('c123', 'USER1'),
                                            mock.call('d123', 'USER1')])
            mock_add_disk.assert_has_calls([mock.call(['c123', 'd123'],
                                                      'USER1', wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz')])
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

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
                           'assigner_id': 'user2',
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
        fcp_info_list = [('c123', 'user1', 0, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('d123', 'user1', 0, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.attach(connection_info)
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('c123')
            self.assertEqual(userid, 'USER2')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 1)
            self.assertEqual(tmpl_id, '')
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('d123')
            self.assertEqual(userid, 'USER2')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 1)
            self.assertEqual(tmpl_id, '')
            self.assertFalse(mock_dedicate.called)
            self.assertFalse(mock_add_disk.called)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

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
                    'Owner: NONE']
        mock_fcp_info.return_value = fcp_list
        mock_check.return_value = True
        wwpns = ['20076d8500005182', '20076d8500005183']
        fcp_info_list = [('c123', 'user1', 2, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('d123', 'user1', 2, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.attach(connection_info)
            self.assertFalse(mock_dedicate.called)
            mock_add_disk.assert_has_calls([mock.call(['c123', 'd123'],
                                                      'USER1', wwpns,
                                                      '2222', False, 'rhel7',
                                                      '/dev/sdz')])

        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

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
        get_fcp_usage.return_value = ('user1', 0, 0, '')
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
        # set connections of f83c to 1
        # left connections of f84c to 0
        fcp_info_list = [('f83c', 'user1', 1, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('f84c', 'user1', 0, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            get_fcp_usage.return_value = ('use1', 0, 0, '')
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
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach(self, mock_undedicate, mock_remove_disk, mock_check,
                    mock_fcp_info):
        """Test detach API."""
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
        fcp_info_list = [('183c', 'user1', 0, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('283c', 'user1', 1, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.detach(connection_info)
            mock_undedicate.assert_has_calls([mock.call('183c', 'USER1'),
                                              mock.call('283c', 'USER1')])
            mock_remove_disk.assert_has_calls([mock.call(['183c', '283c'],
                                                         'USER1', wwpns,
                                                         '2222', True, 'rhel7',
                                                         '/dev/sdz', 0)])
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('183c')
            self.assertEqual(userid, 'user1')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 0)
            self.assertEqual(tmpl_id, '')
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('283c')
            self.assertEqual(userid, 'user1')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 0)
            self.assertEqual(tmpl_id, '')
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_root_volume_detach(self, mock_undedicate, mock_remove_disk,
                                mock_check, mock_fcp_info):
        """Test detach root volume."""
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
        fcp_info_list = [('183c', 'user1', 0, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('283c', 'user1', 1, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            self.assertFalse(mock_remove_disk.called)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_update_connections_only_detach(self, mock_undedicate,
            mock_remove_disk, mock_check, mock_fcp_info):
        """Test only update connections when detach volume."""
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
        fcp_info_list = [('183c', 'user1', 0, 1, 'c05076de3300011c',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('283c', 'user1', 1, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            self.assertFalse(mock_remove_disk.called)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._remove_disks")
    @mock.patch("zvmsdk.volumeop.FCPVolumeManager._undedicate_fcp")
    def test_detach_no_undedicate(self, mock_undedicate, mock_remove_disk,
                                  mock_check):
        """Test no undedidicate action is called when detach."""
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
        fcp_info_list = [('283c', 'user1', 2, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)

        try:
            self.volumeops.detach(connection_info)
            self.assertFalse(mock_undedicate.called)
            mock_remove_disk.assert_called_once_with(['283c'], 'USER1',
                                                     ['1111'], '2222',
                                                     False, 'rhel7',
                                                     '/dev/sdz', 1)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_update_statistics_usage(self):
        """ Test for _update_statistics_usage()
            is included in test_get_all_fcp_usage_xxx()
        """
        pass

    def test_update_raw_fcp_usage(self):
        """ Test for _update_raw_fcp_usage()
            is included in test_get_all_fcp_usage_xxx()
        """
        pass

    def test_get_fcp_usage(self):
        """Test get_fcp_usage"""
        template_id = 'fakehost-1111-1111-1111-111111111111'
        # reserved == 1, connections == 2, assigner_id == 'user1'
        fcp_info_list = [('283c', 'user1', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp (fcp_id, assigner_id, "
                             "connections, reserved, wwpn_npiv, wwpn_phy, "
                             "chpid, state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)
        try:
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('283c')
            self.assertEqual(userid, 'user1')
            self.assertEqual(reserved, 1)
            self.assertEqual(conns, 2)
            self.assertEqual(template_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_set_fcp_usage(self):
        """Test set_fcp_usage"""
        template_id = 'fakehost-1111-1111-1111-111111111111'
        # reserved == 1, connections == 2, assigner_id == 'user1'
        fcp_info_list = [('283c', 'user1', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp (fcp_id, assigner_id, "
                             "connections, reserved, wwpn_npiv, wwpn_phy, "
                             "chpid, state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)
        try:
            # change reserved to 0 and connections to 3
            new_tmpl_id = 'newhost-1111-1111-1111-111111111111'
            self.volumeops.set_fcp_usage('283c', 'user2', 0, 3, new_tmpl_id)
            userid, reserved, conns, tmpl_id = self.volumeops.get_fcp_usage('283c')
            self.assertEqual(userid, 'user2')
            self.assertEqual(reserved, 0)
            self.assertEqual(conns, 3)
            self.assertEqual(new_tmpl_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    @mock.patch("zvmsdk.volumeop.FCPManager.decrease_fcp_usage")
    def test_rollback_dedicated_fcp(self, mock_decrease_fcp_usage):
        fcp_list = ['1a10', '1b10']
        assigner_id = 'test_assigner'
        all_fcp_list = ['1a10', '1a11', '1b10', '1b11']
        mock_decrease_fcp_usage.return_value = 2

        fcp_info_list = [('1a10', assigner_id, 1, 0, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          ''),
                         ('1a11', assigner_id, 1, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          ''),
                         ('1b10', assigner_id, 1, 0, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          ''),
                         ('1b11', assigner_id, 1, 1, 'c05076de3300011d',
                          'c05076de33002641', '27', 'active', 'owner2',
                          ''),
                         ]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            self.volumeops._rollback_dedicated_fcp(fcp_list, assigner_id, all_fcp_list)
            assigner_id_1, reserved_1, *_ = self.db_op.get_usage_of_fcp("1a10")
            assigner_id_2, reserved_2, *_ = self.db_op.get_usage_of_fcp("1a11")
            assigner_id_3, reserved_3, *_ = self.db_op.get_usage_of_fcp("1b10")
            assigner_id_4, reserved_4, *_ = self.db_op.get_usage_of_fcp("1b11")
            self.assertEqual(0, reserved_1)
            self.assertEqual(1, reserved_2)
            self.assertEqual(0, reserved_3)
            self.assertEqual(1, reserved_4)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
