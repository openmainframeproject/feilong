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
import random
import unittest
import uuid

from zvmsdk import api
from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import configdrive
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
        self.zvmclient = zvmclient.get_zvmclient()

    def image_import(self, image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version):
        image_url = ''.join(('file://', image_path))
        remote_host = zvmutils.get_host()
        self.api.image_import(image_url, {'os_version': os_version},
                              remote_host)

    def get_available_test_userid(self):
        exist_list = self.api.host_list_guests()
        test_list = CONF.tests.userid_list.split(' ')
        for uid in test_list:
            if uid in exist_list:
                try:
                    self.api.guest_delete(uid)
                except exception.SDKBaseException as e:
                    print("WARNING: Delete guest failed: %s" %
                          e.format_message())
                continue
            else:
                return uid

    def get_available_ip_addr(self):
        ip_list = CONF.tests.ip_addr_list.split(' ')
        vs_info = str(self.zvmclient.virtual_network_vswitch_query_iuo_stats())
        for ip in ip_list:
            if ip not in vs_info:
                return ip

    def generate_mac_addr(self):
        tmp_list = []
        for i in (1, 2, 3):
            tmp_list.append(''.join(random.sample("0123456789abcdef", 2)))

        mac_suffix = ':'.join(tmp_list)
        mac_addr = ':'.join((CONF.tests.mac_user_prefix, mac_suffix))
        return mac_addr

    def guest_deploy(self, userid=None, cpu=1, memory=1024,
                     image_path=CONF.tests.image_path, ip_addr=None,
                     root_disk_size='3g', login_password='password'):
        image_name = os.path.basename(image_path)
        image_name_xcat = '-'.join((CONF.tests.image_os_version,
                                's390x-netboot', image_name.replace('-', '_')))
        if not self.api.image_query(image_name.replace('-', '_')):
            print("Importing image %s ...\n" % image_name)
            self.image_import()

        print("Using image %s ...\n" % image_name)

        if userid is None:
            userid = self.get_available_test_userid()
        print("Using userid %s ...\n" % userid)

        user_profile = CONF.zvm.user_profile
        nic_id = str(uuid.uuid1())

        if ip_addr is None:
            ip_addr = self.get_available_ip_addr()

        print("Using IP address of %s ...\n" % ip_addr)

        mac_addr = self.generate_mac_addr()
        print("Using MAC address of %s ...\n" % mac_addr)

        nic_info = {'nic_id': nic_id, 'mac_addr': mac_addr}
        vdev = CONF.zvm.default_nic_vdev
        vswitch_name = CONF.tests.vswitch
        remote_host = zvmutils.get_host()
        transportfiles = configdrive.create_config_drive(ip_addr,
                                                CONF.tests.image_os_version)
        disks_list = [{'size': root_disk_size,
                       'is_boot_disk': True,
                       'disk_pool': CONF.zvm.disk_pool}]

        # Create vm in zVM
        print("Creating userid %s ...\n" % userid)
        self.api.guest_create(userid, cpu, memory, disks_list, user_profile)

        # Setup network for vm
        print("Creating nic %s ...\n" % str(nic_info))
        self.api.guest_create_nic(userid, [nic_info], ip_addr)
        self.api.guest_update_nic_definition(userid, vdev, mac_addr,
                                             vswitch_name)
        self.api.vswitch_grant_user(vswitch_name, userid)

        # Deploy image on vm
        print("Deploying userid %s ...\n" % userid)
        self.api.guest_deploy(userid, image_name_xcat, transportfiles,
                              remote_host)

        # Power on the vm, then put MN's public key into vm
        print("Power on userid %s ...\n" % userid)
        self.api.guest_start(userid)

        return userid, ip_addr

    def guest_destroy(self, userid):
        self.api.guest_delete(userid)


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
        self.userid = self.sdkutils.get_available_test_userid()
        try:
            self.sdkutils.guest_deploy(self.userid)
        finally:
            self.addCleanup(self.sdkutils.guest_destroy, self.userid)
