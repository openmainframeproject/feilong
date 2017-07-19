#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

import unittest

from zvmsdk import config
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


CONF = config.CONF


class ImageTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(ImageTestCase, self).__init__(methodName)

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def _image_create(self):
        image_fname = "image1"
        image_fpath = ''.join([CONF.image.temp_path, image_fname])
        os.system('touch %s' % image_fpath)
        url = "file://" + image_fpath
        image_meta = '{"os_version": "rhel7.2"}'

        body = '{"image": {"url": "%s", "image_meta": %s}}' % (url,
                                                               image_meta)

        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        self.assertEqual(200, resp.status_code)
        return resp

    def _image_delete(self):
        url = '/images/rhel7.2-s390x-netboot-image1'
        resp = self.client.api_request(url=url, method='DELETE')
        self.assertEqual(204, resp.status_code)
        return resp

    def _image_get_root_disk_size(self):
        # Note here we query the image that already exist in the test system
        # it might be changed if the test system is changed
        # another way is to use mkdummyimage to create a dummy image
        url = '/images/'
        url += 'rhel7.2-s390x-netboot-e19708cf_a55b_4f97_b9d5_bab54fa6f94f/'
        url += 'root_disk_size'

        resp = self.client.api_request(url=url, method='GET')
        self.assertEqual(200, resp.status_code)
        return resp

    def _image_query(self):
        resp = self.client.api_request(url='/images?imagename=image1',
                                       method='GET')
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

    def test_image_get_not_valid_resource(self):
        resp = self.client.api_request(url='/images/image1/root')
        self.assertEqual(404, resp.status_code)

    def test_image_create_delete(self):
        self._image_create()

        try:
            self._image_query()
            self._image_get_root_disk_size()
        except Exception:
            raise
        finally:
            # if delete failed, anyway we can't re-delete it because of failure
            self._image_delete()
