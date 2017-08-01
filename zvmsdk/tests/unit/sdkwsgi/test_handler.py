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

import mock
import unittest
import webob.exc

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
            start.return_value = ''
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
            deploy.return_value = ''
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
            stop.return_value = ''
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
            get_console_output.return_value = ''
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

    def test_guest_meminfo_method_invalid(self):
        self.env['PATH_INFO'] = '/guests/meminfo'
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

    def test_guest_volume_invalid_method(self):
        self.env['PATH_INFO'] = '/guests/1/volumes'
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
            list.return_value = ''
            h(self.env, dummy)

            self.assertTrue(list.called)

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1/info'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMHandler.get_info') \
            as get_info:
            get_info.return_value = ''
            h(self.env, dummy)

            get_info.assert_called_once_with('1')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.get'
        with mock.patch(func) as get:
            get.return_value = ''
            h(self.env, dummy)

            get.assert_called_once_with('1')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_nic_info(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1/nic'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.get_nic'
        with mock.patch(func) as get_nic_info:
            h(self.env, dummy)

            get_nic_info.assert_called_once_with('1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_delete_nic(self, mock_validate, mock_json):
        mock_json.return_value = ''
        self.env['PATH_INFO'] = '/guests/1/nic/1000'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.delete_nic'
        with mock.patch(func) as delete_nic:
            h(self.env, dummy)

            delete_nic.assert_called_once_with('1', '1000', '')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_power_state(self, mock_validate):
        self.env['PATH_INFO'] = '/guests/1/power_state'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler'\
                   '.get_power_state'
        with mock.patch(function) as get_power:
            get_power.return_value = ''
            h(self.env, dummy)

            get_power.assert_called_once_with('1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.create'
        with mock.patch(function) as create:
            h(self.env, dummy)

            self.assertTrue(create.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_delete(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.delete'
        with mock.patch(function) as delete:
            h(self.env, dummy)
            delete.assert_called_once_with('1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_create_nic(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/nic'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.create_nic'
        with mock.patch(function) as create_nic:
            h(self.env, dummy)

            self.assertTrue(create_nic.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_update_nic(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/guests/1/nic/1000'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler.couple_uncouple_nic'
        with mock.patch(func) as update_nic:
            h(self.env, dummy)

            self.assertTrue(update_nic.called)

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_mem_info_empty_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/meminfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_mem'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with([])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_mem_info_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/meminfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2'
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_mem'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with(['l1', 'l2'])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_vnics_info_empty_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/vnicsinfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_vnics'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with([])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_vnics_info_user_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/vnicsinfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2'
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_vnics'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with(['l1', 'l2'])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_cpu_info_empty_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/cpuinfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = ''
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_cpus'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with([])

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_cpu_info_userid_list(self, mock_validate):
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/cpuinfo'
        self.env['REQUEST_METHOD'] = 'GET'
        self.env['QUERY_STRING'] = 'userid=l1,l2'
        h = handler.SdkHandler()
        func = 'zvmsdk.api.SDKAPI.guest_inspect_cpus'
        with mock.patch(func) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with(['l1', 'l2'])

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
            h(self.env, dummy)

            attach.assert_called_once_with('1', {})

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_guest_detach_volume(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['wsgiorg.routing_args'] = ()
        self.env['PATH_INFO'] = '/guests/1/volumes'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        func = 'zvmsdk.sdkwsgi.handlers.volume.VolumeAction.detach'
        with mock.patch(func) as detach:
            h(self.env, dummy)

            detach.assert_called_once_with('1', {})


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
        function = 'zvmsdk.sdkwsgi.handlers.image.ImageAction'\
                   '.get_root_disk_size'
        with mock.patch(function) as get_size:
            h(self.env, dummy)

            get_size.assert_called_once_with('image1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_image_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/images'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.image.ImageAction.create'
        with mock.patch(function) as create:
            h(self.env, dummy)

            self.assertTrue(create.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_image_delete(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/images/image1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.image.ImageAction.delete'
        with mock.patch(function) as delete:
            h(self.env, dummy)

            delete.assert_called_once_with('image1')

    @mock.patch.object(tokens, 'validate')
    def test_image_query(self, mock_validate):
        self.env['PATH_INFO'] = '/images'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.image.ImageAction.query'
        with mock.patch(function) as query:
            h(self.env, dummy)

            query.assert_called_once_with(None)


class HostHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

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
    def test_host_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/host/info'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.get_info'
        with mock.patch(function) as get_info:
            get_info.return_value = ''
            h(self.env, dummy)

            self.assertTrue(get_info.called)

    @mock.patch.object(tokens, 'validate')
    def test_host_get_disk_info(self, mock_validate):
        self.env['PATH_INFO'] = '/host/disk_info/disk1'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.get_disk_info'
        with mock.patch(function) as get_disk_info:
            get_disk_info.return_value = ''
            h(self.env, dummy)

            get_disk_info.assert_called_once_with('disk1')


class VswitchHandlerNegativeTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    def test_vswitch_put_method_invalid(self):
        self.env['PATH_INFO'] = '/vswitchs'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        self.assertRaises(webob.exc.HTTPMethodNotAllowed,
                          h, self.env, dummy)


class VswitchHandlerTest(unittest.TestCase):
    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_vswitch_list(self, mock_validate):
        self.env['PATH_INFO'] = '/vswitchs'
        self.env['REQUEST_METHOD'] = 'GET'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.list'
        with mock.patch(function) as list:
            list.return_value = ''
            h(self.env, dummy)

            self.assertTrue(list.called)

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_vswitch_create(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/vswitchs'
        self.env['REQUEST_METHOD'] = 'POST'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.create'
        with mock.patch(function) as create:
            h(self.env, dummy)

            self.assertTrue(create.called)

    @mock.patch.object(tokens, 'validate')
    def test_vswitch_delete(self, mock_validate):
        self.env['PATH_INFO'] = '/vswitchs/vsw1'
        self.env['REQUEST_METHOD'] = 'DELETE'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.delete'
        with mock.patch(function) as delete:
            h(self.env, dummy)

            delete.assert_called_once_with('vsw1')

    @mock.patch('zvmsdk.sdkwsgi.util.extract_json')
    @mock.patch.object(tokens, 'validate')
    def test_vswitch_update(self, mock_validate, mock_json):
        mock_json.return_value = {}
        self.env['PATH_INFO'] = '/vswitchs/vsw1'
        self.env['REQUEST_METHOD'] = 'PUT'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.vswitch.VswitchAction.update'
        with mock.patch(function) as update:
            h(self.env, dummy)

            update.assert_called_once_with('vsw1', body={})
