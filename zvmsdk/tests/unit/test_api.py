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
        url = "file:////install/temp/test.img"
        image_meta = {'os_version': "rhel6.7"}
        self.api.image_import(url, image_meta=image_meta)
        image_import.assert_called_once_with(url, image_meta=image_meta,
                                             remote_host=None)

    @mock.patch("zvmsdk.vmops.VMOps.create_vm")
    def test_guest_create(self, create_vm):
        userid = 'userid'
        vcpus = 1
        memory = 1024
        disk_list = []
        user_profile = 'profile'

        self.api.guest_create(userid, vcpus, memory, disk_list,
                              user_profile)
        create_vm.assert_called_once_with(userid, vcpus, memory, disk_list,
                                          user_profile)

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

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_cpus")
    def test_guest_inspect_cpus_list(self, inspect_cpus):
        userid_list = ["userid1", "userid2"]
        self.api.guest_inspect_cpus(userid_list)
        inspect_cpus.assert_called_once_with(userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_cpus")
    def test_guest_inspect_cpus_single(self, inspect_cpus):
        userid_list = "userid1"
        self.api.guest_inspect_cpus(userid_list)
        inspect_cpus.assert_called_once_with(["userid1"])

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_mem")
    def test_guest_inspect_mem_list(self, inspect_mem):
        userid_list = ["userid1", "userid2"]
        self.api.guest_inspect_mem(userid_list)
        inspect_mem.assert_called_once_with(userid_list)

    @mock.patch("zvmsdk.monitor.ZVMMonitor.inspect_mem")
    def test_guest_inspect_mem_single(self, inspect_mem):
        userid_list = "userid1"
        self.api.guest_inspect_mem(userid_list)
        inspect_mem.assert_called_once_with(["userid1"])

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
        gs.assert_called_once_with(userid, 0, 10)

    @mock.patch("zvmsdk.vmops.VMOps.guest_config_minidisks")
    def test_guest_process_additional_disks(self, config_disks):
        userid = 'userid'
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        self.api.guest_config_minidisks(userid, disk_list)
        config_disks.assert_called_once_with(userid, disk_list)

    @mock.patch("zvmsdk.vmops.VMOps.guest_start")
    def test_skip_api_input_check(self, gs):
        zapi = api.SDKAPI(skip_input_check=True)
        zapi.guest_start(1)
        gs.assert_called_once_with(1)

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_api_input_check_with_default_value(self, gs):
        self.api.guest_stop('fakeuser', 60)
        gs.assert_called_once_with('fakeuser', 60, 10)

    def test_api_input_check_failed(self):
        self.assertRaises(exception.ZVMInvalidInput, self.api.guest_start, 1)

    @mock.patch("zvmsdk.vmops.VMOps.get_definition_info")
    def test_api_input_check_with_keyword(self, gdi):
        self.api.guest_get_definition_info('uid', nic_coupled='1000')
        gdi.assert_called_once_with('uid', nic_coupled='1000')

    @mock.patch("zvmsdk.vmops.VMOps.get_definition_info")
    def test_api_input_check_with_invalid_keyword(self, gdi):
        self.assertRaises(exception.ZVMInvalidInput,
                          self.api.guest_get_definition_info, 'uid',
                          invalid='1000')

    @mock.patch("zvmsdk.vmops.VMOps.guest_start")
    def test_check_input_userid_length(self, gs):
        self.assertRaises(exception.ZVMInvalidInput, self.api.guest_start,
                          '123456789')

    @mock.patch("zvmsdk.vmops.VMOps.guest_start")
    def test_check_input_too_many_parameters(self, gs):
        self.assertRaises(exception.ZVMInvalidInput, self.api.guest_start,
                          'fakeuser', '12345678')

    @mock.patch("zvmsdk.imageops.ImageOps.image_delete")
    def test_image_delete(self, image_delete):
        image_name = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self.api.image_delete(image_name)
        image_delete.assert_called_once_with(image_name)
