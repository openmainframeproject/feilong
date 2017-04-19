
import commands
import constants as const
import dist
import os
import uuid

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import log
from zvmsdk import utils as zvmutils


_VMOPS = None
CONF = config.CONF
LOG = log.LOG


def _get_vmops():
    global _VMOPS
    if _VMOPS is None:
        _VMOPS = VMOps()
    return _VMOPS


class VMOps(object):

    def __init__(self):
        self.zvmclient = zvmclient.get_zvmclient()
        self._dist_manager = dist.ListDistManager()

    def get_power_state(self, vm_id):
        """Get power status of a z/VM instance."""
        return self.zvmclient.get_power_state(vm_id)

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsdef(self, instance_name):
        url = self._xcat_url.lsdef_node('/' + instance_name)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0]
        return resp_info

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_ip_addr_from_lsdef_info(self, info):
        for inf in info:
            if 'ip=' in inf:
                ip_addr = inf.rpartition('ip=')[2].strip(' \n')
                return ip_addr

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_os_from_lsdef_info(self, info):
        for inf in info:
            if 'os=' in inf:
                _os = inf.rpartition('os=')[2].strip(' \n')
                return _os

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _lsvm(self, instance_name):
        url = self._xcat_url.lsvm('/' + instance_name)
        resp_info = zvmutils.xcat_request("GET", url)['info'][0][0]
        return resp_info.split('\n')

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_cpu_num_from_lsvm_info(self, info):
        cpu_num = 0
        for inf in info:
            if ': CPU ' in inf:
                cpu_num += 1
        return cpu_num

    @zvmutils.wrap_invalid_xcat_resp_data_error
    def _get_memory_from_lsvm_info(self, info):
        return info[0].split(' ')[4]

    def get_info(self, instance_name):
        power_stat = self.get_power_state(instance_name)

        lsdef_info = self._lsdef(instance_name)
        ip_addr = self._get_ip_addr_from_lsdef_info(lsdef_info)
        _os = self._get_os_from_lsdef_info(lsdef_info)

        lsvm_info = self._lsvm(instance_name)
        vcpus = self._get_cpu_num_from_lsvm_info(lsvm_info)
        mem = self._get_memory_from_lsvm_info(lsvm_info)

        return {'power_state': power_stat,
                'vcpus': vcpus,
                'memory': mem,
                'ip_addr': ip_addr,
                'os': _os}

    def instance_metadata(self, instance, content, extra_md):
        pass

    def add_instance_metadata(self):
        pass

    def _preset_instance_network(self, instance_name, ip_addr):
        zvmutils.config_xcat_mac(instance_name)
        LOG.debug("Add ip/host name on xCAT MN for instance %s",
                    instance_name)

        zvmutils.add_xcat_host(instance_name, ip_addr, instance_name)
        zvmutils.makehosts()

    def _add_nic_to_table(self, instance_name, ip_addr):
        nic_vdev = CONF.zvm_default_nic_vdev
        nic_name = CONF.nic_name
        zhcpnode = CONF.zhcp
        zvmutils.create_xcat_table_about_nic(zhcpnode,
                                         instance_name,
                                         nic_name,
                                         ip_addr,
                                         nic_vdev)
        nic_vdev = str(hex(int(nic_vdev, 16) + 3))[2:]

    def _wait_for_reachable(self, instance_name):
        """Called at an interval until the instance is reachable."""
        self._reachable = False

        def _check_reachable():
            if not self.is_reachable(instance_name):
                pass
            else:
                self._reachable = True

        zvmutils.looping_call(_check_reachable, 5, 5, 30,
            CONF.zvm_reachable_timeout,
            zvmutils.ZVMException(msg='not reachable, retry'))

    def is_reachable(self, instance_name):
        """Return True is the instance is reachable."""
        url = self._xcat_url.nodestat('/' + instance_name)
        LOG.debug('Get instance status of %s', instance_name)
        res_dict = zvmutils.xcat_request("GET", url)

        with zvmutils.expect_invalid_xcat_resp_data(res_dict):
            status = res_dict['node'][0][0]['data'][0]

        if status is not None:
            if status.__contains__('sshd'):
                return True

        return False

    def power_on(self, instance_name):
        """"Power on z/VM instance."""
        try:
            self.zvmclient.power_on(instance_name)
        except Exception as err:
            err_str = str(err)
            if ("Return Code: 200" in err_str and
                    "Reason Code: 8" in err_str):
                # Instance already not active
                LOG.warning("z/VM instance %s already active", instance_name)
                return
            else:
                raise

    def create_userid(self, instance_name, cpu, memory, image_name):
        """Create z/VM userid into user directory for a z/VM instance."""
        LOG.debug("Creating the z/VM user entry for instance %s"
                      % instance_name)

        kwprofile = 'profile=%s' % const.ZVM_USER_PROFILE
        body = [kwprofile,
                'password=%s' % CONF.zvm_user_default_password,
                'cpu=%i' % cpu,
                'memory=%im' % memory,
                'privilege=%s' % const.ZVM_USER_DEFAULT_PRIVILEGE,
                'ipl=%s' % CONF.zvm_user_root_vdev,
                'imagename=%s' % image_name]

        url = zvmutils.get_xcat_url().mkvm('/' + instance_name)

        try:
            zvmutils.xcat_request("POST", url, body)
            size = CONF.root_disk_units
            # Add root disk and set ipl
            self.add_mdisk(instance_name, CONF.zvm_diskpool,
                           CONF.zvm_user_root_vdev,
                               size)
            self.set_ipl(instance_name, CONF.zvm_user_root_vdev)

        except Exception as err:
            msg = ("Failed to create z/VM userid: %s") % err
            LOG.error(msg)
            raise zvmutils.ZVMException(msg=err)

    def add_mdisk(self, instance_name, diskpool, vdev, size, fmt=None):
        """Add a 3390 mdisk for a z/VM user.

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """
        disk_type = CONF.zvm_diskpool_type
        if (disk_type == 'ECKD'):
            action = '--add3390'
        elif (disk_type == 'FBA'):
            action = '--add9336'
        else:
            errmsg = ("Disk type %s is not supported.") % disk_type
            LOG.error(errmsg)
            raise zvmutils.ZVMException(msg=errmsg)

        if fmt:
            body = [" ".join([action, diskpool, vdev, size, "MR", "''", "''",
                    "''", fmt])]
        else:
            body = [" ".join([action, diskpool, vdev, size])]
        url = zvmutils.get_xcat_url().chvm('/' + instance_name)
        zvmutils.xcat_request("PUT", url, body)

    def set_ipl(self, instance_name, ipl_state):
        body = ["--setipl %s" % ipl_state]
        url = zvmutils.get_xcat_url().chvm('/' + instance_name)
        zvmutils.xcat_request("PUT", url, body)

    def instance_exists(self, instance_name):
        """Overwrite this to using instance name as input parameter."""
        return instance_name in self.list_instances()

    def list_instances(self):
        """Return the names of all the instances known to the virtualization
        layer, as a list.
        """
        zvm_host = CONF.zvm_host
        hcp_base = CONF.zhcp

        url = self._xcat_url.tabdump("/zvm")
        res_dict = zvmutils.xcat_request("GET", url)

        instances = []

        with zvmutils.expect_invalid_xcat_resp_data(res_dict):
            data_entries = res_dict['data'][0][1:]
            for data in data_entries:
                l = data.split(",")
                node, hcp = l[0].strip("\""), l[1].strip("\"")
                hcp_short = hcp_base.partition('.')[0]

                # zvm host and zhcp are not included in the list
                if (hcp.upper() == hcp_base.upper() and
                        node.upper() not in (zvm_host.upper(),
                        hcp_short.upper(), CONF.zvm_xcat_master.upper())):
                    instances.append(node)

        return instances

    def is_powered_off(self, instance_name):
        """Return True if the instance is powered off."""
        return self._check_power_stat(instance_name) == 'off'

    def _check_power_stat(self, instance_name):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s', instance_name)
        res_dict = self._power_state(instance_name, "GET", "stat")

        @zvmutils.wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        power_stat = _get_power_string(res_dict)
        return power_stat

    def _delete_userid(self, url):
        try:
            zvmutils.xcat_request("DELETE", url)
        except Exception as err:
            emsg = err.format_message()
            LOG.debug("error emsg in delete_userid: %s", emsg)
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 4")):
                # zVM user definition not found, delete xCAT node directly
                self.delete_xcat_node()
            else:
                raise

    def delete_userid(self, instance_name, zhcp_node):
        """Delete z/VM userid for the instance.This will remove xCAT node
        at same time.
        """
        # Versions of xCAT that do not understand the instance ID and
        # request ID will silently ignore them.
        url = zvmutils.get_xcat_url().rmvm('/' + instance_name)

        try:
            self._delete_userid(url)
        except Exception as err:
            emsg = err.format_message()
            if (emsg.__contains__("Return Code: 400") and
               (emsg.__contains__("Reason Code: 16") or
                emsg.__contains__("Reason Code: 12"))):
                self._delete_userid(url)
            else:
                LOG.debug("exception not able to handle in delete_userid "
                          "%s", self._name)
                raise err
        except Exception as err:
            emsg = err.format_message()
            if (emsg.__contains__("Invalid nodes and/or groups") and
                    emsg.__contains__("Forbidden")):
                # Assume neither zVM userid nor xCAT node exist in this case
                return
            else:
                raise err

    def delete_xcat_node(self, instance_name):
        """Remove xCAT node for z/VM instance."""
        url = self._xcat_url.rmdef('/' + instance_name)
        try:
            zvmutils.xcat_request("DELETE", url)
        except Exception as err:
            if err.format_message().__contains__("Could not find an object"):
                # The xCAT node not exist
                return
            else:
                raise err

    def capture_instance(self, instance_name):
        """Invoke xCAT REST API to capture a instance."""
        LOG.info('Begin to capture instance %s' % instance_name)
        url = self._xcat_url.capture()
        nodename = instance_name
        image_id = str(uuid.uuid1())
        image_uuid = image_id.replace('-', '_')
        profile = image_uuid
        body = ['nodename=' + nodename,
                'profile=' + profile]
        res = zvmutils.xcat_request("POST", url, body)
        LOG.info(res['info'][3][0])
        image_name = res['info'][3][0].split('(')[1].split(')')[0]
        return image_name

    def delete_image(self, image_name):
        """"Invoke xCAT REST API to delete a image."""
        url = self._xcat_url.rmimage('/' + image_name)
        try:
            zvmutils.xcat_request("DELETE", url)
        except zvmutils.ZVMException:
            LOG.warn(("Failed to delete image file %s from xCAT") %
                    image_name)

        url = self._xcat_url.rmobject('/' + image_name)
        try:
            zvmutils.xcat_request("DELETE", url)
        except zvmutils.ZVMException:
            LOG.warn(("Failed to delete image definition %s from xCAT") %
                    image_name)
        LOG.info('Image %s successfully deleted' % image_name)


