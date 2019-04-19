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


import os
import subprocess
import tempfile
import time
import unittest


from parameterized import parameterized
from zvmsdk.tests.fvt import base
from zvmsdk.tests.fvt import test_utils
from zvmsdk import config
from zvmsdk import utils
from zvmsdk import database

CONF = config.CONF
TEST_IMAGE_LIST = test_utils.TEST_IMAGE_LIST
# This list contains tuple of (case_name, userid, version) where case_name is
# composed by image name and image distro, userid is used as userid to deploy
# guest with the corresponding image, version is the guest distro version.
TEST_USERID_LIST = []


def generate_test_userid_list():
    global TEST_USERID_LIST
    utils = test_utils.ZVMConnectorTestUtils()
    for i in range(0, len(TEST_IMAGE_LIST)):
        userid = utils.generate_test_userid()
        TEST_USERID_LIST.append((TEST_IMAGE_LIST[i][0], userid,
                                 TEST_IMAGE_LIST[i][2]))


# Generate the global userid list at the beginning so that the following
# test classes (currently only cases in GuestHandlerTestCaseWithDeployedGuest)
# can use this list to parameterize test cases for different distros.
generate_test_userid_list()


class GuestHandlerBase(base.ZVMConnectorBaseTestCase):
    """Base class for guest releated tests, which includes:
    - common init steps;
    - common helper functions;
    """

    def __init__(self, methodName='runTest'):
        super(GuestHandlerBase, self).__init__(methodName)
        # Generate random userid foreach run
        self.userid = self.utils.generate_test_userid()
        self.test_vsw = "RESTVSW1"
        self.test_vsw2 = "RESTVSW2"
        self._GuestDbOperator = database.GuestDbOperator()

    def _check_CPU_MEM(self, userid, cpu_cnt=None, cpu_cnt_live=None,
                       memory_size=None,
                       memory_size_live=None,
                       check_reserve=True,
                       maxcpu=CONF.zvm.user_default_max_cpu,
                       maxmem=CONF.zvm.user_default_max_memory):
        resp_info = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp_info.status_code)

        Statement = "USER %s LBYONLY" % userid.upper()
        resp_content = test_utils.load_output(resp_info.content)
        user_direct = resp_content['output']['user_direct']
        cpu_num = 0
        cpu_num_live = 0
        cpu_num_online = 0

        for ent in user_direct:
            if ent.startswith(Statement):
                memory_direct = ent.split()[3].strip()
                max_memory = ent.split()[4].strip()
                memory_direct = int(utils.convert_to_mb(memory_direct))
            if ent.startswith("COMMAND DEF STOR RESERVED"):
                memory_reserve_direct = ent.split()[4].strip()
                memory_reserve_direct = int(utils.convert_to_mb(
                                                    memory_reserve_direct))
            if ent.startswith("CPU"):
                cpu_num = cpu_num + 1
            if ent.startswith("MACHINE ESA"):
                max_cpus = int(ent.split()[2].strip())
        if cpu_cnt_live is not None:
            active_cpus = self._smtclient.execute_cmd(userid, "lscpu -e")[1:]
            cpu_num_live = len(active_cpus)
            active_cpus = self._smtclient.execute_cmd(userid,
                                                       "lscpu --parse=ONLINE")
            for c in active_cpus:
                # check online CPU number
                if c.startswith("# "):
                    continue
                online_state = c.strip().upper()
                if online_state == "Y":
                    cpu_num_online = cpu_num_online + 1
        if memory_size_live is not None:
            memory_info = self._smtclient.execute_cmd(userid, "lsmem")[-2:]
            online_memory = int(memory_info[0].split()[4].strip())
            offline_memory = int(memory_info[1].split()[3].strip())

        if cpu_cnt is not None:
            self.assertEqual(cpu_cnt, cpu_num)
        if memory_size is not None:
            memory_size = int(utils.convert_to_mb(memory_size))
            self.assertEqual(memory_size, memory_direct)
        if cpu_cnt_live is not None:
            self.assertEqual(cpu_cnt_live, cpu_num_live)
            self.assertEqual(cpu_cnt_live, cpu_num_online)

        if memory_size_live is not None:
            memory_size_live = int(utils.convert_to_mb(memory_size_live))
            self.assertEqual(memory_size_live, online_memory)
            if check_reserve:
                self.assertEqual(memory_reserve_direct, offline_memory)

        self.assertEqual(maxcpu, max_cpus)
        self.assertEqual(maxmem, max_memory)

    def _check_total_memory(self, userid,
                            maxmem=CONF.zvm.user_default_max_memory):
        result_list = self._smtclient.execute_cmd(userid,
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

    def _check_interface(self, userid, ip):
        """ Check network interface.
        Returns a bool value to indicate whether the network interface is
        defined
        """
        result_list = self._smtclient.execute_cmd(userid, 'ip addr')

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
                      "disk_pool": CONF.zvm.disk_pool},
                     {"size": "512m", "format": "swap",
                      "disk_pool": CONF.zvm.disk_pool}]
        return self.client.guest_create_disks(userid, disk_list)

    def _guest_config_minidisk_multiple(self, userid):
        """Configure minidisk 101, 102"""
        disk_list = [{"vdev": "0101",
                      "format": "ext3",
                      "mntdir": "/mnt/0101"},
                     {"vdev": "0102",
                      "format": "ext3",
                      "mntdir": "/mnt/0102"}]

        return self.client.guest_config_minidisks(userid, disk_list)

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
        if vsw is not None:
            vsw = vsw.upper()

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
        resp = self.client.guests_get_nic_info(userid)
        nics_info = test_utils.load_output(resp.content)['output']

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

    def _make_transport_file(self):
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        os.mkdir('/'.join([tempDir, 'openstack']))
        os.mkdir('/'.join([tempDir, 'openstack/latest']))
        transport_file = '/'.join([tempDir,
                                "openstack/latest/meta_data.json"])
        transport_file1 = '/'.join([tempDir,
                            "openstack/latest/network_data.json"])
        transport_file2 = '/'.join([tempDir,
                            "openstack/latest/vendor_data.json"])
        transport_file3 = '/'.join([tempDir,
                            "openstack/latest/vendor_data2.json"])
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
                      "hostname": "deploy_fvt",\
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
        cmd = ['mkisofs',
               '-o',
               '/var/lib/zvmsdk/cfgdrive.iso',
               '-ldots',
               '-allow-lowercase',
               '-allow-multidot',
               '-l',
               '-quiet',
               '-J',
               '-r',
               '-V',
               'config-2',
               tempDir]
        try:
            output = subprocess.check_output(cmd,
                                             close_fds=True,
                                             stderr=subprocess.STDOUT)
            output = bytes.decode(output)
            output.split()[2]
        except subprocess.CalledProcessError as e:
            msg = e.output
            print("Create cfgdrive.iso meet error: %s" % msg)
        except Exception as e:
            msg = e.output
            print("Create cfgdrive.iso meet error: %s" % msg)

        os.system('rm -rf %s' % tempDir)
        os.system('chown -R zvmsdk:zvmsdk /var/lib/zvmsdk/cfgdrive.iso')
        os.system('chmod -R 755 /var/lib/zvmsdk/cfgdrive.iso')

    def _get_free_osa(self):
        osa_info = self._smtclient._query_OSA()
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

    def _get_userid_auto_cleanup(self):
        userid = self.utils.generate_test_userid()
        self.addCleanup(self.utils.destroy_guest, userid)
        return userid


