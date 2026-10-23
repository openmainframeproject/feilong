#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

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

from zvmsdk import config
from zvmsdk import imageops
from zvmsdk import utils as zvmutils
from zvmsdk.tests.unit import base


CONF = config.CONF
_SHA512 = ('cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921'
           'd36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81'
           'a538327af927da3e')


class SDKImageOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._image_ops = imageops.get_imageops()
        self._pathutil = zvmutils.PathUtils()

    @mock.patch("zvmsdk.smtclient.SMTClient.image_import")
    def test_image_import(self, image_import):
        image_name = '95a4da37-9f9b-4fb2-841f-f0bb441b7544'
        url = 'file:///path/to/image/file'
        image_meta = {'os_version': 'rhel7.2',
                      'checksum': _SHA512}
        remote_host = 'image@192.168.99.1'
        self._image_ops.image_import(image_name, url, image_meta,
                                     remote_host)
        image_import.assert_called_once_with(image_name,
                                             url,
                                             image_meta,
                                             remote_host)

    @mock.patch("zvmsdk.smtclient.SMTClient.image_query")
    def test_image_query(self, image_query):
        imagekeyword = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self._image_ops.image_query(imagekeyword)
        image_query.assert_called_once_with(imagekeyword)

    @mock.patch("zvmsdk.smtclient.SMTClient.image_delete")
    def test_image_delete(self, image_delete):
        image_name = 'eae09a9f_7958_4024_a58c_83d3b2fc0aab'
        self._image_ops.image_delete(image_name)
        image_delete.assert_called_once_with(image_name)

    @mock.patch("zvmsdk.smtclient.SMTClient.image_export")
    def test_image_export(self, image_export):
        image_name = 'testimage'
        dest_url = 'file:///path/to/export/image'
        self._image_ops.image_export(image_name, dest_url)
        image_export.assert_called_once_with(image_name, dest_url, None)
