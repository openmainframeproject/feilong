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


import os
import tempfile
import uuid

from zvmsdk import config
from zvmsdk.tests.functional import base
from zvmsdk import utils


CONF = config.CONF


class SDKAPIImageTestCase(base.SDKAPIBaseTestCase):

    def test_image_operations(self):
        """ Import a image, query the existence and then delete it"""
        image_fname = str(uuid.uuid1())
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        image_fpath = '/'.join([tempDir, image_fname])
        utils.make_dummy_image(image_fpath)
        url = "file://" + image_fpath
        image_meta = {'os_version': 'rhel7.2'}
        self.sdkapi.image_import(image_fname, url, image_meta,
                                 utils.get_host())

        os.system('rm -f %s' % image_fpath)

        query_result = self.sdkapi.image_query(image_fname)
        result_length = len(query_result)
        self.assertEqual(result_length, 1)

        image_size = self.sdkapi.image_get_root_disk_size(image_fname)
        self.assertEqual(image_size, u'0')

        export_tempDir = tempfile.mkdtemp()
        os.chmod(export_tempDir, 0o777)

        image_export_result = self.sdkapi.image_export(image_fname,
                                                       export_tempDir)

        self.assertEqual(image_export_result['image_name'], image_fname)
        self.assertEqual(image_export_result['image_path'], export_tempDir)
        self.assertEqual(image_export_result['os_version'],
                         image_meta['os_version'])

        # Verify after export, the source image has been deleted by default
        query_result_after_export = self.sdkapi.image_query(image_fname)
        expect_result_after_export = []
        self.assertEqual(query_result_after_export,
                         expect_result_after_export)

        # Remove the exported image
        os.system('rm -f %s' % export_tempDir)
