#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time
import unittest
import json
import os

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi
from zvmsdk import config
from zvmsdk import smutclient

CONF = config.CONF


class GuestHandlerTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestHandlerTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        self.client = test_sdkwsgi.TestSDKClient()

        self._smutclient = smutclient.get_smutclient()

        # every time, we need to random generate userid
        self.userid = 'RESTT%03d' % (time.time() % 1000)
        self._cleanup()

    def _cleanup(self):
        url = '/guests/%s' % self.userid
        self.client.api_request(url=url, method='DELETE')

        self.client.api_request(url='/vswitches/restvsw1',
                                method='DELETE')

    def setUp(self):
        pass

    def _guest_create(self):
        body = """{"guest": {"userid": "%s", "vcpus": 1,
                             "memory": 1024,
                             "disk_list": [{"size": "1100",
                                            "is_boot_disk": "True"}]}}"""
        body = body % self.userid
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

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
                             "disk_list": [{"size": "3g",
                                            "is_boot_disk": "True"},
                                            {"size": "3g"}]}}"""
        user_profile = 'notexist'
        body = body % (self.userid, user_profile)
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

    def _guest_delete(self):
        url = '/guests/%s' % self.userid
        resp = self.client.api_request(url=url, method='DELETE')
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_nic_create(self, vdev="1000", userid=None):
        body = '{"nic": {"vdev": "%s"}}' % vdev
        if userid is None:
            userid = self.userid

        url = '/guests/%s/nic' % userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _guest_create_network_interface(self, userid=None):
        body = """{"interface": {"os_version": "rhel6",
                                 "guest_networks":
                                    [{"ip_addr": "192.168.98.123",
                                     "dns_addr": ["9.0.3.1"],
                                     "gateway_addr": "192.168.98.1",
                                     "cidr": "192.168.98.0/24",
                                     "nic_vdev": "1000",
                                     "mac_addr": "02:00:00:12:34:56"}],
                                 "active": "False"}}"""
        if userid is None:
            userid = self.userid
        url = '/guests/%s/interface' % userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        return resp

    def _guest_delete_network_interface(self, userid=None):
        body = """{"interface": {"os_version": "rhel6",
                                 "vdev": "1000",
                                 "active": "False"}}"""
        if userid is None:
            userid = self.userid
        url = '/guests/%s/interface' % userid
        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        return resp

    def _guest_nic_delete(self, vdev="1000", userid=None):
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
                                      "disk_pool": "%s"}]}}""" % disk
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
                                      "mntdir": "/mnt/0101"}]}}""" % disk
        url = '/guests/%s/disks' % userid

        resp = self.client.api_request(url=url,
                                       method='PUT',
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

    def _guest_softstop(self, userid=None):
        body = '{"action": "softstop", "timeout": 300, "poll_interval": 20}'
        return self._guest_action(body, userid=userid)

    def _guest_stop(self, userid=None):
        body = '{"action": "stop", "timeout": 300, "poll_interval": 15}'
        return self._guest_action(body, userid=userid)

    def _guest_deploy_with_transport_file(self, userid=None, vdev=None,
                                          image=None, transportfiles=None):
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

    def _guest_deploy_with_transprot_file(self, userid=None,
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

    def test_guest_disk_pool_create_not_exist(self):
        resp = self._guest_disks_create(disk="ECKD:notexist")
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_delete_not_exist(self):
        resp = self._guest_disks_delete(userid='notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_disk_device_delete_not_exist(self):
        # disk not exist
        resp = self._guest_disks_delete(vdev="FFFF")
        self.assertEqual(404, resp.status_code)

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

    def test_guest_create_with_profile(self):
        resp = self._guest_create_with_profile()
        self.assertEqual(200, resp.status_code)
        time.sleep(20)

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)
            resp_create = self._guest_get()
            self.assertEqual(200, resp_create.status_code)
            self.assertTrue('MDISK 0100' in resp_create.content)
            self.assertTrue('MDISK 0101' in resp_create.content)
        finally:
            self._guest_delete()

    def test_guest_create_delete(self):
        PURGE_GUEST = PURGE_VSW = PURGE_IMG = 0
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)
        PURGE_GUEST = 1

        # give chance to make disk online
        time.sleep(15)

        self._make_transport_file()
        transport_file = '/var/lib/zvmsdk/cfgdrive.tgz'

        try:
            resp = self._guest_deploy_with_transprot_file(
                                           transportfiles=transport_file)
            self.assertEqual(200, resp.status_code)

            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)

            time.sleep(15)
            result = self._smutclient.execute_cmd(self.userid, 'hostname')
            self.assertEqual('deploy_tests', result[0])

            resp = self._guest_nic_create()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_get()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get', resp.content)

            resp = self._guest_get_info()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_info', resp.content)

            resp = self._guest_get_power_state()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_power_state',
                                       resp.content)

            resp = self._guest_vnicsinfo()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_vnics_info',
                                       resp.content)

            resp = self._guest_nic_create("2000")
            self.assertEqual(200, resp.status_code)

            self._vswitch_create()
            PURGE_VSW = 1

            resp = self._vswitch_couple()
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_uncouple()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_nic_delete()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_pause()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_unpause()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_stop()
            self.assertEqual(200, resp.status_code)

            time.sleep(10)
            resp_state = self._guest_get_power_state()
            self.assertEqual(200, resp_state.status_code)
            resp_content = json.loads(resp_state.content)
            self.assertEqual('off', resp_content['output'])

            resp = self._guest_stats()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_stats',
                                       resp.content)

            # Capture a powered off instance will lead to error
            resp = self._guest_capture()
            self.assertEqual(500, resp.status_code)

            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)

            time.sleep(10)
            resp_info = self._guest_get_info()
            self.assertEqual(200, resp_info.status_code)
            resp_content = json.loads(resp_info.content)
            info_off = resp_content['output']
            self.assertEqual('on', info_off['power_state'])
            self.assertNotEqual(info_off['cpu_time_us'], 0)
            self.assertNotEqual(info_off['mem_kb'], 0)

            resp = self._guest_capture(capture_type='alldisks')
            self.assertEqual(500, resp.status_code)

            resp = self._guest_capture()
            self.assertEqual(200, resp.status_code)

            PURGE_IMG = 1

            resp = self._image_query(image_name='test_capture_image1')
            self.assertEqual(200, resp.status_code)

            resp_state = self._guest_get_power_state()
            self.assertEqual(200, resp_state.status_code)
            resp_content = json.loads(resp_state.content)
            self.assertEqual('off', resp_content['output'])
        finally:
            os.system('rm /var/lib/zvmsdk/cfgdrive.tgz')
            if PURGE_GUEST:
                self._guest_delete()
            if PURGE_VSW:
                self._vswitch_delete()
            if PURGE_IMG:
                self._image_delete()

    def test_guest_list(self):
        resp = self.client.api_request(url='/guests')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_list', resp.content)

    def test_guest_disks_create_delete(self):
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        # another create, to test when we report create duplication error
        resp = self._guest_create()
        self.assertEqual(409, resp.status_code)

        # give chance to make disk online
        time.sleep(15)
        flag = False

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_nic_create()
            self.assertEqual(200, resp.status_code)
            # create new disks
            resp = self._guest_disks_create()
            self.assertEqual(200, resp.status_code)

            resp_create = self._guest_get()
            self.assertEqual(200, resp_create.status_code)

            # delete new disks
            resp = self._guest_disks_delete()
            self.assertEqual(200, resp.status_code)

            resp_delete = self._guest_get()
            self.assertEqual(200, resp_delete.status_code)

            self.assertTrue('MDISK 0101' in resp_create.content)
            self.assertTrue('MDISK 0101' not in resp_delete.content)

            # create new disks
            resp = self._guest_disks_create_additional()
            self.assertEqual(200, resp.status_code)
            resp_create = self._guest_get()
            self.assertEqual(200, resp_create.status_code)
            self.assertTrue('MDISK 0101' in resp_create.content)
            # config 'MDISK 0101'
            resp_config = self._guest_config_minidisk()
            self.assertEqual(200, resp_config.status_code)

            resp = self._guest_start()
            self.assertEqual(200, resp.status_code)
            time.sleep(15)
            result = self._smutclient.execute_cmd(self.userid, 'df -h')
            result_list = result
            for element in result_list:
                if '/mnt/0101' in element:
                    flag = True
            self.assertTrue(True, flag)

            resp = self._guest_softstop()
            self.assertEqual(200, resp.status_code)
            time.sleep(10)
            resp_state = self._guest_get_power_state()
            self.assertEqual(200, resp_state.status_code)
            resp_content = json.loads(resp_state.content)
            self.assertEqual('off', resp_content['output'])
        finally:
            self._guest_delete()
            self._vswitch_delete()

    def test_guest_create_delete_network_interface(self):
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_create_network_interface()
            self.assertEqual(200, resp.status_code)
            resp = self._guest_delete_network_interface()
            self.assertEqual(200, resp.status_code)
        finally:
            self._guest_delete()
            self._vswitch_delete()

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

    def _vswitch_create(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        return resp

    def _vswitch_delete(self):
        resp = self.client.api_request(url='/vswitches/restvsw1',
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

    def _vswitch_couple(self, vswitch=None, userid=None):
        body = '{"info": {"couple": "True", "vswitch": "%s"}}' % vswitch
        if not userid:
            userid = self.userid

        if not vswitch:
            vswitch = "RESTVSW1"

        url = '/guests/%s/nic/2000' % userid
        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        return resp

    def _vswitch_uncouple(self, userid=None):
        body = '{"info": {"couple": "False"}}'
        if not userid:
            userid = self.userid

        url = '/guests/%s/nic/2000' % userid
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
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_nic_create("2000")
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_create()
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_couple()
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_uncouple()
            self.assertEqual(200, resp.status_code)

            resp = self._guest_nic_query()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guest_get_nic', resp.content)

            resp = self._guest_nic_delete()
            self.assertEqual(200, resp.status_code)
        finally:
            self._guest_delete()
            self._vswitch_delete()


class GuestActionTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestActionTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

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
