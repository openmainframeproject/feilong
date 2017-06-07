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
        vdev = None
        self.api.guest_deploy(user_id, image_name, transportfiles, vdev)
        guest_deploy.assert_called_with(user_id, image_name, transportfiles,
                                        vdev)

    @mock.patch("zvmsdk.imageops.ImageOps.image_import")
    def test_image_import(self, image_import):
        image_file_path = "/install/temp/test.img"
        os_version = "1.0"
        self.api.image_import(image_file_path, os_version)
        image_import.assert_called_once_with(image_file_path, os_version)

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

    @mock.patch("zvmsdk.vmops.VMOps.guest_stop")
    def test_guest_stop(self, gs):
        userid = 'fakeuser'
        self.api.guest_stop(userid)
        gs.assert_called_once_with(userid, 0, 10)