class GuestHandlerTestCase(GuestHandlerBase):
    """Guest testcases without an existing userid."""

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

    def test_guest_deploy_userid_not_exist(self):
        resp = self.client.guest_deploy(userid='notexist')
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

    def test_guest_vswitch_couple_uncouple_userid_not_exist(self):
        resp = self.client.guest_nic_couple_to_vswitch("notexist", "1000",
                                                       self.test_vsw)
        self.assertEqual(404, resp.status_code)

        resp = self.client.guest_nic_uncouple_from_vswitch("notexist", "5000")
        self.assertEqual(404, resp.status_code)

    def test_guest_vif_create_not_exist(self):
        resp = self.client.guest_create_network_interface('notexist',
                                                          'rhel6.7', [])
        self.assertEqual(404, resp.status_code)

    def test_guest_vif_delete_not_exist(self):
        resp = self.client.guest_delete_network_interface(userid='notexist',
                                                          os_version='rhel6.7')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_query_not_exist(self):
        resp = self.client.guests_get_nic_info(userid='notexist')
        self.assertEqual(200, resp.status_code)

    def test_guest_nic_delete_not_exist(self):
        resp = self.client.guest_delete_nic(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_create_not_exist(self):
        resp = self.client.guest_create_disks('notexist', [])
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_not_exist(self):
        resp = self.client.guest_delete_disks('notexist', ['FF00'])
        self.assertEqual(404, resp.status_code)

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

        resp = self.client.guest_inspect_stats('abc, @@@@@123456789')
        self.assertEqual(400, resp.status_code)

        resp = self.client.guest_inspect_vnics('abc, @@@@@123456789')
        self.assertEqual(400, resp.status_code)

    def test_guest_create_with_profile_notexit(self):
        userid = self.utils.generate_test_userid()
        resp = self.client.guest_create(userid, user_profile="notexist")
        self.assertEqual(404, resp.status_code)

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

    def test_guest_create_with_profile_multiple_disks_with_vdev(self):
        userid = self._get_userid_auto_cleanup()
        disk_list = [{"size": "3g", "is_boot_disk": True, "vdev": "0150"},
                     {"size": "2g", "vdev": "0200"}]

        # create multi-disks guest with profile specified
        resp = self.client.guest_create(userid, disk_list=disk_list,
                                        user_profile=CONF.zvm.user_profile)
        self.assertEqual(200, resp.status_code)

        # get guest definition
        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)

        resp_content = test_utils.load_output(resp.content)
        resp_direct = str(resp_content['output']['user_direct'])

        # verify two disks added
        self.assertFalse('MDISK 0100' in resp_direct)
        self.assertFalse('MDISK 0101' in resp_direct)
        self.assertTrue('MDISK 0150' in resp_direct)
        self.assertTrue('MDISK 0200' in resp_direct)
        # verify included the profile
        self.assertTrue('INCLUDE %s' % CONF.zvm.user_profile.upper() in
                        resp_direct)

    def test_guest_create_with_profile_multiple_disks(self):
        userid = self._get_userid_auto_cleanup()
        disk_list = [{"size": "3g", "is_boot_disk": True},
                     {"size": "1g"}]

        # create multi-disks guest with profile specified
        resp = self.client.guest_create(userid, disk_list=disk_list,
                                        user_profile=CONF.zvm.user_profile)
        self.assertEqual(200, resp.status_code)

        # get guest definition
        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)

        # verify two disks added
        self.assertTrue('MDISK 0100' in resp.content)
        self.assertTrue('MDISK 0101' in resp.content)
        # verify included the profile
        self.assertTrue('INCLUDE %s' % CONF.zvm.user_profile.upper() in
                        resp.content)

    def test_guest_create_with_ipl_cms(self):
        userid = self._get_userid_auto_cleanup()
        disk_list = [{"size": "3g", "is_boot_disk": True}]

        resp = self.client.guest_create(userid, disk_list=disk_list,
                                        user_profile=CONF.zvm.user_profile,
                                        ipl_from='cms')
        self.assertEqual(200, resp.status_code)

        # get guest definition
        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)

        # verify two disks added
        self.assertTrue('IPL CMS' in resp.content)
        self.assertFalse('IPL 0100' in resp.content)

    def test_guest_create_with_ipl_with_param(self):
        userid = self._get_userid_auto_cleanup()
        disk_list = [{"size": "3g", "is_boot_disk": True}]

        resp = self.client.guest_create(userid, disk_list=disk_list,
                                        user_profile=CONF.zvm.user_profile,
                                        ipl_param='dummy',
                                        ipl_loadparam='load=1')
        self.assertEqual(200, resp.status_code)

        # get guest definition
        resp = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp.status_code)

        # verify two disks added
        self.assertTrue('IPL 0100 PARM DUMMY LOADPARM LOAD=1' in resp.content)

    @parameterized.expand(TEST_IMAGE_LIST)
    def test_guest_create_deploy_capture_delete(self, case_name,
                                                image_path, os_version):
        """Scenario BVT testcases."""
        userid = self._get_userid_auto_cleanup()
        ip_addr = self.utils.generate_test_ip()
        guest_networks = [{'ip_addr': ip_addr, 'cidr': CONF.tests.cidr}]
        captured_image_name = "test_capture_%s" % case_name

        resp = self.client.guest_create(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_create_userid_complete(userid))

        self._make_transport_file()
        self.addCleanup(os.system, 'rm /var/lib/zvmsdk/cfgdrive.iso')

        transport_file = '/var/lib/zvmsdk/cfgdrive.iso'
        image_name = self.utils.import_image_if_not_exist(image_path,
                                                          os_version)

        resp = self.client.guest_deploy(userid, image_name=image_name,
                                        transportfiles=transport_file)
        self.assertEqual(200, resp.status_code)

        # todo: create network interface
        resp = self.client.guest_create_network_interface(userid, os_version,
                                                          guest_networks)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        # Verify cfgdrive.iso take effect
        time.sleep(60)
        result = self._smtclient.execute_cmd(userid, 'hostname')
        self.assertIn('deploy_fvt', str(result))

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

        # Use softstop instend of stop to avoid the data lose with guest_stop
        # when testing the sles12 image.
        resp = self.client.guest_softstop(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(userid,
                                                                   "off"))

        resp = self.client.guest_inspect_stats(userid)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_stats',
                                   resp.content)

        # pause unpause a stopped instance should return 409
        resp = self.client.guest_pause(userid)
        self.assertEqual(409, resp.status_code)
        resp = self.client.guest_unpause(userid)
        self.assertEqual(409, resp.status_code)

        # Capture a powered off instance will lead to error
        resp = self.client.guest_capture(userid, 'failed')
        self.assertEqual(409, resp.status_code)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        resp_info = self.client.guest_get_info(userid)
        self.assertEqual(200, resp_info.status_code)

        resp_content = test_utils.load_output(resp_info.content)
        info_off = resp_content['output']
        self.assertEqual('on', info_off['power_state'])
        self.assertNotEqual(info_off['cpu_time_us'], 0)
        self.assertNotEqual(info_off['mem_kb'], 0)

        resp = self.client.guest_capture(userid, 'failed',
                                         capture_type='alldisks')
        self.assertEqual(501, resp.status_code)

        resp = self.client.guest_capture(userid, captured_image_name)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.image_delete, captured_image_name)

        resp = self.client.image_query(captured_image_name)
        self.assertEqual(200, resp.status_code)

        resp_state = self.client.guest_get_power_state(userid)
        self.assertEqual(200, resp_state.status_code)

        resp_content = test_utils.load_output(resp_state.content)
        self.assertEqual('off', resp_content['output'])

    @parameterized.expand(TEST_IMAGE_LIST)
    def test_guest_create_deploy_set_hostname(self, case_name, image_path,
                                              os_version):
        """Deploy with hostname specified."""
        userid = self._get_userid_auto_cleanup()
        ip_addr = self.utils.generate_test_ip()
        guest_networks = [{'ip_addr': ip_addr, 'cidr': CONF.tests.cidr}]
        hostname = 'fakehostname'

        resp = self.client.guest_create(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_create_userid_complete(userid))

        image_name = self.utils.import_image_if_not_exist(image_path,
                                                          os_version)

        resp = self.client.guest_deploy(userid, image_name=image_name,
                                        hostname=hostname)
        self.assertEqual(200, resp.status_code)

        # todo: create network interface
        resp = self.client.guest_create_network_interface(userid, os_version,
                                                          guest_networks)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        # Verify hostname changed
        time.sleep(30)
        result = self._smtclient.execute_cmd(userid, 'hostname')
        self.assertIn('fakehostname', result)

    def test_guests_get_nic_info(self):
        resp = self.client.guests_get_nic_info()
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self.client.guests_get_nic_info(userid='test')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self.client.guests_get_nic_info(nic_id='testnic')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self.client.guests_get_nic_info(vswitch='vswitch')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self.client.guests_get_nic_info(userid='test', nic_id='testnic')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

        resp = self.client.guests_get_nic_info(userid='test', nic_id='testnic',
                                              vswitch='vswitch')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info',
                                   resp.content)

    @parameterized.expand(TEST_IMAGE_LIST)
    def test_guest_live_resize_cpus(self, case_name,
                                    image_path, os_version):
        userid = self._get_userid_auto_cleanup()
        resp = self.client.guest_create(userid, max_cpu=10, max_mem="2048M")
        self.assertEqual(200, resp.status_code)

        image_name = self.utils.import_image_if_not_exist(image_path,
                                                          os_version)

        resp = self.client.guest_deploy(userid, image_name)
        self.assertEqual(200, resp.status_code)

        # Live resize a guest's CPU when the guest is not active
        resp = self.client.guest_live_resize_cpus(userid, 2)
        self.assertEqual(409, resp.status_code)

        # Power on the guest
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        # check max cpu memory
        self._check_CPU_MEM(userid, maxcpu=10, maxmem="2048M")
        self._check_total_memory(userid, maxmem="2048M")

        # Resized cpu number exceed the user's max cpu number
        resp = self.client.guest_resize_cpus(userid, 11)
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu number exceed the allowed max cpu number
        resp = self.client.guest_resize_cpus(userid, 65)
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu number is less than the allowed min cpu number
        resp = self.client.guest_resize_cpus(userid, 0)
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu number exceed the user's max cpu number
        resp = self.client.guest_live_resize_cpus(userid, 11)
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu number exceed the allowed max cpu number
        resp = self.client.guest_live_resize_cpus(userid, 65)
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu number is less than the allowed min cpu number
        resp = self.client.guest_live_resize_cpus(userid, 0)
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num equal to the current cpu num in user direct,
        # and equal to the live cpu num
        #  - cpu num in user direct: not change
        #  - live cpu num: not change
        resp = self.client.guest_live_resize_cpus(userid, 1)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=1, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num equal to the user's max cpu num in user direct,
        #  - cpu num in user direct: increase
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 10)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=10, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num is less than the current cpu num in user direct
        #  - cpu num in user direct: decrease
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 3)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=1,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num equal to the current cpu num in user direct,
        # and is greater than the live cpu num
        #  - cpu num in user direct: not change
        #  - live cpu num: increased
        resp = self.client.guest_live_resize_cpus(userid, 3)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=3,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num equal to the current cpu num in user direct,
        # and equal to the live cpu num
        #  - cpu num in user direct: not change
        #  - live cpu num: not change
        resp = self.client.guest_live_resize_cpus(userid, 3)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=3, cpu_cnt_live=3,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num is greater than the current cpu num in user
        # direct, and is greater than the live cpu num
        #  - cpu num in user direct: increase
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 5)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=3,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num is less than the current cpu num
        # in user direct, and is greater than the live cpu num
        #  - cpu num in user direct: decrease
        #  - live cpu num: increase
        resp = self.client.guest_live_resize_cpus(userid, 4)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=4,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num is greater than the current cpu num
        # in user direct, and is greater than the live cpu num
        #  - cpu num in user direct: increase
        #  - live cpu num: increase
        resp = self.client.guest_live_resize_cpus(userid, 5)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num is greater than the current cpu num
        # in user direct, and is greater than the live cpu num
        #  - cpu num in user direct: increase
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 7)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num is less than the current cpu num
        # in user direct, and is less than the live cpu num
        #  - cpu num in user direct: decrease
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 4)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num equal to the current cpu num
        # in user direct, and is less than the live cpu num
        #  - cpu num in user direct: not change
        #  - live cpu num: not change
        resp = self.client.guest_live_resize_cpus(userid, 4)
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num is greater than the current cpu num
        # in user direct, and equal to the live cpu num
        #  - cpu num in user direct: increase
        #  - live cpu num: not change
        resp = self.client.guest_live_resize_cpus(userid, 5)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num is less than the live cpu num
        #  - cpu num in user direct: not change
        #  - live cpu num: not change
        resp = self.client.guest_live_resize_cpus(userid, 4)
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=5, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Resized cpu num is less than the current cpu num
        # in user direct, and is less than the live cpu num
        #  - cpu num in user direct: decrease
        #  - live cpu num: not change
        resp = self.client.guest_resize_cpus(userid, 4)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=5,
                            maxcpu=10, maxmem="2048M")

        # Restart guest, check cpu number
        resp = self.client.guest_softstop(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(userid,
                                                                  "off"))
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))
        self._check_CPU_MEM(userid, cpu_cnt=4, cpu_cnt_live=4,
                            maxcpu=10, maxmem="2048M")

        # Live resized cpu num is greater than the current cpu num
        # in user direct, and is greater than the live cpu num
        #  - cpu num in user direct: increase
        #  - live cpu num: increase
        resp = self.client.guest_live_resize_cpus(userid, 7)
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=7,
                            maxcpu=10, maxmem="2048M")

        # Restart guest, check cpu number
        resp = self.client.guest_softstop(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(userid,
                                                                  "off"))
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))
        self._check_CPU_MEM(userid, cpu_cnt=7, cpu_cnt_live=7,
                            maxcpu=10, maxmem="2048M")

    @parameterized.expand(TEST_IMAGE_LIST)
    def test_guest_live_resize_memory(self, case_name,
                                    image_path, os_version):
        userid = self._get_userid_auto_cleanup()
        resp = self.client.guest_create(userid, memory=2048,
                                        max_cpu=10, max_mem="10G")
        self.assertEqual(200, resp.status_code)

        image_name = self.utils.import_image_if_not_exist(image_path,
                                                          os_version)

        resp = self.client.guest_deploy(userid, image_name)
        self.assertEqual(200, resp.status_code)

        # Live resize a guest's CPU when the guest is not active
        resp = self.client.guest_live_resize_memory(userid, "1G")
        self.assertEqual(409, resp.status_code)

        # Power on the guest
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        # check cpu memory
        self._check_CPU_MEM(userid, memory_size="2048M",
                            memory_size_live="2048M", maxcpu=10, maxmem="10G")
        self._check_total_memory(userid, maxmem="10G")

        # Live resize a guest's memory when the guest is active, unit M
        resp = self.client.guest_live_resize_memory(userid, "4096M")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="4096M",
                            memory_size_live="4096M", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory more than the current size, unit G
        resp = self.client.guest_live_resize_memory(userid, "9G")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="9G",
                            memory_size_live="9G", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory less than the current size
        resp = self.client.guest_live_resize_memory(userid, "4096M")
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="9G",
                            memory_size_live="9G", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory equal to the current size
        resp = self.client.guest_live_resize_memory(userid, "9G")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="9G",
                            memory_size_live="9G", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory more than the max size
        resp = self.client.guest_live_resize_memory(userid, "20G")
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="9G",
                            memory_size_live="9G", maxcpu=10, maxmem="10G")

        # Resize a guest's memory more than the current size
        resp = self.client.guest_resize_memory(userid, "10G")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="10G",
                            memory_size_live="9G", check_reserve=False,
                            maxcpu=10, maxmem="10G")

        # Resize a guest's memory less than the current size
        resp = self.client.guest_resize_memory(userid, "8192M")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="8192M",
                            memory_size_live="9G", check_reserve=False,
                            maxcpu=10, maxmem="10G")

        # Resize a guest's memory equal to the current size
        resp = self.client.guest_resize_memory(userid, "8192M")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="8192M",
                            memory_size_live="9G", check_reserve=False,
                            maxcpu=10, maxmem="10G")

        # Resize a guest's memory more than the max size
        resp = self.client.guest_resize_memory(userid, "20G")
        self.assertEqual(409, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="8192M",
                            memory_size_live="9G", check_reserve=False,
                            maxcpu=10, maxmem="10G")

        # Restart guest, check memory
        resp = self.client.guest_softstop(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(userid,
                                                                  "off"))
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))
        self._check_CPU_MEM(userid, memory_size="8192M",
                            memory_size_live="8192M", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory equal to the max size
        resp = self.client.guest_live_resize_memory(userid, "10G")
        self.assertEqual(200, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="10G",
                            memory_size_live="10G", maxcpu=10, maxmem="10G")

        # Live resize a guest's memory, invalid size/unit
        resp = self.client.guest_live_resize_memory(userid, "1T")
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="10G",
                            memory_size_live="10G", maxcpu=10, maxmem="10G")

        resp = self.client.guest_live_resize_memory(userid, "10240m")
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="10G",
                            memory_size_live="10G", maxcpu=10, maxmem="10G")

        resp = self.client.guest_live_resize_memory(userid, "1024k")
        self.assertEqual(400, resp.status_code)
        self._check_CPU_MEM(userid, memory_size="10G",
                            memory_size_live="10G", maxcpu=10, maxmem="10G")


