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
import functools
import hashlib
import urlparse
import requests
import threading
import os
import re
import shutil
import six
import string
import tempfile


from smutLayer import smut

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import database
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import returncode
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG

_LOCK = threading.Lock()
CHUNKSIZE = 4096

_SMUT_CLIENT = None


def get_smutclient():
    global _SMUT_CLIENT
    if _SMUT_CLIENT is None:
        try:
            _SMUT_CLIENT = zvmutils.import_object(
                'zvmsdk.smutclient.SMUTClient')
        except ImportError:
            LOG.error("Unable to get smutclient")
            raise ImportError
    return _SMUT_CLIENT


class SMUTClient(object):

    def __init__(self):
        self._smut = smut.SMUT()
        self._pathutils = zvmutils.PathUtils()
        self._NetDbOperator = database.NetworkDbOperator()
        self._GuestDbOperator = database.GuestDbOperator()
        self._ImageDbOperator = database.ImageDbOperator()

    def _request(self, requestData):
        try:
            results = self._smut.request(requestData)
        except Exception as err:
            LOG.error('SMUT internal parse encounter error')
            raise exception.SDKInternalError(msg=err, modID='smut')

        def _is_smut_internal_error(results):
            internal_error_list = returncode.SMUT_INTERNAL_ERROR
            for error in internal_error_list:
                if results['overallRC'] != error[0]:
                    # overallRC does not match, continue next
                    continue
                if error[1] is not None and results['rc'] != error[1]:
                    # rc match failed
                    continue
                if error[2] is not None and results['rs'] not in error[2]:
                    # rs match failed
                    continue
                # All match finish successfully, return true
                return True
            return False

        if results['overallRC'] != 0:
            results.pop('logEntries')
            # Check whether this smut error belongs to internal error, if so,
            # raise internal error, otherwise raise clientrequestfailed error
            if _is_smut_internal_error(results):
                msg = "SMUT internal error. Results: %s" % str(results)
                LOG.error(msg)
                raise exception.SDKInternalError(msg=msg,
                                                    modID='smut',
                                                    results=results)
            else:
                msg = ("SMUT request failed. RequestData: '%s', Results: '%s'"
                       % (requestData, str(results)))
                raise exception.SDKSMUTRequestFailed(results, msg)
        return results

    def get_guest_temp_path(self, userid, module):
        return self._pathutils.get_guest_temp_path(userid, module)

    def _generate_vdev(self, base, offset):
        """Generate virtual device number based on base vdev
        :param base: base virtual device number, string of 4 bit hex.
        :param offset: offset to base, integer.
        """
        vdev = hex(int(base, 16) + offset)[2:]
        return vdev.rjust(4, '0')

    def generate_disk_vdev(self, start_vdev=None, offset=0):
        """Generate virtual device number for disks
        :param offset: offset of user_root_vdev.
        :return: virtual device number, string of 4 bit hex.
        """
        if not start_vdev:
            start_vdev = CONF.zvm.user_root_vdev
        vdev = self._generate_vdev(start_vdev, offset)
        if offset >= 0 and offset < 254:
            return vdev
        else:
            msg = ("Failed to generate disk vdev, invalid virtual device"
                   "number for disk:%s" % vdev)
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=2, msg=msg)

    def add_mdisks(self, userid, disk_list, start_vdev=None):
        """Add disks for the userid

        :disks: A list dictionary to describe disk info, for example:
                disk: [{'size': '1g',
                       'format': 'ext3',
                       'disk_pool': 'ECKD:eckdpool1'}]

        """

        for idx, disk in enumerate(disk_list):
            vdev = self.generate_disk_vdev(start_vdev=start_vdev, offset=idx)
            self._add_mdisk(userid, disk, vdev)

    def remove_mdisks(self, userid, vdev_list):
        for vdev in vdev_list:
            self._remove_mdisk(userid, vdev)

    def get_image_performance_info(self, userid):
        """Get CPU and memory usage information.

        :userid: the zvm userid to be queried
        """
        pi_dict = self.image_performance_query([userid])
        return pi_dict.get(userid.upper(), None)

    def _parse_vswitch_inspect_data(self, rd_list):
        """ Parse the Virtual_Network_Vswitch_Query_IUO_Stats data to get
        inspect data.
        """
        def _parse_value(data_list, idx, keyword, offset):
            return idx + offset, data_list[idx].rpartition(keyword)[2].strip()

        vsw_dict = {}
        with zvmutils.expect_invalid_resp_data():
            # vswitch count
            idx = 0
            idx, vsw_count = _parse_value(rd_list, idx, 'vswitch count:', 2)
            vsw_dict['vswitch_count'] = int(vsw_count)

            # deal with each vswitch data
            vsw_dict['vswitches'] = []
            for i in range(vsw_dict['vswitch_count']):
                vsw_data = {}
                # skip vswitch number
                idx += 1
                # vswitch name
                idx, vsw_name = _parse_value(rd_list, idx, 'vswitch name:', 1)
                vsw_data['vswitch_name'] = vsw_name
                # uplink count
                idx, up_count = _parse_value(rd_list, idx, 'uplink count:', 1)
                # skip uplink data
                idx += int(up_count) * 9
                # skip bridge data
                idx += 8
                # nic count
                vsw_data['nics'] = []
                idx, nic_count = _parse_value(rd_list, idx, 'nic count:', 1)
                nic_count = int(nic_count)
                for j in range(nic_count):
                    nic_data = {}
                    idx, nic_id = _parse_value(rd_list, idx, 'nic_id:', 1)
                    userid, toss, vdev = nic_id.partition(' ')
                    nic_data['userid'] = userid
                    nic_data['vdev'] = vdev
                    idx, nic_data['nic_fr_rx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_rx:', 1
                                                              )
                    idx, nic_data['nic_fr_rx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_rx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_err:', 1
                                                            )
                    idx, nic_data['nic_fr_tx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_tx:', 1
                                                              )
                    idx, nic_data['nic_fr_tx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_tx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_err:', 1
                                                            )
                    idx, nic_data['nic_rx'] = _parse_value(rd_list, idx,
                                                           'nic_rx:', 1
                                                           )
                    idx, nic_data['nic_tx'] = _parse_value(rd_list, idx,
                                                           'nic_tx:', 1
                                                           )
                    vsw_data['nics'].append(nic_data)
                # vlan count
                idx, vlan_count = _parse_value(rd_list, idx, 'vlan count:', 1)
                # skip vlan data
                idx += int(vlan_count) * 3
                # skip the blank line
                idx += 1

                vsw_dict['vswitches'].append(vsw_data)

        return vsw_dict

    def _is_vdev_valid(self, vdev, vdev_info):
        for used_vdev in vdev_info:
            if (((int(vdev, 16) >= int(used_vdev, 16)) and
                 (int(vdev, 16) <= int(used_vdev, 16) + 2)) or
                ((int(vdev, 16) < int(used_vdev, 16)) and
                 (int(vdev, 16) >= int(used_vdev, 16) - 2))):
                return False

        return True

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Querying power stat of %s' % userid)
        requestData = "PowerVM " + userid + " status"
        action = "query power state of '%s'" % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            results = self._request(requestData)
        with zvmutils.expect_invalid_resp_data(results):
            status = results['response'][0].partition(': ')[2]
        return status

    def guest_start(self, userid):
        """Power on VM."""
        requestData = "PowerVM " + userid + " on"
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_stop(self, userid, **kwargs):
        """Power off VM."""
        requestData = "PowerVM " + userid + " off"

        if 'timeout' in kwargs.keys() and kwargs['timeout']:
            requestData += ' --maxwait ' + str(kwargs['timeout'])
        if 'poll_interval' in kwargs.keys() and kwargs['poll_interval']:
            requestData += ' --poll ' + str(kwargs['poll_interval'])

        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_softstop(self, userid, **kwargs):
        """Power off VM gracefully, it will call shutdown os then
            deactivate vm"""
        requestData = "PowerVM " + userid + " softoff"
        if 'timeout' in kwargs.keys() and kwargs['timeout']:
            requestData += ' --maxwait ' + str(kwargs['timeout'])
        if 'poll_interval' in kwargs.keys() and kwargs['poll_interval']:
            requestData += ' --poll ' + str(kwargs['poll_interval'])

        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_pause(self, userid):
        requestData = "PowerVM " + userid + " pause"
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_unpause(self, userid):
        requestData = "PowerVM " + userid + " unpause"
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_reboot(self, userid):
        requestData = ' '.join(("PowerVM", userid, "reboot"))
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_reset(self, userid):
        requestData = ' '.join(("PowerVM", userid, "reset"))
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def create_vm(self, userid, cpu, memory, disk_list, profile):
        """ Create VM and add disks if specified. """
        rd = ('makevm %(uid)s directory LBYONLY %(mem)im %(pri)s '
              '--cpus %(cpu)i --profile %(prof)s' %
              {'uid': userid, 'mem': memory,
               'pri': const.ZVM_USER_DEFAULT_PRIVILEGE,
               'cpu': cpu, 'prof': profile})

        if CONF.zvm.default_admin_userid:
            rd += (' --logonby "%s"' % CONF.zvm.default_admin_userid)

        if disk_list and 'is_boot_disk' in disk_list[0]:
            ipl_disk = CONF.zvm.user_root_vdev
            rd += (' --ipl %s' % ipl_disk)

        action = "create userid '%s'" % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

        # Add the guest to db immediately after user created
        action = "add guest '%s' to database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.add_guest(userid)

        # Continue to add disk
        if disk_list:
            # Add disks for vm
            self.add_mdisks(userid, disk_list)

    def _add_mdisk(self, userid, disk, vdev):
        """Create one disk for userid

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """
        size = disk['size']
        fmt = disk.get('format')
        disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
        [diskpool_type, diskpool_name] = disk_pool.split(':')

        if (diskpool_type.upper() == 'ECKD'):
            action = 'add3390'
        else:
            action = 'add9336'

        rd = ' '.join(['changevm', userid, action, diskpool_name,
                       vdev, size, '--mode MR'])
        if fmt:
            rd += (' --filesystem %s' % fmt.lower())

        action = "add mdisk to userid '%s'" % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

    def get_vm_list(self):
        """Get the list of guests that are created by SDK
        return userid list"""
        action = "list all guests in database"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            guests = self._GuestDbOperator.get_guest_list()
        # guests is a list of tuple (uuid, userid, metadata, comments)
        userid_list = []
        for g in guests:
            userid_list.append(g[1])
        return userid_list

    def _remove_mdisk(self, userid, vdev):
        rd = ' '.join(('changevm', userid, 'removedisk', vdev))
        action = "remove disk with vdev '%s' from userid '%s'" % (vdev, userid)
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

    def guest_authorize_iucv_client(self, userid, client=None):
        """Punch a script that used to set the authorized client userid in vm
        If the guest is in log off status, the change will take effect when
        the guest start up at first time.
        If the guest is in active status, power off and power on are needed
        for the change to take effect.

        :param str guest: the user id of the vm
        :param str client: the user id of the client that can communicate to
               guest using IUCV"""

        client = client or zvmutils.get_smut_userid()

        iucv_path = "/tmp/" + userid
        if not os.path.exists(iucv_path):
            os.makedirs(iucv_path)
        iucv_auth_file = iucv_path + "/iucvauth.sh"
        zvmutils.generate_iucv_authfile(iucv_auth_file, client)

        try:
            requestData = "ChangeVM " + userid + " punchfile " + \
                iucv_auth_file + " --class x"
            self._request(requestData)
        except exception.SDKSMUTRequestFailed as err:
            msg = ("Failed to punch IUCV auth file to userid '%s'. SMUT error:"
                   " %s" % (userid, err.format_message()))
            LOG.error(msg)
            raise exception.SDKSMUTRequestFailed(err.results, msg)
        finally:
            self._pathutils.clean_temp_folder(iucv_path)

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        """ Deploy image and punch config driver to target """
        # Get image location (TODO: update this image location)
        image_file = self._get_image_path_by_name(image_name)
        # Unpack image file to root disk
        vdev = vdev or CONF.zvm.user_root_vdev
        cmd = ['sudo', '/opt/zthin/bin/unpackdiskimage', userid, vdev,
               image_file]
        with zvmutils.expect_and_reraise_internal_error(modID='guest'):
            (rc, output) = zvmutils.execute(cmd)
        if rc != 0:
            err_msg = ("unpackdiskimage failed with return code: %d." % rc)
            err_output = ""
            output_lines = output.split('\n')
            for line in output_lines:
                if line.__contains__("ERROR:"):
                    err_output += ("\\n" + line.strip())
            LOG.error(err_msg + err_output)
            raise exception.SDKGuestOperationError(rs=3, userid=userid,
                                                   unpack_rc=rc,
                                                   err=err_output)

        # Purge guest reader to clean dirty data
        rd = ("changevm %s purgerdr" % userid)
        action = "purge reader of '%s'" % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

        # Punch transport files if specified
        if transportfiles:
            # Copy transport file to local
            try:
                tmp_trans_dir = tempfile.mkdtemp()
                local_trans = tmp_trans_dir + '/cfgdrv'
                if remotehost:
                    cmd = ["/usr/bin/scp", "-B",
                           ("%s:%s" % (remotehost, transportfiles)),
                           local_trans]
                else:
                    cmd = ["/usr/bin/cp", transportfiles, local_trans]
                with zvmutils.expect_and_reraise_internal_error(modID='guest'):
                    (rc, output) = zvmutils.execute(cmd)
                if rc != 0:
                    err_msg = ("copy config drive to local failed with"
                               "return code: %d." % rc)
                    LOG.error(err_msg)
                    raise exception.SDKGuestOperationError(rs=4, userid=userid,
                                                           cp_rc=rc)

                # Punch config drive to guest userid
                rd = ("changevm %(uid)s punchfile %(file)s --class X" %
                      {'uid': userid, 'file': local_trans})
                action = "punch config drive to userid '%s'" % userid
                with zvmutils.log_and_reraise_smut_request_failed(action):
                    self._request(rd)
            finally:
                # remove the local temp config drive folder
                self._pathutils.clean_temp_folder(tmp_trans_dir)
        # Authorize iucv client
        self.guest_authorize_iucv_client(userid)

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6):
        # Get the vm status
        power_state = self.get_power_state(userid)
        # Power on the vm if it is inactive
        if power_state == 'off':
            msg = ('The vm %(vm)s is powered off, please start up it '
                   'before capture' % userid)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)

        # Make sure the iucv channel is ready for communication on source vm
        try:
            self.execute_cmd(userid, 'pwd')
        except exception.SDKSMUTRequestFailed as err:
            msg = ('Failed to check iucv status on capture source vm '
                   '%(vm)s with error %(err)s' % {'vm': userid,
                                        'err': err.results['response'][0]})
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        # Get the os version of the vm
        try:
            os_version = self._guest_get_os_version(userid)
        except exception.SDKSMUTRequestFailed as err:
            msg = ('Failed to execute command on capture source vm %(vm)s'
                   'to get os version with error %(err)s' % {'vm': userid,
                                        'err': err.results['response'][0]})
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        except Exception as err:
            msg = ('Error happened when parsing os version on source vm '
                   '%(vm)s with error: %(err)s' % {'vm': userid,
                                                   'err': six.text_type(err)})
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        LOG.info('The os version of source vm is %s' % os_version)
        # Find the root device according to the capture type
        try:
            capture_devices = self._get_capture_devices(userid, capture_type)
        except exception.SDKSMUTRequestFailed as err:
            msg = ('Failed to execute command on source vm %(vm)s to get the '
                   'devices for capture with error %(err)s' % {'vm': userid,
                                        'err': err.results['response'][0]})
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        except Exception as err:
            msg = ('Internal error happened when getting the devices for '
                   'capture on source vm %(vm)s with error %(err)s' %
                   {'vm': userid,
                    'err': six.text_type(err)})
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        except exception.SDKGuestOperationError:
            raise
        # Shutdown the vm before capture
        self.guest_softstop(userid)

        # Prepare directory for writing image file
        image_temp_dir = '/'.join((CONF.image.sdk_image_repository,
                                   const.IMAGE_TYPE['CAPTURE'],
                                   os_version,
                                   image_name))
        self._pathutils.mkdir_if_not_exist(image_temp_dir)

        # Call creatediskimage to capture a vm to generate an image
        # TODO:(nafei) to support multiple disk capture
        vdev = capture_devices[0]
        image_file_name = '.'.join((vdev, 'img'))
        image_file_path = '/'.join((image_temp_dir, image_file_name))
        cmd = ['sudo', '/opt/zthin/bin/creatediskimage', userid, vdev,
               image_file_path]
        with zvmutils.expect_and_reraise_internal_error(modID='guest'):
            (rc, output) = zvmutils.execute(cmd)
        if rc != 0:
            err_msg = ("creatediskimage failed with return code: %d." % rc)
            err_output = ""
            output_lines = output.split('\n')
            for line in output_lines:
                if line.__contains__("ERROR:"):
                    err_output += ("\\n" + line.strip())
            LOG.error(err_msg + err_output)
            self._pathutils.clean_temp_folder(image_temp_dir)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=err_output)

        # Move the generated image to netboot folder
        image_final_dir = '/'.join([CONF.image.sdk_image_repository,
                                    const.IMAGE_TYPE['DEPLOY'],
                                    os_version,
                                    image_name])
        image_final_path = '/'.join((image_final_dir,
                                     image_file_name))
        self._pathutils.mkdir_if_not_exist(image_final_dir)
        cmd = ['mv', image_file_path, image_final_path]
        with zvmutils.expect_and_reraise_internal_error(modID='guest'):
            (rc, output) = zvmutils.execute(cmd)
            if rc != 0:
                err_msg = ("move image file from staging to netboot "
                           "folder failed with return code: %d." % rc)
                LOG.error(err_msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       err=err_msg)

        # Get md5sum of image
        real_md5sum = self._get_md5sum(image_final_path)
        # Get disk_size_units of image
        disk_size_units = self._get_disk_size_units(image_final_path)
        # Get the image physical size
        image_size = self._get_image_size(image_final_path)
        # Create the image record in image database
        self._ImageDbOperator.image_add_record(image_name, os_version,
            real_md5sum, disk_size_units, image_size,
            const.IMAGE_TYPE['DEPLOY'])
        LOG.info("Image %s is import successfully" % image_name)

    def _guest_get_os_version(self, userid):
        os_version = ''
        release_file = self.execute_cmd(userid, 'ls /etc/*-release')
        if '/etc/os-release' in release_file:
            # Parse os-release file, part of the output looks like:
            # NAME="Red Hat Enterprise Linux Server"
            # ID="rhel"
            # VERSION_ID="7.0"

            release_info = self.execute_cmd(userid, 'cat /etc/os-release')
            release_dict = {}
            for item in release_info:
                if item:
                    release_dict[item.split('=')[0]] = item.split('=')[1]
            distro = release_dict['ID']
            version = release_dict['VERSION_ID']
            if '"' in distro:
                distro = eval(distro)
            if '"' in version:
                version = eval(version)
            os_version = '%s%s' % (distro, version)
            return os_version

        elif '/etc/redhat-release' in release_file:
            # The output looks like:
            # "Red Hat Enterprise Linux Server release 6.7 (Santiago)"
            distro = 'rhel'
            release_info = self.execute_cmd(userid, 'cat /etc/redhat-release')
            distro_version = release_info[0].split()[6]
            os_version = ''.join((distro, distro_version))
            return os_version
        elif '/etc/SuSE-release' in release_file:
            # The output for this file looks like:
            # SUSE Linux Enterprise Server 11 (s390x)
            # VERSION = 11
            # PATCHLEVEL = 3
            distro = 'sles'
            release_info = self.execute_cmd(userid, 'cat /etc/SuSE-release')
            LOG.debug('OS release info is %s' % release_info)
            release_version = '.'.join((release_info[1].split('=')[1].strip(),
                                     release_info[2].split('=')[1].strip()))
            os_version = ''.join((distro, release_version))
            return os_version

    def _get_capture_devices(self, userid, capture_type='rootonly'):
        capture_devices = []
        if capture_type == 'rootonly':
            # Parse the /proc/cmdline to get root devices
            proc_cmdline = self.execute_cmd(userid, 'cat /proc/cmdline '
                            '| tr " " "\\n" | grep -a "^root=" | cut -c6-')
            root_device_info = proc_cmdline[0]
            if not root_device_info:
                msg = ('Unable to get useful info from /proc/cmdline to '
                      'locate the device associated with the root directory '
                      'on capture source vm %s' % userid)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            else:
                if 'UUID=' in root_device_info:
                    uuid = root_device_info.split()[0].split('=')[1]
                    root_device = '/'.join(('/dev/disk/by-uuid', uuid))
                elif 'LABEL=' in root_device_info:
                    label = root_device_info.split()[0].split('=')[1]
                    root_device = '/'.join(('/dev/disk/by-label', label))
                elif 'mapper' in root_device_info:
                    msg = ('Capturing a disk with root filesystem on logical'
                           ' volume is not supported')
                    raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                           msg=msg)
                else:
                    root_device = root_device_info

            root_device_node = self.execute_cmd(userid, 'readlink -f %s' %
                                                root_device)[0]
            # Get device node vdev by node name
            cmd = ('cat /proc/dasd/devices | grep -i "is %s" ' %
                    root_device_node.split('/')[-1].rstrip(string.digits))
            result = self.execute_cmd(userid, cmd)[0]
            root_device_vdev = result.split()[0][4:8]
            capture_devices.append(root_device_vdev)
            return capture_devices
        else:
            # For sysclone, parse the user directory entry to get the devices
            # for capture, leave for future
            pass

    def grant_user_to_vswitch(self, vswitch_name, userid):
        """Set vswitch to grant user."""
        smut_userid = zvmutils.get_smut_userid()
        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Vswitch_Set_Extended' % smut_userid,
            "--operands",
            "-k switch_name=%s" % vswitch_name,
            "-k grant_userid=%s" % userid,
            "-k persist=YES"))

        try:
            self._request(requestData)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to grant user %s to vswitch %s, error: %s"
                      % (userid, vswitch_name, err.format_message()))
            raise

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        """Revoke user for vswitch."""
        smut_userid = zvmutils.get_smut_userid()
        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Vswitch_Set_Extended' % smut_userid,
            "--operands",
            "-k switch_name=%s" % vswitch_name,
            "-k revoke_userid=%s" % userid,
            "-k persist=YES"))

        try:
            self._request(requestData)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to revoke user %s from vswitch %s, error: %s"
                      % (userid, vswitch_name, err.format_message()))
            raise

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        if uid_list == []:
            return {}

        if not isinstance(uid_list, list):
            uid_list = [uid_list]

        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Image_Performance_Query" % smut_userid,
            "--operands",
            '-T "%s"' % (' '.join(uid_list)),
            "-c %d" % len(uid_list)))
        action = "get performance info of userid '%s'" % str(uid_list)
        with zvmutils.log_and_reraise_smut_request_failed(action):
            results = self._request(rd)

        ipq_kws = {
            'userid': "Guest name:",
            'guest_cpus': "Guest CPUs:",
            'used_cpu_time': "Used CPU time:",
            'elapsed_cpu_time': "Elapsed time:",
            'min_cpu_count': "Minimum CPU count:",
            'max_cpu_limit': "Max CPU limit:",
            'samples_cpu_in_use': "Samples CPU in use:",
            'samples_cpu_delay': "Samples CPU delay:",
            'used_memory': "Used memory:",
            'max_memory': "Max memory:",
            'min_memory': "Minimum memory:",
            'shared_memory': "Shared memory:",
        }

        pi_dict = {}
        pi = {}
        rpi_list = ('\n'.join(results['response'])).split("\n\n")
        for rpi in rpi_list:
            try:
                pi = zvmutils.translate_response_to_dict(rpi, ipq_kws)
            except exception.SDKInternalError as err:
                emsg = err.format_message()
                # when there is only one userid queried and this userid is
                # in 'off'state, the smcli will only returns the queried
                # userid number, no valid performance info returned.
                if(emsg.__contains__("No value matched with keywords.")):
                    continue
                else:
                    raise err
            for k, v in pi.items():
                pi[k] = v.strip('" ')
            if pi.get('userid') is not None:
                pi_dict[pi['userid']] = pi

        return pi_dict

    def get_vm_nic_vswitch_info(self, vm_id):
        """
        Get NIC and switch mapping for the specified virtual machine.
        """
        switch_info = self._NetDbOperator.switch_select_record_for_userid(
                                                                    vm_id)
        switch_dict = {}
        for item in switch_info:
            switch_dict[item[1]] = item[2]

        LOG.debug("Switch info the %(vm_id)s is %(switch_dict)s",
                  {"vm_id": vm_id, "switch_dict": switch_dict})
        return switch_dict

    def virtual_network_vswitch_query_iuo_stats(self):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query_IUO_Stats" %
            smut_userid,
            "--operands",
            '-T "%s"' % smut_userid,
            '-k "switch_name=*"'
            ))
        action = "query vswitch usage info"
        with zvmutils.log_and_reraise_smut_request_failed(action):
            results = self._request(rd)
        return self._parse_vswitch_inspect_data(results['response'])

    def get_host_info(self):
        with zvmutils.log_and_reraise_smut_request_failed():
            results = self._request("getHost general")
        host_info = zvmutils.translate_response_to_dict(
            '\n'.join(results['response']), const.RINV_HOST_KEYWORDS)

        return host_info

    def get_diskpool_info(self, pool):
        with zvmutils.log_and_reraise_smut_request_failed():
            results = self._request("getHost diskpoolspace %s" % pool)
        dp_info = zvmutils.translate_response_to_dict(
            '\n'.join(results['response']), const.DISKPOOL_KEYWORDS)

        return dp_info

    def get_vswitch_list(self):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query" % smut_userid,
            "--operands",
            "-s \'*\'"))
        try:
            result = self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            if ((err.results['rc'] == 212) and (err.results['rs'] == 40)):
                LOG.warning("No Virtual switch in the host")
                return []
            else:
                LOG.error("Failed to get vswitch list, error: %s" %
                          err.format_message())
                raise

        with zvmutils.expect_invalid_resp_data():
            if (not result['response'] or not result['response'][0]):
                return []
            else:
                data = '\n'.join([s for s in result['response']
                                  if isinstance(s, const._TSTR_OR_TUNI)])
                output = re.findall('VSWITCH:  Name: (.*)', data)
                return output

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Set_Extended" %
            smut_userid,
            "--operands",
            "-k grant_userid=%s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k user_vlan_id=%s" % vlan_id,
            "-k persist=YES"))

        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to set VLAN ID %s on vswitch %s for user %s, "
                      "error: %s" %
                      (vlan_id, vswitch_name, userid, err.format_message()))
            raise

    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='IP',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):

        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Create_Extended" %
            smut_userid,
            "--operands",
            '-k switch_name=%s' % name))
        if rdev is not None:
            rd += " -k real_device_address" +\
                  "=\'%s\'" % rdev.replace(',', ' ')

        if controller != '*':
            rd += " -k controller_name=%s" % controller
        rd = ' '.join((rd,
                       "-k connection_value=%s" % connection,
                       "-k queue_memory_limit=%s" % queue_mem,
                       "-k transport_type=%s" % network_type,
                       "-k vlan_id=%s" % vid,
                       "-k persist=%s" % (persist and 'YES' or 'NO')))
        # Only if vswitch is vlan awared, port_type, gvrp and native_vid are
        # allowed to specified
        if isinstance(vid, int) or vid.upper() != 'UNAWARE':
            rd = ' '.join((rd,
                           "-k port_type=%s" % port_type,
                           "-k gvrp_value=%s" % gvrp,
                           "-k native_vlanid=%s" % native_vid))

        if router is not None:
            rd += " -k routing_value=%s" % router

        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to create vswitch %s, error: %s" %
                      (name, err.format_message()))
            raise

    def set_vswitch(self, switch_name, **kwargs):
        """Set vswitch"""
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Set_Extended" %
            smut_userid,
            "--operands",
            "-k switch_name=%s" % switch_name))

        for k, v in kwargs.items():
            rd = ' '.join((rd,
                           "-k %(key)s=\'%(value)s\'" %
                           {'key': k, 'value': v}))

        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to set vswitch %s, error: %s" %
                      (switch_name, err.format_message()))
            raise

    def delete_vswitch(self, switch_name, persist=True):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Delete_Extended" %
            smut_userid,
            "--operands",
            "-k switch_name=%s" % switch_name,
            "-k persist=%s" % (persist and 'YES' or 'NO')))

        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            results = err.results
            if ((results['rc'] == 212) and
                (results['rs'] == 40)):
                LOG.warning("Vswitch %s does not exist", switch_name)
                return
            else:
                LOG.error("Failed to delete vswitch %s, error: %s" %
                      (switch_name, err.format_message()))
                raise

    def create_nic(self, userid, vdev=None, nic_id=None,
                   mac_addr=None, active=False):
        ports_info = self._NetDbOperator.switch_select_table()
        vdev_info = []
        for p in ports_info:
            if p[0] == userid.upper():
                vdev_info.append(p[1])

        if len(vdev_info) == 0:
            # no nic defined for the guest
            if vdev is None:
                nic_vdev = CONF.zvm.default_nic_vdev
            else:
                nic_vdev = vdev
        else:
            if vdev is None:
                used_vdev = max(vdev_info)
                nic_vdev = str(hex(int(used_vdev, 16) + 3))[2:]
            else:
                if self._is_vdev_valid(vdev, vdev_info):
                    nic_vdev = vdev
                else:
                    errmsg = ("The specified virtual device number %s "
                              "has already been used." % vdev)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
        if len(nic_vdev) > 4:
            errmsg = ("Virtual device number %s is not valid" % nic_vdev)
            raise exception.SDKNetworkOperationError(rs=2,
                                                     msg=errmsg)
        LOG.debug('Nic attributes: vdev is %(vdev)s, '
                  'ID is %(id)s, address is %(address)s',
                  {'vdev': nic_vdev,
                   'id': nic_id or 'not specified',
                   'address': mac_addr or 'not specified'})
        self._create_nic(userid, nic_vdev, nic_id=nic_id,
                         mac_addr=mac_addr, active=active)
        return nic_vdev

    def _create_nic(self, userid, vdev, nic_id=None, mac_addr=None,
                    active=False):
        if active:
            # Get the vm status
            power_state = self.get_power_state(userid)
            if power_state == 'off':
                msg = ('The vm %(vm)s is powered off' % userid)
                raise exception.SDKNetworkOperationError(rs=5, userid=userid,
                                                         msg=msg)

        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Adapter_Create_Extended_DM' %
            userid,
            "--operands",
            "-k image_device_number=%s" % vdev,
            "-k adapter_type=QDIO"))

        if mac_addr is not None:
            mac = ''.join(mac_addr.split(':'))[6:]
            requestData += ' -k mac_id=%s' % mac

        try:
            self._request(requestData)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to create nic %s for user %s in "
                      "the guest's user direct,, error: %s" %
                      (vdev, userid, err.format_message()))
            raise

        if active:
            if mac_addr is not None:
                LOG.warning("Ignore the mac address %s when "
                            "adding nic on an active system" % mac_addr)
            requestData = ' '.join((
                'SMAPI %s API Virtual_Network_Adapter_Create_Extended' %
                userid,
                "--operands",
                "-k image_device_number=%s" % vdev,
                "-k adapter_type=QDIO"))

            try:
                self._request(requestData)
            except (exception.SDKSMUTRequestFailed,
                    exception.SDKInternalError) as err1:
                msg1 = err1.format_message()
                persist_OK = True
                requestData = ' '.join((
                    'SMAPI %s API Virtual_Network_Adapter_Delete_DM' % userid,
                    "--operands",
                    '-v %s' % vdev))
                try:
                    self._request(requestData)
                except (exception.SDKSMUTRequestFailed,
                        exception.SDKInternalError) as err2:
                    results = err2.results
                    msg2 = err2.format_message()
                    if ((results['rc'] == 404) and
                        (results['rs'] == 8)):
                        persist_OK = True
                    else:
                        persist_OK = False
                if persist_OK:
                    raise err1
                else:
                    raise exception.SDKNetworkOperationError(rs=4,
                                    nic=vdev, userid=userid,
                                    create_err=msg1, revoke_err=msg2)

        self._NetDbOperator.switch_add_record(userid, vdev, port=nic_id)

    def get_user_direct(self, userid):
        with zvmutils.log_and_reraise_smut_request_failed():
            results = self._request("getvm %s directory" % userid)
        return results.get('response', [])

    def delete_nic(self, userid, vdev, active=False):
        if active:
            # Get the vm status
            power_state = self.get_power_state(userid)
            if power_state == 'off':
                msg = ('The vm %(vm)s is powered off' % userid)
                raise exception.SDKNetworkOperationError(rs=5, userid=userid,
                                                         msg=msg)
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Adapter_Delete_DM" %
            userid,
            "--operands",
            '-v %s' % vdev))
        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            results = err.results
            emsg = err.format_message()
            if ((results['rc'] == 404) and
                (results['rs'] == 8)):
                LOG.warning("Virtual device %s does not exist in "
                            "the guest's user direct", vdev)
            else:
                LOG.error("Failed to delete nic %s for %s in "
                          "the guest's user direct, error: %s" %
                          (vdev, userid, emsg))
                raise

        self._NetDbOperator.switch_delete_record_for_nic(userid, vdev)
        if active:
            rd = ' '.join((
                "SMAPI %s API Virtual_Network_Adapter_Delete" %
                userid,
                "--operands",
                '-v %s' % vdev))
            try:
                self._request(rd)
            except exception.SDKSMUTRequestFailed as err:
                results = err.results
                emsg = err.format_message()
                if ((results['rc'] == 204) and
                    (results['rs'] == 8)):
                    LOG.warning("Virtual device %s does not exist on "
                                "the active guest system", vdev)
                else:
                    LOG.error("Failed to delete nic %s for %s on "
                              "the active guest system, error: %s" %
                              (vdev, userid, emsg))
                    raise

    def _couple_nic(self, userid, vdev, vswitch_name,
                    active=False):
        """Couple NIC to vswitch by adding vswitch into user direct."""
        if active:
            # Get the vm status
            power_state = self.get_power_state(userid)
            if power_state == 'off':
                msg = ('The vm %(vm)s is powered off' % userid)
                raise exception.SDKNetworkOperationError(rs=5, userid=userid,
                                                         msg=msg)
        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Connect_Vswitch_DM",
            "--operands",
            "-v %s" % vdev,
            "-n %s" % vswitch_name))

        try:
            self._request(requestData)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to couple nic %s to vswitch %s for user %s "
                      "in the guest's user direct, error: %s" %
                      (vdev, vswitch_name, userid, err.format_message()))
            raise

        # the inst must be active, or this call will failed
        if active:
            requestData = ' '.join((
                'SMAPI %s' % userid,
                'API Virtual_Network_Adapter_Connect_Vswitch',
                "--operands",
                "-v %s" % vdev,
                "-n %s" % vswitch_name))

            try:
                self._request(requestData)
            except (exception.SDKSMUTRequestFailed,
                    exception.SDKInternalError) as err1:
                results1 = err1.results
                msg1 = err1.format_message()
                if ((results1 is not None) and
                    (results1['rc'] == 204) and
                    (results1['rs'] == 20)):
                    LOG.warning("Virtual device %s already connected "
                                "on the active guest system", vdev)
                else:
                    persist_OK = True
                    requestData = ' '.join((
                        'SMAPI %s' % userid,
                        'API Virtual_Network_Adapter_Disconnect_DM',
                        "--operands",
                        '-v %s' % vdev))
                    try:
                        self._request(requestData)
                    except (exception.SDKSMUTRequestFailed,
                            exception.SDKInternalError) as err2:
                        results2 = err2.results
                        msg2 = err2.format_message()
                        if ((results2 is not None) and
                            (results2['rc'] == 212) and
                            (results2['rs'] == 32)):
                            persist_OK = True
                        else:
                            persist_OK = False
                    if persist_OK:
                        raise err1
                    else:
                        raise exception.SDKNetworkOperationError(rs=3,
                                    nic=vdev, vswitch=vswitch_name,
                                    couple_err=msg1, revoke_err=msg2)

        """Update information in switch table."""
        self._NetDbOperator.switch_update_record_with_switch(userid, vdev,
                                                             vswitch_name)

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False):
        """Couple nic to vswitch."""
        if active:
            msg = ("both in the user direct of guest %s and on "
                   "the active guest system" % userid)
        else:
            msg = "in the user direct of guest %s" % userid
        LOG.debug("Connect nic %s to switch %s %s",
                  nic_vdev, vswitch_name, msg)
        self._couple_nic(userid, nic_vdev, vswitch_name, active=active)

    def _uncouple_nic(self, userid, vdev, active=False):
        """Uncouple NIC from vswitch"""
        if active:
            # Get the vm status
            power_state = self.get_power_state(userid)
            if power_state == 'off':
                msg = ('The vm %(vm)s is powered off' % userid)
                raise exception.SDKNetworkOperationError(rs=5, userid=userid,
                                                         msg=msg)
        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Disconnect_DM",
            "--operands",
            "-v %s" % vdev))

        try:
            self._request(requestData)
        except (exception.SDKSMUTRequestFailed,
                exception.SDKInternalError) as err:
            results = err.results
            emsg = err.format_message()
            if ((results is not None) and
                (results['rc'] == 212) and
                (results['rs'] == 32)):
                LOG.warning("Virtual device %s is already disconnected "
                            "in the guest's user direct", vdev)
            else:
                LOG.error("Failed to uncouple nic %s in the guest's user "
                          "direct, error: %s" % (vdev, emsg))
                raise

        """Update information in switch table."""
        self._NetDbOperator.switch_update_record_with_switch(userid, vdev,
                                                             None)

        # the inst must be active, or this call will failed
        if active:
            requestData = ' '.join((
                'SMAPI %s' % userid,
                'API Virtual_Network_Adapter_Disconnect',
                "--operands",
                "-v %s" % vdev))
            try:
                self._request(requestData)
            except (exception.SDKSMUTRequestFailed,
                    exception.SDKInternalError) as err:
                results = err.results
                emsg = err.format_message()
                if ((results is not None) and
                    (results['rc'] == 204) and
                    (results['rs'] == 48)):
                    LOG.warning("Virtual device %s is already "
                                "disconnected on the active "
                                "guest system", vdev)
                else:
                    LOG.error("Failed to uncouple nic %s on the active "
                              "guest system, error: %s" % (vdev, emsg))
                    raise

    def uncouple_nic_from_vswitch(self, userid, nic_vdev,
                                  active=False):
        if active:
            msg = ("both in the user direct of guest %s and on "
                   "the active guest system" % userid)
        else:
            msg = "in the user direct of guest %s" % userid
        LOG.debug("Disconnect nic %s with network %s",
                  nic_vdev, msg)
        self._uncouple_nic(userid, nic_vdev, active=active)

    def delete_userid(self, userid):
        rd = ' '.join(('deletevm', userid, 'directory'))
        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            if err.results['rc'] == 400 and err.results['rs'] == 4:
                # guest vm definition not found
                LOG.debug("The guest %s does not exist." % userid)
                return
            else:
                msg = "SMUT error: %s" % err.format_message()
                raise exception.SDKSMUTRequestFailed(err.results, msg)

    def delete_vm(self, userid):
        self.delete_userid(userid)

        # revoke userid from vswitch
        action = "revoke id %s authority from vswitch" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            switch_info = self._NetDbOperator.switch_select_record_for_userid(
                                                                       userid)
            switch_list = set()
            for item in switch_info:
                switch_list.add(item[2])

            for item in switch_list:
                if item is not None:
                    self.revoke_user_from_vswitch(item, userid)

        # cleanup db record from network table
        action = "delete network record for user %s" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._NetDbOperator.switch_delete_record_for_userid(userid)

        # TODO: cleanup db record from volume table
        pass

        # cleanup db record from guest table
        action = "delete guest %s from database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.delete_guest_by_userid(userid)

    def execute_cmd(self, userid, cmdStr):
        """"cmdVM."""
        requestData = 'cmdVM ' + userid + ' CMD \'' + cmdStr + '\''
        with zvmutils.log_and_reraise_smut_request_failed(action='execute '
        'command on vm via iucv channel'):
            results = self._request(requestData)

        ret = results['response']
        return ret

    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import the image specified in url to SDK image repository, and
        create a record in image db, the imported images are located in
        image_repository/prov_method/os_version/, for example,
        /opt/sdk/images/netboot/rhel7.2/90685d2b-167b.img"""
        image_info = []
        try:
            image_info = self._ImageDbOperator.image_query_record(image_name)
        except exception.SDKObjectNotExistError:
            msg = ("The image record %s doens't exist in SDK image datebase,"
                   " will import the image and create record now")
            LOG.info(msg)

        # Ensure the specified image is not exist in image DB
        if image_info:
            msg = ("The image name %s has already exist in SDK image "
                   "database, please check if they are same image or consider"
                   " to use a different image name for import" % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=13, img=image_name)

        try:
            target = '/'.join([CONF.image.sdk_image_repository,
                           const.IMAGE_TYPE['DEPLOY'],
                           image_meta['os_version'],
                           image_name])
            self._pathutils.create_import_image_repository(
                image_meta['os_version'], const.IMAGE_TYPE['DEPLOY'])
            self._scheme2backend(urlparse.urlparse(url).scheme).image_import(
                                                    image_name, url,
                                                    image_meta,
                                                    remote_host=remote_host)
            # Check md5 after import to ensure import a correct image
            # TODO change to use query image name in DB
            expect_md5sum = image_meta.get('md5sum')
            real_md5sum = self._get_md5sum(target)
            if expect_md5sum and expect_md5sum != real_md5sum:
                msg = ("The md5sum after import is not same as source image,"
                       " the image has been broken")
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=4)
            disk_size_units = self._get_disk_size_units(target)
            image_size = self._get_image_size(target)
            self._ImageDbOperator.image_add_record(image_name,
                                         image_meta['os_version'],
                                         real_md5sum,
                                         disk_size_units,
                                         image_size,
                                         const.IMAGE_TYPE['DEPLOY'])
            LOG.info("Image %s is import successfully" % image_name)
        except Exception:
            # Cleanup the image from image repository
            self._pathutils.remove_file(target)
            raise

    def image_export(self, image_name, dest_url, remote_host=None):
        """Export the specific image to remote host or local file system
        :param image_name: image name that can be uniquely identify an image
        :param dest_path: the location to store exported image, eg.
        /opt/images, the image will be stored in folder
         /opt/images/
        :param remote_host: the server that export image to, the format is
         username@IP eg. nova@192.168.99.1, if remote_host is
        None, it means the image will be stored in local server
        :returns a dictionary that contains the exported image info
        {
         'image_name': the image_name that exported
         'image_path': the image_path after exported
         'os_version': the os version of the exported image
         'md5sum': the md5sum of the original image
        }
        """
        image_info = self._ImageDbOperator.image_query_record(image_name)
        if not image_info:
            msg = ("The image %s does not exist in image repository"
                      % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=20, img=image_name)
        source_path = '/'.join([CONF.image.sdk_image_repository,
                               image_info[0][5],
                               image_info[0][1],
                               image_name])

        self._scheme2backend(urlparse.urlparse(dest_url).scheme).image_export(
                                                    source_path, dest_url,
                                                    remote_host=remote_host)

        export_dict = {'image_name': image_name,
                       'image_path': dest_url,
                       'os_version': image_info[0][1],
                       'md5sum': image_info[0][2]}
        LOG.info("Image %s export successfully" % image_name)
        return export_dict

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
            raise exception.SDKImageOperationError(rs=5)

        try:
            root_disk_size = int(output[144:156])
            disk_units = output[220:223]
            root_disk_units = ':'.join([str(root_disk_size), disk_units])
        except ValueError:
            msg = ("Image file at %s is missing built-in disk size "
                   "metadata, it was probably not captured by SDK" %
                   image_path)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=6)

        if 'FBA' not in output and 'CKD' not in output:
            raise exception.SDKImageOperationError(rs=7)

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
            raise exception.SDKImageOperationError(rs=8)
        size = output.split()[0]
        return size

    def _get_image_path_by_name(self, image_name):
        target_info = self._ImageDbOperator.image_query_record(image_name)
        if not target_info:
            msg = ("The image %s does not exist in image repository"
                      % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=20, img=image_name)

        image_path = '/'.join([CONF.image.sdk_image_repository,
                               target_info[0][5],
                               target_info[0][1],
                               image_name])
        return image_path

    def _scheme2backend(self, scheme):
        try:
            return {
                    "file": FilesystemBackend,
                    "http": HTTPBackend,
#                   "https": HTTPSBackend
            }[scheme]
        except KeyError:
            msg = ("No backend found for '%s'" % scheme)
            LOG.err(msg)
            raise exception.SDKImageOperationError(rs=2, schema=scheme)

    def _get_md5sum(self, fpath):
        """Calculate the md5sum of the specific image file"""
        try:
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
        except Exception:
            msg = ("Failed to calculate the image's md5sum")
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=3)

    def _read_chunks(self, fh):
        fh.seek(0)
        chunk = fh.read(CHUNKSIZE)
        while chunk:
            yield chunk
            chunk = fh.read(CHUNKSIZE)
        else:
            fh.seek(0)

    def image_delete(self, image_name):
        # Delete image file
        self._delete_image_file(image_name)
        # Delete image record from db
        self._ImageDbOperator.image_delete_record(image_name)

    def _delete_image_file(self, image_name):
        image_path = self._get_image_path_by_name(image_name)
        self._pathutils.remove_file(image_path)

    def image_query(self, imagename=None):
        return self._ImageDbOperator.image_query_record(imagename)

    def image_get_root_disk_size(self, image_name):
        """Return the root disk units of the specified image
        image_name: the unique image name in db
        Return the disk units in format like 3339:CYL or 467200:BLK
        """
        image_info = self.image_query(image_name)
        if not image_info:
            raise exception.SDKImageOperationError(rs=20, img=image_name)
        disk_size_units = image_info[0][3].split(':')[0]
        return disk_size_units

    def punch_file(self, userid, fn, fclass):
        rd = ("changevm %(uid)s punchfile %(file)s --class %(class)s" %
                      {'uid': userid, 'file': fn, 'class': fclass})
        try:
            self._request(rd)
        except exception.SDKSMUTRequestFailed as err:
            LOG.error("Failed to punch file to userid '%s',"
                      "error: %s" % (userid, err.format_message()))
            raise
        finally:
            os.remove(fn)

    def get_guest_connection_status(self, userid):
        '''Get guest vm connection status.'''
        rd = ' '.join(('getvm', userid, 'isreachable'))
        results = self._request(rd)
        if results['rs'] == 1:
            return True
        else:
            return False

    def _generate_disk_parmline(self, vdev, fmt, mntdir):
        parms = [
                'action=' + 'addMdisk',
                'vaddr=' + vdev,
                'filesys=' + fmt,
                'mntdir=' + mntdir
                ]
        parmline = ' '.join(parms)
        parmstr = "'" + parmline + "'"
        return parmstr

    def process_additional_minidisks(self, userid, disk_info):
        '''Generate and punch the scripts used to process additional disk into
        target vm's reader.
        '''
        for idx, disk in enumerate(disk_info):
            vdev = disk.get('vdev') or self.generate_disk_vdev(
                                                    offset = (idx + 1))
            fmt = disk.get('format')
            mount_dir = disk.get('mntdir') or ''.join(['/mnt/', str(vdev)])
            disk_parms = self._generate_disk_parmline(vdev, fmt, mount_dir)
            func_name = '/var/lib/zvmsdk/setupDisk'
            self.aemod_handler(userid, func_name, disk_parms)

    def aemod_handler(self, instance_name, func_name, parms):
        rd = ' '.join(['changevm', instance_name, 'aemod', func_name,
                       '--invparms', parms])
        action = parms[0] + instance_name
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

    def get_user_console_output(self, userid):
        # get console into reader
        rd = 'getvm %s consoleoutput' % userid
        action = 'get console log reader file list for guest vm: %s' % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            resp = self._request(rd)

        with zvmutils.expect_invalid_resp_data(resp):
            rf_list = resp['response'][0].rpartition(':')[2].strip().split()

        # TODO: make sure reader device is online
        # via 'cat /sys/bus/ccw/drivers/vmur/0.0.000c/online'
        #     'sudo /sbin/cio_ignore -r 000c; sudo /sbin/chccwdev -e 000c'
        #     'which udevadm &> /dev/null && udevadm settle || udevsettle'

        logs = []
        for rf in rf_list:
            cmd = '/usr/sbin/vmur re -t -O %s' % rf
            rc, output = zvmutils.execute(cmd)
            if rc == 0:
                logs.append(output)

        return ''.join(logs)

    def query_vswitch(self, switch_name):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query_Extended" %
            smut_userid,
            "--operands",
            '-k switch_name=%s' % switch_name
            ))
        action = "query vswitch details info"
        with zvmutils.log_and_reraise_smut_request_failed(action):
            results = self._request(rd)
            rd_list = results['response']

        vsw_info = {}
        with zvmutils.expect_invalid_resp_data():
            # ignore user_vlan_id part and jump to the vswitch basic info
            idx_end = len(rd_list)
            idx = 0
            while((idx < idx_end) and
                  not rd_list[idx].__contains__('switch_name')):
                idx = idx + 1

            # The next 21 lines contains the vswitch basic info
            # eg, name, type, port_type, vlan_awareness, etc
            for i in range(21):
                rd = rd_list[idx + i].split(':')
                vsw_info[rd[0].strip()] = rd[1].strip()
            idx = idx + 21
            # Skip the vepa_status
            while((idx < idx_end) and
                  not rd_list[idx].__contains__('real_device_address') and
                  not rd_list[idx].__contains__('port_num') and
                  not rd_list[idx].__contains__('adapter_owner')):
                idx = idx + 1

            def _parse_value(data_list, idx, keyword, offset=1):
                value = data_list[idx].rpartition(keyword)[2].strip()
                if value == '(NONE)':
                    value = 'NONE'
                return idx + offset, value

            # Start to analyse the real devices info
            vsw_info['real_devices'] = {}
            while((idx < idx_end) and
                  rd_list[idx].__contains__('real_device_address')):
                # each rdev has 6 lines' info
                idx, rdev_addr = _parse_value(rd_list, idx,
                                              'real_device_address: ')
                idx, vdev_addr = _parse_value(rd_list, idx,
                                              'virtual_device_address: ')
                idx, controller = _parse_value(rd_list, idx,
                                              'controller_name: ')
                idx, port_name = _parse_value(rd_list, idx, 'port_name: ')
                idx, dev_status = _parse_value(rd_list, idx,
                                                  'device_status: ')
                idx, dev_err = _parse_value(rd_list, idx,
                                            'device_error_status ')
                vsw_info['real_devices'][rdev_addr] = {'vdev': vdev_addr,
                                                'controller': controller,
                                                'port_name': port_name,
                                                'dev_status': dev_status,
                                                'dev_err': dev_err
                                                }
                # Under some case there would be an error line in the output
                # "Error controller_name is NULL!!", skip this line
                if ((idx < idx_end) and
                    rd_list[idx].__contains__(
                        'Error controller_name is NULL!!')):
                    idx += 1

            # Start to get the authorized userids
            vsw_info['authorized_users'] = {}
            while((idx < idx_end) and rd_list[idx].__contains__('port_num')):
                # each authorized userid has 6 lines' info at least
                idx, port_num = _parse_value(rd_list, idx,
                                              'port_num: ')
                idx, userid = _parse_value(rd_list, idx,
                                              'grant_userid: ')
                idx, prom_mode = _parse_value(rd_list, idx,
                                              'promiscuous_mode: ')
                idx, osd_sim = _parse_value(rd_list, idx, 'osd_sim: ')
                idx, vlan_count = _parse_value(rd_list, idx,
                                                  'vlan_count: ')
                vlan_ids = []
                for i in range(int(vlan_count)):
                    idx, id = _parse_value(rd_list, idx,
                                                  'user_vlan_id: ')
                    vlan_ids.append(id)
                # For vlan unaware vswitch, the query smcli would
                # return vlan_count as 1, here we just set the count to 0
                if (vsw_info['vlan_awareness'] == 'UNAWARE'):
                    vlan_count = 0
                    vlan_ids = []
                vsw_info['authorized_users'][userid] = {
                    'port_num': port_num,
                    'prom_mode': prom_mode,
                    'osd_sim': osd_sim,
                    'vlan_count': vlan_count,
                    'vlan_ids': vlan_ids
                    }

            # Start to get the connected adapters info
            # OWNER_VDEV would be used as the dict key for each adapter
            vsw_info['adapters'] = {}
            while((idx < idx_end) and
                  rd_list[idx].__contains__('adapter_owner')):
                # each adapter has four line info: owner, vdev, macaddr, type
                idx, owner = _parse_value(rd_list, idx,
                                              'adapter_owner: ')
                idx, vdev = _parse_value(rd_list, idx,
                                              'adapter_vdev: ')
                idx, mac = _parse_value(rd_list, idx,
                                              'adapter_macaddr: ')
                idx, type = _parse_value(rd_list, idx, 'adapter_type: ')
                key = owner + '_' + vdev
                vsw_info['adapters'][key] = {
                    'mac': mac,
                    'type': type
                    }
            # Todo: analyze and add the uplink NIC info and global member info

        return vsw_info

    def get_nic_info(self, userid=None, nic_id=None, vswitch=None):
        nic_info = self._NetDbOperator.switch_select_record(userid=userid,
                                            nic_id=nic_id, vswitch=vswitch)
        return nic_info

    def is_first_network_config(self, userid):
        action = "get guest '%s' to database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            info = self._GuestDbOperator.get_guest_by_userid(userid)
            # check net_set
            if int(info[3]) == 0:
                return True
            else:
                return False

    def update_guestdb_with_net_set(self, userid):
        action = "update guest '%s' in database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.update_guest_by_userid(userid, net_set='1')


class FilesystemBackend(object):
    @classmethod
    def image_import(cls, image_name, url, image_meta, **kwargs):
        """Import image from remote host to local image repository using scp.
        If remote_host not specified, it means the source file exist in local
        file system, just copy the image to image repository
        """

        source = urlparse.urlparse(url).path
        target = '/'.join([CONF.image.sdk_image_repository,
                          const.IMAGE_TYPE['DEPLOY'],
                          image_meta['os_version'],
                          image_name])
        if kwargs['remote_host']:
            if '@' in kwargs['remote_host']:
                source_path = ':'.join([kwargs['remote_host'], source])
                command = ' '.join(['/usr/bin/scp -r ', source_path,
                                    target])
                (rc, output) = commands.getstatusoutput(command)
                if rc:
                    msg = ("Copying image file from remote filesystem failed"
                           " with reason: %s" % output)
                    LOG.error(msg)
                    raise exception.SDKImageOperationError(rs=10, err=output)
            else:
                msg = ("The specified remote_host %s format invalid" %
                        kwargs['remote_host'])
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=11,
                                                    rh=kwargs['remote_host'])
        else:
            LOG.debug("Remote_host not specified, will copy from local")
            try:
                shutil.copyfile(source, target)
            except Exception as err:
                msg = ("Import image from local file system failed"
                       " with reason %s" % six.text_type(err))
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=12,
                                                    err=six.text_type(err))

    @classmethod
    def image_export(cls, source_path, dest_url, **kwargs):
        """Export the specific image to remote host or local file system """
        dest_path = urlparse.urlparse(dest_url).path
        if kwargs['remote_host']:
            target_path = ':'.join([kwargs['remote_host'], dest_path])
            command = ' '.join(['/usr/bin/scp -r ', source_path, target_path])
            (rc, output) = commands.getstatusoutput(command)
            if rc:
                msg = ("Error happened when copying image file to remote "
                       "host with reason: %s" % output)
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=21, msg=output)
        else:
            # Copy to local file system
            LOG.debug("Remote_host not specified, will copy to local server")
            try:
                shutil.copyfile(source_path, dest_path)
            except Exception as err:
                msg = ("Export image from %(src)s to local file system"
                       " %(dest)s failed: %(err)s" %
                       {'src': source_path,
                        'dest': dest_path,
                        'err': six.text_type(err)})
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=22,
                                                       err=six.text_type(err))


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

    def handle_download_errors(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as err:
                self.fd.close()
                msg = ("Download image from http server failed: %s" %
                       six.text_type(err))
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=9,
                                                    err=six.text_type(err))
        return wrapper

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

    @handle_download_errors
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
        LOG.info('Download %s success' % (self.name))
        self.fd.close()
