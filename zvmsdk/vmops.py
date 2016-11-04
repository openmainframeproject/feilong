import pdb
import time
import os
from log import LOG
import utils as zvmutils
import config as CONF
import constants as const
from zvmsdk.utils import ZVMException
import dist
import six
import configdrive


_VMOPS = None


def _get_vmops():
    global _VMOPS
    if _VMOPS is None:
        _VMOPS = VMOps()
    return _VMOPS

def run_instance(instance_name, image_name, cpu, memory,
                 login_password, ip_addr):
    """Deploy and provision a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, no more than 8.
    :image_name:      Image name
    :cpu:             vcpu
    :memory:          memory
    :login_password:  login password
    :ip_addr:         ip address
    """
    image_name = CONF.image_name
    # For zVM instance, limit the maximum length of instance name to be 8
    if len(instance_name) > 8:
        msg = (("Don't support spawn vm on zVM hypervisor with instance "
            "name: %s, please change your instance name no longer than 8 "
            "characters") % instance_name)
        raise ZVMException(msg)
    
    instance_path = zvmutils.get_instance_path(CONF.zvm_host, instance_name)
    os_version = CONF.os_version
    linuxdist = _get_vmops()._dist_manager.get_linux_dist(os_version)()
    transportfiles = configdrive.create_config_drive(ip_addr)
    
    spawn_start = time.time()
    
    # Create xCAT node and userid for the instance
    zvmutils.create_xcat_node(instance_name, CONF.zhcp)
    _get_vmops().create_userid(instance_name, cpu, memory, image_name)
    
    # Setup network for z/VM instance
    _get_vmops()._preset_instance_network(instance_name, ip_addr)
    _get_vmops()._add_nic_to_table(instance_name, ip_addr)
    zvmutils.update_node_info(instance_name, image_name)
    deploy_image_name = zvmutils.get_imgname_xcat(CONF.image_id)
    zvmutils.deploy_node(instance_name, deploy_image_name, transportfiles)
    
    # Change vm's admin password during spawn
    zvmutils.punch_adminpass_file(instance_path, instance_name,
                                  login_password, linuxdist)
    # Unlock the instance
    zvmutils.punch_xcat_auth_file(instance_path, instance_name)
    
    # Power on the instance, then put MN's public key into instance
    _get_vmops().power_on(instance_name)
    spawn_time = time.time() - spawn_start
    LOG.info("Instance spawned succeeded in %s seconds", spawn_time)
    
    return instance_name

def terminate_instance(instance_name):
    """Destroy a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    pass

def start_instance(instance_name):
    """Power on a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    _get_vmops()._power_state(instance_name, "PUT", "on")

def stop_instance(instance_name):
    """Shutdown a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    pass


def create_volume(volume_name, size):
    """Create a volume.

    Input parameters:
    :volume_name:     volume name
    :size:            size
    """
    pass


def delete_volume(volume_name):
    """Create a volume.

    Input parameters:
    :volume_name:     volume name
    """
    pass


def attach_volume(instance_name, volume_name):
    """Create a volume.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :volume_name:     volume name
    """
    pass


def capture_instance(instance_name, image_name):
    """Caputre a virtual machine image.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :image_name:      Image name
    """
    pass


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name
    """
    pass


def detach_volume(instance_name, volume_name):
    """Create a volume.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    :volume_name:     volume name
    """
    pass


