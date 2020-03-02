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
import json
import mock
import unittest

from zvmsdk import config
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
    def test_refresh_volume_bootmap(self, mock_detach):
        mock_detach.return_value = {'overallRC': 0}
        fcpchannels = ['5d71']
        wwpns = ['5005076802100c1b', '5005076802200c1b']
        lun = '0000000000000000'
        info = {"fcpchannel": fcpchannels,
                "wwpn": wwpns,
                "lun": lun}
        body_str = {"info": info}
        self.req.body = json.dumps(body_str)

        volume.volume_refresh_bootmap(self.req)
        mock_detach.assert_called_once_with(
            'volume_refresh_bootmap',
            fcpchannels, wwpns, lun, False)
