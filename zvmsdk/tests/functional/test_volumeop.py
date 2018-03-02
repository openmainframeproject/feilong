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

import time

from zvmsdk.tests.functional import base
from zvmsdk import utils as zvmutils
from zvmsdk import config


CONF = config.CONF


class SDKVolumeOpTestCase(base.SDKAPIGuestBaseTestCase):

    def punch_auth_key(self, userid):
        """NOTICE:will reset instance!!"""
        if self.sdkapi.guest_get_power_state(self.userid) != 'on':
            time.sleep(10)
        # reset to solve network problem
        self.sdkapi.guest_reset(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'on':
            time.sleep(10)
        # punch key into instance
        zvmutils.punch_xcat_auth_file('', self.userid)
        # restart instance, do not use reset
        # resstart api has a bug,so use stop&start to replace it
        self.sdkapi.guest_stop(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'off':
            time.sleep(10)
        self.sdkapi.guest_start(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'on':
            time.sleep(10)

    def test_attach_volume_to_instance(self):
        # get volume info
        lun_id = CONF.tests.volume_lun_id
        fcps = CONF.tests.volume_fcps.split(' ')
        # prepare data for volume attach
        guest = {'name': self.userid, 'os_type': CONF.tests.image_os_version}
        volume = {'size': '1G', 'type': 'fc',
                  'lun': '00%s000000000000' % lun_id}
        wwpns = ['5005076801302797', '5005076801402797', '5005076801102797',
                 '5005076801202797', '5005076801102991', '5005076801202991',
                 '5005076801302991']
        connection_info = {'protocol': 'fc',
                           'fcps': fcps,
                           'dedicate': fcps,
                           'wwpns': wwpns,
                           'alias': '/dev/vda'}

        print "Start testing volume_attach..."
        # punch xcat auth file
        self.punch_auth_key(self.userid)
        # Start to attach volume,stop instance first
        self.sdkapi.guest_stop(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'off':
            time.sleep(10)
        # attach volume
        self.sdkapi.volume_attach(guest,
                                  volume,
                                  connection_info,
                                  False)
        self.sdkapi.guest_start(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'on':
            time.sleep(10)
        self.sdkapi.guest_reset(self.userid)
        # reset will clean key, so punch again
        self.punch_auth_key(self.userid)
        # check the attach result
        cmd_ls_dev = 'ls %s' % connection_info['alias']
        ret = {'data': [['No such file']]}
        ret = zvmutils.xdsh(self.userid, cmd_ls_dev)
        self.assertTrue('No such file' not in ret['data'][0][0])

    def test_detach_volume_from_instance(self):
        # get volume info
        lun_id = CONF.tests.volume_lun_id
        fcps = CONF.tests.volume_fcps.split(' ')
        # prepare data for volume attach
        guest = {'name': self.userid, 'os_type': CONF.tests.image_os_version}
        volume = {'size': '1G', 'type': 'fc',
                  'lun': '00%s000000000000' % lun_id}
        wwpns = ['5005076801302797', '5005076801402797', '5005076801102797',
                 '5005076801202797', '5005076801102991', '5005076801202991',
                 '5005076801302991']
        connection_info = {'protocol': 'fc',
                           'fcps': fcps,
                           'dedicate': fcps,
                           'wwpns': wwpns,
                           'alias': '/dev/vda'}

        print "Start testing volume_attach..."
        # punch xcat auth file
        self.punch_auth_key(self.userid)
        # Start to attach volume,stop instance first
        self.sdkapi.guest_stop(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'off':
            time.sleep(10)
        # detach volume
        self.sdkapi.volume_detach(guest,
                                  volume,
                                  connection_info,
                                  False)
        self.sdkapi.guest_start(self.userid)
        if self.sdkapi.guest_get_power_state(self.userid) != 'on':
            time.sleep(10)
        self.sdkapi.guest_reset(self.userid)
        # reset will clean key, so punch again
        self.punch_auth_key(self.userid)
        # check the attach result
        cmd_ls_dev = 'ls %s' % connection_info['alias']
        ret = {'data': [['No such file']]}
        ret = zvmutils.xdsh(self.userid, cmd_ls_dev)
        self.assertTrue('No such file' in ret['data'][0][0])
