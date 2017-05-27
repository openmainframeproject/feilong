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

from zvmsdk import api
from zvmsdk import exception
from zvmsdk.sdkwsgi.handlers import guest
from zvmsdk.sdkwsgi import util


FAKE_UUID = '00000000-0000-0000-0000-000000000000'


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.__name__ = ''

    def __getitem__(self, name):
        return self.headers


class SDKWSGITest(unittest.TestCase):
    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload


class GuestActionsTest(SDKWSGITest):
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
    @mock.patch.object(guest.VMAction, 'get_conole_output')
    def test_guest_get_conole_output(self, mock_action,
                        mock_uuid):
        self.req.body = '{"get_conole_output": "None"}'

        mock_uuid.return_value = FAKE_UUID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_invalid_action(self, mock_uuid):
        self.req.body = '{"fake": "None"}'

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(webob.exc.HTTPBadRequest, guest.guest_action,
                          self.req)


class HandlersGuestTest(SDKWSGITest):

    @mock.patch.object(guest.VMHandler, 'list')
    def test_guest_list(self, mock_list):

        guest.guest_list(self.req)
        self.assertTrue(mock_list.called)

    @mock.patch.object(guest.VMHandler, 'create')
    def test_guest_create(self, mock_create):
        body_str = '{"guest": {"name": "name1"}}'
        self.req.body = body_str

        guest.guest_create(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(body=body)

    def test_guest_create_invalidname(self):
        body_str = '{"guest": {"name": ""}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_cpu(self):
        body_str = '{"guest": {"name": "name1", "cpu": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_mem(self):
        body_str = '{"guest": {"name": "name1", "memory": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_false_input(self):
        body_str = '{"guest": {"name": "name1", "dummy": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

        body_str = '{"guest": {"name": "name1"}, "dummy": "dummy"}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_info')
    def test_guest_get_info(self, mock_get, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_get_info(self.req)
        mock_get.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_power_state')
    def test_guest_power_state(self, mock_get, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_get_power_state(self.req)
        mock_get.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'delete')
    def test_guest_delete(self, mock_delete, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_delete(self.req)
        mock_delete.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'create_nic')
    def test_guest_create_nic(self, mock_create, mock_uuid):
        body_str = '{"nic": {"nic_info": [], "ip": "dummy"}}'
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        guest.guest_create_nic(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(FAKE_UUID, body=body)

    def test_guest_create_invalid_ip(self):
        body_str = '{"nic": {"nic_info": [], "ip": 12345}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_nic_info(self):
        body_str = '{"nic": {"nic_info": "abc", "ip": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_nic_missing_required(self):
        body_str = '{"nic": {"ip": "dummy"}}'
        self.req.body = body_str
        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_nic_info')
    def test_guest_get_nic_info(self, mock_get, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_get_nic_info(self.req)
        mock_get.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(api.SDKAPI, 'guest_nic_couple_to_vswitch')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_couple_nic(self, mock_uuid, mock_couple):
        body_str = """{"info": {"couple": "true",
                       "vswitch": "v1", "port": "p1"}}"""
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        guest.guest_couple_uncouple_nic(self.req)
        mock_couple.assert_called_once_with("v1", "p1",
            FAKE_UUID, persist=True)

    @mock.patch.object(api.SDKAPI, 'guest_nic_uncouple_from_vswitch')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic(self, mock_uuid, mock_uncouple):

        body_str = """{"info": {"couple": "false",
                       "vswitch": "v1", "port": "p1",
                       "persist": "false"}}"""
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        guest.guest_couple_uncouple_nic(self.req)
        mock_uncouple.assert_called_once_with("v1", "p1",
            FAKE_UUID, persist=False)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_couple_nic_missing_required_1(self, mock_uuid):

        body_str = """{"info": {"couple": "true",
                       "vswitch": "v1"}}"""
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_couple_nic_missing_required_2(self, mock_uuid):

        body_str = '{"info1": {}}'
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic_bad_vswitch(self, mock_uuid):

        body_str = """{"info": {"couple": "false",
                       "vswitch": 1233, "port": "p1"}}"""
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic_bad_couple(self, mock_uuid):

        body_str = """{"info": {"couple": "couple",
                       "vswitch": "v1", "port": "p1"}}"""
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)
