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
import unittest

from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi

from zvmsdk import log


LOG = log.LOG


class VSwitchTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(VSwitchTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()

        self.client = test_sdkwsgi.TestSDKClient()
        self._cleanup()

    def _cleanup(self):
        self.client.api_request(url='/vswitchs/RESTVSW1',
                                method='DELETE')

    def setUp(self):
        pass

    def _vswitch_list(self):
        resp = self.client.api_request(url='/vswitchs', method='GET')
        self.assertEqual(200, resp.status_code)

        return resp

    def test_vswitch_list(self):
        resp = self._vswitch_list()
        self.apibase.verify_result('test_vswitch_get', resp.content)

    def test_vswitch_create_delete(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitchs', method='POST',
                                       body=body)
        self.assertEqual(204, resp.status_code)

        resp = self._vswitch_list()
        vswlist = json.loads(resp.content)['vswlist']
        inlist = 'RESTVSW1' in vswlist
        self.assertTrue(inlist)

        resp = self.client.api_request(url='/vswitchs/restvsw1',
                                       method='DELETE')
        self.assertEqual(204, resp.status_code)

        resp = self._vswitch_list()
        vswlist = json.loads(resp.content)['vswlist']
        inlist = 'RESTVSW1' in vswlist
        self.assertFalse(inlist)

    def test_vswitch_update(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitchs', method='POST',
                                       body=body)
        self.assertEqual(204, resp.status_code)

        body = '{"vswitch": {"grant_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitchs/RESTVSW1',
                                       method='PUT', body=body)
        self.assertEqual(200, resp.status_code)

        resp = self.client.api_request(url='/vswitchs/RESTVSW1',
                                       method='DELETE')
        self.assertEqual(204, resp.status_code)

    def test_vswitch_create_invalid_body(self):
        body = '{"vswitch": {"v1": "v1"}}'
        resp = self.client.api_request(url='/vswitchs', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_vswitch_create_nobody(self):
        resp = self.client.api_request(url='/vswitchs', method='POST')
        self.assertEqual(400, resp.status_code)
