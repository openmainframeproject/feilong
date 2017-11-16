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
import webob
import six
import json
import hashlib
import os

from zvmconnector import connector
from zvmsdk import api
from zvmsdk import config
from zvmsdk import log
from zvmsdk import utils
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import image
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation



_IMAGEACTION = None
CONF = config.CONF
LOG = log.LOG

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

    def upload(self, image_name, image_file):
        info =self.sdkapi.image_upload(image_name, image_file, image_meta)
        return info

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
    def _upload(image_name, image_file):
        action = get_action()
        return action.upload(image_name, image_file, image_meta)
    import pdb;pdb.set_trace()

    # Check if the request content type is valid
#     try:
#         request.get_content_type(('application/octet-stream',))
#     except exception.InvalidContentType as e:
#         raise webob.exc.HTTPUnsupportedMediaType(explanation=e.msg)

    # TODO: check the request content_type
    #if self.is_valid_encoding(request) and self.is_valid_method(request):
    image_name = util.wsgi_path_item(request.environ, 'name')
    image_file = request.body_file
    image_meta = {}
    for key in ['os_version', 'md5sum']:
        image_meta[key] = request.headers.get(key)

    info = _upload(image_name, image_file, image_meta)

    # Construct response
    response = request.response
    response.status_int = 204
    response.headers['Content-Type'] = 'application/json'

    # encode all headers in response to utf-8 to prevent unicode errors
    for name, value in list(response.headers.items()):
        if six.PY2 and isinstance(value, six.text_type):
            response.headers[name] = encodeutils.safe_encode(value)
    return response


READ_CHUNKSIZE = 4096
@util.SdkWsgify
@tokens.validate
def image_download_file(request):
    import pdb; pdb.set_trace()
    image_id = util.wsgi_path_item(request.environ, 'name')
    image_path = '/data/opt/images/testimage'
    response = request.response
#     response = webob.Response(request=request)
    # Copy from ResponseSerializer download
    offset, chunk_size = 0 , None
    # Maybe not ture here
    range_val = request.headers.get('Range')
    image_size = os.path.getsize(image_path)
 
    if range_val:
        if isinstance(range_val, webob.byterange.Range):
            response_end = image_size -1

            if range_val.start >= 0:
                offset = range_val.start
            else:
                if abs(range_val.start) < image_size:
                    offset = image_size + range_val.start
     
            if range_val.end is not None and range_val.end < image_size:
                chunk_size = range_val.end - offset
                response_end = range_val.end -1
            else:
                # For the last chunk case
                chunk_size = image_size - offset
 
        elif isinstance(range_val, webob.byterange.ContentRange):
            response_end = range_val.stop - 1
            # NOTE(flaper87): if not present, both, start
            # and stop, will be None.
            offset = range_val.start
            chunk_size = range_val.stop - offset
         
        response.status_int = 206

    response.headers['Content-Type'] = 'application/octet-stream'

 
    ## TODO change it
    response.app_iter = iter(get_data(image_path,
                                      offset=offset,
                                      chunk_size=chunk_size))
     
             
 
    if chunk_size is not None:
        response.headers['Content-Range'] = 'bytes %s-%s/%s'\
                                                % (offset,
                                                   response_end,
                                                   image_size)
    else:
        chunk_size = image_size
# 
#    if image.checksum:
#         response.headers['Content-MD5'] = image.checksum
    # NOTE(markwash): "response.app_iter = ..." also erroneously resets the
    # content-length
    image_checksum = '563ab5e31d8095815c6d2fd0326c637b'
    if image_checksum:
        response.headers['Content-MD5'] = image_checksum
    response.headers['Content-Length'] = six.text_type(chunk_size)
    return response
 
def get_data(file_path, offset=0, chunk_size=None):
    data = ChunkedFile(file_path,
                          offset=offset,
                          chunk_size=READ_CHUNKSIZE,
                          partial_length=chunk_size)
 
    return get_chunk_data_iterator(data)
 
 
def get_chunk_data_iterator(data):
    for chunk in data:
        yield chunk

 
class ChunkedFile(object):
    """
    We send something that can iterate over a large file
    """
    # Guess the Partial_length the left bytes that not been read? 
 
    def __init__(self, filepath, offset=0, chunk_size=4096,
                 partial_length=None):
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.partial_length = partial_length
        self.partial = self.partial_length is not None
        self.fp = open(self.filepath, 'rb')
        if offset:
            self.fp.seek(offset)
 
    def __iter__(self):
        """Return an iterator over the image file."""
        try:
            if self.fp:
                while True:
                    if self.partial:
                        size = min(self.chunk_size, self.partial_length)
                    else:
                        size = self.chunk_size
 
                    chunk = self.fp.read(size)
                    if chunk:
                        yield chunk
 
                        if self.partial:
                            self.partial_length -= len(chunk)
                            if self.partial_length <= 0:
                                break
                    else:
                        break
        finally:
            self.close()
 
    def close(self):
        """Close the internal file pointer"""
        if self.fp:
            self.fp.close()
            self.fp = None
