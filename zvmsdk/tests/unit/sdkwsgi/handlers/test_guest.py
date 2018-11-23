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
import webob.exc

from zvmsdk import exception
from zvmsdk.sdkwsgi.handlers import guest
from zvmsdk.sdkwsgi import util


FAKE_USERID = '00000000-0000-0000-0000-000000000000'
FAKE_USERID_LIST_STR = 'ab,c,userid1'
FAKE_USERID_LIST = ['ab', 'c', 'userid1']


class FakeReqGet(object):
    def get(self, userid):
        return FAKE_USERID_LIST_STR

    def keys(self):
        return ['userid']

    def values(self):
        return FAKE_USERID_LIST


class FakeResp(object):
    def __init__(self):
        self.body = {}


class FakeReq(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.body = {}
        self.response = FakeResp()
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
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_start(self, mock_action,
                        mock_userid):
        self.req.body = '{"action": "start"}'

        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_start', FAKE_USERID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_stop(self, mock_action,
                        mock_userid):
        self.req.body = '{"action": "stop"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_stop', FAKE_USERID,
                                            timeout=None, poll_interval=None)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_stop_with_timeout(self, mock_action,
                                     mock_userid):
        self.req.body = '{"action": "stop", "timeout": 300}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_stop', FAKE_USERID,
                                             timeout=300,
                                             poll_interval=None)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_softstop_with_timeout_poll_interval(self, mock_action,
                                                       mock_userid):
        self.req.body = """{"action": "softstop", "timeout": 300,
                            "poll_interval": 15}"""
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_softstop', FAKE_USERID,
                                             timeout=300,
                                             poll_interval=15)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_get_console_output(self, mock_action,
                        mock_userid):
        self.req.body = '{"action": "get_console_output"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_get_console_output',
                                            FAKE_USERID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_cpus(self, mock_action,
                        mock_userid):
        self.req.body = '{"action": "live_resize_cpus", "cpu_cnt": 3}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_live_resize_cpus',
                                            FAKE_USERID, 3)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_cpus_missing_param(self, mock_action,
                                                  mock_userid):
        self.req.body = '{"action": "live_resize_cpus"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_cpus_invalid_cpu_cnt_1(self, mock_action,
                                                      mock_userid):
        self.req.body = '{"action": "live_resize_cpus", "cpu_cnt": 65}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_cpus_invalid_cpu_cnt_2(self, mock_action,
                                                      mock_userid):
        self.req.body = '{"action": "live_resize_cpus", "cpu_cnt": 0}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_cpus_invalid_cpu_cnt_type(self, mock_action,
                                                         mock_userid):
        self.req.body = '{"action": "live_resize_cpus", "cpu_cnt": "2"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus(self, mock_action, mock_userid):
        self.req.body = '{"action": "resize_cpus", "cpu_cnt": 3}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_resize_cpus',
                                            FAKE_USERID, 3)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus_missing_param(self, mock_action, mock_userid):
        self.req.body = '{"action": "resize_cpus"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus_invalid_cpu_cnt_1(self, mock_action,
                                                 mock_userid):
        self.req.body = '{"action": "resize_cpus", "cpu_cnt": 65}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus_invalid_cpu_cnt_2(self, mock_action,
                                                 mock_userid):
        self.req.body = '{"action": "resize_cpus", "cpu_cnt": 0}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus_invalid_cpu_cnt_type(self, mock_action,
                                                    mock_userid):
        self.req.body = '{"action": "resize_cpus", "cpu_cnt": "2"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_mem(self, mock_action, mock_userid):
        self.req.body = '{"action": "resize_mem", "size": "4096m"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_resize_mem',
                                            FAKE_USERID, "4096m")

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_mem_missing_param(self, mock_action, mock_userid):
        self.req.body = '{"action": "resize_mem"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_mem_invalid_mem_1(self, mock_action,
                                            mock_userid):
        self.req.body = '{"action": "resize_mem", "size": "88888M"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_mem_invalid_mem_2(self, mock_action,
                                            mock_userid):
        self.req.body = '{"action": "resize_mem", "size": "123"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_resize_cpus_invalid_mem_type(self, mock_action,
                                                mock_userid):
        self.req.body = '{"action": "resize_mem", "size": 1024}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_live_resize_mem(self, mock_action, mock_userid):
        self.req.body = '{"action": "live_resize_mem", "size": "4G"}'
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_live_resize_mem',
                                            FAKE_USERID, "4G")

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_deploy(self, mock_action,
                          mock_userid):
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": "test@host1.x.y",
                            "vdev": "1000"}"""
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_deploy', FAKE_USERID,
            'image1', remotehost='test@host1.x.y', transportfiles='file1',
            vdev='1000', hostname=None)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_deploy_missing_param(self, mock_userid):
        self.req.body = """{"action": "deploy",
                            "transportfiles": "file1",
                            "remotehost": "test@host1.x.y",
                            "vdev": "1000"}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_deploy_invalid_vdev(self, mock_userid):
        # vdev not string type
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": "test@host.com.cn",
                            "vdev": 1000}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_deploy_invalid_remotehost(self, mock_userid):
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": ".122.sd..",
                            "vdev": "1000"}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_deploy_with_ip_in_remotehost(self, mock_action,
                                                mock_userid):
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": "test@192.168.99.99",
                            "vdev": "1000"}"""
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_deploy', FAKE_USERID,
            'image1', remotehost='test@192.168.99.99',
            transportfiles='file1', vdev='1000', hostname=None)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_deploy_with_fqdn_in_remotehost(self, mock_action,
                                                  mock_userid):
        # remote host with Hostname + DomainName in it
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": "test123@test.xyz.com",
                            "vdev": "1000"}"""
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with('guest_deploy', FAKE_USERID,
            'image1', remotehost='test123@test.xyz.com',
            transportfiles='file1', vdev='1000', hostname=None)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_deploy_without_username_in_remotehost(self,
                                                      mock_userid):
        # remote host without username in it
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiles": "file1",
                            "remotehost": "@test.xyz.com",
                            "vdev": "1000"}"""

        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError,
                          guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_deploy_additional_param(self, mock_userid):
        # A typo in the transportfiles
        self.req.body = """{"action": "deploy",
                            "image": "image1",
                            "transportfiless": "file1",
                            "remotehost": "test@192.168.99.1",
                            "vdev": "1000"}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_invalid_action(self, mock_userid):
        self.req.body = '{"fake": "None"}'

        mock_userid.return_value = FAKE_USERID
        self.assertRaises(webob.exc.HTTPBadRequest, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_capture_additional_param(self, mock_userid):
        # Put wrong parameter compressionlevel, it should be compresslevel
        self.req.body = """{"action": "capture",
                            "image": "image1",
                            "capture_type": "rootonly",
                            "compression_level": "6"}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_capture_invalid_capturetype(self, mock_userid):
        # Put compresslevel to be invalid 10
        self.req.body = """{"action": "capture",
                            "image": "image1",
                            "capture_type": "rootdisk",
                            "compress_level": "10"}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_capture_invalid_compresslevel(self, mock_userid):
        # Put capture type to be invalid value
        self.req.body = """{"action": "capture",
                            "image": "image1",
                            "capture_type": "faketype",
                            "compress_level": 9}"""
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError, guest.guest_action,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_capture(self, mock_action, mock_userid):
        self.req.body = """{"action": "capture",
                            "image": "image1",
                            "capture_type": "rootonly",
                            "compress_level": 6}"""
        mock_action.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_action(self.req)
        mock_action.assert_called_once_with("guest_capture", FAKE_USERID,
            "image1", capture_type="rootonly", compress_level=6)


class HandlersGuestTest(SDKWSGITest):

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create(self, mock_create):
        body_str = '{"guest": {"userid": "name1", "vcpus": 1, "memory": 1}}'
        self.req.body = body_str
        mock_create.return_value = ''

        guest.guest_create(self.req)
        mock_create.assert_called_once_with('guest_create', 'name1',
                                            1, 1)

    def test_guest_create_invalid_userid(self):
        body_str = '{"guest": {"userid": ""}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_with_disk_list(self, mock_create):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g",
                                                "format": "xfs",
                                                "disk_pool": "ECKD:poolname"}
                                              ]}}"""
        self.req.body = body_str
        mock_create.return_value = ''

        guest.guest_create(self.req)
        mock_create.assert_called_once_with('guest_create',
                                            'name1', 1, 1,
                                            disk_list=[{u'size': u'1g',
                                                'format': 'xfs',
                                                'disk_pool': 'ECKD:poolname'}])

    def test_guest_create_invalid_disk_list(self):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": 1}]}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_with_invalid_format(self, mock_create):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g",
                                                "format": "dummy",
                                                "disk_pool": "ECKD:poolname"}
                                              ]}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_disk_list_param(self):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g", "dummy": 1}]}}"""
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create,
                          self.req)

    def test_guest_create_invalid_disk_list_poolname(self):
        body_str = """{"guest": {"userid": "name1", "vcpus": 1, "memory": 1,
                                 "disk_list": [{"size": "1g",
                                                "disk_pool": "pool"}]}}"""
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

    @mock.patch.object(guest.VMHandler, 'list')
    def test_guest_list(self, mock_list):
        mock_list.return_value = ''

        guest.guest_list(self.req)
        mock_list.assert_called_once_with()

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_info')
    def test_guest_get_info(self, mock_get, mock_userid):
        mock_get.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_get_info(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_power_state')
    def test_guest_power_state(self, mock_get, mock_userid):
        mock_get.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_get_power_state(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'delete')
    def test_guest_delete(self, mock_delete, mock_userid):
        mock_delete.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_delete(self.req)
        mock_delete.assert_called_once_with(FAKE_USERID)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_list(self, mock_interface):
        mock_interface.return_value = ''

        guest.guest_list(self.req)
        mock_interface.assert_called_once_with('guest_list')

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_nic(self, mock_create, mock_userid):
        vdev = '1234'
        nic_id = "514fec03-0d96-4349-a670-d972805fb579"
        mac_addr = "02:00:00:11:22:33"
        body_str = """{"nic": {"vdev": "1234",
                             "nic_id": "514fec03-0d96-4349-a670-d972805fb579",
                             "mac_addr": "02:00:00:11:22:33"}
                      }"""
        self.req.body = body_str
        mock_create.return_value = ''

        mock_userid.return_value = FAKE_USERID

        guest.guest_create_nic(self.req)
        mock_create.assert_called_once_with('guest_create_nic',
                                            FAKE_USERID, active=False,
                                            mac_addr=mac_addr,
                                            nic_id=nic_id, vdev=vdev)

    def test_guest_create_nic_invalid_vdev(self):
        body_str = '{"nic": {"vdev": 123}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create_nic,
                          self.req)

    def test_guest_create_nic_invalid_mac_addr(self):
        body_str = '{"nic": {"mac_addr": "11:22:33:44:55:6s"}}'
        self.req.body = body_str

        self.assertRaises(exception.ValidationError, guest.guest_create_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_network_interface(self, mock_interface, mock_userid):
        os_version = 'rhel6'
        guest_networks = [{'ip_addr': '192.168.12.34',
                           'dns_addr': ['9.1.2.3'],
                           'gateway_addr': '192.168.95.1',
                           'cidr': '192.168.95.0/24',
                           'nic_vdev': '1000',
                           'mac_addr': '02:00:00:12:34:56'}]
        bstr = """{"interface": {"os_version": "rhel6",
                                 "guest_networks": [
                                     {"ip_addr": "192.168.12.34",
                                      "dns_addr": ["9.1.2.3"],
                                      "gateway_addr": "192.168.95.1",
                                      "cidr": "192.168.95.0/24",
                                      "nic_vdev": "1000",
                                      "mac_addr": "02:00:00:12:34:56"}]}}"""
        self.req.body = bstr
        mock_userid.return_value = FAKE_USERID
        mock_interface.return_value = ''

        guest.guest_create_network_interface(self.req)
        mock_interface.assert_called_once_with(
            'guest_create_network_interface',
            FAKE_USERID,
            os_version=os_version,
            guest_networks=guest_networks,
            active=False)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_network_interface_OSA(self, mock_interface,
                                                mock_userid):
        os_version = 'rhel6'
        guest_networks = [{'ip_addr': '192.168.12.34',
                           'dns_addr': ['9.1.2.3'],
                           'gateway_addr': '192.168.95.1',
                           'cidr': '192.168.95.0/24',
                           'nic_vdev': '1000',
                           'mac_addr': '02:00:00:12:34:56',
                           'osa_device': 'AABB'}]
        bstr = """{"interface": {"os_version": "rhel6",
                                 "guest_networks": [
                                     {"ip_addr": "192.168.12.34",
                                      "dns_addr": ["9.1.2.3"],
                                      "gateway_addr": "192.168.95.1",
                                      "cidr": "192.168.95.0/24",
                                      "nic_vdev": "1000",
                                      "mac_addr": "02:00:00:12:34:56",
                                      "osa_device": "AABB"}]}}"""
        self.req.body = bstr
        mock_userid.return_value = FAKE_USERID
        mock_interface.return_value = ''

        guest.guest_create_network_interface(self.req)
        mock_interface.assert_called_once_with(
            'guest_create_network_interface',
            FAKE_USERID,
            os_version=os_version,
            guest_networks=guest_networks,
            active=False)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_delete_network_interface(self, mock_interface, mock_userid):
        os_version = 'rhel6'
        vdev = '1000'
        bstr = """{"interface": {"os_version": "rhel6",
                                 "vdev": "1000"}}"""
        self.req.body = bstr
        mock_userid.return_value = FAKE_USERID
        mock_interface.return_value = ''

        guest.guest_delete_network_interface(self.req)
        mock_interface.assert_called_once_with(
            'guest_delete_network_interface',
            FAKE_USERID,
            os_version,
            vdev,
            active=False)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guests_get_nic_info(self, mock_interface):
        self.req.GET = {}
        mock_interface.return_value = ''

        guest.guests_get_nic_info(self.req)
        mock_interface.assert_called_once_with(
            'guests_get_nic_info',
            userid=None, nic_id=None, vswitch=None)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guests_get_nic_info_all(self, mock_interface):
        userid = 'fakeid'
        nic_id = 'fake_nic_id'
        vswitch = 'vswitch'
        self.req.GET = {}
        self.req.GET['userid'] = userid
        self.req.GET['nic_id'] = nic_id
        self.req.GET['vswitch'] = vswitch

        mock_interface.return_value = ''

        guest.guests_get_nic_info(self.req)
        mock_interface.assert_called_once_with(
            'guests_get_nic_info',
            userid=userid, nic_id=nic_id, vswitch=vswitch)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guests_get_nic_info_with_userid(self, mock_interface):
        userid = 'fakeid'
        self.req.GET = {}
        self.req.GET['userid'] = userid

        mock_interface.return_value = ''

        guest.guests_get_nic_info(self.req)
        mock_interface.assert_called_once_with(
            'guests_get_nic_info',
            userid=userid, nic_id=None, vswitch=None)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guests_get_nic_info_with_nicid(self, mock_interface):
        nic_id = 'fake_nic_id'
        self.req.GET = {}
        self.req.GET['nic_id'] = nic_id

        mock_interface.return_value = ''

        guest.guests_get_nic_info(self.req)
        mock_interface.assert_called_once_with(
            'guests_get_nic_info',
            userid=None, nic_id=nic_id, vswitch=None)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guests_get_nic_info_with_vswitch(self, mock_interface):
        vswitch = 'vswitch'
        self.req.GET = {}
        self.req.GET['vswitch'] = vswitch

        mock_interface.return_value = ''

        guest.guests_get_nic_info(self.req)
        mock_interface.assert_called_once_with(
            'guests_get_nic_info',
            userid=None, nic_id=None, vswitch=vswitch)

    # TODO: move this test to sdk layer instead of API layer
    # or we can use validation to validate cidr
    @unittest.skip("we use send_request now.....")
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_create_network_interface_invalid_cidr(self,
                                                         mock_userid):
        # / not in cidr
        bstr = """{"interface": {"os_version": "rhel6",
                                 "guest_networks": [
                                     {"ip_addr": "192.168.12.34",
                                      "dns_addr": ["9.1.2.3"],
                                      "gateway_addr": "192.168.95.1",
                                      "cidr": "192.168.95.0",
                                      "nic_vdev": "1000",
                                      "mac_addr": "02:00:00:12:34:56"}]}}"""

        self.req.body = bstr
        mock_userid.return_value = FAKE_USERID

        self.assertRaises(webob.exc.HTTPBadRequest,
                          guest.guest_create_network_interface,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_guest_create_disks(self, mock_create, mock_userid):
        disk_list = [{u'size': u'1g',
                     'disk_pool': 'ECKD:poolname'}]
        body_str = """{"disk_info": {"disk_list": [{"size": "1g",
                                                "disk_pool": "ECKD:poolname"}
                                              ]}}"""
        mock_create.return_value = ''
        self.req.body = body_str
        mock_userid.return_value = FAKE_USERID

        guest.guest_create_disks(self.req)
        mock_create.assert_called_once_with('guest_create_disks',
                                            FAKE_USERID,
                                            disk_list)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_config_minidisks(self, mock_userid, mock_config):
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        mock_config.return_value = ''
        body_str = """{"disk_info": {"disk_list": [{"vdev": "0101",
                                                    "format": "ext3",
                                                    "mntdir": "/mnt/0101"}
                                                  ]}}"""
        self.req.body = body_str
        mock_userid.return_value = FAKE_USERID

        guest.guest_config_disks(self.req)
        mock_config.assert_called_once_with('guest_config_minidisks',
                                            FAKE_USERID,
                                            disk_list)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_delete_disks(self, mock_userid, mock_delete):
        vdev_list = ['0101']
        mock_delete.return_value = ''
        body_str = """{"vdev_info": {"vdev_list": ["0101"]}}"""
        self.req.body = body_str
        mock_userid.return_value = FAKE_USERID

        guest.guest_delete_disks(self.req)
        mock_delete.assert_called_once_with('guest_delete_disks',
                                            FAKE_USERID,
                                            vdev_list)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch.object(guest.VMHandler, 'get_definition_info')
    def test_guest_get(self, mock_get, mock_userid):
        mock_get.return_value = ''
        mock_userid.return_value = FAKE_USERID

        guest.guest_get(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID)

    @mock.patch.object(guest.VMHandler, 'inspect_stats')
    def test_guest_get_stats(self, mock_get):
        self.req.GET = FakeReqGet()
        mock_get.return_value = '{}'

        guest.guest_get_stats(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID_LIST)

    @mock.patch.object(guest.VMHandler, 'inspect_vnics')
    def test_guest_get_interface_stats(self, mock_get):
        self.req.GET = FakeReqGet()
        mock_get.return_value = '{}'

        guest.guest_get_interface_stats(self.req)
        mock_get.assert_called_once_with(self.req, FAKE_USERID_LIST)

    def mock_get_userid_vdev(self, env, param):
        if param == 'userid':
            return FAKE_USERID
        else:
            return '1000'

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_delete_nic(self, mock_userid, mock_delete):
        body_str = '{"info": {}}'
        self.req.body = body_str
        mock_delete.return_value = {'overallRC': 0}

        mock_userid.side_effect = self.mock_get_userid_vdev

        guest.guest_delete_nic(self.req)
        mock_delete.assert_called_once_with('guest_delete_nic',
                                            FAKE_USERID, "1000",
                                            active=False)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_couple_nic(self, mock_userid, mock_couple):
        body_str = '{"info": {"couple": "true", "vswitch": "vsw1"}}'
        self.req.body = body_str
        mock_couple.return_value = ''

        mock_userid.side_effect = self.mock_get_userid_vdev

        guest.guest_couple_uncouple_nic(self.req)
        mock_couple.assert_called_once_with('guest_nic_couple_to_vswitch',
                                            FAKE_USERID, "1000", "vsw1",
                                            active=False)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic(self, mock_userid, mock_uncouple):

        body_str = '{"info": {"couple": "false"}}'
        self.req.body = body_str
        mock_uncouple.return_value = ''

        mock_userid.side_effect = self.mock_get_userid_vdev

        guest.guest_couple_uncouple_nic(self.req)
        mock_uncouple.assert_called_once_with(
            'guest_nic_uncouple_from_vswitch',
            FAKE_USERID, "1000",
            active=False)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_couple_nic_missing_required_1(self, mock_userid):

        body_str = '{"info": {}}'
        self.req.body = body_str

        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic_bad_vswitch(self, mock_userid):

        body_str = '{"info": {"couple": "false", "active": "dummy"}}'
        self.req.body = body_str

        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(util, 'wsgi_path_item')
    def test_guest_uncouple_nic_bad_couple(self, mock_userid):

        body_str = '{"info": {"couple": "couple"}}'
        self.req.body = body_str

        mock_userid.return_value = FAKE_USERID

        self.assertRaises(exception.ValidationError,
                          guest.guest_couple_uncouple_nic,
                          self.req)

    @mock.patch.object(guest.VMHandler, 'create')
    def test_guest_create_unauthorized(self, mock_create):
        body_str = '{"guest": {"userid": "name1", "vcpus": 1, "memory": 1}}'
        self.req.body = body_str
        mock_create.side_effect = webob.exc.HTTPBadRequest

        self.assertRaises(webob.exc.HTTPBadRequest,
                          guest.guest_create, self.req)
