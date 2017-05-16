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


import uuid

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import constants as const
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
        self._dist_manager = dist.ListDistManager()
        self._imageops = imageops.get_imageops()

    def get_power_state(self, vm_id):
        """Get power status of a z/VM instance."""
        return self._zvmclient.get_power_state(vm_id)

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

    def get_user_direct(self, userid):
        raw_dict = self._zvmclient.get_user_direct(userid)
        return [ent.partition(': ')[2] for ent in raw_dict]

    def get_info(self, userid):
        power_stat = self.get_power_state(userid)
        perf_info = self._zvmclient.get_image_performance_info(userid)

        if perf_info:
            try:
                max_mem_kb = int(perf_info['max_memory'].split()[0])
                mem_kb = int(perf_info['used_memory'].split()[0])
                num_cpu = int(perf_info['guest_cpus'])
                cpu_time_ns = int(perf_info['used_cpu_time'].split()[0]) * 1000
            except (ValueError, TypeError, IndexError, AttributeError,
                    KeyError) as err:
                LOG.error('Parse performance_info encounter error: %s',
                          str(perf_info))
                raise exception.ZVMSDKInteralError(msg=str(err))

            return {'power_state': power_stat,
                    'max_mem_kb': max_mem_kb,
                    'mem_kb': mem_kb,
                    'num_cpu': num_cpu,
                    'cpu_time_ns': cpu_time_ns}
        else:
            # virtual machine in shutdown state or not exists
            with zvmutils.expect_invalid_xcat_node_and_reraise(userid):
                dict_info = self.get_user_direct(userid)
            return {
                'power_state': power_stat,
                'max_mem_kb': self._get_max_memory_from_user_dict(dict_info),
                'mem_kb': 0,
                'num_cpu': self._get_cpu_num_from_user_dict(dict_info),
                'cpu_time_ns': 0}

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

    def power_on(self, instance_name):
        """"Power on z/VM instance."""
        self._zvmclient.power_on(instance_name)

    def create_userid(self, instance_name, cpu, memory, root_disk_size,
                      eph_disks):
        """Create z/VM userid into user directory for a z/VM instance."""
        LOG.debug("Creating the z/VM user entry for instance %s"
                      % instance_name)

        kwprofile = 'profile=%s' % const.ZVM_USER_PROFILE
        try:
            self._zvmclient.make_vm(instance_name, kwprofile,
                                   cpu, memory)

            # Add root disk
            self.add_mdisk(instance_name, CONF.zvm.diskpool,
                               CONF.zvm.user_root_vdev,
                               root_disk_size)
            # Process eph disks
            if eph_disks != []:
                self.process_additional_disks(instance_name, eph_disks)
            # Set ipl
            # TODO:check whether need ipl or not
            self.set_ipl(instance_name, CONF.zvm.user_root_vdev)

        except Exception as err:
            msg = ("Failed to create z/VM userid: %s") % err
            LOG.error(msg)
            raise exception.ZVMException(msg=err)

    def process_additional_disks(self, instance_name, eph_list):
        if eph_list != []:
            LOG.debug("Start to add ephemeral disks to %s." % instance_name)
            for idx, eph in enumerate(eph_list):
                vdev = self._zvmclient.generate_eph_vdev(idx)
                fmt = eph.get('format')
                mount_dir = ''.join([CONF.zvm.default_ephemeral_mntdir,
                                    str(idx)])
                self._zvmclient.process_eph_disk(instance_name, vdev,
                                                 fmt, mount_dir)
        else:
            LOG.debug("No ephemeral disks to add on %s." % instance_name)

    def add_mdisk(self, instance_name, diskpool, vdev, size, fmt=None):
        """Add a 3390 mdisk for a z/VM user.

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """
        disk_type = CONF.zvm.diskpool_type
        if (disk_type == 'ECKD'):
            action = '--add3390'
        elif (disk_type == 'FBA'):
            action = '--add9336'
        else:
            errmsg = ("Disk type %s is not supported.") % disk_type
            LOG.error(errmsg)
            raise exception.ZVMException(msg=errmsg)

        self._zvmclient.change_vm_fmt(instance_name, fmt, action,
                                     diskpool, vdev, size)

    def add_mdisks(self, instance_name, eph_list):
        """add more than one disk
        """
        for idx, eph in eph_list:
            vdev = self._zvmclient.generate_eph_vdev(idx)
            size = eph['size']
            fmt = (eph.get('format') or
                   CONF.zvm.default_ephemeral_format or
                   const.DEFAULT_EPH_DISK_FMT)
            self.add_mdisk(CONF.zvm.diskpool, vdev, size, fmt)

    def set_ipl(self, instance_name, ipl_state):
        self._zvmclient.change_vm_ipl_state(instance_name, ipl_state)

    def is_powered_off(self, instance_name):
        """Return True if the instance is powered off."""
        return self._zvmclient.get_power_state(instance_name) == 'off'

    def create_vm(self, userid, cpu, memory, root_disk_size, eph_disks):
        """
        create_vm will create the node and userid for instance
        :parm userid: eg. lil00033
        :parm cpu: amount of vcpus
        :parm memory: size of memory
        :parm root_gb:
        :parm eph_disks:
        :parm image_name: spawn image name
        """
        # TODO:image_name -> image_file_path
        self._zvmclient.prepare_for_spawn(userid)
        self.create_userid(userid, cpu, memory, root_disk_size, eph_disks)

    def delete_vm(self, userid, zhcp_node):
        """Delete z/VM userid for the instance.This will remove xCAT node
        at same time.
        """
        # Versions of xCAT that do not understand the instance ID and
        # request ID will silently ignore them.
        try:
            self._zvmclient.remove_vm(userid)
        except Exception as err:
            # TODO:implement after exception merged
            # emsg = err.format_message()
            emsg = ""
            if (emsg.__contains__("Return Code: 400") and
               (emsg.__contains__("Reason Code: 16") or
                emsg.__contains__("Reason Code: 12"))):
                self._zvmclient.remove_vm(userid)
            else:
                LOG.debug("exception not able to handle in delete_vm "
                          "%s", self._name)
                raise err
        except Exception as err:
            # TODO:implement after exception merged
            # emsg = err.format_message()
            emsg = ""
            if (emsg.__contains__("Invalid nodes and/or groups") and
                    emsg.__contains__("Forbidden")):
                # Assume neither zVM userid nor xCAT node exist in this case
                return
            else:
                raise err

    def capture_instance(self, instance_name):
        """Invoke xCAT REST API to capture a instance."""
        LOG.info('Begin to capture instance %s' % instance_name)
        nodename = instance_name
        image_id = str(uuid.uuid1())
        image_uuid = image_id.replace('-', '_')
        profile = image_uuid
        res = self._zvmclient.do_capture(nodename, profile)
        LOG.info(res['info'][3][0])
        image_name = res['info'][3][0].split('(')[1].split(')')[0]
        return image_name

    def delete_image(self, image_name):
        """"Invoke xCAT REST API to delete a image."""
        try:
            self._zvmclient.remove_image_file(image_name)
        except exception.ZVMException:
            LOG.warn(("Failed to delete image file %s from xCAT") %
                    image_name)

        try:
            self._zvmclient.remove_image_definition(image_name)
        except exception.ZVMException:
            LOG.warn(("Failed to delete image definition %s from xCAT") %
                    image_name)
        LOG.info('Image %s successfully deleted' % image_name)

    def deploy_image_to_vm(self, user_id, image_name, transportfiles=None,
                           vdev=None):
        try:
            LOG.debug("Begin to deploy image on vm %s", user_id)

            self._zvmclient.deploy_image_to_vm(user_id, image_name,
                                               transportfiles, vdev)

        except exception as err:
            LOG.error(('Failed to deploy image %(img)s to vm %(vm)s') %
                     {'img': image_name,
                      'vm': user_id})
            raise err
