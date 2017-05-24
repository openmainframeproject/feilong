#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import unittest

from zvmsdk.tests.functional.sdkwsgi import test_sdkwsgi


class HostTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(HostTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def test_host_list(self):
        resp = self.client.api_request(url='/host/host1')
        self.assertEqual(200, resp.status_code)

    def test_host_info(self):
        resp = self.client.api_request(url='/host/host1/info')
        self.assertEqual(200, resp.status_code)

    def test_host_disk_info(self):
        resp = self.client.api_request(url='/host/host1/disk_info/disk1')
        self.assertEqual(200, resp.status_code)
