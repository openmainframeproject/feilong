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
import json
import mock
import requests
import unittest


from zvmconnector import restclient
from zvmsdk import config


CONF = config.CONF


class FakeResp(object):
    def __init__(self):
        self.content = '{"output": "{}"}'


class RESTClientTestCase(unittest.TestCase):
    """Testcases for RESTClient."""
    def setUp(self):
        self.client = restclient.RESTClient(ssl_enabled=False)
        self.fake_userid = 'userid01'
        self.base_url = 'http://127.0.0.1:8888'
        self.headers = {'Content-Type': 'application/json'}
        self.headers.update(self.headers or {})
        self.headers['X-Auth-Token'] = self._tmp_token()
        self.response = FakeResp()

        self.client_ssl = restclient.RESTClient(ssl_enabled=True)
        self.base_url_ssl = 'https://127.0.0.1:8888'

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.client, restclient.RESTClient))

    def _tmp_token(self):
        token = '1234567890'
        return token

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_create(self, get_token, request):
        method = 'POST'
        url = '/guests'
        disks = [{'size': '3g', 'is_boot_disk': True}]
        body = {'guest': {'userid': self.fake_userid,
                          'vcpus': 1,
                          'memory': 1024,
                          'disk_list': disks,
                          'user_profile': 'profile'
                          }}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_create", self.fake_userid,
                         1, 1024, disk_list=disks,
                         user_profile='profile')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_list(self, get_token, request):
        method = 'GET'
        url = '/guests'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_list")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_inspect_stats(self, get_token, request):
        method = 'GET'
        url = '/guests/stats?userid=%s' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_inspect_stats", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_inspect_vnics(self, get_token, request):
        method = 'GET'
        url = '/guests/vnicsinfo?userid=%s' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_inspect_vnics", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guests_get_nic_info(self, get_token, request):
        method = 'GET'
        url = '/guests/nics?userid=%s&nic_id=%s&vswitch=%s' % (
                                                    self.fake_userid,
                                                    '1000',
                                                    'xcatvsw1')
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guests_get_nic_info", userid=self.fake_userid,
                         nic_id='1000', vswitch='xcatvsw1')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_delete(self, get_token, request):
        method = 'DELETE'
        url = '/guests/%s' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_delete", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_definition_info(self, get_token, request):
        method = 'GET'
        url = '/guests/%s' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_definition_info", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_start(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'start'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_start", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_stop(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'stop'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_stop", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_softstop(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'softstop'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_softstop", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_pause(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'pause'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_pause", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_unpause(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'unpause'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_unpause", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_reboot(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'reboot'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_reboot", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_reset(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'reset'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_reset", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_console_output(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'get_console_output'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_console_output", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_capture(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'capture',
                'image': 'image_captured'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_capture", self.fake_userid,
                         'image_captured')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_deploy(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'capture',
                'image': 'image_captured'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_capture", self.fake_userid,
                         'image_captured')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_info(self, get_token, request):
        method = 'GET'
        url = '/guests/%s/info' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_info", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_info_ssl(self, get_token, request):
        method = 'GET'
        url = '/guests/%s/info' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url_ssl + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client_ssl.call("guest_get_info", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)
