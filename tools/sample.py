import time
from zvmsdk import api
from zvmsdk import config
from zvmsdk import configdrive
from zvmsdk import log
from zvmsdk import dist


CONF = config.CONF
LOG = log.LOG
sdkapi = api.SDKAPI()


def run_instance(instance_name, image_path, os_version,
                 cpu, memory, login_password, ip_addr,
                 disks_list, nic_list):
    """Deploy and provision a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, no more than 8.
    :image_name:      path of the image file
    :image_name:      os version of the image file
    :cpu:             vcpu
    :memory:          memory
    :login_password:  login password
    :ip_addr:         ip address
    :disks_list: list of root disks. eg:
    disks_list = [{'size': '3g', 'is_boot_disk': True,
                   'disk_pool': 'ECKD:xcateckd'}]

    :nic_list:        NIC info to add to instance.eg:
    nic_list = [{'nic_id': 'ce71a70c-bbf3-480e-b0f7-01a0fcbbb44c',
                 'mac_addr': '02:00:00:0E:11:40'}]
    """
    image_name = sdkapi.image_import(image_path, os_version)

    # Prepare data
    dist_manager = dist.ListDistManager()
    linuxdist = dist_manager.get_linux_dist(os_version)()
    transportfiles = configdrive.create_config_drive(ip_addr, os_version)
    user_profile = 'osdflt'

    spawn_start = time.time()
    # Create vm in zVM
    sdkapi.guest_create(instance_name, cpu, memory,
                        disks_list, user_profile)

    # Setup network for vm
    sdkapi.guest_create_nic(instance_name, nic_list, ip_addr)

    # Deploy image on vm
    sdkapi.guest_deploy(instance_name, image_name, transportfiles)

    # Check network ready
    switch_info = sdkapi.guest_get_nic_switch_info(instance_name)
    if switch_info and '' not in switch_info.values():
        for key in switch_info:
            result = sdkapi.guest_get_definition_info(
                                            instance_name,
                                            nic_coupled=key)
            if not result['nic_coupled']:
                print 'Network not ready in %s.' % instance_name
                return

    # Power on the instance, then put MN's public key into instance
    sdkapi.guest_start(instance_name)

    # End time
    spawn_time = time.time() - spawn_start
    print "Instance-%s spawned succeeded in %s seconds" % (instance_name,
                                                           spawn_time)

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
