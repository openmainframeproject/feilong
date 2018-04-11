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

from zvmsdk.tests.sdkwsgi import base
from zvmsdk import config
from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


CONF = config.CONF


class HostTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(HostTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()
        # test change bind_port
        self.set_conf('sdkserver', 'bind_port', 3123)
        self.client = test_sdkwsgi.TestSDKClient()

    def test_host_info(self):
        self.record_logfile_position()
        resp = self.client.api_request(url='/host')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_host_info', resp.content)

    def test_host_disk_info(self):
        self.record_logfile_position()
        url = '/host/diskpool?poolname=%s' % 'ECKD:xcateckd'
        resp = self.client.api_request(url)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_host_disk_info', resp.content)

    def test_host_disk_info_incorrect(self):
        self.record_logfile_position()
        # disk pool not found
        url = '/host/diskpool?poolname=%s' % 'ECKD:dummy'
        resp = self.client.api_request(url)
        self.assertEqual(404, resp.status_code)

        self.record_logfile_position()
        # disk format not correct
        url = '/host/diskpool?poolname=%s' % 'ECKD'
        resp = self.client.api_request(url)
        self.assertEqual(400, resp.status_code)

        # disk type not correct
        self.record_logfile_position()
        url = '/host/diskpool?poolname=%s' % 'xxxx:dummy'
        resp = self.client.api_request(url)
        self.assertEqual(400, resp.status_code)
