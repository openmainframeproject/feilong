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

    def image_get_root_disk_size(self, image_name):
        return self.zvmclient.image_get_root_disk_size(image_name)

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
