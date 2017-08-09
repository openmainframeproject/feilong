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
import os
import shutil
import tarfile
import xml

from zvmsdk import client as zvmclient
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk import config
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()
        self._xcat_url = zvmutils.get_xcat_url()
        self._pathutils = zvmutils.PathUtils()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self._zvmclient, zvmclient.XCATClient))


class SDKXCATClientTestCases(SDKZVMClientTestCase):
    """Test cases for xcat zvm client."""

    @classmethod
    def setUpClass(cls):
        super(SDKXCATClientTestCases, cls).setUpClass()
        cls.old_client_type = CONF.zvm.client_type
        base.set_conf('zvm', 'client_type', 'xcat')

    @classmethod
    def tearDownClass(cls):
        base.set_conf('zvm', 'client_type', cls.old_client_type)
        super(SDKXCATClientTestCases, cls).tearDownClass()

    def setUp(self):
        super(SDKXCATClientTestCases, self).setUp()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_power_state(self, xrequest):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.rpower('/' + fake_userid)
        fake_body = ['on']
        self._zvmclient._power_state(fake_userid, 'PUT', 'on')
        xrequest.assert_called_once_with('PUT', fake_url, fake_body)

    @mock.patch.object(zvmclient.XCATClient, '_power_state')
    def test_guest_start(self, power_state):
        fake_userid = 'fake_userid'
        self._zvmclient.guest_start(fake_userid)
        power_state.assert_called_once_with(fake_userid, 'PUT', 'on')

    @mock.patch.object(zvmclient.XCATClient, '_power_state')
    def test_guest_stop(self, power_state):
        fake_userid = 'fakeuser'
        self._zvmclient.guest_stop(fake_userid)
        power_state.assert_called_once_with(fake_userid, 'PUT', 'off')

    @mock.patch.object(zvmclient.XCATClient, '_power_state')
    def test_get_power_state(self, power_state):
        fake_userid = 'fake_userid'
        fake_ret = {'info': [[fake_userid + ': on\n']],
                    'node': [],
                    'errocode': [],
                    'data': []}
        power_state.return_value = fake_ret
        ret = self._zvmclient.get_power_state(fake_userid)

        power_state.assert_called_once_with(fake_userid, 'GET', 'stat')
        self.assertEqual('on', ret)

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
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_host_info(self, xrequest, _construct_zhcp_info):
        xrequest.return_value = self._fake_host_rinv_info()
        fake_zhcp_info = {'hostname': 'fakehcp.fake.com',
                          'nodename': 'fakehcp',
                          'userid': 'fakehcp'}
        _construct_zhcp_info.return_value = fake_zhcp_info
        host_info = self._zvmclient.get_host_info()
        self.assertEqual(host_info['zvm_host'], "FAKENODE")
        self.assertEqual(self._zvmclient._zhcp_info, fake_zhcp_info)
        url = "/xcatws/nodes/" + CONF.zvm.host +\
                "/inventory?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password +\
                "&format=json"
        xrequest.assert_called_once_with('GET', url)
        _construct_zhcp_info.assert_called_once_with("fakehcp.fake.com")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_diskpool_info(self, xrequest):
        xrequest.return_value = self._fake_disk_info()
        dp_info = self._zvmclient.get_diskpool_info('FAKEDP')
        url = "/xcatws/nodes/" + CONF.zvm.host +\
                "/inventory?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password +\
                "&format=json&field=--diskpoolspace&field=FAKEDP"
        xrequest.assert_called_once_with('GET', url)
        self.assertEqual(dp_info['disk_total'], "406105.3 G")
        self.assertEqual(dp_info['disk_used'], "367262.6 G")
        self.assertEqual(dp_info['disk_available'], "38842.7 G")

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

    @mock.patch('zvmsdk.client.XCATClient.image_performance_query')
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

    @mock.patch('zvmsdk.client.XCATClient.image_performance_query')
    def test_get_image_performance_info_not_exist(self, ipq):
        ipq.return_value = {}
        info = self._zvmclient.get_image_performance_info('fakevm')
        self.assertEqual(info, None)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_image_performance_query_single(self, dsh, _get_hcp_info):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
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
        pi_info = self._zvmclient.image_performance_query('fakevm')
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM']['elapsed_cpu_time'],
                         "89185770400 uS")
        self.assertEqual(pi_info['FAKEVM']['min_cpu_count'], "2")
        self.assertEqual(pi_info['FAKEVM']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_in_use'], "16659")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_delay'], "638")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "8388608 KB")
        self.assertEqual(pi_info['FAKEVM']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM']['shared_memory'], "5222192 KB")

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_image_performance_query_multiple(self, dsh, _get_hcp_info):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
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
                      'zhcp2: Shared memory: "5222190 KB"\n'
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
        pi_info = self._zvmclient.image_performance_query(['fakevm',
                                                            'fakevm2'])
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM']['elapsed_cpu_time'],
                         "89185770400 uS")
        self.assertEqual(pi_info['FAKEVM']['min_cpu_count'], "2")
        self.assertEqual(pi_info['FAKEVM']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_in_use'], "16659")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_delay'], "638")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "8388608 KB")
        self.assertEqual(pi_info['FAKEVM']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM']['shared_memory'], "5222192 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_memory'], "5222184 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_cpu_time'], "26238001893 uS")
        self.assertEqual(pi_info['FAKEVM2']['elapsed_cpu_time'],
                         "89185770400 uS")
        self.assertEqual(pi_info['FAKEVM2']['min_cpu_count'], "1")
        self.assertEqual(pi_info['FAKEVM2']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM2']['samples_cpu_in_use'], "16659")
        self.assertEqual(pi_info['FAKEVM2']['samples_cpu_delay'], "638")
        self.assertEqual(pi_info['FAKEVM2']['guest_cpus'], "1")
        self.assertEqual(pi_info['FAKEVM2']['userid'], "FAKEVM2")
        self.assertEqual(pi_info['FAKEVM2']['max_memory'], "8388608 KB")
        self.assertEqual(pi_info['FAKEVM2']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM2']['shared_memory'], "5222190 KB")

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_image_performance_query_err1(self, dsh, _get_hcp_info):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
        dsh.return_value = {}
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                          self._zvmclient.image_performance_query, 'fakevm')

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_image_performance_query_err2(self, dsh, _get_hcp_info):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
        dsh.return_value = {'data': [[]]}
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                          self._zvmclient.image_performance_query, 'fakevm')

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_image_performance_query_err3(self, dsh, _get_hcp_info):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
        dsh.return_value = {
            'info': [], 'node': [], 'errorcode': [[u'0']],
            'data': [['zhcp2: Number of virtual server IDs: 1 ', None]],
            'error': []}
        pi_info = self._zvmclient.image_performance_query('fakevm')
        self.assertEqual(pi_info, {})

    @mock.patch('zvmsdk.client.XCATClient._get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_virtual_network_vswitch_query_iuo_stats(self, xdsh, get_hcp_info):
        get_hcp_info.return_value = {'hostname': 'fakehcp.ibm.com',
                                     'nodename': 'fakehcp',
                                     'userid': 'FAKEHCP'}
        vsw_data = ['zhcp11: vswitch count: 2\n'
                    'zhcp11: \n'
                    'zhcp11: vswitch number: 1\n'
                    'zhcp11: vswitch name: XCATVSW1\n'
                    'zhcp11: uplink count: 1\n'
                    'zhcp11: uplink_conn: 6240\n'
                    'zhcp11: uplink_fr_rx:     3658251\n'
                    'zhcp11: uplink_fr_rx_dsc: 0\n'
                    'zhcp11: uplink_fr_rx_err: 0\n'
                    'zhcp11: uplink_fr_tx:     4209828\n'
                    'zhcp11: uplink_fr_tx_dsc: 0\n'
                    'zhcp11: uplink_fr_tx_err: 0\n'
                    'zhcp11: uplink_rx:        498914052\n'
                    'zhcp11: uplink_tx:        2615220898\n'
                    'zhcp11: bridge_fr_rx:     0\n'
                    'zhcp11: bridge_fr_rx_dsc: 0\n'
                    'zhcp11: bridge_fr_rx_err: 0\n'
                    'zhcp11: bridge_fr_tx:     0\n'
                    'zhcp11: bridge_fr_tx_dsc: 0\n'
                    'zhcp11: bridge_fr_tx_err: 0\n'
                    'zhcp11: bridge_rx:        0\n'
                    'zhcp11: bridge_tx:        0\n'
                    'zhcp11: nic count: 2\n'
                    'zhcp11: nic_id: INST1 0600\n'
                    'zhcp11: nic_fr_rx:        573952\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        548780\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    4\n'
                    'zhcp11: nic_rx:           103024058\n'
                    'zhcp11: nic_tx:           102030890\n'
                    'zhcp11: nic_id: INST2 0600\n'
                    'zhcp11: nic_fr_rx:        17493\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        16886\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    4\n'
                    'zhcp11: nic_rx:           3111714\n'
                    'zhcp11: nic_tx:           3172646\n'
                    'zhcp11: vlan count: 0\n'
                    'zhcp11: \n'
                    'zhcp11: vswitch number: 2\n'
                    'zhcp11: vswitch name: XCATVSW2\n'
                    'zhcp11: uplink count: 1\n'
                    'zhcp11: uplink_conn: 6200\n'
                    'zhcp11: uplink_fr_rx:     1608681\n'
                    'zhcp11: uplink_fr_rx_dsc: 0\n'
                    'zhcp11: uplink_fr_rx_err: 0\n'
                    'zhcp11: uplink_fr_tx:     2120075\n'
                    'zhcp11: uplink_fr_tx_dsc: 0\n'
                    'zhcp11: uplink_fr_tx_err: 0\n'
                    'zhcp11: uplink_rx:        314326223',
                    'zhcp11: uplink_tx:        1503721533\n'
                    'zhcp11: bridge_fr_rx:     0\n'
                    'zhcp11: bridge_fr_rx_dsc: 0\n'
                    'zhcp11: bridge_fr_rx_err: 0\n'
                    'zhcp11: bridge_fr_tx:     0\n'
                    'zhcp11: bridge_fr_tx_dsc: 0\n'
                    'zhcp11: bridge_fr_tx_err: 0\n'
                    'zhcp11: bridge_rx:        0\n'
                    'zhcp11: bridge_tx:        0\n'
                    'zhcp11: nic count: 2\n'
                    'zhcp11: nic_id: INST1 1000\n'
                    'zhcp11: nic_fr_rx:        34958\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        16211\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    0\n'
                    'zhcp11: nic_rx:           4684435\n'
                    'zhcp11: nic_tx:           3316601\n'
                    'zhcp11: nic_id: INST2 1000\n'
                    'zhcp11: nic_fr_rx:        27211\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        12344\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    0\n'
                    'zhcp11: nic_rx:           3577163\n'
                    'zhcp11: nic_tx:           2515045\n'
                    'zhcp11: vlan count: 0',
                     None]
        xdsh.return_value = {'data': [vsw_data]}
        vsw_dict = self._zvmclient.virtual_network_vswitch_query_iuo_stats()
        self.assertEqual(2, len(vsw_dict['vswitches']))
        self.assertEqual(2, len(vsw_dict['vswitches'][1]['nics']))
        self.assertEqual('INST1',
                         vsw_dict['vswitches'][0]['nics'][0]['userid'])
        self.assertEqual('3577163',
                         vsw_dict['vswitches'][1]['nics'][1]['nic_rx'])

    @mock.patch('zvmsdk.client.XCATClient._get_hcp_info')
    @mock.patch('zvmsdk.utils.xdsh')
    def test_virtual_network_vswitch_query_iuo_stats_special(self, xdsh,
                                                             get_hcp_info):
        get_hcp_info.return_value = {'hostname': 'fakehcp.ibm.com',
                                     'nodename': 'fakehcp',
                                     'userid': 'FAKEHCP'}
        vsw_data = ['zhcp11: vswitch count: 2\n'
                    'zhcp11: \n'
                    'zhcp11: vswitch number: 1\n'
                    'zhcp11: vswitch name: XCATVSW1\n'
                    'zhcp11: uplink count: 1\n'
                    'zhcp11: uplink_conn: 6240\n'
                    'zhcp11: uplink_fr_rx:     3658251\n'
                    'zhcp11: uplink_fr_rx_dsc: 0\n'
                    'zhcp11: uplink_fr_rx_err: 0\n'
                    'zhcp11: uplink_fr_tx:     4209828\n'
                    'zhcp11: uplink_fr_tx_dsc: 0\n'
                    'zhcp11: uplink_fr_tx_err: 0\n'
                    'zhcp11: uplink_rx:        498914052\n'
                    'zhcp11: uplink_tx:        2615220898\n'
                    'zhcp11: bridge_fr_rx:     0\n'
                    'zhcp11: bridge_fr_rx_dsc: 0\n'
                    'zhcp11: bridge_fr_rx_err: 0\n'
                    'zhcp11: bridge_fr_tx:     0\n'
                    'zhcp11: bridge_fr_tx_dsc: 0\n'
                    'zhcp11: bridge_fr_tx_err: 0\n'
                    'zhcp11: bridge_rx:        0\n'
                    'zhcp11: bridge_tx:        0\n'
                    'zhcp11: nic count: 2\n'
                    'zhcp11: nic_id: INST1 0600\n'
                    'zhcp11: nic_fr_rx:        573952\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        548780\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    4\n'
                    'zhcp11: nic_rx:           103024058\n'
                    'zhcp11: nic_tx:           102030890\n'
                    'zhcp11: nic_id: INST2 0600\n'
                    'zhcp11: nic_fr_rx:        17493\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        16886\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    4\n'
                    'zhcp11: nic_rx:           3111714\n'
                    'zhcp11: nic_tx:           3172646\n'
                    'zhcp11: vlan count: 0',
                    'zhcp11: vswitch number: 2\n'
                    'zhcp11: vswitch name: XCATVSW2\n'
                    'zhcp11: uplink count: 1\n'
                    'zhcp11: uplink_conn: 6200\n'
                    'zhcp11: uplink_fr_rx:     1608681\n'
                    'zhcp11: uplink_fr_rx_dsc: 0\n'
                    'zhcp11: uplink_fr_rx_err: 0\n'
                    'zhcp11: uplink_fr_tx:     2120075\n'
                    'zhcp11: uplink_fr_tx_dsc: 0\n'
                    'zhcp11: uplink_fr_tx_err: 0\n'
                    'zhcp11: uplink_rx:        314326223',
                    'zhcp11: uplink_tx:        1503721533\n'
                    'zhcp11: bridge_fr_rx:     0\n'
                    'zhcp11: bridge_fr_rx_dsc: 0\n'
                    'zhcp11: bridge_fr_rx_err: 0\n'
                    'zhcp11: bridge_fr_tx:     0\n'
                    'zhcp11: bridge_fr_tx_dsc: 0\n'
                    'zhcp11: bridge_fr_tx_err: 0\n'
                    'zhcp11: bridge_rx:        0\n'
                    'zhcp11: bridge_tx:        0\n'
                    'zhcp11: nic count: 2\n'
                    'zhcp11: nic_id: INST1 1000\n'
                    'zhcp11: nic_fr_rx:        34958\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        16211\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    0\n'
                    'zhcp11: nic_rx:           4684435\n'
                    'zhcp11: nic_tx:           3316601\n'
                    'zhcp11: nic_id: INST2 1000\n'
                    'zhcp11: nic_fr_rx:        27211\n'
                    'zhcp11: nic_fr_rx_dsc:    0\n'
                    'zhcp11: nic_fr_rx_err:    0\n'
                    'zhcp11: nic_fr_tx:        12344\n'
                    'zhcp11: nic_fr_tx_dsc:    0\n'
                    'zhcp11: nic_fr_tx_err:    0\n'
                    'zhcp11: nic_rx:           3577163\n'
                    'zhcp11: nic_tx:           2515045\n'
                    'zhcp11: vlan count: 0',
                     None]
        xdsh.return_value = {'data': [vsw_data]}
        vsw_dict = self._zvmclient.virtual_network_vswitch_query_iuo_stats()
        self.assertEqual(2, len(vsw_dict['vswitches']))
        self.assertEqual(2, len(vsw_dict['vswitches'][1]['nics']))
        self.assertEqual('INST1',
                         vsw_dict['vswitches'][0]['nics'][0]['userid'])
        self.assertEqual('3577163',
                         vsw_dict['vswitches'][1]['nics'][1]['nic_rx'])

    @mock.patch('zvmsdk.client.XCATClient._get_hcp_info')
    @mock.patch.object(zvmutils, 'xdsh')
    def test_virtual_network_vswitch_query_iuo_stats_invalid_data(self, xdsh,
                                                                get_hcp_info):
        get_hcp_info.return_value = {'hostname': 'fakehcp.ibm.com',
                                     'nodename': 'fakehcp',
                                     'userid': 'FAKEHCP'}
        xdsh.return_value = ['invalid', 'data']
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                    self._zvmclient.virtual_network_vswitch_query_iuo_stats)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_add_switch_table_record')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_private_create_nic_active(self, xrequest, _add_switch, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}
        xrequest.return_value = {"errorcode": [['0']]}
        self._zvmclient._create_nic("fakenode", "fake_vdev", "fakehcp",
                                    nic_id="fake_nic",
                                    mac_addr='11:22:33:44:55:66',
                                    active=True)
        _add_switch.assert_called_once_with("fakenode", "fake_vdev",
                                            nic_id="fake_nic",
                                            zhcp="fakehcp")

        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Create_Extended_DM',
                             "-T fakenode",
                             "-k image_device_number=fake_vdev",
                             "-k adapter_type=QDIO",
                             "-k mac_id=445566"))
        xdsh_commands = 'command=%s' % commands
        body1 = [xdsh_commands]

        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Create_Extended',
                             "-T fakenode",
                             "-k image_device_number=fake_vdev",
                             "-k adapter_type=QDIO"))
        xdsh_commands = 'command=%s' % commands
        body2 = [xdsh_commands]
        xrequest.assert_any_call("PUT", url, body1)
        xrequest.assert_any_call("PUT", url, body2)

    def test_is_vdev_valid_true(self):
        vdev = '1009'
        vdev_info = ['1003', '1006']
        result = self._zvmclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, True)

    def test_is_vdev_valid_False(self):
        vdev = '2002'
        vdev_info = ['2000', '2004']
        result = self._zvmclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, False)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch_table_record(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "switch.node=fakenode" + " switch.interface=fake"
        commands += " switch.port=fake-port"
        commands += " switch.comments=fakezhcp"
        body = [commands]

        info = self._zvmclient._add_switch_table_record("fakenode", "fake",
                                                        "fake-port",
                                                        "fakezhcp")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch_table_record_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_switch_table_record,
                          "fakenode", "fake", "fake-port",
                          "fakezhcp")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_update_vm_info(self, xrequest):
        node = 'fakenode'
        node_info = ['sles12', 's390x', 'netboot',
                     '0a0c576a_157f_42c8_2a254d8b77f']
        url = "/xcatws/nodes/fakenode?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        self._zvmclient._update_vm_info(node, node_info)
        xrequest.assert_called_with('PUT', url,
                ['noderes.netboot=zvm',
                 'nodetype.os=sles12',
                 'nodetype.arch=s390x',
                 'nodetype.provmethod=netboot',
                 'nodetype.profile=0a0c576a_157f_42c8_2a254d8b77f'])

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmclient.XCATClient, '_update_vm_info')
    def test_guest_deploy(self, _update_vm_info, xrequest):
        node = "testnode"
        image_name = "sles12-s390x-netboot-0a0c576a_157f_42c8_2a254d8b77fc"
        transportfiles = '/tmp/transport.tgz'

        url = "/xcatws/nodes/testnode/bootstate?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        self._zvmclient.guest_deploy(node, image_name, transportfiles)
        _update_vm_info.assert_called_with('testnode',
            ['sles12', 's390x', 'netboot', '0a0c576a_157f_42c8_2a254d8b77fc'])

        xrequest.assert_called_with('PUT', url,
            ['netboot', 'device=0100',
             'osimage=sles12-s390x-netboot-0a0c576a_157f_42c8_2a254d8b77fc',
             'transport=/tmp/transport.tgz'])

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_private_power_state(self, xreq):
        expt = {'info': [[u'fakeid: on\n']]}
        expt_url = ('/xcatws/nodes/fakeid/power?userName=%(uid)s&password='
                    '%(pwd)s&format=json' % {'uid': CONF.xcat.username,
                                             'pwd': CONF.xcat.password})
        xreq.return_value = expt
        resp = self._zvmclient._power_state('fakeid', 'GET', 'state')
        xreq.assert_called_once_with('GET', expt_url, ['state'])
        self.assertEqual(resp, expt)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_private_power_state_invalid_node(self, xreq):
        xreq.side_effect = exception.ZVMXCATRequestFailed(xcatserver='xcat',
            msg='error: Invalid nodes and/or groups: fakenode')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
            self._zvmclient._power_state, 'fakeid', 'GET', ['state'])

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_lsdef(self, xrequest):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.lsdef_node('/' + fake_userid)
        self._zvmclient._lsdef(fake_userid)
        xrequest.assert_called_once_with('GET', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_lsvm(self, xrequest):
        fake_userid = 'fake_userid'
        fake_resp = {'info': [[fake_userid]],
                    'node': [],
                    'errocode': [],
                    'data': []}
        xrequest.return_value = fake_resp
        ret = self._zvmclient._lsvm(fake_userid)
        self.assertEqual(ret[0], fake_userid)

    def test_get_guest_connection_status(self):
        # TODO:moving to vmops and change name to ''
        pass

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_create_xcat_node(self, xrequest, ghi):
        fake_userid = 'userid'
        fake_url = self._xcat_url.mkdef('/' + fake_userid)
        fake_body = ['userid=%s' % fake_userid,
                'hcp=%s' % 'fakehcp',
                'mgt=zvm',
                'groups=%s' % const.ZVM_XCAT_GROUP]
        ghi.return_value = {'hostname': 'fakehcp'}

        self._zvmclient.create_xcat_node(fake_userid)
        xrequest.assert_called_once_with("POST", fake_url, fake_body)

    def test_prepare_for_spawn(self):
        pass

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_remove_image_file(self, xrequest):
        fake_image_name = 'fake_image_name'
        fake_url = self._xcat_url.rmimage('/' + fake_image_name)
        self._zvmclient.remove_image_file(fake_image_name)

        xrequest.assert_called_once_with('DELETE', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_remove_image_definition(self, xrequest):
        fake_image_name = 'fake_image_name'
        fake_url = self._xcat_url.rmobject('/' + fake_image_name)

        self._zvmclient.remove_image_definition(fake_image_name)
        xrequest.assert_called_once_with('DELETE', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_tabdum_info(self, xrequest):
        fake_url = self._xcat_url.tabdump('/zvm')

        self._zvmclient.get_tabdump_info()
        xrequest.assert_called_once_with('GET', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_do_capture(self, xrequest):
        fake_url = self._xcat_url.capture()
        fake_nodename = 'nodename'
        fake_profile = 'profiiiillle'
        fake_body = ['nodename=' + fake_nodename,
                     'profile=' + fake_profile]

        self._zvmclient.do_capture(fake_nodename, fake_profile)
        xrequest.assert_called_once_with('POST', fake_url, fake_body)

    def test_check_space_imgimport_xcat(self):
        pass

    def test_export_image(self):
        pass

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(os, 'remove')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(zvmclient.XCATClient, 'check_space_imgimport_xcat')
    @mock.patch.object(zvmclient.XCATClient, 'generate_image_bundle')
    @mock.patch.object(zvmclient.XCATClient, 'generate_manifest_file')
    def test_image_import(self, generate_manifest_file,
                                generate_image_bundle,
                                check_space,
                                file_exists,
                                remove_file,
                                xrequest):

        image_file_path = '/test/62599661-3D7A-40C1-8210-B6A4BC66DDB7'
        time_stamp_dir = self._pathutils.make_time_stamp()
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)
        os_version = 'rhel7.2'
        remote_host_info = 'nova@192.168.99.99'
        image_profile = '62599661_3D7A_40C1_8210_B6A4BC66DDB7'
        image_meta = {
                u'id': '62599661-3D7A-40C1-8210-B6A4BC66DDB7',
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': os_version,
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                               u'provision_method': u'netboot'}
                }
        generate_manifest_file.return_value = \
        '/tmp/image/spawn_tmp/201706231109/manifest.xml'
        generate_image_bundle.return_value =\
                                '/tmp/image/spawn_tmp/201706231109.tar'
        check_space.return_value = None
        file_exists.return_value = True
        fake_url = self._xcat_url.imgimport()
        fake_body = ['osimage=/tmp/image/spawn_tmp/201706231109.tar',
                     'profile=%s' % image_profile,
                     'nozip',
                     'remotehost=%s' % remote_host_info]

        remove_file.return_value = None
        self._zvmclient.image_import(image_file_path, os_version,
                          remote_host=remote_host_info)
        generate_manifest_file.assert_called_with(image_meta,
            '0100.img', bundle_file_path)

        xrequest.assert_called_once_with('POST', fake_url, fake_body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_vm_nic_vswitch_info(self, xrequest):
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        self._zvmclient.get_vm_nic_vswitch_info("fakenode")
        xrequest.assert_called_with('GET', url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_host_table_record(self, xrequest):
        commands = "node=fakeid" + " hosts.ip=fakeip"
        commands += " hosts.hostnames=fakehost"
        body = [commands]
        url = "/xcatws/tables/hosts?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"

        self._zvmclient._add_host_table_record("fakeid", "fakeip", "fakehost")
        xrequest.assert_called_once_with("PUT", url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_host_table_record_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_host_table_record,
                          "fakeid", "fakeip", "fakehost")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_makehost(self, xrequest):
        url = "/xcatws/networks/makehosts?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"

        self._zvmclient._makehost()
        xrequest.assert_called_once_with("PUT", url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_makehost_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._makehost)

    @mock.patch.object(zvmclient.XCATClient, '_makehost')
    @mock.patch.object(zvmclient.XCATClient, '_add_host_table_record')
    def test_preset_vm_network(self, add_host, makehost):
        self._zvmclient._preset_vm_network("fakeid", "fakeip")
        add_host.assert_called_with("fakeid", "fakeip", "fakeid")
        makehost.assert_called_with()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_nic_ids(self, xrequest):
        xrequest.return_value = {"data": [["test1", "test2"]]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        info = self._zvmclient._get_nic_ids()
        xrequest.assert_called_with('GET', url)
        self.assertEqual(info[0], "test2")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_userid_from_node(self, xrequest):
        xrequest.return_value = {"data": ["fake"]}
        url = "/xcatws/tables/zvm?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json" +\
               "&col=node&value=fakenode&attribute=userid"
        info = self._zvmclient._get_userid_from_node("fakenode")
        xrequest.assert_called_with('GET', url)
        self.assertEqual(info, xrequest.return_value['data'][0][0])

    @mock.patch.object(zvmclient.XCATClient, '_get_userid_from_node')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_nic_settings(self, xrequest, get_userid_from_node):
        xrequest.return_value = {"data": [["fake"]]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json" +\
               "&col=port&value=fakeport&attribute=node"
        self._zvmclient._get_nic_settings("fakeport")
        xrequest.assert_called_once_with('GET', url)
        get_userid_from_node.assert_called_once_with("fake")

    @mock.patch.object(zvmclient.XCATClient, '_get_nic_settings')
    def test_get_node_from_port(self, get_nic_settings):
        self._zvmclient._get_node_from_port("fakeport")
        get_nic_settings.assert_called_with("fakeport", get_node=True)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_grant_user_to_vswitch(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'zhcpuserid'}
        xrequest.return_value = {"errorcode": [['0']]}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended'
        commands += " -T zhcpuserid"
        commands += " -k switch_name=fakevs"
        commands += " -k grant_userid=fakeuserid"
        commands += " -k persist=YES"
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        self._zvmclient.grant_user_to_vswitch("fakevs", "fakeuserid")
        xrequest.assert_called_once_with("PUT", url, body)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_revoke_user_from_vswitch(self, xrequest, get_hcp):
        xrequest.return_value = {"errorcode": [['0']]}
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'zhcpuserid'}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended'
        commands += " -T zhcpuserid"
        commands += " -k switch_name=fakevs"
        commands += " -k revoke_userid=fakeuserid"
        commands += " -k persist=YES"
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        self._zvmclient.revoke_user_from_vswitch("fakevs", "fakeuserid")
        xrequest.assert_called_once_with("PUT", url, body)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_update_xcat_switch')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_couple_nic(self, xrequest, update_switch, get_hcp):
        xrequest.return_value = {"errorcode": [['0']]}
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'zhcpuserid'}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        commands = '/opt/zhcp/bin/smcli'
        commands += ' Virtual_Network_Adapter_Connect_Vswitch_DM'
        commands += " -T fakeuserid " + "-v fakevdev"
        commands += " -n fakevs"
        xdsh_commands = 'command=%s' % commands
        body1 = [xdsh_commands]

        commands = '/opt/zhcp/bin/smcli'
        commands += ' Virtual_Network_Adapter_Connect_Vswitch'
        commands += " -T fakeuserid " + "-v fakevdev"
        commands += " -n fakevs"
        xdsh_commands = 'command=%s' % commands
        body2 = [xdsh_commands]

        self._zvmclient._couple_nic("fakeuserid", "fakevdev", "fakevs",
                                    active=True)
        update_switch.assert_called_with("fakeuserid", "fakevdev",
                                         "fakevs")
        xrequest.assert_any_call("PUT", url, body1)
        xrequest.assert_any_call("PUT", url, body2)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_update_xcat_switch')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_uncouple_nic(self, xrequest, update_switch, get_hcp):
        xrequest.return_value = {"errorcode": [['0']]}
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'zhcpuserid'}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        commands = '/opt/zhcp/bin/smcli'
        commands += ' Virtual_Network_Adapter_Disconnect_DM'
        commands += " -T fakeuserid " + "-v fakevdev"
        xdsh_commands = 'command=%s' % commands
        body1 = [xdsh_commands]

        commands = '/opt/zhcp/bin/smcli'
        commands += ' Virtual_Network_Adapter_Disconnect'
        commands += " -T fakeuserid " + "-v fakevdev"
        xdsh_commands = 'command=%s' % commands
        body2 = [xdsh_commands]

        self._zvmclient._uncouple_nic("fakeuserid",
                                      "fakevdev", active=True)
        update_switch.assert_called_with("fakeuserid", "fakevdev", None)
        xrequest.assert_any_call("PUT", url, body1)
        xrequest.assert_any_call("PUT", url, body2)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_xcat_node_ip(self, xrequest):
        xrequest.return_value = {"data": [["fakeip"]]}
        url = "/xcatws/tables/site?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json" +\
               "&col=key&value=master&attribute=value"

        info = self._zvmclient._get_xcat_node_ip()
        xrequest.assert_called_with("GET", url)
        self.assertEqual(info, "fakeip")

    @mock.patch.object(zvmclient.XCATClient, '_get_xcat_node_ip')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_xcat_node_name(self, xrequest, get_ip):
        get_ip.return_value = "fakeip"
        xrequest.return_value = {"data": [["fakename"]]}
        url = "/xcatws/tables/hosts?userName=" +\
              CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json" +\
              "&col=ip&value=fakeip&attribute=node"

        info = self._zvmclient._get_xcat_node_name()
        get_ip.assert_called_with()
        xrequest.assert_called_with("GET", url)
        self.assertEqual(info, "fakename")

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_vswitch_list(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'fakenode'}
        xrequest.return_value = {
            "data": [[u"VSWITCH:  Name: TEST", u"VSWITCH:  Name: TEST2"]],
            "errorcode": [['0']]
                            }
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query',
            "-T fakenode",
            "-s \'*\'"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        info = self._zvmclient.get_vswitch_list()
        get_hcp.assert_called_with()
        xrequest.assert_called_with("PUT", url, body)
        self.assertEqual(info[0], "TEST")
        self.assertEqual(info[1], "TEST2")

    @mock.patch.object(zvmclient.XCATClient, '_couple_nic')
    def test_couple_nic_to_vswitch(self, couple_nic):
        self._zvmclient.couple_nic_to_vswitch("fake_userid",
                                              "fakevdev",
                                              "fake_VS_name",
                                              True)
        couple_nic.assert_called_with("fake_userid",
                                      "fakevdev",
                                      "fake_VS_name",
                                      active=True)

    @mock.patch.object(zvmclient.XCATClient, '_uncouple_nic')
    def test_uncouple_nic_from_vswitch(self, uncouple_nic):
        self._zvmclient.uncouple_nic_from_vswitch("fake_userid",
                                                  "fakevdev",
                                                  False)
        uncouple_nic.assert_called_with("fake_userid",
                                        "fakevdev", active=False)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_vswitch(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'fakeuserid'}
        xrequest.return_value = {
            "data": [["0"]],
            "errorcode": [['0']]
                            }
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = '/opt/zhcp/bin/smcli ' +\
                   'Virtual_Network_Vswitch_Create_Extended'
        commands += " -T fakeuserid"
        commands += ' -k switch_name=fakename'
        commands += " -k real_device_address='111 222'"
        commands = ' '.join((commands,
                             "-k connection_value=CONNECT",
                             "-k queue_memory_limit=5",
                             "-k transport_type=ETHERNET",
                             "-k vlan_id=10",
                             "-k persist=NO",
                             "-k port_type=ACCESS",
                             "-k gvrp_value=GVRP",
                             "-k native_vlanid=None",
                             "-k routing_value=NONROUTER"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        self._zvmclient.add_vswitch("fakename", rdev="111 222",
                                    controller='*', connection='CONNECT',
                                    network_type='ETHERNET',
                                    router="NONROUTER", vid='10',
                                    port_type='ACCESS', gvrp='GVRP',
                                    queue_mem=5, native_vid=None,
                                    persist=False)
        xrequest.assert_called_with("PUT", url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_image_query_with_keyword(self, xrequest):
        xrequest.return_value = {'info':
            [[u'sles12-s390x-netboot-0a0c576a_157f_42c8_bde5  (osimage)']],
            'node': [],
            'errorcode': [],
            'data': [],
            'error': []}

        imagekeyword = '0a0c576a-157f-42c8-bde5'
        url = "/xcatws/images?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json&criteria=profile=~" + imagekeyword.replace('-',
                                                                       '_')
        image_list = [u'sles12-s390x-netboot-0a0c576a_157f_42c8_bde5']
        ret = self._zvmclient.image_query(imagekeyword)
        xrequest.assert_called_once_with("GET", url)
        self.assertEqual(ret, image_list)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_image_query_without_keyword(self, xrequest):
        xrequest.return_value = {'info':
            [[u'rhel7.2-s390x-netboot-eae09a9f_7958_4024_a58c  (osimage)',
              u'sles12-s390x-netboot-0a0c576a_157f_42c8_bde5  (osimage)']],
            'node': [],
            'errorcode': [],
            'data': [],
            'error': []}
        image_list = [u'rhel7.2-s390x-netboot-eae09a9f_7958_4024_a58c',
                      u'sles12-s390x-netboot-0a0c576a_157f_42c8_bde5']
        url = "/xcatws/images?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        ret = self._zvmclient.image_query()
        xrequest.assert_called_once_with("GET", url)
        self.assertEqual(ret, image_list)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_user_console_output(self, xreq):
        log_str = 'fakeid: this is console log for fakeid\n'
        xreq.return_value = {'info': [[log_str]]}
        clog = self._zvmclient.get_user_console_output('fakeid', 100)
        self.assertEqual(clog, 'this is console log for fakeid\n')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_user_console_output_invalid_output(self, xreq):
        xreq.return_value = {}
        self.assertRaises(exception.ZVMInvalidXCATResponseDataError,
                        self._zvmclient.get_user_console_output, 'fakeid', 100)

    def test_generate_vdev(self):
        base = '0100'
        idx = 1
        vdev = self._zvmclient._generate_vdev(base, idx)
        self.assertEqual(vdev, '0101')

    @mock.patch.object(zvmclient.XCATClient, 'aemod_handler')
    def test_process_additional_minidisks(self, aemod_handler):
        userid = 'inst001'
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        vdev = '0101'
        fmt = 'ext3'
        mntdir = '/mnt/0101'
        func_name = 'setupDisk'
        parms = ' '.join([
                          'action=addMdisk',
                          'vaddr=' + vdev,
                          'filesys=' + fmt,
                          'mntdir=' + mntdir
                        ])
        parmline = ''.join(parms)
        self._zvmclient.process_additional_minidisks(userid, disk_list)
        aemod_handler.assert_called_with(userid, func_name, parmline)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xdsh')
    def test_unlock_userid(self, xdsh, get_hcp):
        userid = 'fakeuser'
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}
        cmd = "/opt/zhcp/bin/smcli Image_Unlock_DM -T %s" % userid
        self._zvmclient.unlock_userid(userid)
        xdsh.assert_called_once_with('zhcp2', cmd)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xdsh')
    def test_unlock_device(self, xdsh, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}
        userid = 'fakeuser'
        resp = {'data': [['Locked type: DEVICE\nDevice address: 0100\n'
                'Device locked by: fake\nDevice address: 0101\n'
                'Device locked by: fake']]}
        xdsh.side_effect = [resp, None, None]
        self._zvmclient.unlock_devices(userid)

        xdsh.assert_any_call('zhcp2',
            '/opt/zhcp/bin/smcli Image_Lock_Query_DM -T fakeuser')
        xdsh.assert_any_call('zhcp2',
            '/opt/zhcp/bin/smcli Image_Unlock_DM -T fakeuser -v 0100')
        xdsh.assert_any_call('zhcp2',
            '/opt/zhcp/bin/smcli Image_Unlock_DM -T fakeuser -v 0101')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_xcat_node(self, xrequest):
        fake_userid = 'fakeuser'
        fake_url = self._xcat_url.rmdef('/' + fake_userid)

        self._zvmclient.delete_xcat_node(fake_userid)
        xrequest.assert_called_once_with('DELETE', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmclient.XCATClient, 'delete_xcat_node')
    def test_delete_userid_not_exist(self, delete_xcat_node, xrequest):
        fake_userid = 'fakeuser'
        fake_url = self._xcat_url.rmvm('/' + fake_userid)
        xrequest.side_effect = exception.ZVMXCATInternalError(
            'Return Code: 400\nReason Code: 4\n')

        self._zvmclient.delete_userid(fake_userid)
        xrequest.assert_called_once_with('DELETE', fake_url)
        delete_xcat_node.assert_called_once_with(fake_userid)

    @mock.patch.object(zvmclient.XCATClient, '_clean_network_resource')
    @mock.patch.object(zvmclient.XCATClient, 'delete_userid')
    def test_delete_vm(self, delete_userid, clean_net):
        fake_userid = 'fakeuser'
        self._zvmclient.delete_vm(fake_userid)
        delete_userid.assert_called_once_with(fake_userid)
        clean_net.assert_called_once_with(fake_userid)

    @mock.patch.object(zvmclient.XCATClient, '_clean_network_resource')
    @mock.patch.object(zvmclient.XCATClient, 'unlock_devices')
    @mock.patch.object(zvmclient.XCATClient, 'delete_userid')
    def test_delete_vm_with_locked_device(self, delete_userid, unlock_devices,
                                          clean_net):
        fake_userid = 'fakeuser'
        delete_userid.side_effect = [exception.ZVMXCATInternalError(
        'Return Code: 408\n Reason Code: 12\n'), None]

        self._zvmclient.delete_vm(fake_userid)
        delete_userid.assert_called_with(fake_userid)
        unlock_devices.assert_called_with(fake_userid)

    @mock.patch.object(zvmclient.XCATClient, '_clean_network_resource')
    @mock.patch.object(zvmclient.XCATClient, 'delete_userid')
    def test_delete_vm_node_not_exist(self, delete_userid, clean_net):
        fake_userid = 'fakeuser'
        delete_userid.side_effect = exception.ZVMXCATRequestFailed('msg')

        self.assertRaises(exception.ZVMXCATRequestFailed,
                          self._zvmclient.delete_vm, fake_userid)

    @mock.patch.object(xml.dom.minidom, 'Document')
    @mock.patch.object(xml.dom.minidom.Document, 'createElement')
    def test_generate_manifest_file(self, create_element, document):
        """
        image_meta = {
                u'id': 'image_uuid_123',
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': u'rhel7.2',
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                             u'provision_metuot'}
                }
        image_name = 'image_name_123'
        tmp_date_dir = 'tmp_date_dir'
        disk_file_name = 'asdf'
        manifest_path = os.getcwd()
        manifest_path = manifest_path + '/' + tmp_date_dir
        """
        pass

    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(tarfile, 'open')
    @mock.patch.object(tarfile.TarFile, 'add')
    @mock.patch.object(tarfile.TarFile, 'close')
    @mock.patch.object(shutil, 'copyfile')
    @mock.patch.object(os, 'chdir')
    def test_generate_image_bundle(self, change_dir,
                                   copy_file, close_file,
                                   add_file, tarfile_open,
                                   file_exist):
        time_stamp_dir = 'tmp_date_dir'
        image_name = 'test'
        spawn_path = '.'
        spawn_path = spawn_path + '/' + time_stamp_dir
        image_file_path = spawn_path + '/images/test.img'
        change_dir.return_value = None
        copy_file.return_value = None
        close_file.return_value = None
        add_file.return_value = None
        tarfile_open.return_value = tarfile.TarFile
        file_exist.return_value = True

        self._zvmclient.generate_image_bundle(
                                    spawn_path, time_stamp_dir,
                                    image_name, image_file_path)
        tarfile_open.assert_called_once_with(spawn_path +
                                             '/tmp_date_dir_test.tar',
                                             mode='w')

    @mock.patch.object(zvmclient.XCATClient, 'add_mdisks')
    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmclient.XCATClient, 'prepare_for_spawn')
    def test_create_vm(self, prepare_for_spawn, xrequest, add_mdisks):
        user_id = 'fakeuser'
        cpu = 2
        memory = 1024
        disk_list = [{'size': '1g',
                      'is_boot_disk': True,
                      'disk_pool': 'ECKD:eckdpool1'}]
        profile = 'dfltprof'
        url = "/xcatws/vms/fakeuser?userName=" + CONF.xcat.username +\
            "&password=" + CONF.xcat.password +\
            "&format=json"
        body = ['profile=dfltprof',
                'password=%s' % CONF.zvm.user_default_password, 'cpu=2',
                'memory=1024m', 'privilege=G', 'ipl=0100']
        self._zvmclient.create_vm(user_id, cpu, memory, disk_list, profile)
        prepare_for_spawn.assert_called_once_with(user_id)
        xrequest.assert_called_once_with('POST', url, body)
        add_mdisks.assert_called_once_with(user_id, disk_list)

    @mock.patch.object(zvmclient.XCATClient, '_add_mdisk')
    def test_add_mdisks(self, add_mdisk):
        userid = 'fakeuser'
        disk_list = [{'size': '1g',
                      'is_boot_disk': True,
                      'disk_pool': 'ECKD:eckdpool1'},
                     {'size': '200000',
                      'disk_pool': 'FBA:fbapool1',
                      'format': 'ext3'}]
        self._zvmclient.add_mdisks(userid, disk_list)
        add_mdisk.assert_any_call(userid, disk_list[0], '0100')
        add_mdisk.assert_any_call(userid, disk_list[1], '0101')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mdisk(self, xrequest):
        userid = 'fakeuser'
        disk = {'size': '1g',
                'disk_pool': 'ECKD:eckdpool1',
                'format': 'ext3'}
        vdev = '0101'
        url = "/xcatws/vms/fakeuser?" + \
            "userName=" + CONF.xcat.username +\
            "&password=" + CONF.xcat.password + "&format=json"
        body = [" ".join(['--add3390', 'eckdpool1', vdev, '1g', "MR", "''",
                "''", "''", 'ext3'])]

        self._zvmclient._add_mdisk(userid, disk, vdev),
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_vswitch_port_vlan_id(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'zhcpuserid'}
        xrequest.return_value = {"errorcode": [['0']]}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended'
        commands += " -T zhcpuserid"
        commands += ' -k grant_userid=userid'
        commands += " -k switch_name=vswitch_name"
        commands += " -k user_vlan_id=vlan_id"
        commands += " -k persist=YES"
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        self._zvmclient.set_vswitch_port_vlan_id("vswitch_name",
                                                 "userid",
                                                 "vlan_id")
        xrequest.assert_called_once_with("PUT", url, body)

    @mock.patch.object(zvmclient.XCATClient, 'remove_image_file')
    @mock.patch.object(zvmclient.XCATClient, 'remove_image_definition')
    def test_image_delete(self, remove_image_def, remove_image_file):
        image_name = 'image-unique-name'
        self._zvmclient.image_delete(image_name)
        remove_image_file.assert_called_once_with(image_name)
        remove_image_def.assert_called_once_with(image_name)

    def test_get_image_path_by_name(self):
        fake_name = 'rhel7.2-s390x-netboot-fake_image_uuid'
        expected_path = '/install/netboot/rhel7.2/s390x/fake_image_uuid/' +\
                CONF.zvm.user_root_vdev + '.img'
        ret = self._zvmclient.get_image_path_by_name(fake_name)
        self.assertEqual(ret, expected_path)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    def test_set_vswitch_with_invalid_key(self, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}
        self.assertRaises(exception.ZVMInvalidInput,
                          self._zvmclient.set_vswitch,
                          "vswitch_name", unknown='fake_id')

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_vswitch(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'fakenode'}
        xrequest.return_value = {"errorcode": [['0']]}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T fakenode",
            "-k switch_name=fake_vs",
            "-k real_device_address='1000 1003'"))

        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        self._zvmclient.set_vswitch("fake_vs",
                                    real_device_address='1000 1003')
        xrequest.assert_called_with("PUT", url, body)

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_vswitch_with_errorcode(self, xrequest, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'fakenode'}
        xrequest.return_value = {"data": "Returned data",
                                 "errorcode": [['1']]}

        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient.set_vswitch,
                          "vswitch_name", grant_userid='fake_id')

    @mock.patch.object(zvmclient.XCATClient, '_get_nic_ids')
    @mock.patch.object(zvmclient.XCATClient, '_preset_vm_network')
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_create_nic')
    def test_create_nic(self, create_nic, get_hcp, preset_vm, get_nic):
        get_nic.return_value = ['"fake_id",,,,"1003",,',
                                '"fake_id",,,,"1006",,']
        get_hcp.return_value = {'nodename': 'zhcp2'}
        self._zvmclient.create_nic('fake_id', vdev='1009', nic_id='nic_id',
                                   ip_addr='fake_ip')
        preset_vm.assert_called_with('fake_id', 'fake_ip')
        create_nic.assert_called_with('fake_id',
                                      '1009', 'zhcp2', nic_id="nic_id",
                                      mac_addr=None, active=False)

    @mock.patch.object(zvmclient.XCATClient, '_get_nic_ids')
    @mock.patch.object(zvmclient.XCATClient, '_preset_vm_network')
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_create_nic')
    def test_create_nic_without_vdev(self, create_nic, get_hcp, preset_vm,
                                     get_nic):
        get_nic.return_value = ['"fake_id",,,,"1003",,',
                                '"fake_id",,,,"2003",,']
        get_hcp.return_value = {'nodename': 'zhcp2'}
        self._zvmclient.create_nic('fake_id', nic_id='nic_id',
                                   ip_addr='fake_ip')
        preset_vm.assert_called_with('fake_id', 'fake_ip')
        create_nic.assert_called_with('fake_id', '2006', 'zhcp2',
                                      nic_id='nic_id',
                                      mac_addr=None, active=False)

    @mock.patch.object(zvmclient.XCATClient, '_get_nic_ids')
    def test_create_nic_with_used_vdev(self, get_nic):
        get_nic.return_value = ['"fake_id",,,,"1003",,',
                                '"fake_id",,,,"1006",,']
        self.assertRaises(exception.ZVMInvalidInput,
                          self._zvmclient.create_nic,
                          'fake_id', nic_id="nic_id", vdev='1004')

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_vswitch_with_errorcode(self, xrequest, get_hcp):
        xrequest.return_value = {"data": [["Returned data"]],
                                 "errorcode": [['1']]}
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}

        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient.delete_vswitch,
                          "vswitch_name", 2)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_private_update_xcat_switch(self, xrequest):
        commands = "node=fake_id"
        commands += ",interface=fake_vdev"
        commands += " switch.switch=fake_vs"
        url = self._xcat_url.tabch("/switch")
        body = [commands]
        self._zvmclient._update_xcat_switch("fake_id", "fake_vdev", "fake_vs")
        xrequest.assert_called_with("PUT", url, body)

    @mock.patch.object(zvmutils, 'xdsh')
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    def test_query_vswitch(self, get_hcp_info, xdsh):
        get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                     'nodename': "fakehcp",
                                     'userid': "fakeuserid"}
        xdsh.return_value = {'info': [], 'node': [], 'errorcode': [[u'0']],
                             'data': [[
                               'zhcp2:  switch_name: UNITTEST\n'
                               'zhcp2:  transport_type: IP\n'
                               'zhcp2:  port_type: ACCESS\n'
                               'zhcp2:  queue_memory_limit: 8\n'
                               'zhcp2:  routing_value: NONROUTER\n'
                               'zhcp2:  vlan_awareness: AWARE\n'
                               'zhcp2:  vlan_id: 0011\n'
                               'zhcp2:  native_vlan_id: 0001\n'
                               'zhcp2:  mac_address: 02-00-02-00-02-23\n'
                               'zhcp2:  gvrp_request_attribute: NOGVRP\n'
                               'zhcp2:  gvrp_enabled_attribute: NOGVRP\n'
                               'zhcp2:  switch_status: 1\n'
                               'zhcp2:  link_ag: LAG:\n'
                               'zhcp2:  lag_interval: 0\n'
                               'zhcp2:  lag_group: (NOGRP)\n'
                               'zhcp2:  IP_timeout: 5\n'
                               'zhcp2:  switch_type: QDIO\n'
                               'zhcp2:  isolation_status: NOISOLATION\n'
                               'zhcp2:  MAC_protect: NOMACPROTECT\n'
                               'zhcp2:  user_port_based: USERBASED\n'
                               'zhcp2:  VLAN_counters: E)\n'
                               'zhcp2:  vepa_status: (NONE)\n'
                               'zhcp2: real_device_address: 1111\n'
                               'zhcp2: virtual_device_address: 0000\n'
                               'zhcp2: controller_name: (NONE)\n'
                               'zhcp2: port_name: (NONE)\n'
                               'zhcp2: device_status: 0\n'
                               'zhcp2: device_error_status 3\n'
                               'zhcp2: real_device_address: 0022\n'
                               'zhcp2: virtual_device_address: 0000\n'
                               'zhcp2: controller_name: (NONE)\n'
                               'zhcp2: port_name: (NONE)\n'
                               'zhcp2: device_status: 0\n'
                               'zhcp2: device_error_status 5\n'
                               'zhcp2: real_device_address: 0033\n'
                               'zhcp2: virtual_device_address: 0000\n'
                               'zhcp2: controller_name: (NONE)\n'
                               'zhcp2: port_name: (NONE)\n'
                               'zhcp2: device_status: 0\n'
                               'zhcp2: device_error_status 11\n'
                               'zhcp2: Error controller_name is NULL!!\n'
                               'zhcp2: port_num: 0000\n'
                               'zhcp2: grant_userid: TEST1\n'
                               'zhcp2: promiscuous_mode: NOPROM\n'
                               'zhcp2: osd_sim: NOOSDSIM\n'
                               'zhcp2: vlan_count: 1\n'
                               'zhcp2: user_vlan_id: 0001\n'
                               'zhcp2: port_num: 0000\n'
                               'zhcp2: grant_userid: TEST2\n'
                               'zhcp2: promiscuous_mode: NOPROM\n'
                               'zhcp2: osd_sim: NOOSDSIM\n'
                               'zhcp2: vlan_count: 1\n'
                               'zhcp2: user_vlan_id: 0001\n'
                               'zhcp2: port_num: 0000\n'
                               'zhcp2: grant_userid: TEST3\n'
                               'zhcp2: promiscuous_mode: NOPROM\n'
                               'zhcp2: osd_sim: NOOSDSIM\n'
                               'zhcp2: vlan_count: 3\n'
                               'zhcp2: user_vlan_id: 0001\n'
                               'zhcp2: user_vlan_id: 0002\n'
                               'zhcp2: user_vlan_id: 0003\n'
                               'zhcp2: adapter_owner: USERID1\n'
                               'zhcp2: adapter_vdev: 0800\n'
                               'zhcp2: adapter_macaddr: 02-00-02-00-00-D3\n'
                               'zhcp2: adapter_type: QDIO\n'
                               'zhcp2: adapter_owner: USERID2\n'
                               'zhcp2: adapter_vdev: 0700\n'
                               'zhcp2: adapter_macaddr: 02-00-02-00-00-70\n'
                               'zhcp2: adapter_type: QDIO']],
                             'error': []}
        vsw = self._zvmclient.query_vswitch('UNITTEST')
        self.assertEqual(vsw['switch_name'], 'UNITTEST')
        self.assertEqual(vsw['transport_type'], 'IP')
        self.assertEqual(vsw['port_type'], 'ACCESS')
        self.assertEqual(vsw['queue_memory_limit'], '8')
        self.assertEqual(vsw['vlan_awareness'], 'AWARE')
        self.assertEqual(vsw['vlan_id'], '0011')
        self.assertEqual(vsw['native_vlan_id'], '0001')
        self.assertEqual(vsw['gvrp_request_attribute'], 'NOGVRP')
        self.assertEqual(vsw['user_port_based'], 'USERBASED')
        self.assertListEqual(sorted(['TEST1', 'TEST2', 'TEST3']),
                             sorted(vsw['authorized_users'].keys()))
        self.assertEqual(vsw['authorized_users']['TEST3']['vlan_count'], '3')
        self.assertListEqual(
            sorted(vsw['authorized_users']['TEST3']['vlan_ids']),
            sorted(['0001', '0002', '0003']))
        self.assertListEqual(sorted(['USERID1_0800', 'USERID2_0700']),
                             sorted(vsw['adapters'].keys()))
        self.assertEqual(vsw['adapters']['USERID1_0800']['mac'],
                         '02-00-02-00-00-D3')
        self.assertEqual(vsw['adapters']['USERID1_0800']['type'],
                         'QDIO')

    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    @mock.patch.object(zvmclient.XCATClient, '_delete_nic_from_switch')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_nic(self, xrequest, delete_nic, get_hcp):
        get_hcp.return_value = {'nodename': 'zhcp2', 'userid': 'cmabvt'}
        xrequest.return_value = {"errorcode": [['0']]}
        url = "/xcatws/nodes/zhcp2" +\
              "/dsh?userName=" + CONF.xcat.username +\
              "&password=" + CONF.xcat.password +\
              "&format=json"
        commands = ' '.join((
            '/opt/zhcp/bin/smcli '
            'Virtual_Network_Adapter_Delete_DM -T fake_id',
            '-v fake_vdev'))
        xdsh_commands = 'command=%s' % commands
        body1 = [xdsh_commands]

        commands = ' '.join((
            '/opt/zhcp/bin/smcli '
            'Virtual_Network_Adapter_Delete -T fake_id',
            '-v fake_vdev'))
        xdsh_commands = 'command=%s' % commands
        body2 = [xdsh_commands]

        self._zvmclient.delete_nic("fake_id", "fake_vdev", True)
        xrequest.assert_any_call("PUT", url, body1)
        xrequest.assert_any_call("PUT", url, body2)
        delete_nic.assert_called_with("fake_id", "fake_vdev")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_nic_from_switch(self, xrequest):
        commands = "-d node=fake_id,interface=fake_vdev switch"
        url = self._xcat_url.tabch("/switch")
        body = [commands]
        self._zvmclient._delete_nic_from_switch("fake_id", "fake_vdev")
        xrequest.assert_called_with("PUT", url, body)

    @mock.patch.object(zvmutils, 'xdsh')
    def test_image_get_root_disk_size(self, execute_cmd):
        fake_name = 'rhel7.2-s390x-netboot-fake_image_uuid'
        hexdumps = [
            '00000000  78 43 41 54 20 43 4b 44  20 44 69 73 6b 20 49 6d  '
            '|xCAT CKD Disk Im|\n',
            '00000010  61 67 65 3a 20 20 20 20  20 20 20 20 33 33 33 38  '
            '|age:        3338|\n',
            '00000020  20 43 59 4c 20 48 4c 65  6e 3a 20 30 30 35 35 20  '
            '| CYL HLen: 0055 |\n',
            '00000030  47 5a 49 50 3a 20 36 20  20 20 20 20 20 20 20 20  '
            '|GZIP: 6         |\n',
            '00000040',
        ]
        prefix = CONF.xcat.master_node + ': '
        output = prefix + prefix.join(hexdumps)
        execute_cmd.return_value = {'data': [[output]]}
        ret = self._zvmclient.image_get_root_disk_size(fake_name)
        self.assertEqual(ret, '3338')
