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
from zvmsdk import constants
from zvmsdk import database
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
        self._ImageDbOperator = database.ImageDbOperator()

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
        image_repository/prov_method/os_version/, for example,
        /opt/sdk/images/netboot/rhel7.2/90685d2b-167b.img"""

        try:
            target = self._get_image_path_by_name(image_name,
                image_meta['os_version'], constants.IMAGE_TYPE['DEPLOY'])
            self._pathutils.create_import_image_repository(
                image_meta['os_version'], constants.IMAGE_TYPE['DEPLOY'])
            self._scheme2backend(urlparse.urlparse(url).scheme).image_import(
                                                    image_name, url,
                                                    image_meta,
                                                    remote_host=remote_host)
            # Check md5 after import to ensure import a correct image
            # TODO change to use query imagename in db
            expect_md5sum = image_meta.get('md5sum')
            real_md5sum = self._get_md5sum(target)
            if expect_md5sum and expect_md5sum != real_md5sum:
                err = ("The md5sum after import is not same as source image,"
                       " the image has been broken")
                raise exception.SDKImageImportException(err)
            LOG.info("Image %s is import successfully" % image_name)
            disk_size_units = self._get_disk_size_units(target)
            image_size = self._get_image_size(target)
            self._ImageDbOperator.image_add_record(image_name,
                                         image_meta['os_version'],
                                         real_md5sum,
                                         disk_size_units,
                                         image_size)
        except KeyError:
            raise exception.SDKUnsupportedImageBackend("No backend found for"
                        " '%s'" % urlparse.urlparse(url).scheme)
        except Exception as err:
            msg = ("Import image to zvmsdk image repository error due to: %s"
                   % str(err))
            # Cleanup the image from image repository
            self._pathutils.remove_file(target)
            raise exception.SDKImageImportException(msg=msg)

    def _get_disk_size_units(self, image_path):
        """Return a string to indicate disk units in format 3390:CYL or 408200:
        BLK"""
        command = 'hexdump -n 48 -C %s' % image_path
        (rc, output) = commands.getstatusoutput(command)
        LOG.debug("hexdump result is %s" % output)
        if rc:
            msg = ("Error happened when executing command hexdump with"
                   "reason: %s" % output)
            LOG.error(msg)
            raise exception.ZVMImageError(msg=msg)

        try:
            root_disk_size = int(output[144:156])
            disk_units = output[220:223]
            root_disk_units = ':'.join([str(root_disk_size), disk_units])
        except ValueError:
            msg = ("Image file at %s is missing built-in disk size "
                   "metadata, it was probably not captured by SDK" %
                   image_path)
            raise exception.ZVMImageError(msg=msg)

        if 'FBA' not in output and 'CKD' not in output:
            msg = ("The image's disk type is not valid. Currently we only"
                      " support FBA and CKD disk")
            raise exception.ZVMImageError(msg=msg)

        LOG.debug("The image's root_disk_units is %s" % root_disk_units)
        return root_disk_units

    def _get_image_size(self, image_path):
        """Return disk size in bytes"""
        command = 'du -b %s' % image_path
        (rc, output) = commands.getstatusoutput(command)
        if rc:
            msg = ("Error happened when executing command du -b with"
                   "reason: %s" % output)
            LOG.error(msg)
            raise exception.ZVMImageError(msg=msg)
        size = output.split()[0]
        return size

    def _get_image_path_by_name(self, image_name, image_os_version, type):
        target = '/'.join([CONF.image.sdk_image_repository,
                           type,
                           image_os_version,
                           image_name])
        return target

    def _scheme2backend(self, scheme):
        return {
            "file": FilesystemBackend,
            "http": HTTPBackend,
    #         "https": HTTPSBackend
        }[scheme]

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
