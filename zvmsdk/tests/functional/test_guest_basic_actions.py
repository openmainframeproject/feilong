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


from zvmsdk.tests.functional import base


class SDKGuestBasicActions(base.SDKAPIGuestBaseTestCase):

    def test_guest_basic_actions(self):
        userid_list = self.sdkapi.guest_list()
        self.assertTrue(self.userid in userid_list)

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
