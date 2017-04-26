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
from zvmsdk import hostops
from zvmsdk import utils as zvmutils
from zvmsdk.tests.unit import base


class SDKHostOpsTestCase(base.SDKTestCase):
    def setUp(self):
        self._hostops = hostops.get_hostops()

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

    @mock.patch.object(zvmutils, 'get_userid')
    @mock.patch('zvmsdk.client.XCATClient.get_diskpool_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_host_info(self, xrequest, get_diskpool_info, get_userid):
        xrequest.return_value = self._fake_host_rinv_info()
        get_diskpool_info.return_value = {'disk_total': 100, 'disk_used': 80,
                                          'disk_available': 20}
        get_userid.return_value = "fakehcp"
        host_info = self._hostops.get_host_info('fakenode')
        self.assertEqual(host_info['vcpus'], 10)
        self.assertEqual(host_info['hypervisor_version'], 610)
        self.assertEqual(host_info['disk_total'], 100)
        self.assertEqual(self._hostops._zvmclient._zhcp_info,
                         {'hostname': 'fakehcp.fake.com',
                          'nodename': 'fakehcp',
                          'userid': 'fakehcp'})
        url = "/xcatws/nodes/fakenode/inventory?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        xrequest.assert_called_once_with('GET', url)
        get_diskpool_info.assert_called_once_with('fakenode')
        get_userid.assert_called_once_with("fakehcp")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_diskpool_info(self, xrequest):
        xrequest.return_value = self._fake_disk_info()
        dp_info = self._hostops.get_diskpool_info('fakenode', 'FAKEDP')
        url = "/xcatws/nodes/fakenode/inventory?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json" +\
                "&field=--diskpoolspace&field=FAKEDP"
        xrequest.assert_called_once_with('GET', url)
        self.assertEqual(dp_info['disk_total'], 406105)
        self.assertEqual(dp_info['disk_used'], 367263)
        self.assertEqual(dp_info['disk_available'], 38843)

    @mock.patch.object(zvmclient.XCATClient, 'get_hcp_info')
    def test_get_hcp_info(self, get_hcp_info):
        self._hostops.get_hcp_info("fakehcp.fake.com")
        get_hcp_info.assert_called_once_with("fakehcp.fake.com")

    @mock.patch.object(zvmclient.XCATClient, 'get_vm_list')
    def test_get_vm_list(self, get_vm_list):
        self._hostops.get_vm_list()
        get_vm_list.assert_called_once_with()
