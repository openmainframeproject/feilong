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
from zvmsdk import config
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self._zvmclient = zvmclient.get_zvmclient()

    def test_get_zvmclient(self):
        _client = zvmclient.get_zvmclient()
        if CONF.zvm.client_type == 'smut':
            self.assertTrue(isinstance(_client,
                                       smutclient.SMUTClient))

    def test_generate_vdev(self):
        base = '0100'
        idx = 1
        vdev = self._zvmclient._generate_vdev(base, idx)
        self.assertEqual(vdev, '0101')

    @mock.patch.object(zvmclient.get_zvmclient(), '_add_mdisk')
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

    @mock.patch.object(zvmclient.get_zvmclient(), '_remove_mdisk')
    def test_remove_mdisks(self, remove_mdisk):
        userid = 'fakeuser'
        vdev_list = ['102', '103']
        self._zvmclient.remove_mdisks(userid, vdev_list)
        remove_mdisk.assert_any_call(userid, vdev_list[0])
        remove_mdisk.assert_any_call(userid, vdev_list[1])

    @mock.patch.object(zvmclient.get_zvmclient(), 'image_performance_query')
    def test_get_image_performance_info(self, ipq):
        ipq.return_value = {
            u'FAKEVM': {
                'used_memory': u'5222192 KB',
                'used_cpu_time': u'25640530229 uS',
                'guest_cpus': u'2',
                'userid': u'FKAEVM',
                'max_memory': u'8388608 KB'}}
        info = self._zvmclient.get_image_performance_info('fakevm')
        self.assertEqual(info['used_memory'], '5222192 KB')

    @mock.patch.object(zvmclient.get_zvmclient(), 'image_performance_query')
    def test_get_image_performance_info_not_exist(self, ipq):
        ipq.return_value = {}
        info = self._zvmclient.get_image_performance_info('fakevm')
        self.assertEqual(info, None)

    def test_is_vdev_valid_true(self):
        vdev = '1009'
        vdev_info = ['1003', '1006']
        result = self._zvmclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, True)

    def test_is_vdev_valid_False(self):
        vdev = '2002'
        vdev_info = ['2000', '2004']
        result = self._zvmclient._is_vdev_valid(vdev, vdev_info)
        self.assertEqual(result, False)
