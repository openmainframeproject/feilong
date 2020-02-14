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

from zvmsdk import exception
from zvmsdk import vmops
from zvmsdk.tests.unit import base


class SDKVMOpsTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKVMOpsTestCase, self).setUp()
        self.vmops = vmops.get_vmops()

    @mock.patch("zvmsdk.smtclient.SMTClient.get_power_state")
    def test_get_power_state(self, gps):
        gps.return_value = 'on'
        self.vmops.get_power_state('cbi00063')
        gps.assert_called_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.get_guest_connection_status")
    def test_is_reachable(self, ggcs):
        ggcs.return_value = True
        ret = self.vmops.is_reachable('cbi00063')
        self.assertEqual(ret, True)

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_start")
    def test_guest_start(self, guest_start):
        self.vmops.guest_start('cbi00063')
        guest_start.assert_called_once_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_pause")
    def test_guest_pause(self, guest_pause):
        self.vmops.guest_pause('cbi00063')
        guest_pause.assert_called_once_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_unpause")
    def test_guest_unpause(self, guest_unpause):
        self.vmops.guest_unpause('cbi00063')
        guest_unpause.assert_called_once_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.namelist_add")
    @mock.patch("zvmsdk.smtclient.SMTClient.create_vm")
    def test_create_vm(self, create_vm, namelistadd):
        userid = 'fakeuser'
        cpu = 2
        memory = '2g'
        disk_list = []
        user_profile = 'testprof'
        max_cpu = 10
        max_mem = '4G'
        vdevs = ['1234']
        loaddev = {'portname': '5678', 'lun': '0000000000000000'}
        self.vmops.create_vm(userid, cpu, memory, disk_list, user_profile,
                             max_cpu, max_mem, '', '', '', vdevs, loaddev)
        create_vm.assert_called_once_with(userid, cpu, memory, disk_list,
                                          user_profile, max_cpu, max_mem,
                                          '', '', '', vdevs, loaddev)
        namelistadd.assert_called_once_with('TSTNLIST', userid)

    @mock.patch("zvmsdk.smtclient.SMTClient.process_additional_minidisks")
    def test_guest_config_minidisks(self, process_additional_minidisks):
        userid = 'userid'
        disk_list = [{'vdev': '0101',
                      'format': 'ext3',
                      'mntdir': '/mnt/0101'}]
        self.vmops.guest_config_minidisks(userid, disk_list)
        process_additional_minidisks.assert_called_once_with(userid, disk_list)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_power_state")
    def test_is_powered_off(self, check_stat):
        check_stat.return_value = 'off'
        ret = self.vmops.is_powered_off('cbi00063')
        self.assertEqual(True, ret)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_image_performance_info")
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
        self.assertEqual(vm_info['cpu_time_us'], 6911844399)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_image_performance_info")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_error(self, gps, gipi):
        gps.return_value = 'on'
        gipi.side_effect = exception.ZVMVirtualMachineNotExist(
            zvm_host='fakehost', userid='fakeid')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
                          self.vmops.get_info, 'fakeid')

    @mock.patch("zvmsdk.smtclient.SMTClient.get_user_direct")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_image_performance_info")
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
        self.assertEqual(vm_info['cpu_time_us'], 0)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_user_direct")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_image_performance_info")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_get_info_get_uid_failed(self, gps, gipi, gud):
        gps.return_value = 'off'
        gipi.return_value = None
        gud.side_effect = exception.ZVMVirtualMachineNotExist(userid='fakeid',
                                                        zvm_host='fakehost')
        self.assertRaises(exception.ZVMVirtualMachineNotExist,
                          self.vmops.get_info, 'fakeid')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_deploy")
    def test_guest_deploy(self, deploy_image_to_vm):
        self.vmops.guest_deploy('fakevm', 'fakeimg',
                                '/test/transport.tgz')
        deploy_image_to_vm.assert_called_with('fakevm', 'fakeimg',
                                              '/test/transport.tgz', None,
                                              None)

    @mock.patch('zvmsdk.vmops.VMOps.set_hostname')
    @mock.patch("zvmsdk.database.ImageDbOperator.image_query_record")
    @mock.patch("zvmsdk.smtclient.SMTClient.guest_deploy")
    def test_guest_deploy_sethostname(self, deploy_image_to_vm, img_query,
                                      set_hostname):
        fake_hostname = 'fakehost'
        img_query.return_value = [{'imageosdistro': 'rhel6.7'}]
        self.vmops.guest_deploy('fakevm', 'fakeimg',
                                hostname=fake_hostname)
        deploy_image_to_vm.assert_called_with('fakevm', 'fakeimg', None, None,
                                              None)
        img_query.assert_called_once_with('fakeimg')
        set_hostname.assert_called_once_with('fakevm', fake_hostname,
                                             'rhel6.7')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_capture")
    def test_guest_capture(self, guest_capture):
        self.vmops.guest_capture('fakevm', 'fakeimg')
        guest_capture.assert_called_once_with('fakevm', 'fakeimg',
                                              capture_type = 'rootonly',
                                              compress_level = 6)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_user_direct")
    def test_get_definition_info(self, get_user_direct):
        get_user_direct.return_value = [
            'line1',
            'NICDEF 1000 TYPE QDIO LAN SYSTEM VSWITCH']

        self.vmops.get_definition_info("fake_user_id", nic_coupled='1000')
        get_user_direct.assert_called_with("fake_user_id")

    @mock.patch("zvmsdk.smtclient.SMTClient.namelist_remove")
    @mock.patch("zvmsdk.smtclient.SMTClient.delete_vm")
    def test_delete_vm(self, delete_vm, namelistremove):
        userid = 'userid'
        self.vmops.delete_vm(userid)
        delete_vm.assert_called_once_with(userid)
        namelistremove.assert_called_once_with('TSTNLIST', userid)

    @mock.patch("zvmsdk.smtclient.SMTClient.execute_cmd")
    def test_execute_cmd(self, execute_cmd):
        userid = 'userid'
        cmdStr = 'ls'
        self.vmops.execute_cmd(userid, cmdStr)
        execute_cmd.assert_called_once_with(userid, cmdStr)

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_stop")
    def test_guest_stop(self, gs):
        userid = 'userid'
        self.vmops.guest_stop(userid)
        gs.assert_called_once_with(userid)

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_stop")
    def test_guest_stop_with_timeout(self, gs):
        userid = 'userid'
        gs.return_value = u'off'
        self.vmops.guest_stop(userid, timeout=300, poll_interval=10)
        gs.assert_called_once_with(userid, timeout=300, poll_interval=10)

    @mock.patch("zvmsdk.smtclient.SMTClient.get_vm_list")
    def test_guest_list(self, get_vm_list):
        self.vmops.guest_list()
        get_vm_list.assert_called_once_with()

    @mock.patch("zvmsdk.smtclient.SMTClient.add_mdisks")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_user_direct")
    def test_create_disks(self, gud, amds):
        user_direct = ['USER TEST TEST',
                       'MDISK 100 3390',
                       'MDISK 101 3390']
        gud.return_value = user_direct

        self.vmops.create_disks('userid', [])
        gud.assert_called_once_with('userid')
        amds.assert_called_once_with('userid', [], '0102')

    @mock.patch("zvmsdk.smtclient.SMTClient.add_mdisks")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_user_direct")
    def test_create_disks_200(self, gud, amds):
        user_direct = ['USER TEST TEST',
                       'MDISK 100 3390',
                       'MDISK 200 3390']
        gud.return_value = user_direct
        self.vmops.create_disks('userid', [])

        gud.assert_called_once_with('userid')
        amds.assert_called_once_with('userid', [], '0201')

    @mock.patch("zvmsdk.smtclient.SMTClient.remove_mdisks")
    @mock.patch("zvmsdk.smtclient.SMTClient.get_power_state")
    def test_delete_disks(self, gps, rmd):
        gps.return_value = 'off'
        self.vmops.delete_disks('userid', ['101', '102'])
        rmd.assert_called_once_with('userid', ['101', '102'])

    @mock.patch("zvmsdk.smtclient.SMTClient.get_power_state")
    def test_delete_disks_active(self, gps):
        gps.return_value = 'on'
        self.assertRaises(exception.SDKFunctionNotImplementError,
                          self.vmops.delete_disks, 'userid', ['101', '102'])
        gps.assert_called_once_with('userid')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_reboot")
    def test_guest_reboot(self, guest_reboot):
        self.vmops.guest_reboot('cbi00063')
        guest_reboot.assert_called_once_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.guest_reset")
    def test_guest_reset(self, guest_reset):
        self.vmops.guest_reset('cbi00063')
        guest_reset.assert_called_once_with('cbi00063')

    @mock.patch("zvmsdk.smtclient.SMTClient.live_resize_cpus")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_resize_cpus(self, power_state, do_resize):
        userid = 'testuid'
        cpu_cnt = 3
        power_state.return_value = 'on'
        self.vmops.live_resize_cpus(userid, cpu_cnt)
        power_state.assert_called_once_with(userid)
        do_resize.assert_called_once_with(userid, cpu_cnt)

    @mock.patch("zvmsdk.smtclient.SMTClient.live_resize_cpus")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_resize_cpus_guest_inactive(self, power_state, do_resize):
        userid = 'testuid'
        cpu_cnt = 3
        power_state.return_value = 'off'
        self.assertRaises(exception.SDKConflictError,
                          self.vmops.live_resize_cpus, userid, cpu_cnt)
        power_state.assert_called_once_with(userid)
        do_resize.assert_not_called()

    @mock.patch("zvmsdk.smtclient.SMTClient.resize_cpus")
    def test_resize_cpus(self, do_resize):
        userid = 'testuid'
        cpu_cnt = 3
        self.vmops.resize_cpus(userid, cpu_cnt)
        do_resize.assert_called_once_with(userid, cpu_cnt)

    @mock.patch("zvmsdk.smtclient.SMTClient.live_resize_memory")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_resize_memory(self, power_state, do_resize):
        userid = 'testuid'
        size = '1g'
        power_state.return_value = 'on'
        self.vmops.live_resize_memory(userid, size)
        power_state.assert_called_once_with(userid)
        do_resize.assert_called_once_with(userid, size)

    @mock.patch("zvmsdk.smtclient.SMTClient.live_resize_memory")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_resize_memory_guest_inactive(self, power_state, do_resize):
        userid = 'testuid'
        size = '1g'
        power_state.return_value = 'off'
        self.assertRaises(exception.SDKConflictError,
                          self.vmops.live_resize_memory, userid, size)
        power_state.assert_called_once_with(userid)
        do_resize.assert_not_called()

    @mock.patch("zvmsdk.smtclient.SMTClient.resize_memory")
    def test_resize_memory(self, do_resize):
        userid = 'testuid'
        size = '1g'
        self.vmops.resize_memory(userid, size)
        do_resize.assert_called_once_with(userid, size)

    @mock.patch("zvmsdk.smtclient.SMTClient.live_migrate_move")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_migrate_vm(self, power_state, live_migrate_vm):
        userid = 'testuid'
        destination = 'testssi'
        parms = {}
        action = "move"
        power_state.return_value = 'on'
        self.vmops.live_migrate_vm(userid, destination, parms, action)
        power_state.assert_called_once_with(userid)
        live_migrate_vm.assert_called_once_with(userid, destination,
                                                    parms)

    @mock.patch("zvmsdk.smtclient.SMTClient.live_migrate_test")
    @mock.patch('zvmsdk.vmops.VMOps.get_power_state')
    def test_live_migrate_test(self, power_state, live_migrate_vm):
        userid = 'testuid'
        destination = 'testssi'
        parms = {}
        action = "test"
        power_state.return_value = 'on'
        self.vmops.live_migrate_vm(userid, destination, parms, action)
        power_state.assert_called_once_with(userid)
        live_migrate_vm.assert_called_once_with(userid, destination)
