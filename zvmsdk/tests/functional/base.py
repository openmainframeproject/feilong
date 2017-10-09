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
import re
import unittest

from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKAPITestUtils(object):

    def __init__(self):
        self.api = api.SDKAPI()

    def image_import(self, image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version):

        image_name = os.path.basename(image_path)
        image_url = ''.join(('file://', image_path))
        self.api.image_import(image_name, image_url,
                              {'os_version': os_version})

    def _guest_exist(self, userid):
        cmd = 'vmcp q %s' % userid
        rc, output = zvmutils.execute(cmd)
        if re.search('(^HCP\w\w\w003E)', output):
            # userid not exist
            return False
        return True

    def get_available_userid_ipaddr(self):
        userid_list = CONF.tests.userid_list.split(' ')
        ip_list = CONF.tests.ip_addr_list.split(' ')
        for uid in userid_list:
            if self._guest_exist(uid):
                try:
                    self.api.guest_delete(uid)
                except exception.SDKBaseException as e:
                    print("WARNING: Delete guest failed: %s" %
                          e.format_message())
                continue
            else:
                idx = userid_list.index(uid)
                return uid, ip_list[idx]

    def _get_next_userid_ipaddr(self, userid):
        userids = CONF.tests.userid_list.split(' ')
        ip_list = CONF.tests.ip_addr_list.split(' ')
        idx = userids.index(userid)
        if (idx + 1) == len(userids):
            # the userid is the last one in userids, return the first one
            return userids[0], ip_list[0]
        else:
            return userids[idx + 1], ip_list[idx + 1]

    def guest_deploy(self, userid=None, cpu=1, memory=1024,
                     image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version,
                     ip_addr=None):
        image_name = os.path.basename(image_path)
        url = 'file://' + image_path

        print("Checking if image %s exists or not, import it if not exists" %
              image_name)
        image_info = self.api.image_query(image_name)
        print("Image query result is %s" % str(image_info))

        if not image_info:
            print("Importing image %s ..." % image_name)
            self.api.image_import(image_name, url,
                        {'os_version': os_version})

        print("Using image %s ..." % image_name)

        ipaddr = '0.4.0.4'
        if userid is None:
            userid, ipaddr = self.get_available_userid_ipaddr()
        ip_addr = ip_addr or ipaddr
        print("Using userid %s and IP addr %s ..." % (userid, ip_addr))

        user_profile = CONF.zvm.user_profile

        size = self.api.image_get_root_disk_size(image_name)
        print("root disk size is %s" % size)
        disks_list = [{'size': size,
                       'is_boot_disk': True,
                       'disk_pool': CONF.zvm.disk_pool}]

        # Create vm in zVM
        print("Creating userid %s ..." % userid)
        try:
            self.api.guest_create(userid, cpu, memory, disks_list,
                                  user_profile)
        except exception.ZVMException as err:
            errmsg = err.format_message()
            print("WARNING: create userid failed: %s" % errmsg)
            if (errmsg.__contains__("Return Code: 400") and
                    errmsg.__contains__("Reason Code: 8")):
                # delete userid not completed
                print("userid %s still exist" % userid)
                # switch to new userid
                userid, ip_addr = self._get_next_userid_ipaddr(userid)
                print("turn to use new userid %s and IP addr 5s" %
                      (userid, ip_addr))
                self.api.guest_create(userid, cpu, memory, disks_list,
                                      user_profile)

        # Create nic and configure it
        guest_networks = [{
            'ip_addr': ip_addr,
            'gateway_addr': CONF.tests.gateway_v4,
            'cidr': CONF.tests.cidr,
        }]
        netinfo = self.api.guest_create_network_interface(userid, os_version,
                                                          guest_networks)
        nic_vdev = netinfo[0]['nic_vdev']
        self.api.guest_nic_couple_to_vswitch(userid, nic_vdev,
                                             CONF.tests.vswitch)
        self.api.vswitch_grant_user(CONF.tests.vswitch, userid)

        # Grant IUCV access
        smut_uid = zvmutils.get_smut_userid()
        self.api.guest_authorize_iucv_client(userid, smut_uid)

        # Deploy image on vm
        print("Deploying userid %s ..." % userid)
        self.api.guest_deploy(userid, image_name)

        # Power on the vm, then put MN's public key into vm
        print("Power on userid %s ..." % userid)
        self.api.guest_start(userid)

        return userid, ip_addr

    def guest_destroy(self, userid):
        print("Deleting userid %s ..." % userid)
        try:
            self.api.guest_delete(userid)
        except exception.SDKBaseException as err:
            print("WARNING: deleting userid failed: %s" % err.format_message())


class SDKAPIBaseTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPIBaseTestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()
        self.sdkutils = SDKAPITestUtils()

    def set_conf(self, section, opt, value):
        old_value = CONF[section][opt]
        CONF[section][opt] = value
        self.addCleanup(set_conf, section, opt, old_value)


class SDKAPIGuestBaseTestCase(SDKAPIBaseTestCase):
    """Base test class for testcases that require a deployed vm."""

    def __init__(self, methodName='runTest'):
        super(SDKAPIGuestBaseTestCase, self).__init__(methodName)
        self.sdkapi = api.SDKAPI()

    def setUp(self):
        super(SDKAPIGuestBaseTestCase, self).setUp()

        # create test server
        self.userid, ip_addr = self.sdkutils.get_available_userid_ipaddr()
        try:
            userid, ip_addr = self.sdkutils.guest_deploy(self.userid)
            self.userid = userid
        finally:
            self.addCleanup(self.sdkutils.guest_destroy, self.userid)
