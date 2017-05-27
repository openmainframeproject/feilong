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

from zvmsdk.sdkwsgi.handlers import host


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.__name__ = ''

    def __getitem__(self, name):
        return self.headers


class HandlersGuestTest(unittest.TestCase):

    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(host.HostAction, 'list')
    def test_host_list(self, mock_list):

        host.host_list_guests(self.req)
        self.assertTrue(mock_list.called)

    @mock.patch.object(host.HostAction, 'get_info')
    def test_host_get_info(self, mock_get_info):

        host.host_get_info(self.req)
        self.assertTrue(mock_get_info.called)

    @mock.patch.object(host.HostAction, 'get_disk_info')
    def test_host_get_disk_info(self, mock_get_disk_info):

        host.host_get_disk_info(self.req)
        self.assertTrue(mock_get_disk_info.called)
