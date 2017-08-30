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
import commands
import hashlib
import urlparse
import requests
import threading
import os
import shutil
from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk import log


LOG = log.LOG
CONF = config.CONF

_IMAGEOPS = None
_LOCK = threading.Lock()
CHUNKSIZE = 4096


def get_imageops():
    global _IMAGEOPS
    if _IMAGEOPS is None:
        _IMAGEOPS = ImageOps()
    return _IMAGEOPS


class ImageOps(object):
    def __init__(self):
        self.zvmclient = zvmclient.get_zvmclient()
        self._pathutils = zvmutils.PathUtils()

    def image_get_root_disk_size(self, image_name):
        return self.zvmclient.image_get_root_disk_size(image_name)

    def image_import(self, image_name, url, image_meta, remote_host=None):
        if CONF.zvm.client_type == 'xcat':
            self.zvmclient.image_import(image_name,
                                        url,
                                        image_meta,
                                        remote_host=remote_host)
        else:
            self.import_image_to_sdk_imagerepo(image_name, url, image_meta,
                                               remote_host)

    def image_query(self, imagekeyword=None):
        return self.zvmclient.image_query(imagekeyword)

    def image_delete(self, image_name):
        return self.zvmclient.image_delete(image_name)

    def import_image_to_sdk_imagerepo(self, image_name, url, image_meta,
                                      remote_host=None):
        """Import the image specified in url to SDK image repository, and
            create a record in image db, the imported images are located in
            image_repository/image_name/os_version/, for example,
            /opt/sdk/images/netboot/rhel7.2/"""

        try:
            target = '/'.join([CONF.image.sdk_image_repository,
                              'netboot',
                              image_meta['os_version'],
                              image_name])
            self._pathutils.create_import_image_repository(
                                                    image_meta['os_version'])
            self._scheme2backend(urlparse.urlparse(url).scheme).image_import(
                                                    image_name, url,
                                                    image_meta,
                                                    remote_host=remote_host)
            # Check md5 after import to ensure import a correct image
            # TODO change to use query imagename in db
            md5sum = image_meta.get('md5sum')
            if md5sum and not self._md5sum_check_pass(target, md5sum):
                err = ("The md5sum after import is not same as source image,"
                       " the image has been broken")
                raise exception.SDKImageImportException(err)
            LOG.info("Image %s is import successfully" % image_name)

            self._create_image_db_record(image_name, url, image_meta)
        except KeyError:
            raise exception.SDKUnsupportedImageBackend("No backend found for"
                        " '%s'" % urlparse.urlparse(url).scheme)
        except Exception as err:
            msg = ("Import image to zvmsdk image repository error due to: %s"
                   % str(err))
            # Cleanup the image from image repository
            self._pathutils.remove_file(target)
            raise exception.SDKImageImportException(msg=msg)

    def _create_image_db_record(self, image_name, url, image_meta):
        pass

    def _scheme2backend(self, scheme):
        return {
            "file": FilesystemBackend,
            "http": HTTPBackend,
    #         "https": HTTPSBackend
        }[scheme]

    def _md5sum_check_pass(self, fpath, expect_md5sum):
        """Return True if md5sum matches"""
        real_md5sum = self._get_md5sum(fpath)
        return real_md5sum == expect_md5sum

    def _get_md5sum(self, fpath):
        """Calculate the md5sum of the specific image file"""
        current_md5 = hashlib.md5()
        if isinstance(fpath, basestring) and os.path.exists(fpath):
            with open(fpath, "rb") as fh:
                for chunk in self._read_chunks(fh):
                    current_md5.update(chunk)

        elif (fpath.__class__.__name__ in ["StringIO", "StringO"] or
              isinstance(fpath, file)):
            for chunk in self._read_chunks(fpath):
                current_md5.update(chunk)
        else:
            return ""
        return current_md5.hexdigest()

    def _read_chunks(self, fh):
        fh.seek(0)
        chunk = fh.read(CHUNKSIZE)
        while chunk:
            yield chunk
            chunk = fh.read(CHUNKSIZE)
        else:
            fh.seek(0)


class FilesystemBackend(object):
    @classmethod
    def image_import(cls, image_name, url, image_meta, **kwargs):
        """Import image from remote host to local image repository using scp.
        If remote_host not specified, it means the source file exist in local
        file system, just copy the image to image repository
        """
        try:
            source = urlparse.urlparse(url).path
            target = '/'.join([CONF.image.sdk_image_repository,
                              'netboot',
                              image_meta['os_version'],
                              image_name])
            if kwargs['remote_host']:
                if '@' in kwargs['remote_host']:
                    source_path = ':'.join([kwargs['remote_host'], source])
                    command = ' '.join(['/usr/bin/scp', source_path, target])
                    (rc, output) = commands.getstatusoutput(command)
                    if rc:
                        msg = ("Error happened when copying image file with"
                               "reason: %s" % output)
                        LOG.error(msg)
                        raise
                else:
                    msg = ("The specified remote_host %s format invalid" %
                            kwargs['remote_host'])
                    LOG.error(msg)
                    raise
            else:
                LOG.debug("Remote_host not specified, will copy from local")
                shutil.copyfile(source, target)

        except Exception as err:
                msg = ("Error happened when importing image to SDK"
                          " image repository with reason: %s" % str(err))
                LOG.error(msg)
                raise err


class HTTPBackend(object):
    @classmethod
    def image_import(cls, image_name, url, image_meta, **kwargs):
        import_image = MultiThreadDownloader(image_name, url, image_meta)
        import_image.run()


class MultiThreadDownloader(threading.Thread):

    def __init__(self, image_name, url, image_meta):
        super(MultiThreadDownloader, self).__init__()
        self.url = url
        # Set thread number
        self.threadnum = 8
        self.name = image_name
        self.image_osdistro = image_meta['os_version']
        r = requests.head(self.url)
        # Get the size of the download resource
        self.totalsize = int(r.headers['Content-Length'])
        self.target = '/'.join([CONF.image.sdk_image_repository, 'netboot',
                                self.image_osdistro,
                                self.name])

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
