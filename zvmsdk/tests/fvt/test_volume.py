# Copyright 2017,2018 IBM Corp.
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

import time
from parameterized import parameterized
from zvmsdk.tests.fvt import base
from zvmsdk import config
from zvmsdk import smtclient
from zvmsdk.tests.fvt import test_utils

CONF = config.CONF
TEST_IMAGE_LIST = test_utils.TEST_IMAGE_LIST
# This list contains tuple of (case_name, userid, version) where case_name is
# composed by image name and image distro, userid is used as userid to deploy
# guest with the corresponding image, version is the guest distro version.
TEST_USERID_LIST = []


def generate_test_userid_list():
    global TEST_USERID_LIST
    utils = test_utils.ZVMConnectorTestUtils()
    for i in range(0, len(TEST_IMAGE_LIST)):
        userid = utils.generate_test_userid()
        TEST_USERID_LIST.append((TEST_IMAGE_LIST[i][0], userid,
                                 TEST_IMAGE_LIST[i][2]))


# Generate the global userid list at the beginning so that the following
# test classes (currently only cases in GuestHandlerTestCaseWithDeployedGuest)
# can use this list to parameterize test cases for different distros.
generate_test_userid_list()


class VolumeTestCase(base.ZVMConnectorBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(VolumeTestCase, cls).setUpClass()
        cls.smtcli = smtclient.get_smtclient()
        cls.userid_list = []
        # Deploy a guest with each specified image and previously generated
        # userid.
        for i in range(0, len(TEST_IMAGE_LIST)):
            image = TEST_IMAGE_LIST[i]
            userid = TEST_USERID_LIST[i][1]
            cls.utils.deploy_guest(userid, image_path=image[1],
                                   os_version=image[2])
            cls.userid_list.append(userid)

    @classmethod
    def tearDownClass(cls):
        super(VolumeTestCase, cls).tearDownClass()
        for userid in cls.userid_list:
            cls.utils.destroy_guest(userid)

    def check_mount_result(self, userid):
        cmd = 'test -e %s && echo exist' % CONF.tests.mount_point
        ret = self.smtcli.execute_cmd_direct(userid, cmd)['response'][0]
        return ret == 'exist'

    @parameterized.expand(TEST_USERID_LIST)
    def test_attach_detach_active_mode(self, case_name, userid, os_version):
        # active mode: power on guest
        self.utils.power_on_guest_until_reachable(userid)
        time.sleep(10)
        # prepare connection_info
        connection_info = {'assigner_id': userid,
                           'zvm_fcp': CONF.tests.zvm_fcp,
                           'os_version': os_version,
                           'multipath': True,
                           'target_wwpn': CONF.tests.target_wwpn,
                           'target_lun': CONF.tests.target_lun,
                           'mount_point': CONF.tests.mount_point}
        # attach volume
        resp = self.client.volume_attach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
        time.sleep(60)
        self.assertTrue(self.check_mount_result(userid))
        # detach volume
        resp = self.client.volume_detach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
        time.sleep(60)
        self.assertFalse(self.check_mount_result(userid))

    @parameterized.expand(TEST_USERID_LIST)
    def test_attach_detach_inactive_mode(self, case_name,
                                         userid, os_version):
        self.utils.power_on_guest_until_reachable(userid)
        time.sleep(10)
        connection_info = {'assigner_id': userid,
                           'zvm_fcp': CONF.tests.zvm_fcp,
                           'os_version': os_version,
                           'multipath': True,
                           'target_wwpn': CONF.tests.target_wwpn,
                           'target_lun': CONF.tests.target_lun,
                           'mount_point': CONF.tests.mount_point}
        # attach volume
        self.utils.softstop_guest(userid)
        time.sleep(10)
        resp = self.client.volume_attach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
        self.utils.power_on_guest_until_reachable(userid)
        time.sleep(60)
        self.assertTrue(self.check_mount_result(userid))
        # detach volume
        self.utils.softstop_guest(userid)
        time.sleep(10)
        resp = self.client.volume_detach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
        self.utils.power_on_guest_until_reachable(userid)
        time.sleep(60)
        self.assertFalse(self.check_mount_result(userid))

    @parameterized.expand(TEST_USERID_LIST)
    def test_attach_detach_active_userid_not_exist(self, case_name, userid,
                                                   os_version):
        connection_info = {'assigner_id': 'dummy',
                           'zvm_fcp': CONF.tests.zvm_fcp,
                           'os_version': os_version,
                           'multipath': True,
                           'target_wwpn': CONF.tests.target_wwpn,
                           'target_lun': CONF.tests.target_lun,
                           'mount_point': CONF.tests.mount_point}
        resp = self.client.volume_attach(connection_info)
        self.assertEqual(404, resp.status_code)
        resp = self.client.volume_detach(connection_info)
        self.assertEqual(404, resp.status_code)

    @parameterized.expand(TEST_USERID_LIST)
    def test_attach_detach_inactive_userid_not_exist(self, case_name, userid,
                                                     os_version):
        connection_info = {'assigner_id': 'dummy',
                           'zvm_fcp': CONF.tests.zvm_fcp,
                           'os_version': os_version,
                           'multipath': True,
                           'target_wwpn': CONF.tests.target_wwpn,
                           'target_lun': CONF.tests.target_lun,
                           'mount_point': CONF.tests.mount_point}
        resp = self.client.volume_attach(connection_info)
        self.assertEqual(404, resp.status_code)
        resp = self.client.volume_detach(connection_info)
        self.assertEqual(404, resp.status_code)

    @parameterized.expand(TEST_USERID_LIST)
    def test_attach_detach_bootable_volume(self, case_name,
                                           userid, os_version):
        # prepare connection_info
        connection_info = {'assigner_id': userid,
                           'zvm_fcp': CONF.tests.zvm_fcp,
                           'os_version': os_version,
                           'multipath': True,
                           'target_wwpn': CONF.tests.target_wwpn,
                           'target_lun': CONF.tests.target_lun,
                           'mount_point': CONF.tests.mount_point,
                           'is_root_volume': True}
        # attach volume
        resp = self.client.volume_attach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
        # detach volume
        resp = self.client.volume_detach(connection_info)
        time.sleep(10)
        self.assertEqual(200, resp.status_code)
