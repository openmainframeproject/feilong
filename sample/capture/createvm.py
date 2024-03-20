#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017 IBM Corp.

from zvmconnector import connector
import os
import time

print("Setup client: client=connector.ZVMConnector('9.60.18.170', 8080)\n")
client=connector.ZVMConnector('9.60.18.170', 8080)

print("Test: send_request('vswitch_get_list')")
list = client.send_request('vswitch_get_list')
print("Result: %s\n" % list)

GUEST_USERID = 'LINUX173'
GUEST_PROFILE = 'osdflt'
GUEST_VCPUS = 1
GUEST_MEMORY = 2048
DISK_POOL = 'ECKD:POOL1'
IMAGE_PATH = '/tmp/rhel7eckd_IUCV_zvmguestconfigure.img'
IMAGE_OS_VERSION = 'rhel7.0'
GUEST_IP_ADDR = '9.60.18.173'
GATEWAY = '9.60.18.129'
CIDR = '9.60.18.128/25'
VSWITCH_NAME = 'xcatvsw2'
network_info = [{'ip_addr': GUEST_IP_ADDR, 'gateway_addr': GATEWAY, 'cidr': CIDR}]

image_name = os.path.basename(IMAGE_PATH)
url = 'file://' + IMAGE_PATH

print("Parameter list:")
print("GUEST_USERID: %s" % GUEST_USERID)
print("GUEST_PROFILE: %s" % GUEST_PROFILE)
print("GUEST_VCPUS: %s" % GUEST_VCPUS)
print("GUEST_MEMORY: %s" % GUEST_MEMORY)
print("DISK_POOL: %s" % DISK_POOL)
print("IMAGE_PATH: %s" % IMAGE_PATH)
print("IMAGE_OS_VERSION: %s" % IMAGE_OS_VERSION)
print("image_name: %s" % image_name)
print("url: %s" % url)
print("network_info: %s" % network_info)
print("-----------------------------------------------------------------------------------------------------------\n")

print("Import image: send_request('image_import', '%s', url, {'os_version': '%s'})" % (image_name, IMAGE_OS_VERSION))
info = client.send_request('image_import', image_name, url, {'os_version': IMAGE_OS_VERSION})
print('Result: %s\n' % info)

print("Get image size: send_request('image_get_root_disk_size', '%s')" % image_name)
info = client.send_request('image_get_root_disk_size', image_name)
print('Result: %s\n' % info)

size=info['output']

disks_list = [{'size': size, 'is_boot_disk': True, 'disk_pool': DISK_POOL}]
print("set disks_list: %s\n" % disks_list)

print("Create guest: send_request('guest_create', '%s', '%s', '%s', disk_list='%s', user_profile='%s')" % 
      (GUEST_USERID, GUEST_VCPUS, GUEST_MEMORY, disks_list, GUEST_PROFILE))
info = client.send_request('guest_create', GUEST_USERID, GUEST_VCPUS, GUEST_MEMORY, disk_list=disks_list, user_profile=GUEST_PROFILE)
print('Result: %s\n' % info)

print("Guest deploy: send_request('guest_deploy', '%s', '%s')" % (GUEST_USERID, image_name))
info = client.send_request('guest_deploy', GUEST_USERID, image_name)
print('Result: %s\n' % info)

print("Set network: send_request('guest_create_network_interface', '%s', '%s', '%s')" %(GUEST_USERID, IMAGE_OS_VERSION, network_info))
info = client.send_request('guest_create_network_interface', GUEST_USERID, IMAGE_OS_VERSION, network_info)
print('Result: %s\n' % info)

nic = info['output'][0]['nic_vdev']
print("Couple network: send_request('guest_nic_couple_to_vswitch', '%s', '%s', '%s')" % (GUEST_USERID, nic, VSWITCH_NAME))
info = client.send_request('guest_nic_couple_to_vswitch', GUEST_USERID, '1000', VSWITCH_NAME)
print('Result: %s\n' % info)

print("Grant user: send_request('vswitch_grant_user', '%s', '%s')" % (VSWITCH_NAME, GUEST_USERID))
info = client.send_request('vswitch_grant_user', VSWITCH_NAME, GUEST_USERID)
print('Result: %s\n' % info)

print("Check power state: send_request('guest_get_power_state', '%s')" % GUEST_USERID)
info = client.send_request('guest_get_power_state', GUEST_USERID)
print('Result: %s\n' % info)

print("Start guest: send_request('guest_start', '%s')" % GUEST_USERID)
info = client.send_request('guest_start', GUEST_USERID)
print('Result: %s\n' % info)

print("Check power state: send_request('guest_get_power_state', '%s')" % GUEST_USERID)
info = client.send_request('guest_get_power_state', GUEST_USERID)
print('Result: %s\n' % info)

print("Get user direct: send_request('guest_get_definition_info', '%s')" % GUEST_USERID)
info = client.send_request('guest_get_definition_info', GUEST_USERID)
print('Result: %s\n' % info)

print('Completed\n')

