

import os
import time

from zvmsdk import api
from zvmsdk import configdrive


sdkapi = api.SDKAPI()

def run_guest():
    """ A sample for quick_start_guest()
    """
    userid = 'cbi00004'
    image_path = '/var/lib/glance/images/e19708cf-a55b-4f97-b9d5-bab54fa6f94f'
    os_version = 'rhel7.2'
    cpu = 1
    memory = 1024
    login_password = ''
    network_info = {'ip_addr': '192.168.95.11',
                    'vswitch_name': 'xcatvsw2',
                    'vdev': '1000',
                    'mac_addr': '02:00:00:0E:11:40',
                    'gateway': '192.168.95.1',
                    'cidr': '192.168.95.0/24',
                    }
    disks_list = [{'size': '3g',
                   'is_boot_disk': True,
                   'disk_pool': 'ECKD:xcateckd'}]

    deploy_guest(userid, image_path, os_version, cpu, memory, login_password,
              network_info, disks_list)


def deploy_guest(userid, image_path, os_version, cpu, memory, login_password,
              network_info, disks_list, profile='osdflt'):
    """Deploy and provision a virtual machine.

    Input parameters:
    :userid:     USERID of the guest, no more than 8.
    :image_name:        path of the image file
    :os_version:        os version of the image file
    :cpu:               vcpu
    :memory:            memory
    :login_password:    login password
    :network_info:      dict of network info.members:
        :ip_addr:           ip address of vm
        :vswitch_name:      switch name
        :vdev:              vdev
        :mac_addr:          mac address
        :gateway:           gateway of network
        :cidr:              network CIDR
    :disks_list:            list of dikks to add.eg:
        disks_list = [{'size': '3g',
                       'is_boot_disk': True,
                       'disk_pool': 'ECKD:xcateckd'}]
    :profile:           user template; default as 'osdflt'
    """
    # Import image to zvmclient
    image_name = os.path.basename(image_path)
    full_image_name = '-'.join((os_version, 's390x-netboot',
                                image_name.replace('-', '_')))

    if not sdkapi.image_query(image_name.replace('-', '_')):
        print("Importing image %s ..." % image_name)
        import_image(image_path, os_version)

    network_interface_info = {'ip_addr': network_info['ip_addr'],
                              'nic_vdev': network_info['vdev'],
                              'gateway_v4': network_info['gateway'],
                              'cidr': network_info['cidr']}

    # Prepare network configuration file to inject into vm
    transportfiles = configdrive.create_config_drive(userid,
                                         network_interface_info, os_version)

    # Start time
    spawn_start = time.time()

    # Create vm in zVM
    sdkapi.guest_create(userid, cpu, memory,
                        disks_list, profile)

    # Setup network for vm
    sdkapi.guest_create_nic(userid,
                            mac_addr=network_info['mac_addr'],
                            ip_addr=network_info['ip_addr'])

    # Couple nic to vswitch
    vdev = network_info['vdev']
    vswitch_name = network_info['vswitch_name']
    sdkapi.vswitch_grant_user(vswitch_name, userid)
    sdkapi.guest_nic_couple_to_vswitch(userid, vdev,
                                       vswitch_name)

    # Deploy image on vm
    sdkapi.guest_deploy(userid, full_image_name, transportfiles)

    # Power on the vm, then put MN's public key into vm
    sdkapi.guest_start(userid)

    # End time
    spawn_time = time.time() - spawn_start
    print "Guest vm %s spawned succeeded in %s seconds" % (userid, spawn_time)


def terminate_guest(userid):
    """Destroy a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """

    guest_info = sdkapi.guest_get_info(userid)
    if guest_info['power_state'] == 'on':
        print "Destroying guest %s." % userid
    else:
        print "Node %s is powered off." % userid

    # TODO: clean mac vswitch host ?

    # Delete guest
    sdkapi.guest_delete(userid)


def describe_guest(userid):
    """Get virtual machine basic information.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """

    inst_info = sdkapi.guest_get_info(userid)
    return inst_info


def start_guest(userid):
    """Power on a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    sdkapi.guest_start(userid)


def stop_guest(userid):
    """Shutdown a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    sdkapi.guest_start(userid)


def capture_guest(userid):
    """Caputre a virtual machine image.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8

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

def import_image(image_path, os_version, remote_host=None):
    """Import image.

    :param image_path: image path
    :param os_version: OS version of the image
    :param remote_host: remote access through SSH

    Examples:
    1. import image from local file system
        import_image("/home/test/images/image_file.img", "rhel72")
    2. import image from remote host
        import_image("/home/test/images/image_file.img", "rhel72",
                     "test@1.1.1.1")
    """
    image_url = ''.join(('file://', image_path))
    sdkapi.image_import(image_url, {'os_version': os_version},
                        remote_host)
