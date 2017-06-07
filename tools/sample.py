import time
from zvmsdk import api
from zvmsdk import config
from zvmsdk import configdrive
from zvmsdk import log
from zvmsdk import dist


CONF = config.CONF
LOG = log.LOG
sdkapi = api.SDKAPI()


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
    os_version = image_name.split('-')[0]

    # Prepare data
    dist_manager = dist.ListDistManager()
    linuxdist = dist_manager.get_linux_dist(os_version)()
    transportfiles = configdrive.create_config_drive(ip_addr, os_version)
    disks_list = [{'size': '3g', 'is_boot_disk': True, 'disk_pool': 'ECKD:xcateckd'}]
    user_profile = 'osdflt'

    spawn_start = time.time()
    # Create vm in zVM
    sdkapi.guest_create(instance_name, cpu, memory,
                        disks_list, user_profile)

    # Setup network for vm
    nic_list = [{'nic_id': 'ce71a70c-bbf3-480e-b0f7-01a0fcbbb44c',
                 'mac_addr': 'ff:ff:ff:ff:ff:ff'}]
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
    print("Instance spawned succeeded in %s seconds", spawn_time)

    return instance_name


def terminate_instance(instance_name):
    """Destroy a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    """
    power_state = sdkapi.guest_get_power_state()
    if power_state == 'on':
        LOG.info(("Destroying instance %s"), instance_name)
        if sdkapi.guest_is_reachable(instance_name):
            LOG.debug(("Node %s is reachable, "
                      "skipping diagnostics collection"), instance_name)
        else:
            LOG.debug(("Node %s is powered on but unreachable"), instance_name)
    else:
        LOG.debug(("Node %s is powered off, "
                      "skipping diagnostics collection"), instance_name)

    # TODO: clean up network data?
    """

    sdkapi.guest_delete(instance_name)


def describe_instance(instance_name):
    """Get virtual machine basic information.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    guest_info = sdkapi.guest_get_info(instance_name)
    return guest_info


def start_instance(instance_name):
    """Power on a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    sdkapi.guest_start(instance_name)


def stop_instance(instance_name):
    """Shutdown a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    sdkapi.guest_stop(instance_name)


def capture_instance(instance_name):
    """Caputre a virtual machine image.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8

    Output parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    if sdkapi.guest_get_power_state(instance_name) == "off":
        sdkapi.guest_start(instance_name)

    # return sdkapi.capture_instance(instance_name)


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    # VMOPS.delete_image(image_name)
