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
import webob.exc

from zvmsdk.sdkwsgi.handlers import guest
from zvmsdk.sdkwsgi import util


FAKE_UUID = '00000000-0000-0000-0000-000000000000'


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}

    def __getitem__(self, name):
        return self.headers


class HandlersGuestTest(unittest.TestCase):

    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(guest.VMAction, 'list')
    def test_guest_list(self, mock_list):

        guest.guest_list(self.req)
        self.assertTrue(mock_list.called)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMAction, 'start')
    def test_guest_start(self, mock_action,
                        mock_uuid):
        self.req.body = '{"start": "None"}'

        mock_uuid.return_value = FAKE_UUID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMAction, 'stop')
    def test_guest_stop(self, mock_action,
                        mock_uuid):
        self.req.body = '{"stop": "None"}'

        mock_uuid.return_value = FAKE_UUID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_invalid_action(self, mock_uuid):
        self.req.body = '{"fake": "None"}'

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(webob.exc.HTTPBadRequest, guest.guest_action,
                          self.req)

    @mock.patch.object(guest.VMAction, 'create')
    def test_guest_create(self, mock_create):
        body_str = '{"name": "name1"}'
        self.req.body = body_str

        guest.guest_create(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(body)
