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
#    License for the specific language governing permissions and limitations
#    under the License.


import json
import os
import time
import unittest

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import base
from zvmsdk.tests.sdkwsgi import test_sdkwsgi
from zvmsdk.tests.sdkwsgi import test_utils
from zvmsdk import config
from zvmsdk import smutclient


CONF = config.CONF


class GuestHandlerTestCase(base.ZVMConnectorBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(GuestHandlerTestCase, cls).setUpClass()
        cls.apibase = api_sample.APITestBase()

        # test change bind_port
        base.set_conf('sdkserver', 'bind_port', 3000)

        cls.client = test_sdkwsgi.TestSDKClient()
        cls._smutclient = smutclient.get_smutclient()

        # every time, we need to random generate userid
        # the userid is used in most testcases that assume exists
        cls.userid = test_utils.generate_test_userid()

        cls.userid_exists = test_utils.generate_test_userid()
        cls._guest_create(cls.userid_exists)

    @classmethod
    def tearDownClass(cls):
        super(GuestHandlerTestCase, cls).tearDownClass()
        cls._cleanup()

    @classmethod
    def _cleanup(cls):
        url = '/guests/%s' % cls.userid_exists
        cls.client.api_request(url=url, method='DELETE')

        cls.client.api_request(url='/vswitches/restvsw1',
                                method='DELETE')

    def setUp(self):
        super(GuestHandlerTestCase, self).setUp()
        self.record_logfile_position()

    @classmethod
    def _guest_create(cls, userid=None, maxcpu=None, maxmem=None):
        content = {"guest": {"vcpus": 1,
                             "memory": 1024,
                             "disk_list": [{"size": "1100",
                                            "is_boot_disk": "True"}]}}
        userid = userid or cls.userid
        content["guest"]["userid"] = userid
        if maxcpu is not None:
            content["guest"]["max_cpu"] = maxcpu
        if maxmem is not None:
            content["guest"]["max_mem"] = maxmem

        body = json.dumps(content)
        resp = cls.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

    def _check_CPU_MEM(self, userid=None, cpu_cnt = None,
                       cpu_cnt_live = None,
                       maxcpu=CONF.zvm.user_default_max_cpu,
                       maxmem=CONF.zvm.user_default_max_memory):
        if userid is None:
            userid = self.userid

        resp_info = self._guest_get(userid=userid)
        self.assertEqual(200, resp_info.status_code)

        Statement = "USER %s LBYONLY" % userid.upper()
        resp_content = json.loads(resp_info.content)
        user_direct = resp_content['output']['user_direct']
        cpu_num = 0
        cpu_num_live = 0
        for ent in user_direct:
            if ent.startswith(Statement):
                max_memory = ent.split()[4].strip()
            if ent.startswith("CPU"):
                cpu_num = cpu_num + 1
            if ent.startswith("MACHINE ESA"):
                max_cpus = int(ent.split()[2].strip())
        if cpu_cnt_live is not None:
            active_cpus = self.execute_cmd(userid, "lscpu -e")[1:]
            cpu_num_live = len(active_cpus)

        if cpu_cnt is not None:
            self.assertEqual(cpu_cnt, cpu_num)
        if cpu_cnt_live is not None:
            self.assertEqual(cpu_cnt_live, cpu_num_live)
        self.assertEqual(maxcpu, max_cpus)
        self.assertEqual(maxmem, max_memory)

    def _check_total_memory(self, userid=None,
                            maxmem=CONF.zvm.user_default_max_memory):
        if userid is None:
            userid = self.userid

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

    def _guest_create_with_profile(self):
        body = """{"guest": {"userid": "%s", "vcpus": 1,
                             "memory": 1024,
                             "user_profile": "%s",
                             "disk_list": [{"size": "3g",
                                            "is_boot_disk": "True"},
                                            {"size": "3g"}]}}"""
        body = body % (self.userid, CONF.zvm.user_profile)
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

    def _guest_create_with_profile_notexit(self):
        body = """{"guest": {"userid": "%s", "vcpus": 1,
                             "memory": 1024,
                             "user_profile": "%s",
                             "disk_list": [{"size": "1100",
                                            "is_boot_disk": "True"},
                                            {"size": "1100"}]}}"""
        user_profile = 'notexist'
        body = body % (self.userid, user_profile)
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

    def _guest_delete(self, userid=None):
        if userid is None:
            userid = self.userid
        url = '/guests/%s' % userid
        resp = self.client.api_request(url=url, method='DELETE')
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_nic_create(self, vdev="1000", userid=None, nic_id=None,
                          mac_addr=None, active=False):
        content = {"nic": {"vdev": vdev}}
        if active:
            content["nic"]["active"] = "True"
        else:
            content["nic"]["active"] = "False"
        if nic_id is not None:
            content["nic"]["nic_id"] = nic_id

        if mac_addr is not None:
            content["nic"]["mac_addr"] = mac_addr
        body = json.dumps(content)
        if userid is None:
            userid = self.userid

        url = '/guests/%s/nic' % userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _check_interface(self, userid=None, ip="192.168.95.123"):
        """ Check network interface.
        Returns a bool value to indicate whether the network interface is
        defined
        """
        if userid is None:
            userid = self.userid
        result_list = self._smutclient.execute_cmd(userid, 'ifconfig')

        for element in result_list:
            if ip in element:
                return True
        return False

    def _guest_create_network_interface(self, userid,
                                        networks=[{'ip': "192.168.95.123",
                                                   'vdev': '1000'}],
                                        active=False):
        """
        possible keys for networks parameter includes: 'ip'(required),
        'vdev', 'osa'
        """
        common_attributes = {"dns_addr": ["9.0.3.1"],
                             "gateway_addr": "192.168.95.1",
                             "cidr": "192.168.95.0/24"}
        res_networks = []
        for net in networks:
            res_network = {}
            res_network["ip_addr"] = net['ip']
            if 'vdev' in net.keys():
                res_network["nic_vdev"] = net['vdev']
            if 'osa' in net.keys():
                res_network["osa_device"] = net['osa']
            res_network.update(common_attributes)
            res_networks.append(res_network)

        content = {"interface": {"os_version": "rhel6.7",
                                 "guest_networks": res_networks}}
        if active:
            content["interface"]["active"] = "True"
        else:
            content["interface"]["active"] = "False"

        body = json.dumps(content)

        if userid is None:
            userid = self.userid
        url = '/guests/%s/interface' % userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _guest_delete_network_interface(self, userid=None, vdev='1000',
                                        active=False):
        content = {"interface": {"os_version": "rhel6.7",
                                 "vdev": vdev}}
        if active:
            content["interface"]["active"] = "True"
        else:
            content["interface"]["active"] = "False"
        body = json.dumps(content)

        if userid is None:
            userid = self.userid
        url = '/guests/%s/interface' % userid
        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        return resp

    def _guest_nic_delete(self, vdev="1000", userid=None, active=False):
        if active:
            body = '{"active": "True"}'
        else:
            body = '{"active": "False"}'
        if userid is None:
            userid = self.userid

        url = '/guests/%s/nic/%s' % (userid, vdev)
        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        return resp

    def _guest_nic_query(self, userid=None):
        if userid is None:
            userid = self.userid

        url = '/guests/%s/nic' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_disks_create_additional(self, userid=None, disk=None):
        if userid is None:
            userid = self.userid

        if disk is None:
            disk = "ECKD:xcateckd"

        body = """{"disk_info": {"disk_list":
                                    [{"size": "1g",
                                      "format": "ext3",
                                      "disk_pool": "%s"},
                                      {"size": "1g",
                                      "format": "ext3",
                                      "disk_pool": "%s"}]}}""" % (disk, disk)
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _guest_disks_create(self, userid=None, disk=None):
        if userid is None:
            userid = self.userid

        if disk is None:
            disk = "ECKD:xcateckd"

        body = """{"disk_info": {"disk_list":
                                    [{"size": "1g",
                                      "disk_pool": "%s"}]}}""" % disk
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _guest_config_minidisk(self, userid=None, disk=None):
        if userid is None:
            userid = self.userid

        if disk is None:
            disk = "0101"

        body = """{"disk_info": {"disk_list":
                                    [{"vdev": "%s",
                                      "format": "ext3",
                                      "mntdir": "/mnt/0101"},
                                     {"vdev": "0102",
                                      "format": "ext3",
                                      "mntdir": "/mnt/0102"}]}}""" % disk
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        return resp

    def _guest_mutidisks_delete(self, userid=None, vdev=None):
        if userid is None:
            userid = self.userid

        body = """{"vdev_info": {"vdev_list": ["0101", "0102"]}}"""
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        return resp

    def _guest_disks_delete(self, userid=None, vdev=None):
        if userid is None:
            userid = self.userid

        if vdev is None:
            vdev = "0101"

        body = """{"vdev_info": {"vdev_list": ["%s"]}}""" % vdev
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        return resp

    def _guest_get(self, userid=None):
        if userid is None:
            userid = self.userid

        url = '/guests/%s' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_get_info(self, userid=None):
        if userid is None:
            userid = self.userid

        url = '/guests/%s/info' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_get_power_state(self, userid=None):
        if userid is None:
            userid = self.userid
        url = '/guests/%s/power_state' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_action(self, body, userid=None):
        if userid is None:
            userid = self.userid
        url = '/guests/%s/action' % userid
        resp = self.client.api_request(url=url,
                                       method='POST', body=body)
        return resp

    def _guest_start(self, userid=None):
        body = '{"action": "start"}'
        return self._guest_action(body, userid=userid)

    def _guest_get_console_output(self, userid=None):
        body = '{"action": "get_console_output"}'
        return self._guest_action(body, userid=userid)

    def _guest_softstop(self, userid=None):
        body = '{"action": "softstop", "timeout": 300, "poll_interval": 20}'
        return self._guest_action(body, userid=userid)

    def _guest_stop(self, userid=None):
        body = '{"action": "stop", "timeout": 300, "poll_interval": 15}'
        return self._guest_action(body, userid=userid)

    def _guest_deploy_with_transport_file(self, userid=None,
                                       vdev=None, image=None,
                                       transportfiles=None):
        if image is None:
            image = '46a4aea3_54b6_4b1c_8a49_01f302e70c60'

        if vdev is None:
            vdev = "100"

        if transportfiles is None:
            transportfiles = "/var/lib/zvmsdk/cfgdrive.tgz"

        body = """{"action": "deploy",
                   "image": "%s",
                   "vdev": "%s",
                   "transportfiles": "%s"}""" % (image, vdev, transportfiles)

        return self._guest_action(body, userid=userid)

    def _guest_deploy(self, userid=None, vdev=None, image=None):
        if image is None:
            image = '46a4aea3_54b6_4b1c_8a49_01f302e70c60'

        if vdev is None:
            vdev = "100"
        # "transportfiles" is None here
        # "remotehost" is None here because transportfiles is None
        body = """{"action": "deploy",
                   "image": "%s",
                   "vdev": "%s"}""" % (image, vdev)

        return self._guest_action(body, userid=userid)

    def _guest_capture(self, userid=None, image=None, capture_type=None,
                       compress_level=None):
        if capture_type is None:
            capture_type = 'rootonly'

        if compress_level is None:
            compress_level = 6
        body = """{"action": "capture",
                   "image": "test_capture_image1",
                   "capture_type": "%s",
                   "compress_level": %d}""" % (capture_type,
                                               compress_level)
        return self._guest_action(body, userid=userid)

    def _guest_pause(self, userid=None):
        body = '{"action": "pause"}'
        return self._guest_action(body, userid=userid)

    def _guest_unpause(self, userid=None):
        body = '{"action": "unpause"}'
        return self._guest_action(body, userid=userid)

    def _guest_reboot(self, userid=None):
        body = '{"action": "reboot"}'
        return self._guest_action(body, userid=userid)

    def _guest_resize_cpus(self, max_cpu, userid=None):
        body = """{"action": "resize_cpus",
                   "cpu_cnt": %s}""" % max_cpu
        return self._guest_action(body, userid=userid)

    def _guest_live_resize_cpus(self, max_cpu, userid=None):
        body = """{"action": "live_resize_cpus",
                   "cpu_cnt": %s}""" % max_cpu
        return self._guest_action(body, userid=userid)

    def is_reachable(self, userid):
        """Reachable through IUCV communication channel."""
        return self._smutclient.get_guest_connection_status(userid)

    def _wait_until(self, expect_state, func, *args, **kwargs):
        """Looping call func until get expected state, otherwise 1 min timeout.

        :param expect_state:    expected state
        :param func:            function or method to be called
        :param *args, **kwargs: parameters for the function
        """
        _inc_slp = [1, 2, 2, 5, 10, 20, 20]
        # sleep intervals, total timeout 60 seconds
        for _slp in _inc_slp:
            real_state = func(*args, **kwargs)
            if real_state == expect_state:
                # sleep another 5 seconds to make sure at expected state
                time.sleep(5)
                return True
            else:
                time.sleep(_slp)

        # timeout
        return False

    def _guest_reset(self, userid=None):
        body = '{"action": "reset"}'
        return self._guest_action(body, userid=userid)

    def _guest_stats(self, userid=None):
        if userid is None:
            userid = self.userid

        url = '/guests/stats?userid=%s' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_vnicsinfo(self, userid=None):
        if userid is None:
            userid = self.userid

        url = '/guests/vnicsinfo?userid=%s' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_get_nic_DB_info(self, userid=None, nic_id=None,
                               vswitch=None):
        if ((userid is None) and
            (nic_id is None) and
            (vswitch is None)):
            append = ''
        else:
            append = "?"
            if userid is not None:
                append += 'userid=%s&' % userid
            if nic_id is not None:
                append += 'nic_id=%s&' % nic_id
            if vswitch is not None:
                append += 'vswitch=%s&' % vswitch
            append = append.strip('&')
        url = '/guests/nics%s' % append
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _image_query(self, image_name='image1'):
        url = '/images?imagename=%s' % image_name
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _image_delete(self):
        url = '/images/test_capture_image1'
        resp = self.client.api_request(url=url,
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)
        return resp

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

        definition = self._guest_get(userid=userid)
        self.assertEqual(200, definition.status_code)

        # Check definition
        for entry in entries:
            if entry not in definition.content:
                return False, ""

        # Continue to check the nic info defined in vswitch table
        resp = self._guest_get_nic_DB_info(userid)
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
        resp = self._guest_get('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_incorrect(self):
        resp = self._guest_get('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_info_not_exist(self):
        resp = self._guest_get_info('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_info_incorrect(self):
        resp = self._guest_get_info('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_power_state_not_exist(self):
        resp = self._guest_get_power_state('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_get_power_state_incorrect(self):
        resp = self._guest_get_power_state('@@@@@')
        self.assertEqual(400, resp.status_code)

    def test_guest_get_start_not_exist(self):
        resp = self._guest_start('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_softstop_not_exist(self):
        resp = self._guest_softstop('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_stop_not_exist(self):
        resp = self._guest_stop('notexist')
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
        resp = self._guest_deploy(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_deploy_vdev_not_exist(self):
        resp = self._guest_deploy(vdev='FFFF')
        self.assertEqual(404, resp.status_code)

    def test_guest_deploy_image_not_exist(self):
        resp = self._guest_deploy(image='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_capture_userid_not_exist(self):
        resp = self._guest_capture(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_pause_not_exist(self):
        resp = self._guest_pause('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_unpause_not_exist(self):
        resp = self._guest_unpause('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_reboot_not_exist(self):
        resp = self._guest_reboot('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_reset_not_exist(self):
        resp = self._guest_reset('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_create_not_exist(self):
        resp = self._guest_nic_create(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_vic_create_not_exist(self):
        resp = self._guest_create_network_interface(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_vic_delete_not_exist(self):
        resp = self._guest_delete_network_interface(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_query_not_exist(self):
        resp = self._guest_nic_query(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_delete_not_exist(self):
        resp = self._guest_nic_delete(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_nic_device_delete_not_exist(self):
        resp = self._guest_nic_delete(vdev='FFFF')
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_create_not_exist(self):
        resp = self._guest_disks_create(userid='notexist')
        self.assertEqual(404, resp.status_code)

    @unittest.skip("Skip until bug/1747591 fixed")
    def test_guest_disk_pool_create_not_exist(self):
        resp = self._guest_disks_create(userid=self.userid_exists,
                                        disk="ECKD:notexist")
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_not_exist(self):
        resp = self._guest_disks_delete(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_device_delete_not_exist(self):
        # disk not exist
        resp = self._guest_disks_delete(userid=self.userid_exists, vdev="FFFF")
        self.assertEqual(200, resp.status_code)

    def test_guest_inspect_not_exist(self):
        # following 200 is expected
        resp = self._guest_stats('notexist')
        self.assertEqual(200, resp.status_code)

        resp = self._guest_vnicsinfo('notexist')
        self.assertEqual(200, resp.status_code)

    def test_guest_inspect_incorrect(self):
        resp = self._guest_stats('@@@@@123456789')
        self.assertEqual(400, resp.status_code)

        resp = self._guest_vnicsinfo('@@@@@123456789')
        self.assertEqual(400, resp.status_code)

    def test_guest_creat_with_profile_notexit(self):
        resp = self._guest_create_with_profile_notexit()
        self.assertEqual(404, resp.status_code)

    def test_guest_create_maxcpu_incorrect(self):
        resp = self._guest_create(maxcpu=0)
        self.assertEqual(400, resp.status_code)
        resp = self._guest_create(maxcpu=65)
        self.assertEqual(400, resp.status_code)

    def test_guest_create_maxmem_incorrect(self):
        resp = self._guest_create(maxmem="11111M")
        self.assertEqual(400, resp.status_code)
        resp = self._guest_create(maxmem="1024K")
        self.assertEqual(400, resp.status_code)
        resp = self._guest_create(maxmem="1024")
        self.assertEqual(400, resp.status_code)

    def test_guest_create_with_profile(self):
        resp = self._guest_create_with_profile()
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)
            resp_create = self._guest_get()
            self.assertEqual(200, resp_create.status_code)
            self.assertTrue('MDISK 0100' in resp_create.content)
            self.assertTrue('MDISK 0101' in resp_create.content)
            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                            self.userid))

            resp = self._guest_get_console_output()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_reboot()
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             self.userid))
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             self.userid))
            resp = self._guest_reset()
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             self.userid))
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             self.userid))
        finally:
            self._guest_delete()

    def test_guest_create_delete(self):
        PURGE_GUEST = PURGE_VSW = PURGE_IMG = 0
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid)
        self.assertEqual(200, resp.status_code)
        PURGE_GUEST = 1

        # sleep 5 seconds to make sure create userid completed
        time.sleep(5)

        self._make_transport_file()
        transport_file = '/var/lib/zvmsdk/cfgdrive.tgz'

        try:
            resp = self._guest_deploy_with_transport_file(userid=userid,
                                           transportfiles=transport_file)
            self.assertEqual(200, resp.status_code)

            # Creating NIC, not active.
            resp = self._guest_nic_create(userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Creating another NIC with fixed vdev.
            resp = self._guest_nic_create("1003", userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1003", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Creating NIC with vdev conflict with defined NIC."
            resp = self._guest_nic_create(vdev="1004", userid=userid)
            self.assertEqual(409, resp.status_code)

            # Creating NIC with nic_id.
            resp = self._guest_nic_create(vdev="1006", nic_id='123456',
                                          userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_get_nic_DB_info(nic_id='123456', userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_info = json.loads(resp.content)['output']
            self.assertEqual("1006", nic_info[0]["interface"])
            self.assertEqual("123456", nic_info[0]["port"])

            # Creating NIC with mac_addr
            resp = self._guest_nic_create(vdev="1009",
                                          userid=userid,
                                          mac_addr='02:00:00:12:34:56')
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1009", mac='123456',
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Creating NIC to active guest when guest is in off status.
            resp = self._guest_nic_create(vdev="1100", active=True,
                                          userid=userid)
            self.assertEqual(409, resp.status_code)

            # Deleting NIC to active guest when guest is in off status.
            resp = self._guest_nic_delete(vdev="1009", active=True,
                                          userid=userid)
            self.assertEqual(409, resp.status_code)
            nic_defined, vsw = self._check_nic("1009", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            # Deleting NIC
            resp = self._guest_nic_delete(vdev="1009", userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1009", userid=userid)
            self.assertFalse(nic_defined)

            # Deleting NIC not existed
            resp = self._guest_nic_delete(vdev="1009", userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_start(userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable, userid))

            # Creating nic to the active guest
            resp = self._guest_nic_create(vdev="1100", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1100", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            resp = self._guest_get(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get', resp.content)

            resp = self._guest_get_info(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_info', resp.content)

            resp = self._guest_get_power_state(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_power_state',
                                       resp.content)

            resp = self._guest_vnicsinfo(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_vnics_info',
                                       resp.content)

            # Creating NIC
            resp = self._guest_nic_create(vdev="2000", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            self._vswitch_create()
            PURGE_VSW = 1

            resp = self._vswitch_couple(userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", vsw="RESTVSW1",
                                               userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual("RESTVSW1", vsw)

            resp = self._vswitch_uncouple(userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertTrue(nic_defined)
            self.assertEqual(None, vsw)

            resp = self._guest_nic_delete(vdev="2000", active=True,
                                          userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("2000", userid=userid)
            self.assertFalse(nic_defined)

            resp = self._guest_pause(userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_unpause(userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_stop(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             userid))

            resp = self._guest_stats(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_stats',
                                       resp.content)

            # Capture a powered off instance will lead to error
            resp = self._guest_capture(userid=userid)
            self.assertEqual(500, resp.status_code)

            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)

            time.sleep(10)
            resp_info = self._guest_get_info(userid=userid)
            self.assertEqual(200, resp_info.status_code)
            resp_content = json.loads(resp_info.content)
            info_off = resp_content['output']
            self.assertEqual('on', info_off['power_state'])
            self.assertNotEqual(info_off['cpu_time_us'], 0)
            self.assertNotEqual(info_off['mem_kb'], 0)

            resp = self._guest_capture(capture_type='alldisks', userid=userid)
            self.assertEqual(501, resp.status_code)

            resp = self._guest_capture(userid=userid)
            self.assertEqual(200, resp.status_code)

            PURGE_IMG = 1

            resp = self._image_query(image_name='test_capture_image1')
            self.assertEqual(200, resp.status_code)

            resp_state = self._guest_get_power_state(userid=userid)
            self.assertEqual(200, resp_state.status_code)
            resp_content = json.loads(resp_state.content)
            self.assertEqual('off', resp_content['output'])
        finally:
            os.system('rm /var/lib/zvmsdk/cfgdrive.tgz')
            if PURGE_GUEST:
                self._guest_delete(userid)
            if PURGE_VSW:
                self._vswitch_delete()
            if PURGE_IMG:
                self._image_delete()

    def test_guest_list(self):
        resp = self.client.api_request(url='/guests')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_list', resp.content)

    def test_guest_disks_create_delete(self):
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid)
        self.assertEqual(200, resp.status_code)

        # another create, to test when we report create duplication error
        resp = self._guest_create(userid=userid)
        self.assertEqual(409, resp.status_code)

        flag1 = False
        flag2 = False

        try:
            resp = self._guest_deploy(userid=userid)
            self.assertEqual(200, resp.status_code)

            # create new disks
            resp = self._guest_disks_create_additional(userid=userid)
            self.assertEqual(200, resp.status_code)
            resp_create = self._guest_get(userid=userid)
            self.assertEqual(200, resp_create.status_code)
            self.assertTrue('MDISK 0101' in resp_create.content)
            self.assertTrue('MDISK 0102' in resp_create.content)
            # config 'MDISK 0101'
            resp_config = self._guest_config_minidisk(userid=userid)
            self.assertEqual(200, resp_config.status_code)

            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             userid))
            time.sleep(10)
            result = self._smutclient.execute_cmd(userid, 'df -h')
            result_list = result

            for element in result_list:
                if '/mnt/0101' in element:
                    flag1 = True
                if '/mnt/0102' in element:
                    flag2 = True
            self.assertEqual(True, flag1)
            self.assertEqual(True, flag2)

            resp = self._guest_softstop(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(False, self.is_reachable,
                                             self.userid))

            # delete new disks
            resp = self._guest_mutidisks_delete(userid=userid)
            self.assertEqual(200, resp.status_code)
            resp_delete = self._guest_get(userid=userid)
            self.assertEqual(200, resp_delete.status_code)
            self.assertTrue('MDISK 0101' not in resp_delete.content)
            self.assertTrue('MDISK 0102' not in resp_delete.content)
        finally:
            self._guest_delete(userid=userid)

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
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid)
        self.assertEqual(200, resp.status_code)
        self._make_transport_file()
        transport_file = '/var/lib/zvmsdk/cfgdrive.tgz'
        ip_addrs = ["192.168.95.123", "192.168.95.124", "192.168.95.125",
                    "192.168.95.126"]

        try:
            resp = self._guest_deploy_with_transport_file(userid=userid,
                                           transportfiles=transport_file)
            self.assertEqual(200, resp.status_code)

            # Case 1: create an interface to couple to vswitch
            resp = self._guest_create_network_interface(userid=userid,
                                            networks=[{'ip': ip_addrs[0],
                                                       'vdev': "1000"}])
            self.assertEqual(200, resp.status_code)

            # Authorizing VM to couple to vswitch.
            body = '{"vswitch": {"grant_userid": "%s"}}' % self.userid
            resp = self.client.api_request(url='/vswitches/XCATVSW2',
                                           method='PUT', body=body)
            self.assertEqual(200, resp.status_code)

            # Coupling NIC to the vswitch.
            resp = self._vswitch_couple(vdev="1000", vswitch="XCATVSW2",
                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("1000", userid, vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)

            # Case 2: create an interface to dedicate osa
            osa = self._get_free_osa()
            self.assertNotEqual(osa, None)
            resp = self._guest_create_network_interface(
                        userid=userid, networks=[{'ip': ip_addrs[1],
                                                  'vdev': '2000',
                                                  'osa': osa}])
            self.assertEqual(200, resp.status_code)

            nic_defined, nic_osa = self._check_nic("2000", userid=userid,
                                                   osa=osa)
            self.assertTrue(nic_defined)
            self.assertEqual(nic_osa, osa)

            # Case 3: create two interfaces together
            resp = self._guest_create_network_interface(userid=userid,
                                            networks=[{'ip': ip_addrs[2],
                                                       'vdev': "3000"},
                                                      {'ip': ip_addrs[3],
                                                       'vdev': "4000"}])
            self.assertEqual(200, resp.status_code)

            # Coupling NIC to the vswitch.
            resp = self._vswitch_couple(vdev="3000", vswitch="XCATVSW2",
                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            resp = self._vswitch_couple(vdev="4000", vswitch="XCATVSW2",
                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            nic_defined, vsw = self._check_nic("3000", userid=userid,
                                               vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)
            nic_defined, vsw = self._check_nic("4000", userid=userid,
                                               vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)

            # Start the guest and check results
            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             userid))
            time.sleep(20)
            for addr in ip_addrs:
                ip_set = self._check_interface(userid=userid, ip=addr)
                self.assertTrue(ip_set)

            # Case: Delete network interface
            resp = self._guest_delete_network_interface(vdev="1000",
                                                        active=True,
                                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[0])
            self.assertFalse(ip_set)
            resp = self._guest_delete_network_interface(vdev="2000",
                                                        active=True,
                                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[1])
            self.assertFalse(ip_set)
            resp = self._guest_delete_network_interface(vdev="3000",
                                                        active=True,
                                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[2])
            self.assertFalse(ip_set)
            resp = self._guest_delete_network_interface(vdev="4000",
                                                        active=True,
                                                        userid=userid)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[3])
            self.assertFalse(ip_set)

            # Case: Re-create with active=True
            resp = self._guest_create_network_interface(userid=userid,
                                            networks=[{'ip': ip_addrs[0],
                                                       'vdev': "1000"}],
                                            active=True)
            self.assertEqual(200, resp.status_code)

            osa = self._get_free_osa()
            self.assertNotEqual(osa, None)
            resp = self._guest_create_network_interface(userid=userid,
                                        networks=[{'ip': ip_addrs[1],
                                                   'vdev': '2000',
                                                  'osa': osa}],
                                        active=True)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_create_network_interface(userid=userid,
                                            networks=[{'ip': ip_addrs[2],
                                                       'vdev': "3000"},
                                                      {'ip': ip_addrs[3],
                                                       'vdev': "4000"}],
                                            active=True)
            self.assertEqual(200, resp.status_code)

            # Coupling NIC to the vswitch.
            resp = self._vswitch_couple(vdev="1000", vswitch="XCATVSW2",
                                        active=True, userid=userid)
            self.assertEqual(200, resp.status_code)
            resp = self._vswitch_couple(vdev="3000", vswitch="XCATVSW2",
                                        userid=userid, active=True)
            self.assertEqual(200, resp.status_code)
            resp = self._vswitch_couple(vdev="4000", vswitch="XCATVSW2",
                                        userid=userid, active=True)
            self.assertEqual(200, resp.status_code)
            # check NICs defined
            nic_defined, vsw = self._check_nic("1000", userid=userid,
                                               vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)
            nic_defined, nic_osa = self._check_nic("2000", userid=userid,
                                                   osa=osa)
            self.assertTrue(nic_defined)
            self.assertEqual(nic_osa, osa)
            nic_defined, vsw = self._check_nic("3000", userid=userid,
                                               vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)
            nic_defined, vsw = self._check_nic("4000", userid=userid,
                                               vsw="XCATVSW2")
            self.assertTrue(nic_defined)
            self.assertEqual("XCATVSW2", vsw)

            # Check IPs are all set in interface
            for addr in ip_addrs:
                ip_set = self._check_interface(userid=userid, ip=addr)
                self.assertTrue(ip_set)

            # Delete interfaces with active=False
            resp = self._guest_delete_network_interface(userid=userid,
                                                        vdev="1000",
                                                        active=False)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[0])
            self.assertTrue(ip_set)
            nic_defined, vsw = self._check_nic("1000", userid=userid)
            self.assertFalse(nic_defined)
            self.assertEqual("", vsw)
            # undedicate OSA
            resp = self._guest_delete_network_interface(userid=userid,
                                                        vdev="2000",
                                                        active=False)
            self.assertEqual(200, resp.status_code)
            ip_set = self._check_interface(userid=userid, ip=ip_addrs[1])
            self.assertTrue(ip_set)
            nic_defined, osa = self._check_nic("2000", userid=userid, osa=osa)
            self.assertFalse(nic_defined)
            self.assertEqual("", osa)
        finally:
            os.system('rm /var/lib/zvmsdk/cfgdrive.tgz')
            self._guest_delete(userid=userid)

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

    def test_guest_create_cpu_memory_userset(self):
        userid = test_utils.generate_test_userid()
        resp = self._guest_create(userid=userid, maxcpu=10, maxmem="2048M")
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy(userid=userid)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_start(userid=userid)
            self.assertEqual(200, resp.status_code)
            self.assertTrue(self._wait_until(True, self.is_reachable,
                                             userid))
            self._check_CPU_MEM(userid, maxcpu=10, maxmem="2048M")
            self._check_total_memory(userid, maxmem="2048M")
        finally:
            self._guest_delete(userid=userid)


class GuestActionTestCase(base.ZVMConnectorBaseTestCase):
    def __init__(self, methodName='runTest'):
        super(GuestActionTestCase, self).__init__(methodName)

    def setUp(self):
        super(GuestActionTestCase, self).setUp()
        self.client = test_sdkwsgi.TestSDKClient()
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
