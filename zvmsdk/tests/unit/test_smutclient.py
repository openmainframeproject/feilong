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
import tempfile

from smutLayer import smut

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils
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
        self.assertRaises(exception.ZVMClientRequestFailed,
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
        base.set_conf('zvm', 'default_admin_userid', 'lbyuser1 lbyuser2')
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
        client_userid = 'ClientID'
        requestData = "ChangeVM FakeID punchfile /tmp/FakeID/iucvauth.sh" + \
                      " --class x"
        request.return_value = {'overallRC': 0}
        self._smutclient.guest_authorize_iucv_client(fake_userid,
                                                     client_userid)
        request.assert_called_once_with(requestData)
        self.assertIs(os.path.exists('/tmp/FakeID'), False)

    @mock.patch.object(zvmutils.PathUtils, 'clean_temp_folder')
    @mock.patch.object(tempfile, 'mkdtemp')
    @mock.patch.object(zvmutils, 'execute')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_deploy(self, request, execute, mkdtemp, cleantemp):
        base.set_conf("zvm", "user_root_vdev", "0100")
        execute.side_effect = [(0, ""), (0, "")]
        mkdtemp.return_value = '/tmp/tmpdir'
        userid = 'fakeuser'
        image_name = 'fakeimg'
        transportfiles = '/faketrans'
        self._smutclient.guest_deploy(userid, image_name, transportfiles)
        unpack_cmd = ['/opt/zthin/bin/unpackdiskimage', 'fakeuser', '0100',
                     '/var/lib/zvmsdk/images/fakeimg']
        cp_cmd = ["/usr/bin/cp", '/faketrans', '/tmp/tmpdir/cfgdrv']
        execute.assert_has_calls([mock.call(unpack_cmd), mock.call(cp_cmd)])
        purge_rd = "changevm fakeuser purgerdr"
        punch_rd = "changevm fakeuser punchfile /tmp/tmpdir/cfgdrv --class X"
        request.assert_has_calls([mock.call(purge_rd), mock.call(punch_rd)])
        mkdtemp.assert_called_with()
        cleantemp.assert_called_with('/tmp/tmpdir')

    @mock.patch.object(zvmutils, 'execute')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_deploy_unpackdiskimage_failed(self, request, execute):
        base.set_conf("zvm", "user_root_vdev", "0100")
        userid = 'fakeuser'
        image_name = 'fakeimg'
        transportfiles = '/faketrans'
        unpack_error = ('unpackdiskimage fakeuser start time: '
                        '2017-08-16-01:29:59.453\nSOURCE USER ID: "fakeuser"\n'
                        'DISK CHANNEL:   "0100"\n'
                        'IMAGE FILE:     "/var/lib/zvmsdk/images/fakeimg"\n\n'
                        'Image file compression level: 6\n'
                        'Deploying image to fakeuser\'s disk at channel 100.\n'
                        'ERROR: Unable to link fakeuser 0100 disk. '
                        'HCPLNM053E FAKEUSER not in CP directory\n'
                        'HCPDTV040E Device 260C does not exist\n'
                        'ERROR: Failed to connect disk: fakeuser:0100\n\n'
                        'IMAGE DEPLOYMENT FAILED.\n'
                        'A detailed trace can be found at: /var/log/zthin/'
                        'unpackdiskimage_trace_2017-08-16-01:29:59.453.txt\n'
                        'unpackdiskimage end time: 2017-08-16-01:29:59.605\n')
        execute.return_value = (3, unpack_error)
        self.assertRaises(exception.ZVMGuestDeployFailed,
                           self._smutclient.guest_deploy, userid, image_name,
                           transportfiles)
        unpack_cmd = ['/opt/zthin/bin/unpackdiskimage', 'fakeuser', '0100',
                     '/var/lib/zvmsdk/images/fakeimg']
        execute.assert_called_once_with(unpack_cmd)

    @mock.patch.object(zvmutils.PathUtils, 'clean_temp_folder')
    @mock.patch.object(tempfile, 'mkdtemp')
    @mock.patch.object(zvmutils, 'execute')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_deploy_cp_transport_failed(self, request, execute, mkdtemp,
                                              cleantemp):
        base.set_conf("zvm", "user_root_vdev", "0100")
        cp_error = ("/usr/bin/cp: cannot stat '/faketrans': "
                    "No such file or directory\n")
        execute.side_effect = [(0, ""), (1, cp_error)]
        mkdtemp.return_value = '/tmp/tmpdir'
        userid = 'fakeuser'
        image_name = 'fakeimg'
        transportfiles = '/faketrans'
        self.assertRaises(exception.ZVMGuestDeployFailed,
                           self._smutclient.guest_deploy, userid, image_name,
                           transportfiles)
        unpack_cmd = ['/opt/zthin/bin/unpackdiskimage', 'fakeuser', '0100',
                     '/var/lib/zvmsdk/images/fakeimg']
        cp_cmd = ["/usr/bin/cp", '/faketrans', '/tmp/tmpdir/cfgdrv']
        execute.assert_has_calls([mock.call(unpack_cmd), mock.call(cp_cmd)])
        purge_rd = "changevm fakeuser purgerdr"
        request.assert_called_once_with(purge_rd)
        mkdtemp.assert_called_with()
        cleantemp.assert_called_with('/tmp/tmpdir')

    @mock.patch.object(zvmutils.PathUtils, 'clean_temp_folder')
    @mock.patch.object(tempfile, 'mkdtemp')
    @mock.patch.object(zvmutils, 'execute')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_guest_deploy_smut_request_failed(self, request, execute, mkdtemp,
                                       cleantemp):
        base.set_conf("zvm", "user_root_vdev", "0100")
        fake_smut_results = {'rs': 8, 'errno': 0, 'strError': 'Failed',
                             'overallRC': 3, 'rc': 400, 'logEntries': '',
                             'response': ['(Error) output and error info']}
        execute.side_effect = [(0, ""), (0, "")]
        request.side_effect = [None,
                               exception.ZVMClientRequestFailed(
                                   results=fake_smut_results)]
        mkdtemp.return_value = '/tmp/tmpdir'
        userid = 'fakeuser'
        image_name = 'fakeimg'
        transportfiles = '/faketrans'
        remote_host = "user@1.1.1.1"
        self.assertRaises(exception.ZVMGuestDeployFailed,
                           self._smutclient.guest_deploy, userid, image_name,
                           transportfiles, remote_host)
        unpack_cmd = ['/opt/zthin/bin/unpackdiskimage', 'fakeuser', '0100',
                     '/var/lib/zvmsdk/images/fakeimg']
        scp_cmd = ["/usr/bin/scp", "-B", 'user@1.1.1.1:/faketrans',
                  '/tmp/tmpdir/cfgdrv']
        execute.assert_has_calls([mock.call(unpack_cmd), mock.call(scp_cmd)])
        purge_rd = "changevm fakeuser purgerdr"
        punch_rd = "changevm fakeuser punchfile /tmp/tmpdir/cfgdrv --class X"
        request.assert_has_calls([mock.call(purge_rd), mock.call(punch_rd)])
        mkdtemp.assert_called_with()
        cleantemp.assert_called_with('/tmp/tmpdir')

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_grant_user_to_vswitch(self, request, userid):
        userid.return_value = 'FakeHostID'
        vswitch_name = 'FakeVs'
        userid = 'FakeID'
        requestData = ' '.join((
            'SMAPI FakeHostID API Virtual_Network_Vswitch_Set_Extended',
            "--operands",
            "-k switch_name=FakeVs",
            "-k grant_userid=FakeID",
            "-k persist=YES"))
        self._smutclient.grant_user_to_vswitch(vswitch_name, userid)
        request.assert_called_once_with(requestData)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_revoke_user_from_vswitch(self, request, userid):
        """Revoke user for vswitch."""
        userid.return_value = 'FakeHostID'
        vswitch_name = 'FakeVs'
        userid = 'FakeID'
        requestData = ' '.join((
            'SMAPI FakeHostID API Virtual_Network_Vswitch_Set_Extended',
            "--operands",
            "-k switch_name=FakeVs",
            "-k revoke_userid=FakeID",
            "-k persist=YES"))

        self._smutclient.revoke_user_from_vswitch(vswitch_name, userid)
        request.assert_called_once_with(requestData)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_image_performance_query_single(self, smut_req, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                     'overallRC': 0, 'logEntries': [], 'rc': 0,
                                     'response': [
                                        'Virtual server ID: FAKEVM',
                                        'Record version: "1"',
                                        'Guest flags: "0"',
                                        'Used CPU time: "646609178 uS"',
                                        'Elapsed time: "596837441984 uS"',
                                        'Minimum memory: "0 KB"',
                                        'Max memory: "2097152 KB"',
                                        'Shared memory: "302180 KB"',
                                        'Used memory: "302180 KB"',
                                        'Active CPUs in CEC: "44"',
                                        'Logical CPUs in VM: "6"',
                                        'Guest CPUs: "2"',
                                        'Minimum CPU count: "2"',
                                        'Max CPU limit: "10000"',
                                        'Processor share: "100"',
                                        'Samples CPU in use: "371"',
                                        ',Samples CPU delay: "116"',
                                        'Samples page wait: "0"',
                                        'Samples idle: "596331"',
                                        'Samples other: "12"',
                                        'Samples total: "596830"',
                                        'Guest name: "FAKEVM  "',
                                        '']
                                     }
        pi_info = self._smutclient.image_performance_query('fakevm')
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "302180 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "646609178 uS")
        self.assertEqual(pi_info['FAKEVM']['elapsed_cpu_time'],
                         "596837441984 uS")
        self.assertEqual(pi_info['FAKEVM']['min_cpu_count'], "2")
        self.assertEqual(pi_info['FAKEVM']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_in_use'], "371")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_delay'], "116")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "2097152 KB")
        self.assertEqual(pi_info['FAKEVM']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM']['shared_memory'], "302180 KB")

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_image_performance_query_single_off(self, smut_req,
                                                get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                     'overallRC': 0, 'logEntries': [], 'rc': 0,
                                     'response': []
                                     }
        pi_info = self._smutclient.image_performance_query('fakevm')
        self.assertDictEqual(pi_info, {})

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_image_performance_query_multiple(self, smut_req, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        response_list = ['Virtual server ID: fakevm',
                         'Record version: "1"',
                         'Guest flags: "0"',
                         'Used CPU time: "652337849 uS"',
                         'Elapsed time: "602181110336 uS"',
                         'Minimum memory: "0 KB"',
                         'Max memory: "2097152 KB"',
                         'Shared memory: "302336 KB"',
                         'Used memory: "302336 KB"',
                         'Active CPUs in CEC: "44"',
                         'Logical CPUs in VM: "6"',
                         'Guest CPUs: "2"',
                         'Minimum CPU count: "2"',
                         'Max CPU limit: "10000"',
                         'Processor share: "100"',
                         'Samples CPU in use: "375"',
                         ',Samples CPU delay: "116"',
                         'Samples page wait: "0"',
                         'Samples idle: "601671"',
                         'Samples other: "12"',
                         'Samples total: "602174"',
                         'Guest name: "FAKEVM  "',
                         '',
                         'Virtual server ID: fakevm2',
                         'Record version: "1"',
                         'Guest flags: "0"',
                         'Used CPU time: "3995650268844 uS"',
                         'Elapsed time: "3377790094595 uS"',
                         'Minimum memory: "0 KB"',
                         'Max memory: "8388608 KB"',
                         'Shared memory: "8383048 KB"',
                         'Used memory: "8383048 KB"',
                         'Active CPUs in CEC: "44"',
                         'Logical CPUs in VM: "6"',
                         'Guest CPUs: "4"',
                         'Minimum CPU count: "4"',
                         'Max CPU limit: "10000"',
                         'Processor share: "100"',
                         'Samples CPU in use: "1966323"',
                         ',Samples CPU delay: "111704"',
                         'Samples page wait: "0"',
                         'Samples idle: "4001258"',
                         'Samples other: "8855"',
                         'Samples total: "6088140"',
                         'Guest name: "FAKEVM2 "',
                         '']

        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                     'overallRC': 0, 'logEntries': [], 'rc': 0,
                                     'response': response_list
                                     }

        pi_info = self._smutclient.image_performance_query(['fakevm',
                                                            'fakevm2'])
        self.assertEqual(pi_info['FAKEVM']['used_memory'], "302336 KB")
        self.assertEqual(pi_info['FAKEVM']['used_cpu_time'], "652337849 uS")
        self.assertEqual(pi_info['FAKEVM']['elapsed_cpu_time'],
                         "602181110336 uS")
        self.assertEqual(pi_info['FAKEVM']['min_cpu_count'], "2")
        self.assertEqual(pi_info['FAKEVM']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_in_use'], "375")
        self.assertEqual(pi_info['FAKEVM']['samples_cpu_delay'], "116")
        self.assertEqual(pi_info['FAKEVM']['guest_cpus'], "2")
        self.assertEqual(pi_info['FAKEVM']['userid'], "FAKEVM")
        self.assertEqual(pi_info['FAKEVM']['max_memory'], "2097152 KB")
        self.assertEqual(pi_info['FAKEVM']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM']['shared_memory'], "302336 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_memory'], "8383048 KB")
        self.assertEqual(pi_info['FAKEVM2']['used_cpu_time'],
                         "3995650268844 uS")
        self.assertEqual(pi_info['FAKEVM2']['elapsed_cpu_time'],
                         "3377790094595 uS")
        self.assertEqual(pi_info['FAKEVM2']['min_cpu_count'], "4")
        self.assertEqual(pi_info['FAKEVM2']['max_cpu_limit'], "10000")
        self.assertEqual(pi_info['FAKEVM2']['samples_cpu_in_use'], "1966323")
        self.assertEqual(pi_info['FAKEVM2']['samples_cpu_delay'], "111704")
        self.assertEqual(pi_info['FAKEVM2']['guest_cpus'], "4")
        self.assertEqual(pi_info['FAKEVM2']['userid'], "FAKEVM2")
        self.assertEqual(pi_info['FAKEVM2']['max_memory'], "8388608 KB")
        self.assertEqual(pi_info['FAKEVM2']['min_memory'], "0 KB")
        self.assertEqual(pi_info['FAKEVM2']['shared_memory'], "8383048 KB")

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_virtual_network_vswitch_query_iuo_stats(self, smut_req,
                                                     get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        vsw_data = ['vswitch count: 2',
                    '',
                    'vswitch number: 1',
                    'vswitch name: XCATVSW1',
                    'uplink count: 1',
                    'uplink_conn: 6240',
                    'uplink_fr_rx:     3658251',
                    'uplink_fr_rx_dsc: 0',
                    'uplink_fr_rx_err: 0',
                    'uplink_fr_tx:     4209828',
                    'uplink_fr_tx_dsc: 0',
                    'uplink_fr_tx_err: 0',
                    'uplink_rx:        498914052',
                    'uplink_tx:        2615220898',
                    'bridge_fr_rx:     0',
                    'bridge_fr_rx_dsc: 0',
                    'bridge_fr_rx_err: 0',
                    'bridge_fr_tx:     0',
                    'bridge_fr_tx_dsc: 0',
                    'bridge_fr_tx_err: 0',
                    'bridge_rx:        0',
                    'bridge_tx:        0',
                    'nic count: 2',
                    'nic_id: INST1 0600',
                    'nic_fr_rx:        573952',
                    'nic_fr_rx_dsc:    0',
                    'nic_fr_rx_err:    0',
                    'nic_fr_tx:        548780',
                    'nic_fr_tx_dsc:    0',
                    'nic_fr_tx_err:    4',
                    'nic_rx:           103024058',
                    'nic_tx:           102030890',
                    'nic_id: INST2 0600',
                    'nic_fr_rx:        17493',
                    'nic_fr_rx_dsc:    0',
                    'nic_fr_rx_err:    0',
                    'nic_fr_tx:        16886',
                    'nic_fr_tx_dsc:    0',
                    'nic_fr_tx_err:    4',
                    'nic_rx:           3111714',
                    'nic_tx:           3172646',
                    'vlan count: 0',
                    '',
                    'vswitch number: 2',
                    'vswitch name: XCATVSW2',
                    'uplink count: 1',
                    'uplink_conn: 6200',
                    'uplink_fr_rx:     1608681',
                    'uplink_fr_rx_dsc: 0',
                    'uplink_fr_rx_err: 0',
                    'uplink_fr_tx:     2120075',
                    'uplink_fr_tx_dsc: 0',
                    'uplink_fr_tx_err: 0',
                    'uplink_rx:        314326223',
                    'uplink_tx:        1503721533',
                    'bridge_fr_rx:     0',
                    'bridge_fr_rx_dsc: 0',
                    'bridge_fr_rx_err: 0',
                    'bridge_fr_tx:     0',
                    'bridge_fr_tx_dsc: 0',
                    'bridge_fr_tx_err: 0',
                    'bridge_rx:        0',
                    'bridge_tx:        0',
                    'nic count: 2',
                    'nic_id: INST1 1000',
                    'nic_fr_rx:        34958',
                    'nic_fr_rx_dsc:    0',
                    'nic_fr_rx_err:    0',
                    'nic_fr_tx:        16211',
                    'nic_fr_tx_dsc:    0',
                    'nic_fr_tx_err:    0',
                    'nic_rx:           4684435',
                    'nic_tx:           3316601',
                    'nic_id: INST2 1000',
                    'nic_fr_rx:        27211',
                    'nic_fr_rx_dsc:    0',
                    'nic_fr_rx_err:    0',
                    'nic_fr_tx:        12344',
                    'nic_fr_tx_dsc:    0',
                    'nic_fr_tx_err:    0',
                    'nic_rx:           3577163',
                    'nic_tx:           2515045',
                    'vlan count: 0'
                    ]

        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                 'overallRC': 0, 'logEntries': [],
                                 'rc': 0, 'response': vsw_data
                                 }
        vsw_dict = self._smutclient.virtual_network_vswitch_query_iuo_stats()
        self.assertEqual(2, len(vsw_dict['vswitches']))
        self.assertEqual(2, len(vsw_dict['vswitches'][1]['nics']))
        self.assertEqual('INST1',
                         vsw_dict['vswitches'][0]['nics'][0]['userid'])
        self.assertEqual('3577163',
                         vsw_dict['vswitches'][1]['nics'][1]['nic_rx'])
