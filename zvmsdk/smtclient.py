#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2024 IBM Corp.
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

import functools
import hashlib
import math
# On SLES12, we found that if you import urllib.parse later
# than requests, you will find a error like 'not able to load
# urllib.parse, this is because urllib will be in sys.modules
# when first import requests
# as workaround here, we first import urllib then import requests
# later, we need consider to use urllib.request to replace
# requests if that's possible to avoid this kind of issue
from io import IOBase
import shutil
import six.moves.urllib.parse as urlparse
import requests
import threading
import os
import re
import six
import string
import subprocess
import tempfile
import time

from smtLayer import smt

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

DIRMAINT_ERROR_MESSAGE = ("https://www-40.ibm.com/servers/resourcelink/"
    "svc0302a.nsf/pages/zVMV7R2gc246282?OpenDocument")
CP_ERROR_MESSAGE = ("https://www-40.ibm.com/servers/resourcelink/"
    "svc0302a.nsf/pages/zVMV7R2gc246270?OpenDocument")


_SMT_CLIENT = None


def get_smtclient():
    global _SMT_CLIENT
    if _SMT_CLIENT is None:
        try:
            _SMT_CLIENT = zvmutils.import_object(
                'zvmsdk.smtclient.SMTClient')
        except ImportError:
            LOG.error("Unable to get smtclient")
            raise ImportError
    return _SMT_CLIENT


