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


import os
import mock

from smutLayer import smut

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import smutclient
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKSMUTClientTestCases(base.SDKTestCase):
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

    @mock.patch.object(smutclient.SMUTClient, 'add_mdisks')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_create_vm(self, request, add_mdisks):
        user_id = 'fakeuser'
        cpu = 2
        memory = 1024
        disk_list = [{'size': '1g',
                      'is_boot_disk': True,
                      'disk_pool': 'ECKD:eckdpool1',
                      'format': 'ext3'}]
        profile = 'dfltprof'
        base.set_conf('zvm', 'logonby_users', 'lbyuser1 lbyuser2')
        base.set_conf('zvm', 'user_root_vdev', '0100')
        rd = ('makevm fakeuser directory LBYONLY 1024m G --cpus 2 '
              '--profile dfltprof --logonby "lbyuser1 lbyuser2" --ipl 0100')
        self._smutclient.create_vm(user_id, cpu, memory, disk_list, profile)
        request.assert_called_once_with(rd)
        add_mdisks.assert_called_once_with(user_id, disk_list)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_add_mdisk(self, request):
        userid = 'fakeuser'
        disk = {'size': '1g',
                'disk_pool': 'ECKD:eckdpool1',
                'format': 'ext3'}
        vdev = '0101'
        rd = ('changevm fakeuser add3390 eckdpool1 0101 1g --mode MR '
              '--filesystem ext3')

        self._smutclient._add_mdisk(userid, disk, vdev),
        request.assert_called_once_with(rd)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_authorize_iucv_client(self, request):
        fake_userid = 'FakeID'
        requestData = "ChangeVM FakeID punchfile /tmp/FakeID/iucvauth.sh" + \
                      " --class x"
        request.return_value = {'overallRC': 0}
        self._smutclient.guest_authorize_iucv_client(fake_userid)
        request.assert_called_once_with(requestData)
        self.assertIs(os.path.exists, False)