class GuestHandlerTestCaseWithCreatedGuest(GuestHandlerBase):
    """This class is used to test functions that requires a guest to be
    created but doesn't need the guest to be started, so no need to do deploy.
    """

    @classmethod
    def setUpClass(cls):
        super(GuestHandlerTestCaseWithCreatedGuest, cls).setUpClass()
        cls.userid_exists = cls.utils.generate_test_userid()
        cls.client.guest_create(cls.userid_exists)
        cls.utils.wait_until_create_userid_complete(cls.userid_exists)

    @classmethod
    def tearDownClass(cls):
        super(GuestHandlerTestCaseWithCreatedGuest, cls).tearDownClass()
        cls.client.vswitch_delete('restvsw1')
        cls.utils.destroy_guest(cls.userid_exists)

    def test_guest_deploy_vdev_not_exist(self):
        resp = self.client.guest_deploy(self.userid_exists, vdev='FFFF')
        self.assertEqual(404, resp.status_code)

    def test_guest_deploy_image_not_exist(self):
        resp = self.client.guest_deploy(self.userid_exists,
                                        image_name='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_delete_device_not_exist(self):
        # no error returned if the vnic does not exist
        resp = self.client.guest_delete_nic(self.userid_exists, vdev='FFFF')
        self.assertEqual(200, resp.status_code)

    @unittest.skip("Skip until bug/1747591 fixed")
    def test_guest_disk_pool_create_not_exist(self):
        disk_list = [{"size": "1g", "format": "ext3",
                      "disk_pool": 'ECKD:notexist'}]
        resp = self.client.guest_create_disks(self.userid_exists, disk_list)
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_device_not_exist(self):
        # disk not exist
        resp = self.client.guest_delete_disks(self.userid_exists, ["FFFF"])
        self.assertEqual(200, resp.status_code)

    def test_guest_create_exist(self):
        resp = self.client.guest_create(self.userid_exists)
        self.assertEqual(409, resp.status_code)

    def test_guest_vswitch_couple_uncouple_vswitch_not_exist(self):
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                                               "5000", vswitch_name="NOTEXIST")
        self.assertEqual(404, resp.status_code)


