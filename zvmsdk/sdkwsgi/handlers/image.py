# Copyright 2017,2018 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
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
import webob
import six
import json
import hashlib
import os

from zvmconnector import connector
from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import image
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation



_IMAGEACTION = None
_SDKAPI = None
CONF = config.CONF
LOG = log.LOG
results = {'overallRC': 0, 'modID': None,
           'rc': 0, 'rs': 0,
           'errmsg': '',
           'output': ''}

def get_sdkapi():
    global _SDKAPI
    if _SDKAPI is None:
        _SDKAPI = api.SDKAPI()
    return _SDKAPI


class ImageAction(object):

    def __init__(self):
        self.client = connector.ZVMConnector(connection_type='socket',
                                             ip_addr=CONF.sdkserver.bind_addr,
                                             port=CONF.sdkserver.bind_port)
        self.sdkapi = get_sdkapi()

    @validation.schema(image.create)
    def create(self, body):
        image = body['image']
        image_name = image['image_name']
        url = image['url']
        remote_host = image.get('remote_host', None)
        image_meta = image['image_meta']

        info = self.client.send_request('image_import', image_name,
                                        url, image_meta, remote_host)
        return info

    @validation.query_schema(image.query)
    def get_root_disk_size(self, req, name):
        # FIXME: this param need combined image nameg, e.g the profile
        # name, not the given image name from customer side
        info = self.client.send_request('image_get_root_disk_size',
                                        name)
        return info

    def delete(self, name):
        info = self.client.send_request('image_delete', name)
        return info

    @validation.query_schema(image.query)
    def query(self, req, name):
        info = self.client.send_request('image_query', name)
        return info

    @validation.schema(image.export)
    def export(self, name, body):
        location = body['location']
        dest_url = location['dest_url']
        remotehost = location.get('remote_host', None)
        info = self.client.send_request('image_export', name,
                                        dest_url, remotehost)
        return info

    # If using sdkserver, the socket server will catch the exception and
    # construct the result to socket client, here not use sdkserver, so need
    # to construct the exception info here
    def upload(self, image_name, image_file, image_meta):

        try:
            self.sdkapi.image_upload(image_name, image_file, image_meta)
        except exception.SDKBaseException as e:
           LOG.error("Exception happened during image upload")
           results = {'overallRC': e.results['overallRC'],
                      'modID': e.results['modID'],
                      'rc': e.results['rc'],
                      'rs': e.results['rs'],
                      'errmsg': e.format_message(),
                      'output': ''}
        return results

    def download(self, image_name):
        try:
            (image_iter, md5sum, image_size) = self.sdkapi.image_download(
                                                                image_name)
            return image_iter, md5sum, image_size
        except exception.SDKBaseException as e:
            LOG.error("Exception happened during image upload")
            results = {'overallRC': e.results['overallRC'],
                      'modID': e.results['modID'],
                      'rc': e.results['rc'],
                      'rs': e.results['rs'],
                      'errmsg': e.format_message(),
                      'output': ''}
            return results

def get_action():
    global _IMAGEACTION
    if _IMAGEACTION is None:
        _IMAGEACTION = ImageAction()
    return _IMAGEACTION


@util.SdkWsgify
@tokens.validate
def image_create(req):

    def _image_create(req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.create(body=body)

    info = _image_create(req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_already_exists)
    req.response.content_type = 'application/json'
    return req.response


@util.SdkWsgify
@tokens.validate
def image_get_root_disk_size(req):

    def _image_get_root_disk_size(req, name):
        action = get_action()
        return action.get_root_disk_size(req, name)

    name = util.wsgi_path_item(req.environ, 'name')
    info = _image_get_root_disk_size(req, name)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info)
    return req.response


@util.SdkWsgify
@tokens.validate
def image_delete(req):

    def _image_delete(name):
        action = get_action()
        return action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    info = _image_delete(name)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    req.response.content_type = 'application/json'
    return req.response


@util.SdkWsgify
@tokens.validate
def image_export(req):

    def _image_export(name, req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.export(name, body=body)

    name = util.wsgi_path_item(req.environ, 'name')
    info = _image_export(name, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    return req.response


@util.SdkWsgify
@tokens.validate
def image_query(req):

    def _image_query(imagename, req):
        action = get_action()
        return action.query(req, imagename)

    imagename = None
    if 'imagename' in req.GET:
        imagename = req.GET['imagename']
    info = _image_query(imagename, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    return req.response

@util.SdkWsgify
@tokens.validate
def image_upload(request):
    def _upload(image_name, image_file, image_meta):
        action = get_action()
        return action.upload(image_name, image_file, image_meta)

    # Check if the request content type is valid
    if request.content_type not in ['application/octet-stream']:
        msg = ('Invalid content type: %s for image upload, the supported '
               'content type is application/octet-stream' %
                request.content_type)
        LOG.error(msg)
        raise webob.exc.HTTPUnsupportedMediaType(explanation=msg)

    image_name = util.wsgi_path_item(request.environ, 'name')
    image_file = request.body_file
    image_meta = {}
    for key in ['os_version', 'md5sum']:
        image_meta[key] = request.headers.get(key)

    info = _upload(image_name, image_file, image_meta)

    info_json = json.dumps(info)
    request.response.body = utils.to_utf8(info_json)
    request.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_already_exists)
    request.response.content_type = 'application/json'
    return request.response


@util.SdkWsgify
@tokens.validate
def image_download(request):
    import pdb; pdb.set_trace()
    def _download(imagename):
        action = get_action()
        return action.download(image_name)

#     # Check if the request content type is valid
#     if request.content_type not in ['application/octet-stream']:
#         msg = ('Invalid content type: %s for image upload, the supported '
#                'content type is application/octet-stream' %
#                 request.content_type)
#         LOG.error(msg)
#         raise webob.exc.HTTPUnsupportedMediaType(explanation=msg)

    image_name = util.wsgi_path_item(request.environ, 'name')
    results = _download(image_name)
    import pdb; pdb.set_trace()

    # if image_iter is dict, means error happened.
    if len(results) == 1 and isinstance(results[0], dict):
        info_json = json.dumps(results[0])
        request.response.body = utils.to_utf8(info_json)
        request.response.status = util.get_http_code_from_sdk_return(
            results[0], additional_handler=util.handle_already_exists)
        request.response.content_type = 'application/json'
        return request.response

    # Result contains (image_iter, md5sum, image_size)
    elif len(results) == 3:
        request.response.headers['Content-Type'] = 'application/octet-stream'
        ## TODO change it
        request.response.app_iter = results[0]
        request.response.status_int = 200
             
        image_checksum = results[1]
        chunk_size = results[2]

        request.response.headers['Content-Type'] = 'application/octet-stream'
        if image_checksum:
            request.response.headers['Content-MD5'] = image_checksum
        request.response.headers['Content-Length'] = six.text_type(chunk_size)
        return request.response
