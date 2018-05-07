# Copyright 2017,2018 IBM Corp.
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
#    under the License.


import json
import os
import time
import unittest

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import base
from zvmsdk.tests.sdkwsgi import test_utils
from zvmsdk import config
from zvmsdk import smutclient


CONF = config.CONF


class GuestHandlerTestCase(base.ZVMConnectorBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(GuestHandlerTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        # test change bind_port
        base.set_conf('sdkserver', 'bind_port', 3000)

        self.client = test_utils.TestzCCClient()
        self._smutclient = smutclient.get_smutclient()
        self.utils = test_utils.ZVMConnectorTestUtils()

        # Generate random userid foreach run
        self.userid = self.utils.generate_test_userid()

    @classmethod
    def setUpClass(cls):
        super(GuestHandlerTestCase, cls).setUpClass()
        cls.userid_exists = cls.utils.deploy_guest()[0]

    @classmethod
    def tearDownClass(cls):
        super(GuestHandlerTestCase, cls).tearDownClass()
        cls.client.vswitch_delete('restvsw1')
        cls.client.guest_delete(cls.userid_exists)

    def setUp(self):
        super(GuestHandlerTestCase, self).setUp()
        self.record_logfile_position()

    def _check_CPU_MEM(self, userid, cpu_cnt = None,
                       cpu_cnt_live = None,
                       maxcpu=CONF.zvm.user_default_max_cpu,
                       maxmem=CONF.zvm.user_default_max_memory):
        resp_info = self._guest_get(userid=userid)
        self.assertEqual(200, resp_info.status_code)

        Statement = "USER %s LBYONLY" % userid.upper()
        resp_content = json.loads(resp_info.content)
        user_direct = resp_content['output']['user_direct']
        cpu_num = 0
        cpu_num_live = 0
        cpu_num_online = 0
        for ent in user_direct:
            if ent.startswith(Statement):
                max_memory = ent.split()[4].strip()
            if ent.startswith("CPU"):
                cpu_num = cpu_num + 1
            if ent.startswith("MACHINE ESA"):
                max_cpus = int(ent.split()[2].strip())
        if cpu_cnt_live is not None:
            active_cpus = self._smutclient.execute_cmd(userid, "lscpu -e")[1:]
            cpu_num_live = len(active_cpus)
            active_cpus = self._smutclient.execute_cmd(userid,
                                                       "lscpu --parse=ONLINE")
            for c in active_cpus:
                # check online CPU number
                if c.startswith("# "):
                    continue
                online_state = c.strip().upper()
                if online_state == "Y":
                    cpu_num_online = cpu_num_online + 1
        if cpu_cnt is not None:
            self.assertEqual(cpu_cnt, cpu_num)
        if cpu_cnt_live is not None:
            self.assertEqual(cpu_cnt_live, cpu_num_live)
            self.assertEqual(cpu_cnt_live, cpu_num_online)
        self.assertEqual(maxcpu, max_cpus)
        self.assertEqual(maxmem, max_memory)

    def _check_total_memory(self, userid,
                            maxmem=CONF.zvm.user_default_max_memory):
        result_list = self._smutclient.execute_cmd(userid,
                                                   'lsmem | grep Total')
        online_memory = offline_memory = 0

        for element in result_list:
            if "Total online memory" in element:
                online_memory = int(element.split()[4].strip())
                online_unit = element.split()[5].strip().upper()
                self.assertEqual("MB", online_unit)
            if "Total offline memory" in element:
                offline_memory = int(element.split()[3].strip())
                offline_unit = element.split()[4].strip().upper()
                self.assertEqual("MB", offline_unit)
        total_memory = online_memory + offline_memory
        maxMemMb = int(maxmem[:-1])
        maxMemSuffix = maxmem[-1].upper()
        if maxMemSuffix == 'G':
            maxMemMb = maxMemMb * 1024
        self.assertEqual(total_memory, maxMemMb)

    def _check_interface(self, userid, ip="192.168.95.123"):
        """ Check network interface.
        Returns a bool value to indicate whether the network interface is
        defined
        """
        result_list = self._smutclient.execute_cmd(userid, 'ifconfig')

        for element in result_list:
            if ip in element:
                return True
        return False

    def _guest_disks_create_single(self, userid):
        """Create 101 minidisk."""
        disk_list = [{"size": "1g", "format": "ext3",
                      "disk_pool": CONF.zvm.disk_pool}]
        return self.client.guest_create_disks(userid, disk_list)

    def _guest_disks_create_multiple(self, userid):
        """Create 101 102 minidisks."""
        disk_list = [{"size": "1g", "format": "ext3",
                      "disk_pool": CONF.zvm.disk_pool},
                     {"size": "1g", "format": "ext3",
                      "disk_pool": CONF.zvm.disk_pool}]
        return self.client.guest_create_disks(userid, disk_list)

    def _guest_config_minidisk_multiple(self, userid):
        """Configure minidisk 101, 102"""
        disk_info = {"disk_list": [{"vdev": "0101",
                                    "format": "ext3",
                                    "mntdir": "/mnt/0101"},
                                   {"vdev": "0102",
                                    "format": "ext3",
                                    "mntdir": "/mnt/0102"}]}

        return self.client.guest_config_minidisks(userid, disk_info)

    def _check_nic(self, vdev, userid, mac=None, vsw=None, devices=3,
                   osa=None):
        """ Check nic status.
        output: defined, osa_or_vswitch
                defined: a bool value to indicate whether the nic is defined
                in user entry.
                osa_or_vswitch: a string value to indicate the vswitch that
                the nic is attached to or the osa vdev as recorded in database.
        """
        userid = userid.upper()

        entries = []
        if osa is None:
            nic_entry = 'NICDEF %s TYPE QDIO' % vdev.upper()
            if vsw is not None:
                nic_entry += (" LAN SYSTEM %s") % vsw
            nic_entry += (" DEVICES %d") % devices
            if mac is not None:
                nic_entry += (" MACID %s") % mac
            entries = [nic_entry]
        else:
            osa = osa.upper()
            vdev = vdev.upper()
            osa1 = str(str(hex(int(osa, 16) + 1))[2:]).zfill(4).upper()
            osa2 = str(str(hex(int(osa, 16) + 2))[2:]).zfill(4).upper()
            vdev1 = str(hex(int(vdev, 16) + 1))[2:].upper()
            vdev2 = str(hex(int(vdev, 16) + 2))[2:].upper()
            entries = [("DEDICATE %s %s" % (vdev, osa)),
                       ("DEDICATE %s %s" % (vdev1, osa1)),
                       ("DEDICATE %s %s" % (vdev2, osa2))]

        definition = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, definition.status_code)

        # Check definition
        for entry in entries:
            if entry not in definition.content:
                return False, ""

        # Continue to check the nic info defined in vswitch table
        resp = self.client.guest_get_nic_info(userid)
        nics_info = json.loads(resp.content)['output']

        for nic in nics_info:
            if (nic['interface'] != vdev) or (nic['userid'] != userid):
                continue
            # nic coupled to vswitch
            if nic['switch'] is not None:
                return True, nic['switch']
            # dedicated osa
            if nic['comments'] is not None:
                return True, nic['comments'].split('=')[1].strip()
        # Defined in user entry, but not attached to vswitch or OSA
        return True, None

    def test_guest_get_not_exist(self):
        resp = self.client.guest_get_definition_info('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_incorrect(self):
        resp = self.client.guest_get_definition_info('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_info_not_exist(self):
        resp = self.client.guest_get_info('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_info_incorrect(self):
        resp = self.client.guest_get_info('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_power_state_not_exist(self):
        resp = self.client.guest_get_power_state('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_power_state_incorrect(self):
        resp = self.client.guest_get_power_state('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_start_not_exist(self):
        resp = self.client.guest_start('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_softstop_not_exist(self):
        resp = self.client.guest_softstop('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_stop_not_exist(self):
        resp = self.client.guest_stop('notexist')
        self.assertEqual(404, resp.status_code)

    def _make_transport_file(self):
        os.mkdir('openstack')
        os.mkdir('openstack/latest')
        transport_file = "openstack/latest/meta_data.json"
        transport_file1 = "openstack/latest/network_data.json"
        transport_file2 = "openstack/latest/vendor_data.json"
        transport_file3 = "openstack/latest/vendor_data2.json"
        with open(transport_file, 'w') as f:
            f.write('{"admin_pass": "sMcTNh8b65dM",\
                      "random_seed": "Q2UzyJ+6ITjY4STr/sSkDeoP4Wy\
                      Nz62TlTiwc09NbkOEnunHn8v15DHdGsiLOJw0skc\
                      lGC3ERWpl6WVdyqK7Y6RB9PmttJF2w9MV\
                      kSZGIdhuyPa2b+tlIRxHBQTrXGIGoEKWq6KY9t\
                      g0fY+GqmPOT/DnEB3Iz3AISdAk8dYsYG4KR\
                      xbQHsgshX1J56hMRwehhZ4EbdggD0lr3otnN\
                      ssteZYFGVnFq0CHE8gDfUZCsdPaVJrFmbe5Ae\
                      ElJzDCoPBF71e+FSpJtcxbBH18x6yhFbzC+lbj\
                      1A+KOf3+IaWP+kTr4oxoMV3Ho9w0woxi4cK\
                      zx6yBuzd+7TOr+8P+LJovQ93pPNJ/OWdaLNK\
                      d2mdcU85x7zSngotQwnhHau0eihQjvHTmFHpe\
                      LXEjfLNdmYFJMBAVfI6qlUgTNk+lRfRhXpA7CA\
                      b0C0r31r1ofzgYB4mM7i+rbK8GdY7wB2NoM\
                      jE9zMwTHHoq9zfhLissEIGf/6Rl2BTGa8BBU\
                      aWg5kf+C5zSK0ehxHX8FW0oRqWoSCEEucaB+S\
                      EAckXoDDLdm83maBaMi7Q67GbRkfA6D1+UOk5q\
                      WQey6z2/1jYWS8hmlByfelawEtJ674NWs84\
                      VT2kuLFuGByXS/ToJ23V2+I4cn2ihzf4B7IT\
                      c+4O3LrQu1GOY1+JyC146EW951tsW0bKWigM=",\
                      "uuid": "d93b1ef2-5ca7-459f-beaf-eedea6b6ee43",\
                      "availability_zone": "nova",\
                      "hostname": "deploy_tests",\
                      "launch_index": 0,\
                      "devices"    : [],\
                      "project_id": "6e3ab252b982424c859fa83ff281e8ab",\
                      "name": "transport_tests"}')
        with open(transport_file1, 'w') as f:
            f.write('{}')
        with open(transport_file2, 'w') as f:
            f.write('{}')
        with open(transport_file3, 'w') as f:
            f.write('{}')
        os.system('tar -czvf cfgdrive.tgz openstack')
        os.system('cp cfgdrive.tgz /var/lib/zvmsdk/cfgdrive.tgz')
        os.system('rm -rf openstack')
        os.system('rm cfgdrive.tgz')
        os.system('chown -R zvmsdk:zvmsdk /var/lib/zvmsdk/cfgdrive.tgz')
        os.system('chmod -R 755 /var/lib/zvmsdk/cfgdrive.tgz')

    def test_guest_deploy_userid_not_exist(self):
        resp = self.client.guest_deploy(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_deploy_vdev_not_exist(self):
        resp = self.client.guest_deploy(self.userid_exists, vdev='FFFF')
        self.assertEqual(404, resp.status_code)

    def test_guest_deploy_image_not_exist(self):
        resp = self.client.guest_deploy(self.userid_exists, image='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_capture_userid_not_exist(self):
        resp = self.client.guest_capture(userid='notexist', image_name='test1')
        self.assertEqual(404, resp.status_code)

    def test_guest_pause_not_exist(self):
        resp = self.client.guest_pause('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_unpause_not_exist(self):
        resp = self.client.guest_unpause('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_reboot_not_exist(self):
        resp = self.client.guest_reboot('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_reset_not_exist(self):
        resp = self.client.guest_reset('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_create_not_exist(self):
        resp = self.client.guest_create_nic(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_vif_create_not_exist(self):
        resp = self.client.guest_create_network_interface(userid='notexist',
                                                          os_version='rhel67')
        self.assertEqual(404, resp.status_code)

    def test_guest_vif_delete_not_exist(self):
        resp = self.client.guest_delete_network_interface(userid='notexist',
                                                          os_version='rhel67')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_query_not_exist(self):
        resp = self.client.guest_get_nic_info(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_delete_not_exist(self):
        resp = self.client.guest_delete_nic(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_delete_device_not_exist(self):
        resp = self.client.guest_delete_nic(self.userid_exists, vdev='FFFF')
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_create_not_exist(self):
        resp = self.client.guest_create_disks('notexist', [])
        self.assertEqual(404, resp.status_code)

    @unittest.skip("Skip until bug/1747591 fixed")
    def test_guest_disk_pool_create_not_exist(self):
        disk_list = [{"size": "1g", "format": "ext3",
                      "disk_pool": 'ECKD:notexist'}]
        resp = self.client.guest_create_disks(self.userid_exists, disk_list)
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_not_exist(self):
        resp = self.client.guest_delete_disks(userid='notexist', [])
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_device_not_exist(self):
        # disk not exist
        resp = self.client.guest_delete_disks(self.userid_exists, ["FFFF"])
        self.assertEqual(200, resp.status_code)

    def test_guest_inspect_not_exist(self):
        # following 200 is expected
        resp = self.client.guest_inspect_stats('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self.client.guest_inspect_vnics('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_inspect_incorrect(self):
        resp = self.client.guest_inspect_stats('@@@@@123456789')
        self.assertEqual(400, resp.status_code)

        resp = self.client.guest_inspect_vnics('@@@@@123456789')
        self.assertEqual(400, resp.status_code)

    def test_guest_creat_with_profile_notexit(self):
        userid = self.utils.generate_test_userid()
        resp = self.client.guest_create(userid, user_profile="notexist")
        self.assertEqual(404, resp.status_code)

    def _get_userid_auto_cleanup(self):
        userid = self.utils.generate_test_userid()
        self.addCleanup(self.client.guest_delete, userid)
        return userid

    def test_guest_create_maxcpu_incorrect(self):
        userid = self._get_userid_auto_cleanup()
        resp = self.client.guest_create(userid, max_cpu=0)
        self.assertEqual(400, resp.status_code)
        resp = self.client.guest_create(userid, max_cpu=65)
        self.assertEqual(400, resp.status_code)

    def test_guest_create_maxmem_incorrect(self):
        userid = self._get_userid_auto_cleanup()
        resp = self.client.guest_create(userid, max_mem="11111M")
        self.assertEqual(400, resp.status_code)
        resp = self.client.guest_create(userid, max_mem="1024K")
        self.assertEqual(400, resp.status_code)
        resp = self.client.guest_create(userid, max_mem="1024")
        self.assertEqual(400, resp.status_code)

    def test_guest_list(self):
        resp = self.client.guest_list()
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_list', resp.content)

    def test_guest_get_console_output(self):
        # power on
        self.client.guest_start(self.userid_exists)
        self.utils.wait_until_guest_in_power_state(self.userid_exists, "on")
        self.addCleanup(self.client.guest_stop, self.userid_exists)

        # get console output
        resp = self.client.guest_get_console_output(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        outputs = json.loads(resp.content)['output']
        self.assertNotEqual(outputs, '')

    def test_guest_power_actions(self):
        # make sure the guest in power off state
        self.client.guest_stop(self.userid_exists)
        self.utils.wait_until_guest_in_power_state(self.userid_exists, "off")

        # power on
        resp = self.client.guest_start(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_in_power_state(self.userid_exists, "on")
        self.assertTrue(self._wait_until(True, self.is_reachable, self.userid))

        # pause and unpause
        resp = self.client.guest_pause(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        resp = self.client.guest_unpause(self.userid_exists)
        self.assertEqual(200, resp.status_code)

        # reboot and reset
        resp = self.client.guest_reboot(self.userid_exists)
        self.assertTrue(self._wait_until(False, self.is_reachable,
                                         self.userid))
        self.assertTrue(self._wait_until(True, self.is_reachable,
                                         self.userid))
        self.assertEqual(200, resp.status_code)

        resp = self.client.guest_reset(self.userid_exists)
        self.assertTrue(self._wait_until(False, self.is_reachable,
                                         self.userid))
        self.assertTrue(self._wait_until(True, self.is_reachable,
                                         self.userid))
        self.assertEqual(200, resp.status_code)

        # power off
        resp = self.client.guest_softstop(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_in_power_state(self.userid_exists, "off")

    def test_guest_create_with_profile_multiple_disks(self):
        userid = self._get_userid_auto_cleanup()
        disk_list = [{"size": "3g", "is_boot_disk": True},
                     {"size": "1g"}]

        # create multi-disks guest with profile specified
        resp = self.client.guest_create(userid, disk_list=disk_list,
                                        user_profile=CONF.zvm.user_profile)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete, userid)

        # get guest definition
        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)

        # verify two disks added
        self.assertTrue('MDISK 0100' in resp.content)
        self.assertTrue('MDISK 0101' in resp.content)
        # verify included the profile
        self.assertTrue('INCLUDE %s' % CONF.zvm.user_profile in resp.content)

    def test_guest_create_delete(self):
        """Scenario BVT testcases."""
        userid = self._get_userid_auto_cleanup()
        vswitch_name = 'RESTVSW1'

        resp = self.client.guest_create(userid)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.utils.destroy_guest, userid)
        self.utils.wait_until_create_userid_complete(userid)

        self._make_transport_file()
        self.addCleanup(os.system, 'rm /var/lib/zvmsdk/cfgdrive.tgz')

        transport_file = '/var/lib/zvmsdk/cfgdrive.tgz'
        image_name = self.utils.get_image_name(CONF.test.image_path)

        resp = self.client.guest_deploy(userid, image_name=image_name,
                                        transportfiles=transport_file)
        self.assertEqual(200, resp.status_code)

        # Creating NIC, not active.
        resp = self.client.guest_create_nic(userid)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1000", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Creating another NIC with fixed vdev.
        resp = self.client.guest_create_nic(userid, vdev="1003")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1003", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Creating NIC with vdev conflict with defined NIC.
        resp = self.client.guest_create_nic(userid, vdev="1004")
        self.assertEqual(409, resp.status_code)

        # Creating NIC with nic_id.
        resp = self.client.guest_create_nic(userid, vdev="1004",
                                            nic_id='123456')
        self.assertEqual(200, resp.status_code)

        resp = self.client.guest_get_nic_info(userid, nic_id='123456')
        self.assertEqual(200, resp.status_code)
        nic_info = json.loads(resp.content)['output']
        self.assertEqual("1006", nic_info[0]["interface"])
        self.assertEqual("123456", nic_info[0]["port"])

        # Creating NIC with mac_addr
        resp = self.client.guest_create_nic(userid, vdev="1009",
                                            mac_addr='02:00:00:12:34:56')
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", mac='123456',
                                           userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Creating NIC to active guest when guest is in off status.
        resp = self.client.guest_create_nic(userid, vdev='1100',
                                            active=True)
        self.assertEqual(409, resp.status_code)

        # Deleting NIC to active guest when guest is in off status.
        resp = self.client.guest_delete_nic(userid, vdev="1009",
                                            active=True)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Deleting NIC
        resp = self.client.guest_delete_nic(userid, vdev="1009")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", userid=userid)
        self.assertFalse(nic_defined)

        # Deleting NIC not existed
        resp = self.client.guest_delete_nic(userid, vdev="1009")
        self.assertEqual(200, resp.status_code)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_reachable(userid)

        # Creating nic to the active guest
        resp = self.client.guest_create_nic(userid, vdev='1100',
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1100", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get', resp.content)

        resp = self.client.guest_get_info(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get_info', resp.content)

        resp = self.client.guest_get_power_state(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get_power_state',
                                   resp.content)

        resp = self.client.guest_inspect_vnics(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_interface_stats',
                                   resp.content)

        # Creating NIC
        resp = self.client.guest_create_nic(userid, vdev='2000',
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        self.client.vswitch_create(vswitch_name)
        self.addCleanup(self.client.vswitch_delete, vswitch_name)

        resp = self.client.guest_nic_couple_to_vswitch(userid, "2000",
                                               vswitch_name=vswitch_name)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", vsw="RESTVSW1",
                                           userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual("RESTVSW1", vsw)

        resp = self._vswitch_uncouple(userid=userid)
        resp = self.client.guest_nic_uncouple_from_vswitch(userid, "2000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", userid=userid)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        resp = self.client.guest_delete_nic(userid, vdev="2000",
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", userid=userid)
        self.assertFalse(nic_defined)

        resp = self.client.guest_stop(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self._wait_until(False, self.is_reachable,
                                         userid))

        resp = self.client.guest_inspect_stats(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_stats',
                                   resp.content)

        # Capture a powered off instance will lead to error
        resp = self.client.guest_capture(userid, 'failed')
        self.assertEqual(500, resp.status_code)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_reachable(userid)

        resp_info = self.client.guest_get_info(userid)
        self.assertEqual(200, resp_info.status_code)
        resp_content = json.loads(resp_info.content)
        info_off = resp_content['output']
        self.assertEqual('on', info_off['power_state'])
        self.assertNotEqual(info_off['cpu_time_us'], 0)
        self.assertNotEqual(info_off['mem_kb'], 0)

        resp = self.client.guest_capture(userid, 'failed',
                                         capture_type='alldisks')
        self.assertEqual(501, resp.status_code)

        image_name= 'test_capture_image1'
        resp = self.client.guest_capture(userid, image_name)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.image_delete, image_name)

        resp = self.client.image_query(image_name)
        self.assertEqual(200, resp.status_code)

        resp_state = self.client.guest_get_power_state(userid)
        self.assertEqual(200, resp_state.status_code)
        resp_content = json.loads(resp_state.content)
        self.assertEqual('off', resp_content['output'])

    def test_guest_create_exist(self):
        resp = self.client.guest_create(self.userid_exists)
        self.assertEqual(409, resp.status_code)

    def test_guest_create_disks_and_configure(self):
        flag1 = False
        flag2 = False

        # create new disks
        resp = self._guest_disks_create_multiple(self.userid_exists)
        self.assertEqual(200, resp.status_code)

        resp_create = self.client.guest_get_definition_info(self.userid_exists)
        self.assertEqual(200, resp_create.status_code)
        self.assertTrue('MDISK 0101' in resp_create.content)
        self.assertTrue('MDISK 0102' in resp_create.content)

        # config 'MDISK 0101'
        resp_config = self._guest_config_minidisk_multiple(self.userid_exists)
        self.assertEqual(200, resp_config.status_code)

        resp = self.client.guest_start(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_reachable(self.userid_exists)

        result = self._smutclient.execute_cmd(self.userid_exists, 'df -h')
        for element in result:
            if '/mnt/0101' in element:
                flag1 = True
            if '/mnt/0102' in element:
                flag2 = True
        self.assertEqual(True, flag1)
        self.assertEqual(True, flag2)

        # delete new disks
        resp = self.client.guest_delete_disks(self.userid_exists,
                                              ['101', '102'])
        self.assertEqual(200, resp.status_code)
        resp_delete = self.client.guest_get_definition_info(self.userid_exists)
        self.assertEqual(200, resp_delete.status_code)
        self.assertTrue('MDISK 0101' not in resp_delete.content)
        self.assertTrue('MDISK 0102' not in resp_delete.content)

    def _get_free_osa(self):
        osa_info = self._smutclient._query_OSA()
        if 'OSA' not in osa_info.keys():
            return None
        elif len(osa_info['OSA']['FREE']) == 0:
            return None
        else:
            for osa in osa_info['OSA']['FREE']:
                osa_1 = str(str(hex(int(osa, 16) + 1))[2:]).zfill(4).upper()
                osa_2 = str(str(hex(int(osa, 16) + 2))[2:]).zfill(4).upper()
                if (osa_1 in osa_info['OSA']['FREE']) and (
                    osa_2 in osa_info['OSA']['FREE']):
                    return osa
            return None

    def test_guest_create_delete_network_interface(self):

        # create two interfaces together
        ip_addr2 = self.utils.generate_test_ip()
        ip_addr3 = self.utils.generate_test_ip()
        if_list = [
            {'ip': ip_addr2, 'vdev': "3000", "cidr": CONF.tests.cidr},
            {'ip': ip_addr3, 'vdev': "4000", "cidr": CONF.tests.cidr}]
        resp = self.client.guest_create_network_interface(self.userid_exists,
                                                      guest_networks=if_list)
        self.assertEqual(200, resp.status_code)

        # Coupling NIC to the vswitch.
        resp = self.client.guest_nic_couple_to_vswitch(self.useri_exists,
                                                       "3000")
        self.assertEqual(200, resp.status_code)
        resp = self.client.guest_nic_couple_to_vswitch(self.useri_exists,
                                                       "4000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("3000", self.useri_exists,
                                           vsw=CONF.tests.vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw=CONF.tests.vswitch, vsw)
        nic_defined, vsw = self._check_nic("4000", self.useri_exists,
                                           vsw=CONF.tests.vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(vsw=CONF.tests.vswitch, vsw)

        # Start the guest and check results
        self.client.guest_start(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self._wait_until(True, self.is_reachable,
                                         self.userid_exists))

        for addr in (ip_addr1, ip_addr2, ip_addr3):
            ip_set = self._check_interface(self.userid_exists, ip=addr)
            self.assertTrue(ip_set)

        # Delete network interface
        resp = self.client.guest_delete_network_interface(self.userid_exists,
                                                      vdev="2000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(self.userid_exists, ip=ip_addr1)
        self.assertFalse(ip_set)

        resp = self.client.guest_delete_network_interface(self.userid_exists,
                                                      vdev="3000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(self.userid_exists, ip=ip_addr2)
        self.assertFalse(ip_set)

        resp = self.client.guest_delete_network_interface(self.userid_exists,
                                                      vdev="4000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(self.userid_exists, ip=ip_addr3)
        self.assertFalse(ip_set)

    def test_guest_create_network_interface_multiple(self):
        pass

    def test_guest_create_network_interface_recreate(self):
        pass

    def test_guest_create_network_interface_dedicate_osa(self):
        # create an interface to dedicate osa
        osa = self._get_free_osa()
        self.assertNotEqual(osa, None)

        ip_addr = self.utils.generate_test_ip()
        if_info = {"ip_addr": ip_addr,
                   "gateway_addr": CONF.tests.gateway_v4,
                   "cidr": CONF.tests.cidr,
                   "nic_vdev": "2000",
                   "osa_device": osa}

        resp = self.client.guest_create_network_interface(self.userid_exists,
                                                      guest_networks=[if_info])
        self.assertEqual(200, resp.status_code)

        nic_defined, nic_osa = self._check_nic("2000", self.userid_exists,
                                               osa=osa)
        self.assertTrue(nic_defined)
        self.assertEqual(nic_osa, osa)

        is_ip_set = self._check_interface(self.userid_exists, ip=ip_addr)
        self.assertTrue(is_ip_set)

    def test_guests_get_nic_info(self):
        resp = self._guest_get_nic_DB_info()
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self._guest_get_nic_DB_info(userid='test')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self._guest_get_nic_DB_info(nic_id='testnic')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self._guest_get_nic_DB_info(vswitch='vswitch')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self._guest_get_nic_DB_info(userid='test', nic_id='testnic')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self._guest_get_nic_DB_info(userid='test', nic_id='testnic',
                                           vswitch='vswitch')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

    def _vswitch_create(self, vswitch=None):
        if not vswitch:
            body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        else:
            content = {"vswitch": {"name": vswitch, "rdev": "FF10"}}
            body = json.dumps(content)
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        return resp

    def _vswitch_delete(self, vswitch="restvsw1"):
        url = '/vswitches/%s' % vswitch
        resp = self.client.api_request(url=url,
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

    def _vswitch_couple(self, vswitch=None, userid=None, vdev="2000",
                        active=False):
        if not vswitch:
            vswitch = "RESTVSW1"
        if active:
            content = {"info": {"couple": "True",
                                "vswitch": vswitch, "active": "True"}}
            body = json.dumps(content)
        else:
            content = {"info": {"couple": "True",
                                "vswitch": vswitch, "active": "False"}}
            body = json.dumps(content)
        if not userid:
            userid = self.userid

        url = '/guests/%s/nic/%s' % (userid, vdev)
        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        return resp

    def _vswitch_uncouple(self, userid=None, vdev="2000", active=False):
        if active:
            body = '{"info": {"couple": "False", "active": "True"}}'
        else:
            body = '{"info": {"couple": "False", "active": "False"}}'
        if not userid:
            userid = self.userid

        url = '/guests/%s/nic/%s' % (userid, vdev)
        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        return resp

    def test_guest_vswitch_couple_uncouple_not_exist(self):
        resp = self._vswitch_couple(userid="notexist")
        self.assertEqual(404, resp.status_code)

        # vswitch = "notexist"
        resp = self._vswitch_couple(vswitch="NOTEXIST")
        self.assertEqual(404, resp.status_code)

        resp = self._vswitch_uncouple(userid="notexist")
        self.assertEqual(404, resp.status_code)

    def test_guest_vswitch_couple_uncouple(self):
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid)
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy(userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_create()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_nic_create("1000", userid=userid)
            self.assertEqual(200, resp.status_code)
            # Check nic defined in user direct and not coupled to vswitch
            nic_defined, vsw = self._check_nic("1000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Coupling with active=True on an off-state VM
            # The action should fail and rollback the user direct
            resp = self._vswitch_couple(vdev="1000", active=True,
                                        userid=userid)
            self.assertEqual(409, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Coupling NIC to VSWITCH.
            resp = self._vswitch_couple(vdev="1000", userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Coupling NIC to VSWITCH second time, same vswitch, supported.
            resp = self._vswitch_couple(vdev="1000", userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Coupling NIC to VSWITCH, to different vswitch, not supported
            # Should still be coupled to original vswitch
            resp = self._vswitch_create(vswitch="RESTVSW2")
            self.assertEqual(200, resp.status_code)
            resp = self._vswitch_couple(vdev="1000", vswitch="RESTVSW2",
                                        userid=userid)
            self.assertEqual(409, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Uncoupling with active=True on an off-state VM.
            # The NIC shoule not uncoupled in user direct and switch table
            resp = self._vswitch_uncouple(vdev="1000", active=True,
                                          userid=userid)
            self.assertEqual(409, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Uncoupling NIC from VSWITCH the second time.
            resp = self._vswitch_uncouple(vdev="1000", userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Deleting NIC
            resp = self._guest_nic_delete(userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic('1000', userid=userid)
            self.assertFalse(nic_defined)

            # Deleting NIC not existed
            resp = self._guest_nic_delete(userid=userid)
            self.assertEqual(200, resp.status_code)

            # Activating the VM
            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            time.sleep(10)

            # Creating NIC with active=True
            resp = self._guest_nic_create(vdev="2000", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Bypass the following case due to Lineitem RN
            # (NICDEF Security COntrols)
            # Unauthorized to couple NIC in active mode.
            # resp = self._vswitch_couple(vdev="2000", active=True)
            # self.assertEqual(400, resp.status_code)
            # nic_defined, vsw = self._check_nic("2000")
            # self.assertTrue(nic_defined)
            # self.assertEqual(None, vsw)

            # Authorizing VM to couple to vswitch.
            body = '{"vswitch": {"grant_userid": "%s"}}' % self.userid
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(200, resp.status_code)

            # Coupling NIC to an unexisted vswitch.
            resp = self._vswitch_couple(vdev="2000", vswitch="VSWNONE",
                                        active=True, userid=userid)
            self.assertEqual(404, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)
            time.sleep(10)

            # Coupling NIC to VSWITCH.
            resp = self._vswitch_couple(vdev="2000", active=True,
                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Coupling NIC to VSWITCH second time, same vswitch, supported
            resp = self._vswitch_couple(vdev="2000", active=True,
                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Coupling NIC to VSWITCH, to different vswitch, not supported.
            # Should still be coupled to original vswitch
            resp = self._vswitch_couple(vdev="2000", vswitch="RESTVSW2",
                                        active=True, userid=userid)
            self.assertEqual(409, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            # Uncoupling NIC from VSWITCH.
            resp = self._vswitch_uncouple(vdev="2000", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Uncoupling NIC from VSWITCH the second time.
            resp = self._vswitch_uncouple(vdev="2000", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            resp = self._guest_nic_query(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_nic', resp.content)

            resp = self._guest_nic_delete(vdev="2000", userid=userid)
            self.assertEqual(200, resp.status_code)

        finally:
            self._guest_delete(userid=userid)
            self._vswitch_delete()
            self._vswitch_delete(vswitch="RESTVSW2")

    def test_guest_create_cpu_memory_default(self):
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid)
        self.assertEqual(200, resp.status_code)
        self._make_transport_file()
        transport_file = '/var/lib/zvmsdk/cfgdrive.tgz'

        try:
            resp = self._guest_deploy_with_transport_file(userid=userid,
                                           transportfiles=transport_file)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             userid))
            self._check_CPU_MEM(userid)
            self._check_total_memory(userid)
        finally:
            os.system('rm /var/lib/zvmsdk/cfgdrive.tgz')
            self._guest_delete(userid=userid)

    def test_guest_live_resize_cpus(self):
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid, maxcpu=10, maxmem="2048M")
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy(userid=userid)
            self.assertEqual(200, resp.status_code)

            # Live resize a guest's CPU when the guest is not active
            resp = self._guest_live_resize_cpus(2, userid=userid)
            self.assertEqual(409, resp.status_code)

            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             userid))
            self._check_CPU_MEM(userid, maxcpu=10, maxmem="2048M")
            self._check_total_memory(userid, maxmem="2048M")

            # Resized cpu number exceed the user's max cpu number
            resp = self._guest_resize_cpus(11, userid=userid)
            self.assertEqual(409, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu number exceed the allowed max cpu number
            resp = self._guest_resize_cpus(65, userid=userid)
            self.assertEqual(400, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu number is less than the allowed min cpu number
            resp = self._guest_resize_cpus(0, userid=userid)
            self.assertEqual(400, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu number exceed the user's max cpu number
            resp = self._guest_live_resize_cpus(11, userid=userid)
            self.assertEqual(409, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu number exceed the allowed max cpu number
            resp = self._guest_live_resize_cpus(65, userid=userid)
            self.assertEqual(400, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu number is less than the allowed min cpu number
            resp = self._guest_live_resize_cpus(0, userid=userid)
            self.assertEqual(400, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num equal to the current cpu num in user direct,
            # and equal to the live cpu num
            #  - cpu num in user direct: not change
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(1, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num equal to the user's max cpu num in user direct,
            #  - cpu num in user direct: increase
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(10, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=10, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num is less than the current cpu num in user direct
            #  - cpu num in user direct: decrease
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(3, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=1,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num equal to the current cpu num in user direct,
            # and is greater than the live cpu num
            #  - cpu num in user direct: not change
            #  - live cpu num: increased
            resp = self._guest_live_resize_cpus(3, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=3,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num equal to the current cpu num in user direct,
            # and equal to the live cpu num
            #  - cpu num in user direct: not change
            #  - live cpu num: not change
            resp = self._guest_live_resize_cpus(3, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=3,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num is greater than the current cpu num in user
            # direct, and is greater than the live cpu num
            #  - cpu num in user direct: increase
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(5, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=3,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is less than the current cpu num
            # in user direct, and is greater than the live cpu num
            #  - cpu num in user direct: decrease
            #  - live cpu num: increase
            resp = self._guest_live_resize_cpus(4, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=4,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is greater than the current cpu num
            # in user direct, and is greater than the live cpu num
            #  - cpu num in user direct: increase
            #  - live cpu num: increase
            resp = self._guest_live_resize_cpus(5, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num is greater than the current cpu num
            # in user direct, and is greater than the live cpu num
            #  - cpu num in user direct: increase
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(7, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num is less than the current cpu num
            # in user direct, and is less than the live cpu num
            #  - cpu num in user direct: decrease
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(4, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num equal to the current cpu num
            # in user direct, and is less than the live cpu num
            #  - cpu num in user direct: not change
            #  - live cpu num: not change
            resp = self._guest_live_resize_cpus(4, userid=userid)
            self.assertEqual(409, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is greater than the current cpu num
            # in user direct, and equal to the live cpu num
            #  - cpu num in user direct: increase
            #  - live cpu num: not change
            resp = self._guest_live_resize_cpus(5, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is greater than the user's max cpu
            # num in user direct
            #  - cpu num in user direct: not change
            #  - live cpu num: not change
            resp = self._guest_live_resize_cpus(11, userid=userid)
            self.assertEqual(409, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is less than the live cpu num
            #  - cpu num in user direct: not change
            #  - live cpu num: not change
            resp = self._guest_live_resize_cpus(4, userid=userid)
            self.assertEqual(409, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Resized cpu num is less than the current cpu num
            # in user direct, and is less than the live cpu num
            #  - cpu num in user direct: decrease
            #  - live cpu num: not change
            resp = self._guest_resize_cpus(4, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                                maxcpu=10, maxmem="2048M")

            # Restart guest, check cpu number
            resp = self._guest_stop(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             userid))
            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                            self.userid))
            self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=4,
                                maxcpu=10, maxmem="2048M")

            # Live resized cpu num is greater than the current cpu num
            # in user direct, and is greater than the live cpu num
            #  - cpu num in user direct: increase
            #  - live cpu num: increase
            resp = self._guest_live_resize_cpus(7, userid=userid)
            self.assertEqual(200, resp.status_code)
            self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=7,
                                maxcpu=10, maxmem="2048M")

            # Restart guest, check cpu number
            resp = self._guest_stop(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             userid))
            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                            self.userid))
            self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=7,
                                maxcpu=10, maxmem="2048M")

        finally:
            self._guest_delete(userid=userid)


class GuestActionTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(GuestActionTestCase, self).__init__(methodName)

    def setUp(self):
        super(GuestActionTestCase, self).setUp()
        self.client = test_utils.TestzCCClient()
        self.record_logfile_position()

    def test_guest_action_invalid_body(self):
        body = '{"dummy": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_guest_action_empty_body(self):
        body = '{}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_guest_action_invalid_method(self):
        body = '{"get_conole_output": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='PUT',
                                       body=body)
        self.assertEqual(405, resp.status_code)
