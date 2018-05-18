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
        self._namelist = zvmutils.get_namelist()

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
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
        LOG.info("Begin to power on vm %s", userid)
        self._smutclient.guest_start(userid)
        LOG.info("Complete power on vm %s", userid)

    def guest_stop(self, userid, **kwargs):
        LOG.info("Begin to power off vm %s", userid)
        self._smutclient.guest_stop(userid, **kwargs)
        LOG.info("Complete power off vm %s", userid)

    def guest_softstop(self, userid, **kwargs):
        LOG.info("Begin to soft power off vm %s", userid)
        self._smutclient.guest_softstop(userid, **kwargs)
        LOG.info("Complete soft power off vm %s", userid)

    def guest_pause(self, userid):
        LOG.info("Begin to pause vm %s", userid)
        self._smutclient.guest_pause(userid)
        LOG.info("Complete pause vm %s", userid)

    def guest_unpause(self, userid):
        LOG.info("Begin to unpause vm %s", userid)
        self._smutclient.guest_unpause(userid)
        LOG.info("Complete unpause vm %s", userid)

    def guest_reboot(self, userid):
        """Reboot a guest vm."""
        LOG.info("Begin to reboot vm %s", userid)
        self._smutclient.guest_reboot(userid)
        LOG.info("Complete reboot vm %s", userid)

    def guest_reset(self, userid):
        """Reset z/VM instance."""
        LOG.info("Begin to reset vm %s", userid)
        self._smutclient.guest_reset(userid)
        LOG.info("Complete reset vm %s", userid)

    def create_vm(self, userid, cpu, memory, disk_list,
                  user_profile, max_cpu, max_mem):
        """Create z/VM userid into user directory for a z/VM instance."""
        LOG.info("Creating the user directory for vm %s", userid)

        self._smutclient.create_vm(userid, cpu, memory,
                                   disk_list, user_profile,
                                   max_cpu, max_mem)

        # add userid into smapi namelist
        self._smutclient.namelist_add(self._namelist, userid)

    def create_disks(self, userid, disk_list):
        LOG.info("Beging to create disks for vm: %(userid)s, list: %(list)s",
                 {'userid': userid, 'list': disk_list})
        user_direct = self._smutclient.get_user_direct(userid)

        exist_disks = []
        for ent in user_direct:
            if ent.strip().startswith('MDISK'):
                md_vdev = ent.split()[1].strip()
                exist_disks.append(md_vdev)

        if exist_disks:
            start_vdev = hex(int(max(exist_disks), 16) + 1)[2:].rjust(4, '0')
        else:
            start_vdev = None
        self._smutclient.add_mdisks(userid, disk_list, start_vdev)

        LOG.info("Complete create disks for vm: %s", userid)

    def delete_disks(self, userid, vdev_list):
        LOG.info("Begin to delete disk on vm: %(userid), vdev list: %(list)s",
                 {'userid': userid, 'list': vdev_list})
        self._smutclient.remove_mdisks(userid, vdev_list)
        LOG.info("Complete delete disks for vm: %s", userid)

    def guest_config_minidisks(self, userid, disk_info):
        LOG.info("Begin to configure disks on vm: %(userid), info: %(info)s",
                 {'userid': userid, 'info': disk_info})
        if disk_info != []:
            self._smutclient.process_additional_minidisks(userid, disk_info)
            LOG.info("Complete configure disks for vm: %s", userid)
        else:
            LOG.info("No disk to handle on %s." % userid)

    def is_powered_off(self, instance_name):
        """Return True if the instance is powered off."""
        return self._smutclient.get_power_state(instance_name) == 'off'

    def delete_vm(self, userid):
        """Delete z/VM userid for the instance."""
        LOG.info("Begin to delete vm %s", userid)
        self._smutclient.delete_vm(userid)

        # remove userid from smapi namelist
        self._smutclient.namelist_remove(self._namelist, userid)
        LOG.info("Complete delete vm %s", userid)

    def execute_cmd(self, userid, cmdStr):
        """Execute commands on the guest vm."""
        LOG.debug("executing cmd: %s", cmdStr)
        return self._smutclient.execute_cmd(userid, cmdStr)

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        LOG.info("Begin to deploy image on vm %s", userid)
        self._smutclient.guest_deploy(userid, image_name,
                                      transportfiles, remotehost, vdev)

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6):
        LOG.info("Begin to capture vm %(userid), image name is %(name)s",
                 {'userid': userid, 'name': image_name})
        self._smutclient.guest_capture(userid, image_name,
                                       capture_type=capture_type,
                                       compress_level=compress_level)
        LOG.info("Complete capture image on vm %s", userid)

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

        LOG.info("Begin to capture console log on vm %s", userid)
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

        LOG.info("Complete get console output on vm %s", userid)
        return log_data

    def check_guests_exist_in_db(self, userids, raise_exc=True):
        if not isinstance(userids, list):
            # convert userid string to list
            userids = [userids]

        all_userids = self.guest_list()
        userids_not_in_db = list(set(userids) - set(all_userids))
        if userids_not_in_db:
            if raise_exc:
                # log and raise exception
                userids_not_in_db = ' '.join(userids_not_in_db)
                LOG.error("Guest '%s' does not exist in guests database" %
                          userids_not_in_db)
                raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % userids_not_in_db), modID='guest')
            else:
                return False
        else:
            return True

    def live_resize_cpus(self, userid, count):
        # Check power state is 'on'
        state = self.get_power_state(userid)
        if state != 'on':
            LOG.error("Failed to live resize cpus of guest %s, error: "
                      "guest is inactive, cann't perform live resize." %
                      userid)
            raise exception.SDKConflictError(modID='guest', rs=1,
                                             userid=userid)
        # Do live resize
        self._smutclient.live_resize_cpus(userid, count)

        LOG.info("Complete live resize cpu on vm %s", userid)

    def resize_cpus(self, userid, count):
        LOG.info("Begin to resize cpu on vm %s", userid)
        # Do resize
        self._smutclient.resize_cpus(userid, count)
        LOG.info("Complete resize cpu on vm %s", userid)
