import time
from zvmsdk import api
from zvmsdk import configdrive
from zvmsdk import dist


sdkapi = api.SDKAPI()

def do_test():
    """ A sample for quick_start_guest()
    """
    userid = 'cbi00004'
    image_path = '/root/images/img/rhel72-eckd-tempest.img'
    os_version = 'rhel7'
    cpu = 1
    memory = 1024
    login_password = ''
    network_info = {'ip_addr': '192.168.114.12',
                    'vswitch_name': 'xcatvsw2',
                    'vdev': '1000',
                    'nic_id': 'ce71a70c-bbf3-480e-b0f7-01a0fcbbb44c',
                    'mac_addr': '02:00:00:0E:11:40',
                    }
    disks_list = [{'size': '3g',
                   'is_boot_disk': True,
                   'disk_pool': 'ECKD:xcateckd'}]


    create_guest(userid, image_path, os_version,
                 cpu, memory, login_password,
                 network_info, disks_list)


def create_guest(userid, image_path, os_version,
                 cpu, memory, login_password,
                 network_info, disks_list):
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
        :gateway:           gateway of net
        :vswitch_name:      switch name
        :vdev:              vdev
        :nic_id:            nic identifier
        :mac_addr:          mac address
        refer to do_test() for example
    :disks_list:            list of dikks to add.eg:
        disks_list = [{'size': '3g',
                       'is_boot_disk': True,
                       'disk_pool': 'ECKD:xcateckd'}]
    """
    # Import image to zvmclient
    sdkapi.image_import(image_path, os_version)
    image_file_name = image_path.split('/')[-1]
    keywords = image_file_name.split('-')[-1]
    spawn_image_exist = self._sdk_api.image_query(keywords)
    if not spawn_image_exist:
        print "failed to import image or image not exist."

    image_name = sdkapi.image_query(keywords)[0]

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
    sdkapi.guest_create(userid, cpu, memory,
                        disks_list, user_profile)

    # Setup network for vm
    sdkapi.guest_create_nic(userid, nic_id=network_info['nic_id'],
                            mac_addr=network_info['mac_addr'],
                            ip_addr=ip_addr)

    # Deploy image on vm
    sdkapi.guest_deploy(userid, image_name, transportfiles)

    # Couple nic to vswitch
    vdev = network_info['vdev']
    vswitch_name = network_info['vswitch_name']
    # TODO: loop to process multi NICs
    mac_info = network_info['mac_addr'].split(':')
    mac = mac_info[3] + mac_info[4] + mac_info[5]
    sdkapi.vswitch_grant_user(vswitch_name, userid)
    sdkapi.guest_nic_couple_to_vswitch(userid, vdev,
                                       vswitch_name)
    # Check network ready
    result = sdkapi.guest_get_definition_info(
                                            userid,
                                            nic_coupled=vdev)
    if not result['nic_coupled']:
        print 'Network not ready in %s.' % userid
        return

    # Power on the vm, then put MN's public key into vm
    sdkapi.guest_start(userid)

    # End time
    spawn_time = time.time() - spawn_start
    print "Instance-%s pawned succeeded in %s seconds" % (userid,
                                                          spawn_time)


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
