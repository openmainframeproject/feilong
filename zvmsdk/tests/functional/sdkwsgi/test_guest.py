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


class GuestTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(GuestTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def test_guest_list(self):
        resp = self.client.api_request(url='/guest')
        self.assertEqual(200, resp.status_code)

    def _test_guest_start(self):
        resp = self.client.api_request(url='/guest', method='POST')
        self.assertEqual(200, resp.status_code)

        uuid = resp['uuid']
        resp = self.client.api_request()
        self.assertEqual(200, resp.status_code)

    def _test_guest_create(self):
        resp = self.client.api_request(url='/guest', method='POST')
        self.assertEqual(200, resp.status_code)
