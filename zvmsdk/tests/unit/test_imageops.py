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

# from zvmsdk.config import CONF
from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import imageops
from zvmsdk import utils as zvmutils
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKImageOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._image_ops = imageops.get_imageops()
        self._pathutil = zvmutils.PathUtils()

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
        self.assertEqual(ret, '3338')

    @mock.patch.object(zvmclient.XCATClient, 'image_import')
    def test_image_import_xcat(self, image_import):
        url = 'file:///path/to/image/file'
        image_meta = {'os_version': 'rhel7.2',
                      'md5sum': 'e34166f61130fc9221415d76298d7987'}
        remote_host = 'image@192.168.99.1'
        self._image_ops.image_import(url, image_meta=image_meta,
                                     remote_host=remote_host)
        image_import.assert_called_once_with('/path/to/image/file',
                                             'rhel7.2',
                                             remote_host=remote_host)

    @mock.patch.object(zvmclient.XCATClient, 'image_query')
    def test_image_query(self, image_query):
        imagekeyword = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self._image_ops.image_query(imagekeyword)
        image_query.assert_called_once_with(imagekeyword)

    @mock.patch.object(zvmclient.XCATClient, 'image_delete')
    def test_image_delete(self, image_delete):
        image_name = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self._image_ops.image_delete(image_name)
        image_delete.assert_called_once_with(image_name)
