# Copyright 2017,2022 IBM Corp.
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
import json
import mock
import unittest

from zvmsdk import config
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi.handlers import volume


CONF = config.CONF

FAKE_UUID = '00000000-0000-0000-0000-000000000000'


def set_conf(section, opt, value):
    CONF[section][opt] = value


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
        set_conf('wsgi', 'auth', 'none')
        expired_elapse = datetime.timedelta(seconds=100)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, 'username')

        self.req = FakeReq()
        self.req.headers['X-Auth-Token'] = payload

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_volume_attach(self, mock_attach):
        mock_attach.return_value = {'overallRC': 0}
        connection_info = {"assigner_id": "username", "zvm_fcp": ["1fc5"],
                           "target_wwpn": ["0x5005076801401234"],
                           "target_lun": "0x0026000000000000",
                           "os_version": "rhel7.2",
                           "multipath": "true", "mount_point": ""}
        body_str = {"info": {"connection": connection_info}}
        self.req.body = json.dumps(body_str)

        volume.volume_attach(self.req)
        mock_attach.assert_called_once_with(
            'volume_attach',
            connection_info)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_volume_detach(self, mock_detach):
        mock_detach.return_value = {'overallRC': 0}
        connection_info = {"assigner_id": "username", "zvm_fcp": ["1fc5"],
                           "target_wwpn": ["0x5005076801401234"],
                           "target_lun": "0x0026000000000000",
                           "os_version": "rhel7.2",
                           "multipath": "true", "mount_point": ""}
        body_str = {"info": {"connection": connection_info}}
        self.req.body = json.dumps(body_str)

        volume.volume_detach(self.req)
        mock_detach.assert_called_once_with(
            'volume_detach',
            connection_info)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_refresh_volume_bootmap(self, mock_refresh_bootmap):
        mock_refresh_bootmap.return_value = {'overallRC': 0}
        fcpchannels = ['5d71']
        wwpns = ['5005076802100c1b', '5005076802200c1b']
        lun = '0000000000000000'
        wwid = '600507640083826de00000000000605b'
        fcp_template_id = 'fake_fcp_tmpl_id'
        info = {"fcpchannel": fcpchannels,
                "wwpn": wwpns,
                "lun": lun,
                "wwid": wwid,
                "fcp_template_id": fcp_template_id}
        body_str = {"info": info}
        self.req.body = json.dumps(body_str)

        volume.volume_refresh_bootmap(self.req)
        mock_refresh_bootmap.assert_called_once_with(
            'volume_refresh_bootmap',
            fcpchannels, wwpns, lun, wwid, '', [], fcp_template_id)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_get_volume_connector(self, mock_send_request, mock_path_item):
        mock_send_request.return_value = {'overallRC': 0}
        mock_path_item.return_value = 'fakeuser'
        info = {'reserve': True,
                'fcp_template_id': 'faketmpl'}
        body_str = {"info": info}
        self.req.body = json.dumps(body_str)
        # to pass validataion.query_schema
        self.req.environ['wsgiorg.routing_args'] = (
            (), {'userid': 'fakeuser'})
        volume.get_volume_connector(self.req)
        mock_send_request.assert_called_once_with('get_volume_connector', 'fakeuser', True, 'faketmpl', None)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_get_fcp_usage(self, mock_send_request, mock_path_item):
        mock_send_request.return_value = {'overallRC': 0}
        mock_path_item.return_value = '1a00'
        # to pass validataion.query_schema
        self.req.environ['wsgiorg.routing_args'] = (
            (), {'fcp_id': '1a00'})
        volume.get_fcp_usage(self.req)
        mock_send_request.assert_called_once_with('get_fcp_usage', '1a00')

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_set_fcp_usage(self, mock_send_request, mock_path_item):
        mock_send_request.return_value = {'overallRC': 0}
        mock_path_item.return_value = '1a00'
        info = {'userid': 'fakeuser',
                'reserved': 1,
                'connections': 2,
                'fcp_template_id': 'faketmpl'}
        body_str = {"info": info}
        self.req.body = json.dumps(body_str)
        volume.set_fcp_usage(self.req)
        mock_send_request.assert_called_once_with('set_fcp_usage', '1a00', 'fakeuser', 1, 2, 'faketmpl')

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_create_fcp_template(self, mock_send_request):
        mock_send_request.return_value = {'overallRC': 0}
        body = {'name': 'tmpl name',
                'description': 'desc text',
                'fcp_devices': '1a00-1a0f;1b00, 1b05-1b0f',
                'host_default': 'yes',
                'storage_providers': [],
                'min_fcp_paths_count': 2}
        self.req.body = json.dumps(body)
        volume.create_fcp_template(self.req)
        mock_send_request.assert_called_once_with('create_fcp_template', 'tmpl name',
                                                  description='desc text',
                                                  fcp_devices='1a00-1a0f;1b00, 1b05-1b0f',
                                                  host_default=True,
                                                  default_sp_list=[], min_fcp_paths_count=2)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_create_fcp_template_default_values(self, mock_send_request):
        """Test the default values was set correctly when create fcp template."""
        mock_send_request.return_value = {'overallRC': 0}
        body = {'name': 'tmpl name'}
        self.req.body = json.dumps(body)
        volume.create_fcp_template(self.req)
        mock_send_request.assert_called_once_with('create_fcp_template', 'tmpl name', description='',
                                                  fcp_devices='', host_default=False, default_sp_list=[],
                                                  min_fcp_paths_count=None)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_edit_fcp_template(self, mock_send_request):
        mock_send_request.return_value = {'overallRC': 0}
        body_str = {
            'storage_providers': ['sp8', 'sp9'],
            'host_default': True,
            'name': 'fake_name'}
        request_args = {
            'default_sp_list': ['sp8', 'sp9'],
            'host_default': True,
            'name': 'fake_name'}
        self.req.body = json.dumps(body_str)
        # tmpl_id lenght must be 36 defined in
        # zvmsdk/sdkwsgi/validation/parameter_types.py
        tmpl_id = 'fake_template_id' + '0' * 20
        self.req.environ['wsgiorg.routing_args'] = (
            (), {'template_id': tmpl_id})
        volume.edit_fcp_template(self.req)
        mock_send_request.assert_called_once_with(
            'edit_fcp_template', tmpl_id,
            description=None, fcp_devices=None, min_fcp_paths_count=None, **request_args)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_get_fcp_templates(self, mock_send_request):
        mock_send_request.return_value = {'overallRC': 0}
        # To pass validataion.query_schema
        self.req.environ['wsgiorg.routing_args'] = (
            (), {'template_id_list': ['id1', 'id2']})
        self.req.GET = {'template_id_list': ['id1', 'id2'],
                        'assigner_id': 'fakeuser',
                        'storage_providers': ['v7k']}
        volume.get_fcp_templates(self.req)
        mock_send_request.assert_called_once_with('get_fcp_templates', ['id1', 'id2'],
                                                  'fakeuser', ['v7k'], None)

    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_get_fcp_templates_details(self, mock_send_request):
        mock_send_request.return_value = {'overallRC': 0}
        # To pass validataion.query_schema
        self.req.environ['wsgiorg.routing_args'] = (
            (), {'template_id_list': ['id1', 'id2']})
        self.req.GET = {'template_id_list': ['id1', 'id2']}
        volume.get_fcp_templates_details(self.req)
        mock_send_request.assert_called_once_with('get_fcp_templates_details', ['id1', 'id2'],
                                                  raw=False, statistics=True, sync_with_zvm=False)

    @mock.patch.object(util, 'wsgi_path_item')
    @mock.patch('zvmconnector.connector.ZVMConnector.send_request')
    def test_delete_fcp_template(self, mock_send_request, mock_path_item):
        mock_send_request.return_value = {'overallRC': 0}
        mock_path_item.return_value = 'fake tmpl id'
        volume.delete_fcp_template(self.req)
        mock_send_request.assert_called_once_with('delete_fcp_template', 'fake tmpl id')
