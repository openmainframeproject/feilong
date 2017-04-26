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

from zvmsdk.config import CONF
import zvmsdk.utils as zvmutils
import zvmsdk.client as zvmclient
from zvmsdk.tests.unit import base


class SDKClientTestCase(base.SDKTestCase):
    def setUp(self):
        self._zvmclient = zvmclient.get_zvmclient()

    @mock.patch.object(zvmclient.XCATClient, 'get_host_info')
    @mock.patch.object(zvmclient.XCATClient, '_construct_zhcp_info')
    def test_get_hcp_info(self, _construct_zhcp_info, get_host_info):
        self._zvmclient.get_hcp_info()
        get_host_info.assert_called_once_with()
        self._zvmclient.get_hcp_info("fakehcp.fake.com")
        _construct_zhcp_info.assert_called_once_with("fakehcp.fake.com")

    @mock.patch.object(zvmutils, 'get_userid')
    def test_construct_zhcp_info(self, get_userid):
        get_userid.return_value = "fkuserid"
        hcp_info = self._zvmclient._construct_zhcp_info("fakehcp.fake.com")
        get_userid.assert_called_once_with("fakehcp")
        self.assertEqual(hcp_info['hostname'], "fakehcp.fake.com")
        self.assertEqual(hcp_info['nodename'], "fakehcp")
        self.assertEqual(hcp_info['userid'], "fkuserid")

    def _fake_vm_list(self):
        vm_list = ['#node,hcp,userid,nodetype,parent,comments,disable',
                     '"fakehcp","fakehcp.fake.com","HCP","vm","fakenode"',
                     '"fakenode","fakehcp.fake.com",,,,,',
                     '"os000001","fakehcp.fake.com","OS000001",,,,']
        return vm_list

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmclient.XCATClient, 'get_hcp_info')
    def test_get_vm_list(self, get_hcp_info, xrequest):
        get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
        fake_vm_list = self._fake_vm_list()
        fake_vm_list.append('"xcat","fakexcat.fake.com",,,,,')
        xrequest.return_value = {'data': [fake_vm_list, ]}
        vm_list = self._zvmclient.get_vm_list()
        self.assertIn("os000001", vm_list)
        self.assertNotIn("xcat", vm_list)
        self.assertNotIn("fakehcp", vm_list)
        url = "/xcatws/tables/zvm?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        xrequest.assert_called_once_with("GET", url)
