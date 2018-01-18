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
        self._vswitch_delete()

    def setUp(self):
        pass

    def _vswitch_list(self):
        resp = self.client.api_request(url='/vswitches', method='GET')
        self.assertEqual(200, resp.status_code)

        return resp

    def test_vswitch_list(self):
        resp = self._vswitch_list()
        self.apibase.verify_result('test_vswitch_get', resp.content)

    def _vswitch_create(self):
        body = '{"vswitch": {"name": "RESTVSW1", "rdev": "FF00"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        return resp

    def _vswitch_delete(self):
        resp = self.client.api_request(url='/vswitches/restvsw1',
                                       method='DELETE')
        return resp

    def _vswitch_query(self):
        resp = self.client.api_request(url='/vswitches/restvsw1',
                                       method='GET')
        return resp

    def test_vswitch_create_query_delete(self):
        resp = self._vswitch_create()
        self.assertEqual(200, resp.status_code)

        # Try to create another vswitch, this should fail
        resp = self._vswitch_create()
        self.assertEqual(409, resp.status_code)

        try:
            resp = self._vswitch_list()
            vswlist = json.loads(resp.content)['output']
            inlist = 'RESTVSW1' in vswlist
            self.assertTrue(inlist)

            resp = self._vswitch_query()
            vswinfo = json.loads(resp.content)['output']
            switch_name = vswinfo['switch_name']
            self.assertEqual(switch_name, 'RESTVSW1')
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

            # Try to delete again, currently ignore not exist error
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

            resp = self._vswitch_list()
            vswlist = json.loads(resp.content)['output']
            inlist = 'RESTVSW1' in vswlist
            self.assertFalse(inlist)

    def test_vswitch_update(self):
        resp = self._vswitch_create()
        self.assertEqual(200, resp.status_code)

        try:
            body = '{"vswitch": {"grant_userid": "FVTUSER1"}}'
            resp = self.client.api_request(url='/vswitches/RESTVSW1',
                                           method='PUT', body=body)
            self.assertEqual(200, resp.status_code)
        finally:
            resp = self._vswitch_delete()
            self.assertEqual(200, resp.status_code)

    def test_vswitch_delete_update_query_not_exist(self):
        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='DELETE')
        self.assertEqual(200, resp.status_code)

        # Test update the vswitch not found
        body = '{"vswitch": {"grant_userid": "FVTUSER1"}}'
        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='PUT', body=body)
        self.assertEqual(404, resp.status_code)

        resp = self.client.api_request(url='/vswitches/notexist',
                                       method='GET')
        self.assertEqual(404, resp.status_code)

    def test_vswitch_create_invalid_body(self):
        body = '{"vswitch": {"v1": "v1"}}'
        resp = self.client.api_request(url='/vswitches', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_vswitch_create_nobody(self):
        resp = self.client.api_request(url='/vswitches', method='POST')
        self.assertEqual(400, resp.status_code)
