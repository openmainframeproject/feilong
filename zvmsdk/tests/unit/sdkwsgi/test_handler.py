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


class GuestHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_guest_list(self, mock_validate):
        self.env['PATH_INFO'] = '/guest'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMHandler.list') \
            as list:
            h(self.env, dummy)

            self.assertTrue(list.called)

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/guest/1/info'
        h = handler.SdkHandler()
        with mock.patch('zvmsdk.sdkwsgi.handlers.guest.VMHandler.get_info') \
            as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with('1')

    @mock.patch.object(tokens, 'validate')
    def test_guest_get_power_state(self, mock_validate):
        self.env['PATH_INFO'] = '/guest/1/power_state'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.guest.VMHandler'\
                   '.get_power_state'
        with mock.patch(function) as get_power:
            h(self.env, dummy)

            get_power.assert_called_once_with('1')


class ImageHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_image_root_disk_size(self, mock_validate):
        self.env['PATH_INFO'] = '/image/image1/root_disk_size'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.image.ImageAction'\
                   '.get_root_disk_size'
        with mock.patch(function) as get_size:
            h(self.env, dummy)

            get_size.assert_called_once_with('image1')


class HostHandlerTest(unittest.TestCase):

    def setUp(self):
        self.env = env

    @mock.patch.object(tokens, 'validate')
    def test_host_list(self, mock_validate):
        self.env['PATH_INFO'] = '/host/host1'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.list'
        with mock.patch(function) as list:
            h(self.env, dummy)

            list.assert_called_once_with('host1')

    @mock.patch.object(tokens, 'validate')
    def test_host_get_info(self, mock_validate):
        self.env['PATH_INFO'] = '/host/host1/info'
        h = handler.SdkHandler()
        function = 'zvmsdk.sdkwsgi.handlers.host.HostAction.get_info'
        with mock.patch(function) as get_info:
            h(self.env, dummy)

            get_info.assert_called_once_with('host1')