_VOLUMEOPS = None


def _get_volumeops():
    global _VOLUMEOPS
    if _VOLUMEOPS is None:
        _VOLUMEOPS = VOLUMEOps()
    return _VOLUMEOPS


class VOLUMEOps(object):

    def __init__(self):
        cwd = os.getcwd()
        self._zvm_volumes_file = os.path.join(cwd, const.ZVM_VOLUMES_FILE)
        if not os.path.exists(self._zvm_volumes_file):
            LOG.debug("z/VM volume management file %s does not exist, "
            "creating it." % self._zvm_volumes_file)
            try:
                os.mknod(self._zvm_volumes_file)
            except Exception as err:
                msg = ("Failed to create the z/VM volume management file, "
                       "error: %s" % str(err))
                raise zvmutils.ZVMException(msg)

    def _generate_vdev(self, base, offset=1):
        """Generate virtual device number based on base vdev.

        :param base: base virtual device number, string of 4 bit hex.
        :param offset: offset to base, integer.

        :output: virtual device number, string of 4 bit hex.
        """
        vdev = hex(int(base, 16) + offset)[2:]
        return vdev.rjust(4, '0')

    def get_free_mgr_vdev(self):
        """Get a free vdev address in volume_mgr userid

        Returns:
        :vdev:   virtual device number, string of 4 bit hex
        """
        vdev = CONF.volume_vdev_start
        if os.path.exists(self._zvm_volumes_file):
            volumes = []
            with open(self._zvm_volumes_file, 'r') as f:
                volumes = f.readlines()
            if len(volumes) >= 1:
                last_line = volumes[-1]
                last_vdev = last_line.strip().split(" ")[0]
                vdev = self._generate_vdev(last_vdev)
                LOG.debug("last_vdev used in volumes file: %s,"
                          " return vdev: %s", last_vdev, vdev)
            else:
                LOG.debug("volumes file has no vdev defined. ")
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)
        return vdev

    def get_free_vdev(self, userid):
        """Get a free vdev address in target userid

        Returns:
        :vdev:   virtual device number, string of 4 bit hex
        """
        vdev = CONF.volume_vdev_start
        if os.path.exists(self._zvm_volumes_file):
            volumes = []
            with open(self._zvm_volumes_file, 'r') as f:
                volumes = f.readlines()
            max_vdev = ''
            for volume in volumes:
                volume_info = volume.strip().split(' ')
                attached_userid = volume_info[2]
                curr_vdev = volume_info[3]
                if (attached_userid == userid) and (
                    (max_vdev == '') or (
                        int(curr_vdev, 16) > int(max_vdev, 16))):
                    max_vdev = curr_vdev
            if max_vdev != '':
                vdev = self._generate_vdev(max_vdev)
                LOG.debug("max_vdev used in volumes file: %s,"
                              " return vdev: %s", max_vdev, vdev)
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)
        LOG.debug("Final link address in target VM: %s", vdev)
        return vdev

    def get_volume_info(self, uuid):
        """Get the volume status from the volume management file

        Input parameters:
        :uuid: the uuid of the volume

        Returns a dict containing:
        :uuid:   the volume uuid, it's also the vdev in volume_mgr_userid
        :status: the status of the volume, one of the const.ZVM_VOLUME_STATUS
        :userid: the userid to which the volume belongs to
        :vdev:   the vdev of the volume in target vm
        """
        volume_info = {}
        if os.path.exists(self._zvm_volumes_file):
            volumes = []
            with open(self._zvm_volumes_file, 'r') as f:
                volumes = f.readlines()
            for volume in volumes:
                info = volume.strip().split(" ")
                if info[0] == uuid:
                    volume_info['uuid'] = info[0]
                    volume_info['status'] = info[1]
                    volume_info['userid'] = info[2]
                    volume_info['vdev'] = info[3]
                    break
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)
        return volume_info

    def add_volume_info(self, volinfo):
        """Add one new volume in the z/VM volume management file

        Input parameters:
        a string containing the volume info string: uuid status userid vdev
        """
        if os.path.exists(self._zvm_volumes_file):
            with open(self._zvm_volumes_file, 'a') as f:
                f.write(volinfo + '\n')
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)

    def delete_volume_info(self, uuid):
        """Delete the volume from the z/VM volume management file

        Input parameters:
        :uuid: uuid of the volume to be deleted
        """
        if os.path.exists(self._zvm_volumes_file):
            cmd = ("grep -i \"^%(uuid)s\" %(file)s") % {'uuid': uuid,
                   'file': self._zvm_volumes_file}
            status_lines = commands.getstatusoutput(cmd)[1].split("\n")
            if len(status_lines) != 1:
                msg = ("Found %(count) line status for volume %(uuid)s."
                       ) % {'count': len(status_lines), 'uuid': uuid}
                raise zvmutils.ZVMException(msg)
            # Delete the volume status line
            cmd = ("sed -i \'/^%(uuid)s.*/d\' %(file)s"
                   ) % {'uuid': uuid, 'file': self._zvm_volumes_file}
            LOG.debug("Deleting volume status, cmd: %s" % cmd)
            commands.getstatusoutput(cmd)
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)

    def update_volume_info(self, volinfo):
        """Update volume info in the z/VM volume management file

        Input parameters:
        a string containing the volume info string: uuid status userid vdev
        """
        if os.path.exists(self._zvm_volumes_file):
            uuid = volinfo.split(' ')[0]
            # Check whether there are multiple lines correspond to this uuid
            cmd = ("grep -i \"^%(uuid)s\" %(file)s") % {'uuid': uuid,
                   'file': self._zvm_volumes_file}
            status_lines = commands.getstatusoutput(cmd)[1].split("\n")
            if len(status_lines) != 1:
                msg = ("Found %(count) line status for volume %(uuid)s."
                       ) % {'count': len(status_lines), 'uuid': uuid}
                raise zvmutils.ZVMException(msg)
            # Write the new status
            cmd = ("sed -i \'s/^%(uuid)s.*/%(new_line)s/g\' %(file)s"
                   ) % {'uuid': uuid, 'new_line': volinfo,
                   'file': self._zvm_volumes_file}
            LOG.debug("Updating volume status, cmd: %s" % cmd)
            commands.getstatusoutput(cmd)
        else:
            msg = ("Cann't find z/VM volume management file")
            raise zvmutils.ZVMException(msg)
