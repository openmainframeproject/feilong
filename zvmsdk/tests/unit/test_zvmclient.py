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


from zvmsdk import client as zvmclient
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk.config import CONF
from zvmsdk.tests.unit import base


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()
        self._xcat_url = zvmutils.get_xcat_url()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self._zvmclient, zvmclient.XCATClient))


class SDKXCATCientTestCases(SDKZVMClientTestCase):
    """Test cases for xcat zvm client."""

    def setUp(self):
        super(SDKXCATCientTestCases, self).setUp()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_power_state(self, xrequest):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.rpower('/' + fake_userid)
        fake_body = ['on']
        self._zvmclient._power_state(fake_userid, 'PUT', 'on')
        xrequest.assert_called_once_with('PUT', fake_url, fake_body)

    @mock.patch.object(zvmclient.XCATClient, '_power_state')
    def test_power_on(self, power_state):
        fake_userid = 'fake_userid'
        self._zvmclient.power_on(fake_userid)
        power_state.assert_called_once_with(fake_userid, 'PUT', 'on')

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

    @mock.patch('zvmsdk.client.XCATClient._image_performance_query')
    def test_get_image_performance_info_not_exist(self, ipq):
        ipq.return_value = {}
        info = self._zvmclient.get_image_performance_info('fakevm')
        self.assertEqual(info, None)

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

    @mock.patch.object(zvmclient.XCATClient, '_add_switch_table_record')
    @mock.patch.object(zvmclient.XCATClient, '_add_mac_table_record')
    @mock.patch.object(zvmclient.XCATClient, '_delete_mac')
    @mock.patch.object(zvmclient.XCATClient, '_get_hcp_info')
    def test_create_port(self, _get_hcp_info, _delete_mac,
                         _add_mac, _add_switch):
        _get_hcp_info.return_value = {'hostname': "fakehcp.fake.com",
                                      'nodename': "fakehcp",
                                      'userid': "fakeuserid"}
        self._zvmclient.create_port("fakenode", "fake_nic",
                                    "fake_mac", "fake_vdev")
        _get_hcp_info.assert_called_once_with()
        zhcpnode = _get_hcp_info.return_value['nodename']
        _delete_mac.assert_called_once_with("fakenode")
        _add_mac.assert_called_once_with("fakenode", "fake_vdev",
                                         "fake_mac", zhcpnode)
        _add_switch.assert_called_once_with("fakenode", "fake_nic",
                                            "fake_vdev", zhcpnode)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mac_table_record(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/mac?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "mac.node=fakenode" + " mac.mac=00:00:00:00:00:00"
        commands += " mac.interface=fake"
        commands += " mac.comments=fakezhcp"
        body = [commands]

        info = self._zvmclient._add_mac_table_record("fakenode", "fake",
                                                     "00:00:00:00:00:00",
                                                     "fakezhcp")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mac_table_record_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_mac_table_record,
                          "fakenode", "fake",
                          "00:00:00:00:00:00", "fakezhcp")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch_table_record(self, xrequest):
        xrequest.return_value = {"data": ["fakereturn"]}
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "switch.node=fakenode" + " switch.port=fake-port"
        commands += " switch.interface=fake"
        commands += " switch.comments=fakezhcp"
        body = [commands]

        info = self._zvmclient._add_switch_table_record("fakenode",
                                                        "fake-port",
                                                        "fake",
                                                        "fakezhcp")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info[0], "fakereturn")

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_switch_table_record_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self._zvmclient._add_switch_table_record,
                          "fakenode", "fake-port",
                          "fake", "fakezhcp")

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
    def test_deploy_image_to_vm(self, _update_vm_info, xrequest):
        node = "testnode"
        image_name = "sles12-s390x-netboot-0a0c576a_157f_42c8_2a254d8b77fc"
        transportfiles = '/tmp/transport.tgz'

        url = "/xcatws/nodes/testnode/bootstate?userName=" +\
                CONF.xcat.username +\
               "&password=" + CONF.xcat.password +\
               "&format=json"
        self._zvmclient.deploy_image_to_vm(node, image_name, transportfiles)
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

    def test_get_node_status(self):
        # TODO:moving to vmops and change name to ''
        pass

    def test_make_vm(self):
        pass

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_create_xcat_node(self, xrequest):
        # TODO:moving to vmops and change name to 'create_vm_node'
        pass

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_xcat_node(self, xrequest):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.rmdef('/' + fake_userid)

        self._zvmclient._delete_xcat_node(fake_userid)
        xrequest.assert_called_once_with('DELETE', fake_url)

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmclient.XCATClient, '_delete_xcat_node')
    def test_delete_userid(self, delete_xcat_node, xrequest):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.rmvm('/' + fake_userid)

        self._zvmclient._delete_userid(fake_url)
        xrequest.assert_called_once_with('DELETE', fake_url)

    @mock.patch.object(zvmclient.XCATClient, '_delete_userid')
    def test_remove_vm(self, delete_userid):
        fake_userid = 'fake_userid'
        fake_url = self._xcat_url.rmvm('/' + fake_userid)
        self._zvmclient.remove_vm(fake_userid)
        delete_userid.assert_called_once_with(fake_url)

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
    def test_change_vm_ipl_state(self, xrequest):
        fake_userid = 'fake_userid'
        fake_state = 0100
        fake_body = ['--setipl %s' % fake_state]
        fake_url = self._xcat_url.chvm('/' + fake_userid)

        self._zvmclient.change_vm_ipl_state(fake_userid, fake_state)
        xrequest.assert_called_once_with('PUT', fake_url, fake_body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_change_vm_fmt(self, xrequest):
        fake_userid = 'fake_userid'
        fmt = False
        action = ''
        diskpool = ''
        vdev = ''
        size = '1000M'
        fake_url = self._xcat_url.chvm('/' + fake_userid)
        fake_body = [" ".join([action, diskpool, vdev, size])]

        self._zvmclient.change_vm_fmt(fake_userid, fmt, action,
                                      diskpool, vdev, size)
        xrequest.assert_called_once_with('PUT', fake_url, fake_body)

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

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_lsdef_image(self, xrequest):
        fake_image_uuid = 'image_uuid_xxxx'
        fake_parm = '&criteria=profile=~' + fake_image_uuid
        fake_url = self._xcat_url.lsdef_image(addp=fake_parm)

        self._zvmclient.lsdef_image(fake_image_uuid)
        xrequest.assert_called_once_with('GET', fake_url)

    def test_check_space_imgimport_xcat(self):
        pass

    def test_export_image(self):
        pass

    @mock.patch.object(zvmutils, 'xcat_request')
    @mock.patch.object(zvmutils, 'get_host')
    @mock.patch.object(os, 'remove')
    def test_import_image(self, remove_file, get_host, xrequest):
        image_bundle_package = 'asdfe'
        image_profile = 'imagep_prooooffffille'
        remote_host_info = {}
        get_host.return_value = remote_host_info
        fake_url = self._xcat_url.imgimport()
        fake_body = ['osimage=%s' % image_bundle_package,
                     'profile=%s' % image_profile,
                     'remotehost=%s' % remote_host_info,
                     'nozip']
        remove_file.return_value = None

        self._zvmclient.import_image(image_bundle_package, image_profile)
        xrequest.assert_called_once_with('POST', fake_url, fake_body)

    def test_add_host_table_record(self, xrequest):
        """Add/Update hostname/ip bundle in xCAT MN nodes table."""
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
    @mock.patch.object(zvmclient.XCATClient, '_config_xcat_mac')
    def test_preset_vm_network(self, config_mac, add_host, makehost):
        self._zvmclient.preset_vm_network("fakeid", "fakeip")
        config_mac.assert_called_with("fakeid")
        add_host.assert_called_with("fakeid", "fakeip", "fakeid")
        makehost.assert_called_with()

    @mock.patch.object(zvmclient.XCATClient, '_add_mac_table_record')
    def test_config_xcat_mac(self, add_mac):
        self._zvmclient._config_xcat_mac("fakeid")
        add_mac.assert_called_with("fakeid", "fake", "00:00:00:00:00:00")
