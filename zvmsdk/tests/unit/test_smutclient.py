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
from zvmsdk import database
from zvmsdk import exception
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKSMUTClientTestCases(base.SDKTestCase):
    """Test cases for smut zvm client."""

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
        request.assert_called_once_with(requestData,
                                        "query power state of 'FakeID'")
        self.assertEqual('on', status)

    @mock.patch.object(smutclient.SMUTClient, 'add_mdisks')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    @mock.patch.object(database.GuestDbOperator, 'add_guest')
    def test_create_vm(self, add_guest, request, add_mdisks):
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
        add_guest.assert_called_once_with(user_id)

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
    def test_remove_mdisk(self, request):
        userid = 'fakeuser'
        vdev = '0102'
        rd = 'changevm fakeuser removedisk 0102'

        self._smutclient._remove_mdisk(userid, vdev),
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
        self.assertRaises(exception.SDKGuestOperationError,
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
        self.assertRaises(exception.SDKGuestOperationError,
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
                                   fake_smut_results, 'fake error')]
        mkdtemp.return_value = '/tmp/tmpdir'
        userid = 'fakeuser'
        image_name = 'fakeimg'
        transportfiles = '/faketrans'
        remote_host = "user@1.1.1.1"
        self.assertRaises(exception.ZVMClientRequestFailed,
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

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_get_host_info(self, smut_req):
        resp = ['z/VM Host: OPNSTK2',
                'Architecture: s390x',
                'CEC Vendor: IBM',
                'CEC Model: 2817',
                'Hypervisor OS: z/VM 6.4.0',
                'Hypervisor Name: OPNSTK2',
                'LPAR CPU Total: 6',
                'LPAR CPU Used: 6',
                'LPAR Memory Total: 50G',
                'LPAR Memory Offline: 0',
                'LPAR Memory Used: 36.5G',
                'IPL Time: IPL at 07/12/17 22:37:47 EDT']
        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                 'overallRC': 0, 'logEntries': [], 'rc': 0,
                                 'response': resp}

        expect = {'architecture': 's390x',
                  'cec_model': '2817',
                  'cec_vendor': 'IBM',
                  'hypervisor_name': 'OPNSTK2',
                  'hypervisor_os': 'z/VM 6.4.0',
                  'ipl_time': 'IPL at 07/12/17 22:37:47 EDT',
                  'lpar_cpu_total': '6',
                  'lpar_cpu_used': '6',
                  'lpar_memory_offline': '0',
                  'lpar_memory_total': '50G',
                  'lpar_memory_used': '36.5G',
                  'zvm_host': 'OPNSTK2'}
        host_info = self._smutclient.get_host_info()

        smut_req.assert_called_once_with('getHost general')
        self.assertDictEqual(host_info, expect)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_get_diskpool_info(self, smut_req):
        resp = ['XCATECKD Total: 3623.0G',
                'XCATECKD Used: 397.4G',
                'XCATECKD Free: 3225.6G']
        smut_req.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                 'overallRC': 0, 'logEntries': [], 'rc': 0,
                                 'response': resp}
        expect = {'disk_available': '3225.6G',
                  'disk_total': '3623.0G',
                  'disk_used': '397.4G'}
        dp_info = self._smutclient.get_diskpool_info('pool')

        smut_req.assert_called_once_with('getHost diskpoolspace pool')
        self.assertDictEqual(dp_info, expect)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_get_vswitch_list(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        request.return_value = {'overallRC': 0,
            'response': ['VSWITCH:  Name: VSTEST1', 'VSWITCH:  Name: VSTEST2',
                         'VSWITCH:  Name: VSTEST3', 'VSWITCH:  Name: VSTEST4']}
        expect = ['VSTEST1', 'VSTEST2', 'VSTEST3', 'VSTEST4']
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Query",
            "--operands",
            "-s \'*\'"))

        list = self._smutclient.get_vswitch_list()
        request.assert_called_once_with(rd)
        self.assertEqual(list, expect)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_set_vswitch_port_vlan_id(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        request.return_value = {'overallRC': 0}
        userid = 'FakeID'
        vswitch_name = 'FakeVS'
        vlan_id = 'FakeVLAN'
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Set_Extended",
            "--operands",
            "-k grant_userid=FakeID",
            "-k switch_name=FakeVS",
            "-k user_vlan_id=FakeVLAN",
            "-k persist=YES"))

        self._smutclient.set_vswitch_port_vlan_id(vswitch_name,
                                                  userid, vlan_id)
        request.assert_called_once_with(rd)

    @mock.patch.object(database.NetworkDbOperator,
                       'switch_select_record_for_userid')
    def test_get_vm_nic_vswitch_info(self, select):
        """
        Get NIC and switch mapping for the specified virtual machine.
        """
        select.return_value = [('FakeID', '1000', 'testvs1', None, None),
                               ('FakeID', '2000', 'testvs2', None, None)]
        expect = {'1000': 'testvs1', '2000': 'testvs2'}
        switch_dict = self._smutclient.get_vm_nic_vswitch_info('FakeID')
        select.assert_called_once_with('FakeID')
        self.assertDictEqual(switch_dict, expect)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_add_vswitch(self, request, get_smut_userid):
        get_smut_userid.return_value = 'SMUTUSER'
        request.return_value = {'overallRC': 0}
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Create_Extended",
            "--operands",
            "-k switch_name=fakename",
            "-k real_device_address='111 222'",
            "-k connection_value=CONNECT",
            "-k queue_memory_limit=5",
            "-k transport_type=ETHERNET",
            "-k vlan_id=10",
            "-k persist=NO",
            "-k port_type=ACCESS",
            "-k gvrp_value=GVRP",
            "-k native_vlanid=None",
            "-k routing_value=NONROUTER"))
        self._smutclient.add_vswitch("fakename", rdev="111 222",
                                     controller='*', connection='CONNECT',
                                     network_type='ETHERNET',
                                     router="NONROUTER", vid='10',
                                     port_type='ACCESS', gvrp='GVRP',
                                     queue_mem=5, native_vid=None,
                                     persist=False)
        request.assert_called_with(rd)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_set_vswitch(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        request.return_value = {'overallRC': 0}
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Set_Extended",
            "--operands",
            "-k switch_name=fake_vs",
            "-k real_device_address='1000 1003'"))
        self._smutclient.set_vswitch("fake_vs",
                                     real_device_address='1000 1003')
        request.assert_called_with(rd)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_set_vswitch_with_errorcode(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        request.side_effect = exception.ZVMClientRequestFailed(
            results, 'fake error')
        self.assertRaises(exception.ZVMClientRequestFailed,
                          self._smutclient.set_vswitch,
                          "vswitch_name", grant_userid='fake_id')

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_vswitch(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        request.return_value = {'rs': 0, 'errno': 0, 'strError': '',
                                'overallRC': 0, 'logEntries': [], 'rc': 0,
                                'response': ['fake response']}
        switch_name = 'FakeVS'
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Delete_Extended",
            "--operands",
            "-k switch_name=FakeVS",
            "-k persist=YES"))
        self._smutclient.delete_vswitch(switch_name, True)
        request.assert_called_once_with(rd)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_vswitch_with_errorcode(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        results = {'rs': 0, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 0,
                   'response': ['fake response']}
        request.side_effect = exception.ZVMClientRequestFailed(
            results, 'fake error')
        self.assertRaises(exception.ZVMClientRequestFailed,
                          self._smutclient.delete_vswitch,
                          "vswitch_name", True)

    @mock.patch.object(zvmutils, 'get_smut_userid')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_vswitch_not_exist(self, request, get_smut_userid):
        get_smut_userid.return_value = "SMUTUSER"
        results = {'rs': 40, 'errno': 0, 'strError': '',
                   'overallRC': 1, 'logEntries': [], 'rc': 212,
                   'response': ['fake response']}
        request.side_effect = exception.ZVMClientRequestFailed(
            results, 'fake error')
        switch_name = 'FakeVS'
        rd = ' '.join((
            "SMAPI SMUTUSER API Virtual_Network_Vswitch_Delete_Extended",
            "--operands",
            "-k switch_name=FakeVS",
            "-k persist=YES"))
        self._smutclient.delete_vswitch(switch_name, True)
        request.assert_called_once_with(rd)

    @mock.patch.object(database.NetworkDbOperator, 'switch_select_table')
    @mock.patch.object(smutclient.SMUTClient, '_create_nic')
    def test_create_nic(self, create_nic, switch_select_table):
        userid = 'fake_id'
        switch_select_table.return_value = [("fake_id", "1003"),
                                            ("fake_id", "1006")]
        self._smutclient.create_nic(userid, vdev='1009', nic_id='nic_id')
        create_nic.assert_called_with(userid, '1009', nic_id="nic_id",
                                      mac_addr=None, active=False)
        switch_select_table.assert_called_with()

    @mock.patch.object(database.NetworkDbOperator, 'switch_select_table')
    @mock.patch.object(smutclient.SMUTClient, '_create_nic')
    def test_create_nic_without_vdev(self, create_nic, switch_select_table):
        userid = 'fake_id'
        switch_select_table.return_value = [("fake_id", "1003"),
                                            ("fake_id", "2003")]
        self._smutclient.create_nic(userid, nic_id='nic_id')
        create_nic.assert_called_with(userid, '2006', nic_id='nic_id',
                                      mac_addr=None, active=False)
        switch_select_table.assert_called_with()

    @mock.patch.object(database.NetworkDbOperator, 'switch_select_table')
    def test_create_nic_with_used_vdev(self, switch_select_table):
        switch_select_table.return_value = [("fake_id", "1003"),
                                            ("fake_id", "1006")]
        self.assertRaises(exception.ZVMInvalidInputFormat,
                          self._smutclient.create_nic,
                          'fake_id', nic_id="nic_id", vdev='1004')

    @mock.patch.object(database.NetworkDbOperator, 'switch_add_record_for_nic')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_private_create_nic_active(self, request, add_record):
        request.return_value = {'overallRC': 0}
        self._smutclient._create_nic("fakenode", "fake_vdev",
                                     nic_id="fake_nic",
                                     mac_addr='11:22:33:44:55:66',
                                     active=True)
        add_record.assert_called_once_with("fakenode", "fake_vdev",
                                            port="fake_nic")
        rd1 = ' '.join((
            'SMAPI fakenode API Virtual_Network_Adapter_Create_Extended_DM',
            "--operands",
            "-k image_device_number=fake_vdev",
            "-k adapter_type=QDIO",
            "-k mac_id=445566"))

        rd2 = ' '.join((
            'SMAPI fakenode API Virtual_Network_Adapter_Create_Extended',
            "--operands",
            "-k image_device_number=fake_vdev",
            "-k adapter_type=QDIO"))
        request.assert_any_call(rd1)
        request.assert_any_call(rd2)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_get_user_direct(self, req):
        req.return_value = {'response': 'OK'}
        resp = self._smutclient.get_user_direct('user1')
        req.assert_called_once_with('getvm user1 directory')
        self.assertEqual(resp, 'OK')

    @mock.patch.object(database.NetworkDbOperator,
                       'switch_delete_record_for_nic')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_nic(self, request, delete_nic):
        userid = 'FakeID'
        vdev = 'FakeVdev'
        rd1 = ' '.join((
            "SMAPI FakeID API Virtual_Network_Adapter_Delete_DM",
            "--operands",
            '-v FakeVdev'))
        rd2 = ' '.join((
            "SMAPI FakeID API Virtual_Network_Adapter_Delete",
            "--operands",
            '-v FakeVdev'))
        self._smutclient.delete_nic(userid, vdev, True)
        request.assert_any_call(rd1)
        request.assert_any_call(rd2)
        delete_nic.assert_called_with(userid, vdev)

    @mock.patch.object(smutclient.SMUTClient, '_couple_nic')
    def test_couple_nic_to_vswitch(self, couple_nic):
        self._smutclient.couple_nic_to_vswitch("fake_userid",
                                               "fakevdev",
                                               "fake_VS_name",
                                               True)
        couple_nic.assert_called_with("fake_userid",
                                      "fakevdev",
                                      "fake_VS_name",
                                      active=True)

    @mock.patch.object(smutclient.SMUTClient, '_uncouple_nic')
    def test_uncouple_nic_from_vswitch(self, uncouple_nic):
        self._smutclient.uncouple_nic_from_vswitch("fake_userid",
                                                   "fakevdev",
                                                   False)
        uncouple_nic.assert_called_with("fake_userid",
                                        "fakevdev", active=False)

    @mock.patch.object(database.NetworkDbOperator,
                       'switch_updat_record_with_switch')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_couple_nic(self, request, update_switch):
        request.return_value = {'overallRC': 0}
        userid = 'FakeID'
        vdev = 'FakeVdev'
        vswitch_name = 'FakeVS'

        requestData1 = ' '.join((
            'SMAPI FakeID',
            "API Virtual_Network_Adapter_Connect_Vswitch_DM",
            "--operands",
            "-v FakeVdev",
            "-n FakeVS"))

        requestData2 = ' '.join((
            'SMAPI FakeID',
            "API Virtual_Network_Adapter_Connect_Vswitch",
            "--operands",
            "-v FakeVdev",
            "-n FakeVS"))

        self._smutclient._couple_nic(userid, vdev, vswitch_name,
                                     active=True)
        update_switch.assert_called_with(userid, vdev, vswitch_name)
        request.assert_any_call(requestData1)
        request.assert_any_call(requestData2)

    @mock.patch.object(database.NetworkDbOperator,
                       'switch_updat_record_with_switch')
    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_uncouple_nic(self, request, update_switch):
        request.return_value = {'overallRC': 0}
        userid = 'FakeID'
        vdev = 'FakeVdev'

        requestData1 = ' '.join((
            'SMAPI FakeID',
            "API Virtual_Network_Adapter_Disconnect_DM",
            "--operands",
            "-v FakeVdev"))

        requestData2 = ' '.join((
            'SMAPI FakeID',
            "API Virtual_Network_Adapter_Disconnect",
            "--operands",
            "-v FakeVdev"))

        self._smutclient._uncouple_nic(userid, vdev, active=True)
        update_switch.assert_called_with(userid, vdev, None)
        request.assert_any_call(requestData1)
        request.assert_any_call(requestData2)

    def get_vm_list(self):
        """Get the list of guests that are created by SDK
        return userid list"""
        guests = self._GuestDbOperator.get_guest_list()
        # guests is a list of tuple (uuid, userid, metadata, comments)
        userid_list = []
        for g in guests:
            userid_list.append(g[1])

    @mock.patch.object(database.GuestDbOperator,
                       'get_guest_list')
    def test_get_vm_list(self, db_list):
        db_list.return_value = [(u'9a5c9689-d099-46bb-865f-0c01c384f58c',
                                 u'TEST0', u'', u''),
                                (u'3abe0ac8-90b5-4b00-b624-969c184b8158',
                                 u'TEST1', u'comm1', u''),
                                (u'aa252ca5-03aa-4407-9c2e-d9737ddb8d24',
                                 u'TEST2', u'comm2', u'meta2')]
        userid_list = self._smutclient.get_vm_list()
        self.assertListEqual(sorted(userid_list),
                             sorted(['TEST0', 'TEST1', 'TEST2']))

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_userid(self, request):
        rd = 'deletevm fuser1 directory'
        self._smutclient.delete_userid('fuser1')
        request.assert_called_once_with(rd)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_userid_not_exist(self, request):
        rd = 'deletevm fuser1 directory'
        results = {'rc': 400, 'rs': 4, 'logEntries': ''}
        request.side_effect = exception.ZVMClientRequestFailed(results,
                                                               "fake error")
        self._smutclient.delete_userid('fuser1')
        request.assert_called_once_with(rd)

    @mock.patch.object(smutclient.SMUTClient, '_request')
    def test_delete_userid_failed(self, request):
        rd = 'deletevm fuser1 directory'
        results = {'rc': 400, 'rs': 104, 'logEntries': ''}
        request.side_effect = exception.ZVMClientRequestFailed(results,
                                                               "fake error")
        self.assertRaises(exception.ZVMClientRequestFailed,
                          self._smutclient.delete_userid, 'fuser1')
        request.assert_called_once_with(rd)

    @mock.patch.object(database.ImageDbOperator, 'image_add_record')
    @mock.patch.object(smutclient.SMUTClient, '_get_image_size')
    @mock.patch.object(smutclient.SMUTClient, '_get_disk_size_units')
    @mock.patch.object(smutclient.SMUTClient, '_get_md5sum')
    @mock.patch.object(smutclient.FilesystemBackend, 'image_import')
    @mock.patch.object(smutclient.SMUTClient, '_get_image_path_by_name')
    @mock.patch.object(database.ImageDbOperator, 'image_query_record')
    def test_image_import(self, image_query, get_img_path, image_import,
                          get_md5sum, disk_size_units, image_size,
                          image_add_record):
        image_name = 'testimage'
        url = 'file:///tmp/testdummyimg'
        image_meta = {'os_version': 'rhel6.5',
                      'md5sum': 'c73ce117eef8077c3420bfc8f473ac2f'}
        get_img_path.return_value = \
            '/var/lib/zvmsdk/images/netboot/rhel6.5/testimage'
        target = self._smutclient._get_image_path_by_name(image_name)
        image_query.return_value = []
        get_md5sum.return_value = 'c73ce117eef8077c3420bfc8f473ac2f'
        disk_size_units.return_value = '3338:CYL'
        image_size.return_value = '512000'
        self._smutclient.image_import(image_name, url, image_meta)
        image_query.assert_called_once_with(image_name)
        image_import.assert_called_once_with(image_name, url, image_meta,
                                             remote_host=None)
        get_md5sum.assert_called_once_with(target)
        disk_size_units.assert_called_once_with(target)
        image_size.assert_called_once_with(target)
        image_add_record.assert_called_once_with(image_name,
                                    'rhel6.5',
                                    'c73ce117eef8077c3420bfc8f473ac2f',
                                    '3338:CYL',
                                    '512000',
                                    'netboot')

    @mock.patch.object(smutclient.SMUTClient, '_get_image_path_by_name')
    @mock.patch.object(database.ImageDbOperator, 'image_query_record')
    def test_image_import_image_already_exist(self, image_query,
                                              get_image_path):
        image_name = 'testimage'
        url = 'file:///tmp/testdummyimg'
        image_meta = {'os_version': 'rhel6.5',
                      'md5sum': 'c73ce117eef8077c3420bfc8f473ac2f'}
        image_query.return_value = [(u'testimage', u'rhel6.5',
            u'c73ce117eef8077c3420bfc8f473ac2f',
            u'3338:CYL', u'5120000', u'netboot', None)]
        self._smutclient.image_import(image_name, url, image_meta)
        image_query.assert_called_once_with(image_name)
        get_image_path.assert_not_called()

    @mock.patch.object(smutclient.SMUTClient, '_get_md5sum')
    @mock.patch.object(smutclient.FilesystemBackend, 'image_import')
    @mock.patch.object(database.ImageDbOperator, 'image_query_record')
    def test_image_import_invalid_md5sum(self, image_query, image_import,
                                         get_md5sum):
        image_name = 'testimage'
        url = 'file:///tmp/testdummyimg'
        image_meta = {'os_version': 'rhel6.5',
                      'md5sum': 'c73ce117eef8077c3420bfc8f473ac2f'}
        image_query.return_value = []
        get_md5sum.return_value = 'c73ce117eef8077c3420bfc000000'
        self.assertRaises(exception.SDKImageOperationError,
                          self._smutclient.image_import,
                          image_name, url, image_meta)

    @mock.patch.object(database.ImageDbOperator, 'image_query_record')
    def test_image_query(self, image_query):
        image_name = "testimage"
        self._smutclient.image_query(image_name)
        image_query.assert_called_once_with(image_name)

    @mock.patch.object(database.ImageDbOperator, 'image_delete_record')
    @mock.patch.object(smutclient.SMUTClient, '_delete_image_file')
    def test_image_delete(self, delete_file, delete_db_record):
        image_name = 'testimage'
        self._smutclient.image_delete(image_name)
        delete_file.assert_called_once_with(image_name)
        delete_db_record.assert_called_once_with(image_name)

    @mock.patch.object(database.ImageDbOperator, 'query_disk_size_units')
    def test_image_get_root_disk_size(self, query_disk_size_units):
        image_name = 'testimage'
        self._smutclient.image_get_root_disk_size(image_name)
        query_disk_size_units.assert_called_once_with(image_name)

    @mock.patch.object(database.ImageDbOperator, 'image_query_record')
    @mock.patch.object(smutclient.FilesystemBackend, 'image_export')
    def test_image_export(self, image_export, image_query):
        image_name = u'testimage'
        dest_url = 'file:///path/to/exported/image'
        remote_host = 'nova@9.x.x.x'
        image_query.return_value = [(u'testimage', u'rhel6.5',
            u'c73ce117eef8077c3420bfc8f473ac2f',
            u'3338:CYL', u'5120000', u'netboot', None)]
        expect_return = {
            'image_name': u'testimage',
            'image_path': u'file:///path/to/exported/image',
            'os_version': u'rhel6.5',
            'md5sum': u'c73ce117eef8077c3420bfc8f473ac2f'
        }
        real_return = self._smutclient.image_export(image_name, dest_url,
                                                remote_host=remote_host)
        image_query.assert_called_once_with(image_name)
        self.assertDictEqual(real_return, expect_return)

    def test_generate_vdev(self):
        base = '0100'
        idx = 1
        vdev = self._smutclient._generate_vdev(base, idx)
        self.assertEqual(vdev, '0101')

    @mock.patch.object(smutclient.SMUTClient, '_add_mdisk')
    def test_add_mdisks(self, add_mdisk):
        userid = 'fakeuser'
        disk_list = [{'size': '1g',
                      'is_boot_disk': True,
                      'disk_pool': 'ECKD:eckdpool1'},
                     {'size': '200000',
                      'disk_pool': 'FBA:fbapool1',
                      'format': 'ext3'}]
        self._smutclient.add_mdisks(userid, disk_list)
        add_mdisk.assert_any_call(userid, disk_list[0], '0100')
        add_mdisk.assert_any_call(userid, disk_list[1], '0101')

    @mock.patch.object(smutclient.SMUTClient, '_remove_mdisk')
    def test_remove_mdisks(self, remove_mdisk):
        userid = 'fakeuser'
        vdev_list = ['102', '103']
        self._smutclient.remove_mdisks(userid, vdev_list)
        remove_mdisk.assert_any_call(userid, vdev_list[0])
        remove_mdisk.assert_any_call(userid, vdev_list[1])

    @mock.patch.object(smutclient.SMUTClient, 'image_performance_query')
    def test_get_image_performance_info(self, ipq):
        ipq.return_value = {
            u'FAKEVM': {
                'used_memory': u'5222192 KB',
                'used_cpu_time': u'25640530229 uS',
                'guest_cpus': u'2',
                'userid': u'FKAEVM',
                'max_memory': u'8388608 KB'}}
        info = self._smutclient.get_image_performance_info('fakevm')
        self.assertEqual(info['used_memory'], '5222192 KB')

    @mock.patch.object(smutclient.SMUTClient, 'image_performance_query')
    def test_get_image_performance_info_not_exist(self, ipq):
        ipq.return_value = {}
        info = self._smutclient.get_image_performance_info('fakevm')
        self.assertEqual(info, None)

    def test_is_vdev_valid_true(self):
        vdev = '1009'
        vdev_info = ['1003', '1006']
        result = self._smutclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, True)

    def test_is_vdev_valid_False(self):
        vdev = '2002'
        vdev_info = ['2000', '2004']
        result = self._smutclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, False)
