#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017, 2024 IBM Corp.
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
    def test_guest_create(self, get_token, request):
        # method = 'POST'
        # url = '/guests'
        disks = [{'size': '3g', 'is_boot_disk': True}]
        # body = {'guest': {'userid': self.fake_userid,
        #                'vcpus': 1,
        #                'memory': 1024,
        #               'disk_list': disks,
        #               'user_profile': 'profile'
        #               }}
        # body = json.dumps(body)
        # header = self.headers
        # full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_create", self.fake_userid,
                         1, 1024, disk_list=disks,
                         user_profile='profile')
        # request.assert_called_with(method, full_uri,
        #                             data=body, headers=header,
        #                             verify=False)

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

        fake_userid_string = 'userid1, userid2, userid3,userid4'
        url = '/guests/stats?userid=%s' % fake_userid_string
        full_uri = self.base_url + url
        self.client.call("guest_inspect_stats", fake_userid_string)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_inspect_vnics(self, get_token, request):
        method = 'GET'
        url = '/guests/interfacestats?userid=%s' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_inspect_vnics", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        fake_userid_string = 'userid1, userid2, userid3,userid4'
        url = '/guests/interfacestats?userid=%s' % fake_userid_string
        full_uri = self.base_url + url
        self.client.call("guest_inspect_vnics", fake_userid_string)
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
    def test_guest_softstop_parameter_set_zero(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'softstop', 'timeout': 0, 'poll_interval': 0}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_softstop", self.fake_userid,
                         timeout=0, poll_interval=0)
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
    def test_guest_live_migrate(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_register(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_deregister(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_live_resize_cpus(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_resize_cpus(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_resize_mem(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'resize_mem',
                'size': '4g'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_resize_mem", self.fake_userid,
                         '4g')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_live_resize_mem(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'live_resize_mem',
                'size': '4g'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_live_resize_mem", self.fake_userid,
                         '4g')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_grow_root_volume(self, get_token, request):
        method = 'POST'
        url = '/guests/%s/action' % self.fake_userid
        body = {'action': 'grow_root_volume',
                'os_version': 'RHEL7.8'}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_grow_root_volume", self.fake_userid,
                         'RHEL7.8')
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
    def test_guest_get_power_state_real(self, get_token, request):
        method = 'GET'
        url = '/guests/%s/power_state_real' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_power_state_real", self.fake_userid)
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

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_user_direct(self, get_token, request):
        method = 'GET'
        url = '/guests/%s/user_direct' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_user_direct", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_adapters_info(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_create_nic(self, get_token, request):
        # method = 'POST'
        # url = '/guests/%s/nic' % self.fake_userid
        body = {'nic': {'vdev': '123', 'nic_id': '1234',
                        'mac_addr': 'xx:xx:xx:xx:xx:xx',
                        'active': False}}
        body = json.dumps(body)
        # header = self.headers
        # full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_create_nic", self.fake_userid,
                         vdev='123', nic_id='1234',
                         mac_addr='xx:xx:xx:xx:xx:xx',
                         active=False)
        request.assert_called_once()
        # request.assert_called_with(method, full_uri,
        #                            data=body, headers=header,
        #                            verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_delete_nic(self, get_token, request):
        method = 'DELETE'
        url = '/guests/%s/nic/%s' % (self.fake_userid, '123')
        body = {'active': False}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_delete_nic", self.fake_userid, '123',
                         active=False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_nic_couple_to_vswitch(self, get_token, request):
        method = 'PUT'
        url = '/guests/%s/nic/%s' % (self.fake_userid, '123')
        body = {'info': {'couple': True,
                         'vswitch': 'vswitch1',
                         'active': False}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_nic_couple_to_vswitch", self.fake_userid,
                         '123', 'vswitch1', active=False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_nic_couple_to_vswitch_vlan_id(self, get_token, request):
        method = 'PUT'
        url = '/guests/%s/nic/%s' % (self.fake_userid, '123')
        body = {'info': {'couple': True,
                         'vswitch': 'vswitch1',
                         'vlan_id': 1234,
                         'active': False}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_nic_couple_to_vswitch", self.fake_userid,
                         '123', 'vswitch1', vlan_id=1234, active=False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_nic_uncouple_from_vswitch(self, get_token, request):
        method = 'PUT'
        url = '/guests/%s/nic/%s' % (self.fake_userid, '123')
        body = {'info': {'couple': False,
                         'active': False}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_nic_uncouple_from_vswitch", self.fake_userid,
                         '123', active=False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_create_network_interface(self, get_token, request):
        method = 'POST'
        networks = [{'ip_addr': '12.12.12.12'}]
        url = '/guests/%s/interface' % self.fake_userid
        body = {'interface': {'os_version': 'rhel7.2',
                              'guest_networks': networks,
                              'active': False}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        # **kwargs accepts the key=val arguments
        self.client.call("guest_create_network_interface", self.fake_userid,
                         'rhel7.2', networks, False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_delete_network_interface(self, get_token, request):
        method = 'DELETE'
        url = '/guests/%s/interface' % self.fake_userid
        body = {'interface': {'os_version': 'rhel7.2',
                              'vdev': '123',
                              'active': False}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_delete_network_interface", self.fake_userid,
                         'rhel7.2', '123', active=False)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_get_power_state(self, get_token, request):
        method = 'GET'
        url = '/guests/%s/power_state' % self.fake_userid
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_get_power_state", self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_create_disks(self, get_token, request):
        method = 'POST'
        disks = [{'size': '3g'}]
        url = '/guests/%s/disks' % self.fake_userid
        body = {'disk_info': {'disk_list': disks}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_create_disks", self.fake_userid, disks)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_delete_disks(self, get_token, request):
        method = 'DELETE'
        vdevs = ['0101', '0102']
        url = '/guests/%s/disks' % self.fake_userid
        body = {'vdev_info': {'vdev_list': vdevs}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_delete_disks", self.fake_userid, vdevs)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_guest_config_minidisks(self, get_token, request):
        method = 'PUT'
        disks = [{'vdev': '0101', 'mntdir': '/mnt/0101'}]
        url = '/guests/%s/disks' % self.fake_userid
        body = {'disk_info': {'disk_list': disks}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("guest_config_minidisks", self.fake_userid, disks)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_volume_attach(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_volume_detach(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_volume_refresh_bootmap(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_get_volume_connector(self, get_token, request):
        method = 'GET'
        kwargs = {'reserve': True,
                  'fcp_template_id': 'fake id',
                  'storage_provider': 'v7k'}
        url = '/volumes/conn/fakeuser'
        header = self.headers
        body = {
            "info": {
                "reserve": True,
                "fcp_template_id": 'fake id',
                "storage_provider": "v7k"
            }
        }
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("get_volume_connector", 'fakeuser', **kwargs)
        request.assert_called_with(method, full_uri,
                                   data=json.dumps(body), headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_get_fcp_templates(self, get_token, request):
        method = 'GET'
        template_list = ['fake_template_id' + '0' * 20]
        url = '/volumes/fcptemplates?template_id_list=%s' % template_list
        full_uri = self.base_url + url
        header = self.headers
        request.return_value = self.response
        get_token.return_value = self._tmp_token()
        kwargs = {'template_id_list': template_list}
        args = []
        self.client.call("get_fcp_templates",
                         *args, **kwargs)
        body = None
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        assigner_id = 'assigner_id'
        kwargs = {'assigner_id': assigner_id}
        url = '/volumes/fcptemplates?assigner_id=%s' % assigner_id
        full_uri = self.base_url + url
        self.client.call("get_fcp_templates",
                         *args, **kwargs)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        default_sp_list = 'default_sp_list'
        kwargs = {'storage_providers': default_sp_list}
        url = '/volumes/fcptemplates?storage_providers=%s' % default_sp_list
        full_uri = self.base_url + url
        self.client.call("get_fcp_templates",
                         *args, **kwargs)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        host_default = 'host_default'
        kwargs = {'host_default': host_default}
        url = '/volumes/fcptemplates?host_default=%s' % host_default
        full_uri = self.base_url + url
        self.client.call("get_fcp_templates",
                         *args, **kwargs)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_get_fcp_templates_details(self, get_token, request):
        method = 'GET'
        template_list = ['fake_template_id' + '0' * 20]
        url = '/volumes/fcptemplates/detail?template_id_list=%s&' % template_list
        url += 'raw=False&statistics=True&sync_with_zvm=False'
        full_uri = self.base_url + url
        header = self.headers
        request.return_value = self.response
        get_token.return_value = self._tmp_token()
        kwargs = {'template_id_list': template_list}
        args = []
        self.client.call("get_fcp_templates_details",
                         *args, **kwargs)
        body = None
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        kwargs = {}
        url = '/volumes/fcptemplates/detail?'
        url += 'raw=False&statistics=True&sync_with_zvm=False'
        full_uri = self.base_url + url
        self.client.call("get_fcp_templates_details",
                         *args, **kwargs)
        body = None
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_delete_fcp_template(self, get_token, request):
        method = 'DELETE'
        url = '/volumes/fcptemplates/92ac944a-fb7a-11ec-870c-02553600000f'
        header = self.headers
        body = None
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("delete_fcp_template", '92ac944a-fb7a-11ec-870c-02553600000f')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_get_fcp_usage(self, get_token, request):
        method = 'GET'
        url = '/volumes/fcp/1a00'
        header = self.headers
        body = None
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("get_fcp_usage", '1a00')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_set_fcp_usage(self, get_token, request):
        method = 'PUT'
        url = '/volumes/fcp/1a00'
        header = self.headers
        body = {'info': {'userid': 'fakeuser',
                         'reserved': 1,
                         'connections': 2,
                         'fcp_template_id': 'f0fd9e40-fb7a-11ec-ba2a-02553600000f'}}
        body = json.dumps(body)
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("set_fcp_usage", '1a00', 'fakeuser', 1, 2, 'f0fd9e40-fb7a-11ec-ba2a-02553600000f')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        body = {'info': {'userid': 'fakeuser',
                         'reserved': 0,
                         'connections': 0,
                         'fcp_template_id': ''}}
        body = json.dumps(body)
        self.client.call("set_fcp_usage", '1a00', 'fakeuser', 0, 0, '')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_create_fcp_template(self, get_token, request):
        method = 'POST'
        url = '/volumes/fcptemplates'
        header = self.headers
        body = {'name': 'tmpl name',
                'description': 'desc text',
                'fcp_devices': '1a00,1a03-1a04;1b00-1b05',
                'host_default': True,
                'default_sp_list': ['v5k', 'v7k', 'd8k']}
        body = json.dumps(body)
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("create_fcp_template", 'tmpl name',
                         description='desc text',
                         fcp_devices='1a00,1a03-1a04;1b00-1b05',
                         host_default=True, default_sp_list=['v5k', 'v7k', 'd8k'])
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        body = {'name': 'tmpl name',
                'description': 'desc text',
                'fcp_devices': '1a00,1a03-1a04;1b00-1b05'}
        body = json.dumps(body)
        self.client.call("create_fcp_template", 'tmpl name',
                         description='desc text',
                         fcp_devices='1a00,1a03-1a04;1b00-1b05')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_edit_fcp_template(self, get_token, request):
        method = 'PUT'
        fake_tmpl_id = 'fake_template_id' + '0' * 20
        url = '/volumes/fcptemplates/%s' % fake_tmpl_id
        full_uri = self.base_url + url
        header = self.headers
        request.return_value = self.response
        get_token.return_value = self._tmp_token()
        kwargs = {'name': 'fake_name', 'description': 'desc'}
        self.client.call("edit_fcp_template",
                         fake_tmpl_id, **kwargs)
        body = json.dumps(kwargs)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_get_info(self, get_token, request):
        method = 'GET'
        url = '/host'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("host_get_info")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_get_guest_list(self, get_token, request):
        method = 'GET'
        url = '/host/guests'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("host_get_guest_list")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_get_diskpool_volumes(self, get_token, request):
        method = 'GET'
        url = '/host/diskpool_volumes?poolname=pool1'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("host_get_diskpool_volumes", disk_pool='pool1')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        url = '/host/diskpool_volumes'
        full_uri = self.base_url + url
        self.client.call("host_get_diskpool_volumes")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_diskpool_get_info(self, get_token, request):
        # wait host_diskpool_get_info bug fixed
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_get_volume_info(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_host_get_ssi_info(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_image_import(self, get_token, request):
        method = 'POST'
        image_uri = 'file:///tmp/100.img'
        image_meta = {'os_version': 'rhel7.2', 'md5sum': 'dummy'}
        url = '/images'
        body = {'image': {'image_name': '100.img',
                          'url': image_uri,
                          'image_meta': image_meta}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("image_import", '100.img',
                         image_uri, image_meta)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_image_query(self, get_token, request):
        method = 'GET'
        url = '/images'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("image_query")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

        url = '/images?imagename=test-name1'
        full_uri = self.base_url + url
        self.client.call("image_query", imagename='test-name1')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_image_delete(self, get_token, request):
        method = 'DELETE'
        url = '/images/%s' % '100.img'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("image_delete", '100.img')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_image_export(self, get_token, request):
        method = 'PUT'
        destination = 'file:///tmp/export.img'
        url = '/images/%s' % '100.img'
        body = {'location': {'dest_url': destination}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("image_export", '100.img',
                         destination)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_image_get_root_disk_size(self, get_token, request):
        method = 'GET'
        url = '/images/%s/root_disk_size' % '100.img'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("image_get_root_disk_size", '100.img')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_file_import(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_file_export(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_token_create(self, get_token, request):
        method = 'POST'
        url = '/token'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("token_create")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_get_list(self, get_token, request):
        method = 'GET'
        url = '/vswitches'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_get_list")
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_create(self, get_token, request):
        method = 'POST'
        url = '/vswitches'
        body = {'vswitch': {'name': 'dummy'}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_create", 'dummy')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_delete(self, get_token, request):
        method = 'DELETE'
        url = '/vswitches/%s' % 'dummy'
        body = None
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_delete", 'dummy')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_query(self, get_token, request):
        pass

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_grant_user(self, get_token, request):
        method = 'PUT'
        url = '/vswitches/%s' % 'dummy'
        body = {'vswitch': {'grant_userid': self.fake_userid}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_grant_user", 'dummy', self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_revoke_user(self, get_token, request):
        method = 'PUT'
        url = '/vswitches/%s' % 'dummy'
        body = {'vswitch': {'revoke_userid': self.fake_userid}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_revoke_user", 'dummy', self.fake_userid)
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)

    @mock.patch.object(requests, 'request')
    @mock.patch('zvmconnector.restclient.RESTClient._get_token')
    def test_vswitch_set_vlan_id_for_user(self, get_token, request):
        method = 'PUT'
        url = '/vswitches/%s' % 'dummy'
        body = {'vswitch': {'user_vlan_id': {'userid': self.fake_userid,
                                             'vlanid': 'vlan_id'}}}
        body = json.dumps(body)
        header = self.headers
        full_uri = self.base_url + url
        request.return_value = self.response
        get_token.return_value = self._tmp_token()

        self.client.call("vswitch_set_vlan_id_for_user",
                         'dummy', self.fake_userid, 'vlan_id')
        request.assert_called_with(method, full_uri,
                                   data=body, headers=header,
                                   verify=False)
