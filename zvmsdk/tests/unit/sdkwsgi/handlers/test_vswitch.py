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
from zvmsdk.sdkwsgi.handlers import vswitch
from zvmsdk.sdkwsgi import util


FAKE_UUID = '00000000-0000-0000-0000-000000000000'


class FakeResp(object):
    def __init__(self):
        self.body = {}


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.__name__ = ''
        self.response = FakeResp()

    def __getitem__(self, name):
        return self.headers


class HandlersGuestTest(unittest.TestCase):

    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(vswitch.VswitchAction, 'list')
    def test_vswitch_list(self, mock_list):

        mock_list.return_value = ''
        vswitch.vswitch_list(self.req)
        self.assertTrue(mock_list.called)

    @mock.patch.object(vswitch.VswitchAction, 'create')
    def test_vswitch_create(self, mock_create):
        body_str = '{"vswitch": {"name": "name1"}}'
        self.req.body = body_str

        vswitch.vswitch_create(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(body=body)

    def test_vswitch_create_invalidname(self):
        body_str = '{"vswitch": {"name": ""}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(vswitch.VswitchAction, 'delete')
    def test_vswitch_delete(self, mock_delete, mock_name):
        mock_name.return_value = 'vsw1'

        vswitch.vswitch_delete(self.req)
        mock_delete.assert_called_once_with('vsw1')
