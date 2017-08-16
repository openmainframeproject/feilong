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
        self.assertRaises(exception.ZVMSMUTRequestFailed,
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
                               exception.ZVMSMUTRequestFailed(
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
