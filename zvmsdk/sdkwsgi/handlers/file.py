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

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import returncode
from zvmsdk import utils
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi import util

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
                      {'filesize_in_bytes': bytes_written,
                       'dest_url': target_fpath,
                       'md5sum': checksum_hex})
            return_data = {'filesize_in_bytes': bytes_written,
                           'dest_url': 'file://' + target_fpath,
                           'md5sum': checksum_hex}

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
                       'rc': returncode.errors['file']['overallRC'],
                       'rs': 1,
                       'errmsg': six.text_type(err),
                       'output': ''}
        return results

    def file_export(self, fpath):
        try:
            if not os.path.exists(fpath):
                msg = ("The specific file %s for export does not exist in "
                       "zvmsdk server" % fpath)
                LOG.error(msg)
                results = {'overallRC':
                           returncode.errors['file'][0]['overallRC'],
                           'modID': returncode.errors['file'][0]['modID'],
                           'rc': returncode.errors['file'][0]['rc'],
                           'rs': 2,
                           'errmsg': msg,
                           'output': ''}
                return results

            offset = 0
            file_size = os.path.getsize(fpath)
            # image_size here is the image_size in bytes

            file_iter = iter(get_data(fpath,
                                      offset=offset,
                                      file_size=file_size))

            return file_iter

        except exception as err:
            msg = ("Exception happened during file export with error %s " %
                   six.text_type(err))
            results = {'overallRC': returncode.errors['file'][0]['overallRC'],
                       'modID': returncode.errors['file'][0]['modID'],
                       'rc': returncode.errors['file'][0]['rc'],
                       'rs': 2,
                       'errmsg': msg,
                       'output': ''}
            return results


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
    content_type = request.content_type
    info = {}
    info = content_type_validation(content_type)
    if not info:
        file_obj = request.body_file
        info = _import(file_obj)

    info_json = json.dumps(info)
    request.response.body = utils.to_utf8(info_json)
    request.response.status = util.get_http_code_from_sdk_return(info)
    request.response.content_type = 'application/json'
    return request.response


def content_type_validation(content_type):
    info = {}
    if content_type not in ['application/octet-stream']:
        msg = ('Invalid content type %s found for file import/export, the '
               'supported content type is application/octet-stream' %
               content_type)
        LOG.error(msg)
        errmsg = returncode.errors['RESTAPI'][1][1] % msg
        info = {'overallRC': returncode.errors['RESTAPI'][0]['overallRC'],
                'modID': returncode.errors['RESTAPI'][0]['modID'],
                'rc': returncode.errors['RESTAPI'][0]['overallRC'],
                'rs': 1,
                'errmsg': errmsg,
                'output': ''}
    return info


@util.SdkWsgify
@tokens.validate
def file_export(request):
    def _export(fpath):
        action = get_action()
        return action.file_export(fpath)

    # Check if the request content type is valid
    content_type = request.content_type

    results = content_type_validation(content_type)
    if not results:
        fpath = request.body
        results = _export(fpath)

    # if image_iter is dict, means error happened.
    if isinstance(results, dict):
        info_json = json.dumps(results)
        request.response.body = utils.to_utf8(info_json)
        request.response.status = util.get_http_code_from_sdk_return(
            results)
        request.response.content_type = 'application/json'
        return request.response

    # Result contains (image_iter, md5sum, image_size)
    else:
        request.response.headers['Content-Type'] = 'application/octet-stream'
        # TODO change it
        request.response.app_iter = results
        request.response.status_int = 200

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
