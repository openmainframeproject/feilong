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

    def get_image_path_by_name(self, spawn_image_name):
        # eg. rhel7.2-s390x-netboot-<image_uuid>
        # eg. /install/netboot/rhel7.2/s390x/<image_uuid>/image_name.img
        name_split = spawn_image_name.split('-')
        # tmpdir can extract from 'tabdump site' but consume time
        tmpdir = '/install'
        """
        cmd = 'tabdump site'
        output = zvmtuils.execute(cmd)
        for i in output:
            if 'tmpdir' in i:
                tmpdir = i.split(',')[1]
        """
        image_uuid = name_split[-1]
        image_file_path = tmpdir + '/' + name_split[2] + '/' +\
                name_split[0] + '/' + name_split[1] + '/' + image_uuid +\
                '/' + CONF.zvm.user_root_vdev + '.img'
        return image_file_path

    def image_get_root_disk_size(self, spawn_image_name):
        """use 'hexdump' to get the root_disk_size."""
        image_file_path = self.get_image_path_by_name(spawn_image_name)
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

    def image_import(self, image_file_path, os_version):
        """import a spawn image to XCAT"""
        LOG.debug("Getting a spawn image...")
        image_uuid = image_file_path.split('/')[-1]
        disk_file_name = CONF.zvm.user_root_vdev + '.img'
        image_name = disk_file_name
        image_name = zvmutils.remove_prefix_of_unicode(image_name)
        spawn_path = self._pathutils.get_spawn_folder()

        time_stamp_dir = self._pathutils.make_time_stamp()
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)

        image_meta = {
                u'id': image_uuid,
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': os_version,
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                               u'provision_method': u'netboot'}
                }

        # Generate manifest.xml
        LOG.debug("Generating the manifest.xml as a part of bundle file for "
                    "image %s", image_meta['id'])
        self.zvmclient.generate_manifest_file(image_meta, image_name,
                                    disk_file_name, bundle_file_path)
        # Generate the image bundle
        LOG.debug("Generating bundle file for image %s", image_meta['id'])
        image_bundle_package = self.zvmclient.generate_image_bundle(
                                    spawn_path, time_stamp_dir,
                                    image_name, image_file_path)

        # Import image bundle to xCAT MN's image repository
        LOG.debug("Importing the image %s to xCAT", image_meta['id'])
        profile_str = image_uuid.replace('-', '_')
        image_profile = profile_str
        self.zvmclient.check_space_imgimport_xcat(image_bundle_package,
                        CONF.xcat.free_space_threshold,
                        CONF.xcat.master_node)
        self.zvmclient.image_import(image_bundle_package,
                                    image_profile)

        # TODO(Cao Biao): Add log info
        pass

    def image_query(self, imagekeyword=None):
        return self.zvmclient.image_query(imagekeyword)

    def image_delete(self, image_name):
        return self.zvmclient.image_delete(image_name)
