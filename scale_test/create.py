#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

"""
Sample code that invokes SDKAPI.
"""

import os
import sys
import time

from zvmconnector import connector


# Guest properties
GUEST_USERID = ''
GUEST_PROFILE = 'osdflt'
GUEST_VCPUS = 1
GUEST_MEMORY = 1024         # in megabytes
GUEST_ROOT_DISK_SIZE = 3    # in gigabytes
DISK_POOL = 'ECKD:POOL3390'

# Image properties
IMAGE_PATH = '/data/rhel72eckd.img'
IMAGE_OS_VERSION = 'rhel7.2'

# Network properties
GUEST_IP_ADDR = '192.168.222.200'
GATEWAY = '192.168.222.1'
CIDR = '192.168.222.0/24'
VSWITCH_NAME = 'xcatvsw2'


sdk_client = connector.ZVMConnector(connection_type='rest', port='8080')


def terminate_guest(userid):
    """Destroy a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    res = sdk_client.send_request('guest_delete', userid)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_delete: %s" % res)


def describe_guest(userid):
    """Get virtual machine basic information.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """

    inst_info = sdk_client.send_request('guest_get_info', userid)
    return inst_info


def start_guest(userid):
    """Power on a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    sdk_client.send_request('guest_start', userid)


def stop_guest(userid):
    """Shutdown a virtual machine.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8
    """
    sdk_client.send_request('guest_start', userid)


def capture_guest(userid):
    """Caputre a virtual machine image.

    Input parameters:
    :userid:   USERID of the guest, last 8 if length > 8

    Output parameters:
    :image_name:      Image name that captured
    """
    # check power state, if down, start it
    ret = sdk_client.send_request('guest_get_power_state', userid)
    power_status = ret['output']
    if power_status == 'off':
        sdk_client.send_request('guest_start', userid)
        # TODO: how much time?
        time.sleep(1)

    # do capture
    image_name = 'image_captured_%03d' % (time.time() % 1000)
    res = sdk_client.send_request('guest_capture', userid, image_name,
                                  capture_type='rootonly', compress_level=6)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_capture: %s" % res)

    return image_name


def import_image(image_path, os_version):
    """Import image.

    Input parameters:
    :image_path:      Image file path
    :os_version:      Operating system version. e.g. rhel7.2
    """
    image_name = os.path.basename(image_path)

    image_info = sdk_client.send_request('image_query', imagename=image_name)
    if image_info and 'overallRC' in image_info and image_info['overallRC']:
        print("Importing image %s ..." % image_name)
        url = 'file://' + image_path
        res = sdk_client.send_request('image_import', image_name, url,
                                      {'os_version': os_version})
        if res and 'overallRC' in res and res['overallRC']:
            print("Error in image_import: %s" % res)


def delete_image(image_name):
    """Delete image.

    Input parameters:
    :image_name:      Image name that defined in xCAT image repo
    """
    res = sdk_client.send_request('image_delete', image_name)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in delete_image: %s" % res)


def _run_guest(userid, image_path, os_version, profile,
                 cpu, memory, network_info, disks_list):
    """Deploy and provision a virtual machine.

    Input parameters:
    :userid:            USERID of the guest, no more than 8.
    :image_name:        path of the image file
    :os_version:        os version of the image file
    :profile:           profile of the userid
    :cpu:               the number of vcpus
    :memory:            memory
    :network_info:      dict of network info.members:
        :ip_addr:           ip address of vm
        :gateway:           gateway of net
        :vswitch_name:      switch name
        :cidr:              CIDR
    :disks_list:            list of disks to add.eg:
        disks_list = [{'size': '3g',
                       'is_boot_disk': True,
                       'disk_pool': 'ECKD:xcateckd'}]
    """
    # Import image if not exists
    import_image(image_path, os_version)

    # Start time
    spawn_start = time.time()

    # Create userid
    print("Creating userid %s ..." % userid)
    res = sdk_client.send_request('guest_create', userid, cpu, memory,
                                  disk_list=disks_list,
                                  user_profile=profile)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_create: %s" % res)

    deploy_start = time.time()
    create_time = deploy_start - spawn_start
    print("%s create takes %s seconds" % (userid, create_time))

    # Deploy image to root disk
    image_name = os.path.basename(image_path)
    print("Deploying %s to %s ..." % (image_name, userid))
    res = sdk_client.send_request('guest_deploy', userid, image_name)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_deploy: %s" % res)

    network_create = time.time()
    deploy_time = network_create - deploy_start
    print("%s deploy takes %s seconds" % (userid, deploy_time))

    # Create network device and configure network interface
    res = sdk_client.send_request('guest_create_network_interface', userid,
                                  os_version, [network_info])
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_create_network_interface: %s" % res)

    res = sdk_client.send_request('guest_nic_couple_to_vswitch', userid,
                                  '1000', network_info['vswitch_name'])
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_nic_couple_to_vswitch: %s" % res)

    res = sdk_client.send_request('vswitch_grant_user',
                                  network_info['vswitch_name'],
                                  userid)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in vswitch_grant_user: %s" % res)

    guest_start = time.time()
    network_time = guest_start - network_create
    print("%s configure network %s seconds" % (userid, network_time))

    # Power on the vm
    print("Starting guest %s" % userid)
    sdk_client.send_request('guest_start', userid)
    if res and 'overallRC' in res and res['overallRC']:
        print("Error in guest_start: %s" % res)

    # End time
    spawn_time = time.time() - spawn_start
    print("%s test completed in %s seconds" % (userid, spawn_time))


def run_guest():
    """ A sample for quick deploy and start a virtual guest."""
    network_info = {'ip_addr': GUEST_IP_ADDR,
         'gateway_addr': GATEWAY,
         'cidr': CIDR,
         'vswitch_name': VSWITCH_NAME}
    disks_list = [{'size': '%ig' % GUEST_ROOT_DISK_SIZE,
                   'is_boot_disk': True,
                   'disk_pool': DISK_POOL}]

    _run_guest(GUEST_USERID, IMAGE_PATH, IMAGE_OS_VERSION, GUEST_PROFILE,
               GUEST_VCPUS, GUEST_MEMORY, network_info, disks_list)


def main():
    if len(sys.argv) != 2:
        print('need param for guest name')
        exit(1)

    global GUEST_USERID
    GUEST_USERID = sys.argv[1]
    print('create %s' % GUEST_USERID)
    run_guest()


if __name__ == "__main__":
    main()
