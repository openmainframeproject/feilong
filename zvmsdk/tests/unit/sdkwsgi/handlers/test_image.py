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

import datetime
import jwt
import mock
import unittest

from zvmsdk import exception
from zvmsdk import config
from zvmsdk.sdkwsgi.handlers import image
from zvmsdk.sdkwsgi import util


CONF = config.CONF

FAKE_UUID = '00000000-0000-0000-0000-000000000000'


def set_conf(section, opt, value):
    CONF[section][opt] = value


class FakeResp(object):
    def __init__(self):
        self.body = {}


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.response = FakeResp()
        self.__name__ = ''

    def __getitem__(self, name):
        return self.headers


class HandlersImageTest(unittest.TestCase):

    def setUp(self):
        set_conf('wsgi', 'auth', 'none')
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(image.ImageAction, 'create')
    def test_image_create(self, mock_create):
        body_str = """{"image": {"image_name": "46a4aea3-54b6-4b1c",
                                 "url": "file:///tmp/test.img",
                                 "image_meta": {
                                 "os_version": "rhel7.2",
                                 "md5sum": "12345678912345678912345678912345"
                                 },
                                 "remotehost": "hostname"
                                }
                      }"""
        self.req.body = body_str
        body = {
                  'image':
                  {
                       'remotehost': 'hostname',
                       'image_meta':
                       {
                            'os_version': 'rhel7.2',
                            'md5sum': '12345678912345678912345678912345'
                       },
                       'url': 'file:///tmp/test.img',
                       'image_name': '46a4aea3-54b6-4b1c'
                   }
               }
        mock_create.return_value = ''

        image.image_create(self.req)
        mock_create.assert_called_once_with(body=body)

    @mock.patch.object(image.ImageAction, 'create')
    def test_image_create_rhcos(self, mock_create):
        body_str = """{"image": {"image_name": "46a4aea3-54b6-4b1c",
                                 "url": "file:///tmp/test.img",
                                 "image_meta": {
                                 "os_version": "rhcos4.2",
                                 "md5sum": "12345678912345678912345678912345",
                                 "disk_type": "DASD"
                                 },
                                 "remotehost": "hostname"
                                }
                      }"""
        self.req.body = body_str
        body = {
                  'image':
                  {
                       'remotehost': 'hostname',
                       'image_meta':
                       {
                            'os_version': 'rhcos4.2',
                            'md5sum': '12345678912345678912345678912345',
                            "disk_type": "DASD"
                       },
                       'url': 'file:///tmp/test.img',
                       'image_name': '46a4aea3-54b6-4b1c'
                   }
               }
        mock_create.return_value = ''

        image.image_create(self.req)
        mock_create.assert_called_once_with(body=body)

    def test_image_create_invalidname(self):
        body_str = '{"image": {"version": ""}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    def test_image_create_invalid_os_version(self):
        body_str = """{"image": {"image_name": "46a4aea3-54b6-4b1c",
                         "url": "file:///tmp/test.img",
                         "image_meta": {
                         "os_version": "rhel2.2",
                         "md5sum": "12345678912345678912345678912345"
                         }
                        }
              }"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    def test_image_create_invalid_rhcos_os_version(self):
        body_str = """{"image": {"image_name": "46a4aea3-54b6-4b1c",
                         "url": "file:///tmp/test.img",
                         "image_meta": {
                         "os_version": "rhcos43",
                         "md5sum": "12345678912345678912345678912345",
                         "disk_type": "DASD"
                         }
                        }
              }"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    def test_image_create_rhcos_invalid_disktype(self):
        body_str = """{"image": {"image_name": "46a4aea3-54b6-4b1c",
                         "url": "file:///tmp/test.img",
                         "image_meta": {
                         "os_version": "rhcos4.2",
                         "md5sum": "12345678912345678912345678912345",
                         "disk_type": "any"
                         }
                        }
              }"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    def test_image_create_invalid_url(self):
        # FIXME: need url format validation
        pass

    def test_image_create_invalid_image_meta(self):
        # miss os_version param
        body_str = """{"image": {"url": "file:///tmp/test.img",
                                 "image_meta": {
                                 "md5sum": "12345678912345678912345678912345"
                                 }
                                }
                      }"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    def test_image_create_invalid_image_meta_md5sum(self):
        # md5sum is less than 32 chars
        body_str = """{"image": {"url": "file://tmp/test.img",
                                 "image_meta": {
                                 "os_version": "rhel7.2",
                                 "md5sum": "2345678912345678912345678912345"
                                 }
                                }
                      }"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, image.image_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(image.ImageAction, 'get_root_disk_size')
    def test_image_get_root_disk_size(self, mock_get, mock_name):
        mock_name.return_value = 'dummy'
        mock_get.return_value = '100'
        image.image_get_root_disk_size(self.req)
        mock_get.assert_called_once_with(self.req, 'dummy')

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(image.ImageAction, 'delete')
    def test_image_delete(self, mock_delete, mock_name):
        mock_delete.return_value = ''
        mock_name.return_value = 'dummy'

        image.image_delete(self.req)
        mock_delete.assert_called_once_with('dummy')

    @mock.patch.object(image.ImageAction, 'query')
    def test_image_query(self, mock_query):
        mock_query.return_value = '[]'
        self.req.GET = {}
        self.req.GET['imagename'] = 'image1'
        image.image_query(self.req)
        mock_query.assert_called_once_with(self.req, 'image1')

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(image.ImageAction, 'export')
    def test_image_export(self, mock_export, mock_get):
        mock_export.return_value = '{}'
        body_str = """{"location":{
                                    "dest_url": "file:///tmp/images/image1",
                                    "remote_host": "192.168.12.34"
                                  }
                      }"""
        body = {u'location': {u'dest_url': u'file:///tmp/images/image1',
                              u'remote_host': u'192.168.12.34'}}
        fake_image_name = '46a4aea3-54b6-4b1c'
        mock_get.return_value = fake_image_name
        self.req.body = body_str
        image.image_export(self.req)
        mock_export.assert_called_once_with(fake_image_name,
                                            body=body)
