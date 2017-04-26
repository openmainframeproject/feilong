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

import zvmsdk.client as zvmclient
from zvmsdk import hostops
from zvmsdk.tests.unit import base


class SDKHostOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._hostops = hostops.get_hostops()

    @mock.patch.object(zvmclient.XCATClient, 'get_host_info')
    def test_get_host_info(self, get_host_info):
        self._hostops.get_host_info("zvmhost")
        get_host_info.assert_called_once_with("zvmhost")

    @mock.patch.object(zvmclient.XCATClient, 'get_diskpool_info')
    def test_get_diskpool_info(self, get_diskpool_info):
        self._hostops.get_diskpool_info("zvmhost", "fakepool")
        get_diskpool_info.assert_called_once_with("zvmhost", "fakepool")

    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_get_vm_list(self, get_vm_list):
        self._hostops.get_vm_list()
        get_vm_list.assert_called_once_with()
