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

from zvmsdk import config
from zvmsdk import utils
from zvmsdk.tests.sdkwsgi import api_sample
from zvmsdk.tests.sdkwsgi import test_sdkwsgi


CONF = config.CONF


class ImageTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(ImageTestCase, self).__init__(methodName)

        self.apibase = api_sample.APITestBase()

    def setUp(self):
        self.client = test_sdkwsgi.TestSDKClient()

    def _image_create(self):
        image_fname = "image1"
        image_fpath = ''.join([CONF.image.temp_path, image_fname])
        utils.make_dummy_image(image_fpath)
        url = "file://" + image_fpath
        image_meta = '''{"os_version": "rhel7.2"}'''

        body = """{"image": {"image_name": "%s",
                             "url": "%s",
                             "image_meta": %s}}""" % (image_fname, url,
                                                      image_meta)

        resp = self.client.api_request(url='/images', method='POST',
                                       body=body)
        return resp

    def _image_delete(self):
        url = '/images/image1'
        resp = self.client.api_request(url=url, method='DELETE')
        self.assertEqual(204, resp.status_code)
        return resp

    def _image_get_root_disk_size(self):
        url = '/images/'
        url += 'image1/'
        url += 'root_disk_size'

        resp = self.client.api_request(url=url, method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_get_root_disk_size',
                                   resp.content)
        return resp

    def _image_query(self):
        resp = self.client.api_request(url='/images?imagename=image1',
                                       method='GET')
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_query', resp.content)
        return resp

    def _image_export(self):
        url = '/images/image1'
        dest_url = 'file:///tmp/images/image1'
        body = """{"location": {"dest_url": "%s"}}""" % (dest_url)

        resp = self.client.api_request(url=url,
                                       method='PUT',
                                       body=body)
        self.assertEqual(200, resp.status_code)
        self.apibase.verify_result('test_image_export', resp.content)
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

    def test_image_create_duplicate(self):
        resp = self._image_create()
        self.assertEqual(200, resp.status_code)

        resp = self._image_create()
        self.assertEqual(409, resp.status_code)

    def test_image_create_delete(self):
        self._image_create()

        try:
            self._image_query()
            self._image_get_root_disk_size()
            self._image_export()
        except Exception:
            raise
        finally:
            # if delete failed, anyway we can't re-delete it because of failure
            self._image_delete()
