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
        self.assertEqual(200, resp.status_code)

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
        self.assertEqual(200, resp.status_code)

    def _guest_get(self):
        url = '/guests/%s' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get', resp.content)
        return resp

    def _guest_get_info(self):
        url = '/guests/%s/info' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get_info', resp.content)
        return resp

    def _guest_get_power_state(self):
        url = '/guests/%s/power_state' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guest_get_power_state',
                                   resp.content)
        return resp

    def _guest_action(self, body):
        url = '/guests/%s/action' % self.userid
        resp = self.client.api_request(url=url,
                                       method='POST', body=body)
        self.assertEqual(200, resp.status_code)
        return resp

    def _guest_start(self):
        body = '{"action": "start"}'
        return self._guest_action(body)

    def _guest_stop(self):
        body = '{"action": "stop"}'
        return self._guest_action(body)

    def _guest_deploy(self):
        image = '46a4aea3_54b6_4b1c_8a49_01f302e70c60'
        # "transportfiles" is None here
        # "remotehost" is None here because transportfiles is None
        body = """{"action": "deploy",
                   "image": "%s",
                   "vdev": "100"}""" % image

        return self._guest_action(body)

    def _guest_pause(self):
        body = '{"pause": "none"}'
        return self._guest_action(body)

    def _guest_unpause(self):
        body = '{"unpause": "none"}'
        return self._guest_action(body)

    def _guest_cpuinfo(self):
        url = '/guests/cpuinfo?userid=%s' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_cpu_info',
                                   resp.content)

    def _guest_meminfo(self):
        url = '/guests/meminfo?userid=%s' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_memory_info',
                                   resp.content)

    def _guest_vnicsinfo(self):
        url = '/guests/vnicsinfo?userid=%s' % self.userid
        resp = self.client.api_request(url=url,
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_get_vnics_info',
                                   resp.content)

    def test_guest_create_delete(self):
        self._guest_create()

        try:
            self._guest_deploy()

            self._guest_nic_create()

            self._guest_get()

            self._guest_get_info()

            self._guest_get_power_state()

            self._guest_cpuinfo()
            self._guest_meminfo()
            self._guest_vnicsinfo()

            self._guest_nic_create("2000")

            self._vswitch_create()

            self._vswitch_couple()

            self._vswitch_uncouple()

            self._guest_nic_delete()

            self._guest_stop()

            # FIXME need further enhancement to test start
            # the action is supported, but need add IPL param etc
            # self._guest_start()

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
        self._guest_create()
        try:
            self._guest_deploy()
            self._guest_nic_create()
            # create new disks
            self._guest_disks_create()
            resp_create = self._guest_get()
            # delete new disks
            self._guest_disks_delete()
            resp_delete = self._guest_get()

            self.assertTrue('MDISK 0101' in resp_create.content)
            self.assertTrue('MDISK 0101' not in resp_delete.content)
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
        self._guest_create()

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
