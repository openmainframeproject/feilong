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
import zvmsdk.client as zvmclient
import zvmsdk.utils as zvmutils

from zvmsdk.config import CONF
from zvmsdk import exception
from zvmsdk import vmops
from zvmsdk.tests.unit import base


class SDKVMOpsTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKVMOpsTestCase, self).setUp()
        self.vmops = vmops.get_vmops()
        self.xcat_url = zvmutils.get_xcat_url()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_get_power_state(self, xrequest):
        url = "/xcatws/nodes/cbi00063/power?" + \
                "userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        body = ['stat']
        self.vmops.get_power_state('cbi00063')
        xrequest.assert_called_with('GET', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_is_reachable(self, xrequest):
        xrequest.return_value = {
                'info': [],
                'node': [[{u'data': [u'sshd'], u'name': [u'cbi00063']}]],
                'errorcode': [], 'data': [], 'error': []}
        ret = self.vmops.is_reachable('cbi00063')

        self.assertEqual(ret, True)

    @mock.patch.object(zvmclient.XCATClient, '_power_state')
    def test_guest_start(self, power_state):
        self.vmops.guest_start('cbi00063')
        power_state.assert_called_once_with('cbi00063', 'PUT', 'on')

    @mock.patch.object(zvmclient.XCATClient, 'create_vm')
    def test_create_vm(self, create_vm):
        userid = 'fakeuser'
        cpu = 2
        memory = '2g'
        disk_list = []
        user_profile = 'testprof'
        self.vmops.create_vm(userid, cpu, memory, disk_list, user_profile)
        create_vm.assert_called_once_with(userid, cpu, memory, disk_list,
                                          user_profile)

    @mock.patch('zvmsdk.client.XCATClient.generate_disk_vdev')
    @mock.patch('zvmsdk.client.XCATClient.process_eph_disk')
    def test_process_additional_disks(self, process_eph_disk,
                                      generate_disk_vdev):
        fake_eph_list = [{'size': 1, 'format': 'ext3'}]
        fake_instance = 'inst001'
        mount_dir = '/mnt/ephemeral/'
        generate_disk_vdev.return_value = '0111'
        self.vmops.process_additional_disks(fake_instance, fake_eph_list)
        process_eph_disk.assert_called_with(fake_instance, '0111', 'ext3',
                                            mount_dir + '0')

    @mock.patch('zvmsdk.client.XCATClient.get_power_state')
    def test_is_powered_off(self, check_stat):
        check_stat.return_value = 'off'
        ret = self.vmops.is_powered_off('cbi00063')
        self.assertEqual(True, ret)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_capture_instance(self, xrequest):
        res = {
            'info': [
                [u'cbi00063: Capturing the image using zHCP node'],
                [u'cbi00063: creatediskimage start time'],
                [u'cbi00063: Moving the image files to the directory:xxxx'],
                [u'cbi00063: Completed capturing the image(test-image-name)']],
            'node': [],
            'errorcode': [],
            'data': [],
            'error': []}

        xrequest.return_value = res
        image_name = self.vmops.capture_instance('cbi00063')
        self.assertEqual(image_name, 'test-image-name')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_image(self, xrequest):
        url = "/xcatws/objects/osimage/test-image-name?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        self.vmops.delete_image('test-image-name')

        xrequest.assert_called_with('DELETE', url)

    @mock.patch('zvmsdk.client.XCATClient.get_image_performance_info')
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info(self, gps, gipi):
        gps.return_value = 'on'
        gipi.return_value = {'used_memory': u'4872872 KB',
                             'used_cpu_time': u'6911844399 uS',
                             'guest_cpus': u'2',
                             'userid': u'CMABVT',
                             'max_memory': u'8388608 KB'}
        vm_info = self.vmops.get_info('fakeid')
        gps.assert_called_once_with('fakeid')
        gipi.assert_called_once_with('fakeid')
        self.assertEqual(vm_info['power_state'], 'on')
        self.assertEqual(vm_info['max_mem_kb'], 8388608)
        self.assertEqual(vm_info['mem_kb'], 4872872)
        self.assertEqual(vm_info['num_cpu'], 2)
        self.assertEqual(vm_info['cpu_time_ns'], 6911844399000)

    @mock.patch('zvmsdk.client.XCATClient.get_image_performance_info')
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_error(self, gps, gipi):
        gps.return_value = 'on'
        gipi.side_effect = exception.ZVMVirtualMachineNotExist(
            zvm_host='fakehost', userid='fakeid')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
                          self.vmops.get_info, 'fakeid')

    @mock.patch('zvmsdk.client.XCATClient.get_user_direct')
    @mock.patch('zvmsdk.client.XCATClient.get_image_performance_info')
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_shutdown(self, gps, gipi, gud):
        gps.return_value = 'off'
        gipi.return_value = None
        gud.return_value = [
            u'USER FAKEUSER DFLTPASS 2048m 2048m G',
            u'INCLUDE PROFILE',
            u'CPU 00 BASE',
            u'CPU 01',
            u'IPL 0100',
            u'NICDEF 1000 TYPE QDIO LAN SYSTEM VSW2 MACID 0E4E8E',
            u'MDISK 0100 3390 34269 3338 OMB1A9 MR', u'']
        vm_info = self.vmops.get_info('fakeid')
        gps.assert_called_once_with('fakeid')
        gud.assert_called_once_with('fakeid')
        self.assertEqual(vm_info['power_state'], 'off')
        self.assertEqual(vm_info['max_mem_kb'], 2097152)
        self.assertEqual(vm_info['mem_kb'], 0)
        self.assertEqual(vm_info['num_cpu'], 2)
        self.assertEqual(vm_info['cpu_time_ns'], 0)

    @mock.patch('zvmsdk.client.XCATClient.get_user_direct')
    @mock.patch('zvmsdk.client.XCATClient.get_image_performance_info')
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_get_uid_failed(self, gps, gipi, gud):
        gps.return_value = 'off'
        gipi.return_value = None
        gud.side_effect = exception.ZVMVirtualMachineNotExist(userid='fakeid',
                                                        zvm_host='fakehost')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
                          self.vmops.get_info, 'fakeid')

    @mock.patch('zvmsdk.client.XCATClient.guest_deploy')
    def test_guest_deploy(self, deploy_image_to_vm):
        self.vmops.guest_deploy('fakevm', 'fakeimg',
                                '/test/transport.tgz')
        deploy_image_to_vm.assert_called_with('fakevm', 'fakeimg',
                                              '/test/transport.tgz', None)

    @mock.patch.object(zvmclient.XCATClient, 'get_user_direct')
    def test_get_definition_info(self, get_user_direct):
        get_user_direct.return_value = [
            'line1',
            'NICDEF 1000 TYPE QDIO LAN SYSTEM VSWITCH']

        self.vmops.get_definition_info("fake_user_id", nic_coupled='1000')
        get_user_direct.assert_called_with("fake_user_id")

    @mock.patch.object(zvmclient.XCATClient, 'delete_vm')
    def test_delete_vm(self, delete_vm):
        userid = 'userid'
        self.vmops.delete_vm(userid)
        delete_vm.assert_called_once_with(userid)

    @mock.patch.object(zvmclient.XCATClient, 'guest_stop')
    def test_guest_stop(self, gs):
        userid = 'userid'
        self.vmops.guest_stop(userid, 0, 10)
        gs.assert_called_once_with(userid)

    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(zvmclient.XCATClient, 'guest_stop')
    def test_guest_stop_with_retry(self, gs, gps):
        userid = 'userid'
        gps.return_value = u'off'
        self.vmops.guest_stop(userid, 60, 10)
        gs.assert_called_once_with(userid)
        gps.assert_called_once_with(userid)

    @mock.patch.object(zvmclient.XCATClient, 'get_power_state')
    @mock.patch.object(zvmclient.XCATClient, 'guest_stop')
    def test_guest_stop_timeout(self, gs, gps):
        userid = 'userid'
        gps.return_value = u'on'
        self.vmops.guest_stop(userid, 1, 1)
        gps.assert_called_once_with(userid)
