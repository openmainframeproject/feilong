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

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def _guest_create(self):
        body = """{"guest": {"userid": "RESTT100", "vcpus": 1,
                             "memory": 1024}}"""
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_delete(self):
        resp = self.client.api_request(url='/guests/RESTT100',
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

        return resp

    def _guest_nic_create(self):
        body = '{"nic": {}}'
        resp = self.client.api_request(url='/guests/RESTT100/nic',
                                       method='POST',
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

    def test_guest_create_delete(self):
        self._guest_create()
        self._guest_nic_create()

        resp = self._guest_get()
        print resp

        resp = self._guest_get_info()
        print resp

        resp = self._guest_get_power_state()
        print resp

        self._guest_delete()

    def test_guest_create_invalid_param(self):
        body = '{"guest1": {"userid": "name1"}}'
        resp = self.client.api_request(url='/guests', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_guest_create_nic_invalid_param(self):
        body = '{"nic1": {"nic_info": [{"nic_id": "c"}]}}'
        resp = self.client.api_request(url='/guests/1/nic', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_guest_get_nic(self):
        resp = self.client.api_request(url='/guests/1/nic', method='GET')
        self.assertEqual(200, resp.status_code)

    def test_guest_list(self):
        resp = self.client.api_request(url='/guests')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_guests_list', resp.content)

    # FIXME after function test ready
    def _test_guest_couple_uncouple(self):
        body = '{"info": {"couple": "True", "vswitch": "v1", "port": "p1"}'
        resp = self.client.api_request(url='/guests/1/nic', method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)

        body = '{"info": {"couple": "False", "vswitch": "v1", "port": "p1"}'
        resp = self.client.api_request(url='/guests/1/nic', method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_couple_uncouple_invalid(self):
        body = '{"info1": {"couple": "True", "vswitch": "v1", "port": "p1"}'
        resp = self.client.api_request(url='/guests/1/nic', method='PUT',
                                       body=body)
        self.assertEqual(400, resp.status_code)

        body = '{"info": {"couple": "False", "vswitch": "v1"}'
        resp = self.client.api_request(url='/guests/1/nic', method='PUT',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_guest_get_info(self):
        resp = self.client.api_request(url='/guests/1/info', method='GET')
        self.assertEqual(200, resp.status_code)

    def test_guest_get_power_state(self):
        resp = self.client.api_request(url='/guests/1/power_state',
                                       method='GET')
        self.assertEqual(200, resp.status_code)


class GuestActionTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestActionTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def test_guest_start(self):
        body = '{"start": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_stop(self):
        body = '{"stop": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_pause(self):
        body = '{"pause": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_unpause(self):
        body = '{"unpause": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_get_console_output(self):
        body = '{"get_conole_output": "none"}'
        resp = self.client.api_request(url='/guests/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

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