class VMOps(object):

    def __init__(self):
        self._xcat_url = zvmutils.get_xcat_url()
                
        self._dist_manager = dist.ListDistManager()

    def _power_state(self, instance_name, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + instance_name)
        return zvmutils.xcat_request(method, url, body)

    def get_power_state(self, instance_name):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % instance_name)
        res_dict = self._power_state(instance_name, "GET", "stat")

        @zvmutils.wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        power_stat = _get_power_string(res_dict)
        return power_stat

    def update_host_status(self):
        """Refresh host stats. One compute service entry possibly
        manages several hypervisors, so will return a list of host
        status information.
        """
        host = CONF.zvm_host
        LOG.debug("Updating host status for %s", host)

        caps = []

        info = self._get_host_inventory_info(host)

        data = {'host': host,
                'allowed_vm_type': const.ALLOWED_VM_TYPE}
        data['vcpus'] = info['vcpus']
        data['vcpus_used'] = info['vcpus_used']
        data['cpu_info'] = info['cpu_info']
        data['disk_total'] = info['disk_total']
        data['disk_used'] = info['disk_used']
        data['disk_available'] = info['disk_available']
        data['host_memory_total'] = info['memory_mb']
        data['host_memory_free'] = (info['memory_mb'] -
                                    info['memory_mb_used'])
        data['hypervisor_type'] = info['hypervisor_type']
        data['hypervisor_version'] = info['hypervisor_version']
        data['hypervisor_hostname'] = info['hypervisor_hostname']
        data['supported_instances'] = [(const.ARCHITECTURE,
                                        const.HYPERVISOR_TYPE)]
        data['zhcp'] = CONF.zhcp
        data['ipl_time'] = info['ipl_time']

        caps.append(data)

        return caps
    
    def _create_config_drive(self, instance_path, instance_name,
                             image_name, injected_files, login_password,
                             commands, linuxdist):
        if const.CONFIG_DRIVE_FORMAT not in ['tgz', 'iso9660']:
            msg = (("Invalid config drive format %s") %
                   const.CONFIG_DRIVE_FORMAT)
            raise ZVMException(msg=msg)

        LOG.debug('Using config drive', instance_name)

        extra_md = {}
        extra_md['admin_pass'] = login_password

        udev_settle = linuxdist.get_znetconfig_contents()

        if len(commands) == 0:
            znetconfig = '\n'.join(('#!/bin/bash', udev_settle))
        else:
            znetconfig = '\n'.join(('#!/bin/bash', commands, udev_settle))
        znetconfig += '\nrm -rf /tmp/znetconfig.sh\n'
        # Create a temp file in instance to execute above commands
        net_cmd_file = []
        net_cmd_file.append(('/tmp/znetconfig.sh', znetconfig))  # nosec
        injected_files.extend(net_cmd_file)
        # injected_files.extend(('/tmp/znetconfig.sh', znetconfig))

        inst_md = self.instance_metadata(instance_name,
                                                 content=injected_files,
                                                 extra_md=extra_md)

        configdrive_tgz = os.path.join(instance_path, 'cfgdrive.tgz')

        LOG.debug('Creating config drive at %s', configdrive_tgz,
                  instance=instance_name)
        self.add_instance_metadata(inst_md)
        zvmutils.make_drive(configdrive_tgz, configdrive_tgz)

        return configdrive_tgz
    
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
                              ZVMException(msg='not reachable, retry'))
        
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
            self._power_state(instance_name, "PUT", "on")
        except Exception as err:
            err_str = err.format_message()
            if ("Return Code: 200" in err_str and
                    "Reason Code: 8" in err_str):
                # Instance already not active
                LOG.warning("z/VM instance %s already active", instance_name)
                return
        
    def _get_host_inventory_info(self, host):
        url = self._xcat_url.rinv('/' + host)
        inv_info_raw = zvmutils.xcat_request("GET", url)['info'][0]
        inv_keys = const.XCAT_RINV_HOST_KEYWORDS
        inv_info = zvmutils.translate_xcat_resp(inv_info_raw[0], inv_keys)
        dp_info = self._get_diskpool_info(host)

        host_info = {}

        with zvmutils.expect_invalid_xcat_resp_data(inv_info):
            host_info['vcpus'] = int(inv_info['lpar_cpu_total'])
            host_info['vcpus_used'] = int(inv_info['lpar_cpu_used'])
            host_info['cpu_info'] = {}
            host_info['cpu_info'] = {'architecture': const.ARCHITECTURE,
                                     'cec_model': inv_info['cec_model'], }
            host_info['disk_total'] = dp_info['disk_total']
            host_info['disk_used'] = dp_info['disk_used']
            host_info['disk_available'] = dp_info['disk_available']
            mem_mb = zvmutils.convert_to_mb(inv_info['lpar_memory_total'])
            host_info['memory_mb'] = mem_mb
            mem_mb_used = zvmutils.convert_to_mb(inv_info['lpar_memory_used'])
            host_info['memory_mb_used'] = mem_mb_used
            host_info['hypervisor_type'] = const.HYPERVISOR_TYPE
            verl = inv_info['hypervisor_os'].split()[1].split('.')
            version = int(''.join(verl))
            host_info['hypervisor_version'] = version
            host_info['hypervisor_hostname'] = inv_info['hypervisor_name']
            host_info['zhcp'] = inv_info['zhcp']
            host_info['ipl_time'] = inv_info['ipl_time']

        return host_info
    
    def _get_diskpool_info(self, host):
        addp = '&field=--diskpoolspace&field=' + CONF.zvm_diskpool
        url = self._xcat_url.rinv('/' + host, addp)
        res_dict = zvmutils.xcat_request("GET", url)

        dp_info_raw = res_dict['info'][0]
        dp_keys = const.XCAT_DISKPOOL_KEYWORDS
        dp_info = zvmutils.translate_xcat_resp(dp_info_raw[0], dp_keys)

        with zvmutils.expect_invalid_xcat_resp_data(dp_info):
            for k in list(dp_info.keys()):
                s = dp_info[k].strip().upper()
                if s.endswith('G'):
                    sl = s[:-1].split('.')
                    n1, n2 = int(sl[0]), int(sl[1])
                    if n2 >= 5:
                        n1 += 1
                    dp_info[k] = n1
                elif s.endswith('M'):
                    n_mb = int(s[:-1])
                    n_gb, n_ad = n_mb / 1024, n_mb % 1024
                    if n_ad >= 512:
                        n_gb += 1
                    dp_info[k] = n_gb
                else:
                    exp = "ending with a 'G' or 'M'"
                    errmsg = ("Invalid diskpool size format: %(invalid)s; "
                        "Expected: %(exp)s"), {'invalid': s, 'exp': exp}
                    LOG.error(errmsg)
                    raise ZVMException(msg=errmsg)

        return dp_info

    def create_userid(self, instance_name, cpu, memory, image_id):
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
                'imagename=%s' % image_id]
    
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
            raise ZVMException(msg=err)
        
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
            raise ZVMException(msg=errmsg)
    
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
