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

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


class GuestHandlerTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestHandlerTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        self.client = test_sdkwsgi.TestSDKClient()

        # every time, we need to random generate userid
        self.userid = 'RESTT%03d' % (time.time() % 1000)
        self._cleanup()

    def _cleanup(self):
        url = '/guests/%s' % self.userid
        self.client.api_request(url=url, method='DELETE')

        self.client.api_request(url='/vswitchs/restvsw1',
                                method='DELETE')

    def setUp(self):
        pass

    def _guest_create(self):
        body = """{"guest": {"userid": "%s", "vcpus": 1,
                             "memory": 1024,
                             "disk_list": [{"size": "3g"}]}}"""
        body = body % self.userid
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)

        return resp

    def _guest_delete(self):
        url = '/guests/%s' % self.userid
        resp = self.client.api_request(url=url, method='DELETE')
        self.assertEqual(204, resp.status_code)

        return resp

    def _guest_nic_create(self, vdev="1000"):
        body = '{"nic": {"vdev": "%s"}}' % vdev

        url = '/guests/%s/nic' % self.userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _guest_create_network_interface(self):
        body = """{"interface": {"os_version": "rhel6",
                                 "guest_networks":
                                    [{"ip_addr": "192.168.98.123",
                                     "dns_addr": ["9.0.3.1"],
                                     "gateway_addr": "192.168.98.1",
                                     "cidr": "192.168.98.0/24",
                                     "nic_vdev": "1000",
                                     "mac_addr": "02:00:00:12:34:56"}]}}"""
        url = '/guests/%s/interface' % self.userid
        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _guest_nic_delete(self, vdev="1000"):
        body = '{"nic": {}}'
        url = '/guests/%s/nic/%s' % (self.userid, vdev)
        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        self.assertEqual(204, resp.status_code)

    def _guest_nic_query(self):
        url = '/guests/%s/nic' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get_nic', resp.content)
        return resp

    def _guest_disks_create(self):
        body = """{"disk_info": {"disk_list":
                                    [{"size": "1g",
                                      "disk_pool": "ECKD:xcateckd"}]}}"""
        url = '/guests/%s/disks' % self.userid

        resp = self.client.api_request(url=url,
                                       method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _guest_disks_delete(self):
        body = """{"vdev_info": {"vdev_list": ["0101"]}}"""
        url = '/guests/%s/disks' % self.userid

        resp = self.client.api_request(url=url,
                                       method='DELETE',
                                       body=body)
        self.assertEqual(204, resp.status_code)

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

    def _guest_stop(self, userid=None):
        body = '{"action": "stop"}'
        return self._guest_action(body, userid=userid)

    def _guest_deploy(self, userid=None):
        image = '46a4aea3_54b6_4b1c_8a49_01f302e70c60'
        # "transportfiles" is None here
        # "remotehost" is None here because transportfiles is None
        body = """{"action": "deploy",
                   "image": "%s",
                   "vdev": "100"}""" % image

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

    def _guest_cpuinfo(self, userid=None):
        if userid is None:
            userid = self.userid
        url = '/guests/cpuinfo?userid=%s' % userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        return resp

    def _guest_meminfo(self, userid=None):
        if userid is None:
            userid = self.userid
        url = '/guests/meminfo?userid=%s' % userid
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

    def test_guest_update_not_exist(self):
        resp = self._guest_get('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_get_info('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_get_power_state('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_start('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_stop('notexist')
        # FIXME
        self.assertEqual(200, resp.status_code)

        resp = self._guest_deploy('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_pause('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_unpause('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_reboot('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_reset('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_cpuinfo('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_meminfo('notexist')
        self.assertEqual(404, resp.status_code)

        resp = self._guest_vnicsinfo('notexist')
        self.assertEqual(404, resp.status_code)

    def test_guest_create_delete(self):
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        # give chance to make disk online
        time.sleep(15)

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)

            self._guest_nic_create()

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

            resp = self._guest_cpuinfo()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_cpu_info',
                                       resp.content)

            resp = self._guest_meminfo()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_memory_info',
                                       resp.content)

            resp = self._guest_vnicsinfo()
            self.assertEqual(200, resp.status_code)
            self.apibase.verify_result('test_guests_get_vnics_info',
                                       resp.content)

            self._guest_nic_create("2000")

            self._vswitch_create()

            self._vswitch_couple()

            self._vswitch_uncouple()

            self._guest_nic_delete()

            resp = self._guest_stop()
            self.assertEqual(200, resp.status_code)

            # FIXME need further enhancement to test start
            # the action is supported, but need add IPL param etc
            # self._guest_start()

            # self._guest_pause()
            # self._guest_unpause()

        except Exception as e:
            raise e
        finally:
            self._guest_delete()
            self._vswitch_delete()

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

        try:
            self._guest_deploy()
            self._guest_nic_create()
            # create new disks
            self._guest_disks_create()
            resp_create = self._guest_get()
            self.assertEqual(200, resp_create.status_code)

            # delete new disks
            self._guest_disks_delete()
            resp_delete = self._guest_get()
            self.assertEqual(200, resp_delete.status_code)

            self.assertTrue('MDISK 0101' in resp_create.content)
            self.assertTrue('MDISK 0101' not in resp_delete.content)
        except Exception as e:
            raise e
        finally:
            self._guest_delete()
            self._vswitch_delete()

    def test_guest_create_network_interface(self):
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        try:
            resp = self._guest_deploy()
            self.assertEqual(200, resp.status_code)

            self._guest_create_network_interface()
        except Exception as e:
            raise e
        finally:
            self._guest_delete()
            self._vswitch_delete()

    def _vswitch_create(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitchs', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _vswitch_delete(self):
        resp = self.client.api_request(url='/vswitchs/restvsw1',
                                       method='DELETE')
        self.assertEqual(204, resp.status_code)

    def _vswitch_couple(self):
        body = '{"info": {"couple": "True", "vswitch": "RESTVSW1"}}'
        url = '/guests/%s/nic/2000' % self.userid
        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _vswitch_uncouple(self):
        body = '{"info": {"couple": "False"}}'
        url = '/guests/%s/nic/2000' % self.userid
        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_vswitch_couple_uncouple(self):
        resp = self._guest_create()
        self.assertEqual(200, resp.status_code)

        try:
            self._guest_nic_create("2000")

            self._vswitch_create()

            self._vswitch_couple()

            self._vswitch_uncouple()

            self._guest_nic_query()

            self._guest_nic_delete()

        except Exception as e:
            raise e
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
