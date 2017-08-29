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


import os
import re
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


class SMUTClient(client.ZVMClient):

    def __init__(self):
        super(SMUTClient, self).__init__()
        self._smut = smut.SMUT()
        self._NetDbOperator = database.NetworkDbOperator()

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
        set_vswitch_command = ["grant_userid", "user_vlan_id",
                               "revoke_userid", "real_device_address",
                               "port_name", "controller_name",
                               "connection_value", "queue_memory_limit",
                               "routing_value", "port_type", "persist",
                               "gvrp_value", "mac_id", "uplink",
                               "nic_userid", "nic_vdev",
                               "lacp", "interval", "group_rdev",
                               "iptimeout", "port_isolation", "promiscuous",
                               "MAC_protect", "VLAN_counters"]
        smut_userid = zvmutils.get_smut_userid()
        rd = ' '.join((
            "SMAPI %s API Virtual_Network_Vswitch_Set_Extended" %
            smut_userid,
            "--operands",
            "-k switch_name=%s" % switch_name))

        for k, v in kwargs.items():
            if k in set_vswitch_command:
                rd = ' '.join((rd,
                               "-k %(key)s=\'%(value)s\'" %
                               {'key': k, 'value': v}))
            else:
                raise exception.ZVMInvalidInput(
                    msg=("switch %s changes failed, invalid keyword %s") %
                        (switch_name, k))
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
