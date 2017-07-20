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

    def test_guest_create_normal(self):
        self.USERID_GC_SMALL = "ugcsmall"
        self.addCleanup(self.sdkapi.guest_delete, self.USERID_GC_SMALL)
        self.USERID_GC_BIG = "ugcbig"
        self.addCleanup(self.sdkapi.guest_delete, self.USERID_GC_BIG)
        self.USERID_GC_DISK = "ugcdisk"
        self.addCleanup(self.sdkapi.guest_delete, self.USERID_GC_DISK)

        userid = self.USERID_GC_SMALL
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        LOG.info("test_guest_create: %s ... ok!" % self.USERID_GC_SMALL)

        userid = self.USERID_GC_BIG
        vcpu = 8
        memory = 8192
        self.sdkapi.guest_create(userid, vcpu, memory)
        LOG.info("test_guest_create: %s ... ok!" % self.USERID_GC_BIG)

        userid = self.USERID_GC_DISK
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
        LOG.info("test_guest_create: %s ... ok!" % self.USERID_GC_DISK)

        # TODO: guest with customized profile

    def test_guest_create_abnormal(self):
        self.USERID_GC_DUPLICATE = "ugcdup"
        self.addCleanup(self.sdkapi.guest_delete, self.USERID_GC_DUPLICATE)

        # Duplicate creation
        userid = self.USERID_GC_DUPLICATE
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_create,
                          userid, vcpu, memory)
