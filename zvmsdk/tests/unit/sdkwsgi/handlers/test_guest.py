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
FAKE_USERID_LIST = ['abc', '123', 'defdf']


class FakeReqGet(object):
    def getall(self, userid):
        return FAKE_USERID_LIST

    def keys(self):
        return ['userid']


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.body = {}
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

    @mock.patch.object(api.SDKAPI, 'guest_create')
    def test_guest_create(self, mock_create):
        body_str = '{"guest": {"userid": "name1", "vcpus": 1, "memory": 1}}'
        self.req.body = body_str

        guest.guest_create(self.req)
        mock_create.assert_called_once_with('name1', 1, 1, disk_list=None)

    def test_guest_create_invalidname(self):
        body_str = '{"guest": {"userid": ""}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch.object(api.SDKAPI, 'guest_create')
    def test_guest_create_with_disk_list(self, mock_create):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g"}]}}"""
        self.req.body = body_str

        guest.guest_create(self.req)
        mock_create.assert_called_once_with('name1', 1, 1,
                                            disk_list=[{u'size': u'1g'}])

    def test_guest_create_invalid_disk_list(self):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": 1}]}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_disk_list_param(self):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g", "dummy": 1}]}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_cpu(self):
        body_str = '{"guest": {"userid": "name1", "vcpus": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_mem(self):
        body_str = '{"guest": {"userid": "name1", "memory": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_false_input(self):
        body_str = '{"guest": {"userid": "name1", "dummy": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

        body_str = '{"guest": {"userid": "name1"}, "dummy": "dummy"}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch.object(api.SDKAPI, 'guest_deploy')
    def test_guest_deploy(self, mock_deploy):
        body_str = '{"guest": {"userid": "name1", "image_name": "i1"}}'
        self.req.body = body_str

        guest.guest_deploy(self.req)
        mock_deploy.assert_called_once_with('name1', 'i1', remotehost=None,
                                            transportfiles=None, vdev=None)

    @mock.patch.object(api.SDKAPI, 'guest_deploy')
    def test_guest_deploy_with_param(self, mock_deploy):
        body_str = """{"guest": {"userid": "name1", "image_name": "i1",
                               "remotehost": "r1", "vdev": "v1"}}"""
        self.req.body = body_str

        guest.guest_deploy(self.req)
        mock_deploy.assert_called_once_with('name1', 'i1', remotehost='r1',
                                            transportfiles=None, vdev='v1')

    @mock.patch.object(api.SDKAPI, 'guest_deploy')
    def test_guest_deploy_invalid_vdev(self, mock_deploy):
        body_str = """{"guest": {"userid": "name1", "image_name": "i1",
                               "remotehost": "r1", "vdev": 1}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_deploy,
                          self.req)

    @mock.patch.object(api.SDKAPI, 'guest_deploy')
    def test_guest_deploy_no_userid(self, mock_deploy):
        body_str = """{"guest": {"image_name": "i1",
                                 "remotehost": "r1", "vdev": "v1"}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_deploy,
                          self.req)

    @mock.patch.object(api.SDKAPI, 'guest_deploy')
    def test_guest_deploy_invalid_image_name(self, mock_deploy):
        body_str = """{"guest": {"userid": "name1", "image_name": 1,
                                 "remotehost": "r1", "vdev": "1"}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_deploy,
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
        body_str = '{"nic": {"vdev": "1234"}}'
        self.req.body = body_str

        mock_uuid.return_value = FAKE_UUID

        guest.guest_create_nic(self.req)
        body = util.extract_json(body_str)
        mock_create.assert_called_once_with(FAKE_UUID, body=body)

    def test_guest_create_nic_invalid_vdev(self):
        body_str = '{"nic": {"vdev": 123}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create_nic,
                          self.req)

    def test_guest_create_nic_invalid_nic_ip(self):
        body_str = '{"nic": {"ip_addr": "dummy"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_nic_info')
    def test_guest_get_nic_info(self, mock_get, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_get_nic_info(self.req)
        mock_get.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get')
    def test_guest_get(self, mock_get, mock_uuid):
        mock_uuid.return_value = FAKE_UUID

        guest.guest_get(self.req)
        mock_get.assert_called_once_with(FAKE_UUID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'update')
    def test_guest_update(self, mock_update, mock_uuid):
        mock_uuid.return_value = FAKE_UUID
        self.req.body = '{}'

        guest.guest_update(self.req)
        mock_update.assert_called_once_with(FAKE_UUID, {})

    @mock.patch.object(guest.VMHandler, 'get_cpu_info')
    def test_guest_get_cpu_info(self, mock_get):
        self.req.GET = FakeReqGet()

        guest.guest_get_cpu_info(self.req)
        mock_get.assert_called_once_with(FAKE_USERID_LIST)

    @mock.patch.object(guest.VMHandler, 'get_memory_info')
    def test_guest_get_mem_info(self, mock_get):
        self.req.GET = FakeReqGet()

        guest.guest_get_memory_info(self.req)
        mock_get.assert_called_once_with(FAKE_USERID_LIST)

    @mock.patch.object(guest.VMHandler, 'get_vnics_info')
    def test_guest_get_vnics_info(self, mock_get):
        self.req.GET = FakeReqGet()

        guest.guest_get_vnics_info(self.req)
        mock_get.assert_called_once_with(FAKE_USERID_LIST)

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
