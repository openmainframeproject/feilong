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
import re
import shutil
import tempfile


from smutLayer import smut

from zvmsdk import client
from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import database
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG
_LOCK = threading.Lock()
CHUNKSIZE = 4096


class SMUTClient(client.ZVMClient):

    def __init__(self):
        super(SMUTClient, self).__init__()
        self._smut = smut.SMUT()
        self._NetDbOperator = database.NetworkDbOperator()
        self._GuestDbOperator = database.GuestDbOperator()
        self._ImageDbOperator = database.ImageDbOperator()

    def _request(self, requestData):
        try:
            results = self._smut.request(requestData)
        except Exception as err:
            LOG.error('SMUT internal parse encounter error')
            raise exception.ZVMClientInternalError(msg=err)

        if results['overallRC'] != 0:
            raise exception.ZVMClientRequestFailed(results=results)
        return results

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % userid)
        requestData = "PowerVM " + userid + " status"
        results = self._request(requestData)
        with zvmutils.expect_invalid_resp_data(results):
            status = results['response'][0].partition(': ')[2]
        return status

    def guest_start(self, userid):
        """"Power on VM."""
        requestData = "PowerVM " + userid + " on"
        self._request(requestData)

    def guest_stop(self, userid):
        """"Power off VM."""
        requestData = "PowerVM " + userid + " off"
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

        self._request(rd)

        # Add the guest to db immediately after user created
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
        image_file = "/var/lib/zvmsdk/images/" + image_name
        # Unpack image file to root disk
        vdev = vdev or CONF.zvm.user_root_vdev
        cmd = ['/opt/zthin/bin/unpackdiskimage', userid, vdev, image_file]
        (rc, output) = zvmutils.execute(cmd)
        if rc != 0:
            err_msg = ("unpackdiskimage failed with return code: %d." % rc)
            output_lines = output.split('\n')
            for line in output_lines:
                if line.__contains__("ERROR:"):
                    err_msg += ("\\n" + line.strip())
            LOG.error(err_msg)
            raise exception.ZVMGuestDeployFailed(userid=userid, msg=err_msg)

        # Purge guest reader to clean dirty data
        rd = ("changevm %s purgerdr" % userid)
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMGuestDeployFailed, userid=userid):
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
                (rc, output) = zvmutils.execute(cmd)
                if rc != 0:
                    err_msg = ("copy config drive to local failed with"
                               "return code: %d." % rc)
                    LOG.error(err_msg)
                    raise exception.ZVMGuestDeployFailed(userid=userid,
                                                         msg=err_msg)

                # Punch config drive to guest userid
                rd = ("changevm %(uid)s punchfile %(file)s --class X" %
                      {'uid': userid, 'file': local_trans})
                with zvmutils.expect_request_failed_and_reraise(
                    exception.ZVMGuestDeployFailed, userid=userid):
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

        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(requestData)

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        """Revoke user for vswitch."""
        smut_userid = zvmutils.get_smut_userid()
        requestData = ' '.join((
            'SMAPI %s API Virtual_Network_Vswitch_Set_Extended' % smut_userid,
            "--operands",
            "-k switch_name=%s" % vswitch_name,
            "-k revoke_userid=%s" % userid,
            "-k persist=YES"))

        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(requestData)

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
        with zvmutils.expect_invalid_resp_data():
            rpi_list = ('\n'.join(results['response'])).split("\n\n")
            for rpi in rpi_list:
                try:
                    pi = zvmutils.translate_response_to_dict(rpi, ipq_kws)
                except exception.ZVMInvalidResponseDataError as err:
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
        switch_info = self._NetDbOperator.switch_select_record_for_node(vm_id)
        with zvmutils.expect_invalid_resp_data():
            switch_dict = {}
            for item in switch_info:
                switch_dict[item[0]] = item[1]

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

    @zvmutils.wrap_invalid_resp_data_error
    def get_vswitch_list(self):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Query" % smut_userid,
            "--operands",
            "-s \'*\'"))
        with zvmutils.expect_request_failed_and_reraise(
                exception.ZVMNetworkError):
            try:
                result = self._request(rd)
            except exception.ZVMClientRequestFailed as err:
                emsg = err.format_message()
                if ((err.results['rc'] == 212) and (err.results['rs'] == 40)):
                    LOG.warning("No Virtual switch in the host")
                    return []
                else:
                    raise exception.ZVMNetworkError(
                            msg=("Failed to query vswitch list, %s") % emsg)

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
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(rd)

    @zvmutils.wrap_invalid_resp_data_error
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
            if ((native_vid is not None) and
                ((native_vid < 1) or (native_vid > 4094))):
                raise exception.ZVMInvalidInput(
                    msg=("Failed to create vswitch %s: %s") % (name,
                         'valid native VLAN id should be 1-4094 or None'))

            rd = ' '.join((rd,
                           "-k port_type=%s" % port_type,
                           "-k gvrp_value=%s" % gvrp,
                           "-k native_vlanid=%s" % native_vid))

        if router is not None:
            rd += " -k routing_value=%s" % router
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(rd)

    @zvmutils.wrap_invalid_resp_data_error
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
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(rd)

    @zvmutils.wrap_invalid_resp_data_error
    def delete_vswitch(self, switch_name, persist=True):
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Delete_Extended" %
            smut_userid,
            "--operands",
            "-k switch_name=%s" % switch_name,
            "-k persist=%s" % (persist and 'YES' or 'NO')))
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            try:
                self._request(rd)
            except exception.ZVMClientRequestFailed as err:
                results = err.results
                emsg = err.format_message()
                if ((results['rc'] == 212) and
                    (results['rs'] == 40)):
                    LOG.warning("Vswitch %s does not exist", switch_name)
                    return
                else:
                    raise exception.ZVMNetworkError(
                        msg=("Failed to delete vswitch %s: %s") %
                            (switch_name, emsg))

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
                    raise exception.ZVMInvalidInput(
                        msg=("The specified virtual device number %s "
                             "has already been used" % vdev))
        if len(nic_vdev) > 4:
            raise exception.ZVMNetworkError(
                        msg=("Virtual device number %s is not valid" %
                             nic_vdev))

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

        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(requestData)

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
                    exception.ZVMClientInternalError) as err1:
                msg1 = err1.format_message()
                persist_OK = True
                requestData = ' '.join((
                    'SMAPI %s API Virtual_Network_Adapter_Delete_DM' % userid,
                    "--operands",
                    '-v %s' % vdev))
                try:
                    self._request(requestData)
                except exception.ZVMClientRequestFailed as err2:
                    results = err2.results
                    msg2 = err2.format_message()
                    if ((results['rc'] == 404) and
                        (results['rs'] == 8)):
                        persist_OK = True
                    else:
                        persist_OK = False
                if persist_OK:
                    msg = ("Failed to create nic %s for %s on the active "
                           "guest system, %s") % (vdev, userid, msg1)
                else:
                    msg = ("Failed to create nic %s for %s on the active "
                           "guest system, %s, and failed to revoke user "
                           "direct's changes, %s") % (vdev, userid,
                                                      msg1, msg2)
                raise exception.ZVMNetworkError(msg)

        self._NetDbOperator.switch_add_record_for_nic(userid, vdev,
                                                      port=nic_id)

    def get_user_direct(self, userid):
        results = self._request("getvm %s directory" % userid)
        return results.get('response', [])

    def delete_nic(self, userid, vdev, active=False):
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Adapter_Delete_DM" %
            userid,
            '-v %s' % vdev))
        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
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
                    raise exception.ZVMNetworkError(
                        msg=("Failed to delete nic %s for %s in "
                             "the guest's user direct, %s") %
                             (vdev, userid, emsg))

        self._NetDbOperator.switch_delete_record_for_nic(userid, vdev)
        if active:
            rd = ' '.join((
                "SMAPI %s API Virtual_Network_Adapter_Delete" %
                userid,
                '-v %s' % vdev))
            with zvmutils.expect_request_failed_and_reraise(
                exception.ZVMNetworkError):
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
                        raise exception.ZVMNetworkError(
                            msg=("Failed to delete nic %s for %s on "
                                 "the active guest system, %s") %
                                 (vdev, userid, emsg))

    def _couple_nic(self, userid, vdev, vswitch_name,
                    active=False):
        """Couple NIC to vswitch by adding vswitch into user direct."""
        requestData = ' '.join((
            'SMAPI %s' % userid,
            "API Virtual_Network_Adapter_Connect_Vswitch_DM",
            "--operands",
            "-v %s" % vdev,
            "-n %s" % vswitch_name))

        with zvmutils.expect_request_failed_and_reraise(
            exception.ZVMNetworkError):
            self._request(requestData)

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
                    exception.ZVMClientInternalError) as err1:
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
                            exception.ZVMClientInternalError) as err2:
                        results2 = err2.results
                        msg2 = err2.format_message()
                        if ((results2 is not None) and
                            (results2['rc'] == 212) and
                            (results2['rs'] == 32)):
                            persist_OK = True
                        else:
                            persist_OK = False
                    if persist_OK:
                        msg = ("Failed to couple nic %s to vswitch %s "
                               "on the active guest system, %s") % (vdev,
                                                    vswitch_name, msg1)
                    else:
                        msg = ("Failed to couple nic %s to vswitch %s "
                               "on the active guest system, %s, and "
                               "failed to revoke user direct's changes, "
                               "%s") % (vdev, vswitch_name,
                                        msg1, msg2)
                    raise exception.ZVMNetworkError(msg)

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
                exception.ZVMClientInternalError) as err:
            results = err.results
            emsg = err.format_message()
            if ((results is not None) and
                (results['rc'] == 212) and
                (results['rs'] == 32)):
                LOG.warning("Virtual device %s is already disconnected "
                        "in the guest's user direct", vdev)
            else:
                raise exception.ZVMNetworkError(
                    msg=("Failed to uncouple nic %s "
                         "in the guest's user direct,  %s") %
                         (vdev, emsg))

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
                    exception.ZVMClientInternalError) as err:
                results = err.results
                emsg = err.format_message()
                if ((results is not None) and
                    (results['rc'] == 204) and
                    (results['rs'] == 48)):
                    LOG.warning("Virtual device %s is already "
                                "disconnected on the active "
                                "guest system", vdev)
                else:
                    raise exception.ZVMNetworkError(
                        msg=("Failed to uncouple nic %s "
                             "on the active guest system, %s") %
                             (vdev, emsg))

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

    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import the image specified in url to SDK image repository, and
        create a record in image db, the imported images are located in
        image_repository/prov_method/os_version/, for example,
        /opt/sdk/images/netboot/rhel7.2/90685d2b-167b.img"""

        try:
            # Ensure the specified image is not exisit in image DB
            image_exists = self._ImageDbOperator.image_query_record(image_name)
            if image_exists:
                LOG.info("The image %s has already exist in image repository"
                         % image_name)
                return
            target = self._get_image_path_by_name(image_name,
                image_meta['os_version'], const.IMAGE_TYPE['DEPLOY'])
            self._pathutils.create_import_image_repository(
                image_meta['os_version'], const.IMAGE_TYPE['DEPLOY'])
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
                                         image_size,
                                         const.IMAGE_TYPE['DEPLOY'])
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

    def image_delete(self, image_name):
        # Delete image file
        self._delete_image_file(image_name)
        # Delete image record from db
        self._ImageDbOperator.image_delete_record(image_name)

    def _delete_image_file(self, image_name):
        target_info = self._ImageDbOperator.image_query_record(image_name)
        image_path = '/'.join([CONF.image.sdk_image_repository,
                               target_info[5],
                               target_info[1],
                               image_name])

        self._pathutils.remove_file(image_path)


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
                              const.IMAGE_TYPE['DEPLOY'],
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
