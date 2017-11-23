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
import requests
import unittest


from zvmsdkclient import restclient
from zvmsdk import config


CONF = config.CONF


class FakeResp(object):
    def __init__(self):
        self.content = '{"output": "{}"}'


class RESTClientTestCase(unittest.TestCase):
    """Testcases for RESTClient."""
    def setUp(self):
        self.client = restclient.RESTClient()
        self.fake_userid = 'userid01'
        self.base_url = 'http://127.0.0.1:8888'
        self.headers = {'Content-Type': 'application/json'}
        self.headers.update(self.headers or {})
        self.headers['X-Auth-Token'] = self._tmp_token()
        self.response = FakeResp()

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.client, restclient.RESTClient))

    def _tmp_token(self):
        expires = 30

        expired_elapse = datetime.timedelta(seconds=expires)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'password')

        return payload

    @mock.patch.object(requests, 'request')
    def test_guest_get_info(self, request):
        method = 'GET'
        url = '/guests/%s/info' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response

        self.client.call("guest_get_info", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header)
