import time
from zvmsdk import api
from zvmsdk import configdrive
from zvmsdk import dist


sdkapi = api.SDKAPI()

def do_test():
    """ A sample for run_instance
    """
    instance_name = 'cbi00004'
    image_path = '/root/images/img/rhel72-eckd-tempest.img'
    os_version = 'rhel7'
    cpu = 1
    memory = 1024
    login_password = ''
    network_info = {'ip_addr': '192.168.114.12',
                    'vswitch_name': 'xcatvsw2',
                    'vdev': '1000',
                    'nic_list':
                        [{'nic_id': 'ce71a70c-bbf3-480e-b0f7-01a0fcbbb44c',
                          'mac_addr': '02:00:00:0E:11:40'}]}
    disks_list = [{'size': '3g',
                   'is_boot_disk': True,
                   'disk_pool': 'ECKD:xcateckd'}]


    run_instance(instance_name, image_path, os_version,
                 cpu, memory, login_password,
                 network_info, disks_list)


def run_instance(instance_name, image_path, os_version,
                 cpu, memory, login_password,
                 network_info, disks_list):
    """Deploy and provision a virtual machine.

    Input parameters:
    :instance_name:     USERID of the instance, no more than 8.
    :image_name:        path of the image file
    :image_name:        os version of the image file
    :cpu:               vcpu
    :memory:            memory
    :login_password:    login password
    :network_info:      dict of network info.members:
        :ip_addr:           ip address of vm
        :gateway:           gateway of net
        :vswitch_name:      switch name
        :vdev:              vdev
        :nic_list:          list of NICs to add
        example refer to do_test()
    :disks_list:            list of dikks to add.eg:  
        disks_list = [{'size': '3g',
                       'is_boot_disk': True,
                       'disk_pool': 'ECKD:xcateckd'}]
    """
    # Import image to zvmclient
    image_name = sdkapi.image_import(image_path, os_version)

    # Get OS distribution
    dist_manager = dist.ListDistManager()
    linuxdist = dist_manager.get_linux_dist(os_version)()

    # Prepare network configuration file to inject into vm
    ip_addr = network_info['ip_addr']
    transportfiles = configdrive.create_config_drive(ip_addr, os_version)
    user_profile = 'osdflt'

    # Start time
    spawn_start = time.time()

    # Create vm in zVM
    sdkapi.guest_create(instance_name, cpu, memory,
                        disks_list, user_profile)

    # Setup network for vm
    nic_list = network_info['nic_list']
    sdkapi.guest_create_nic(instance_name, nic_list, ip_addr)

    # Deploy image on vm
    sdkapi.guest_deploy(instance_name, image_name, transportfiles)

    # Couple nic to vswitch
    vdev = network_info['vdev']
    vswitch_name = network_info['vswitch_name']
    # TODO: loop to process multi NICs
    mac_info = nic_list[0]['mac_addr'].split(':')
    mac = mac_info[3] + mac_info[4] + mac_info[5]
    print 'MAC value is:',mac
    sdkapi.vswitch_grant_user(vswitch_name, instance_name)
    sdkapi.guest_update_nic_definition(instance_name, vdev,
                                       mac, vswitch_name)
    # Check network ready
    result = sdkapi.guest_get_definition_info(
                                            instance_name,
                                            nic_coupled=vdev)
    print "definition info:", result
    if not result['nic_coupled']:
        print 'Network not ready in %s.' % instance_name
        return

    # Power on the instance, then put MN's public key into instance
    sdkapi.guest_start(instance_name)

    # End time
    spawn_time = time.time() - spawn_start
    print "Instance-%s pawned succeeded in %s seconds" % (instance_name,
                                                          spawn_time)


def terminate_instance(instance_name):
    """Destroy a virtual machine.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """
    
    guest_info = sdkapi.guest_get_info(instance_name)
    if guest_info['power_state'] == 'on':
        print "Destroying instance %s." % instance_name
    else:
        print "Node %s is powered off." % instance_name

    # TODO: clean mac vswitch host ?

    # Delete instance
    sdkapi.guest_delete(instance_name)


def describe_instance(instance_name):
    """Get virtual machine basic information.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8
    """

    inst_info = sdkapi.guest_get_info(instance_name)
    return inst_info


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
    sdkapi.guest_start(instance_name)


def capture_instance(instance_name):
    """Caputre a virtual machine image.

    Input parameters:
    :instance_name:   USERID of the instance, last 8 if length > 8

    Output parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    # TODO: check power state ,if down ,start

    # do capture
    pass


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    pass
