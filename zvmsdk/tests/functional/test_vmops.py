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


from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.tests.functional import base


CONF = config.CONF
LOG = log.LOG


class SDKGuestActionsTestCase(base.SDKAPIBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(SDKGuestActionsTestCase, self).__init__(methodName)
        # TODO: guest with customized profile

    def test_guest_create_normal(self):
        userid_small = "usmall"
        userid_big = "ubig"
        userid_with_disk = "udisk"

        userid = userid_small
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        LOG.info("test_guest_create: %s ... ok!" % self.userid_small)

        userid = userid_big
        vcpu = 8
        memory = 8192
        self.sdkapi.guest_create(userid, vcpu, memory)
        LOG.info("test_guest_create: %s ... ok!" % self.userid_big)

        userid = userid_with_disk
        vcpu = 2
        memory = 2048
        disk = [{'size': '1G',
                 'format': 'ext3',
                 'is_boot_disk': True,
                 'disk_pool': 'ECKD:xcateckd'},
                {'size': '200M',
                 'format': 'xfs',
                 'is_boot_disk': False,
                 'disk_pool': 'FBA:xcatfba1'}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk)
        LOG.info("test_guest_create: %s ... ok!" % self.userid_with_disk)

        self.sdkapi.guest_delete(userid_small)
        self.sdkapi.guest_delete(userid_big)
        self.sdkapi.guest_delete(userid_with_disk)
        # TODO: guest with customized profile

    def test_guest_create_abnormal(self):
        # Duplicate creation
        userid_duplicate = "udup"
        userid = userid_duplicate
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_create,
                          userid, vcpu, memory)

        self.sdkapi.guest_delete(userid_duplicate)
