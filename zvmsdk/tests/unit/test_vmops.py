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
import zvmsdk.constants as const

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
    def test_power_on(self, power_state):
        self.vmops.power_on('cbi00063')
        power_state.assert_called_once_with('cbi00063', 'PUT', 'on')

    def test_validate_vm_id(self):
        fake_userid = 'fake_userid'

        msg = ("Don't support spawn vm on zVM hypervisor with name:%s,"
               "please make sure vm_id not longer than 8." % fake_userid)

        with self.assertRaises(exception.ZVMInvalidInput) as err:
            self.vmops.validate_vm_id(fake_userid)
        exc = err.exception
        self.assertEqual(exc.format_message(), msg)

        fake_userid = '12345678'
        ret = self.vmops.validate_vm_id(fake_userid)
        self.assertEqual(ret, True)

    @mock.patch('zvmsdk.imageops.ImageOps.get_root_disk_size')
    @mock.patch('zvmsdk.vmops.VMOps.set_ipl')
    @mock.patch('zvmsdk.vmops.VMOps.add_mdisk')
    @mock.patch.object(zvmutils, 'xcat_request')
    def test_create_userid(self, xrequest, add_mdisk, set_ipl, get_root_size):
        url = "/xcatws/vms/cbi00063?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password +\
                "&format=json"
        body = ['profile=%s' % const.ZVM_USER_PROFILE,
                'password=%s' % CONF.zvm.user_default_password,
                'cpu=1', 'memory=1024m',
                'privilege=G', 'ipl=0100',
                'imagename=test-image-name']
        get_root_size.return_value = CONF.zvm.root_disk_units
        self.vmops.create_userid('cbi00063', 1, 1024, 'test-image-name', 0, 0)
        xrequest.assert_called_once_with('POST', url, body)
        add_mdisk.assert_called_once_with('cbi00063', CONF.zvm.diskpool,
                                          CONF.zvm.user_root_vdev,
                                          CONF.zvm.root_disk_units)
        set_ipl.assert_called_once_with('cbi00063', CONF.zvm.user_root_vdev)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_vm(self, xrequest):
        url = "/xcatws/vms/cbi00038?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        self.vmops.delete_vm('cbi00038', 'zhcp2')

        xrequest.assert_called_once_with('DELETE', url)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_add_mdisk(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?" + \
                "userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        body_str = '--add3390 ' + CONF.zvm.diskpool + ' 0100 3338'
        body = []
        body.append(body_str)
        self.vmops.add_mdisk('cbi00063', CONF.zvm.diskpool,
                                          CONF.zvm.user_root_vdev,
                                          CONF.zvm.root_disk_units)
        xrequest.assert_called_once_with('PUT', url, body)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_set_ipl(self, xrequest):
        # TODO
        url = "/xcatws/vms/cbi00063?userName=" + CONF.xcat.username +\
                "&password=" + CONF.xcat.password + "&format=json"
        # TODO
        body = ['--setipl 0100']
        self.vmops.set_ipl('cbi00063', CONF.zvm.user_root_vdev)
        xrequest.assert_called_once_with('PUT', url, body)

    def test_create_vm(self):
        pass

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

    @mock.patch('zvmsdk.vmops.VMOps.get_user_direct')
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

    @mock.patch('zvmsdk.vmops.VMOps.get_user_direct')
    @mock.patch('zvmsdk.client.XCATClient.get_image_performance_info')
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_get_uid_failed(self, gps, gipi, gud):
        gps.return_value = 'off'
        gipi.return_value = None
        gud.side_effect = exception.ZVMVirtualMachineNotExist(userid='fakeid',
                                                        zvm_host='fakehost')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
                          self.vmops.get_info, 'fakeid')

    @mock.patch('zvmsdk.client.XCATClient.deploy_image_to_vm')
    def test_deploy_image_to_vm(self, deploy_image_to_vm):
        self.vmops.deploy_image_to_vm('fakevm', 'fakeimg',
                                      '/test/transport.tgz')
        deploy_image_to_vm.assert_called_with('fakevm', 'fakeimg',
                                              '/test/transport.tgz')
