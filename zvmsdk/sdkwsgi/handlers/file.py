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
import uuid

from zvmsdk import config
from zvmsdk import constants as const
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


INVALID_CONTENT_TYPE = {
    'overallRC': returncode.errors['RESTAPI'][0]['overallRC'],
    'modID': returncode.errors['RESTAPI'][0]['modID'],
    'rc': returncode.errors['RESTAPI'][0]['overallRC'],
    'rs': 1,
    'errmsg': '',
    'output': ''}

FILE_OPERATION_ERROR = {
    'overallRC': returncode.errors['file'][0]['overallRC'],
    'modID': returncode.errors['file'][0]['modID'],
    'rc': returncode.errors['file'][0]['overallRC'],
    'rs': 1,
    'errmsg': '',
    'output': ''}


class FileAction(object):

    def __init__(self):
        self._pathutils = utils.PathUtils()

    def file_import(self, fileobj):
        try:
            importDir = self._pathutils.create_file_repository(
                    const.FILE_TYPE['IMPORT'])
            fname = str(uuid.uuid1())
            target_fpath = '/'.join([importDir, fname])

            # The following steps save the imported file into sdkserver
            checksum = hashlib.md5()
            bytes_written = 0

            with open(target_fpath, 'wb') as f:
                for buf in fileChunkReadable(fileobj, CHUNKSIZE):
                    bytes_written += len(buf)
                    checksum.update(buf)
                    f.write(buf)

            checksum_hex = checksum.hexdigest()

            LOG.debug("Wrote %(bytes_written)d bytes to %(target_image)s"
                      " with checksum %(checksum_hex)s" %
                      {'bytes_written': bytes_written,
                       'target_image': target_fpath,
                       'checksum_hex': checksum_hex})
            return_data = {'filesize_in_bytes': bytes_written,
                           'dest_url': 'file://' + target_fpath,
                           'md5sum': checksum_hex}

            results = {'overallRC': 0, 'modID': None,
                       'rc': 0, 'rs': 0,
                       'errmsg': '',
                       'output': return_data}

        except OSError as err:
            msg = ("File import error: %s, please check access right to "
                   "specified file or folder" % six.text_type(err))
            LOG.error(msg)
            results = FILE_OPERATION_ERROR
            results.update({'rs': 1, 'errmsg': msg, 'output': ''})
        except Exception as err:
            # Cleanup the file from file repository
            self._pathutils.clean_temp_folder(target_fpath)
            msg = ("Exception happened during file import: %s" %
                   six.text_type(err))
            LOG.error(msg)
            results = FILE_OPERATION_ERROR
            results.update({'rs': 1, 'errmsg': msg, 'output': ''})

        return results

    def file_export(self, fpath):
        try:
            if not os.path.exists(fpath):
                msg = ("The specific file %s for export does not exist" %
                       fpath)
                LOG.error(msg)
                results = FILE_OPERATION_ERROR.update({'rs': 2,
                    'errmsg': msg, 'output': ''})
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
            LOG.error(msg)
            results = FILE_OPERATION_ERROR.update({'rs': 2, 'errmsg': msg,
                                                   'output': ''})
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
    info = _content_type_validation(content_type)
    if not info:
        file_obj = request.body_file
        info = _import(file_obj)

    info_json = json.dumps(info)
    request.response.body = utils.to_utf8(info_json)
    request.response.status = util.get_http_code_from_sdk_return(info)
    request.response.content_type = 'application/json'
    return request.response


def _content_type_validation(content_type):
    results = {}
    if content_type not in ['application/octet-stream']:
        msg = ('Invalid content type %s found for file import/export, the '
               'supported content type is application/octet-stream' %
               content_type)
        LOG.error(msg)
        results = INVALID_CONTENT_TYPE.update({'errmsg': msg})
    return results


@util.SdkWsgify
@tokens.validate
def file_export(request):
    def _export(fpath):
        action = get_action()
        return action.file_export(fpath)

    # Check if the request content type is valid
    content_type = request.content_type

    results = _content_type_validation(content_type)
    if not results:
        fpath = request.body
        results = _export(fpath)

    # if results is dict, means error happened.
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
        request.response.app_iter = results
        request.response.status_int = 200

        return request.response


def fileChunkReadable(file_obj, chunk_size=65536):
    """
    Return a readable iterator with a reader yielding chunks of
    a preferred size, otherwise leave file object unchanged.

    :param file_obj: an iter which may be readable
    :param chunk_size: maximum size of chunk
    """

    if hasattr(file_obj, 'read'):
        return fileChunkIter(file_obj, chunk_size)
    else:
        return file_obj


def fileChunkIter(file_object, file_chunk_size=65536):
    """
    Return an iterator to a file-like object that yields fixed size chunks

    :param file_object: a file-like object
    :param file_chunk_size: maximum size of chunk
    """
    while True:
        chunk = file_object.read(file_chunk_size)
        if chunk:
            yield chunk
        else:
            break


def get_data(file_path, offset=0, file_size=None):
    data = chunkedFile(file_path,
                       file_offset=offset,
                       file_chunk_size=CHUNKSIZE,
                       file_partial_length=file_size)
    return get_chunk_data_iterator(data)


def get_chunk_data_iterator(data):
    for chunk in data:
        yield chunk


class chunkedFile(object):
    """
    Send iterator to wsgi server so that it can iterate over a large file
    """

    def __init__(self, file_path, file_offset=0, file_chunk_size=4096,
                 file_partial_length=None):
        self.file_path = file_path
        self.file_chunk_size = file_chunk_size
        self.file_partial_length = file_partial_length
        self.file_partial = self.file_partial_length is not None
        self.file_object = open(self.file_path, 'rb')
        if file_offset:
            self.file_pointer.seek(file_offset)

    def __iter__(self):
        """Return an iterator over the large file."""
        try:
            if self.file_object:
                while True:
                    if self.file_partial:
                        size = min(self.file_chunk_size,
                                   self.file_partial_length)
                    else:
                        size = self.file_chunk_size

                    chunk = self.file_object.read(size)
                    if chunk:
                        yield chunk

                        if self.file_partial:
                            self.file_partial_length -= len(chunk)
                            if self.file_partial_length <= 0:
                                break
                    else:
                        break
        finally:
            self.close()

    def close(self):
        """Close the internal file pointer"""
        if self.file_object:
            self.file_object.close()
            self.file_object = None
