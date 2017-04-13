

import time

from zvmsdk import config
from zvmsdk import configdrive
from zvmsdk import log
from zvmsdk import utils as zvmutils
from zvmsdk import vmops


CONF = config.CONF
LOG = log.LOG
VMOPS = vmops._get_vmops()


def run_instance(instance_name, image_name, cpu, memory,
                 login_password, ip_addr):
    """Deploy and provision a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, no more than 8.
    :image_name:      e.g. rhel7.2-s390x-netboot-7e5_9f4e_11e6_b85d_02000b15
    :cpu:             vcpu
    :memory:          memory
    :login_password:  login password
    :ip_addr:         ip address
    """
    os_version = zvmutils.get_image_version(image_name)

    # For zVM instance, limit the maximum length of instance name to be 8
    if len(instance_name) > 8:
        msg = (("Don't support spawn vm on zVM hypervisor with instance "
            "name: %s, please change your instance name no longer than 8 "
            "characters") % instance_name)
        raise zvmutils.ZVMException(msg)

    instance_path = zvmutils.get_instance_path(CONF.zvm_host, instance_name)
    linuxdist = VMOPS._dist_manager.get_linux_dist(os_version)()
    transportfiles = configdrive.create_config_drive(ip_addr, os_version)

    spawn_start = time.time()

    # Create xCAT node and userid for the instance
    zvmutils.create_xcat_node(instance_name, CONF.zhcp)
    VMOPS.create_userid(instance_name, cpu, memory, image_name)

    # Setup network for z/VM instance
    VMOPS._preset_instance_network(instance_name, ip_addr)
    VMOPS._add_nic_to_table(instance_name, ip_addr)
    zvmutils.update_node_info(instance_name, image_name, os_version)
    zvmutils.deploy_node(instance_name, image_name, transportfiles)

    # Change vm's admin password during spawn
    zvmutils.punch_adminpass_file(instance_path, instance_name,
                                  login_password, linuxdist)
    # Unlock the instance
    zvmutils.punch_xcat_auth_file(instance_path, instance_name)

    # Power on the instance, then put MN's public key into instance
    VMOPS.power_on(instance_name)
    spawn_time = time.time() - spawn_start
    LOG.info("Instance spawned succeeded in %s seconds", spawn_time)

    return instance_name


def terminate_instance(instance_name):
    """Destroy a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    if VMOPS.instance_exists(instance_name):
        LOG.info(("Destroying instance %s"), instance_name)
        if VMOPS.is_reachable(instance_name):
            LOG.debug(("Node %s is reachable, "
                      "skipping diagnostics collection"), instance_name)
        elif VMOPS.is_powered_off(instance_name):
            LOG.debug(("Node %s is powered off, "
                      "skipping diagnostics collection"), instance_name)
        else:
            LOG.debug(("Node %s is powered on but unreachable"), instance_name)

    zvmutils.clean_mac_switch_host(instance_name)

    VMOPS.delete_userid(instance_name, CONF.zhcp)


def describe_instance(instance_name):
    """Get virtual machine basic information.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    inst_info = VMOPS.get_info(instance_name)
    return inst_info


def start_instance(instance_name):
    """Power on a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    VMOPS._power_state(instance_name, "PUT", "on")


def stop_instance(instance_name):
    """Shutdown a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    VMOPS._power_state(instance_name, "PUT", "off")


def capture_instance(instance_name):
    """Caputre a virtual machine image.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8

    Output parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    if VMOPS.get_power_state(instance_name) == "off":
        VMOPS.power_on(instance_name)

    return VMOPS.capture_instance(instance_name)


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    VMOPS.delete_image(image_name)
