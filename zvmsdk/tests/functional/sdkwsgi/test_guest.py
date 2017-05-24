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

from zvmsdk.tests.functional.sdkwsgi import test_sdkwsgi


class GuestHandlerTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestHandlerTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def test_guest_list(self):
        resp = self.client.api_request(url='/guest')
        self.assertEqual(200, resp.status_code)


class GuestActionTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestActionTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def test_guest_start(self):
        body = '{"start": "none"}'
        resp = self.client.api_request(url='/guest/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_stop(self):
        body = '{"stop": "none"}'
        resp = self.client.api_request(url='/guest/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_pause(self):
        body = '{"pause": "none"}'
        resp = self.client.api_request(url='/guest/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_unpause(self):
        body = '{"unpause": "none"}'
        resp = self.client.api_request(url='/guest/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)

    def test_guest_get_console_output(self):
        body = '{"get_conole_output": "none"}'
        resp = self.client.api_request(url='/guest/1/action', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)
