#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import unittest

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


class GuestHandlerTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestHandlerTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        self.client = test_sdkwsgi.TestSDKClient()
        self._cleanup()

    def _cleanup(self):
        self.client.api_request(url='/guests/RESTT100',
                                method='DELETE')

        self.client.api_request(url='/vswitchs/restvsw1',
                                method='DELETE')

    def setUp(self):
        pass

    def _guest_create(self):
        body = """{"guest": {"userid": "RESTT100", "vcpus": 1,
                             "memory": 1024,
                             "disk_list": [{"size": "3g"}]}}"""
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_delete(self):
        resp = self.client.api_request(url='/guests/RESTT100',
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_nic_create(self, vdev="1000"):
        body = '{"nic": {"vdev": "%s"}}' % vdev

        resp = self.client.api_request(url='/guests/RESTT100/nic',
                                       method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _guest_nic_delete(self, vdev="1000"):
        body = '{"nic": {}}'
        resp = self.client.api_request(url='/guests/RESTT100/nic/2000',
                                       method='DELETE',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _guest_get(self):
        resp = self.client.api_request(url='/guests/RESTT100',
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        return resp

    def _guest_get_info(self):
        resp = self.client.api_request(url='/guests/RESTT100/info',
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        return resp

    def _guest_get_power_state(self):
        resp = self.client.api_request(url='/guests/RESTT100/power_state',
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        return resp

    def _guest_action(self, body):
        resp = self.client.api_request(url='/guests/RESTT100/action',
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
        image = 'rhel7.2-s390x-netboot-e19708cf_a55b_4f97_b9d5_bab54fa6f94f'
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
        resp = self.client.api_request(url='/guests/cpuinfo?userid=RESTT100',
                                       method='GET')
        self.assertEqual(200, resp.status_code)

    def _guest_meminfo(self):
        resp = self.client.api_request(url='/guests/meminfo?userid=RESTT100',
                                       method='GET')
        self.assertEqual(200, resp.status_code)

    def _guest_vnicsinfo(self):
        resp = self.client.api_request(url='/guests/vnicsinfo?userid=RESTT100',
                                       method='GET')
        self.assertEqual(200, resp.status_code)

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

            # self._guest_stop()
            # self._guest_start()

        except Exception as e:
            raise e
        finally:
            pass
            # self._guest_delete()

    def test_guest_list(self):
        resp = self.client.api_request(url='/guests')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_list', resp.content)

    def _vswitch_create(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitchs', method='POST',
                                       body=body)
        self.assertEqual(204, resp.status_code)

    def _vswitch_delete(self):
        resp = self.client.api_request(url='/vswitchs/restvsw1',
                                       method='DELETE')
        self.assertEqual(204, resp.status_code)

    def _vswitch_couple(self):
        body = '{"info": {"couple": "True", "vswitch": "RESTVSW1"}}'
        resp = self.client.api_request(url='/guests/RESTT100/nic/2000',
                                       method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def _vswitch_uncouple(self):
        body = '{"info": {"couple": "False"}}'
        resp = self.client.api_request(url='/guests/RESTT100/nic/2000',
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
