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


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self._zvmclient, zvmclient.XCATClient))

    def _fake_host_rinv_info(self):
        fake_host_rinv_info = ["fakenode: z/VM Host: FAKENODE\n"
                               "fakenode: zHCP: fakehcp.fake.com\n"
                               "fakenode: CEC Vendor: FAKE\n"
                               "fakenode: CEC Model: 2097\n"
                               "fakenode: Hypervisor OS: z/VM 6.1.0\n"
                               "fakenode: Hypervisor Name: fakenode\n"
                               "fakenode: Architecture: s390x\n"
                               "fakenode: LPAR CPU Total: 10\n"
                               "fakenode: LPAR CPU Used: 10\n"
                               "fakenode: LPAR Memory Total: 16G\n"
                               "fakenode: LPAR Memory Offline: 0\n"
                               "fakenode: LPAR Memory Used: 16.0G\n"
                               "fakenode: IPL Time:"
                               "IPL at 03/13/14 21:43:12 EDT\n"]
        return {'info': [fake_host_rinv_info, ]}

    def _fake_disk_info(self):
        fake_disk_info = ["fakenode: FAKEDP Total: 406105.3 G\n"
                          "fakenode: FAKEDP Used: 367262.6 G\n"
                          "fakenode: FAKEDP Free: 38842.7 G\n"]
        return {'info': [fake_disk_info, ]}

    @mock.patch.object(zvmclient.XCATClient, '_construct_zhcp_info')
    @mock.patch.object(zvmclient.XCATClient, 'get_diskpool_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_host_info(self, xrequest, get_diskpool_info,
                           _construct_zhcp_info):
        xrequest.return_value = self._fake_host_rinv_info()
        get_diskpool_info.return_value = {'disk_total': 100, 'disk_used': 80,
                                          'disk_available': 20}
        fake_zhcp_info = {'hostname': 'fakehcp.fake.com',
                          'nodename': 'fakehcp',
                          'userid': 'fakehcp'}
        _construct_zhcp_info.return_value = fake_zhcp_info
        host_info = self._zvmclient.get_host_info('fakenode')
        self.assertEqual(host_info['vcpus'], 10)
        self.assertEqual(host_info['hypervisor_version'], 610)
        self.assertEqual(host_info['disk_total'], 100)
        self.assertEqual(self._zvmclient._zhcp_info, fake_zhcp_info)
        url = "/xcatws/nodes/fakenode/inventory?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        xrequest.assert_called_once_with('GET', url)
        get_diskpool_info.assert_called_once_with('fakenode')
        _construct_zhcp_info.assert_called_once_with("fakehcp.fake.com")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_diskpool_info(self, xrequest):
        xrequest.return_value = self._fake_disk_info()
        dp_info = self._zvmclient.get_diskpool_info('fakenode', 'FAKEDP')
        url = "/xcatws/nodes/fakenode/inventory?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json" +\
                "&field=--diskpoolspace&field=FAKEDP"
        xrequest.assert_called_once_with('GET', url)
        self.assertEqual(dp_info['disk_total'], 406105)
        self.assertEqual(dp_info['disk_used'], 367263)
        self.assertEqual(dp_info['disk_available'], 38843)

    @mock.patch.object(zvmclient.XCATClient, 'get_host_info')
    @mock.patch.object(zvmclient.XCATClient, '_construct_zhcp_info')
    def test_get_hcp_info(self, _construct_zhcp_info, get_host_info):
        self._zvmclient._get_hcp_info()
        get_host_info.assert_called_once_with()
        self._zvmclient._get_hcp_info("fakehcp.fake.com")
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
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    def test_get_vm_list(self, _get_hcp_info, xrequest):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
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
