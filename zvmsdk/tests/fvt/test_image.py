#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2018 IBM Corp.
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
import shutil
import tempfile

from zvmsdk.tests.fvt import base
from zvmsdk import config
from zvmsdk import utils


CONF = config.CONF


class ImageTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(ImageTestCase, self).__init__(methodName)
        self.dummy_image_fname = "image1"

    def _import_dummy_image(self):
        image_fname = "image1"
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        image_fpath = '/'.join([tempDir, image_fname])
        utils.make_dummy_image(image_fpath)

        try:
            resp = self.client.image_import(image_fpath, "rhel7.2")
        finally:
            shutil.rmtree(tempDir)

        return resp

    def test_image_create_empty_body(self):
        body = {}
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_image_create_invalid_body(self):
        body = '{"dummy": {"uuid": "1"}}'
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_image_create_invalid_os_version(self):
        image_fname = "image1"
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        image_fpath = '/'.join([tempDir, image_fname])
        url = "file://" + image_fpath
        image_meta = '''{"os_version": "rhel8.2"}'''
        body = """{"image": {"image_name": "%s",
                             "url": "%s",
                             "image_meta": %s}}""" % (image_fname, url,
                                                      image_meta)
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)
        shutil.rmtree(tempDir)

    def test_image_get_not_valid_resource(self):
        resp = self.client.api_request(url='/images/image1/root')
        self.assertEqual(404, resp.status_code)

    def test_image_create_duplicate(self):
        resp = self._import_dummy_image()
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.image_delete, self.dummy_image_fname)

        resp = self._import_dummy_image()
        self.assertEqual(409, resp.status_code)

    def test_image_export_not_exist(self):
        # image not created yet
        resp = self.client.image_export("dummy")
        self.assertEqual(404, resp.status_code)

    def test_image_query_not_exist(self):
        resp = self.client.image_query("dummy")
        self.assertEqual(404, resp.status_code)

    def test_image_delete_not_exist(self):
        resp = self.client.image_delete("dummy")
        self.assertEqual(200, resp.status_code)

    def test_image_get_root_disk_size_not_exist(self):
        resp = self.client.image_get_root_disk_size(self.dummy_image_fname)
        self.assertEqual(404, resp.status_code)

    def test_image_create_delete(self):
        """Senario tests for image operations."""
        resp = self._import_dummy_image()
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.image_delete, self.dummy_image_fname)

        resp = self.client.image_query(self.dummy_image_fname)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_query', resp.content)

        resp = self.client.image_get_root_disk_size(self.dummy_image_fname)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_get_root_disk_size',
                                   resp.content)

        resp = self.client.image_export(self.dummy_image_fname)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_export', resp.content)
