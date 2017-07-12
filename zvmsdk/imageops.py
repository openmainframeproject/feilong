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

import urlparse

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk import log


LOG = log.LOG
CONF = config.CONF

_IMAGEOPS = None


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

    def image_import(self, url, image_meta={}, remote_host=None):
        parsed_url = urlparse.urlparse(url)
        if CONF.zvm.client_type == 'xcat':
            self.zvmclient.image_import(parsed_url.path,
                                        image_meta['os_version'],
                                        remote_host=remote_host)

    def image_query(self, imagekeyword=None):
        return self.zvmclient.image_query(imagekeyword)

    def image_delete(self, image_name):
        return self.zvmclient.image_delete(image_name)
