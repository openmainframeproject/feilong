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

from zvmsdk.sdkwsgi import util


class SDKWsgiUtilsTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(SDKWsgiUtilsTestCase, self).__init__(methodName)

    def test_get_http_code_from_sdk_return(self):
        msg = {}
        msg['overallRC'] = 404
        ret = util.get_http_code_from_sdk_return(msg, default=201)
        self.assertEqual(404, ret)

        msg['overallRC'] = 400
        ret = util.get_http_code_from_sdk_return(msg)
        self.assertEqual(400, ret)

        msg['overallRC'] = 100
        ret = util.get_http_code_from_sdk_return(msg, default=200)
        self.assertEqual(400, ret)

        msg['overallRC'] = 0
        ret = util.get_http_code_from_sdk_return(msg, default=204)
        self.assertEqual(204, ret)

        msg['overallRC'] = 300
        ret = util.get_http_code_from_sdk_return(msg, default=201)
        self.assertEqual(500, ret)
