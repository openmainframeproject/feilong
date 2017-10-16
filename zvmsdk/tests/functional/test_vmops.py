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
import time

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.tests.functional import base


CONF = config.CONF
printLOG = log.LOG


class SDKGuestActionsTestCase(base.SDKAPIBaseTestCase):

    TEST_UIDS = ['ugcprof', 'ugcdup', 'ugdtrspt', 'ugdrhost', 'ugdvdev',
                 'ugsnml']

    def __init__(self, methodName='runTest'):
        super(SDKGuestActionsTestCase, self).__init__(methodName)
        self.test_util = base.SDKAPITestUtils()
        self.test_util.image_import()
        self.image_name = os.path.basename(CONF.tests.image_path)

        # cleanup all userids that will be used in this test
        for userid in self.TEST_UIDS:
            self.sdkapi.guest_delete(userid)
            time.sleep(2)

        self.disks = [
            {'size': '1G',
             'format': 'ext3',
             'is_boot_disk': True,
             'disk_pool': CONF.zvm.disk_pool}]

    def test_create_with_profile(self):
        """Create guest with profile specified.

        :Steps:
        1. Create guest with profile specified
        2. Delete the guest

        :Verify:
        1. No exception
        """
        userid_prof = "ugcprof"
        self.addCleanup(self.sdkapi.guest_delete, userid_prof)

        # make sure the guest not exists
        self.sdkapi.guest_create(userid_prof, 1, 1024,
                                 user_profile=CONF.zvm.user_profile)
        self.assertTrue(
                self.test_util.wait_until_create_userid_complete(userid_prof))

    def test_create_with_duplicate_userid(self):
        """Create guest with duplicated userid.

        :Steps:
        1. Create a guest
        2. Create another guest with same userid as first one

        :Verify:
        1. return value with rc/rs 400/8
        """
        userid_duplicate = "ugcdup"
        self.addCleanup(self.sdkapi.guest_delete, userid_duplicate)

        self.sdkapi.guest_create(userid_duplicate, 1, 1024)
        try:
            self.sdkapi.guest_create(userid_duplicate, 1, 1024)
        except exception.SDKSMUTRequestFailed as err:
            self.assertEqual(err.results['rc'], 400)
            self.assertEqual(err.results['rs'], 8)

    def _make_transport_file(self):
        transport_file = "/tmp/sdktest.txt"
        with open(transport_file, 'w') as f:
            f.write('A quick brown fox jump over the lazy dog.\n')
        self.addCleanup(os.remove, transport_file)
        return transport_file

    def test_deploy_with_transport_file(self):
        """Deploy guest with transport file.

        :Steps:
        1. Create a guest
        2. Deploy the guest with transport file

        :Verify:
        1. The guest can start correctly
        """
        userid_trspt = "ugdtrspt"
        self.addCleanup(self.sdkapi.guest_delete, userid_trspt)

        transport_file = self._make_transport_file()

        self.sdkapi.guest_create(userid_trspt, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(userid_trspt, self.image_name, transport_file)

        self.sdkapi.guest_start(userid_trspt)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                            userid_trspt, 'on')
        self.assertTrue(powered_on)

    def test_deploy_with_remote_host(self):
        """Deploy guest with remote_host.

        :Steps:
        1. Create a guest
        2. Deploy the guest with remote_host

        :Verify:
        1. The guest can start correctly
        """
        userid_rmthost = 'ugdrhost'
        self.addCleanup(self.sdkapi.guest_delete, userid_rmthost)

        remote_host = CONF.tests.remote_host
        transportfile = self._make_transport_file()
        self.sdkapi.guest_create(userid_rmthost, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(userid_rmthost,
                                 self.image_name,
                                 transportfiles=transportfile,
                                 remotehost=remote_host)
        self.sdkapi.guest_start(userid_rmthost)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                        userid_rmthost, 'on')
        self.assertTrue(powered_on)

    def test_deploy_with_vdev(self):
        """Deploy guest with root vdev.

        :Steps:
        1. Create a guest
        2. Deploy the guest to specified vdev

        :Verify:
        1. The guest can start correctly
        """
        userid_vdev = 'ugdvdev'
        self.addCleanup(self.sdkapi.guest_delete, userid_vdev)

        # back up user_root_vdev value in config file
        def _restore_conf(root_vdev_back):
            CONF.zvm.user_root_vdev = root_vdev_back
        root_vdev_back = CONF.zvm.user_root_vdev
        self.addCleanup(_restore_conf, root_vdev_back)

        new_root = '123'
        CONF.zvm.user_root_vdev = new_root
        disks = [
            {'size': '3G',
             'format': 'xfs',
             'is_boot_disk': True,
             'disk_pool': CONF.zvm.disk_pool},
            {'size': '200M',
             'format': 'ext3',
             'is_boot_disk': False,
             'disk_pool': 'ECKD:xcateckd'}]

        self.sdkapi.guest_create(userid_vdev, 1, 1024, disk_list=disks)
        self.sdkapi.guest_deploy(userid_vdev,
                                 self.image_name,
                                 vdev=new_root)
        self.sdkapi.guest_start(userid_vdev)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                        userid_vdev, 'on')
        self.assertTrue(powered_on)

    def test_guest_start_stop(self):
        """Start and stop guest vm.

        :Steps:
        1. Create a guest
        2. Power off the guest
        3. Power on the guest
        4. Power off the guest again
        2. Deploy the guest to specified vdev

        :Verify:
        1. The guest can be set to expect power state.
        """
        userid_normal = "ugsnml"
        self.addCleanup(self.sdkapi.guest_delete, userid_normal)

        self.sdkapi.guest_create(userid_normal, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(userid_normal, self.image_name)

        # make sure the guest is off
        self.sdkapi.guest_stop(userid_normal)
        self.assertTrue(self.test_util.wait_until_guest_in_power_state(
                                                        userid_normal, 'off'))
        # power on the guest
        self.sdkapi.guest_start(userid_normal)
        self.assertTrue(self.test_util.wait_until_guest_in_power_state(
                                                        userid_normal, 'on'))
        # power off the guest
        self.sdkapi.guest_stop(userid_normal)
        self.assertTrue(self.test_util.wait_until_guest_in_power_state(
                                                        userid_normal, 'off'))
