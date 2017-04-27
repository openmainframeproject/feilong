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


from zvmsdk import client as zvmclient
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk.config import CONF
from zvmsdk.tests.unit import base


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self._zvmclient, zvmclient.XCATClient))


class SDKXCATCientTestCases(SDKZVMClientTestCase):
    """Test cases for xcat zvm client."""

    def setUp(self):
        super(SDKXCATCientTestCases, self).setUp()

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

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_mac(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/mac?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode mac"
        body = [commands]

        info = self._zvmclient._delete_mac("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_mac_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._delete_mac, 'fakenode')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_switch(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode switch"
        body = [commands]

        info = self._zvmclient._delete_switch("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_switch_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._delete_switch, 'fakenode')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_host(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/hosts?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode hosts"
        body = [commands]

        info = self._zvmclient._delete_host("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_host_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._delete_host, 'fakenode')

    @mock.patch('zvmsdk.client.XCATClient._image_performance_query')
    def test_get_image_performance_info(self, ipq):
        ipq.return_value = {
            u'FAKEVM': {
                'used_memory': u'5222192 KB',
                'used_cpu_time': u'25640530229 uS',
                'guest_cpus': u'2',
                'userid': u'FKAEVM',
                'max_memory': u'8388608 KB'}}
        info = self._zvmclient.get_image_performance_info('fakevm')
        self.assertEqual(info['used_memory'], '5222192 KB')

    @mock.patch('zvmsdk.utils.xdsh')
    def test_private_get_image_performance_info_single(self, dsh):
        dsh.return_value = {
            'info': [], 'node': [], 'errorcode': [[u'0']],
            'data': [['zhcp2: Number of virtual server IDs: 1 \n'
                      'zhcp2: Virtual server ID: fakevm\n'
                      'zhcp2: Record version: "1"\n'
                      'zhcp2: Guest flags: "0"\n'
                      'zhcp2: Used CPU time: "26238001893 uS"\n'
                      'zhcp2: Elapsed time: "89185770400 uS"\n'
                      'zhcp2: Minimum memory: "0 KB"\n'
                      'zhcp2: Max memory: "8388608 KB"\n'
                      'zhcp2: Shared memory: "5222192 KB"\n'
                      'zhcp2: Used memory: "5222184 KB"\n'
                      'zhcp2: Active CPUs in CEC: "44"\n'
                      'zhcp2: Logical CPUs in VM: "6"\n'
                      'zhcp2: Guest CPUs: "2"\nz'
                      'hcp2: Minimum CPU count: "2"\n'
                      'zhcp2: Max CPU limit: "10000"\n'
                      'zhcp2: Processor share: "100"\n'
                      'zhcp2: Samples CPU in use: "16659"\n'
                      'zhcp2: ,Samples CPU delay: "638"\n'
                      'zhcp2: Samples page wait: "0"\n'
                      'zhcp2: Samples idle: "71550"\n'
                      'zhcp2: Samples other: "337"\n'
                      'zhcp2: Samples total: "89184"\n'
                      'zhcp2: Guest name: "FAKEVM  "', None]], 'error': []}
        pi_info = self._zvmclient._image_performance_query('fakevm')
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "8388608 KB")

    @mock.patch('zvmsdk.utils.xdsh')
    def test_private_get_image_performance_info_multiple(self, dsh):
        dsh.return_value = {
            'info': [], 'node': [], 'errorcode': [[u'0']],
            'data': [['zhcp2: Number of virtual server IDs: 2 \n'
                      'zhcp2: Virtual server ID: fakevm\n'
                      'zhcp2: Record version: "1"\n'
                      'zhcp2: Guest flags: "0"\n'
                      'zhcp2: Used CPU time: "26238001893 uS"\n'
                      'zhcp2: Elapsed time: "89185770400 uS"\n'
                      'zhcp2: Minimum memory: "0 KB"\n'
                      'zhcp2: Max memory: "8388608 KB"\n'
                      'zhcp2: Shared memory: "5222192 KB"\n'
                      'zhcp2: Used memory: "5222184 KB"\n'
                      'zhcp2: Active CPUs in CEC: "44"\n'
                      'zhcp2: Logical CPUs in VM: "6"\n'
                      'zhcp2: Guest CPUs: "2"\nz'
                      'hcp2: Minimum CPU count: "2"\n'
                      'zhcp2: Max CPU limit: "10000"\n'
                      'zhcp2: Processor share: "100"\n'
                      'zhcp2: Samples CPU in use: "16659"\n'
                      'zhcp2: ,Samples CPU delay: "638"\n'
                      'zhcp2: Samples page wait: "0"\n'
                      'zhcp2: Samples idle: "71550"\n'
                      'zhcp2: Samples other: "337"\n'
                      'zhcp2: Samples total: "89184"\n'
                      'zhcp2: Guest name: "FAKEVM  "\n'
                      'zhcp2: \n'
                      'zhcp2: Virtual server ID: fakevm2\n'
                      'zhcp2: Record version: "1"\n'
                      'zhcp2: Guest flags: "0"\n'
                      'zhcp2: Used CPU time: "26238001893 uS"\n'
                      'zhcp2: Elapsed time: "89185770400 uS"\n'
                      'zhcp2: Minimum memory: "0 KB"\n'
                      'zhcp2: Max memory: "8388608 KB"\n'
                      'zhcp2: Shared memory: "5222192 KB"\n'
                      'zhcp2: Used memory: "5222184 KB"\n'
                      'zhcp2: Active CPUs in CEC: "44"\n'
                      'zhcp2: Logical CPUs in VM: "6"\n'
                      'zhcp2: Guest CPUs: "1"\nz'
                      'hcp2: Minimum CPU count: "1"\n'
                      'zhcp2: Max CPU limit: "10000"\n'
                      'zhcp2: Processor share: "100"\n'
                      'zhcp2: Samples CPU in use: "16659"\n'
                      'zhcp2: ,Samples CPU delay: "638"\n'
                      'zhcp2: Samples page wait: "0"\n'
                      'zhcp2: Samples idle: "71550"\n'
                      'zhcp2: Samples other: "337"\n'
                      'zhcp2: Samples total: "89184"\n'
                      'zhcp2: Guest name: "FAKEVM2 "\n', None]], 'error': []}
        pi_info = self._zvmclient._image_performance_query(['fakevm',
                                                            'fakevm2'])
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "8388608 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM2']['guest_cpus'], "1")
        self.assertEqual(pi_info['FAKEVM2']['userid'], "FAKEVM2")
        self.assertEqual(pi_info['FAKEVM2']['max_memory'], "8388608 KB")

    @mock.patch('zvmsdk.utils.xdsh')
    def test_private_get_image_performance_info_err1(self, dsh):
        dsh.return_value = {}
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                          self._zvmclient._image_performance_query, 'fakevm')

    @mock.patch('zvmsdk.utils.xdsh')
    def test_private_get_image_performance_info_err21(self, dsh):
        dsh.return_value = {'data': [[]]}
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                          self._zvmclient._image_performance_query, 'fakevm')

    @mock.patch.object(zvmclient.XCATClient, '_add_switch')
    @mock.patch.object(zvmclient.XCATClient, '_add_mac')
    @mock.patch.object(zvmclient.XCATClient, '_delete_mac')
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    def test_create_port(self, _get_hcp_info, _delete_mac,
                         _add_mac, _add_switch):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                      'nodename': "fakehcp",
                                      'userid': "fakeuserid"}
        self._zvmclient.create_port("fakenode", "face_nic",
                                    "fake_mac", "fake_vdev")
        _get_hcp_info.assert_called_once_with()
        zhcpnode = _get_hcp_info.return_value['nodename']
        _delete_mac.assert_called_once_with("fakenode")
        _add_mac.assert_called_once_with("fakenode", "fake_vdev",
                                          "fake_mac", zhcpnode)
        _add_switch.assert_called_once_with("fakenode", "fake_nic"
                                             "fake_vdev", zhcpnode)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mac(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/mac?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "mac.node=fakenode" + " mac.mac=00:00:00:00:00:00"
        commands += " mac.interface=fake"
        commands += " mac.comments=fakezhcp"
        body = [commands]

        info = self._zvmclient._add_mac("fakenode", "fake",
                                        "00:00:00:00:00:00", "fakezhcp")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mac_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_mac,
                          "fakenode", "fake",
                          "00:00:00:00:00:00", "fakezhcp")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "switch.node=fakenode" + " switch.port=fake-port"
        commands += " switch.interface=fake"
        commands += " switch.comments=fakezhcp"
        body = [commands]

        info = self._zvmclient._add_switch("fakenode", "fake-port",
                                        "fake", "fakezhcp")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_switch,
                          "fakenode", "fake-port",
                          "fake", "fakezhcp")
