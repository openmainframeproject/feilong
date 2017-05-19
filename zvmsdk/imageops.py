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


import datetime
import os
import re
import shutil
import tarfile
import xml.dom.minidom as Dom
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

    def check_image_exist(self, image_uuid):
        """
        Check if the specific image exist or not
        :param image_uuid: eg. when we get an item from 'tabdump osimage'
        the imagename is 'rhel7.2-s390x-netboot-rhel72eckdbug1555_edbcfbb9
        _2e17_4876_befa_834f2f6b0f6c',the image_uuid should be
        'rhel72eckdbug1555_edbcfbb9_2e17_4876_befa_834f2f6b0f6c'
        """
        LOG.debug("Checking if the image %s exists or not." % image_uuid)
        image_uuid = image_uuid.replace('-', '_')
        res = self.zvmclient.lsdef_image(image_uuid)
        res_image = res['info']

        if '_' in str(res_image):
            return True
        else:
            return False

    def get_image_name(self, image_uuid):
        """Get the image name by image_uuid"""
        image_uuid = image_uuid.replace('-', '_')
        res = self.zvmclient.lsdef_image(image_uuid)
        res_image = res['info'][0][0]
        res_img_name = res_image.strip().split(" ")[0]

        if res_img_name:
            return res_img_name
        else:
            LOG.error("Fail to find the right image name")

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
                '/' + spawn_image_name + '.img'
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
            root_disk_size = int(output[144:156])
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

    def generate_manifest_file(self, image_meta, image_name, disk_file_name,
                               manifest_path):
        """
        Generate the manifest.xml file from glance's image metadata
        as a part of the image bundle.
        """
        image_id = image_meta['id']
        image_type = image_meta['properties']['image_type_xcat']
        os_version = image_meta['properties']['os_version']
        os_name = image_meta['properties']['os_name']
        os_arch = image_meta['properties']['architecture']
        prov_method = image_meta['properties']['provision_method']

        image_profile = image_id.replace('-', '_')
        image_name_xcat = '-'.join((os_version, os_arch,
                               prov_method, image_profile))
        rootimgdir_str = ('/install', prov_method, os_version,
                          os_arch, image_profile)
        rootimgdir = '/'.join(rootimgdir_str)
        today_date = datetime.date.today()
        last_use_date_string = today_date.strftime("%Y-%m-%d")
        is_deletable = "auto:last_use_date:" + last_use_date_string

        doc = Dom.Document()
        xcatimage = doc.createElement('xcatimage')
        doc.appendChild(xcatimage)

        # Add linuximage section
        imagename = doc.createElement('imagename')
        imagename_value = doc.createTextNode(image_name_xcat)
        imagename.appendChild(imagename_value)
        rootimagedir = doc.createElement('rootimgdir')
        rootimagedir_value = doc.createTextNode(rootimgdir)
        rootimagedir.appendChild(rootimagedir_value)
        linuximage = doc.createElement('linuximage')
        linuximage.appendChild(imagename)
        linuximage.appendChild(rootimagedir)
        xcatimage.appendChild(linuximage)

        # Add osimage section
        osimage = doc.createElement('osimage')
        manifest = {'imagename': image_name_xcat,
                    'imagetype': image_type,
                    'isdeletable': is_deletable,
                    'osarch': os_arch,
                    'osname': os_name,
                    'osvers': os_version,
                    'profile': image_profile,
                    'provmethod': prov_method}

        if 'image_comments' in image_meta['properties']:
            manifest['comments'] = image_meta['properties']['image_comments']

        for item in list(manifest.keys()):
            itemkey = doc.createElement(item)
            itemvalue = doc.createTextNode(manifest[item])
            itemkey.appendChild(itemvalue)
            osimage.appendChild(itemkey)
            xcatimage.appendChild(osimage)
            f = open(manifest_path + '/manifest.xml', 'w')
            f.write(doc.toprettyxml(indent=''))
            f.close()

        # Add the rawimagefiles section
        rawimagefiles = doc.createElement('rawimagefiles')
        xcatimage.appendChild(rawimagefiles)

        files = doc.createElement('files')
        files_value = doc.createTextNode(rootimgdir + '/' + disk_file_name)
        files.appendChild(files_value)

        rawimagefiles.appendChild(files)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(doc.toprettyxml(indent='  '))
        f.close()

        self._rewr(manifest_path)

        return manifest_path + '/manifest.xml'

    def _rewr(self, manifest_path):
        f = open(manifest_path + '/manifest.xml', 'r')
        lines = f.read()
        f.close()

        lines = lines.replace('\n', '')
        lines = re.sub(r'>(\s*)<', r'>\n\1<', lines)
        lines = re.sub(r'>[ \t]*(\S+)[ \t]*<', r'>\1<', lines)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(lines)
        f.close()

    def generate_image_bundle(self, spawn_path, time_stamp_dir,
                              image_name, image_file_path):
        """
        Generate the image bundle which is used to import to xCAT MN's
        image repository.
        """
        image_bundle_name = image_name + '.tar'
        tar_file = spawn_path + '/' + time_stamp_dir + '_' + image_bundle_name
        LOG.debug("The generate the image bundle file is %s", tar_file)

        # copy tmp image file to bundle path
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)
        image_file_copy = os.path.join(bundle_file_path, image_name)
        shutil.copyfile(image_file_path, image_file_copy)

        os.chdir(spawn_path)
        tarFile = tarfile.open(tar_file, mode='w')
        try:
            tarFile.add(time_stamp_dir)
            tarFile.close()
        except Exception as err:
            msg = ("Generate image bundle failed: %s" % err)
            LOG.error(msg)
            if os.path.isfile(tar_file):
                os.remove(tar_file)
            raise exception.ZVMImageError(msg=msg)
        finally:
            self._pathutils.clean_temp_folder(time_stamp_dir)

        return tar_file

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
        self.generate_manifest_file(image_meta, image_name,
                                    disk_file_name, bundle_file_path)
        # Generate the image bundle
        LOG.debug("Generating bundle file for image %s", image_meta['id'])
        image_bundle_package = self.generate_image_bundle(
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
