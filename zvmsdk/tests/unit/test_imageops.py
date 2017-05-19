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
import os
import shutil
import tarfile
import xml

# from zvmsdk.config import CONF
from zvmsdk import client as zvmclient
from zvmsdk import imageops
from zvmsdk import utils as zvmutils
from zvmsdk.tests.unit import base


class SDKImageOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._image_ops = imageops.get_imageops()
        self._pathutil = zvmutils.PathUtils()

    @mock.patch.object(zvmclient.XCATClient, 'lsdef_image')
    def test_check_image_exist(self, lsdef_image):
        lsdef_image.return_value = {
                'info': [[u'rhel7.2-s390x-netboot-rhel72eckdbug1555_' +
                    'edbcfbb9_2e17_4876_befa_834f2f6b0f6c  (osimage)']],
                'node': [],
                'errorcode': [],
                'data': [],
                'error': []}
        image_uuid = 'rhel72eckdbug1555_edbcfbb9_2e17_4876_befa_834f2f6b0f6c'
        ret = self._image_ops.check_image_exist(image_uuid)
        self.assertEqual(ret, True)

    @mock.patch.object(zvmclient.XCATClient, 'lsdef_image')
    def test_get_image_name(self, lsdef_image):
        lsdef_image.return_value = {
                'info': [[u'rhel7.2-s390x-netboot-rhel72eckdbug1555_' +
                    'edbcfbb9_2e17_4876_befa_834f2f6b0f6c  (osimage)']],
                'node': [],
                'errorcode': [],
                'data': [],
                'error': []}
        image_uuid = 'rhel72eckdbug1555_edbcfbb9_2e17_4876_befa_834f2f6b0f6c'
        image_name = 'rhel7.2-s390x-netboot-rhel72eckdbug1555_' +\
                     'edbcfbb9_2e17_4876_befa_834f2f6b0f6c'
        ret = self._image_ops.get_image_name(image_uuid)
        self.assertEqual(ret, image_name)

    def test_get_image_path_by_name(self):
        fake_name = 'rhel7.2-s390x-netboot-fake_image_uuid'
        expected_path = '/install/netboot/rhel7.2/s390x/fake_image_uuid/' +\
                fake_name + '.img'
        ret = self._image_ops.get_image_path_by_name(fake_name)
        self.assertEqual(ret, expected_path)

    @mock.patch.object(zvmutils, 'execute')
    def test_image_get_root_disk_size(self, execute_cmd):
        fake_name = 'rhel7.2-s390x-netboot-fake_image_uuid'
        execute_cmd.return_value =\
            '00000000  78 43 41 54 20 43 4b 44  20 44 69 73 6b 20 49 6d  ' +\
            '|xCAT CKD Disk Im|\n' +\
            '00000010  61 67 65 3a 20 20 20 20  20 20 20 20 33 33 33 38  ' +\
            '|age:        3338|\n' +\
            '00000020  20 43 59 4c 20 48 4c 65  6e 3a 20 30 30 35 35 20  ' +\
            '| CYL HLen: 0055 |\n' +\
            '00000030  47 5a 49 50 3a 20 36 20  20 20 20 20 20 20 20 20  ' +\
            '|GZIP: 6         |\n' +\
            '00000040'

        ret = self._image_ops.image_get_root_disk_size(fake_name)
        self.assertEqual(ret, 3338)

    @mock.patch.object(xml.dom.minidom, 'Document')
    @mock.patch.object(xml.dom.minidom.Document, 'createElement')
    def test_generate_manifest_file(self, create_element, document):
        """
        image_meta = {
                u'id': 'image_uuid_123',
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': u'rhel7.2',
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                             u'provision_metuot'}
                }
        image_name = 'image_name_123'
        tmp_date_dir = 'tmp_date_dir'
        disk_file_name = 'asdf'
        manifest_path = os.getcwd()
        manifest_path = manifest_path + '/' + tmp_date_dir
        """
        pass

    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(tarfile, 'open')
    @mock.patch.object(tarfile.TarFile, 'add')
    @mock.patch.object(tarfile.TarFile, 'close')
    @mock.patch.object(shutil, 'copyfile')
    @mock.patch.object(os, 'chdir')
    def test_generate_image_bundle(self, change_dir,
                                   copy_file, close_file,
                                   add_file, tarfile_open,
                                   file_exist):
        time_stamp_dir = 'tmp_date_dir'
        image_name = 'test'
        spawn_path = '.'
        spawn_path = spawn_path + '/' + time_stamp_dir
        image_file_path = spawn_path + '/images/test.img'
        change_dir.return_value = None
        copy_file.return_value = None
        close_file.return_value = None
        add_file.return_value = None
        tarfile_open.return_value = tarfile.TarFile
        file_exist.return_value = True

        self._image_ops.generate_image_bundle(
                                    spawn_path, time_stamp_dir,
                                    image_name, image_file_path)
        tarfile_open.assert_called_once_with(spawn_path +
                                             '/tmp_date_dir_test.tar',
                                             mode='w')

    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(zvmclient.XCATClient, 'image_import')
    @mock.patch.object(zvmclient.XCATClient, 'check_space_imgimport_xcat')
    @mock.patch.object(imageops.ImageOps, 'generate_image_bundle')
    @mock.patch.object(imageops.ImageOps, 'generate_manifest_file')
    def test_image_import(self, generate_manifest_file,
                                generate_bundle_file,
                                check_space,
                                import_image,
                                file_exists):
        generate_manifest_file.return_value = './tmp_date_dir/manifest.xml'
        generate_bundle_file.return_value =\
                                './tmp_date_dir/tmp_date_dir_test.tar'
        check_space.return_value = None
        file_exists.return_value = True
        import_image.return_value = {'data': [['1.output line one'],
                                             ['2.output line2'],
                                             ['3.output line 3'],
                                             ['4.output line 3'],
                                             ['5.output line 5']]}
        image_file_path = './test/image-uuid'
        time_stamp_dir = self._pathutil.make_time_stamp()
        bundle_file_path = self._pathutil.get_bundle_tmp_path(time_stamp_dir)
        os_version = '7.2'
        image_meta = {
                u'id': 'image-uuid',
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': os_version,
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                               u'provision_method': u'netboot'}
                }
        self._image_ops.image_import(image_file_path, os_version)
        generate_manifest_file.assert_called_with(image_meta,
                                                  '0100.img',
                                                  '0100.img',
                                                  bundle_file_path)
