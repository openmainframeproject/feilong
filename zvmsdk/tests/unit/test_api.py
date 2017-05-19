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
    def test_get_vm_info(self, ginfo):
        self.api.get_vm_info('fakevm')
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

    @mock.patch("zvmsdk.vmops.VMOps.guest_create")
    def test_guest_create(self, create_vm):
        userid = 'userid'
        vcpus = 1
        memory = 1024
        root_disk_size = 3338
        eph_disks = []

        self.api.guest_create(userid, vcpus, memory, root_disk_size, eph_disks)
        create_vm.assert_called_once_with(userid, vcpus, memory,
                                          root_disk_size, eph_disks)

    @mock.patch("zvmsdk.imageops.ImageOps.image_query")
    def test_image_query(self, image_query):
        imagekeyword = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self.api.image_query(imagekeyword)
        image_query.assert_called_once_with(imagekeyword)
