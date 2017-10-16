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

    def __init__(self, methodName='runTest'):
        super(SDKGuestActionsTestCase, self).__init__(methodName)
        self.test_util = base.SDKAPITestUtils()
        self.test_util.image_import()
        self.userid = 'ugatuid'
        self.image_name = os.path.basename(CONF.tests.image_path)
        self.disks = [
            {'size': '1G',
             'format': 'ext3',
             'is_boot_disk': True,
             'disk_pool': CONF.zvm.disk_pool}]

    def setUp(self):
        base.SDKAPIBaseTestCase.setUp(self)
        self.addCleanup(self.sdkutils.guest_destroy, self.userid)

    def test_create_with_profile(self):
        """Create guest with profile specified."""
        # make sure the guest not exists
        self.sdkapi.guest_create(self.userid, 1, 1024,
                                 user_profile=CONF.zvm.user_profile)
        self.assertTrue(
                self.test_util.wait_until_create_userid_complete(self.userid))

    def test_create_with_duplicate_userid(self):
        """Create guest with duplicated userid."""

        self.sdkapi.guest_create(self.userid, 1, 1024)
        try:
            self.sdkapi.guest_create(self.userid, 1, 1024)
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
        """Deploy guest with transport file."""
        transport_file = self._make_transport_file()

        self.sdkapi.guest_create(self.userid, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(self.userid, self.image_name, transport_file)

        self.sdkapi.guest_start(self.userid)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                            self.userid, 'on')
        self.assertTrue(powered_on)

    def test_deploy_with_remote_host(self):
        """Deploy guest with remote_host."""
        remote_host = CONF.tests.remote_host
        transportfile = self._make_transport_file()
        self.sdkapi.guest_create(self.userid, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(self.userid,
                                 self.image_name,
                                 transportfiles=transportfile,
                                 remotehost=remote_host)
        self.sdkapi.guest_start(self.userid)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                        self.userid, 'on')
        self.assertTrue(powered_on)

    def test_deploy_with_vdev(self):
        """Deploy guest with root vdev."""
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

        self.sdkapi.guest_create(self.userid, 1, 1024, disk_list=disks)
        self.sdkapi.guest_deploy(self.userid,
                                 self.image_name,
                                 vdev=new_root)
        self.sdkapi.guest_start(self.userid)
        powered_on = self.test_util.wait_until_guest_in_power_state(
                                                        self.userid, 'on')
        self.assertTrue(powered_on)

    def test_get_info(self):
        """Test guest_get_info in active/inactive/paused state."""
        self.addCleanup(self.sdkapi.guest_delete, self.userid)

        self.sdkapi.guest_create(self.userid, 1, 1024, disk_list=self.disks)
        self.sdkapi.guest_deploy(self.userid, self.image_name)

        # get info in shutdown state
        info_off = self.sdkapi.guest_get_info(self.userid)
        self.assertEquals(info_off['power_state'], 'off')
        self.assertEquals(info_off['mem_kb'], 0)
        self.assertEquals(info_off['cpu_time_us'], 0)

        # get info in active state
        self.sdkapi.guest_start(self.userid)
        self.assertTrue(self.sdkutils.wait_until_guest_in_power_state(
                                                        self.userid, 'on'))
        time.sleep(1)
        info_on = self.sdkapi.guest_get_info(self.userid)
        self.assertEquals(info_on['power_state'], 'on')
        self.assertNotEqual(info_on['cpu_time_us'], 0)
        self.assertNotEqual(info_on['mem_kb'], 0)

        # get info in paused state
        self.sdkapi.guest_pause(self.userid)
        info_on = self.sdkapi.guest_get_info(self.userid)
        self.assertEquals(info_on['power_state'], 'on')
        self.assertNotEqual(info_on['cpu_time_us'], 0)
        self.assertNotEqual(info_on['mem_kb'], 0)

    def test_guest_list(self):
        pass

    def test_get_definition_info(self):
        pass

    def test_create_disks(self):
        pass

    def test_delete_disks(self):
        pass

    def test_get_console_output(self):
        pass

    def test_config_minidisks(self):
        pass


class SDKGuestScenarioTestcase(base.SDKAPIGuestBaseTestCase):

    def test_guest_power_actions(self):
        # make sure the guest is off
        self.sdkapi.guest_stop(self.userid)
        self.assertTrue(self.sdkutils.wait_until_guest_in_power_state(
                    self.userid, 'off'), 'Power off %s failed' % self.userid)

        # power on the guest
        self.sdkapi.guest_start(self.userid)
        self.assertTrue(self.sdkutils.wait_until_guest_in_power_state(
                    self.userid, 'on'), 'Power on %s failed' % self.userid)

        # pause the guest
        self.sdkapi.guest_pause(self.userid)

        # unpause the guest
        self.sdkapi.guest_unpause(self.userid)

        self.assertTrue(self.sdkutils.wait_until_guest_in_connection_state(
                                                            self.userid, True))

        # reboot the vm
        self.sdkapi.guest_reboot(self.userid)
        self.assertTrue(self.sdkutils.wait_until_guest_in_connection_state(
                                                        self.userid, False))
        self.assertTrue(self.sdkutils.wait_until_guest_in_connection_state(
                                                            self.userid, True))

        # reset the vm
        self.sdkapi.guest_reset(self.userid)
        self.assertTrue(self.sdkutils.wait_until_guest_in_connection_state(
                                                        self.userid, False))
        self.assertTrue(self.sdkutils.wait_until_guest_in_connection_state(
                                                            self.userid, True))
