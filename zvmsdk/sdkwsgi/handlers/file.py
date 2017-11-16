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

import six
import json
import hashlib
import os
import tempfile
import uuid
import webob

from zvmconnector import connector
from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import returncode
from zvmsdk import utils
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import image
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation



_FILEACTION = None
CONF = config.CONF
LOG = log.LOG
CHUNKSIZE = 4096

class FileAction(object):
    # If using sdkserver, the socket server will catch the exception and
    # construct the result to socket client, here not use sdkserver, so need
    # to construct the exception info here

    def file_import(self, fileobj):
        # TODO: (nafei) add a configuration option to put the imported files
        fname = str(uuid.uuid1())
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        target_fpath = '/'.join([tempDir, fname])

        # The following steps save the imgae file into image repository.
        checksum = hashlib.md5()
        bytes_written = 0

        try:
            with open(target_fpath, 'wb') as f:
                for buf in chunkreadable(fileobj, CHUNKSIZE):
                    bytes_written += len(buf)
                    checksum.update(buf)
                    f.write(buf)

            checksum_hex = checksum.hexdigest()

            LOG.debug(("Wrote %(bytes_written)d bytes to %(target_image)s"
                       " with checksum %(checksum_hex)s"),
                      {'bytes_written': bytes_written,
                       'target_image': target_fpath,
                       'checksum_hex': checksum_hex})
            return_data = {'bytes_written': bytes_written,
                           'target_image': target_fpath,
                           'checksum_hex': checksum_hex}

            results = {'overallRC': 0, 'modID': None,
                       'rc': 0, 'rs': 0,
                       'errmsg': '',
                       'output': return_data}

        except Exception as err:
            # Cleanup the image from image repository
            self._pathutils.clean_temp_folder(target_fpath)
            LOG.error("Exception happened during file import")

            results = {'overallRC': returncode.errors['file']['overallRC'],
                       'modID': returncode.errors['file']['modID'],
                       'rc':  returncode.errors['file']['overallRC'],
                       'rs': returncode.errors['file'][1]['2'],
                       'errmsg': six.text_type(err),
                       'output': ''}
        return results

    def file_export(self, fpath):
        try:
            file_iter = self._file_export(fpath)
            return file_iter
        except exception.SDKBaseException as e:
            LOG.error("Exception happened during image upload")
            results = {'overallRC': e.results['overallRC'],
                       'modID': e.results['modID'],
                       'rc': e.results['rc'],
                       'rs': e.results['rs'],
                       'errmsg': e.format_message(),
                       'output': ''}
            return results


    def _file_export(self, fpath):
        """Download the image from image repository"""

        if not fpath:
            msg = ("The specific file %s does not exist in zvmsdk server"
                   % fpath)
            LOG.error(msg)

        offset = 0
        import pdb; pdb.set_trace()
        app_iter = iter(get_data(fpath,
                                 offset=offset,
                                 file_size=image_size))

        return file_iter

def get_action():
    global _FILEACTION
    if _FILEACTION is None:
        _FILEACTION = FileAction()
    return _FILEACTION


@util.SdkWsgify
@tokens.validate
def file_import(request):
    def _import(file_obj):
        action = get_action()
        return action.file_import(file_obj)

    # Check if the request content type is valid
    import pdb; pdb.set_trace()
    if request.content_type not in ['application/octet-stream']:
        msg = ('Invalid content type: %s for file import, the supported '
               'content type is application/octet-stream' %
                request.content_type)
        LOG.error(msg)
        raise webob.exc.HTTPUnsupportedMediaType(explanation=msg)

    file_obj = request.body_file
    info = _import(file_obj)

    info_json = json.dumps(info)
    request.response.body = utils.to_utf8(info_json)
    request.response.status = util.get_http_code_from_sdk_return(info)
    request.response.content_type = 'application/json'
    return request.response


@util.SdkWsgify
@tokens.validate
def file_export(request):
    import pdb; pdb.set_trace()
    def _export(fpath):
        action = get_action()
        return action.file_export(fpath)

    # Check if the request content type is valid
    if request.content_type not in ['application/octet-stream']:
        msg = ('Invalid content type: %s for image upload, the supported '
              'content type is application/octet-stream' %
               request.content_type)
        LOG.error(msg)
    raise webob.exc.HTTPUnsupportedMediaType(explanation=msg)

    fpath = request.body
    results = _export(fpath)
    import pdb; pdb.set_trace()

    # if image_iter is dict, means error happened.
    if len(results) == 1 and isinstance(results[0], dict):
        info_json = json.dumps(results[0])
        request.response.body = utils.to_utf8(info_json)
        request.response.status = util.get_http_code_from_sdk_return(
            results[0])
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


def chunkreadable(iter, chunk_size=65536):
    """
    Wrap a readable iterator with a reader yielding chunks of
    a preferred size, otherwise leave iterator unchanged.

    :param iter: an iter which may also be readable
    :param chunk_size: maximum size of chunk
    """
    return chunkiter(iter, chunk_size) if hasattr(iter, 'read') else iter


def chunkiter(fp, chunk_size=65536):
    """
    Return an iterator to a file-like obj which yields fixed size chunks

    :param fp: a file-like object
    :param chunk_size: maximum size of chunk
    """
    while True:
        chunk = fp.read(chunk_size)
        if chunk:
            yield chunk
        else:
            break


def get_data(file_path, offset=0, file_size=None):
    data = ChunkedFile(file_path,
                       offset=offset,
                       chunk_size=CHUNKSIZE,
                       partial_length=file_size)
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
