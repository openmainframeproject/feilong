#    licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Handler for the image of the sdk API."""

from zvmsdk import api
from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import image
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper

_IMAGEACTION = None
CONF = config.CONF
LOG = log.LOG


class ImageAction(object):

    def __init__(self):
        self.api = api.SDKAPI()

    @validation.schema(image.create)
    def create(self, body):
        pass
        # image = body['image']
        # url = image['url']
        # remote_host = image.get('remote_host', None)
        # image_meta = image.get('image_meta', None)
        # self.api.image_import(url, image_meta, remote_host)

    def get_root_disk_size(self, name):
        LOG.info('get root disk size')

    def delete(self, name):
        self.api.image_delete(name)

    def query(self, imagename):
        LOG.info('image query %s', imagename)


def get_action():
    global _IMAGEACTION
    if _IMAGEACTION is None:
        _IMAGEACTION = ImageAction()
    return _IMAGEACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_create(req):

    def _image_create(req):
        action = get_action()
        body = util.extract_json(req.body)
        action.create(body=body)

    _image_create(req)

    req.response.status = 204
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_get_root_disk_size(req):

    def _image_get_root_disk_size(name):
        action = get_action()
        action.get_root_disk_size(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _image_get_root_disk_size(name)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_delete(req):

    def _image_delete(name):
        action = get_action()
        action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _image_delete(name)

    req.response.status = 204
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_query(req):

    def _image_query(imagename):
        action = get_action()
        action.query(imagename)

    imagename = None
    if 'imagename' in req.GET:
        imagename = req.GET['imagename']
    _image_query(imagename)
