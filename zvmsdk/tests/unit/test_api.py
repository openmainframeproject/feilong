#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2022 IBM Corp.
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
import six

from zvmsdk import api
from zvmsdk import exception
from zvmsdk.tests.unit import base
from zvmsdk import vmops


class SDKAPITestCase(base.SDKTestCase):
    """Testcases for compute APIs."""

    @classmethod
    def setUpClass(cls):
        super(SDKAPITestCase, cls).setUpClass()
        cls.userid = 'TESTUID'
        cls.userid_list = ["USERID1", "USERID2"]

    def setUp(self):
        super(SDKAPITestCase, self).setUp()
        vmops.VMOps.check_guests_exist_in_db = mock.MagicMock()
        patcher = mock.patch('zvmsdk.volumeop.FCPManager.sync_db')
        self.addCleanup(patcher.stop)
        self.mock_sync_db = patcher.start()
        self.api = api.SDKAPI()

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.api, api.SDKAPI))

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.edit_fcp_template")
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
        self.api.edit_fcp_template(tmpl_id, **kwargs)
        mock_edit_tmpl.assert_called_once_with(tmpl_id, **kwargs)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.get_fcp_templates")
    def test_get_fcp_templates(self, mock_get_tmpl):
        """ Test get_fcp_templates """
        tmpl_list = ['fake_id']
        assigner_id = 'fake_user'
        host_default = True
        default_sp_list = ['fake_sp']
        self.api.get_fcp_templates(template_id_list=tmpl_list,
                                   assigner_id=assigner_id,
                                   default_sp_list=default_sp_list,
                                   host_default=host_default)
        mock_get_tmpl.assert_called_once_with(template_id_list=tmpl_list,
                                              assigner_id=assigner_id,
                                              default_sp_list=default_sp_list,
                                              host_default=host_default)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.get_fcp_templates_details")
    def test_get_fcp_templates_details(self, mock_get_tmpl_details):
        """ Test get_fcp_templates_details """
        tmpl_list = ['fake_id']
        self.api.get_fcp_templates_details(template_id_list=tmpl_list,
                                           raw=True, statistics=True,
                                           sync_with_zvm=False)
        mock_get_tmpl_details.assert_called_once_with(template_id_list=['fake_id'],
                                                      raw=True,
                                                      statistics=True,
                                                      sync_with_zvm=False)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.delete_fcp_template")
    def test_delete_fcp_template(self, mock_del_tmpl):
        self.api.delete_fcp_template('fake_id')
        mock_del_tmpl.assert_called_once_with('fake_id')

    @mock.patch("zvmsdk.vmops.VMOps.get_power_state")
    def test_guest_get_power_state_real(self, gstate):
        self.api.guest_get_power_state_real(self.userid)
        gstate.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.vmops.VMOps.get_power_state")
    def test_guest_get_power_state(self, gstate, chk_uid):
        chk_uid.return_value = True
        self.api.guest_get_power_state(self.userid)
        chk_uid.assert_called_once_with(self.userid)
        gstate.assert_called_once_with(self.userid)

        chk_uid.reset_mock()
        gstate.reset_mock()
        chk_uid.return_value = False
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.api.guest_get_power_state, self.userid)
        chk_uid.assert_called_once_with(self.userid)
        gstate.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.get_info")
    def test_guest_get_info(self, ginfo):
        self.api.guest_get_info(self.userid)
        ginfo.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.get_definition_info")
    def test_guest_get_user_direct_(self, ginfo):
        ginfo.return_value = {'user_direct':
                              ['CPU 00 BASE',
                               'USER USERID1 PASSWORD 4096m ']}
        expected_value = {'user_direct':
                          ['CPU 00 BASE',
                           'USER USERID1 ****** 4096m ']}
        result = self.api.guest_get_user_direct(self.userid)
        ginfo.assert_called_once_with(self.userid)
        self.assertEqual(result, expected_value)

    @mock.patch("zvmsdk.vmops.VMOps.get_adapters_info")
    def test_guest_get_adapters_info(self, adapters_info):
        self.api.guest_get_adapters_info(self.userid)
        adapters_info.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_deploy")
    def test_guest_deploy(self, guest_deploy):
        user_id = 'fakevm'
        image_name = 'fakeimg'
        transportfiles = '/tmp/transport.tgz'
        vdev = '0100'
        self.api.guest_deploy(user_id, image_name,
                              transportfiles=transportfiles,
                              vdev=vdev)
        guest_deploy.assert_called_with(user_id.upper(), image_name,
                                        transportfiles, None, vdev,
                                        None, False)

    @mock.patch("zvmsdk.imageops.ImageOps.image_import")
    def test_image_import(self, image_import):
        image_name = '95a4da37-9f9b-4fb2-841f-f0bb441b7544'
        url = "file:///install/temp/test.img"
        image_meta = {'os_version': "rhel6.7"}
        self.api.image_import(image_name, url, image_meta)
        image_import.assert_called_once_with(image_name, url,
                                             image_meta,
                                             remote_host=None)

    @mock.patch("zvmsdk.imageops.ImageOps.image_export")
    def test_image_export(self, image_export):
        image_name = '95a4da37-9f9b-4fb2-841f-f0bb441b7544'
        dest_url = "file:///install/temp/test.img"
        self.api.image_export(image_name, dest_url)
        image_export.assert_called_once_with(image_name, dest_url,
                                             None)

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, '', '', '',
                                  '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_account(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        account = "dummy account"

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              account=account)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, account, None, '', '',
                                  '', '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_cpupool(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        cschedule = 'POOL1'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              cschedule=cschedule)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, cschedule, '',
                                  '', '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_share(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        cshare = 'RELATIVE 125'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              cshare=cshare)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, '', cshare, '',
                                  '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_rdomain(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        rdomain = 'Z15ONLY'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              rdomain=rdomain)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, '', '',
                                  rdomain, '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_pcif(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        pcif = '100:200'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              pcif=pcif)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, '', '',
                                  '', pcif)

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_comment(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        comment_list = ["dummy account", "this is a test"]

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem,
                              comment_list=comment_list)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, user_profile, max_cpu, max_mem,
                                  '', '', '', [], {}, '', comment_list, '',
                                  '', '', '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_default_profile(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = ''
        max_cpu = 10
        max_mem = '4G'
        base.set_conf('zvm', 'user_profile', 'abc')

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                  disk_list, 'abc', max_cpu, max_mem,
                                  '', '', '', [], {}, '', None, '', '', '',
                                  '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_no_disk_pool(self, create_vm):
        disk_list = [{'size': '1g', 'is_boot_disk': True,
                      'disk_pool': 'ECKD: eckdpool1'},
                     {'size': '1g', 'format': 'ext3'},
                     {'size': '1g', 'format': 'swap'}]
        vcpus = 1
        memory = 1024
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        base.set_conf('zvm', 'disk_pool', None)
        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.guest_create, self.userid, vcpus,
                          memory, disk_list, user_profile,
                          max_cpu, max_mem)
        create_vm.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_no_disk_pool_swap_only(self, create_vm):
        disk_list = [{'size': '1g', 'format': 'swap'}]
        vcpus = 1
        memory = 1024
        user_profile = 'profile'
        base.set_conf('zvm', 'disk_pool', None)
        base.set_conf('zvm', 'swap_force_mdisk', False)
        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                          disk_list, user_profile, 32, '64G',
                                          '', '', '', [], {}, '', None, '',
                                          '', '', '')

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_no_disk_pool_force_mdisk(self, create_vm):
        disk_list = [{'size': '1g', 'is_boot_disk': True,
                      'disk_pool': 'ECKD: eckdpool1'},
                     {'size': '1g', 'format': 'ext3'},
                     {'size': '1g', 'format': 'swap'}]
        vcpus = 1
        memory = 1024
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'
        # should be no side effect at all
        base.set_conf('zvm', 'swap_force_mdisk', True)
        base.set_conf('zvm', 'disk_pool', None)
        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.guest_create, self.userid, vcpus,
                          memory, disk_list, user_profile,
                          max_cpu, max_mem)
        create_vm.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_no_disk_pool_swap_only_force_mdisk(self, create_vm):
        disk_list = [{'size': '1g', 'format': 'swap'}]
        vcpus = 1
        memory = 1024
        user_profile = 'profile'
        base.set_conf('zvm', 'disk_pool', None)
        base.set_conf('zvm', 'swap_force_mdisk', True)
        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.guest_create, self.userid, vcpus,
                          memory, disk_list, user_profile)

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_default_max_cpu_memory(self, create_vm):
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'

        self.api.guest_create(self.userid, vcpus, memory, disk_list,
                              user_profile)
        create_vm.assert_called_once_with(self.userid, vcpus, memory,
                                          disk_list, user_profile, 32, '64G',
                                          '', '', '', [], {}, '', None, '',
                                          '', '', '')

    @mock.patch("zvmsdk.imageops.ImageOps.image_query")
    def test_image_query(self, image_query):
        imagekeyword = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self.api.image_query(imagekeyword)
        image_query.assert_called_once_with(imagekeyword)

    @mock.patch("zvmsdk.vmops.VMOps.delete_vm")
    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    def test_guest_delete(self, cge, delete_vm):
        cge.return_value = True
        self.api.guest_delete(self.userid)
        cge.assert_called_once_with(self.userid, raise_exc=False)
        delete_vm.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.delete_vm")
    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    def test_guest_delete_userid_in_lower_case(self, cge, delete_vm):
        cge.return_value = True
        self.api.guest_delete('testuid')
        cge.assert_called_once_with(self.userid, raise_exc=False)
        delete_vm.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    def test_guest_delete_not_exist(self, cge, cue):
        cge.return_value = False
        cue.return_value = False
        self.api.guest_delete(self.userid)
        cge.assert_called_once_with(self.userid, raise_exc=False)
        cue.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    def test_guest_delete_not_exist_in_db(self, cge, cue):
        cge.return_value = False
        cue.return_value = True
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.api.guest_delete, self.userid)
        cge.assert_called_once_with(self.userid, raise_exc=False)
        cue.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_stats")
    def test_guest_inspect_cpus_list(self, inspect_stats):
        self.api.guest_inspect_stats(self.userid_list)
        inspect_stats.assert_called_once_with(self.userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_stats")
    def test_guest_inspect_cpus_single(self, inspect_stats):
        self.api.guest_inspect_stats(self.userid)
        inspect_stats.assert_called_once_with([self.userid])

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_vnics")
    def test_guest_inspect_vnics_list(self, inspect_vnics):
        self.api.guest_inspect_vnics(self.userid_list)
        inspect_vnics.assert_called_once_with(self.userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_vnics")
    def test_guest_inspect_vnics_single(self, inspect_vnics):
        self.api.guest_inspect_vnics(self.userid)
        inspect_vnics.assert_called_once_with([self.userid])

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_guest_stop(self, gs):
        self.api.guest_stop(self.userid)
        gs.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_guest_stop_with_timeout(self, gs):
        self.api.guest_stop(self.userid, timeout=300)
        gs.assert_called_once_with(self.userid, timeout=300)

    @mock.patch("zvmsdk.vmops.VMOps.guest_softstop")
    def test_guest_softstop(self, gss):
        self.api.guest_softstop(self.userid, timeout=300)
        gss.assert_called_once_with(self.userid, timeout=300)

    @mock.patch("zvmsdk.vmops.VMOps.guest_pause")
    def test_guest_pause(self, gp):
        self.api.guest_pause(self.userid)
        gp.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_unpause")
    def test_guest_unpause(self, gup):
        self.api.guest_unpause(self.userid)
        gup.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_config_minidisks")
    def test_guest_process_additional_disks(self, config_disks):
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        self.api.guest_config_minidisks(self.userid, disk_list)
        config_disks.assert_called_once_with(self.userid, disk_list)

    @mock.patch("zvmsdk.imageops.ImageOps.image_delete")
    def test_image_delete(self, image_delete):
        image_name = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self.api.image_delete(image_name)
        image_delete.assert_called_once_with(image_name)

    def test_set_vswitch(self):
        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.vswitch_set,
                          "vswitch_name", unknown='fake_id')

    @mock.patch("zvmsdk.vmops.VMOps.create_disks")
    def test_guest_add_disks(self, cds):
        disk_list = [{'size': '1g'}]
        self.api.guest_create_disks(self.userid, disk_list)
        cds.assert_called_once_with(self.userid, disk_list)

    @mock.patch("zvmsdk.vmops.VMOps.create_disks")
    def test_guest_add_disks_no_disk_pool(self, cds):
        disk_list = [{'size': '1g', 'is_boot_disk': True,
                      'disk_pool': 'ECKD: eckdpool1'},
                     {'size': '1g', 'format': 'ext3'}]
        base.set_conf('zvm', 'disk_pool', None)
        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.guest_create_disks, self.userid, disk_list)
        cds.ssert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.create_disks")
    def test_guest_add_disks_nothing_to_do(self, cds):
        self.api.guest_create_disks('userid', [])
        cds.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.delete_disks")
    def test_guest_delete_disks(self, dds):
        vdev_list = ['0102', '0103']
        self.api.guest_delete_disks(self.userid, vdev_list)
        dds.assert_called_once_with(self.userid, vdev_list)

    @mock.patch("zvmsdk.vmops.VMOps.live_resize_cpus")
    def test_guest_live_resize_cpus(self, live_resize_cpus):
        cpu_cnt = 3
        self.api.guest_live_resize_cpus(self.userid, cpu_cnt)
        live_resize_cpus.assert_called_once_with(self.userid, cpu_cnt)

    @mock.patch("zvmsdk.vmops.VMOps.resize_cpus")
    def test_guest_resize_cpus(self, resize_cpus):
        cpu_cnt = 3
        self.api.guest_resize_cpus(self.userid, cpu_cnt)
        resize_cpus.assert_called_once_with(self.userid, cpu_cnt)

    @mock.patch("zvmsdk.vmops.VMOps.live_resize_memory")
    def test_guest_live_resize_mem(self, live_resize_memory):
        size = "1024M"
        self.api.guest_live_resize_mem(self.userid, size)
        live_resize_memory.assert_called_once_with(self.userid, size)

    @mock.patch("zvmsdk.vmops.VMOps.resize_memory")
    def test_guest_resize_mem(self, resize_memory):
        size = "2g"
        self.api.guest_resize_mem(self.userid, size)
        resize_memory.assert_called_once_with(self.userid, size)

    @mock.patch("zvmsdk.vmops.VMOps.guest_grow_root_volume")
    def test_guest_grow_root_volume(self, grow_root_volume):
        os_version = "RHEL7.8"
        self.api.guest_grow_root_volume(self.userid, os_version)
        grow_root_volume.assert_called_once_with(self.userid, os_version)

    @mock.patch("zvmsdk.networkops.NetworkOPS.grant_user_to_vswitch")
    def test_vswitch_grant_user(self, guv):
        self.api.vswitch_grant_user("testvsw", self.userid)
        guv.assert_called_once_with("testvsw", self.userid)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.attach_volume_to_instance")
    def test_volume_attach(self, mock_attach):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'assigner_id': 'user1'}
        self.api.volume_attach(connection_info)
        mock_attach.assert_called_once_with(connection_info)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI.volume_refresh_bootmap")
    def test_refresh_bootmap(self, mock_attach):
        fcpchannel = ['5d71']
        wwpn = ['5005076802100c1b', '5005076802200c1b']
        lun = '01000000000000'
        wwid = '600507640083826de00000000000605b'
        fcp_template_id = 'fake_tmpl_id'
        self.api.volume_refresh_bootmap(fcpchannel, wwpn, lun, wwid, fcp_template_id=fcp_template_id)
        mock_attach.assert_called_once_with(fcpchannel, wwpn, lun, wwid=wwid,
                                            transportfiles=None, guest_networks=None,
                                            fcp_template_id=fcp_template_id)

    @mock.patch("zvmsdk.volumeop.VolumeOperatorAPI."
                "detach_volume_from_instance")
    def test_volume_detach(self, mock_detach):
        connection_info = {'platform': 'x86_64',
                           'ip': '1.2.3.4',
                           'os_version': 'rhel7',
                           'multipath': False,
                           'target_wwpn': '1111',
                           'target_lun': '2222',
                           'zvm_fcp': 'b83c',
                           'assigner_id': 'user1'}
        self.api.volume_detach(connection_info)
        mock_detach.assert_called_once_with(connection_info)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_adapters_info")
    @mock.patch("zvmsdk.database.GuestDbOperator.add_guest_registered")
    @mock.patch("zvmsdk.database.NetworkDbOperator.switch_add_record")
    def test_guest_register(self, networkdb_add, guestdb_reg,
                              get_adapters_info, chk_usr):
        networkdb_add.return_value = ''
        guestdb_reg.return_value = ''
        adapters = [{'adapter_address': '1000',
                     'adapter_status': '02',
                     'lan_owner': 'SYSTEM',
                     'lan_name': 'VSC11590',
                     'mac_address': '02:55:36:EF:50:91',
                     'mac_ip_version': '4',
                     'mac_ip_address': '1.2.3.4'}]
        get_adapters_info.return_value = adapters
        chk_usr.return_value = True

        meta_data = 'rhel7'
        net_set = '1'
        port_macs = {'EF5091': '6e2ecc4f-14a2-4f33-9f12-5ac4a42f97e7',
                     '69FCF1': '389dee5e-7b03-405c-b1e8-7c9c235d1425'
                    }

        self.api.guest_register(self.userid, meta_data, net_set, port_macs)
        networkdb_add.assert_called_once_with(self.userid, '1000',
                                              '6e2ecc4f-14a2-4f33-9f12'
                                              '-5ac4a42f97e7',
                                              'VSC11590')
        guestdb_reg.assert_called_once_with(self.userid, 'rhel7', '1')
        get_adapters_info.assert_called_once_with(self.userid)
        chk_usr.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_adapters_info")
    @mock.patch("zvmsdk.database.GuestDbOperator.add_guest_registered")
    @mock.patch("zvmsdk.database.NetworkDbOperator.switch_add_record")
    def test_guest_register_invalid_portmacs(self, networkdb_add, guestdb_reg,
                              get_adapters_info, chk_usr):
        networkdb_add.return_value = ''
        guestdb_reg.return_value = ''
        adapters = [{'adapter_address': '1000',
                     'adapter_status': '02',
                     'lan_owner': 'SYSTEM',
                     'lan_name': 'VSC11590',
                     'mac_address': '02:55:36:EF:50:91',
                     'mac_ip_version': '4',
                     'mac_ip_address': '1.2.3.4'}]
        get_adapters_info.return_value = adapters
        chk_usr.return_value = True

        meta_data = 'rhel7'
        net_set = '1'
        port_macs = '6e2ecc4f-14a2-4f33-9f12-5ac4a42f97e7'

        self.assertRaises(exception.SDKInvalidInputFormat,
                          self.api.guest_register,
                          self.userid, meta_data, net_set, port_macs)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_adapters_info")
    @mock.patch("zvmsdk.database.GuestDbOperator.add_guest_registered")
    @mock.patch("zvmsdk.database.NetworkDbOperator.switch_add_record")
    def test_guest_register_no_port_macs(self, networkdb_add, guestdb_reg,
                              get_adapters_info, chk_usr):
        networkdb_add.return_value = ''
        guestdb_reg.return_value = ''
        adapters = [{'adapter_address': '1000',
                     'adapter_status': '02',
                     'lan_owner': 'SYSTEM',
                     'lan_name': 'VSC11590',
                     'mac_address': '02:55:36:EF:50:91',
                     'mac_ip_version': '4',
                     'mac_ip_address': '1.2.3.4'}]
        get_adapters_info.return_value = adapters
        chk_usr.return_value = True

        meta_data = 'rhel7'
        net_set = '1'

        self.api.guest_register(self.userid, meta_data, net_set)
        networkdb_add.assert_called_once_with(self.userid, '1000',
                                              None,
                                              'VSC11590')
        guestdb_reg.assert_called_once_with(self.userid, 'rhel7', '1')
        get_adapters_info.assert_called_once_with(self.userid)
        chk_usr.assert_called_once_with(self.userid)

    @mock.patch("zvmsdk.utils.check_userid_exist")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_adapters_info")
    @mock.patch("zvmsdk.database.GuestDbOperator.add_guest_registered")
    @mock.patch("zvmsdk.database.NetworkDbOperator.switch_add_record")
    @mock.patch("zvmsdk.database.GuestDbOperator.update_guest_by_userid")
    @mock.patch("zvmsdk.database.GuestDbOperator.get_comments_by_userid")
    @mock.patch("zvmsdk.database.GuestDbOperator.get_migrated_guest_list")
    @mock.patch("zvmsdk.database.GuestDbOperator.get_guest_by_userid")
    def test_guest_register_guest_in_db(self, get_guest, get_mig_guest,
                              get_comments, update_guest, networkdb_add,
                              guestdb_reg, get_adapters_info, chk_usr):
        get_guest.return_value = 'fake_guest'
        get_mig_guest.return_value = self.userid + ' other info'
        get_comments.return_value = {'migrated': 1}
        update_guest.return_value = ''
        # Below mocks shall not be called
        networkdb_add.return_value = ''
        guestdb_reg.return_value = ''
        get_adapters_info.return_value = []
        chk_usr.return_value = True

        meta_data = 'rhel7'
        net_set = '1'

        self.api.guest_register(self.userid, meta_data, net_set)
        get_guest.assert_called_once_with(self.userid)
        get_mig_guest.assert_called_once_with()
        get_comments.assert_called_once_with(self.userid)
        update_guest.assert_called_once_with(self.userid,
                                             comments={'migrated': 0})
        chk_usr.assert_called_once_with(self.userid)

        networkdb_add.assert_not_called()
        guestdb_reg.assert_not_called()
        get_adapters_info.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    @mock.patch("zvmsdk.database.NetworkDbOperator."
                "switch_delete_record_for_userid")
    @mock.patch("zvmsdk.database.GuestDbOperator.delete_guest_by_userid")
    def test_guest_deregister(self, guestdb_del, networkdb_del, chk_db):
        guestdb_del.return_value = ''
        networkdb_del.return_value = ''
        chk_db.return_value = True
        self.api.guest_deregister(self.userid)
        guestdb_del.assert_called_once_with(self.userid)
        networkdb_del.assert_called_once_with(self.userid)
        chk_db.assert_called_once_with(self.userid, raise_exc=False)

    @mock.patch("zvmsdk.vmops.VMOps.check_guests_exist_in_db")
    @mock.patch("zvmsdk.database.NetworkDbOperator."
                "switch_delete_record_for_userid")
    @mock.patch("zvmsdk.database.GuestDbOperator.delete_guest_by_userid")
    def test_guest_deregister_not_exists(self, guestdb_del,
                                         networkdb_del, chk_db):
        guestdb_del.return_value = ''
        networkdb_del.return_value = ''
        chk_db.return_value = False
        self.api.guest_deregister(self.userid)
        guestdb_del.assert_called_once_with(self.userid)
        networkdb_del.assert_called_once_with(self.userid)
        chk_db.assert_called_once_with(self.userid, raise_exc=False)

    @mock.patch("zvmsdk.hostops.HOSTOps.guest_list")
    def test_host_get_guest_list(self, guest_list):
        self.api.host_get_guest_list()
        guest_list.assert_called_once_with()

    @mock.patch("zvmsdk.hostops.HOSTOps.diskpool_get_volumes")
    def test_host_get_diskpool_volumes(self, diskpool_vols):
        base.set_conf('zvm', 'disk_pool', None)
        disk_pool = 'ECKD:IAS1PL'
        result = self.api.host_get_diskpool_volumes(disk_pool)
        diskpool_vols.assert_called_once_with('ECKD:IAS1PL')
        # Test disk_pool is None
        disk_pool = None
        try:
            self.api.host_get_diskpool_volumes(disk_pool)
        except Exception as exc:
            errmsg = ("Invalid disk_pool input None, disk_pool should be"
                      " configured for sdkserver.")
            result = errmsg in six.text_type(exc)
            self.assertEqual(result, True)
            pass

    @mock.patch("zvmsdk.hostops.HOSTOps.get_volume_info")
    def test_host_get_volume_info(self, volume_info):
        volume = 'VOLUM1'
        result = self.api.host_get_volume_info(volume)
        volume_info.assert_called_once_with(volume)
        # Test volume is None
        volume = None
        try:
            self.api.host_get_volume_info(volume)
        except Exception as exc:
            errmsg = ("Invalid volume input None, volume"
                      " must be specified.")
            result = errmsg in six.text_type(exc)
            self.assertEqual(result, True)
            pass

    @mock.patch("zvmsdk.hostops.HOSTOps.diskpool_get_info")
    def test_host_diskpool_get_info(self, dp_info):
        base.set_conf('zvm', 'disk_pool', None)
        results = self.api.host_diskpool_get_info()
        self.assertEqual(results['disk_total'], 0)
        self.assertEqual(results['disk_available'], 0)
        self.assertEqual(results['disk_used'], 0)
        dp_info.ssert_not_called()
