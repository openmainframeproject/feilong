# Copyright 2017 IBM Corp.
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

import exceptions
import hashlib
import os

import threading
import urlparse

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk import log


LOG = log.LOG
CONF = config.CONF

_IMAGEOPS = None

IMAGE_REPO = CONF.image.sdk_image_repository
CHUNKSIZE = 65536
_LOCK = threading.Lock()


def get_imageops():
    global _IMAGEOPS
    if _IMAGEOPS is None:
        _IMAGEOPS = ImageOps()
    return _IMAGEOPS


class ImageOps(object):
    def __init__(self):
        self.zvmclient = zvmclient.get_zvmclient()
        self._pathutils = zvmutils.PathUtils()

    def image_get_root_disk_size(self, spawn_image_name):
        """use 'hexdump' to get the root_disk_size."""
        image_file_path = self.zvmclient.get_image_path_by_name(
                                                    spawn_image_name)
        try:
            cmd = 'hexdump -C -n 64 %s' % image_file_path
            output = zvmutils.execute(cmd)
        except ValueError:
            msg = ("Get image property failed,"
                    " please check whether the image file exists!")
            raise exception.ZVMImageError(msg=msg)

        LOG.debug("hexdump result is %s", output)
        try:
            root_disk_size = output[144:156].strip()
        except ValueError:
            msg = ("Image file at %s is missing built-in disk size "
                    "metadata, it was probably not captured with xCAT"
                    % image_file_path)
            raise exception.ZVMImageError(msg=msg)

        if 'FBA' not in output and 'CKD' not in output:
            msg = ("The image's disk type is not valid. Currently we only"
                      " support FBA and CKD disk")
            raise exception.ZVMImageError(msg=msg)

        LOG.debug("The image's root_disk_size is %s", root_disk_size)
        return root_disk_size

    def image_query(self, imagekeyword=None):
        return self.zvmclient.image_query(imagekeyword)

    def image_delete(self, image_name):
        return self.zvmclient.image_delete(image_name)

    def image_import(self, url, image_meta={}, remote_host=None):
        parsed_url = urlparse.urlparse(url)
        if CONF.zvm.client_type == 'xcat':
            self.zvmclient.image_import(parsed_url.path,
                                        image_meta['os_version'],
                                        remote_host=remote_host)
            return
        # TODO: need to import requests and paramiko for further process
        image_name = parsed_url.path.split('/')[-1]
        target = ''.join([IMAGE_REPO, image_name])
        if os.path.exists(target):
            msg = ("There is one image with same name %s as source image"
                    " already exists in image repository, please considering"
                    " to change the source image name or remove the existing"
                    " one in image repository ") % image_name
            raise exceptions.SDKImageImportExcetpion(msg)

        try:
            scheme2backend(parsed_url.scheme).image_import(url,
                                                    image_meta=image_meta,
                                                    remote_host=remote_host)
        except KeyError:
            raise exceptions.SDKUnsupportedImageBackend("No backend found for"
                        " '%s'" % parsed_url.scheme)

        # Check md5 after import to ensure import a correct image
        md5sum = image_meta.get('md5sum')
        if md5sum and not md5sum_check_pass(target, md5sum):
            msg = ("The md5sum after import is not same as source image, the"
            " image has been broken")
            raise exceptions.SDKImageImportException(msg)


def scheme2backend(scheme):
    return {
        "file": FilesystemBackend,
        "http": HTTPBackend,
#         "https": HTTPSBackend
    }[scheme]


def md5sum_check_pass(fname, expect_md5sum):

    real_md5sum = get_md5sum(fname)
#     print "real md5sum is: %s" % real_md5sum
#     print "expect md5sum is %s" % expect_md5sum
    return real_md5sum == expect_md5sum


