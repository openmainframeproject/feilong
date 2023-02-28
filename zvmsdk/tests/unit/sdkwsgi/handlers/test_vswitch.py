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

import datetime
import jwt
import mock
import unittest

from zvmsdk import exception
from zvmsdk import config
from zvmsdk.sdkwsgi.handlers import vswitch
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
        self.__name__ = ''
        self.response = FakeResp()

    def __getitem__(self, name):
        return self.headers


class HandlersGuestTest(unittest.TestCase):

    def setUp(self):
        set_conf('wsgi', 'auth', 'none')
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
        mock_create.return_value = {}
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234 abcd 123F",
                                   "port_type": 1,
                                   "controller": "*"}}"""
        self.req.body = body_str

        vswitch.vswitch_create(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(body=body)

    @mock.patch.object(vswitch.VswitchAction, 'create')
    def test_vswitch_create_with_userid_controller(self, mock_create):
        mock_create.return_value = {}
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234 abcd 123F",
                                   "port_type": 1,
                                   "controller": "userid01"}}"""
        self.req.body = body_str

        vswitch.vswitch_create(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(body=body)

    def test_vswitch_create_invalidname(self):
        body_str = '{"vswitch": {"name": "", "rdev": "1234"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_rdevlist(self):
        body_str = '{"vswitch": {"name": "name1", "rdev": "12345 sss"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(vswitch.VswitchAction, 'delete')
    def test_vswitch_delete(self, mock_delete, mock_name):
        mock_delete.return_value = {}
        mock_name.return_value = 'vsw1'

        vswitch.vswitch_delete(self.req)
        mock_delete.assert_called_once_with('vsw1')

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(vswitch.VswitchAction, 'query')
    def test_vswitch_query(self, mock_query, mock_name):
        mock_query.return_value = {}
        mock_name.return_value = 'vsw1'

        vswitch.vswitch_query(self.req)
        mock_query.assert_called_once_with('vsw1')

    def test_vswitch_create_invalid_connection(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "connection": 3}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_queue_mem(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "queue_mem": 10}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_network_type(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "network_type": 3}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_update(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "update": 4}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_vid(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "vid": -1}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_native_vid(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "native_vid": 4096}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_router(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "router": 3}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_grvp(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "gvrp": 3}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    def test_vswitch_create_invalid_controller(self):
        body_str = """{"vswitch": {"name": "name1",
                                   "rdev": "1234",
                                   "controller": "node12345"}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, vswitch.vswitch_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(vswitch.VswitchAction, 'update')
    def test_vswitch_update(self, mock_update, mock_name):
        mock_name.return_value = 'vsw1'
        body_str = '{"vswitch": {"grant_userid": "user1"}}'
        mock_update.return_value = {}
        self.req.body = body_str

        vswitch.vswitch_update(self.req)
        body = util.extract_json(body_str)
        mock_update.assert_called_once_with('vsw1', body=body)
