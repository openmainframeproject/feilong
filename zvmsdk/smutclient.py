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
            raise exception.ZVMSDKInternalError(msg=err, modID='smut')

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
                raise exception.ZVMSDKInternalError(msg=msg,
                                                    modID='smut',
                                                    results=results)
            else:
                msg = ("SMUT request failed. RequestData: '%s', Results: '%s'"
                       % (requestData, str(results)))
                raise exception.ZVMClientRequestFailed(results, msg)
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
            if ((int(vdev, 16) >= int(used_vdev, 16)) and
                (int(vdev, 16) <= int(used_vdev, 16) + 2)):
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
        """"Power on VM."""
        requestData = "PowerVM " + userid + " on"
        with zvmutils.log_and_reraise_smut_request_failed():
            self._request(requestData)

    def guest_stop(self, userid):
        """"Power off VM."""
        requestData = "PowerVM " + userid + " off"
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
            rd += (' --filesystem %s' % fmt)

        action = "add mdisk to userid '%s'" % userid
        with zvmutils.log_and_reraise_smut_request_failed(action):
            self._request(rd)

    def get_vm_list(self):
        """Get the list of guests that are created by SDK
        return userid list"""
        guests = self._GuestDbOperator.get_guest_list()
        # guests is a list of tuple (uuid, userid, metadata, comments)
        userid_list = []
        for g in guests:
            userid_list.append(g[1])
        return userid_list

    def _remove_mdisk(self, userid, vdev):
        rd = ' '.join(('changevm', userid, 'removedisk', vdev))
        self._request(rd)

    def guest_authorize_iucv_client(self, userid, client=None):
        """Punch a script to authorized the client on guest vm"""
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
        except Exception as err:
            raise exception.ZVMSMUTAuthorizeIUCVClientFailed(
                client=client, vm=userid, msg=err)
        finally:
            self._pathutils.clean_temp_folder(iucv_path)

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        """ Deploy image and punch config driver to target """
        # Get image location (TODO: update this image location)
        image_file = self._get_image_path_by_name(image_name)
        # Unpack image file to root disk
        vdev = vdev or CONF.zvm.user_root_vdev
        cmd = ['/opt/zthin/bin/unpackdiskimage', userid, vdev, image_file]
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
        except exception.ZVMClientRequestFailed as err:
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
        except exception.ZVMClientRequestFailed as err:
            LOG.error("Failed to revoke user %s from vswitch %s, error: %s"
                      % (userid, vswitch_name, err.format_message()))
            raise

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        if not isinstance(uid_list, list):
            uid_list = [uid_list]

        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Image_Performance_Query" % smut_userid,
            "--operands",
            '-T "%s"' % (' '.join(uid_list)),
            "-c %d" % len(uid_list)))
        results = self._request(rd)

        ipq_kws = {
            'userid': "Guest name:",
            'guest_cpus': "Guest CPUs:",
            'used_cpu_time': "Used CPU time:",
            'elapsed_cpu_time': "Elapsed time:",
            'min_cpu_count': "Minimum CPU count:",
            'max_cpu_limit': "Max CPU limit:",
            'samples_cpu_in_use': "Samples CPU in use:",
            'samples_cpu_delay': ",Samples CPU delay:",
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
            except exception.ZVMSDKInternalError as err:
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
        results = self._request(rd)
        return self._parse_vswitch_inspect_data(results['response'])

    def get_host_info(self):
        results = self._request("getHost general")
        host_info = zvmutils.translate_response_to_dict(
            '\n'.join(results['response']), const.RINV_HOST_KEYWORDS)

        return host_info

    def get_diskpool_info(self, pool):
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
        except exception.ZVMClientRequestFailed as err:
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
        except exception.ZVMClientRequestFailed as err:
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
        except exception.ZVMClientRequestFailed as err:
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
        except exception.ZVMClientRequestFailed as err:
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
        except exception.ZVMClientRequestFailed as err:
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
                   mac_addr=None, ip_addr=None, active=False):
        ports_info = self._NetDbOperator.switch_select_table()
        vdev_info = []
        for p in ports_info:
            if p[0] == userid:
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
                    raise exception.ZVMInvalidInputFormat(msg=errmsg)
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
        except exception.ZVMClientRequestFailed as err:
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
            except (exception.ZVMClientRequestFailed,
                    exception.ZVMSDKInternalError) as err1:
                msg1 = err1.format_message()
                persist_OK = True
                requestData = ' '.join((
                    'SMAPI %s API Virtual_Network_Adapter_Delete_DM' % userid,
                    "--operands",
                    '-v %s' % vdev))
                try:
                    self._request(requestData)
                except (exception.ZVMClientRequestFailed,
                        exception.ZVMSDKInternalError) as err2:
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

        self._NetDbOperator.switch_add_record_for_nic(userid, vdev,
                                                      port=nic_id)

    def get_user_direct(self, userid):
        results = self._request("getvm %s directory" % userid)
        return results.get('response', [])

    def delete_nic(self, userid, vdev, active=False):
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Adapter_Delete_DM" %
            userid,
            "--operands",
            '-v %s' % vdev))
        try:
            self._request(rd)
        except exception.ZVMClientRequestFailed as err:
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
            except exception.ZVMClientRequestFailed as err:
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
        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Connect_Vswitch_DM",
            "--operands",
            "-v %s" % vdev,
            "-n %s" % vswitch_name))

        try:
            self._request(requestData)
        except exception.ZVMClientRequestFailed as err:
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
            except (exception.ZVMClientRequestFailed,
                    exception.ZVMSDKInternalError) as err1:
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
                    except (exception.ZVMClientRequestFailed,
                            exception.ZVMSDKInternalError) as err2:
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
        self._NetDbOperator.switch_updat_record_with_switch(userid, vdev,
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
        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Disconnect_DM",
            "--operands",
            "-v %s" % vdev))

        try:
            self._request(requestData)
        except (exception.ZVMClientRequestFailed,
                exception.ZVMSDKInternalError) as err:
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
        self._NetDbOperator.switch_updat_record_with_switch(userid, vdev,
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
            except (exception.ZVMClientRequestFailed,
                    exception.ZVMSDKInternalError) as err:
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
        except exception.ZVMClientRequestFailed as err:
            if err.results['rc'] == 400 and err.results['rs'] == 4:
                # guest vm definition not found
                LOG.debug("The guest vm %s not found" % userid)
                return
            else:
                raise err

    def delete_vm(self, userid):
        self.delete_userid(userid)
        # cleanup db record from network table
        try:
            self._NetDbOperator.switch_delete_record_for_userid(userid)
        except exception.SDKNetworkOperationError as err:
            LOG.error("Failed to delete network record for user %s, "
                      "error: %s" %
                      (userid, err.format_message()))

        # TODO: cleanup db record from volume table
        pass

        # cleanup db record from guest table
        self._GuestDbOperator.delete_guest_by_userid(userid)

    def execute_cmd(self, userid, cmdStr):
        """"cmdVM."""
        requestData = ' '.join(('cmdVM', userid, 'CMD', cmdStr))
        results = self._request(requestData)
        with zvmutils.expect_invalid_resp_data(results):
            ret = results['response']
        return ret

    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import the image specified in url to SDK image repository, and
        create a record in image db, the imported images are located in
        image_repository/prov_method/os_version/, for example,
        /opt/sdk/images/netboot/rhel7.2/90685d2b-167b.img"""
        image_info = self._ImageDbOperator.image_query_record(image_name)
        # Ensure the specified image is not exist in image DB
        if image_info:
            LOG.info("The image %s has already exist in image repository"
                     % image_name)
            return

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
        except exception.ZVMClientRequestFailed as err:
            LOG.error("Failed to punch file to userid '%s',"
                      "error: %s" % (userid, err.format_message()))
            raise
        finally:
            os.remove(fn)

    def get_guest_connection_status(self, userid):
        '''Get guest vm connection status.'''
        # TODO: implement it
        pass

    def process_additional_minidisks(self, userid, disk_info):
        '''Generate and punch the scripts used to process additional disk into
        target vm's reader.
        '''
        # TODO: implement it
        pass


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
                       " with reason %s" % err)
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=12,
                                                    err=err.format_message())

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
                msg = ("Export image to local file system failed: %s" %
                       err.format_message())
                raise exception.SDKImageOperationError(rs=22,
                                                err=err.format_message())


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
                msg = ("Download image from http server failed: %s" % err)
                LOG.error(msg)
                raise exception.SDKImageOperationError(rs=9,
                                                    err=err.format_message())
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