class GuestHandlerTestCaseWithSingleDeployedGuest(GuestHandlerBase):
    """This class is used to test functions that requires a deployed guest to
    be active, but not related to the guest distro."""

    @classmethod
    def setUpClass(cls):
        super(GuestHandlerTestCaseWithSingleDeployedGuest, cls).setUpClass()
        cls.client = test_utils.TestzCCClient()
        cls.utils = test_utils.ZVMConnectorTestUtils()
        cls.userid_exists = cls.utils.deploy_guest()[0]
        cls.utils.softstop_guest(cls.userid_exists)

    @classmethod
    def tearDownClass(cls):
        super(GuestHandlerTestCaseWithSingleDeployedGuest, cls).tearDownClass()
        cls.utils.destroy_guest(cls.userid_exists)

    def tearDown(self):
        # make sure the guest in shutdown state
        self.utils.softstop_guest(self.userid_exists)
        GuestHandlerBase.tearDown(self)

    def test_guest_create_delete_nic(self):
        # Creating NIC with fixed vdev.
        resp = self.client.guest_create_nic(self.userid_exists, vdev="1003")
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_nic, self.userid_exists,
                        "1003")
        nic_defined, vsw = self._check_nic("1003", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Creating NIC with vdev conflict with defined NIC.
        resp = self.client.guest_create_nic(self.userid_exists, vdev="1004")
        self.assertEqual(409, resp.status_code)

        # Creating NIC with nic_id.
        resp = self.client.guest_create_nic(self.userid_exists, vdev="1006",
                                            nic_id='123456')
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_nic, self.userid_exists,
                        "1006")

        resp = self.client.guests_get_nic_info(self.userid_exists,
                                              nic_id='123456')
        self.assertEqual(200, resp.status_code)

        nic_info = test_utils.load_output(resp.content)['output']
        self.assertEqual("1006", nic_info[0]["interface"])
        self.assertEqual("123456", nic_info[0]["port"])

        # Creating NIC with mac_addr
        resp = self.client.guest_create_nic(self.userid_exists, vdev="1009",
                                            mac_addr='02:00:00:12:34:56')
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", self.userid_exists,
                                           mac='123456')
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Creating NIC to active guest when guest is in off status.
        resp = self.client.guest_create_nic(self.userid_exists, vdev='1100',
                                            active=True)
        self.assertEqual(409, resp.status_code)

        # Deleting NIC to active guest when guest is in off status.
        resp = self.client.guest_delete_nic(self.userid_exists, vdev="1009",
                                            active=True)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Deleting NIC
        resp = self.client.guest_delete_nic(self.userid_exists, vdev="1009")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("1009", self.userid_exists)
        self.assertFalse(nic_defined)

        # Deleting NIC not existed
        resp = self.client.guest_delete_nic(self.userid_exists, vdev="1009")
        self.assertEqual(200, resp.status_code)

        # start the guest
        self.client.guest_start(self.userid_exists)
        self.assertTrue(self.utils.wait_until_guest_reachable(
                                                        self.userid_exists))
        # Creating NIC active
        resp = self.client.guest_create_nic(self.userid_exists, vdev='2000',
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        resp = self.client.guest_delete_nic(self.userid_exists, vdev="2000",
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertFalse(nic_defined)

    def test_guest_vswitch_couple_uncouple(self):
        # create vswitch
        resp = self.client.vswitch_create(self.test_vsw, rdev='FF00')
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.vswitch_delete, self.test_vsw)

        resp = self.client.guest_create_nic(self.userid_exists, vdev="2000")
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_nic, self.userid_exists,
                        vdev="2000")

        # Check nic defined in user direct and not coupled to vswitch
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Coupling with active=True on an off-state VM
        # The action should fail and rollback the user direct
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                               "2000", vswitch_name=self.test_vsw, active=True)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Coupling NIC to VSWITCH.
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                                           "2000", vswitch_name=self.test_vsw)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Coupling NIC to VSWITCH second time, same vswitch, supported.
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                                           "2000", vswitch_name=self.test_vsw)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Coupling NIC to VSWITCH, to different vswitch, not supported
        # Should still be coupled to original vswitch
        resp = self.client.vswitch_create(self.test_vsw2, rdev='FF10')
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.vswitch_delete, self.test_vsw2)

        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                                           "2000", vswitch_name=self.test_vsw2)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Uncoupling with active=True on an off-state VM.
        # The NIC shoule not uncoupled in user direct and switch table
        resp = self.client.guest_nic_uncouple_from_vswitch(self.userid_exists,
                                                           "2000", active=True)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Uncoupling NIC from VSWITCH the second time.
        resp = self.client.guest_nic_uncouple_from_vswitch(self.userid_exists,
                                                           "2000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Deleting NIC
        resp = self.client.guest_delete_nic(self.userid_exists, vdev="2000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic('2000', self.userid_exists)
        self.assertFalse(nic_defined)

        # Deleting NIC not existed
        resp = self.client.guest_delete_nic(self.userid_exists, vdev="2000")
        self.assertEqual(200, resp.status_code)

        # Activating the VM
        self.client.guest_start(self.userid_exists)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(
                                                    self.userid_exists, "on"))

        # Creating NIC with active=True
        resp = self.client.guest_create_nic(self.userid_exists, vdev="2000",
                                            active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
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
        resp = self.client.vswitch_grant_user(self.test_vsw,
                                              self.userid_exists)
        self.assertEqual(200, resp.status_code)

        # Coupling NIC to VSWITCH.
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                               "2000", vswitch_name=self.test_vsw, active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Coupling NIC to VSWITCH second time, same vswitch, supported
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                               "2000", vswitch_name=self.test_vsw, active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Coupling NIC to VSWITCH, to different vswitch, not supported.
        # Should still be coupled to original vswitch
        resp = self.client.guest_nic_couple_to_vswitch(self.userid_exists,
                           "2000", vswitch_name=self.test_vsw2, active=True)
        self.assertEqual(409, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists,
                                           vsw=self.test_vsw)
        self.assertTrue(nic_defined)
        self.assertEqual(self.test_vsw, vsw)

        # Uncoupling NIC from VSWITCH.
        resp = self.client.guest_nic_uncouple_from_vswitch(self.userid_exists,
                                                           "2000", active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        # Uncoupling NIC from VSWITCH the second time.
        resp = self.client.guest_nic_uncouple_from_vswitch(self.userid_exists,
                                                           "2000", active=True)
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", self.userid_exists)
        self.assertTrue(nic_defined)
        self.assertEqual(None, vsw)

        resp = self.client.guests_get_nic_info(self.userid_exists)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_nic_info', resp.content)

        resp = self.client.guest_delete_nic(self.userid_exists, "2000")
        self.assertEqual(200, resp.status_code)


class GuestHandlerTestCaseWithMultipleDeployedGuest(GuestHandlerBase):
    """This class is used to test functions that requires multip deployed
    guests to be active, and performs tests on different supported distros.
    """

    @classmethod
    def setUpClass(cls):
        super(GuestHandlerTestCaseWithMultipleDeployedGuest,
              cls).setUpClass()
        cls.userid_list = []
        # Deploy a guest with each specified image and previously generated
        # userid.
        for i in range(0, len(TEST_IMAGE_LIST)):
            image = TEST_IMAGE_LIST[i]
            userid = TEST_USERID_LIST[i][1]
            cls.utils.deploy_guest(userid, image_path=image[1],
                                   os_version=image[2])
            cls.userid_list.append(userid)

    @classmethod
    def tearDownClass(cls):
        super(GuestHandlerTestCaseWithMultipleDeployedGuest,
              cls).tearDownClass()
        for userid in cls.userid_list:
            cls.utils.destroy_guest(userid)

    def tearDown(self):
        # make sure all the guests in shutdown state
        for userid in self.userid_list:
            self.utils.softstop_guest(userid)
            self.utils.wait_until_guest_in_power_state(userid, "off")
            # make sure guest in shutdown state even performed softoff
            self.client.guest_stop(userid)

        GuestHandlerBase.tearDown(self)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_live_migrate(self, case_name, userid, version):
        # Move a running guest from one z/VM to another within an SSI cluster
        # power on
        self.client.guest_start(userid)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(
                                                userid, "on"))
        # live migrate
        resp_test1 = self.client.guest_live_migrate_vm(userid, "LEON0001",
                                         "opnstk2", {}, "test")

        if resp_test1.status_code == 200:
            resp = self.client.guest_live_migrate_vm(userid, "LEON0001",
                                         "opnstk2", {}, "move")
            self.assertEqual(200, resp.status_code)

        comments = self._GuestDbOperator.get_comments_by_userid(userid)
        comments['migrated'] = 0
        self._GuestDbOperator.update_guest_by_userid(userid,
                                                    comments=comments)
        self.client.guest_delete(userid)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_get_console_output(self, case_name, userid, version):
        # power on
        self.client.guest_start(userid)
        self.assertTrue(self.utils.wait_until_guest_in_power_state(
                                                userid, "on"))

        # get console output
        resp = self.client.guest_get_console_output(userid)
        self.assertEqual(200, resp.status_code)
        outputs = test_utils.load_output(resp.content)['output']
        self.assertNotEqual(outputs, '')

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_power_actions(self, case_name, userid, version):
        # power on
        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        # pause and unpause
        resp = self.client.guest_pause(userid)
        self.assertEqual(200, resp.status_code)
        resp = self.client.guest_unpause(userid)
        self.assertEqual(200, resp.status_code)

        # reboot and reset
        resp = self.client.guest_reboot(userid)
        self.assertTrue(self.utils._wait_until(False,
                           self.utils.is_guest_reachable, userid))
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))
        self.assertEqual(200, resp.status_code)

        resp = self.client.guest_reset(userid)
        self.assertTrue(self.utils._wait_until(False,
                           self.utils.is_guest_reachable, userid))
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))
        self.assertEqual(200, resp.status_code)

        # power off
        resp = self.client.guest_softstop(userid)
        self.assertEqual(200, resp.status_code)
        self.utils.wait_until_guest_in_power_state(userid, "off")

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_create_disks_and_configure(self, case_name,
                                              userid, version):
        flag1 = False
        flag2 = False
	flat3 = False

        # create new disks
        resp = self._guest_disks_create_multiple(userid)
        self.assertEqual(200, resp.status_code)

        resp_create = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp_create.status_code)
        self.assertTrue('MDISK 0101' in resp_create.content)
        self.assertTrue('MDISK 0102' in resp_create.content)
	self.assertTrue('MDISK 0103' in resp_create.content)

        # config 'MDISK 0101'
        resp_config = self._guest_config_minidisk_multiple(userid)
        self.assertEqual(200, resp_config.status_code)

        resp = self.client.guest_start(userid)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        time.sleep(15)
        result = self._smtclient.execute_cmd(userid, 'df -h')
        for element in result:
            if '/mnt/0101' in element:
                flag1 = True
            if '/mnt/0102' in element:
                flag2 = True
        self.assertTrue(flag1)
        self.assertTrue(flag2)

        # delete new disks when guest active - not supported
        resp = self.client.guest_delete_disks(userid,
                                              ['101', '102', '103'])
        self.assertEqual(501, resp.status_code)

        # delete disks when guest inactive
        resp = self.client.guest_stop(userid)
        self.assertTrue(
            self.utils.wait_until_guest_in_power_state(userid, 'off'))
        resp = self.client.guest_delete_disks(userid,
                                              ['101', '102', '103'])

        resp_delete = self.client.guest_get_definition_info(userid)
        self.assertEqual(200, resp_delete.status_code)
        self.assertTrue('MDISK 0101' not in resp_delete.content)
        self.assertTrue('MDISK 0102' not in resp_delete.content)
        self.assertTrue('MDISK 0103' not in resp_delete.content)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_create_delete_network_interface(self, case_name,
                                                   userid, version):
        ip_addr = self.utils.generate_test_ip()
        if_list = [{'ip_addr': ip_addr, 'nic_vdev': "2000",
                    "cidr": CONF.tests.cidr}]
        resp = self.client.guest_create_network_interface(userid, version,
                                                    guest_networks=if_list)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_network_interface, userid,
                        version, "2000")

        # Coupling NIC to the vswitch.
        resp = self.client.guest_nic_couple_to_vswitch(userid, "2000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("2000", userid,
                                           vsw=CONF.tests.vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(CONF.tests.vswitch, vsw)

        # Start the guest and check results
        self.assertTrue(self.utils.power_on_guest_until_reachable(userid))

        self.assertTrue(self.utils._wait_until(True, self._check_interface,
                                               userid, ip_addr))

        resp = self.client.guest_delete_network_interface(userid, version,
                                                      vdev="2000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(userid, ip=ip_addr)
        self.assertFalse(ip_set)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_create_network_interface_multiple(self, case_name,
                                                     userid, version):
        # create two interfaces together
        ip_addr2 = self.utils.generate_test_ip()
        ip_addr3 = self.utils.generate_test_ip()
        if_list = [
            {'ip_addr': ip_addr2, 'nic_vdev': "3000", "cidr": CONF.tests.cidr},
            {'ip_addr': ip_addr3, 'nic_vdev': "4000", "cidr": CONF.tests.cidr}]
        resp = self.client.guest_create_network_interface(userid, version,
                                                        guest_networks=if_list)
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_network_interface, userid,
                        version, "3000")
        self.addCleanup(self.client.guest_delete_network_interface, userid,
                        version, "4000")

        # Coupling NIC to the vswitch.
        resp = self.client.guest_nic_couple_to_vswitch(userid, "3000")
        self.assertEqual(200, resp.status_code)
        resp = self.client.guest_nic_couple_to_vswitch(userid, "4000")
        self.assertEqual(200, resp.status_code)
        nic_defined, vsw = self._check_nic("3000", userid,
                                           vsw=CONF.tests.vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(CONF.tests.vswitch, vsw)
        nic_defined, vsw = self._check_nic("4000", userid,
                                           vsw=CONF.tests.vswitch)
        self.assertTrue(nic_defined)
        self.assertEqual(CONF.tests.vswitch, vsw)

        # Start the guest and check results
        self.assertTrue(self.utils.power_on_guest_until_reachable(userid))

        for addr in (ip_addr2, ip_addr3):
            self.assertTrue(self.utils._wait_until(True, self._check_interface,
                                                   userid, addr))

        resp = self.client.guest_delete_network_interface(userid, version,
                                                      vdev="3000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(userid, ip=ip_addr2)
        self.assertFalse(ip_set)

        resp = self.client.guest_delete_network_interface(userid, version,
                                                      vdev="4000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(userid, ip=ip_addr3)
        self.assertFalse(ip_set)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_create_network_interface_dedicate_osa(self, case_name,
                                                         userid, version):
        # create an interface to dedicate osa
        osa = self._get_free_osa()
        self.assertNotEqual(osa, None)

        ip_addr = self.utils.generate_test_ip()
        if_info = {"ip_addr": ip_addr,
                   "gateway_addr": CONF.tests.gateway_v4,
                   "cidr": CONF.tests.cidr,
                   "nic_vdev": "2000",
                   "osa_device": osa}

        resp = self.client.guest_create_network_interface(userid, version,
                                                    guest_networks=[if_info])
        self.assertEqual(200, resp.status_code)
        self.addCleanup(self.client.guest_delete_network_interface, userid,
                        version, "2000")

        nic_defined, nic_osa = self._check_nic("2000", userid, osa=osa)
        self.assertTrue(nic_defined)
        self.assertEqual(nic_osa, osa)

        # power on the guest and check the osa
        self.assertTrue(self.utils.power_on_guest_until_reachable(userid))
        self.assertTrue(self.utils._wait_until(True, self._check_interface,
                                               userid, ip_addr))

        # Delete network interface
        resp = self.client.guest_delete_network_interface(userid, version,
                                                      vdev="2000", active=True)
        self.assertEqual(200, resp.status_code)
        ip_set = self._check_interface(userid, ip=ip_addr)
        self.assertFalse(ip_set)

    @parameterized.expand(TEST_USERID_LIST)
    def test_guest_create_cpu_memory_default(self, case_name,
                                             userid, version):
        # Power on the guest
        self.client.guest_start(userid)
        self.assertTrue(self.utils.wait_until_guest_reachable(userid))

        self._check_CPU_MEM(userid)
        self._check_total_memory(userid)


class GuestActionTestCase(base.ZVMConnectorBaseTestCase):
    """Testcases for url of /guests/<userid>/action ."""

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
