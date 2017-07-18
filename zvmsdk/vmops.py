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


import time

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import constants
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import imageops
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
        self._zvmclient = zvmclient.get_zvmclient()
        self._dist_manager = dist.LinuxDistManager()
        self._imageops = imageops.get_imageops()
        self._pathutils = zvmutils.PathUtils()

    def get_power_state(self, guest_id):
        """Get power status of a z/VM instance."""
        return self._zvmclient.get_power_state(guest_id)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_cpu_num_from_user_dict(self, dict_info):
        cpu_num = 0
        for inf in dict_info:
            if 'CPU ' in inf:
                cpu_num += 1
        return cpu_num

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_max_memory_from_user_dict(self, dict_info):
        mem = dict_info[0].split(' ')[4]
        return zvmutils.convert_to_mb(mem) * 1024

    def get_info(self, userid):
        power_stat = self.get_power_state(userid)
        perf_info = self._zvmclient.get_image_performance_info(userid)

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
                raise exception.ZVMSDKInteralError(msg=str(err))

            return {'power_state': power_stat,
                    'max_mem_kb': max_mem_kb,
                    'mem_kb': mem_kb,
                    'num_cpu': num_cpu,
                    'cpu_time_us': cpu_time_us}
        else:
            # virtual machine in shutdown state or not exists
            with zvmutils.expect_invalid_xcat_node_and_reraise(userid):
                dict_info = self._zvmclient.get_user_direct(userid)
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

    def is_reachable(self, instance_name):
        """Return True is the instance is reachable."""
        res_dict = self._zvmclient.get_node_status(instance_name)
        LOG.debug('Get instance status of %s', instance_name)

        with zvmutils.expect_invalid_xcat_resp_data(res_dict):
            status = res_dict['node'][0][0]['data'][0]

        if status is not None:
            if status.__contains__('sshd'):
                return True

        return False

    def guest_start(self, userid):
        """"Power on z/VM instance."""
        self._zvmclient.guest_start(userid)

    def guest_stop(self, userid, timeout, retry_interval):
        self._zvmclient.guest_stop(userid)

        # retry shutdown until timeout
        if timeout > 0:
            retry_count = timeout // retry_interval
            while (retry_count > 0):
                if self.get_power_state(userid) == constants.POWER_STATE_OFF:
                    # In shutdown state already
                    return
                else:
                    self._zvmclient.guest_stop(userid)
                    time.sleep(retry_interval)
                    retry_count -= 1

            LOG.warning("Failed to shutdown guest vm %(userid)s in %(time)d "
                         "seconds" % {'userid': userid, 'time': timeout})

    def create_vm(self, instance_name, cpu, memory, disk_list=[],
                  user_profile=CONF.zvm.user_profile):
        """Create z/VM userid into user directory for a z/VM instance."""
        LOG.debug("Creating the z/VM user entry for instance %s"
                  % instance_name)

        try:
            self._zvmclient.create_vm(instance_name, cpu, memory,
                                      disk_list, user_profile)
        except Exception as err:
            msg = ("Failed to create z/VM userid: %s") % err
            LOG.error(msg)
            raise exception.ZVMException(msg=err)

    def guest_config_minidisks(self, userid, disk_info):
        if disk_info != []:
            LOG.debug("Start to configure disks to %s." % userid)
            self._zvmclient.process_additional_minidisks(userid, disk_info)
        else:
            LOG.debug("No disk to handle on %s." % userid)

    def is_powered_off(self, instance_name):
        """Return True if the instance is powered off."""
        return self._zvmclient.get_power_state(instance_name) == 'off'

    def delete_vm(self, userid):
        """Delete z/VM userid for the instance.This will remove xCAT node
        at same time.
        """
        self._zvmclient.delete_vm(userid)

    def guest_deploy(self, user_id, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        try:
            LOG.debug("Begin to deploy image on vm %s", user_id)

            self._zvmclient.guest_deploy(user_id, image_name,
                                         transportfiles, remotehost, vdev)

        except exception as err:
            LOG.error(('Failed to deploy image %(img)s to vm %(vm)s') %
                      {'img': image_name,
                       'vm': user_id})
            raise err

    def guests_list(self):
        return self._zvmclient.get_vm_list()

    def get_definition_info(self, userid, **kwargs):
        check_command = ["nic_coupled"]
        direct_info = self._zvmclient.get_user_direct(userid)
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
                raise exception.ZVMInvalidInput(
                    msg=("invalid check option for user direct: %s") % k)

        return info

    def get_console_output(self, userid):
        def append_to_log(log_data, log_path):
            LOG.debug('log_data: %(log_data)r, log_path: %(log_path)r',
                         {'log_data': log_data, 'log_path': log_path})
            fp = open(log_path, 'a+')
            fp.write(log_data)
            fp.close()
            return log_path

        log_size = CONF.guest.console_log_size * 1024
        console_log = ""

        try:
            console_log = self._zvmclient.get_user_console_output(userid,
                                                                  log_size)
        except exception.ZVMXCATInternalError:
            # Ignore no console log avaiable error
            LOG.info("No new console log avaiable.")

        log_path = self._pathutils.get_console_log_path(CONF.zvm.host, userid)
        # TODO: need consider shrink log file size
        append_to_log(console_log, log_path)

        log_fp = file(log_path, 'rb')
        log_data, remaining = zvmutils.last_bytes(log_fp, log_size)
        if remaining > 0:
            LOG.info('Truncated console log returned, %d bytes ignored' %
                     remaining)
        return log_data