def get_md5sum(fpath):
    """Calculate the md5sum of the specific image file"""

    def read_chunks(fh):
        fh.seek(0)
        chunk = fh.read(CHUNKSIZE)
        while chunk:
            yield chunk
            chunk = fh.read(CHUNKSIZE)
        else:
            fh.seek(0)
    current_md5 = hashlib.md5()
    if isinstance(fpath, basestring) and os.path.exists(fpath):
        with open(fpath, "rb") as fh:
            for chunk in read_chunks(fh):
                current_md5.update(chunk)

    elif (fpath.__class__.__name__ in ["StringIO", "StringO"] or
          isinstance(fpath, file)):
        for chunk in read_chunks(fpath):
            current_md5.update(chunk)
    else:
        return ""
    return current_md5.hexdigest()


class UnsupportedBackend(Exception):
    pass


class FilesystemBackend(object):
    @classmethod
    def image_import(cls, url, **kwargs):
        """Import image from remote host to local image repository using scp.
        If remote_host not specified, it means the source file exist in local
        file system, just create a soft link in image repository
        """

        source = urlparse.urlparse(url).path
        image_name = source.split('/')[-1]
        target = ''.join([IMAGE_REPO, image_name])
        if kwargs['remote_host']:
            if '@' in kwargs['remote_host']:
                remote_host_info = kwargs['remote_host']
                remote_host_user = remote_host_info.split('@')[0]
                remote_host_ip = remote_host_info.split('@')[1]

                try:
                    private_key = paramiko.RSAKey.from_private_key_file(
                                CONF.image.image_source_server_private_key)

                    transport = paramiko.Transport((remote_host_ip, 22))
                    transport.connect(username=remote_host_user,
                                      pkey=private_key)

                    sftp = paramiko.SFTPClient.from_transport(transport)
                    sftp.get(source, target)
                    transport.close()
                except Exception as err:
                    emsg = err.format_message()
                    LOG.error("Error happened during scp remote image to SDK"
                              " image repository with reason %s" % emsg)
                    raise exceptions.SDKImageImportException(msg=emsg)

            else:
                LOG.error("remote_host format invalid")
                msg = ("The specified remote_host %s format invalid" %
                        kwargs['remote_host'])
                raise exceptions.SDKImageImportException(msg)
        # Create soft link if sourc e is form local filesystem
        else:
            LOG.debug("Remote_host not specified, will just create soft link")
            os.symlink(source, target)


class HTTPBackend(object):
    @classmethod
    def image_import(cls, url, **kwargs):
        import_image = MultiThreadDownloader(url)
        import_image.run()


class MultiThreadDownloader(threading.Thread):

    def __init__(self, url):
        super(MultiThreadDownloader, self).__init__()
        self.url = url
        # Set thread number
        self.threadnum = 4
        # Get the filename from url
        self.name = self.url.split('/')[-1]
        r = requests.head(self.url)
        # Get the size of the download resource
        self.totalsize = int(r.headers['Content-Length'])
        self.target = ''.join([IMAGE_REPO,
                               urlparse.urlparse(url).path.split('/')[-1]])

    def get_range(self):
        ranges = []
        offset = int(self.totalsize / self.threadnum)
        for i in range(self.threadnum):
            if i == self.threadnum - 1:
                ranges.append((i * offset, ''))
            else:
                # Get the process range for each thread
                ranges.append((i * offset, (i + 1) * offset))
        return ranges

    def download(self, start, end):
        headers = {'Range': 'Bytes=%s-%s' % (start, end),
                   'Accept-Encoding': '*'}
        # Get the data
        res = requests.get(self.url, headers=headers)
        # seek to the right position for writing data
        LOG.debug("Downloading file range %s:%s success" % (start, end))
#
        with _LOCK:
            self.fd.seek(start)
            self.fd.write(res.content)

    def run(self):
        self.fd = open(self.target, 'w')
        thread_list = []
        n = 0
        for ran in self.get_range():
            start, end = ran
            LOG.debug('thread %d start:%s,end:%s' % (n, start, end))
            n += 1
            # Open thread
            thread = threading.Thread(target=self.download, args=(start, end))
            thread.start()
            thread_list.append(thread)

        for i in thread_list:
            i.join()
        LOG.debug('Download %s success' % (self.name))
        self.fd.close()
