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

from zvmsdk.sdkwsgi.handlers import host
from zvmsdk.sdkwsgi import util


FAKE_USERID = 'noexist'


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


class HandlersHostTest(unittest.TestCase):

    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(host.HostAction, 'get_info')
    def test_host_get_info(self, mock_get_info):

        mock_get_info.return_value = ''
        host.host_get_info(self.req)
        self.assertTrue(mock_get_info.called)

    @mock.patch.object(host.HostAction, 'diskpool_get_info')
    def test_host_get_disk_info(self, mock_get_disk_info):

        mock_get_disk_info.return_value = ''
        self.req.GET = {}
        self.req.GET['poolname'] = 'disk1'
        host.host_get_disk_info(self.req)
        self.assertTrue(mock_get_disk_info.called)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(host.HostAction, 'get_guest_definition_info')
    def test_host_get_guest_definition_info(self, mock_get, mock_userid):
        mock_get.return_value = ''
        mock_userid.return_value = FAKE_USERID

        host.host_get_guest_definition_info(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID)