class SMTClient(object):

    def __init__(self):
        self._smt = smt.SMT()
        self._pathutils = zvmutils.PathUtils()
        self._NetDbOperator = database.NetworkDbOperator()
        self._GuestDbOperator = database.GuestDbOperator()
        self._ImageDbOperator = database.ImageDbOperator()

    def _request(self, requestData):
        try:
            results = self._smt.request(requestData)
        except Exception as err:
            LOG.error('SMT internal parse encounter error')
            raise exception.SDKInternalError(msg=err, modID='smt')

        def _is_smt_internal_error(results):
            internal_error_list = returncode.SMT_INTERNAL_ERROR
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
            # Check whether this smt error belongs to internal error, if so,
            # raise internal error, otherwise raise clientrequestfailed error
            if _is_smt_internal_error(results):
                msg = "SMT internal error. Results: %s." % str(results)

                rc = results.get('rc', 0)
                if rc in [-110, -102, -103, -108]:
                    if rc == -108:
                        msg += ("This is likely to be caused by too short timeout "
                                "specified for z/VM SMAPI. Update SMAPI timeout "
                                "configuration in zvmsdk.conf. Contact with your z/VM "
                                "administrators for further help")
                    else:
                        msg += ("This is likely to be caused by temporary z/VM "
                                "SMAPI down issue, Contact with your z/VM "
                                "administrators for further help")

                raise exception.SDKInternalError(msg=msg,
                                                    modID='smt',
                                                    results=results)
            else:
                # no solution if we don't know, so empty string
                solution = ''
                rc = results.get('rc', 0)

                if rc == 396:
                    solution = (("CP command failed, with error code %s."
                                "Check <%s> on z/VM CP error messages")
                                % (results['rs'], CP_ERROR_MESSAGE))
                if rc == 596:
                    solution = (("DIRMAINT command failed, with error code %s."
                                "Check <%s> on z/VM DIRMAINT error messages")
                                % (results['rs'], DIRMAINT_ERROR_MESSAGE))

                msg = (("SMT request failed. RequestData: '%s', Results: '%s'."
                        "%s") % (requestData, str(results), solution))
                raise exception.SDKSMTRequestFailed(results, msg)
        return results

    def get_guest_temp_path(self, userid):
        return self._pathutils.get_guest_temp_path(userid)

    def get_guest_path(self, userid):
        return self._pathutils.get_guest_path(userid)

    def clean_temp_folder(self, tmp_folder):
        return self._pathutils.clean_temp_folder(tmp_folder)

    def _generate_vdev(self, base, offset):
        """Generate virtual device number based on base vdev
        :param base: base virtual device number, string of 4 bit hex.
        :param offset: offset to base, integer.
        """
        vdev = hex(int(base, 16) + offset)[2:]
        return vdev.rjust(4, '0')

    def _generate_increasing_nic_id(self, nic_id):
        """Generate increasing nic id string
        :param nic_id: hexadecimal nic id like '1000'
        :return: increasing nic id, string like '0.0.1000,0.0.1001,0.0.1002'
        """
        nic_id = str(hex(int(nic_id, 16)))[2:]
        nic_id_1 = str(hex(int(nic_id, 16) + 1))[2:]
        nic_id_2 = str(hex(int(nic_id, 16) + 2))[2:]
        if len(nic_id_2) > 4:
            errmsg = ("Virtual device number %s is not valid" % nic_id_2)
            raise exception.SDKInvalidInputFormat(msg=errmsg)
        return "0.0.%s,0.0.%s,0.0.%s" % (nic_id, nic_id_1, nic_id_2)

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
                       'disk_pool': 'ECKD:eckdpool1'},
                       {'size': '1g',
                       'format': 'ext3'}]

        """

        # Firstly, check disk_pool in disk_list, if disk_pool not specified
        # and not configured(the default vaule is None), report error
        # report error
        for idx, disk in enumerate(disk_list):
            disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
            disk['disk_pool'] = disk_pool
            if disk_pool is None:
                msg = ('disk_pool not configured for sdkserver.')
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=2, msg=msg)

        for idx, disk in enumerate(disk_list):
            if 'vdev' in disk:
                # this means user want to create their own device number
                vdev = disk['vdev']
            else:
                vdev = self.generate_disk_vdev(start_vdev=start_vdev,
                                               offset=idx)
            self._add_mdisk(userid, disk, vdev)
            disk['vdev'] = vdev

            sizeUpper = disk.get('size').strip().upper()
            sizeUnit = sizeUpper[-1]
            if sizeUnit != 'G' and sizeUnit != 'M':
                sizeValue = sizeUpper
                disk_pool = disk.get('disk_pool')
                [diskpool_type, diskpool_name] = disk_pool.split(':')
                if (diskpool_type.upper() == 'ECKD'):
                    # Convert the cylinders to bytes
                    convert = 737280
                else:
                    # Convert the blocks to bytes
                    convert = 512
                byteSize = float(float(int(sizeValue) * convert / 1024) / 1024)
                unit = "M"
                if (byteSize > 1024):
                    byteSize = float(byteSize / 1024)
                    unit = "G"
                byteSize = "%.1f" % byteSize
                disk['size'] = byteSize + unit

        return disk_list

    def remove_mdisks(self, userid, vdev_list):
        for vdev in vdev_list:
            self._remove_mdisk(userid, vdev)

    def dedicate_device(self, userid, vaddr, raddr, mode):
        """dedicate device

        :userid: The name of the image obtaining a dedicated device
        :vaddr: The virtual device number of the device
        :raddr: A real device number to be dedicated or attached
                to the specified image
        :mode: Specify a 1 if the virtual device is to be in read-only mode.
               Otherwise, specify a 0.
        """
        # dedicate device to directory entry
        self._dedicate_device(userid, vaddr, raddr, mode)

    def _dedicate_device(self, userid, vaddr, raddr, mode):
        """dedicate device."""
        action = 'dedicate'
        rd = ('changevm %(uid)s %(act)s %(va)s %(ra)s %(mod)i' %
              {'uid': userid, 'act': action,
               'va': vaddr, 'ra': raddr, 'mod': mode})
        action = "dedicate device to userid '%s'" % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            self._request(rd)

    def get_fcp_info_by_status(self, userid, status=None):

        """get fcp information by the status.

        :userid: (str) The name of the image to query fcp info
        :status: (str) If status is None, will return the FCP devices
            of all statuses. If status specified, will only return the
            FCP devices of this status.
            The status must be 'active', 'free' or 'offline'.
        :returns: (list) a list of string lines that the command output.
        """
        action = 'fcpinfo'
        if status is None:
            # if status is None, will transfer status to all
            # to let smtLayer return the FCPs of all the statuses
            status = "all"
        # always set -k OWNER=YES
        rd = ' '.join(['getvm', userid, action, status, "YES"])
        action = "query fcp info of '%s'" % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(rd)

        return results['response']

    def undedicate_device(self, userid, vaddr):
        """undedicate device

        :userid: The name of the image obtaining a dedicated device
        :vaddr: The virtual device number of the device
        """
        # undedicate device to directory entry
        self._undedicate_device(userid, vaddr)

    def _undedicate_device(self, userid, vaddr):
        """undedicate device."""
        action = 'undedicate'
        rd = ('changevm %(uid)s %(act)s %(va)s' %
              {'uid': userid, 'act': action,
               'va': vaddr})
        action = "undedicate device from userid '%s'" % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            self._request(rd)

    def get_image_performance_info(self, userid):
        """Get CPU and memory usage information.

        :userid: the zvm userid to be queried
        """
        pi_dict = self.image_performance_query([userid])
        return pi_dict.get(userid, None)

    def get_adapters_info(self, userid):
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Adapter_Query_Extended" % userid,
            "--operands",
            "-k 'image_device_number=*'"))
        results = None
        action = "get network info of userid '%s'" % str(userid)
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(rd)
        ret = results['response']
        # TODO: muti NIC support?
        nic_count = 0
        for line in ret:
            if 'adapter_count=' in line:
                nic_count = int(line.strip().split('=')[-1])
                break

        if nic_count < 1:
            msg = 'get_network_info:No NIC found on userid %s' % userid
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)
        # save network info into dict by index from 1 to nic_count
        # Firstly, get adapter information
        adapters_info = []
        adapter = dict()
        # if found IP, no need to continue
        found_mac = False
        for line in ret:
            if 'adapter_address=' in line:
                adapter_addr = line.strip().split('=')[-1]
                adapter['adapter_address'] = adapter_addr
            if 'adapter_status=' in line:
                adapter_type = line.strip().split('=')[-1]
                adapter['adapter_status'] = adapter_type
            if 'lan_owner=' in line:
                lan_owner = line.strip().split('=')[-1]
                adapter['lan_owner'] = lan_owner
            if 'lan_name=' in line:
                lan_name = line.strip().split('=')[-1]
                adapter['lan_name'] = lan_name
            if 'mac_address=' in line:
                if not found_mac:
                    mac_addr = line.strip().split('=')[-1]
                    pattern = re.compile('.{2}')
                    mac_address = ':'.join(pattern.findall(mac_addr))
                    adapter['mac_address'] = mac_address
            if 'mac_ip_version=' in line:
                if not found_mac:
                    ip_version = line.strip().split('=')[-1]
                    adapter['mac_ip_version'] = ip_version
            if 'mac_ip_address=' in line:
                # once we found mac_ip_address, assume this is the MAC
                # we are using, then jump to next adapter
                if not found_mac:
                    mac_ip = line.strip().split('=')[-1]
                    adapter['mac_ip_address'] = mac_ip
                    found_mac = True
            if 'adapter_info_end' in line:
                adapters_info.append(adapter)
                # clear adapter and process next
                adapter = dict()
                found_mac = False
        return adapters_info

    def get_disks_info(self, userid):
        rd = ' '.join((
            "SMAPI %s API Image_Disk_Query" % userid,
            "--operands",
            "-k 'vdasd_id=all'"))
        results = None
        action = "get disk info of all disks"
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(rd)
            ret = results['response']
            disks_info = []
            disk = dict()
            for line in ret:
                if line != "":
                    key = line.split(':')[0].strip()
                    value = line.split(':')[-1].strip()
                    if key == 'DASD VDEV':
                        disk['vdev'] = value
                    elif key == 'RDEV':
                        disk['rdev'] = value
                    elif key == 'Access type':
                        disk['access_type'] = value
                    elif key == 'Device type':
                        disk['device_type'] = value
                    elif key == 'Device size':
                        disk['device_size'] = int(value)
                    elif key == 'Device units':
                        disk['device_units'] = value
                    elif key == 'Device volume label':
                        disk['volume_label'] = value
                else:
                    disks_info.append(disk)
                    disk = dict()
        return disks_info

    def _parse_vswitch_inspect_data(self, rd_list):
        """ Parse the Virtual_Network_Vswitch_Query_Byte_Stats data to get
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
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(requestData)
        with zvmutils.expect_invalid_resp_data(results):
            status = results['response'][0].partition(': ')[2]
        return status

    def _check_power_state(self, userid, action):
        # Get the vm status
        power_state = self.get_power_state(userid)

        # Power on the vm if it is inactive
        if power_state == 'off':
            msg = ('The vm %s is powered off, please start up it '
                   'before %s' % (userid, action))
            raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                   msg=msg)

    def guest_start(self, userid):
        """Power on VM."""
        requestData = "PowerVM " + userid + " on"
        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_stop(self, userid, **kwargs):
        """Power off VM."""
        requestData = "PowerVM " + userid + " off"

        if 'timeout' in kwargs.keys() and kwargs['timeout']:
            requestData += ' --maxwait ' + str(kwargs['timeout'])
        if 'poll_interval' in kwargs.keys() and kwargs['poll_interval']:
            requestData += ' --poll ' + str(kwargs['poll_interval'])

        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_softstop(self, userid, **kwargs):
        """Power off VM gracefully, it will call shutdown os then
            deactivate vm"""
        requestData = "PowerVM " + userid + " softoff --wait"
        if 'timeout' in kwargs.keys() and kwargs['timeout']:
            requestData += ' --maxwait ' + str(kwargs['timeout'])
        else:
            requestData += ' --maxwait ' + str(CONF.guest.softstop_timeout)

        if 'poll_interval' in kwargs.keys() and kwargs['poll_interval']:
            requestData += ' --poll ' + str(kwargs['poll_interval'])
        else:
            requestData += ' --poll ' + str(CONF.guest.softstop_interval)

        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_pause(self, userid):
        self._check_power_state(userid, 'pause')

        requestData = "PowerVM " + userid + " pause"
        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_unpause(self, userid):
        self._check_power_state(userid, 'unpause')

        requestData = "PowerVM " + userid + " unpause"
        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_reboot(self, userid):
        requestData = ' '.join(("PowerVM", userid, "reboot"))
        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def guest_reset(self, userid):
        requestData = ' '.join(("PowerVM", userid, "reset"))
        with zvmutils.log_and_reraise_smt_request_failed():
            self._request(requestData)

    def live_migrate_move(self, userid, destination, parms):
        """ moves the specified virtual machine, while it continues to run,
         to the specified system within the SSI cluster. """
        rd = ('migratevm %(uid)s move --destination %(dest)s ' %
              {'uid': userid, 'dest': destination})

        if 'maxtotal' in parms:
            rd += ('--maxtotal ' + str(parms['maxtotal']))
        if 'maxquiesce' in parms:
            rd += (' --maxquiesce ' + str(parms['maxquiesce']))
        if 'immediate' in parms:
            rd += " --immediate"
        if 'forcearch' in parms:
            rd += " --forcearch"
        if 'forcedomain' in parms:
            rd += " --forcedomain"
        if 'forcestorage' in parms:
            rd += " --forcestorage"

        action = "move userid '%s' to SSI '%s'" % (userid, destination)

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            msg = ''
            if action is not None:
                msg = "Failed to %s. " % action
            msg += "SMT error: %s" % err.format_message()
            LOG.error(msg)
            raise exception.SDKSMTRequestFailed(err.results, msg)

    def live_migrate_test(self, userid, destination):
        """ tests the specified virtual machine and reports whether or not
        it is eligible to be relocated to the specified system. """
        rd = ('migratevm %(uid)s test --destination %(dest)s ' %
              {'uid': userid, 'dest': destination})

        action = "test to move userid '%s' to SSI '%s'" % (userid, destination)

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            msg = ''
            if action is not None:
                msg = "Failed to %s. " % action
            msg += "SMT error: %s" % err.format_message()
            LOG.error(msg)
            raise exception.SDKSMTRequestFailed(err.results, msg)

    def _set_vdisk(self, disk, rd, offset):
        """Check and set vdev for vdisk"""
        vd = disk.get('vdev') or self.generate_disk_vdev(offset=offset)
        disk['vdev'] = vd
        sizeUpper = disk['size'].strip().upper()
        sizeUnit = sizeUpper[-1]
        # vdisk size is not allowed to be more than 2G
        if sizeUnit != 'M' and sizeUnit != 'G':
            errmsg = ("%s must has 'M' or 'G' suffix" % sizeUpper)
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        if sizeUnit == 'M':
            size = int(sizeUpper[:-1])
            if size > 2048:
                errmsg = ("%s is great than 2048M" % sizeUpper)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        if sizeUnit == 'G':
            size = int(sizeUpper[:-1])
            if size > 2:
                errmsg = ("%s is great than 2G" % sizeUpper)
                raise exception.SDKInvalidInputFormat(msg=errmsg)
        rd += ' --vdisk %s:%s' % (vd, sizeUpper)
        return disk, rd

    def _get_ipl_param(self, ipl_from):
        if len(ipl_from) > 0:
            ipl_param = ipl_from
        else:
            ipl_param = CONF.zvm.user_root_vdev

        return ipl_param

    def create_vm(self, userid, cpu, memory, disk_list, profile,
                  max_cpu, max_mem, ipl_from, ipl_param, ipl_loadparam,
                  dedicate_vdevs, loaddev, account, comment_list,
                  cschedule='', cshare='', rdomain='', pcif=''):
        """ Create VM and add disks if specified. """
        if memory % 1024 == 0:
            mem = str(int(memory / 1024)) + 'G'
        else:
            mem = str(memory) + 'M'

        rd = ('makevm %(uid)s directory LBYONLY %(mem)s %(pri)s '
              '--cpus %(cpu)i --profile %(prof)s --maxCPU %(max_cpu)i '
              '--maxMemSize %(max_mem)s --setIniStandbyRem' %
              {'uid': userid, 'mem': mem,
               'pri': const.ZVM_USER_DEFAULT_PRIVILEGE,
               'cpu': cpu, 'prof': profile,
               'max_cpu': max_cpu, 'max_mem': max_mem})

        if CONF.zvm.default_admin_userid:
            ids = CONF.zvm.default_admin_userid.split(' ')
            id_str = ':'.join(ids)

            rd += (' --logonby %s' % id_str)

        # when use dasd as root disk, the disk_list[0] would be the boot
        # disk.
        # when boot from volume, ipl_from should be specified explicitly.
        if (disk_list and 'is_boot_disk' in disk_list[0] and
                disk_list[0]['is_boot_disk']) or ipl_from:
            # we assume at least one disk exist, which means, is_boot_disk
            # is true for exactly one disk.
            rd += (' --ipl %s' % self._get_ipl_param(ipl_from))

            # load param for ipl
            if ipl_param:
                rd += ' --iplParam %s' % ipl_param

            if ipl_loadparam:
                rd += ' --iplLoadparam %s' % ipl_loadparam

        if dedicate_vdevs:
            rd += ' --dedicate "%s"' % " ".join(dedicate_vdevs)

        if account:
            rd += ' --account "%s"' % account

        if cschedule:
            rd += ' --commandSchedule %s' % cschedule

        # if share given, then user it
        # or if CONF.zvm.user_default_share_unit is not 0
        # set relative share to CONF.zvm.user_default_share_unit*cpu
        if cshare:
            rd += ' --commandSetShare "%s"' % cshare
        else:
            # only add SHARE statement if unit > 0
            if CONF.zvm.user_default_share_unit > 0:
                total = CONF.zvm.user_default_share_unit * cpu
                data = 'RELATIVE %d' % total
                rd += ' --commandSetShare "%s"' % data

        if rdomain:
            rd += ' --commandRDomain %s' % rdomain

        if pcif:
            v = pcif.split(':')
            if len(v) != 2:
                errmsg = ("pcif input %s is invalid, must be format like"
                          " <dev>:<dev>" % pcif)
                raise exception.SDKInvalidInputFormat(msg=errmsg)
            rd += ' --commandPcif %s' % pcif

        comments = ''
        if comment_list is not None:
            for comment in comment_list:
                comments += comment
                # This s a dummy spliter and will be used for split
                # the comment, for example, input comment is
                # comment1,comment2, it will be constructed into
                # comment1$@$@$comment2 and send to smtLayer to handle
                comments += '$@$@$'

        if comments:
            rd += ' --comment "%s"' % comments

        if loaddev:
            if 'portname' in loaddev:
                rd += ' --loadportname %s' % loaddev['portname']
            if 'lun' in loaddev:
                rd += ' --loadlun %s' % loaddev['lun']
            if 'alterdev' in loaddev:
                rd += ' --alterdev %s' % loaddev['alterdev']

        # now, we need consider swap only case, customer using boot
        # from volume but no disk pool provided, we allow to create
        # swap disk from vdisk by default, when we come to this logic
        # we are very sure that if no disk pool, there is only one
        # disk in disk_list and that's swap
        vdisk = None

        # If not swap only case and customer uses vdisk to create
        # swap disk, we need handle the swap disk and non-swap disk
        # seperately
        swap_device = []

        # this is swap only case, which means, you only create a swap
        # disk (len disk_list is 1) and no other disks
        if len(disk_list) == 1:
            disk = disk_list[0]
            if 'format' in disk and disk['format'].lower() == 'swap':
                disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
                if disk_pool is None or not CONF.zvm.swap_default_with_mdisk:
                    # If it's swap only case, or disk_pool is not None and the
                    # user wants to create swap device with vdisk,
                    # we create user direct directly
                    disk, rd = self._set_vdisk(disk, rd, 0)
                    vdisk = disk
        elif len(disk_list) > 1:
            if not CONF.zvm.swap_default_with_mdisk:
                # We create swap device with vdisk
                for i in range(len(disk_list)):
                    disk = disk_list[i]
                    if 'format' in disk and disk['format'].lower() == 'swap':
                        # if it's vdisk, then create user direct directly
                        disk, rd = self._set_vdisk(disk, rd, len(disk_list) - 1)
                        # Remove the vdisk from disk_list, then in the following
                        # we will only add these remaining disks for the userid
                        disk_list.pop(i)
                        swap_device.append(disk)

        action = "create userid '%s'" % userid

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            if ((err.results['rc'] == 436) and (err.results['rs'] == 4)):
                result = "Profile '%s'" % profile
                raise exception.SDKObjectNotExistError(obj_desc=result,
                                                       modID='guest')
            elif ((err.results['rc'] == 596) and (err.results['rs'] == 3658)):
                # internal issue 9939
                # That is because a previous definition of CIC may have
                # caused it to be defined. I would log it somewhere.
                LOG.warning("ignoring 596/3658 as it might be defined already")
            else:
                msg = ''
                if action is not None:
                    msg = "Failed to %s. " % action
                msg += "SMT error: %s" % err.format_message()
                LOG.error(msg)
                raise exception.SDKSMTRequestFailed(err.results, msg)

        # Add the guest to db immediately after user created
        action = "add guest '%s' to database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.add_guest(userid)

        # Continue to add disk, if vdisk is None, it means
        # it's not only one vdisk device and we need add disks.
        # And we must return all the disks to make guest config handle
        # other remaining jobs
        if vdisk is None and disk_list:
            # not perform mkfs against root disk
            if disk_list[0].get('is_boot_disk'):
                disk_list[0].update({'format': 'none'})
            return self.add_mdisks(userid, disk_list) + swap_device

        # For the swap only case, we must return swap disk in order to make guest config
        # handle other remaining jobs
        return disk_list

    def _add_mdisk(self, userid, disk, vdev):
        """Create one disk for userid

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """
        size = disk['size']
        fmt = disk.get('format', 'ext4')
        disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
        # Check disk_pool, if it's None, report error
        if disk_pool is None:
            msg = ('disk_pool not configured for sdkserver.')
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=2, msg=msg)
        [diskpool_type, diskpool_name] = disk_pool.split(':')

        if (diskpool_type.upper() == 'ECKD'):
            action = 'add3390'
        else:
            action = 'add9336'

        rd = ' '.join(['changevm', userid, action, diskpool_name,
                       vdev, size, '--mode MR'])
        if fmt and fmt != 'none':
            rd += (' --filesystem %s' % fmt.lower())

        action = "add mdisk to userid '%s'" % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            self._request(rd)

    def get_vm_list(self):
        """Get the list of guests that are created by SDK
        return userid list"""
        action = "list all guests in database"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            guests_in_db = self._GuestDbOperator.get_guest_list()
            guests_migrated = \
                    self._GuestDbOperator.get_migrated_guest_info_list()

        # db query return value in tuple (uuid, userid, metadata, comments)
        userids_in_db = [g[1].upper() for g in guests_in_db]
        userids_migrated = [g[1].upper() for g in guests_migrated]
        userid_list = list(set(userids_in_db) - set(userids_migrated))

        return userid_list

    def _remove_mdisk(self, userid, vdev):
        rd = ' '.join(('changevm', userid, 'removedisk', vdev))
        action = "remove disk with vdev '%s' from userid '%s'" % (vdev, userid)
        with zvmutils.log_and_reraise_smt_request_failed(action):
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
        client = client or zvmutils.get_smt_userid()

        iucv_path = "/tmp/" + userid
        if not os.path.exists(iucv_path):
            os.makedirs(iucv_path)
        iucv_auth_file = iucv_path + "/iucvauth.sh"
        zvmutils.generate_iucv_authfile(iucv_auth_file, client)

        try:
            requestData = "ChangeVM " + userid + " punchfile " + \
                iucv_auth_file + " --class x"
            self._request(requestData)
        except exception.SDKSMTRequestFailed as err:
            msg = ("Failed to punch IUCV auth file to userid '%s'. SMT error:"
                   " %s" % (userid, err.format_message()))
            LOG.error(msg)
            raise exception.SDKSMTRequestFailed(err.results, msg)
        finally:
            self._pathutils.clean_temp_folder(iucv_path)

    def volume_refresh_bootmap(self, fcpchannels, wwpns, lun, wwid='',
                               transportfiles=None, guest_networks=None, min_fcp_paths_count=0):
        guest_networks = guest_networks or []
        fcps = ','.join(fcpchannels)
        ws = ','.join(wwpns)
        fcs = "--fcpchannel=%s" % fcps
        wwpns = "--wwpn=%s" % ws
        lun = "--lun=%s" % lun
        wwid = "--wwid=%s" % wwid
        paths = "--minfcp=%s" % min_fcp_paths_count
        cmd = ['sudo', '/opt/zthin/bin/refresh_bootmap', fcs, wwpns,
               lun, wwid, paths]

        if guest_networks:
            # prepare additional parameters for RHCOS BFV
            if not transportfiles:
                err_msg = 'Ignition file is required when deploying RHCOS'
                LOG.error(err_msg)
                raise exception.SDKVolumeOperationError(rs=10)

            # get NIC ID
            from zvmsdk import dist
            _dist_manager = dist.LinuxDistManager()
            linuxdist = _dist_manager.get_linux_dist("rhcos4")()
            ip_config = linuxdist.create_coreos_parameter(guest_networks)
            nic_id = self._generate_increasing_nic_id(
                                ip_config.split(":")[5].replace("enc", ""))

            cmd += ["--ignitionurl=%s" % transportfiles, "--nicid=%s" % nic_id,
                    "--ipconfig=%s" % ip_config]

        LOG.info("Running command: %s", cmd)
        try:
            (rc, output) = zvmutils.execute(cmd,
                               timeout=CONF.volume.refresh_bootmap_timeout)
        except subprocess.TimeoutExpired as err:
            err_msg = err.format_message()
            raise exception.SDKVolumeOperationError(rs=7, msg=err_msg)
        except PermissionError:
            # because zvmsdk user dont have permission to kill background
            # process so if the excute timeout, will raise PermissionError
            # we also treat it as timeout exception
            err_msg = ("Running command: %s timed out." % cmd)
            raise exception.SDKVolumeOperationError(rs=7, msg=err_msg)

        if rc != 0:
            err_msg = ("refresh_bootmap failed with return code: %d." % rc)
            err_output = ""
            output_lines = output.split('\n')
            for line in output_lines:
                if line.__contains__("Exit MSG:"):
                    err_output += ("\\n" + line.strip())
            LOG.error(err_msg + err_output)
            raise exception.SDKVolumeOperationError(rs=5,
                                                    errcode=rc,
                                                    errmsg=err_output)
        output_lines = output.split('\n')
        paths_dict = {}
        for line in output_lines:
            if line.__contains__("RESULT PATHS: "):
                paths_str = line[14:]
                # paths_str format: "FCP1:W1 W2,FCP2:W3 W4"
                # convert paths string into a dict
                paths_list = paths_str.split(',')
                for path in paths_list:
                    fcp, wwpn = path.split(':')
                    wwpn_list = wwpn.split(' ')
                    paths_dict[fcp] = wwpn_list
        return paths_dict

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None, skipdiskcopy=False):
        """ Deploy image and punch config driver to target """
        # (TODO: add the support of multiple disks deploy)
        if skipdiskcopy:
            msg = ('Start guest_deploy without unpackdiskimage, guest: %(vm)s'
                   'os_version: %(img)s' % {'img': image_name, 'vm': userid})
            LOG.info(msg)
        else:
            msg = ('Start to deploy image %(img)s to guest %(vm)s'
                % {'img': image_name, 'vm': userid})
            LOG.info(msg)
            image_file = '/'.join([self._get_image_path_by_name(image_name),
                                   CONF.zvm.user_root_vdev])
            cmd = ['/usr/bin/hexdump', '-C', '-n', '64', image_file]
            with zvmutils.expect_and_reraise_internal_error(modID='guest'):
                (rc, output) = zvmutils.execute(cmd)
                msg = ('Image header info in guest_deploy: rc: %d, header:\n%s'
                       % (rc, output))
                LOG.info(msg)
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

        # Punch transport files if specified
        if transportfiles:
            # Copy transport file to local
            msg = ('Start to send customized file to vm %s' % userid)
            LOG.info(msg)

            try:
                tmp_trans_dir = tempfile.mkdtemp()
                local_trans = '/'.join([tmp_trans_dir,
                                        os.path.basename(transportfiles)])
                if remotehost:
                    cmd = ["/usr/bin/scp", "-B",
                           "-P", CONF.zvm.remotehost_sshd_port,
                           "-o StrictHostKeyChecking=no",
                           ("%s:%s" % (remotehost, transportfiles)),
                           local_trans]
                else:
                    cmd = ["/usr/bin/cp", transportfiles, local_trans]
                with zvmutils.expect_and_reraise_internal_error(modID='guest'):
                    (rc, output) = zvmutils.execute(cmd)
                if rc != 0:
                    err_msg = ('copy config drive with command %(cmd)s '
                               'failed with output: %(res)s' %
                               {'cmd': str(cmd), 'res': output})
                    LOG.error(err_msg)
                    raise exception.SDKGuestOperationError(rs=4, userid=userid,
                                                           err_info=err_msg)

                # Punch config drive to guest userid
                rd = ("changevm %(uid)s punchfile %(file)s --class X" %
                      {'uid': userid, 'file': local_trans})
                action = "punch config drive to userid '%s'" % userid
                with zvmutils.log_and_reraise_smt_request_failed(action):
                    self._request(rd)
            finally:
                # remove the local temp config drive folder
                self._pathutils.clean_temp_folder(tmp_trans_dir)
        # Authorize iucv client
        client_id = None
        # try to re-use previous iucv authorized userid at first
        if os.path.exists(const.IUCV_AUTH_USERID_PATH):
            LOG.debug("Re-use previous iucv authorized userid")
            with open(const.IUCV_AUTH_USERID_PATH) as f:
                client_id = f.read().strip()
        self.guest_authorize_iucv_client(userid, client_id)
        # Update os version in guest metadata
        # TODO: may should append to old metadata, not replace
        if skipdiskcopy:
            os_version = image_name
        else:
            image_info = self._ImageDbOperator.image_query_record(image_name)
            os_version = image_info[0]['imageosdistro']
        metadata = 'os_version=%s' % os_version
        self._GuestDbOperator.update_guest_by_userid(userid, meta=metadata)

        if skipdiskcopy:
            msg = ('guest_deploy without unpackdiskimage finish successfully, '
                   'guest: %(vm)s, os_version: %(img)s'
                   % {'img': image_name, 'vm': userid})
        else:
            msg = ('Deploy image %(img)s to guest %(vm)s disk %(vdev)s'
               ' successfully' % {'img': image_name, 'vm': userid,
                                  'vdev': vdev})
        LOG.info(msg)

    def guest_deploy_rhcos(self, userid, image_name, transportfiles,
                           remotehost=None, vdev=None, hostname=None,
                           skipdiskcopy=False):
        """ Deploy image"""
        # (TODO: add the support of multiple disks deploy)
        if transportfiles is None:
            err_msg = 'Ignition file is required when deploying RHCOS image'
            LOG.error(err_msg)
            raise exception.SDKGuestOperationError(rs=13, userid=userid)
        if skipdiskcopy:
            msg = ('Start guest_deploy without copy disk, guest: %(vm)s'
                   'os_version: %(img)s' % {'img': image_name, 'vm': userid})
            LOG.info(msg)
            image_file = None
        else:
            msg = ('Start to deploy image %(img)s to guest %(vm)s'
                % {'img': image_name, 'vm': userid})
            LOG.info(msg)
            image_file = '/'.join([self._get_image_path_by_name(image_name),
                        CONF.zvm.user_root_vdev])

        # Unpack image file to root disk
        vdev = vdev or CONF.zvm.user_root_vdev
        tmp_trans_dir = None

        try:
            if remotehost:
                # download igintion file from remote host
                tmp_trans_dir = tempfile.mkdtemp()
                local_trans = '/'.join([tmp_trans_dir,
                                        os.path.basename(transportfiles)])
                cmd = ["/usr/bin/scp", "-B",
                       "-P", CONF.zvm.remotehost_sshd_port,
                       "-o StrictHostKeyChecking=no",
                       ("%s:%s" % (remotehost, transportfiles)),
                       local_trans]
                with zvmutils.expect_and_reraise_internal_error(modID='guest'):
                    (rc, output) = zvmutils.execute(cmd)
                if rc != 0:
                    err_msg = ('copy ignition file with command %(cmd)s '
                               'failed with output: %(res)s' %
                               {'cmd': str(cmd), 'res': output})
                    LOG.error(err_msg)
                    raise exception.SDKGuestOperationError(rs=4, userid=userid,
                                                           err_info=err_msg)
                transportfiles = local_trans

            cmd = self._get_unpackdiskimage_cmd_rhcos(userid, image_name,
                                                      transportfiles, vdev,
                                                      image_file, hostname,
                                                      skipdiskcopy)
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
        finally:
            # remove the temp ignition file
            if tmp_trans_dir:
                self._pathutils.clean_temp_folder(tmp_trans_dir)

        # Update os version in guest metadata
        # TODO: may should append to old metadata, not replace
        if skipdiskcopy:
            os_version = image_name
        else:
            os_version = self.image_get_os_distro(image_name)
        metadata = 'os_version=%s' % os_version
        self._GuestDbOperator.update_guest_by_userid(userid, meta=metadata)

        if skipdiskcopy:
            msg = ('guest_deploy without copy disk finish successfully, '
                   'guest: %(vm)s, os_version: %(img)s'
                   % {'img': image_name, 'vm': userid})
        else:
            msg = ('Deploy image %(img)s to guest %(vm)s disk %(vdev)s'
               ' successfully' % {'img': image_name, 'vm': userid,
                                  'vdev': vdev})
        LOG.info(msg)

    def get_os_version_from_userid(self, userid):
        """Get the os_verison of guests from userid.
        return os_version or UNKNOWN"""
        action = "get guests os_version from userid."
        with zvmutils.log_and_reraise_sdkbase_error(action):
            guests_in_db = self._GuestDbOperator.\
                get_guest_metadata_with_userid(userid)
        # db query return metadata in tuple (metadata)
        os_version = 'UNKNOWN'
        for g in guests_in_db:
            if 'os_version='.upper() in g[0].upper():
                os_version = g[0].upper().strip().split('=')[1]
            break
        return os_version

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6, capture_device_assign=None):
        if capture_type == "alldisks":
            func = ('Capture guest with type: %s' % capture_type)
            msg = ('%s is not supported in current release' % func)
            LOG.error(msg)
            raise exception.SDKFunctionNotImplementError(func=func,
                                                         modID='guest')
        msg = ('Start to capture %(vm)s to generate image %(img)s with '
               'capture type %(type)s' % {'vm': userid,
                                          'img': image_name,
                                          'type': capture_type})
        LOG.info(msg)

        # self._check_power_state(userid, 'capture')
        restart_flag = False
        reachable = self.get_guest_connection_status(userid)
        if reachable:
            # Make sure iucv channel is ready for communication on source vm
            try:
                self.execute_cmd(userid, 'pwd')
            except exception.SDKSMTRequestFailed as err:
                msg = ('Failed to check iucv status on capture source vm '
                       '%(vm)s with error %(err)s'
                       % {'vm': userid, 'err': err.results['response'][0]})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            # Get the os version of the vm
            try:
                os_version = self.guest_get_os_version(userid)
            except exception.SDKSMTRequestFailed as err:
                msg = ('Failed to execute command on capture source vm %(vm)s'
                       'to get os version with error %(err)s'
                       % {'vm': userid, 'err': err.results['response'][0]})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            except Exception as err:
                msg = ('Error happened when parsing os version on source vm '
                       '%(vm)s with error: %(err)s'
                       % {'vm': userid, 'err': six.text_type(err)})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            msg = ('The capture source vm os version %(vm)s is %(version)s'
                   % {'vm': userid, 'version': os_version})
            LOG.info(msg)
            # Find the root device according to the capture type
            try:
                capture_devices = self._get_capture_devices(userid,
                                                            capture_type)
            except exception.SDKSMTRequestFailed as err:
                msg = ('Failed to execute command on source vm %(vm)s to get '
                       'devices for capture with error %(err)s'
                       % {'vm': userid, 'err': err.results['response'][0]})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            except Exception as err:
                msg = ('Internal error happened when getting the devices for '
                       'capture on source vm %(vm)s with error %(err)s' %
                       {'vm': userid, 'err': six.text_type(err)})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            except exception.SDKGuestOperationError:
                raise

            # Shutdown the vm before capture
            self.guest_softstop(userid)
            # keep restart flag used after capture.
            restart_flag = True
        else:
            os_version = self.get_os_version_from_userid(userid)
            # Capture_device_assign as assign capture disk.
            # Input should be string to identity disk.
            # use force_capture_disk value first if
            # force_capture_disk=xxxx in zvmsdk.conf.
            if CONF.zvm.force_capture_disk:
                capture_devices = [str(CONF.zvm.force_capture_disk)]
            else:
                if capture_device_assign:
                    capture_devices = [str(capture_device_assign)]
                else:
                    direct_info = self.get_user_direct(userid)
                    disk_info =\
                        [x for x in direct_info if x.startswith('MDISK')]
                    capture_devices = \
                        [x.split(' ')[1].strip(' ') for x in disk_info]
            if not capture_devices:
                msg = ('Error happened when getting the devices for '
                       'get vm disk information on source vm %(vm)s '
                       % {'vm': userid})
                LOG.error(msg)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       msg=msg)
            # if VM power on, the VM need be perform stop and start
            power_state = self.get_power_state(userid)
            if power_state == 'on':
                # Shutdown the vm before capture
                self.guest_stop(userid)
                restart_flag = True

        # Prepare directory for writing image file
        image_temp_dir = '/'.join((CONF.image.sdk_image_repository,
                                   const.IMAGE_TYPE['CAPTURE'],
                                   os_version,
                                   image_name))
        self._pathutils.mkdir_if_not_exist(image_temp_dir)

        # Call creatediskimage to capture a vm to generate an image
        # TODO:(nafei) to support multiple disk capture
        vdev = capture_devices[0]
        msg = ('Found the device %(vdev)s of %(vm)s for capture' %
               {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

        image_file_name = vdev
        image_file_path = '/'.join((image_temp_dir, image_file_name))
        cmd = ['sudo', '/opt/zthin/bin/creatediskimage', userid, vdev,
               image_file_path, '--compression', str(compress_level)]
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
                self._pathutils.clean_temp_folder(image_temp_dir)
                self._pathutils.clean_temp_folder(image_final_dir)
                raise exception.SDKGuestOperationError(rs=5, userid=userid,
                                                       err=err_msg)
        self._pathutils.clean_temp_folder(image_temp_dir)

        msg = ('Updating the metadata for captured image %s ' % image_name)
        LOG.info(msg)
        # Get md5sum of image
        real_md5sum = self._get_md5sum(image_final_path)
        # Get disk_size_units of image
        disk_size_units = self._get_disk_size_units(image_final_path)
        # Get the image physical size
        image_size = self._get_image_size(image_final_path)
        # Create the image record in image database
        self._ImageDbOperator.image_add_record(image_name, os_version,
            real_md5sum, disk_size_units, image_size,
            capture_type)
        if restart_flag:
            LOG.info('Try start %s for capture completed successfully.'
                     % userid)
            self.guest_start(userid)
        LOG.info('Image %s is captured and imported to image repository '
                 'successfully' % image_name)

    def guest_get_os_version(self, userid):
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
        elif '/etc/system-release' in release_file:
            # For some rhel6.7 system, it only have system-release file and
            # the output looks like:
            # "Red Hat Enterprise Linux Server release 6.7 (Santiago)"
            distro = 'rhel'
            release_info = self.execute_cmd(userid, 'cat /etc/system-release')
            distro_version = release_info[0].split()[6]
            os_version = ''.join((distro, distro_version))
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

    def _get_unpackdiskimage_cmd_rhcos(self, userid, image_name,
                                       transportfiles=None, vdev=None,
                                       image_file=None, hostname=None,
                                       skipdiskcopy=False):
        if skipdiskcopy:
            os_version = image_name
            image_disk_type = 'SCSI'
        else:
            os_version = self.image_get_os_distro(image_name)
            # Query image disk type
            image_disk_type = self._get_image_disk_type(image_name)
            if image_disk_type is None:
                err_msg = ("failed to get image disk type for "
                           "image '%(image_name)s'."
                            % {'image_name': image_name})
                raise exception.SDKGuestOperationError(rs=12, userid=userid,
                                                   err=err_msg)
        try:
            # Query vm's disk pool type and image disk type
            from zvmsdk import dist
            _dist_manager = dist.LinuxDistManager()
            linuxdist = _dist_manager.get_linux_dist(os_version)()
            # Read coros fixed ip parameter from tempfile
            fixed_ip_parameter = linuxdist.read_coreos_parameter(userid)
        except Exception as err:
            err_msg = ("failed to read coreos fixed ip "
                        "parameters for userid '%(userid)s',"
                        "error: %(err)s."
                        % {'userid': userid, 'err': err})
            raise exception.SDKGuestOperationError(rs=12, userid=userid,
                                               err=err_msg)
        if fixed_ip_parameter is None:
            err_msg = ("coreos fixed ip parameters don't exist.")
            raise exception.SDKGuestOperationError(rs=12, userid=userid,
                                               err=err_msg)
        if hostname:
            # replace hostname to display name instead of userid
            fixed_ip_parameter = fixed_ip_parameter.replace(userid.upper(),
                                                            hostname)
        # read nic device id and change it into the form like
        # "0.0.1000,0.0.1001,0.0.1002"
        nic_id = self._generate_increasing_nic_id(
            fixed_ip_parameter.split(":")[5].replace("enc", ""))

        if image_disk_type == 'SCSI':
            (wwpn, lun) = self._get_wwpn_lun(userid)
            if wwpn is None or lun is None:
                err_msg = ("wwpn and lun is required for FCP devices,"
                           " please set LOADDEV for userid %s" % userid)
                raise exception.SDKGuestOperationError(rs=14, userid=userid,
                                                       msg=err_msg)
            wwpn = '0x' + wwpn
            lun = '0x' + lun
            if skipdiskcopy:
                return ['sudo', '/opt/zthin/bin/unpackdiskimage', vdev,
                        wwpn, lun, transportfiles, nic_id, fixed_ip_parameter]
            else:
                return ['sudo', '/opt/zthin/bin/unpackdiskimage', vdev,
                        wwpn, lun, image_file, transportfiles,
                        image_disk_type, nic_id, fixed_ip_parameter]
        else:
            return ['sudo', '/opt/zthin/bin/unpackdiskimage', userid, vdev,
                   image_file, transportfiles, image_disk_type, nic_id,
                   fixed_ip_parameter]

    def get_switch_info(self, portid):
        return self._NetDbOperator.switch_select_record(nic_id=portid)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        """Set vswitch to grant user."""
        # Check if the userid has already been granted for the vswitch,
        # if yes, then do nothing. Otherwise, it will cause the existing
        # NICs in the VM down on the vswitch.
        vsw_info = self.query_vswitch(vswitch_name)
        if (userid in vsw_info['authorized_users'] or
            userid.lower() in vsw_info['authorized_users'] or
            userid.upper() in vsw_info['authorized_users']):
            LOG.info("The userid %s has already been granted to "
                     "vswitch %s. Do nothing." % (userid, vswitch_name))
            return

        smt_userid = zvmutils.get_smt_userid()
        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Vswitch_Set_Extended' % smt_userid,
            "--operands",
            "-k switch_name=%s" % vswitch_name,
            "-k grant_userid=%s" % userid,
            "-k persist=YES"))

        try:
            self._request(requestData)
        except exception.SDKSMTRequestFailed as err:
            LOG.error("Failed to grant user %s to vswitch %s, error: %s"
                      % (userid, vswitch_name, err.format_message()))
            self._set_vswitch_exception(err, vswitch_name)

    def _set_vswitch_exception(self, error, switch_name):
        if ((error.results['rc'] == 212) and (error.results['rs'] == 40)):
            obj_desc = "Vswitch %s" % switch_name
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 396) and (error.results['rs'] == 2846)):
            errmsg = ("Operation is not allowed for a "
                      "VLAN UNAWARE vswitch")
            raise exception.SDKConflictError(modID='network', rs=5,
                                             vsw=switch_name,
                                             msg=errmsg)
        elif ((error.results['rc'] == 396) and
              ((error.results['rs'] == 2838) or
               (error.results['rs'] == 2853) or
               (error.results['rs'] == 2856) or
               (error.results['rs'] == 2858) or
               (error.results['rs'] == 3022) or
               (error.results['rs'] == 3033))):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=5,
                                             vsw=switch_name,
                                             msg=errmsg)
        else:
            raise error

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        """Revoke user for vswitch."""
        smt_userid = zvmutils.get_smt_userid()
        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Vswitch_Set_Extended' % smt_userid,
            "--operands",
            "-k switch_name=%s" % vswitch_name,
            "-k revoke_userid=%s" % userid,
            "-k persist=YES"))

        try:
            self._request(requestData)
        except exception.SDKSMTRequestFailed as err:
            LOG.error("Failed to revoke user %s from vswitch %s, error: %s"
                      % (userid, vswitch_name, err.format_message()))
            self._set_vswitch_exception(err, vswitch_name)

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        if uid_list == []:
            return {}

        if not isinstance(uid_list, list):
            uid_list = [uid_list]

        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API Image_Performance_Query" % smt_userid,
            "--operands",
            '-T "%s"' % (' '.join(uid_list)),
            "-c %d" % len(uid_list)))
        action = "get performance info of userid '%s'" % str(uid_list)
        with zvmutils.log_and_reraise_smt_request_failed(action):
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
                if (emsg.__contains__("No value matched with keywords.")):
                    continue
                else:
                    raise err
            for k, v in pi.items():
                pi[k] = v.strip('" ')
            if pi.get('userid') is not None:
                pi_dict[pi['userid']] = pi

        return pi_dict

    def system_image_performance_query(self, namelist):
        """Call System_Image_Performance_Query to get guest current status.

        :namelist: A namelist that defined in smapi namelist file.
        """
        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API System_Image_Performance_Query" % smt_userid,
            "--operands -T %s" % namelist))
        action = "get performance info of namelist '%s'" % namelist
        with zvmutils.log_and_reraise_smt_request_failed(action):
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
                if (emsg.__contains__("No value matched with keywords.")):
                    continue
                else:
                    raise err
            for k, v in pi.items():
                pi[k] = v.strip('" ')
            if pi.get('userid') is not None:
                pi_dict[pi['userid']] = pi

        return pi_dict

    def virtual_network_vswitch_query_byte_stats(self):
        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query_Byte_Stats" %
            smt_userid,
            "--operands",
            '-T "%s"' % smt_userid,
            '-k "switch_name=*"'
            ))
        action = "query vswitch usage info"
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(rd)
        return self._parse_vswitch_inspect_data(results['response'])

    def get_host_info(self):
        with zvmutils.log_and_reraise_smt_request_failed():
            results = self._request("getHost general")
        host_info = zvmutils.translate_response_to_dict(
            '\n'.join(results['response']), const.RINV_HOST_KEYWORDS)

        return host_info

    def get_diskpool_info(self, pool, details=False):
        with zvmutils.log_and_reraise_smt_request_failed():
            details_required = ''
            dp_info = {}
            if details is False:
                details_required = 'false'
            else:
                details_required = 'true'
            results = self._request("getHost diskpoolspace %s %s" % (pool, details_required))
            if not details:
                dp_info = zvmutils.translate_response_to_dict(
                    '\n'.join(results['response']), const.DISKPOOL_KEYWORDS)
            else:
                dp_info = zvmutils.translate_disk_pool_info_to_dict(pool, '\n'.join(results['response']))
        return dp_info

    def get_vswitch_list(self):
        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query" % smt_userid,
            "--operands",
            "-s \'*\'"))
        try:
            result = self._request(rd)
        except exception.SDKSMTRequestFailed as err:
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
                                  if isinstance(s, six.string_types)])
                output = re.findall('VSWITCH:  Name: (.*)', data)
                return output

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        smt_userid = zvmutils.get_smt_userid()
        msg = ('Start to set VLAN ID %(vid)s on vswitch %(vsw)s '
               'for guest %(vm)s'
                % {'vid': vlan_id, 'vsw': vswitch_name, 'vm': userid})
        LOG.info(msg)

        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Set_Extended" %
            smt_userid,
            "--operands",
            "-k grant_userid=%s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k user_vlan_id=%s" % vlan_id,
            "-k persist=YES"))

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            LOG.error("Failed to set VLAN ID %s on vswitch %s for user %s, "
                      "error: %s" %
                      (vlan_id, vswitch_name, userid, err.format_message()))
            self._set_vswitch_exception(err, vswitch_name)
        msg = ('Set VLAN ID %(vid)s on vswitch %(vsw)s '
               'for guest %(vm)s successfully'
                % {'vid': vlan_id, 'vsw': vswitch_name, 'vm': userid})
        LOG.info(msg)

    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='ETHERNET',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):

        smt_userid = zvmutils.get_smt_userid()
        msg = ('Start to create vswitch %s' % name)
        LOG.info(msg)
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Create_Extended" %
            smt_userid,
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

        msg = ('Start to create vswitch %s' % name)
        LOG.info(msg)
        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            LOG.error("Failed to create vswitch %s, error: %s" %
                      (name, err.format_message()))
            raise
        msg = ('Create vswitch %s successfully' % name)
        LOG.info(msg)

    def set_vswitch(self, switch_name, **kwargs):
        """Set vswitch"""
        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Set_Extended" %
            smt_userid,
            "--operands",
            "-k switch_name=%s" % switch_name))

        for k, v in kwargs.items():
            rd = ' '.join((rd,
                           "-k %(key)s=\'%(value)s\'" %
                           {'key': k, 'value': v}))

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            LOG.error("Failed to set vswitch %s, error: %s" %
                      (switch_name, err.format_message()))
            self._set_vswitch_exception(err, switch_name)

    def delete_vswitch(self, switch_name, persist=True):
        smt_userid = zvmutils.get_smt_userid()
        msg = ('Start to delete vswitch %s' % switch_name)
        LOG.info(msg)
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Delete_Extended" %
            smt_userid,
            "--operands",
            "-k switch_name=%s" % switch_name,
            "-k persist=%s" % (persist and 'YES' or 'NO')))

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            results = err.results
            if ((results['rc'] == 212) and
                (results['rs'] == 40)):
                LOG.warning("Vswitch %s does not exist", switch_name)
                return
            else:
                LOG.error("Failed to delete vswitch %s, error: %s" %
                      (switch_name, err.format_message()))
                raise
        msg = ('Delete vswitch %s successfully' % switch_name)
        LOG.info(msg)

    def create_nic(self, userid, vdev=None, nic_id=None,
                   mac_addr=None, active=False):
        nic_vdev = self._get_available_vdev(userid, vdev=vdev)

        LOG.debug('Nic attributes: vdev is %(vdev)s, '
                  'ID is %(id)s, address is %(address)s',
                  {'vdev': nic_vdev,
                   'id': nic_id or 'not specified',
                   'address': mac_addr or 'not specified'})
        self._create_nic(userid, nic_vdev, nic_id=nic_id,
                         mac_addr=mac_addr, active=active)
        return nic_vdev

    def _create_nic_inactive_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=7,
                                             vdev=vdev, userid=userid,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 12)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKConflictError(modID='network', rs=7,
                                             vdev=vdev, userid=userid,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 4)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=6,
                                             vdev=vdev, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _create_nic_active_exception(self, error, userid, vdev):
        if (((error.results['rc'] == 204) and (error.results['rs'] == 4)) or
            ((error.results['rc'] == 204) and (error.results['rs'] == 28))):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=6,
                                             vdev=vdev, userid=userid,
                                             msg=errmsg)
        elif ((error.results['rc'] == 396) and
               (error.results['rs'] == 2797)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=6,
                                             vdev=vdev, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _is_active(self, userid):
        # Get the vm status
        power_state = self.get_power_state(userid)
        if power_state == 'off':
            LOG.error('The vm %s is powered off, '
                      'active operation is not allowed' % userid)
            raise exception.SDKConflictError(modID='network', rs=1,
                                             userid=userid)

    def _create_nic(self, userid, vdev, nic_id=None, mac_addr=None,
                    active=False):
        if active:
            self._is_active(userid)
        msg = ('Start to create nic device %(vdev)s for guest %(vm)s'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Adapter_Create_Extended_DM' %
            userid,
            "--operands",
            "-k image_device_number=%s" % vdev,
            "-k adapter_type=QDIO"))

        if mac_addr is not None:
            mac = ''.join(mac_addr.split(':'))[6:]
            requestData += ' -k mac_id=%s' % mac

        retry = 1
        for secs in [1, 3, 5, 8, -1]:
            try:
                self._request(requestData)
                break
            except exception.SDKSMTRequestFailed as err:
                if (err.results['rc'] == 400 and
                    err.results['rs'] == 12 and
                    retry < 5):
                    LOG.info("The VM is locked, will retry")
                    time.sleep(secs)
                    retry += 1
                else:
                    LOG.error("Failed to create nic %s for user %s in "
                              "the guest's user direct, error: %s" %
                              (vdev, userid, err.format_message()))
                    self._create_nic_inactive_exception(err, userid, vdev)

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
            except (exception.SDKSMTRequestFailed,
                    exception.SDKInternalError) as err1:
                msg1 = err1.format_message()
                persist_OK = True
                requestData = ' '.join((
                    'SMAPI %s API Virtual_Network_Adapter_Delete_DM' % userid,
                    "--operands",
                    '-v %s' % vdev))
                try:
                    self._request(requestData)
                except (exception.SDKSMTRequestFailed,
                        exception.SDKInternalError) as err2:
                    results = err2.results
                    msg2 = err2.format_message()
                    if ((results['rc'] == 404) and
                        (results['rs'] == 8)):
                        persist_OK = True
                    else:
                        persist_OK = False
                if persist_OK:
                    self._create_nic_active_exception(err1, userid, vdev)
                else:
                    raise exception.SDKNetworkOperationError(rs=4,
                                    nic=vdev, userid=userid,
                                    create_err=msg1, revoke_err=msg2)

        self._NetDbOperator.switch_add_record(userid, vdev, port=nic_id)
        msg = ('Create nic device %(vdev)s for guest %(vm)s successfully'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

    def get_user_direct(self, userid):
        with zvmutils.log_and_reraise_smt_request_failed():
            results = self._request("getvm %s directory" % userid)
        return results.get('response', [])

    def get_all_user_direct(self):
        with zvmutils.log_and_reraise_smt_request_failed():
            results = self._request("getvm alldirectory")
        return results.get('response', [])

    def get_diskpool_volumes(self, pool):
        with zvmutils.log_and_reraise_smt_request_failed():
            results = self._request("gethost diskpoolvolumes %s" % pool)
        diskpool_volumes = zvmutils.translate_response_to_dict(
            '\n'.join(results['response']), const.DISKPOOL_VOLUME_KEYWORDS)
        return diskpool_volumes

    def get_volume_info(self):
        with zvmutils.log_and_reraise_smt_request_failed():
            results = self._request("gethost volumeinfo")
        with zvmutils.expect_invalid_resp_data(results):
            volume_info = zvmutils.translate_response_data_to_expect_dict(
                results['response'], 3)
        return volume_info

    def _delete_nic_active_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 204) and (error.results['rs'] == 28)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=8,
                                             vdev=vdev, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _delete_nic_inactive_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=9,
                                             vdev=vdev, userid=userid,
                                             obj=obj_desc)
        else:
            raise error

    def delete_nic(self, userid, vdev, active=False):
        if active:
            self._is_active(userid)

        vdev_exist = False
        nic_list = self._NetDbOperator.switch_select_record_for_userid(userid)
        for p in nic_list:
            if (int(p['interface'], 16) == int(vdev, 16)):
                vdev_exist = True
                vdev_info = p
                break
        if not vdev_exist:
            # Device has already be removed from user direct
            LOG.warning("Virtual device %s does not exist in the switch table",
                        vdev)
            if active:
                try:
                    resp = self.execute_cmd(userid, 'vmcp q %s' % vdev)
                    nic_info = "%s ON NIC" % vdev.zfill(4).upper()
                    osa_info = "%s ON OSA" % vdev.zfill(4).upper()
                    if nic_info in resp[0]:
                        pass
                    elif osa_info in resp[0]:
                        self._undedicate_nic(userid, vdev, active=active,
                                             del_active_only=True)
                        return
                    else:
                        LOG.warning("Device %s of guest %s is not "
                                    "network adapter" % (vdev, userid))
                        return
                except exception.SDKSMTRequestFailed as err:
                    emsg = err.format_message()
                    ignored_msg = ('Device %s does not exist'
                                   % vdev.zfill(4).upper())
                    if (emsg.__contains__(ignored_msg)):
                        LOG.warning("Virtual device %s does not exist for "
                                    "active guest %s" % (vdev, userid))
                        return
                    else:
                        raise
            else:
                return
        else:
            # Device hasnot be removed from user direct,
            # check whether it is related to a dedicated OSA device
            if ((vdev_info["comments"] is not None) and
                (vdev_info["comments"].__contains__('OSA='))):
                self._undedicate_nic(userid, vdev, active=active)
                return
        msg = ('Start to delete nic device %(vdev)s for guest %(vm)s'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)
        if vdev_exist:
            rd = ' '.join((
                "SMAPI %s API Virtual_Network_Adapter_Delete_DM" %
                userid,
                "--operands",
                '-v %s' % vdev))
            try:
                self._request(rd)
            except exception.SDKSMTRequestFailed as err:
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
                    self._delete_nic_inactive_exception(err, userid, vdev)
            self._NetDbOperator.switch_delete_record_for_nic(userid, vdev)

        if active:
            rd = ' '.join((
                "SMAPI %s API Virtual_Network_Adapter_Delete" %
                userid,
                "--operands",
                '-v %s' % vdev))
            try:
                self._request(rd)
            except exception.SDKSMTRequestFailed as err:
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
                    self._delete_nic_active_exception(err, userid, vdev)
        msg = ('Delete nic device %(vdev)s for guest %(vm)s successfully'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

    def _couple_active_exception(self, error, userid, vdev, vswitch):
        if ((error.results['rc'] == 212) and
            ((error.results['rs'] == 28) or
             (error.results['rs'] == 8))):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=10,
                                             vdev=vdev, userid=userid,
                                             vsw=vswitch,
                                             msg=errmsg)
        elif ((error.results['rc'] == 212) and (error.results['rs'] == 40)):
            obj_desc = "Vswitch %s" % vswitch
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 204) and (error.results['rs'] == 8)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 396) and
              ((error.results['rs'] == 2788) or
               (error.results['rs'] == 2848) or
               (error.results['rs'] == 3034) or
               (error.results['rs'] == 6011))):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=10,
                                             vdev=vdev, userid=userid,
                                             vsw=vswitch,
                                             msg=errmsg)
        else:
            raise error

    def _couple_inactive_exception(self, error, userid, vdev, vswitch):
        if ((error.results['rc'] == 412) and (error.results['rs'] == 28)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=10,
                                             vdev=vdev, userid=userid,
                                             vsw=vswitch,
                                             msg=errmsg)
        elif ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=11,
                                             vdev=vdev, userid=userid,
                                             vsw=vswitch,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 400) and (error.results['rs'] == 4)):
            obj_desc = "Guest %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 12)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKConflictError(modID='network', rs=11,
                                             vdev=vdev, userid=userid,
                                             vsw=vswitch,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 8)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        else:
            raise error

    def _couple_nic(self, userid, vdev, vswitch_name,
                    active=False):
        """Couple NIC to vswitch by adding vswitch into user direct."""
        if active:
            self._is_active(userid)

            requestData = ' '.join((
                'SMAPI %s' % userid,
                'API Virtual_Network_Adapter_Connect_Vswitch',
                "--operands",
                "-v %s" % vdev,
                "-n %s" % vswitch_name))

            try:
                self._request(requestData)
            except (exception.SDKSMTRequestFailed,
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
                    except (exception.SDKSMTRequestFailed,
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
                        self._couple_active_exception(err1, userid, vdev,
                                                      vswitch_name)
                    else:
                        raise exception.SDKNetworkOperationError(rs=3,
                                    nic=vdev, vswitch=vswitch_name,
                                    couple_err=msg1, revoke_err=msg2)

        """Update information in switch table."""
        self._NetDbOperator.switch_update_record_with_switch(userid, vdev,
                                                             vswitch_name)
        msg = ('Couple nic device %(vdev)s of guest %(vm)s '
               'with vswitch %(vsw)s successfully'
                % {'vdev': vdev, 'vm': userid, 'vsw': vswitch_name})
        LOG.info(msg)

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False,
                              vlan_id=-1, port_type='ACCESS'):
        """Couple nic to vswitch."""
        if active:
            msg = ("both in the user direct of guest %s and on "
                   "the active guest system" % userid)
        else:
            msg = "in the user direct of guest %s" % userid
        LOG.debug("Connect nic %s to switch %s %s",
                  nic_vdev, vswitch_name, msg)

        # previously we use Virtual_Network_Adapter_Connect_Vswitch_DM
        # but due to limitation in SMAPI, we have to create such user
        # direct by our own due to no way to add VLAN ID

        msg = ('Start to couple nic device %(vdev)s of guest %(vm)s '
               'with vswitch %(vsw)s with vlan %(vlan_id)s:'
                % {'vdev': nic_vdev, 'vm': userid, 'vsw': vswitch_name,
                   'vlan_id': vlan_id})
        LOG.info(msg)

        user_direct = self.get_user_direct(userid)
        new_user_direct = []
        nicdef = "NICDEF %s" % nic_vdev.upper()
        for ent in user_direct:
            if len(ent) > 0:
                new_user_direct.append(ent)
                if ent.upper().startswith(nicdef):
                    # If NIC already coupled with this vswitch,
                    # return and skip following actions,
                    # such as migrating VM
                    if ("LAN SYSTEM %s" % vswitch_name) in ent:
                        LOG.info("NIC %s already coupled to vswitch %s, "
                                 "skip couple action."
                                 % (nic_vdev, vswitch_name))
                        return
                    # vlan_id < 0 means no VLAN ID given
                    v = nicdef
                    if vlan_id < 0:
                        v += " LAN SYSTEM %s" % vswitch_name
                    else:
                        v += " LAN SYSTEM %s VLAN %s PORTTYPE %s" \
                             % (vswitch_name, vlan_id, port_type)

                    new_user_direct.append(v)
        try:
            self._lock_user_direct(userid)
        except exception.SDKSMTRequestFailed as e:
            raise exception.SDKGuestOperationError(rs=9, userid=userid,
                                                   err=e.format_message())
        # Replace user directory
        try:
            self._replace_user_direct(userid, new_user_direct)
        except exception.SDKSMTRequestFailed as e:
            rd = ("SMAPI %s API Image_Unlock_DM " % userid)
            try:
                self._request(rd)
            except exception.SDKSMTRequestFailed as err2:
                # ignore 'not locked' error
                if ((err2.results['rc'] == 400) and (
                    err2.results['rs'] == 24)):
                    LOG.debug("Guest '%s' unlocked successfully." % userid)
                    pass
                else:
                    # just print error and ignore this unlock error
                    msg = ("Unlock definition of guest '%s' failed "
                           "with SMT error: %s" %
                           (userid, err2.format_message()))
                    LOG.error(msg)

            raise exception.SDKGuestOperationError(rs=10,
                                                   userid=userid,
                                                   err=e.format_message())

        self._couple_nic(userid, nic_vdev, vswitch_name, active=active)

    def _uncouple_active_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 204) and (error.results['rs'] == 8)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 204) and (error.results['rs'] == 28)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=12,
                                             vdev=vdev, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _uncouple_inactive_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 404) and (error.results['rs'] == 8)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 400) and (error.results['rs'] == 4)):
            obj_desc = "Guest %s" % vdev
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID='network')
        elif ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=13,
                                             vdev=vdev, userid=userid,
                                             obj=obj_desc)
        else:
            raise error

    def _uncouple_nic(self, userid, vdev, active=False):
        """Uncouple NIC from vswitch"""
        if active:
            self._is_active(userid)
        msg = ('Start to uncouple nic device %(vdev)s of guest %(vm)s'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Disconnect_DM",
            "--operands",
            "-v %s" % vdev))

        try:
            self._request(requestData)
        except (exception.SDKSMTRequestFailed,
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
                self._uncouple_inactive_exception(err, userid, vdev)

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
            except (exception.SDKSMTRequestFailed,
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
                    self._uncouple_active_exception(err, userid, vdev)
        msg = ('Uncouple nic device %(vdev)s of guest %(vm)s successfully'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

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

    def _delete_uesrid_again(self, rd, userid):
        # ok, this is ugly, as we never know when this will happen
        # so we try the stop again and ignore any exception here

        try:
            self.guest_stop(userid, timeout=30, poll_interval=10)
        except Exception as err:
            msg = "SMT error: %s" % err.format_message()
            LOG.info("guest force stop when 596/6831: %s" % msg)

        # wait some time to let guest shutoff and cleanup
        time.sleep(2)

        try:
            self._request(rd)
        except Exception as err:
            msg = "SMT error: %s" % err.format_message()
            LOG.info("guest force delete when 596/6831: %s" % msg)

    def delete_userid(self, userid):
        rd = ' '.join(('deletevm', userid, 'directory'))
        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            if err.results['rc'] == 400 and err.results['rs'] == 4:
                # guest vm definition not found
                LOG.debug("The guest %s does not exist." % userid)
                return

            # ingore delete VM not finished error
            if err.results['rc'] == 596 and err.results['rs'] == 6831:
                # 596/6831 means delete VM not finished yet
                LOG.warning("The guest %s deleted with 596/6831" % userid)

                self._delete_uesrid_again(rd, userid)
                return

            # ignore delete VM with VDISK format error
            # DirMaint does not support formatting TDISK or VDISK extents.
            if err.results['rc'] == 596 and err.results['rs'] == 3543:
                LOG.debug("The guest %s deleted with 596/3543" % userid)
                return

            # The CP or CMS command shown resulted in a non-zero
            # return code. This message is frequently preceded by
            # a DMK, HCP, or DMS error message that describes the cause
            # https://www-01.ibm.com/servers/resourcelink/svc0302a.nsf/
            # pages/zVMV7R2gc246282/$file/hcpk2_v7r2.pdf
            if err.results['rc'] == 596 and err.results['rs'] == 2119:
                LOG.debug("The guest %s deleted with 596/2119" % userid)
                return

            msg = "SMT error: %s" % err.format_message()
            raise exception.SDKSMTRequestFailed(err.results, msg)

    def delete_vm(self, userid):
        self.delete_userid(userid)

        # remove userid from smapi namelist
        self.namelist_remove(zvmutils.get_namelist(), userid)

        # revoke userid from vswitch
        action = "revoke id %s authority from vswitch" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            switch_info = self._NetDbOperator.switch_select_record_for_userid(
                                                                       userid)
            switch_list = set()
            for item in switch_info:
                switch_list.add(item['switch'])

            for item in switch_list:
                if item is not None:
                    self.revoke_user_from_vswitch(item, userid)

        # cleanup db record from network table
        action = "delete network record for user %s" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._NetDbOperator.switch_delete_record_for_userid(userid)

        # TODO: cleanup db record from volume table
        pass

        # cleanup persistent folder for guest
        self._pathutils.remove_guest_path(userid)

        # cleanup db record from guest table
        action = "delete guest %s from database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.delete_guest_by_userid(userid)

    def execute_cmd(self, userid, cmdStr):
        """"cmdVM."""
        requestData = 'cmdVM ' + userid + ' CMD \'' + cmdStr + '\''
        with zvmutils.log_and_reraise_smt_request_failed(action='execute '
        'command on vm via iucv channel'):
            results = self._request(requestData)

        ret = results['response']
        return ret

    def execute_cmd_direct(self, userid, cmdStr, timeout=None):
        """"cmdVM."""
        if not timeout:
            requestData = 'cmdVM ' + userid + ' CMD \'' + cmdStr + '\''
        else:
            requestData = ("cmdVM %s CMD \'%s\' %s" % (userid, cmdStr,
                                                       timeout))

        results = self._smt.request(requestData)
        return results

    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import the image specified in url to SDK image repository, and
        create a record in image db, the imported images are located in
        image_repository/prov_method/os_version/image_name/, for example,
        /opt/sdk/images/netboot/rhel7.2/90685d2b-167bimage/0100"""
        image_info = []
        try:
            image_info = self._ImageDbOperator.image_query_record(image_name)
        except exception.SDKObjectNotExistError:
            msg = ("The image record %s doens't exist in SDK image datebase,"
                   " will import the image and create record now" % image_name)
            LOG.info(msg)

        # Ensure the specified image is not exist in image DB
        if image_info:
            msg = ("The image name %s has already exist in SDK image "
                   "database, please check if they are same image or consider"
                   " to use a different image name for import" % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=13, img=image_name)

        try:
            image_os_version = image_meta['os_version'].lower()
            target_folder = self._pathutils.create_import_image_repository(
                image_os_version, const.IMAGE_TYPE['DEPLOY'],
                image_name)
        except Exception as err:
            msg = ('Failed to create repository to store image %(img)s with '
                   'error: %(err)s, please make sure there are enough space '
                   'on zvmsdk server and proper permission to create the '
                   'repository' % {'img': image_name,
                                   'err': six.text_type(err)})
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=14, msg=msg)

        if self.is_rhcos(image_os_version):
            image_disk_type = image_meta.get('disk_type')
            if ((image_disk_type is None) or
                ((image_disk_type.upper() != "DASD" and
                  image_disk_type.upper() != "SCSI"))):
                msg = ('Disk type is required for RHCOS image import, '
                       'the value should be DASD or SCSI')
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=14, msg=msg)
            else:
                comments = {'disk_type': image_disk_type.upper()}
                comments = str(comments)
        else:
            comments = None

        try:
            import_image_fn = urlparse.urlparse(url).path.split('/')[-1]
            import_image_fpath = '/'.join([target_folder, import_image_fn])
            self._scheme2backend(urlparse.urlparse(url).scheme).image_import(
                                                    image_name, url,
                                                    import_image_fpath,
                                                    remote_host=remote_host)

            # Check md5 after import to ensure import a correct image
            # TODO change to use query image name in DB
            expect_md5sum = image_meta.get('md5sum')
            real_md5sum = self._get_md5sum(import_image_fpath)
            if expect_md5sum and expect_md5sum != real_md5sum:
                msg = ("The md5sum after import is not same as source image,"
                       " the image has been broken")
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=4)

            # After import to image repository, figure out the image type is
            # single disk image or multiple-disk image,if multiple disks image,
            # extract it,  if it's single image, rename its name to be same as
            # specific vdev
            # TODO: (nafei) use sub-function to check the image type
            image_type = 'rootonly'
            if image_type == 'rootonly':
                final_image_fpath = '/'.join([target_folder,
                                              CONF.zvm.user_root_vdev])
                os.rename(import_image_fpath, final_image_fpath)
            elif image_type == 'alldisks':
                # For multiple disks image, extract it, after extract, the
                # content under image folder is like: 0100, 0101, 0102
                # and remove the image file 0100-0101-0102.tgz
                pass

            # TODO: put multiple disk image into consideration, update the
            # disk_size_units and image_size db field
            if not self.is_rhcos(image_os_version):
                disk_size_units = self._get_disk_size_units(final_image_fpath)
            else:
                disk_size_units = self._get_disk_size_units_rhcos(
                                                            final_image_fpath)
            image_size = self._get_image_size(final_image_fpath)

            # TODO: update the real_md5sum field to include each disk image
            self._ImageDbOperator.image_add_record(image_name,
                                                   image_os_version,
                                                   real_md5sum,
                                                   disk_size_units,
                                                   image_size,
                                                   image_type,
                                                   comments=comments)
            LOG.info("Image %s is import successfully" % image_name)
        except Exception:
            # Cleanup the image from image repository
            self._pathutils.clean_temp_folder(target_folder)
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
         'comments': the comments of the original image
        }
        """
        image_info = self._ImageDbOperator.image_query_record(image_name)
        if not image_info:
            msg = ("The image %s does not exist in image repository"
                      % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=20, img=image_name)

        image_type = image_info[0]['type']
        # TODO: (nafei) according to image_type, detect image exported path
        # For multiple disk image, make the tgz firstly, the specify the
        # source_path to be something like: 0100-0101-0102.tgz
        if image_type == 'rootonly':
            source_path = '/'.join([CONF.image.sdk_image_repository,
                               const.IMAGE_TYPE['DEPLOY'],
                               image_info[0]['imageosdistro'],
                               image_name,
                               CONF.zvm.user_root_vdev])
        else:
            pass

        self._scheme2backend(urlparse.urlparse(dest_url).scheme).image_export(
                                                    source_path, dest_url,
                                                    remote_host=remote_host)

        # TODO: (nafei) for multiple disks image, update the expect_dict
        # to be the tgz's md5sum
        export_dict = {'image_name': image_name,
                       'image_path': dest_url,
                       'os_version': image_info[0]['imageosdistro'],
                       'md5sum': image_info[0]['md5sum'],
                       'comments': image_info[0]['comments']}
        LOG.info("Image %s export successfully" % image_name)
        return export_dict

    def _get_image_disk_size_units(self, image_path):
        """ Return a comma separated string to indicate the image disk size
            and units for each image disk file under image_path
            For single disk image , it looks like: 0100=3338:CYL
            For multiple disk image, it looks like:
            0100=3338:CYL,0101=4194200:BLK, 0102=4370:CYL"""
        pass

    def _get_disk_size_units(self, image_path):

        command = 'hexdump -n 48 -C %s' % image_path
        (rc, output) = zvmutils.execute(command)
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

    def _get_disk_size_units_rhcos(self, image_path):
        command = "fdisk -b 4096 -l %s | head -2 | awk '{print $5}'" % (
                                                                image_path)

        rc = 0
        output = ""
        try:
            # shell should be set True because it is a shell command with
            # pipeline, so can not use utils.execute function here
            output = subprocess.check_output(command, shell=True,
                                             stderr=subprocess.STDOUT)
            output = bytes.decode(output)
        except subprocess.CalledProcessError as err:
            rc = err.returncode
            output = err.output
        except Exception as err:
            err_msg = ('Command "%s" Error: %s' % (' '.join(command),
                                                   str(err)))
            raise exception.SDKInternalError(msg=err_msg)

        if rc or output.strip('1234567890*\n'):
            msg = ("Error happened when executing command fdisk with "
                   "reason: %s" % output)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=8)

        image_size = output.split()[0]

        try:
            cyl = (float(image_size)) / 737280
            cyl = str(int(math.ceil(cyl)))
        except Exception:
            msg = ("Failed to convert %s to a number of cylinders."
                   % image_size)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=14, msg=msg)
        disk_units = "CYL"
        root_disk_units = ':'.join([str(cyl), disk_units])

        LOG.debug("The image's root_disk_units is %s" % root_disk_units)
        return root_disk_units

    def _get_image_size(self, image_path):
        """Return disk size in bytes"""
        command = 'du -b %s' % image_path
        (rc, output) = zvmutils.execute(command)
        if rc:
            msg = ("Error happened when executing command du -b with"
                   "reason: %s" % output)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=8)
        size = output.split()[0]
        return size

    def _get_image_path_by_name(self, image_name):
        try:
            target_info = self._ImageDbOperator.image_query_record(image_name)
        except exception.SDKObjectNotExistError:
            msg = ("The image %s does not exist in image repository"
                   % image_name)
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=20, img=image_name)

        # TODO: (nafei) Handle multiple disks image deploy
        image_path = '/'.join([CONF.image.sdk_image_repository,
                               const.IMAGE_TYPE['DEPLOY'],
                               target_info[0]['imageosdistro'],
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
            LOG.error(msg)
            raise exception.SDKImageOperationError(rs=2, schema=scheme)

    def _get_md5sum(self, fpath):
        """Calculate the md5sum of the specific image file"""
        try:
            current_md5 = hashlib.md5()
            if isinstance(fpath, six.string_types) and os.path.exists(fpath):
                with open(fpath, "rb") as fh:
                    for chunk in self._read_chunks(fh):
                        current_md5.update(chunk)

            elif (fpath.__class__.__name__ in ["StringIO", "StringO"] or
                  isinstance(fpath, IOBase)):
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
        try:
            self._delete_image_file(image_name)
            # Delete image record from db
            self._ImageDbOperator.image_delete_record(image_name)
        except exception.SDKImageOperationError as err:
            results = err.results
            if ((results['rc'] == 300) and (results['rs'] == 20)):
                LOG.warning("Image %s does not exist", image_name)
                return
            else:
                LOG.error("Failed to delete image %s, error: %s" %
                          (image_name, err.format_message()))
                raise
        msg = ('Delete image %s successfully' % image_name)
        LOG.info(msg)

    def _delete_image_file(self, image_name):
        image_path = self._get_image_path_by_name(image_name)
        self._pathutils.clean_temp_folder(image_path)

    def _get_image_last_access_time(self, image_name, raise_exception=True):
        """Get the last access time of the image."""
        image_file = os.path.join(self._get_image_path_by_name(image_name),
                                  CONF.zvm.user_root_vdev)
        if not os.path.exists(image_file):
            if raise_exception:
                msg = 'Failed to get time stamp of image:%s' % image_name
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=23, img=image_name)
            else:
                # An invalid timestamp
                return -1
        atime = os.path.getatime(image_file)
        return atime

    def image_query(self, image_name=None):
        image_info = self._ImageDbOperator.image_query_record(image_name)
        if not image_info:
            # because database maybe None, so return nothing here
            return []

        # if image_name is not None, means there is only one record
        if image_name:
            last_access_time = self._get_image_last_access_time(
                                   image_name, raise_exception=False)
            image_info[0]['last_access_time'] = last_access_time
        else:
            for item in image_info:
                image_name = item['imagename']
                # set raise_exception to false because one failed
                # may stop processing all the items in the list
                last_access_time = self._get_image_last_access_time(
                                       image_name, raise_exception=False)
                item['last_access_time'] = last_access_time
        return image_info

    def image_get_root_disk_size(self, image_name):
        """Return the root disk units of the specified image
        image_name: the unique image name in db
        Return the disk units in format like 3339:CYL or 467200:BLK
        """
        image_info = self.image_query(image_name)
        if not image_info:
            raise exception.SDKImageOperationError(rs=20, img=image_name)
        disk_size_units = image_info[0]['disk_size_units'].split(':')[0]
        return disk_size_units

    def image_get_os_distro(self, image_name):
        """
        Return the operating system distro of the specified image
        """
        image_info = self._ImageDbOperator.image_query_record(image_name)
        if not image_info:
            raise exception.SDKImageOperationError(rs=20, img=image_name)
        os_distro = image_info[0]['imageosdistro']
        return os_distro

    def _get_image_disk_type(self, image_name):
        """
        Return image disk type
        """
        image_info = self._ImageDbOperator.image_query_record(image_name)
        if ((image_info[0]['comments'] is not None) and
            (image_info[0]['comments'].__contains__('disk_type'))):
            image_disk_type = eval(image_info[0]['comments'])['disk_type']
            if image_disk_type == 'DASD':
                return 'ECKD'
            elif image_disk_type == 'SCSI':
                return 'SCSI'
            else:
                return None
        else:
            return None

    def punch_file(self, userid, fn, fclass):
        rd = ("changevm %(uid)s punchfile %(file)s --class %(class)s" %
                      {'uid': userid, 'file': fn, 'class': fclass})
        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err:
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
            mount_dir = disk.get('mntdir') or ''.join(['/mnt/ephemeral',
                                                       str(vdev)])
            # the mount point of swap partition is swap
            if fmt == "swap":
                mount_dir = "swap"
            disk_parms = self._generate_disk_parmline(vdev, fmt, mount_dir)
            func_name = '/var/lib/zvmsdk/setupDisk'
            self.aemod_handler(userid, func_name, disk_parms)

        # trigger do-script
        if self.get_power_state(userid) == 'on':
            self.execute_cmd(userid, "/usr/bin/zvmguestconfigure start")

    def aemod_handler(self, instance_name, func_name, parms):
        rd = ' '.join(['changevm', instance_name, 'aemod', func_name,
                       '--invparms', parms])
        action = parms[0] + instance_name
        with zvmutils.log_and_reraise_smt_request_failed(action):
            self._request(rd)

    def get_user_console_output(self, userid):
        # get console into reader
        rd = 'getvm %s consoleoutput' % userid
        action = 'get console log reader file list for guest vm: %s' % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            resp = self._request(rd)

        with zvmutils.expect_invalid_resp_data(resp):
            rf_list = resp['response'][0].rpartition(':')[2].strip().split()

        # TODO: make sure reader device is online
        # via 'cat /sys/bus/ccw/drivers/vmur/0.0.000c/online'
        #     'sudo /sbin/cio_ignore -r 000c; sudo /sbin/chccwdev -e 000c'
        #     'which udevadm &> /dev/null && udevadm settle || udevsettle'

        logs = []
        for rf in rf_list:
            cmd = 'sudo /usr/sbin/vmur re -t -O %s' % rf
            rc, output = zvmutils.execute(cmd)
            if rc == 0:
                logs.append(output)

        return ''.join(logs)

    def query_vswitch(self, switch_name):
        smt_userid = zvmutils.get_smt_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query_Extended" %
            smt_userid,
            "--operands",
            '-k switch_name=%s' % switch_name
            ))

        try:
            results = self._request(rd)
            rd_list = results['response']
        except exception.SDKSMTRequestFailed as err:
            if ((err.results['rc'] == 212) and (err.results['rs'] == 40)):
                msg = 'Vswitch %s does not exist' % switch_name
                LOG.error(msg)
                obj_desc = "Vswitch %s" % switch_name
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID='network')
            else:
                action = "query vswitch details info"
                msg = "Failed to %s. " % action
                msg += "SMT error: %s" % err.format_message()
                LOG.error(msg)
                raise exception.SDKSMTRequestFailed(err.results, msg)

        vsw_info = {}
        with zvmutils.expect_invalid_resp_data():
            # ignore user_vlan_id part and jump to the vswitch basic info
            idx_end = len(rd_list)
            idx = 0
            while ((idx < idx_end) and
                  not rd_list[idx].__contains__('switch_name')):
                idx = idx + 1

            # The next 21 lines contains the vswitch basic info
            # eg, name, type, port_type, vlan_awareness, etc
            for i in range(21):
                rd = rd_list[idx + i].split(':')
                vsw_info[rd[0].strip()] = rd[1].strip()
            idx = idx + 21
            # Skip the vepa_status
            while ((idx < idx_end) and
                  not rd_list[idx].__contains__('real_device_address') and
                  not rd_list[idx].__contains__('port_num') and
                  not rd_list[idx].__contains__('adapter_owner')):
                idx = idx + 1

            def _parse_value(data_list, idx, keyword, offset=1):
                value = data_list[idx].rpartition(keyword)[2].strip()
                if value == '(NONE)':
                    value = 'NONE'
                return idx + offset, value

            def _parse_dev_status(value):
                if value in const.DEV_STATUS.keys():
                    return const.DEV_STATUS[value]
                else:
                    return 'Unknown'

            def _parse_dev_err(value):
                if value in const.DEV_ERROR.keys():
                    return const.DEV_ERROR[value]
                else:
                    return 'Unknown'

            # Start to analyse the real devices info
            vsw_info['real_devices'] = {}
            while ((idx < idx_end) and
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
                                                'dev_status':
                                                        _parse_dev_status(
                                                                dev_status),
                                                'dev_err': _parse_dev_err(
                                                                    dev_err)
                                                }
                # Under some case there would be an error line in the output
                # "Error controller_name is NULL!!", skip this line
                if ((idx < idx_end) and
                    rd_list[idx].__contains__(
                        'Error controller_name is NULL!!')):
                    idx += 1

            # Start to get the authorized userids
            vsw_info['authorized_users'] = {}
            while ((idx < idx_end) and rd_list[idx].__contains__('port_num')):
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
            while ((idx < idx_end) and
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

        def _parse_switch_status(value):
            if value in const.SWITCH_STATUS.keys():
                return const.SWITCH_STATUS[value]
            else:
                return 'Unknown'
        if 'switch_status' in vsw_info.keys():
            vsw_info['switch_status'] = _parse_switch_status(
                                                vsw_info['switch_status'])

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

    def _is_OSA_free(self, OSA_device):
        osa_info = self._query_OSA()
        if 'OSA' not in osa_info.keys():
            return False
        elif len(osa_info['OSA']['FREE']) == 0:
            return False
        else:
            dev1 = str(OSA_device).zfill(4).upper()
            dev2 = str(str(hex(int(OSA_device, 16) + 1))[2:]).zfill(4).upper()
            dev3 = str(str(hex(int(OSA_device, 16) + 2))[2:]).zfill(4).upper()
            if ((dev1 in osa_info['OSA']['FREE']) and
                (dev2 in osa_info['OSA']['FREE']) and
                (dev3 in osa_info['OSA']['FREE'])):
                return True
            else:
                return False

    def _query_OSA(self):
        smt_userid = zvmutils.get_smt_userid()
        rd = "SMAPI %s API Virtual_Network_OSA_Query" % smt_userid
        OSA_info = {}

        try:
            results = self._request(rd)
            rd_list = results['response']
        except exception.SDKSMTRequestFailed as err:
            if ((err.results['rc'] == 4) and (err.results['rs'] == 4)):
                msg = 'No OSAs on system'
                LOG.info(msg)
                return OSA_info
            else:
                action = "query OSA details info"
                msg = "Failed to %s. " % action
                msg += "SMT error: %s" % err.format_message()
                LOG.error(msg)
                raise exception.SDKSMTRequestFailed(err.results, msg)

        with zvmutils.expect_invalid_resp_data():
            idx_end = len(rd_list)
            idx = 0

            def _parse_value(data_list, idx, keyword, offset=1):
                value = data_list[idx].rpartition(keyword)[2].strip()
                return idx + offset, value

            # Start to analyse the osa devices info
            while ((idx < idx_end) and
                  rd_list[idx].__contains__('OSA Address')):
                idx, osa_addr = _parse_value(rd_list, idx,
                                              'OSA Address: ')
                idx, osa_status = _parse_value(rd_list, idx,
                                              'OSA Status: ')
                idx, osa_type = _parse_value(rd_list, idx,
                                              'OSA Type: ')
                if osa_type != 'UNKNOWN':
                    idx, CHPID_addr = _parse_value(rd_list, idx,
                                                   'CHPID Address: ')
                    idx, Agent_status = _parse_value(rd_list, idx,
                                                     'Agent Status: ')
                if osa_type not in OSA_info.keys():
                    OSA_info[osa_type] = {}
                    OSA_info[osa_type]['FREE'] = []
                    OSA_info[osa_type]['BOXED'] = []
                    OSA_info[osa_type]['OFFLINE'] = []
                    OSA_info[osa_type]['ATTACHED'] = []

                if osa_status.__contains__('ATT'):
                    id = osa_status.split()[1]
                    item = (id, osa_addr)
                    OSA_info[osa_type]['ATTACHED'].append(item)
                else:
                    OSA_info[osa_type][osa_status].append(osa_addr)

        return OSA_info

    def _get_available_vdev(self, userid, vdev=None):
        ports_info = self._NetDbOperator.switch_select_table()
        vdev_info = []
        for p in ports_info:
            if p['userid'] == userid.upper():
                vdev_info.append(p['interface'])

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
                    raise exception.SDKConflictError(modID='network', rs=6,
                                                     vdev=vdev, userid=userid,
                                                     msg=errmsg)
        if ((len(nic_vdev) > 4) or
            (len(str(hex(int(nic_vdev, 16) + 2))[2:]) > 4)):
            errmsg = ("Virtual device number %s is not valid" % nic_vdev)
            raise exception.SDKInvalidInputFormat(msg=errmsg)
        return nic_vdev

    def dedicate_OSA(self, userid, OSA_device, vdev=None, active=False):
        nic_vdev = self._get_available_vdev(userid, vdev=vdev)

        if not self._is_OSA_free(OSA_device):
            errmsg = ("The specified OSA device number %s "
                      "is not free" % OSA_device)
            raise exception.SDKConflictError(modID='network', rs=14,
                                             osa=OSA_device, userid=userid,
                                             msg=errmsg)

        LOG.debug('Nic attributes: vdev is %(vdev)s, '
                  'dedicated OSA device is %(osa)s',
                  {'vdev': nic_vdev,
                   'osa': OSA_device})
        self._dedicate_OSA(userid, OSA_device, nic_vdev, active=active)
        return nic_vdev

    def _dedicate_OSA_inactive_exception(self, error, userid, vdev,
                                         OSA_device):
        if ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=15,
                                             osa=OSA_device, userid=userid,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 12)):
            obj_desc = "Guest device %s" % vdev
            raise exception.SDKConflictError(modID='network', rs=15,
                                             osa=OSA_device, userid=userid,
                                             obj=obj_desc)
        elif ((error.results['rc'] == 404) and (error.results['rs'] == 4)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=14,
                                             osa=OSA_device, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _dedicate_OSA_active_exception(self, error, userid, OSA_device):
        if (((error.results['rc'] == 204) and (error.results['rs'] == 4)) or
            ((error.results['rc'] == 204) and (error.results['rs'] == 8)) or
            ((error.results['rc'] == 204) and (error.results['rs'] == 16))):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=14,
                                             osa=OSA_device, userid=userid,
                                             msg=errmsg)
        else:
            raise error

    def _dedicate_OSA(self, userid, OSA_device, vdev, active=False):
        if active:
            self._is_active(userid)

        msg = ('Start to dedicate nic device %(vdev)s of guest %(vm)s '
               'to OSA device %(osa)s'
                % {'vdev': vdev, 'vm': userid, 'osa': OSA_device})
        LOG.info(msg)

        def_vdev = vdev
        att_OSA_device = OSA_device
        for i in range(3):
            requestData = ' '.join((
                'SMAPI %s API Image_Device_Dedicate_DM' %
                userid,
                "--operands",
                "-v %s" % def_vdev,
                "-r %s" % att_OSA_device))

            try:
                self._request(requestData)
            except (exception.SDKSMTRequestFailed,
                    exception.SDKInternalError) as err:
                LOG.error("Failed to dedicate OSA %s to nic %s for user %s "
                          "in the guest's user direct, error: %s" %
                          (att_OSA_device, def_vdev, userid,
                          err.format_message()))
                # TODO revoke the dedicated OSA in user direct
                while (int(def_vdev, 16) != int(vdev, 16)):
                    def_vdev = str(hex(int(def_vdev, 16) - 1))[2:]
                    requestData = ' '.join((
                        'SMAPI %s API Image_Device_Undedicate_DM' %
                        userid,
                        "--operands",
                        "-v %s" % def_vdev))
                    try:
                        self._request(requestData)
                    except (exception.SDKSMTRequestFailed,
                            exception.SDKInternalError) as err2:
                        if ((err2.results['rc'] == 404) and
                            (err2.results['rs'] == 8)):
                            pass
                        else:
                            LOG.error("Failed to Undedicate nic %s for user"
                                      " %s in the guest's user direct, "
                                      "error: %s" %
                                      (def_vdev, userid,
                                       err2.format_message()))
                        pass
                self._dedicate_OSA_inactive_exception(err, userid, vdev,
                                                      OSA_device)

            def_vdev = str(hex(int(def_vdev, 16) + 1))[2:]
            att_OSA_device = str(hex(int(att_OSA_device, 16) + 1))[2:]

        if active:
            def_vdev = vdev
            att_OSA_device = OSA_device
            for i in range(3):
                requestData = ' '.join((
                    'SMAPI %s API Image_Device_Dedicate' %
                    userid,
                    "--operands",
                    "-v %s" % def_vdev,
                    "-r %s" % att_OSA_device))

                try:
                    self._request(requestData)
                except (exception.SDKSMTRequestFailed,
                        exception.SDKInternalError) as err:
                    LOG.error("Failed to dedicate OSA %s to nic %s for user "
                              "%s on the active guest system, error: %s" %
                              (att_OSA_device, def_vdev, userid,
                              err.format_message()))
                    # TODO revoke the dedicated OSA in user direct and active
                    detach_vdev = vdev
                    for j in range(3):
                        requestData = ' '.join((
                            'SMAPI %s API Image_Device_Undedicate_DM' %
                            userid,
                            "--operands",
                            "-v %s" % detach_vdev))
                        try:
                            self._request(requestData)
                        except (exception.SDKSMTRequestFailed,
                                exception.SDKInternalError) as err2:
                            if ((err2.results['rc'] == 404) and
                                (err2.results['rs'] == 8)):
                                pass
                            else:
                                LOG.error("Failed to Undedicate nic %s for "
                                          "user %s in the guest's user "
                                          "direct, error: %s" %
                                          (def_vdev, userid,
                                           err2.format_message()))
                            pass
                        detach_vdev = str(hex(int(detach_vdev, 16) + 1))[2:]

                    while (int(def_vdev, 16) != int(vdev, 16)):
                        def_vdev = str(hex(int(def_vdev, 16) - 1))[2:]
                        requestData = ' '.join((
                            'SMAPI %s API Image_Device_Undedicate' %
                            userid,
                            "--operands",
                            "-v %s" % def_vdev))
                        try:
                            self._request(requestData)
                        except (exception.SDKSMTRequestFailed,
                                exception.SDKInternalError) as err3:
                            if ((err3.results['rc'] == 204) and
                                (err3.results['rs'] == 8)):
                                pass
                            else:
                                LOG.error("Failed to Undedicate nic %s for "
                                          "user %s on the active guest "
                                          "system, error: %s" %
                                          (def_vdev, userid,
                                           err3.format_message()))
                            pass
                    self._dedicate_OSA_active_exception(err, userid,
                                                        OSA_device)

                def_vdev = str(hex(int(def_vdev, 16) + 1))[2:]
                att_OSA_device = str(hex(int(att_OSA_device, 16) + 1))[2:]

        OSA_desc = 'OSA=%s' % OSA_device
        self._NetDbOperator.switch_add_record(userid, vdev, comments=OSA_desc)
        msg = ('Dedicate nic device %(vdev)s of guest %(vm)s '
               'to OSA device %(osa)s successfully'
                % {'vdev': vdev, 'vm': userid, 'osa': OSA_device})
        LOG.info(msg)

    def _undedicate_nic_active_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 204) and (error.results['rs'] == 44)):
            errmsg = error.format_message()
            raise exception.SDKConflictError(modID='network', rs=16,
                                             userid=userid, vdev=vdev,
                                             msg=errmsg)
        else:
            raise error

    def _undedicate_nic_inactive_exception(self, error, userid, vdev):
        if ((error.results['rc'] == 400) and (error.results['rs'] == 12)):
            obj_desc = "Guest %s" % userid
            raise exception.SDKConflictError(modID='network', rs=17,
                                             userid=userid, vdev=vdev,
                                             obj=obj_desc)
        else:
            raise error

    def _undedicate_nic(self, userid, vdev, active=False,
                        del_active_only=False):
        if active:
            self._is_active(userid)

        msg = ('Start to undedicate nic device %(vdev)s of guest %(vm)s'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

        if not del_active_only:
            def_vdev = vdev
            for i in range(3):
                requestData = ' '.join((
                    'SMAPI %s API Image_Device_Undedicate_DM' %
                    userid,
                    "--operands",
                    "-v %s" % def_vdev))

                try:
                    self._request(requestData)
                except (exception.SDKSMTRequestFailed,
                        exception.SDKInternalError) as err:
                    results = err.results
                    emsg = err.format_message()
                    if ((results['rc'] == 404) and
                        (results['rs'] == 8)):
                        LOG.warning("Virtual device %s does not exist in "
                                    "the guest's user direct", vdev)
                    else:
                        LOG.error("Failed to undedicate nic %s for %s in "
                                  "the guest's user direct, error: %s" %
                                  (vdev, userid, emsg))
                    self._undedicate_nic_inactive_exception(err, userid, vdev)
                def_vdev = str(hex(int(def_vdev, 16) + 1))[2:]
            self._NetDbOperator.switch_delete_record_for_nic(userid, vdev)

        if active:
            def_vdev = vdev
            for i in range(3):
                rd = ' '.join((
                    "SMAPI %s API Image_Device_Undedicate" %
                    userid,
                    "--operands",
                    '-v %s' % def_vdev))
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as err:
                    results = err.results
                    emsg = err.format_message()
                    if ((results['rc'] == 204) and
                        (results['rs'] == 8)):
                        LOG.warning("Virtual device %s does not exist on "
                                    "the active guest system", vdev)
                    else:
                        LOG.error("Failed to undedicate nic %s for %s on "
                                  "the active guest system, error: %s" %
                                  (vdev, userid, emsg))
                        self._undedicate_nic_active_exception(err, userid,
                                                              vdev)
                def_vdev = str(hex(int(def_vdev, 16) + 1))[2:]
        msg = ('Undedicate nic device %(vdev)s of guest %(vm)s successfully'
                % {'vdev': vdev, 'vm': userid})
        LOG.info(msg)

    def _request_with_error_ignored(self, rd):
        """Send smt request, log and ignore any errors."""
        try:
            return self._request(rd)
        except Exception as err:
            # log as warning and ignore namelist operation failures
            LOG.warning(six.text_type(err))

    def namelist_add(self, namelist, userid):
        rd = ''.join(("SMAPI %s API Name_List_Add " % namelist,
                      "--operands -n %s" % userid))
        self._request_with_error_ignored(rd)

    def namelist_remove(self, namelist, userid):
        rd = ''.join(("SMAPI %s API Name_List_Remove " % namelist,
                      "--operands -n %s" % userid))
        self._request_with_error_ignored(rd)

    def namelist_query(self, namelist):
        rd = "SMAPI %s API Name_List_Query" % namelist
        resp = self._request_with_error_ignored(rd)
        if resp is not None:
            return resp['response']
        else:
            return []

    def namelist_destroy(self, namelist):
        rd = "SMAPI %s API Name_List_Destroy" % namelist
        self._request_with_error_ignored(rd)

    def _get_defined_cpu_addrs(self, userid):
        user_direct = self.get_user_direct(userid)
        defined_addrs = []
        defined_addrs_long = []
        max_cpus = 0
        for ent in user_direct:
            if ent.startswith("CPU"):
                cpu_addr = ent.split()[1].strip().upper()
                defined_addrs.append(cpu_addr)
            if ent.startswith("COMMAND DEFINE CPU"):
                cpu_addr_long = ent.split()[3].strip().upper()
                defined_addrs_long.append(cpu_addr_long)
            if ent.startswith("MACHINE ESA"):
                # If defined the maximum number of virtual processors
                # the user can define, update max_cpus value.
                if len(ent.split()) > 2:
                    max_cpus = int(ent.split()[2].strip())

        # If empty max cpu number in MACHINE ESA, max_cpus should be set to default.
        # The default max_cpus value is either 1 or the number of CPU statements
        # for this user, whichever is greater.
        if max_cpus == 0:
            if len(defined_addrs) > 1 or len(defined_addrs_long) > 1:
                max_cpus = max(len(defined_addrs), len(defined_addrs_long))
            else:
                max_cpus = 1

        return (max_cpus, defined_addrs, defined_addrs_long)

    def _get_available_cpu_addrs(self, used_addrs, max_cpus):
        # Get available CPU addresses that are not defined in user entry
        used_set = set(used_addrs)
        available_addrs = set([hex(i)[2:].rjust(2, '0').upper()
                               for i in range(0, max_cpus)])
        available_addrs.difference_update(used_set)
        return list(available_addrs)

    def get_active_cpu_addrs(self, userid):
        # Get the active cpu addrs in two-digit hex string in upper case
        # Sample output for 'lscpu --parse=ADDRESS':
        # # The following is the parsable format, which can be fed to other
        # # programs. Each different item in every column has an unique ID
        # # starting from zero.
        # # Address
        # 0
        # 1
        active_addrs = []
        active_cpus = self.execute_cmd(userid, "lscpu --parse=ADDRESS")
        for c in active_cpus:
            # Skip the comment lines at beginning
            if c.startswith("# "):
                continue
            addr = hex(int(c.strip()))[2:].rjust(2, '0').upper()
            active_addrs.append(addr)
        return active_addrs

    def get_active_cpu_offline_addrs(self, userid):
        # Get the offline cpu addrs in two-digit hex string in upper case
        # Sample output for 'lscpu --parse=ADDRESS --offline':
        # # The following is the parsable format, which can be fed to other
        # # programs. Each different item in every column has an unique ID
        # # starting from zero.
        # # Address
        # 2
        offline_addrs = []
        offline_cpus = self.execute_cmd(userid, "lscpu --parse=ADDRESS --offline")
        for c in offline_cpus:
            # Skip the comment lines at beginning
            if c.startswith("# "):
                continue
            addr = hex(int(c.strip()))[2:].rjust(2, '0').upper()
            offline_addrs.append(addr)
        return offline_addrs

    def resize_cpus(self, userid, count):
        # Check defined cpus in user entry. If greater than requested, then
        # delete cpus. Otherwise, add new cpus.
        # Return value: for revert usage, a tuple of
        # action: The action taken for this resize, possible values:
        #         0: no action, 1: add cpu, 2: delete cpu
        # cpu_addrs: list of influenced cpu addrs
        action = 0
        updated_addrs = []
        defined_count = 0

        # Based on the following reasons, we need to delete all short format
        # 'CPU XX' and ensure long format 'COMMAND DEFINE CPU XX TYPE IFL'
        # number correct after resize.
        # 1, For vm not resized after deploying,
        # only having 'COMMAND DEFINE CPU XX TYPE IFL' format definition.
        # 2, For vm resized before, having both kinds definitions:
        # 'COMMAND DEFINE CPU XX TYPE IFL' and 'CPU XX', and their counts
        # may not be the same, as resize and counting before only
        # handles 'CPU XX'.

        (max_cpus, defined_addrs_short, defined_addrs_long) = \
            self._get_defined_cpu_addrs(userid)
        defined_count_short = len(defined_addrs_short)
        defined_count_long = len(defined_addrs_long)
        only_long_def = False
        if (defined_count_short == 0 and defined_count_long > 0):
            defined_count = defined_count_long
            only_long_def = True
        else:
            defined_count = defined_count_short

        # Check maximum cpu count defined
        if max_cpus == 0:
            LOG.error("Resize for guest '%s' cann't be done. The maximum "
                      "number of cpus is not defined in user directory." %
                      userid)
            raise exception.SDKConflictError(modID='guest', rs=3,
                                             userid=userid)
        # Check requested count is less than the maximum cpus
        if count > max_cpus:
            LOG.error("Resize for guest '%s' cann't be done. The "
                      "requested number of cpus: '%i' exceeds the maximum "
                      "number of cpus allowed: '%i'." %
                      (userid, count, max_cpus))
            raise exception.SDKConflictError(modID='guest', rs=4,
                                             userid=userid,
                                             req=count, max=max_cpus)
        # Check count and take action
        if defined_count == count:
            LOG.info("The number of current defined CPUs in user '%s' equals "
                     "to requested count: %i, no action for static resize"
                     "needed." % (userid, count))
            return (action, updated_addrs, max_cpus)
        elif defined_count < count:
            action = 1
            # add more CPUs
            available_addrs_long = self._get_available_cpu_addrs(
                defined_addrs_long, max_cpus)
            available_addrs_long.sort()

            to_delete_addrs_short = []
            to_delete_addrs_long = []
            to_add_addrs_long = []

            if only_long_def:
                # e.g. 5->7
                # short : no short, don't add.
                # long: add
                to_add_addrs_long = available_addrs_long[0:count - defined_count_long]
            else:
                # e.g. 5->3->4, 5->3->6, 5->7->9, or verify old vm which only
                # has short format 4->6

                # short, delete them all
                defined_addrs_short.sort()
                to_delete_addrs_short = defined_addrs_short

                # long, delete or add
                defined_addrs_long.sort()
                if defined_count_long < count:
                    # add. e.g.5->6, 5->9
                    to_add_addrs_long = available_addrs_long[0:count - defined_count_long]
                elif defined_count_long > count:
                    # Delete cpus in user directory, as for the vm resized before,
                    # need to delete long format in some situations, e.g. 5->3->4,
                    # as long format "COMMAND DEFINE CPU XX TYPE IFL" not handled
                    # during resize 5->3 before, although 3->4 is resized up,
                    # still need to delete 1 for long format. e.g. 5->4
                    to_delete_addrs_long = defined_addrs_long[-(defined_count_long - count):]

            # Delete the last few cpus in user directory in format "CPU XX"
            # and "COMMAND DEFINE CPU XX TYPE IFL".
            if len(to_delete_addrs_short) > 0 or len(to_delete_addrs_long) > 0:
                rd = ''.join(("SMAPI %s API Image_Definition_Delete_DM " % userid,
                              "--operands"))
                if len(to_delete_addrs_short) > 0:
                    for addr in to_delete_addrs_short:
                        rd += (" -k CPU=CPUADDR=%s" % addr)
                if len(to_delete_addrs_long) > 0:
                    for addr2 in to_delete_addrs_long:
                        rd += (" -k COMMAND_DEFINE_CPU=CPUADDR=%s" % addr2)
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as e:
                    msg = ("Delete CPUs in user directory for '%s' failed "
                           "with SMT error: %s"
                           % (userid, e.format_message()))
                    LOG.error(msg)
                    raise exception.SDKGuestOperationError(
                        rs=6, userid=userid, err=e.format_message())
                LOG.info("CPUs '%s' and '%s' deleted from user directory"
                         " for '%s' successfully"
                         % (str(to_delete_addrs_short),
                            str(to_delete_addrs_long), userid))

            # Define new cpus in user directory
            rd = ''.join(("SMAPI %s API Image_Definition_Update_DM " % userid,
                          "--operands"))
            need_action = False
            # May not need to send request at all, because existing long
            # format items may be enough. e.g. 5->3->5, resize down 5->3
            # before, as long format items were not handled before,
            # there are still 5 long format items, so we don't need to
            # add more even it is resize up to 5 now.
            if len(to_add_addrs_long) > 0:
                need_action = True
                for addr2 in to_add_addrs_long:
                    rd += (" -k COMMAND_DEFINE_CPU=\'CPUADDR=%s TYPE=IFL\'" % addr2)

            # Add resize support for share of CPU
            if CONF.zvm.user_default_share_unit > 0:
                need_action = True
                total = CONF.zvm.user_default_share_unit * count
                rd += (" -k SHARE=RELATIVE=%s" % total)

            if need_action:
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as e:
                    msg = ("Define new cpus in user directory for '%s' failed with"
                           " SMT error: %s" % (userid, e.format_message()))
                    LOG.error(msg)
                    raise exception.SDKGuestOperationError(rs=6, userid=userid,
                                                           err=e.format_message())
                LOG.info("New CPUs defined '%s' in user directory for '%s' "
                         "or add resize support for share of CPU successfully"
                         % (str(to_add_addrs_long), userid))
                return (action, to_add_addrs_long + to_delete_addrs_long, max_cpus)
            else:
                LOG.info("Existing CPUs defined in long format"
                         " 'COMMAND DEFINE CPU XX TYPE IFL' '%s'"
                         " in user directory for '%s' are enough"
                         " for this resize. Don't need to add more."
                         % (str(defined_addrs_long), userid))
                return (action, to_add_addrs_long + to_delete_addrs_long, max_cpus)
        else:
            action = 2
            # Delete CPUs
            available_addrs_short = self._get_available_cpu_addrs(
                defined_addrs_short, max_cpus)
            available_addrs_short.sort()
            available_addrs_long = self._get_available_cpu_addrs(
                defined_addrs_long, max_cpus)
            available_addrs_long.sort()

            to_delete_addrs_short = []
            to_delete_addrs_long = []
            to_add_addrs_long = []

            if only_long_def:
                # e.g. 5->3
                # short : no short, don't add.
                # long: delete
                defined_addrs_long.sort()
                to_delete_addrs_long = defined_addrs_long[-(defined_count_long - count):]
            else:
                # e.g. 5->3->2, 5->7->6, 5->7->3, or very old vm which only
                # has short format 4->2

                # short, delete all.
                defined_addrs_short.sort()
                to_delete_addrs_short = defined_addrs_short

                # long, delete or add
                defined_addrs_long.sort()
                if defined_count_long < count:
                    # Add cpus in user directory, for an existing vm
                    # resized to a larger size cpu before, e.g. 5->7->6, as long
                    # format "COMMAND DEFINE CPU XX TYPE IFL" not handled during
                    # resize 5->7 before, although 7->6 now, still need to add 1
                    # for long format. e.g.5->6,
                    to_add_addrs_long = available_addrs_long[0:count - defined_count_long]
                elif defined_count_long > count:
                    # delete. e.g. 5->2, 5->3
                    to_delete_addrs_long = defined_addrs_long[-(defined_count_long - count):]

            # Delete the last few cpus in user directory in format "CPU XX"
            # and "COMMAND DEFINE CPU XX TYPE IFL".
            if len(to_delete_addrs_short) > 0 or len(to_delete_addrs_long) > 0:
                rd = ''.join(("SMAPI %s API Image_Definition_Delete_DM " % userid,
                              "--operands"))
                if len(to_delete_addrs_short) > 0:
                    for addr in to_delete_addrs_short:
                        rd += (" -k CPU=CPUADDR=%s" % addr)
                if len(to_delete_addrs_long) > 0:
                    for addr2 in to_delete_addrs_long:
                        rd += (" -k COMMAND_DEFINE_CPU=CPUADDR=%s" % addr2)
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as e:
                    msg = ("Delete CPUs in user directory for '%s' failed "
                           "with SMT error: %s"
                           % (userid, e.format_message()))
                    LOG.error(msg)
                    raise exception.SDKGuestOperationError(
                        rs=6, userid=userid, err=e.format_message())
                LOG.info("CPUs '%s' and '%s' deleted from user directory"
                         " for '%s' successfully"
                         % (str(to_delete_addrs_short),
                            str(to_delete_addrs_long), userid))

            # Add new cpus in user directory
            rd = ''.join(("SMAPI %s API Image_Definition_Update_DM " % userid,
                          "--operands"))
            need_action = False

            if len(to_add_addrs_long) > 0:
                need_action = True
                for addr2 in to_add_addrs_long:
                    rd += (" -k COMMAND_DEFINE_CPU=\'CPUADDR=%s TYPE=IFL\'" % addr2)

            # Add resize support for share of CPU
            if CONF.zvm.user_default_share_unit > 0:
                need_action = True
                total = CONF.zvm.user_default_share_unit * count
                rd += (" -k SHARE=RELATIVE=%s" % total)

            if need_action:
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as e:
                    msg = ("Define new cpus in user directory for '%s' failed with"
                           " SMT error: %s" % (userid, e.format_message()))
                    LOG.error(msg)
                    raise exception.SDKGuestOperationError(rs=6, userid=userid,
                                                           err=e.format_message())
                LOG.info("New CPUs '%s' defined in user directory for '%s'"
                         " successfully or update share statement in user"
                         " directory successfully"
                         % (str(to_add_addrs_long), userid))

            return (action, to_add_addrs_long + to_delete_addrs_long, max_cpus)

    def live_resize_cpus(self, userid, count):
        # Get active cpu(online) count and compare with requested count
        active_addrs = self.get_active_cpu_addrs(userid)
        active_count = len(active_addrs)
        active_addrs.sort()

        # Get offline cpu count
        offline_addrs = self.get_active_cpu_offline_addrs(userid)

        # Backup user directory long format cpu definitions in
        # defined_addrs_long_bk for rollback
        (max_cpus, defined_addrs_short_bk, defined_addrs_long_bk) = \
            self._get_defined_cpu_addrs(userid)

        # If request count is smaller than the current count, then report
        # error and exit immediately.
        # if active_count > count:
        #     LOG.error("Failed to live resize cpus of guest: %(uid)s, "
        #               "current active cpu count: %(cur)i is greater than "
        #               "the requested count: %(req)i." %
        #               {'uid': userid, 'cur': active_count,
        #                'req': count})
        #     raise exception.SDKConflictError(modID='guest', rs=2,
        #                                      userid=userid,
        #                                      active=active_count,
        #                                      req=count)

        # Static resize CPUs. (add or delete CPUs from user directory)
        (action, updated_addrs, max_cpus) = self.resize_cpus(userid, count)
        if active_count == count:
            # active count equals to requested
            LOG.info("Current active cpu count of guest: '%s' equals to the "
                     "requested count: '%i', no more actions needed for "
                     "live resize." % (userid, count))
            LOG.info("Live resize cpus for guest: '%s' finished successfully."
                     % userid)
            return
        else:
            if active_count < count:
                # Add live cpu
                # Get the number of cpus to add to active and check address
                active_free = self._get_available_cpu_addrs(active_addrs,
                                                            max_cpus)
                active_free.sort()
                active_new = active_free[0:count - active_count]

                # For addresses disabled, just enable it,
                # otherwise need to define and trigger cpu scan.
                to_enable_addrs = [a for a in active_new if a in offline_addrs]
                to_define_addrs = list(set(active_new) - set(offline_addrs))
                if not to_enable_addrs:
                    # Let's call 'chcpu -e' explictily because 'chcpu -r'
                    # can't bring the offline cpus online in some Ubuntu &
                    # SLES distros. Use the safest way to do it.
                    to_enable_addrs = to_define_addrs
                to_enable_addrs.sort()
                to_define_addrs.sort()

                # Do live resize.
                # Including 1, define new cpus; 2, enable cups;

                # 1, Define new cpus
                if to_define_addrs:
                    cmd_str = "vmcp def cpu " + ' '.join(to_define_addrs)
                    try:
                        self.execute_cmd(userid, cmd_str)
                    except exception.SDKSMTRequestFailed as err1:
                        # rollback and return.
                        # compare updated_addrs with defined_addrs_long_bk.
                        msg1 = ("Define cpu of guest: '%s' to active failed with "
                                "error: %s." % (userid, err1.format_message()))
                        # Start to do rollback
                        if action == 0:
                            LOG.error(msg1)
                        else:
                            LOG.error(msg1 + (" Will revert the user directory "
                                              "change."))
                            self.roll_back_user_directory_definitions(
                                userid, updated_addrs, defined_addrs_long_bk,
                                active_count)
                        # Finally raise the exception
                        raise exception.SDKGuestOperationError(
                            rs=7, userid=userid, err=err1.format_message())
                    # Activate successfully, rescan in Linux layer to hot-plug new cpus
                    LOG.info("Added new CPUs to active configuration of guest '%s'" %
                             userid)
                    try:
                        self.execute_cmd(userid, "chcpu -r")
                    except exception.SDKSMTRequestFailed as err:
                        msg = err.format_message()
                        LOG.error("Rescan cpus to hot-plug new defined cpus for guest: "
                                  "'%s' failed with error: %s. No rollback is done and you"
                                  "may need to check the status and restart the guest to "
                                  "make the defined cpus online." % (userid, msg))
                        raise exception.SDKGuestOperationError(rs=8, userid=userid,
                                                               err=msg)

                # 2, enable cups
                if to_enable_addrs:
                    cmd_str = "chcpu -e " + ','.join(to_enable_addrs)
                    try:
                        self.execute_cmd(userid, cmd_str)
                    except exception.SDKSMTRequestFailed as err1:
                        # rollback and return
                        msg1 = ("Enable cpu of guest: '%s' to active failed with . "
                                "error: %s." % (userid, err1.format_message()))
                        # Start to do rollback
                        if action == 0:
                            LOG.error(msg1)
                        else:
                            self.roll_back_user_directory_definitions(
                                userid, updated_addrs, defined_addrs_long_bk,
                                active_count)
                        # Finally raise the exception
                        raise exception.SDKGuestOperationError(
                            rs=7, userid=userid, err=err1.format_message())
                    # Enable cups successfully
                    LOG.info("Enable CPUs to online guest '%s'" % userid)

            elif active_count > count:
                # Disable online cpus, as not find a way to undefine or delete
                # a configured cpu. A disabled cpu can only be enabled later,
                # and not be defined again.
                to_disable_addrs = active_addrs[-(active_count - count):]
                cmd_str = "chcpu -d " + ','.join(to_disable_addrs)
                try:
                    self.execute_cmd(userid, cmd_str)
                except exception.SDKSMTRequestFailed as err1:
                    # rollback and return
                    msg1 = ("Disable cpu of guest: '%s' to offline failed "
                            "with error: %s." % (userid,
                                                 err1.format_message()))
                    if action == 0:
                        LOG.error(msg1)
                    else:
                        # Start to do rollback
                        self.roll_back_user_directory_definitions(
                            userid, updated_addrs, defined_addrs_long_bk,
                            active_count)
                    # Finally raise the exception
                    raise exception.SDKGuestOperationError(
                        rs=7, userid=userid, err=err1.format_message())
                # Disable cups successfully
                LOG.info("Disable CPUs to offline guest '%s'" % userid)

    def roll_back_user_directory_definitions(self, userid, updated_addrs,
                                             defined_addrs_long_bk,
                                             active_count):
        # Only need to roll back cpu definition in long
        # format: "COMMAND DEFINE CPU XX TYPE IFL".
        # All the impacted cpus are either been added
        # or deleted.
        to_add_rollback_addrs = [a for a in updated_addrs if a in defined_addrs_long_bk]
        to_del_rollback_addrs = list(set(updated_addrs) - set(to_add_rollback_addrs))
        to_add_rollback_addrs.sort()
        to_del_rollback_addrs.sort()
        if to_add_rollback_addrs:
            rd = ''.join(("SMAPI %s API Image_Definition_Update_DM " % userid,
                          "--operands"))
            for addr in to_add_rollback_addrs:
                rd += (" -k COMMAND_DEFINE_CPU=\'CPUADDR=%s TYPE=IFL\'" % addr)
        else:
            rd = ''.join(("SMAPI %s API Image_Definition_Delete_DM " % userid,
                          "--operands"))
            for addr in to_del_rollback_addrs:
                rd += (" -k COMMAND_DEFINE_CPU=CPUADDR=%s" % addr)

        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err2:
            msg = ("Failed to revert user directory change for '"
                   "%s', SMT error: %s" % (userid,
                                           err2.format_message()))
            LOG.error(msg)
        else:
            # revert change for share statement
            if CONF.zvm.user_default_share_unit > 0:
                old = CONF.zvm.user_default_share_unit * active_count
                rd = ''.join(("SMAPI %s API Image_Definition_Update_DM " % userid,
                              "--operands -k SHARE=RELATIVE=%s" % old))
                try:
                    self._request(rd)
                except exception.SDKSMTRequestFailed as e:
                    msg = ("Failed to revert user directory change of share for '"
                           "%s', SMT error: %s" % (userid, e.format_message()))
                    LOG.error(msg)
                else:
                    LOG.info("Revert user directory change for '%s' "
                             "successfully." % userid)
            else:
                LOG.info("Revert user directory change for '%s' "
                         "successfully." % userid)

    def _get_defined_memory(self, userid):
        user_direct = self.get_user_direct(userid)
        defined_mem = max_mem = -1
        for ent in user_direct:
            # u'USER userid password storage max privclass'
            if ent.startswith("USER "):
                fields = ent.split(' ')
                if len(fields) < 6:
                    # This case should not exist if the target user
                    # is created by zcc and not updated manually by user
                    break
                defined_mem = int(zvmutils.convert_to_mb(fields[3]))
                max_mem = int(zvmutils.convert_to_mb(fields[4]))
        return (defined_mem, max_mem, user_direct)

    def _replace_user_direct(self, userid, user_entry):
        # user_entry can be a list or a string
        entry_str = ""
        if isinstance(user_entry, list):
            for ent in user_entry:
                if ent == "":
                    # skip empty line
                    continue
                else:
                    entry_str += (ent + '\n')
        else:
            entry_str = user_entry
        tmp_folder = tempfile.mkdtemp()
        tmp_user_direct = os.path.join(tmp_folder, userid)
        with open(tmp_user_direct, 'w') as f:
            f.write(entry_str)
        rd = ''.join(("SMAPI %s API Image_Replace_DM " % userid,
                      "--operands ",
                      "-f %s" % tmp_user_direct))
        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as err1:
            msg = ("Replace definition of guest '%s' failed with "
                   "SMT error: %s." % (userid, err1.format_message()))
            LOG.error(msg)
            LOG.debug("Unlocking the user directory.")
            rd = ("SMAPI %s API Image_Unlock_DM " % userid)
            try:
                self._request(rd)
            except exception.SDKSMTRequestFailed as err2:
                # ignore 'not locked' error
                if ((err2.results['rc'] == 400) and (
                    err2.results['rs'] == 24)):
                    LOG.debug("Guest '%s' unlocked successfully." % userid)
                    pass
                else:
                    # just print error and ignore this unlock error
                    msg = ("Unlock definition of guest '%s' failed "
                           "with SMT error: %s" %
                           (userid, err2.format_message()))
                    LOG.error(msg)
            else:
                LOG.debug("Guest '%s' unlocked successfully." % userid)
            # at the end, raise the replace error for upper layer to handle
            raise err1
        finally:
            self._pathutils.clean_temp_folder(tmp_folder)

    def _lock_user_direct(self, userid):
        rd = ("SMAPI %s API Image_Lock_DM " % userid)
        try:
            self._request(rd)
        except exception.SDKSMTRequestFailed as e:
            # ignore the "already locked" error
            if ((e.results['rc'] == 400) and (e.results['rs'] == 12)):
                LOG.debug("Image is already unlocked.")
            else:
                msg = ("Lock definition of guest '%s' failed with"
                       " SMT error: %s" % (userid, e.format_message()))
                LOG.error(msg)
                raise e

    def resize_memory(self, userid, memory):
        # Check defined storage in user entry.
        # Update STORAGE and RESERVED accordingly.
        size = int(zvmutils.convert_to_mb(memory))
        (defined_mem, max_mem, user_direct) = \
            self._get_defined_memory(userid)
        # Check max memory is properly defined
        if defined_mem == -1 or max_mem == -1:
            LOG.error("Memory resize for guest '%s' cann't be done."
                      "Failed to get the defined/max memory size "
                      "from user directory." % userid)
            raise exception.SDKConflictError(modID='guest', rs=19,
                                             userid=userid)
        action = 0
        # Make sure requested size is less than the maximum memory size
        if size > max_mem:
            LOG.error("Memory resize for guest '%s' cann't be done. The "
                      "requested memory size: '%im' exceeds the maximum "
                      "size allowed: '%im'." %
                      (userid, size, max_mem))
            raise exception.SDKConflictError(modID='guest', rs=20,
                                             userid=userid,
                                             req=size, max=max_mem)
        # check if already satisfy request
        if defined_mem == size:
            LOG.info("The current defined memory size in user '%s' equals "
                     "to requested size: %im, no action for memory resize "
                     "needed." % (userid, size))
            return (action, defined_mem, max_mem, user_direct)
        else:
            # set action to 1 to represent that revert need to be done when
            # live resize failed.
            action = 1
            # prepare the new user entry content
            entry_str = ""
            for ent in user_direct:
                if ent == '':
                    # Avoid adding an empty line in the entry file
                    # otherwise Image_Replace_DM would return syntax error.
                    continue
                new_ent = ""
                if ent.startswith("USER "):
                    fields = ent.split(' ')
                    for i in range(len(fields)):
                        # update fields[3] to new defined size
                        if i != 3:
                            new_ent += (fields[i] + ' ')
                        else:
                            new_ent += (str(size) + 'M ')
                    # remove the last space
                    new_ent = new_ent.strip()
                elif re.match(const.RESERVED_STOR_PATTERN, ent):
                    new_ent = ("COMMAND DEF STOR INITIAL STANDBY REMAINDER")
                else:
                    new_ent = ent
                # append this new entry
                entry_str += (new_ent + '\n')

            # Lock and replace user definition with the new_entry content
            try:
                self._lock_user_direct(userid)
            except exception.SDKSMTRequestFailed as e:
                raise exception.SDKGuestOperationError(rs=9, userid=userid,
                                                       err=e.format_message())
            LOG.debug("User directory Locked successfully for guest '%s' " %
                     userid)

            # Replace user directory
            try:
                self._replace_user_direct(userid, entry_str)
            except exception.SDKSMTRequestFailed as e:
                raise exception.SDKGuestOperationError(rs=10,
                                                       userid=userid,
                                                       err=e.format_message())
            # Finally return useful info
            return (action, defined_mem, max_mem, user_direct)

    def _revert_user_direct(self, userid, user_entry):
        # user_entry can be a list or a string
        try:
            self._lock_user_direct(userid)
        except exception.SDKSMTRequestFailed:
            # print revert error and return
            msg = ("Failed to revert user direct of guest '%s'." % userid)
            LOG.error(msg)
            return
        LOG.debug("User directory Locked successfully for guest '%s'." %
                 userid)

        # Replace user directory
        try:
            self._replace_user_direct(userid, user_entry)
        except exception.SDKSMTRequestFailed:
            msg = ("Failed to revert user direct of guest '%s'." % userid)
            LOG.error(msg)
            return
        LOG.debug("User directory reverted successfully for guest '%s'." %
                 userid)

    def _get_active_memory(self, userid):
        # Return an integer value representing the active memory size in mb
        output = self.execute_cmd(userid, "lsmem -b")
        active_mem = 0
        for e in output:
            # cmd output contains line starts with "Total online memory",
            # its format is like:
            # Total online memory:        17179869184
            if e.startswith("Total online memory"):
                try:
                    # sample mem_info_str: 17179869184
                    mem_info_str = e.split(':')[1].replace(' ', '').upper()
                    # mem_info is in Bytes, convert to MB
                    if mem_info_str.endswith('B'):
                        mem_info = mem_info_str[:-1]
                    else:
                        mem_info = mem_info_str
                    # get from lsmem -b output, must be aligned to memory block size(256M)
                    active_mem = int(zvmutils.convert_to_mb(mem_info))
                except (IndexError, ValueError, KeyError, TypeError) as e:
                    errmsg = ("Failed to get active storage size for guest: %s"
                              % userid)
                    LOG.error(errmsg + " with error: " + six.text_type(e))
                    raise exception.SDKInternalError(msg=errmsg)
                break
        return active_mem

    def live_resize_memory(self, userid, memory):
        # Get active memory size and compare with requested size
        # If request size is smaller than the current size, then report
        # error and exit immediately.
        size = int(zvmutils.convert_to_mb(memory))
        active_size = self._get_active_memory(userid)
        if active_size > size:
            LOG.error("Failed to live resize memory of guest: %(uid)s, "
                      "current active memory size: %(cur)im is greater than "
                      "the requested size: %(req)im." %
                      {'uid': userid, 'cur': active_size,
                       'req': size})
            raise exception.SDKConflictError(modID='guest', rs=18,
                                             userid=userid,
                                             active=active_size,
                                             req=size)
        # As long as the input size is aligned to 256M, the increase_size is aligned to 256M
        increase_size = size - active_size

        # Static resize memory. (increase/decrease memory from user directory)
        (action, defined_mem, max_mem,
         user_direct) = self.resize_memory(userid, memory)

        # Compare active size and requested size, then update accordingly
        if active_size == size:
            # online memory already satisfied
            LOG.info("Current active memory size of guest: '%s' equals to the "
                     "requested size: '%iM', no more actions needed for "
                     "live resize." % (userid, size))
            LOG.info("Live resize memory for guest: '%s' finished "
                     "successfully." % userid)
            return
        else:
            # Do live resize. update memory size
            # If the user direct include DEF STOR RESERVED statement,
            # then need define standby storage
            # Step1: Define new standby storage
            if any(re.match(const.RESERVED_STOR_PATTERN, ent) for ent in user_direct):
                # 'DEF STOR RESERVED' statement in Legacy user direct is replace to
                # 'COMMAND DEFINE STORAGE INITIAL STANDBY REMAINDER', so here def all
                # reserved memory to standby
                reserved_mem_size = 0
                stor_info = self.execute_cmd(userid, 'vmcp q storage')
                # stor_info example:
                # ['STORAGE = 40G MAX = 100G INC = 128M STANDBY = 0  RESERVED = 60G']
                if stor_info and len(stor_info) >= 1:
                    reserved_mem = stor_info[0].split('RESERVED =')[1].split()[0]
                    reserved_mem_size = int(zvmutils.convert_to_mb(reserved_mem))
                if reserved_mem_size > 0:
                    cmd_str = ("vmcp def storage standby %sM" % reserved_mem_size)
                else:
                    cmd_str = ("vmcp def storage standby %sM" % increase_size)
                try:
                    self.execute_cmd(userid, cmd_str)
                except exception.SDKSMTRequestFailed as e:
                    # rollback and return
                    msg = ("Define standby memory of guest: '%s' failed with "
                           "error: %s." % (userid, e.format_message()))
                    LOG.error(msg)
                    # Start to do rollback
                    if action == 1:
                        LOG.debug("Start to revert user definition of guest '%s'."
                                  % userid)
                        self._revert_user_direct(userid, user_direct)
                    # Finally, raise the error and exit
                    raise exception.SDKGuestOperationError(rs=11,
                                                           userid=userid,
                                                           err=e.format_message())
            # Step 2: Online new memory
            cmd_str = ("chmem -e %sM" % increase_size)
            try:
                self.execute_cmd(userid, cmd_str)
            except exception.SDKSMTRequestFailed as err1:
                # rollback and return
                msg1 = ("Online memory of guest: '%s' failed with "
                       "error: %s." % (userid, err1.format_message()))
                LOG.error(msg1)
                # Start to do rollback
                LOG.info("Start to do revert.")
                if any(re.match(const.RESERVED_STOR_PATTERN, ent) for ent in user_direct):
                    LOG.debug("Reverting the standby memory.")
                    try:
                        self.execute_cmd(userid, "vmcp def storage standby 0M")
                    except exception.SDKSMTRequestFailed as err2:
                        # print revert error info and continue
                        msg2 = ("Revert standby memory of guest: '%s' failed with "
                               "error: %s." % (userid, err2.format_message()))
                        LOG.error(msg2)
                # Continue to do the user directory change.
                if action == 1:
                    LOG.debug("Reverting the user directory change of guest "
                              "'%s'." % userid)
                    self._revert_user_direct(userid, user_direct)
                # Finally raise the exception
                raise exception.SDKGuestOperationError(
                    rs=17, userid=userid, err=err1.format_message())

        LOG.info("Live resize memory for guest: '%s' finished successfully."
                 % userid)

    def is_rhcos(self, os_version):
        return os_version.lower().startswith('rhcos')

    def _get_wwpn_lun(self, userid):
        user_direct = self.get_user_direct(userid)
        wwpn = None
        lun = None
        for ent in user_direct:
            if ent.upper().startswith("LOADDEV PORT"):
                wwpn = ent.split()[2].strip()
            elif ent.upper().startswith("LOADDEV LUN"):
                lun = ent.split()[2].strip()
        return (wwpn, lun)

    def host_get_ssi_info(self):
        msg = ('Start SSI_Query')
        LOG.info(msg)

        rd = 'SMAPI HYPERVISOR API SSI_Query'
        try:
            results = self._request(rd)
        except exception.SDKSMTRequestFailed as err:
            if err.results['rc'] == 4 and err.results['rs'] == 3008:
                # System is not a member of an SSI cluster
                LOG.debug("Host is not a member of an SSI cluster.")
                return []
            msg = "SMT error: %s" % err.format_message()
            raise exception.SDKSMTRequestFailed(err.results, msg)
            LOG.error("Failed to query SSI information.")
        if results['rc'] == 0 and results['rs'] == 0 \
            and results.get('response'):
            return results.get('response')
        return []

    def guest_get_kernel_info(self, userid):
        # Get the kernel info of 'uname -srm'
        try:
            kernel_info = self.execute_cmd(userid, "uname -srm")
            return kernel_info[0]
        except exception.SDKSMTRequestFailed as err:
            msg = err.format_message()
            LOG.error("Get kernel info from the guest %s failed: %s"
                      % (userid, msg))
        return ''


class FilesystemBackend(object):
    @classmethod
    def image_import(cls, image_name, url, target, **kwargs):
        """Import image from remote host to local image repository using scp.
        If remote_host not specified, it means the source file exist in local
        file system, just copy the image to image repository
        """
        source = urlparse.urlparse(url).path
        if kwargs['remote_host']:
            if '@' in kwargs['remote_host']:
                source_path = ':'.join([kwargs['remote_host'], source])
                command = ' '.join(['/usr/bin/scp',
                                    "-P", CONF.zvm.remotehost_sshd_port,
                                    "-o StrictHostKeyChecking=no",
                                    '-r ', source_path, target])
                (rc, output) = zvmutils.execute(command)
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
            command = ' '.join(['/usr/bin/scp',
                                "-P", CONF.zvm.remotehost_sshd_port,
                                "-o StrictHostKeyChecking=no",
                                '-r ', source_path, target_path])
            (rc, output) = zvmutils.execute(command)
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
    def image_import(cls, image_name, url, target, **kwargs):
        import_image = MultiThreadDownloader(image_name, url,
                                             target)
        import_image.run()


class MultiThreadDownloader(threading.Thread):
    def __init__(self, image_name, url, target):
        super(MultiThreadDownloader, self).__init__()
        self.url = url
        # Set thread number
        self.threadnum = 8
        r = requests.head(self.url)
        # Get the size of the download resource
        self.totalsize = int(r.headers['Content-Length'])
        self.target = target

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
