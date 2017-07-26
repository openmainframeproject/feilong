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

from zvmsdk.sdkwsgi.handlers import volume


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


class HandlersVolumeTest(unittest.TestCase):

    def setUp(self):
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch.object(volume.VolumeAction, 'attach')
    def test_volume_attach(self, mock_attach):
        self.req.body = '{}'

        volume.volume_attach(self.req)
        self.assertTrue(mock_attach.called)

    @mock.patch.object(volume.VolumeAction, 'detach')
    def test_volume_detach(self, mock_detach):
        self.req.body = '{}'

        volume.volume_detach(self.req)
        self.assertTrue(mock_detach.called)
