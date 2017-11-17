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


import six

from zvmsdk import config
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils


_VMOPS = None
CONF = config.CONF
LOG = log.LOG


def get_vmops():
    global _VMOPS
    if _VMOPS is None:
        _VMOPS = VMOps()
    return _VMOPS


class VMOps(object):

    def __init__(self):
        self._smutclient = smutclient.get_smutclient()
        self._dist_manager = dist.LinuxDistManager()
        self._pathutils = zvmutils.PathUtils()

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        zvmutils.check_guest_exist(userid)

        return self._smutclient.get_power_state(userid)

    def _get_cpu_num_from_user_dict(self, dict_info):
        cpu_num = 0
        for inf in dict_info:
            if 'CPU ' in inf:
                cpu_num += 1
        return cpu_num

    def _get_max_memory_from_user_dict(self, dict_info):
        with zvmutils.expect_invalid_resp_data():
            mem = dict_info[0].split(' ')[4]
            return zvmutils.convert_to_mb(mem) * 1024

    def get_info(self, userid):
        power_stat = self.get_power_state(userid)
        perf_info = self._smutclient.get_image_performance_info(userid)

        if perf_info:
            try:
                max_mem_kb = int(perf_info['max_memory'].split()[0])
                mem_kb = int(perf_info['used_memory'].split()[0])
                num_cpu = int(perf_info['guest_cpus'])
                cpu_time_us = int(perf_info['used_cpu_time'].split()[0])
            except (ValueError, TypeError, IndexError, AttributeError,
                    KeyError) as err:
                LOG.error('Parse performance_info encounter error: %s',
                          str(perf_info))
                raise exception.SDKInternalError(msg=str(err),
                                                    modID='guest')

            return {'power_state': power_stat,
                    'max_mem_kb': max_mem_kb,
                    'mem_kb': mem_kb,
                    'num_cpu': num_cpu,
                    'cpu_time_us': cpu_time_us}
        else:
            # virtual machine in shutdown state or not exists
            dict_info = self._smutclient.get_user_direct(userid)
            return {
                'power_state': power_stat,
                'max_mem_kb': self._get_max_memory_from_user_dict(dict_info),
                'mem_kb': 0,
                'num_cpu': self._get_cpu_num_from_user_dict(dict_info),
                'cpu_time_us': 0}

    def instance_metadata(self, instance, content, extra_md):
        pass

    def add_instance_metadata(self):
        pass

    def is_reachable(self, userid):
        """Reachable through IUCV communication channel."""
        return self._smutclient.get_guest_connection_status(userid)

    def guest_start(self, userid):
        """"Power on z/VM instance."""
        zvmutils.check_guest_exist(userid)

        self._smutclient.guest_start(userid)

    def guest_stop(self, userid, **kwargs):
        zvmutils.check_guest_exist(userid)
        self._smutclient.guest_stop(userid, **kwargs)

    def guest_softstop(self, userid, **kwargs):
        zvmutils.check_guest_exist(userid)
        self._smutclient.guest_softstop(userid, **kwargs)

    def guest_pause(self, userid):
        zvmutils.check_guest_exist(userid)

        self._smutclient.guest_pause(userid)

    def guest_unpause(self, userid):
        zvmutils.check_guest_exist(userid)

        self._smutclient.guest_unpause(userid)

    def guest_reboot(self, userid):
        """Reboot a guest vm."""
        zvmutils.check_guest_exist(userid)

        self._smutclient.guest_reboot(userid)

    def guest_reset(self, userid):
        """Reset z/VM instance."""
        zvmutils.check_guest_exist(userid)

        self._smutclient.guest_reset(userid)

    def create_vm(self, userid, cpu, memory, disk_list=[],
                  user_profile=CONF.zvm.user_profile):
        """Create z/VM userid into user directory for a z/VM instance."""
        LOG.debug("Creating the z/VM user entry for instance %s"
                  % userid)

        self._smutclient.create_vm(userid, cpu, memory,
                                   disk_list, user_profile)

    def create_disks(self, userid, disk_list):
        zvmutils.check_guest_exist(userid)

        user_direct = self._smutclient.get_user_direct(userid)

        exist_disks = []
        for ent in user_direct:
            if 'MDISK' in ent:
                md_vdev = ent.split()[1].strip()
                exist_disks.append(md_vdev)

        start_vdev = hex(int(max(exist_disks), 16) + 1)[2:].rjust(4, '0')
        self._smutclient.add_mdisks(userid, disk_list, start_vdev)

    def delete_disks(self, userid, vdev_list):
        zvmutils.check_guest_exist(userid)

        self._smutclient.remove_mdisks(userid, vdev_list)

    def guest_config_minidisks(self, userid, disk_info):
        zvmutils.check_guest_exist(userid)

        if disk_info != []:
            LOG.debug("Start to configure disks to %s." % userid)
            self._smutclient.process_additional_minidisks(userid, disk_info)
        else:
            LOG.debug("No disk to handle on %s." % userid)

    def is_powered_off(self, instance_name):
        """Return True if the instance is powered off."""
        return self._smutclient.get_power_state(instance_name) == 'off'

    def delete_vm(self, userid):
        """Delete z/VM userid for the instance."""
        self._smutclient.delete_vm(userid)

    def execute_cmd(self, userid, cmdStr):
        """Execute commands on the guest vm."""
        return self._smutclient.execute_cmd(userid, cmdStr)

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        zvmutils.check_guest_exist(userid)

        LOG.debug("Begin to deploy image on vm %s", userid)
        self._smutclient.guest_deploy(userid, image_name,
                                      transportfiles, remotehost, vdev)

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6):
        zvmutils.check_guest_exist(userid)
        LOG.debug("Begin to capture vm %s", userid)
        self._smutclient.guest_capture(userid, image_name,
                                       capture_type=capture_type,
                                       compress_level=compress_level)

    def guest_list(self):
        return self._smutclient.get_vm_list()

    def get_definition_info(self, userid, **kwargs):
        check_command = ["nic_coupled"]
        direct_info = self._smutclient.get_user_direct(userid)
        info = {}
        info['user_direct'] = direct_info

        for k, v in kwargs.items():
            if k in check_command:
                if (k == 'nic_coupled'):
                    info['nic_coupled'] = False
                    nstr = "NICDEF %s TYPE QDIO LAN SYSTEM" % v
                    for inf in direct_info:
                        if nstr in inf:
                            info['nic_coupled'] = True
                            break
            else:
                raise exception.SDKInvalidInputFormat(
                    msg=("invalid check option for user direct: %s") % k)

        return info

    def get_console_output(self, userid):
        def append_to_log(log_data, log_path):
            LOG.debug('log_data: %(log_data)r, log_path: %(log_path)r',
                         {'log_data': log_data, 'log_path': log_path})
            with open(log_path, 'a+') as fp:
                fp.write(log_data)

            return log_path

        log_size = CONF.guest.console_log_size * 1024
        console_log = self._smutclient.get_user_console_output(userid)

        log_path = self._pathutils.get_console_log_path(userid)
        # TODO: need consider shrink log file size
        append_to_log(console_log, log_path)

        log_fp = file(log_path, 'rb')
        try:
            log_data, remaining = zvmutils.last_bytes(log_fp, log_size)
        except Exception as err:
            msg = ("Failed to truncate console log, error: %s" %
                   six.text_type(err))
            LOG.error(msg)
            raise exception.SDKInternalError(msg)

        if remaining > 0:
            LOG.info('Truncated console log returned, %d bytes ignored' %
                     remaining)
        return log_data
