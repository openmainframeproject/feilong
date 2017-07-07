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
import uuid

from zvmsdk import config
from zvmsdk.tests.functional import base
from zvmsdk import utils


CONF = config.CONF


class SDKAPIImageTestCase(base.SDKAPIBaseTestCase):

    def test_image_operations(self):
        """ Import a image, query the existence and then delete it"""
        image_fname = str(uuid.uuid1())
        image_fpath = ''.join([CONF.image.temp_path, image_fname])
        os.system('touch %s' % image_fpath)
        url = "file://" + image_fpath
        image_meta = {'os_version': 'rhel7.2'}
        self.sdkapi.image_import(url, image_meta, utils.get_host())

        query_result = self.sdkapi.image_query(image_fname)
        expect_result = ['rhel7.2-s390x-netboot-%s'
                         % image_fname.replace('-', '_')]
        self.assertEqual(query_result, expect_result)

        self.sdkapi.image_delete(query_result[0])
        query_result_after_delete = self.sdkapi.image_query(image_fname)
        expect_result_after_delete = []
        self.assertEqual(query_result_after_delete,
                         expect_result_after_delete)
        os.system('rm -f %s' % image_fpath)
