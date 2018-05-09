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

from zvmsdk import api
from zvmsdk import exception
from zvmsdk.tests.unit import base


class SDKAPITestCase(base.SDKTestCase):
    """Testcases for compute APIs."""
    def setUp(self):
        super(SDKAPITestCase, self).setUp()
        self.api = api.SDKAPI()
        self._vmops = mock.MagicMock()

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.api, api.SDKAPI))

    @mock.patch("zvmsdk.vmops.VMOps.get_info")
    def test_guest_get_info(self, ginfo):
        self.api.guest_get_info('fakevm')
        ginfo.assert_called_once_with('fakevm')

    @mock.patch("zvmsdk.vmops.VMOps.guest_deploy")
    def test_guest_deploy(self, guest_deploy):
        user_id = 'fakevm'
        image_name = 'fakeimg'
        transportfiles = '/tmp/transport.tgz'
        vdev = '0100'
        self.api.guest_deploy(user_id, image_name,
                              transportfiles=transportfiles,
                              vdev=vdev)
        guest_deploy.assert_called_with(user_id, image_name, transportfiles,
                                        None, vdev)

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
        userid = 'userid'
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'
        max_cpu = 10
        max_mem = '4G'

        self.api.guest_create(userid, vcpus, memory, disk_list,
                              user_profile, max_cpu, max_mem)
        create_vm.assert_called_once_with(userid, vcpus, memory, disk_list,
                                          user_profile, max_cpu, max_mem)

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create_with_default_max_cpu_memory(self, create_vm):
        userid = 'userid'
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'

        self.api.guest_create(userid, vcpus, memory, disk_list,
                              user_profile)
        create_vm.assert_called_once_with(userid, vcpus, memory, disk_list,
                                          user_profile, 32, '64G')

    @mock.patch("zvmsdk.imageops.ImageOps.image_query")
    def test_image_query(self, image_query):
        imagekeyword = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self.api.image_query(imagekeyword)
        image_query.assert_called_once_with(imagekeyword)

    @mock.patch("zvmsdk.vmops.VMOps.delete_vm")
    def test_guest_delete(self, delete_vm):
        userid = 'userid'
        self.api.guest_delete(userid)
        delete_vm.assert_called_once_with(userid)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_stats")
    def test_guest_inspect_cpus_list(self, inspect_stats):
        userid_list = ["userid1", "userid2"]
        self.api.guest_inspect_stats(userid_list)
        inspect_stats.assert_called_once_with(userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_stats")
    def test_guest_inspect_cpus_single(self, inspect_stats):
        userid_list = "userid1"
        self.api.guest_inspect_stats(userid_list)
        inspect_stats.assert_called_once_with(["userid1"])

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_vnics")
    def test_guest_inspect_vnics_list(self, inspect_vnics):
        userid_list = ["userid1", "userid2"]
        self.api.guest_inspect_vnics(userid_list)
        inspect_vnics.assert_called_once_with(userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_vnics")
    def test_guest_inspect_vnics_single(self, inspect_vnics):
        userid_list = "userid1"
        self.api.guest_inspect_vnics(userid_list)
        inspect_vnics.assert_called_once_with(["userid1"])

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_guest_stop(self, gs):
        userid = 'fakeuser'
        self.api.guest_stop(userid)
        gs.assert_called_once_with(userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_guest_stop_with_timeout(self, gs):
        userid = 'fakeuser'
        self.api.guest_stop(userid, timeout=300)
        gs.assert_called_once_with(userid, timeout=300)

    @mock.patch("zvmsdk.vmops.VMOps.guest_softstop")
    def test_guest_softstop(self, gss):
        userid = 'fakeuser'
        self.api.guest_softstop(userid, timeout=300)
        gss.assert_called_once_with(userid, timeout=300)

    @mock.patch("zvmsdk.vmops.VMOps.guest_pause")
    def test_guest_pause(self, gp):
        userid = 'fakeuser'
        self.api.guest_pause(userid)
        gp.assert_called_once_with(userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_unpause")
    def test_guest_unpause(self, gup):
        userid = 'fakeuser'
        self.api.guest_unpause(userid)
        gup.assert_called_once_with(userid)

    @mock.patch("zvmsdk.vmops.VMOps.guest_config_minidisks")
    def test_guest_process_additional_disks(self, config_disks):
        userid = 'userid'
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        self.api.guest_config_minidisks(userid, disk_list)
        config_disks.assert_called_once_with(userid, disk_list)

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
        userid = 'testuid'
        disk_list = [{'size': '1g'}]
        self.api.guest_create_disks(userid, disk_list)
        cds.assert_called_once_with(userid, disk_list)

    @mock.patch("zvmsdk.vmops.VMOps.create_disks")
    def test_guest_add_disks_nothing_to_do(self, cds):
        self.api.guest_create_disks('userid', [])
        cds.assert_not_called()

    @mock.patch("zvmsdk.vmops.VMOps.delete_disks")
    def test_guest_delete_disks(self, dds):
        userid = 'testuid'
        vdev_list = ['0102', '0103']
        self.api.guest_delete_disks(userid, vdev_list)
        dds.assert_called_once_with(userid, vdev_list)

    @mock.patch("zvmsdk.vmops.VMOps.live_resize_cpus")
    def test_guest_live_resize_cpus(self, live_resize_cpus):
        userid = "testuid"
        cpu_cnt = 3
        self.api.guest_live_resize_cpus(userid, cpu_cnt)
        live_resize_cpus.assert_called_once_with(userid, cpu_cnt)

    @mock.patch("zvmsdk.vmops.VMOps.resize_cpus")
    def test_guest_resize_cpus(self, resize_cpus):
        userid = "testuid"
        cpu_cnt = 3
        self.api.guest_resize_cpus(userid, cpu_cnt)
        resize_cpus.assert_called_once_with(userid, cpu_cnt)
