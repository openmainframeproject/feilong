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


import mock


from zvmsdk import client as zvmclient
from zvmsdk import smutclient
from zvmsdk import xcatclient
from zvmsdk import config
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()

    def test_get_zvmclient(self):
        _client = zvmclient.get_zvmclient()
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(_client, xcatclient.XCATClient))
        elif CONF.zvm.client_type == 'smut':
            self.assertTrue(isinstance(_client,
                                       smutclient.SMUTClient))

    def test_generate_vdev(self):
        base = '0100'
        idx = 1
        vdev = self._zvmclient._generate_vdev(base, idx)
        self.assertEqual(vdev, '0101')

    @mock.patch.object(zvmclient.ZVMClient, '_add_mdisk')
    def test_add_mdisks(self, add_mdisk):
        userid = 'fakeuser'
        disk_list = [{'size': '1g',
                      'is_boot_disk': True,
                      'disk_pool': 'ECKD:eckdpool1'},
                     {'size': '200000',
                      'disk_pool': 'FBA:fbapool1',
                      'format': 'ext3'}]
        self._zvmclient.add_mdisks(userid, disk_list)
        add_mdisk.assert_any_call(userid, disk_list[0], '0100')
        add_mdisk.assert_any_call(userid, disk_list[1], '0101')
