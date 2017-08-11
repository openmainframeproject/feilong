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

from smutLayer import smut

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import smutclient
from zvmsdk.tests.unit import base
from zvmsdk.tests.unit import test_zvmclient


CONF = config.CONF


class SDKSMUTClientTestCases(test_zvmclient.SDKZVMClientTestCase):
    """Test cases for xcat zvm client."""

    @classmethod
    def setUpClass(cls):
        super(SDKSMUTClientTestCases, cls).setUpClass()
        cls.old_client_type = CONF.zvm.client_type
        base.set_conf('zvm', 'client_type', 'smut')

    @classmethod
    def tearDownClass(cls):
        base.set_conf('zvm', 'client_type', cls.old_client_type)
        super(SDKSMUTClientTestCases, cls).tearDownClass()

    def setUp(self):
        self._smutclient = smutclient.SMUTClient()

    @mock.patch.object(smut.SMUT, 'request')
    def test_private_request_success(self, request):
        requestData = "fake request"
        request.return_value = {'overallRC': 0}
        self._smutclient._request(requestData)
        request.assert_called_once_with(requestData)

    @mock.patch.object(smut.SMUT, 'request')
    def test_private_request_failed(self, request):
        requestData = "fake request"
        request.return_value = {'overallRC': 1, 'logEntries': []}
        self.assertRaises(exception.ZVMSMUTRequestFailed,
                          self._smutclient._request, requestData)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_start(self, request):
        fake_userid = 'FakeID'
        requestData = "PowerVM FakeID on"
        request.return_value = {'overallRC': 0}
        self._smutclient.guest_start(fake_userid)
        request.assert_called_once_with(requestData)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_stop(self, request):
        fake_userid = 'FakeID'
        requestData = "PowerVM FakeID off"
        request.return_value = {'overallRC': 0}
        self._smutclient.guest_stop(fake_userid)
        request.assert_called_once_with(requestData)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_get_power_state(self, request):
        fake_userid = 'FakeID'
        requestData = "PowerVM FakeID status"
        request.return_value = {'overallRC': 0,
                                'response': [fake_userid + ': on']}
        status = self._smutclient.get_power_state(fake_userid)
        request.assert_called_once_with(requestData)
        self.assertEqual('on', status)
