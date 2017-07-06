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

from zvmsdk.tests.sdkwsgi import test_sdkwsgi


class ImageTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(ImageTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def _image_create(self):
        body = '{"image": {"uuid": "1"}}'
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)
        return resp

    def _image_delete(self):
        resp = self.client.api_request(url='/images/1', method='DELETE')
        self.assertEqual(200, resp.status_code)
        return resp

    def test_image_create_empty_body(self):
        body = {}
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_image_create_invalid_body(self):
        body = '{"dummy": {"uuid": "1"}}'
        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(400, resp.status_code)

    def test_image_get_root_disk_size(self):
        resp = self.client.api_request(url='/images/image1/root_disk_size')
        self.assertEqual(200, resp.status_code)

    def test_image_get_not_valid_resource(self):
        resp = self.client.api_request(url='/images/image1/root')
        self.assertEqual(404, resp.status_code)

    def _test_image_create_delete(self):
        self._image_create()

        # if delete failed, anyway we can't re-delete it because of failure
        self._image_delete()

    def _test_image_query(self):
        self._image_create()

        resp = self.client.api_request(url='/images/1', method='GET')
        self.assertEqual(200, resp.status_code)
