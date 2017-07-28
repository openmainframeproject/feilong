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


import os.path

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
        image_path = CONF.tests.image_path
        image_os_version = CONF.tests.image_os_version
        self.image_name = self._get_image_name(image_path, image_os_version)

    def _get_image_name(self, image_path, image_os_version):
        image_file_name = os.path.basename(image_path)
        return "%(os)s-s390x-netboot-%(name)s" % {'os': image_os_version,
                                                  'name': image_file_name}

    def test_guest_create_normal(self):
        """ Normal cases of SDK API guest_create """
        userid_small = "ugcsmall"
        self.addCleanup(self.sdkapi.guest_delete, userid_small)
        userid_big = "ugcbig"
        self.addCleanup(self.sdkapi.guest_delete, userid_big)
        userid_disk = "ugcdisk"
        self.addCleanup(self.sdkapi.guest_delete, userid_disk)

        userid = userid_small
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        print("create guest %s ... ok!" % userid)

        userid = userid_big
        vcpu = 8
        memory = 8192
        self.sdkapi.guest_create(userid, vcpu, memory)
        print("create guest %s ... ok!" % userid)

        userid = userid_disk
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
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        print("create guest %s ... ok!" % userid)

        # TODO: guest with customized profile

    def test_guest_create_abnormal(self):
        """ Error cases of SDK API guest_create """
        userid_duplicate = "ugcdup"
        self.addCleanup(self.sdkapi.guest_delete, userid_duplicate)

        # Duplicate creation
        userid = userid_duplicate
        vcpu = 1
        memory = 512
        self.sdkapi.guest_create(userid, vcpu, memory)
        self.assertRaises(exception.ZVMException,
                          self.sdkapi.guest_create,
                          userid, vcpu, memory)

    def test_guest_deploy_delete_normal(self):
        """ Normal cases of SDK API guest_deploy and guest_delete """
        userid_normal = "ugdnorm"
        self.addCleanup(self.sdkapi.guest_delete, userid_normal)
        userid_trspt = "ugdtrspt"
        self.addCleanup(self.sdkapi.guest_delete, userid_trspt)
        userid_rmthost = 'ugdrhost'
        self.addCleanup(self.sdkapi.guest_delete, userid_rmthost)
        userid_vdev = 'ugdvdev'
        self.addCleanup(self.sdkapi.guest_delete, userid_vdev)

        # create temporary transport file for test
        transport_file = "/tmp/sdktest.txt"
        with open(transport_file, 'w') as f:
            f.write('A quick brown fox jump over the lazy dog.\n')
        self.addCleanup(os.remove, transport_file)

        # back up user_root_vdev value in config file
        def _restore_conf(root_vdev_back):
            CONF.zvm.user_root_vdev = root_vdev_back
        root_vdev_back = CONF.zvm.user_root_vdev
        self.addCleanup(_restore_conf, root_vdev_back)

        # simplest case
        userid = userid_normal
        vcpu = 1
        memory = 1024
        disk = [{'size': '3G',
                 'format': 'ext3',
                 'is_boot_disk': True,
                 'disk_pool': CONF.zvm.disk_pool}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid, self.image_name)
        print("deploy guest %s ... ok!") % userid
        # TOOD test guest delete

        # with transport file
        userid = userid_trspt
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid, self.image_name, transport_file)
        print("deploy guest %s ... ok!") % userid
        # TOOD test guest delete

        # with remote host
        userid = userid_rmthost
        remote_host = 'nova@127.0.0.1'
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid,
                                 self.image_name,
                                 transportfiles=transport_file,
                                 remotehost=remote_host)
        print("deploy guest %s ... ok!") % userid
        # TOOD test guest delete

        # specified root device
        userid = userid_vdev
        new_root = '123'
        CONF.zvm.user_root_vdev = new_root
        disk = [{'size': '3G',
                 'format': 'xfs',
                 'is_boot_disk': True,
                 'disk_pool': CONF.zvm.disk_pool},
                {'size': '200M',
                 'format': 'ext3',
                 'is_boot_disk': False,
                 'disk_pool': 'ECKD:xcateckd'}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        _restore_conf(root_vdev_back)
        self.sdkapi.guest_deploy(userid, self.image_name, vdev=new_root)
        print("deploy guest %s ... ok!") % userid
        # TOOD test guest delete

    def test_guest_deploy_delete_abnormal(self):
        """ Error cases of SDK API guest_deploy and guest_delete """
        userid_duplicate = "ugddup"
        self.addCleanup(self.sdkapi.guest_delete, userid_duplicate)

        userid = userid_duplicate
        vcpu = 1
        memory = 1024
        disk = [{'size': '3G',
                 'format': 'ext3',
                 'is_boot_disk': True,
                 'disk_pool': CONF.zvm.disk_pool}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid, self.image_name)
        # It's valid to deploy a same guest multiple times, each time it makes
        # the guest be reset by the image
        self.sdkapi.guest_deploy(userid, self.image_name)
        # TODO test guest delete

    def test_guest_start_stop_normal(self):
        """ Normal cases of SDK API guest_start and guest_stop """
        userid_normal = "ugsnml"
        self.addCleanup(self.sdkapi.guest_delete, userid_normal)

        userid = userid_normal
        vcpu = 1
        memory = 1024
        disk = [{'size': '3G',
                 'format': 'ext3',
                 'is_boot_disk': True,
                 'disk_pool': CONF.zvm.disk_pool}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid, self.image_name)
        self.sdkapi.guest_stop(userid)
        print("stop guest %s ... ok!" % userid)

        self.sdkapi.guest_start(userid)
        print("start guest %s ... ok!" % userid)

        self.sdkapi.guest_stop(userid, timeout=60, retry_interval=10)
        print("stop guest %s ... within 60 seconds and "
              "retry every 10 seconds ok!" % userid)

    def test_guest_start_stop_abnormal(self):
        """ Abnormal cases of SDK API guest_start and guest_stop """
        userid_abnormal = "ugsabnml"
        self.addCleanup(self.sdkapi.guest_delete, userid_abnormal)

        userid = userid_abnormal
        vcpu = 1
        memory = 1024
        disk = [{'size': '3G',
                 'format': 'ext3',
                 'is_boot_disk': True,
                 'disk_pool': CONF.zvm.disk_pool}]
        self.sdkapi.guest_create(userid, vcpu, memory, disk_list=disk)
        self.sdkapi.guest_deploy(userid, self.image_name)

        self.sdkapi.guest_stop(userid)
        # Stop again
        self.sdkapi.guest_stop(userid)
        print("stop guest %s ... ok!" % userid)

        self.sdkapi.guest_start(userid)
        # Start again
        self.sdkapi.guest_start(userid)
        print("start guest %s ... ok!" % userid)
