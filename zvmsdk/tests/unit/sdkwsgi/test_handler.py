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

import mock
import testtools
import unittest
import webob.exc

from zvmsdk import exception
from zvmsdk.sdkwsgi import handler
from zvmsdk.sdkwsgi.handlers import tokens


env = {'SERVER_SOFTWARE': 'WSGIServer/0.1 Python/2.7.3',
       'SCRIPT_NAME': '',
       'REQUEST_METHOD': 'GET',
       'SERVER_PROTOCOL': 'HTTP/1.1',
       'SERVER_PORT': '8001',
       'HTTP_HOST': '127.0.0.1:8001',
       'wsgi.version': (1, 0),
       'HTTP_ACCEPT': '*/*',
       'LESSCLOSE': '/usr/bin/lesspipe %s %s',
       'wsgi.run_once': False,
       'QUERY_STRING': '',
       'wsgi.multiprocess': False,
       'SERVER_NAME': 'localhost',
       'REMOTE_ADDR': '127.0.0.1',
       'wsgi.url_scheme': 'http',
       'CONTENT_LENGTH': '',
       'wsgi.multithread': True,
       'CONTENT_TYPE': 'text/plain',
       'REMOTE_HOST': 'localhost'}


def dummy(status, headerlist):
    pass


class GuestActionNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_guest_invalid_resource(self):
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)


class GuestActionTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    def test_guest_start(self, mock_json):
        mock_json.return_value = {"action": "start"}
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMAction.start') \
            as start:
            start.return_value = {'overallRC': 0}
            h(self.env, dummy)

            start.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    def test_guest_deploy(self, mock_json):
        mock_json.return_value = {"action": "deploy"}
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMAction.deploy') \
            as deploy:
            deploy.return_value = {'overallRC': 0}
            h(self.env, dummy)

            deploy.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    def test_guest_stop(self, mock_json):
        mock_json.return_value = {"action": "stop"}
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMAction.stop') \
            as stop:
            stop.return_value = {'overallRC': 0}
            h(self.env, dummy)

            stop.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    def test_guest_softstop(self, mock_json):
        mock_json.return_value = {"action": "softstop"}
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMAction.softstop') \
            as stop:
            stop.return_value = {'overallRC': 0}
            h(self.env, dummy)

            stop.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    def test_guest_get_console_output(self, mock_json):
        mock_json.return_value = {"action": "get_console_output"}
        self.env['PATH_INFO'] = '/guests/1/action'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        url = 'zvmsdk.sdkwsgi.handlers.guest.VMAction.get_console_output'
        with mock.patch(url) as get_console_output:
            get_console_output.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_console_output.assert_called_once_with('1', body={})


class GuestHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_guest_invalid_resource(self):
        self.env['PATH_INFO'] = '/gueba'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)

    def test_guest_list_invalid(self):
        self.env['PATH_INFO'] = '/guests'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)

    def test_guest_stats_method_invalid(self):
        self.env['PATH_INFO'] = '/guests/stats'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)

    def test_guest_get_info_method_invalid(self):
        self.env['PATH_INFO'] = '/guests/1/info'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)

    def test_guest_get_info_resource_invalid(self):
        self.env['PATH_INFO'] = '/guests/1/info1'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)

    @testtools.skip('temply disable because of volume not support now')
    def test_guest_volume_invalid_method(self):
        self.env['PATH_INFO'] = '/guests/1/volumes'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)

    def test_guest_network_interface_invalid_method(self):
        self.env['PATH_INFO'] = '/guests/1/interface'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)


class GuestHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_guest_list(self, mock_validate):
        self.env['PATH_INFO'] = '/guests'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMHandler.list') \
            as list:
            list.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(list.called)

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1/info'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMHandler.get_info') \
            as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_info.assert_called_once_with(mock.ANY, '1')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.get_definition_info'
        with mock.patch(func) as get:
            get.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get.assert_called_once_with(mock.ANY, '1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_delete_nic(self, mock_validate, mock_json):
        mock_json.return_value = ''
        self.env['PATH_INFO'] = '/guests/1/nic/1000'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.delete_nic'
        with mock.patch(func) as delete_nic:
            delete_nic.return_value = {'overallRC': 0}
            h(self.env, dummy)

            delete_nic.assert_called_once_with('1', '1000', '')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_power_state(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1/power_state'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler'\
               '.get_power_state'
        with mock.patch(func) as get_power:
            get_power.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_power.assert_called_once_with(mock.ANY, '1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.create'
        with mock.patch(func) as create:
            create.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(create.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_delete(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.delete'
        with mock.patch(func) as delete:
            delete.return_value = {'overallRC': 0}
            h(self.env, dummy)
            delete.assert_called_once_with('1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_create_nic(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/nic'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.create_nic'
        with mock.patch(func) as create_nic:
            create_nic.return_value = {'overallRC': 0}
            h(self.env, dummy)

            create_nic.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_update_nic(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/nic/1000'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.nic_couple_uncouple'
        with mock.patch(func) as update_nic:
            update_nic.return_value = {'overallRC': 0}
            h(self.env, dummy)

            update_nic.assert_called_once_with('1', '1000', body={})

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_stats_empty_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/stats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_info.assert_called_once_with('guest_inspect_stats', [])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_stats_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/stats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_info.assert_called_once_with('guest_inspect_stats',
                                             ['l1', 'l2'])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_stats_invalid(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/stats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2&userd=l3,l4'
        h = handler.SdkHandler()
        self.assertRaises(exception.ValidationError, h, self.env,
                          dummy)

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_interface_stats_empty_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/interfacestats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_info.assert_called_once_with('guest_inspect_vnics',
                                             [])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_interface_stats_user_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/interfacestats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_info.assert_called_once_with('guest_inspect_vnics',
                                             ['l1', 'l2'])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_interface_stats_invalid(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/interfacestats'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'use=l1,l2'
        h = handler.SdkHandler()
        self.assertRaises(exception.ValidationError, h, self.env,
                          dummy)

    @mock.patch.object(tokens, 'validate')
    def test_guests_get_nic_info_without_limitation(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/nics'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as guests_get_nic_info:
            guests_get_nic_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            guests_get_nic_info.assert_called_once_with('guests_get_nic_info',
                                      userid=None, nic_id=None, vswitch=None)

    @mock.patch.object(tokens, 'validate')
    def test_guests_get_nic_info_with_userid(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/nics'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=test'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as guests_get_nic_info:
            guests_get_nic_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            guests_get_nic_info.assert_called_once_with('guests_get_nic_info',
                                    userid='test', nic_id=None, vswitch=None)

    @testtools.skip('temply disable because of volume not support now')
    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_attach_volume(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/1/volumes'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.volume.VolumeAction.attach'
        with mock.patch(func) as attach:
            attach.return_value = {'overallRC': 0}
            h(self.env, dummy)

            attach.assert_called_once_with('1', {})

    @testtools.skip('temply disable because of volume not support now')
    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def _test_guest_detach_volume(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/1/volumes'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.volume.VolumeAction.detach'
        with mock.patch(func) as detach:
            detach.return_value = {'overallRC': 0}
            h(self.env, dummy)

            detach.assert_called_once_with('1', {})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_delete_network_interface(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/interface'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = ('zvmsdk.sdkwsgi.handlers.guest.VMHandler.'
                'delete_network_interface')
        with mock.patch(func) as delete_network_interface:
            delete_network_interface.return_value = {'overallRC': 0}
            h(self.env, dummy)

            delete_network_interface.assert_called_once_with('1', body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_create_network_interface(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/interface'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        func = ('zvmsdk.sdkwsgi.handlers.guest.VMHandler.'
                'create_network_interface')
        with mock.patch(func) as create_network_interface:
            create_network_interface.return_value = {'overallRC': 0}
            h(self.env, dummy)

            create_network_interface.assert_called_once_with('1', body={})


class ImageHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_image_create_invalid_method(self):
        self.env['PATH_INFO'] = '/images'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)

    def test_image_get_root_disk_size_invalid(self):
        self.env['PATH_INFO'] = '/images/image1/root_size'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)


class ImageHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_image_root_disk_size(self, mock_validate):
        self.env['PATH_INFO'] = '/images/image1/root_disk_size'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as get_size:
            get_size.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_size.assert_called_once_with('image_get_root_disk_size',
                                             'image1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_image_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/images'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.image.ImageAction.create'
        with mock.patch(func) as create:
            create.return_value = {'overallRC': 0}
            h(self.env, dummy)

            create.assert_called_once_with(body={})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_image_delete(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/images/image1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as delete:
            delete.return_value = {'overallRC': 0}
            h(self.env, dummy)

            delete.assert_called_once_with('image_delete', 'image1')

    @mock.patch.object(tokens, 'validate')
    def test_image_query(self, mock_validate):
        self.env['PATH_INFO'] = '/images'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmconnector.connector.ZVMConnector.send_request'
        with mock.patch(func) as query:
            query.return_value = {'overallRC': 0}
            h(self.env, dummy)

            query.assert_called_once_with('image_query', None)


class HostHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_host_get_guest_list_invalid(self):
        self.env['PATH_INFO'] = '/host1/guest'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)

    def test_host_get_resource_invalid(self):
        self.env['PATH_INFO'] = '/host1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)

    def test_host_get_info_invalid(self):
        self.env['PATH_INFO'] = '/host/inf'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)

    def test_host_get_disk_size_invalid(self):
        self.env['PATH_INFO'] = '/host/disk_inf/d1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPNotFound,
                          h, self.env, dummy)


class HostHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_host_get_guest_list(self, mock_validate):
        self.env['PATH_INFO'] = '/host/guests'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.host.HostAction.get_guest_list') \
            as get_guest_list:
            get_guest_list.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(get_guest_list.called)

    @mock.patch.object(tokens, 'validate')
    def test_host_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/host'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.get_info'
        with mock.patch(function) as get_info:
            get_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(get_info.called)

    @mock.patch.object(tokens, 'validate')
    def test_host_get_disk_info(self, mock_validate):
        self.env['PATH_INFO'] = '/host/diskpool'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.diskpool_get_info'
        with mock.patch(function) as get_disk_info:
            get_disk_info.return_value = {'overallRC': 0}
            h(self.env, dummy)

            get_disk_info.assert_called_once_with(mock.ANY, None)


class VswitchHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_vswitch_put_method_invalid(self):
        self.env['PATH_INFO'] = '/vswitches'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)


class VswitchHandlerTest(unittest.TestCase):
    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_vswitch_list(self, mock_validate):
        self.env['PATH_INFO'] = '/vswitches'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.list'
        with mock.patch(function) as list:
            list.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(list.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_vswitch_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/vswitches'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.create'
        with mock.patch(function) as create:
            create.return_value = {'overallRC': 0}
            h(self.env, dummy)

            self.assertTrue(create.called)

    @mock.patch.object(tokens, 'validate')
    def test_vswitch_delete(self, mock_validate):
        self.env['PATH_INFO'] = '/vswitches/vsw1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.delete'
        with mock.patch(function) as delete:
            delete.return_value = {'overallRC': 0}
            h(self.env, dummy)

            delete.assert_called_once_with('vsw1')

    @mock.patch.object(tokens, 'validate')
    def test_vswitch_query(self, mock_validate):
        self.env['PATH_INFO'] = '/vswitches/vsw1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.query'
        with mock.patch(function) as query:
            query.return_value = {'overallRC': 0}
            h(self.env, dummy)

            query.assert_called_once_with('vsw1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_vswitch_update(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/vswitches/vsw1'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.update'
        with mock.patch(function) as update:
            update.return_value = {'overallRC': 0}
            h(self.env, dummy)

            update.assert_called_once_with('vsw1', body={})
