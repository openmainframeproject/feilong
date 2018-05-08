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

from zvmsdk.tests.sdkwsgi import base
from zvmsdk import config
from zvmsdk import utils
from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


CONF = config.CONF


class ImageTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(ImageTestCase, self).__init__(methodName)

        self.apibase = api_sample.APITestBase()
        # test change bind_port
        self.set_conf('sdkserver', 'bind_port', 3001)
        self.client = test_sdkwsgi.TestSDKClient()

    def setUp(self):
        super(ImageTestCase, self).setUp()
        self.record_logfile_position()

    def _image_create(self):
        image_fname = "image1"
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        image_fpath = '/'.join([tempDir, image_fname])
        utils.make_dummy_image(image_fpath)
        url = "file://" + image_fpath
        image_meta = '''{"os_version": "rhel7.2"}'''

        body = """{"image": {"image_name": "%s",
                             "url": "%s",
                             "image_meta": %s}}""" % (image_fname, url,
                                                      image_meta)

        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        shutil.rmtree(tempDir)
        return resp

    def _image_delete(self, image_name='image1'):
        url = '/images/%s' % image_name
        resp = self.client.api_request(url=url, method='DELETE')
        return resp

    def _image_get_root_disk_size(self, image_name='image1'):
        url = '/images/%s/root_disk_size' % image_name

        resp = self.client.api_request(url=url, method='GET')
        return resp

    def _image_query(self, image_name='image1'):
        url = '/images?imagename=%s' % image_name
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _image_export(self, image_name='image1'):
        url = '/images'
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        dest_url = ''.join(['file://', tempDir, '/', image_name])
        body = """{"image": {"image_name": "%s",
                             "dest_url": "%s",
                             "delete_source": False}}""" % (image_name,
                                                            dest_url)

        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
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
        resp = self._image_create()
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._image_create()
            self.assertEqual(409, resp.status_code)
        finally:
            self._image_delete()

    def test_image_export_not_exist(self):
        # image not created yet
        resp = self._image_export(image_name='dummy')
        self.assertEqual(404, resp.status_code)

    def test_image_query_not_exist(self):
        resp = self._image_query(image_name='dummy')
        self.assertEqual(404, resp.status_code)

    def test_image_delete_not_exist(self):
        resp = self._image_delete(image_name='dummy')
        self.assertEqual(404, resp.status_code)

    def test_image_get_root_disk_size_not_exist(self):
        resp = self._image_get_root_disk_size(image_name='dummy')
        self.assertEqual(404, resp.status_code)

    def test_image_create_delete(self):
        self._image_create()

        try:
            resp = self._image_query()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_image_query', resp.content)

            resp = self._image_get_root_disk_size()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_image_get_root_disk_size',
                                       resp.content)

            resp = self._image_export()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_image_export', resp.content)
        finally:
            # if delete failed, anyway we can't re-delete it because of failure
            self._image_delete()
