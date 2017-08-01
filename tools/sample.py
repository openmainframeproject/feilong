import time
from zvmsdk import api
from zvmsdk import configdrive
from zvmsdk import dist


sdkapi = api.SDKAPI()

def do_test():
    """ A sample for quick_start_guest()
    """
    userid = 'cbi00004'
    image_path = '/root/images/img/rhel72-s390x-netboot-rhel72eckd_for_test.img'
    image_meta = {'os_version': 'rhel7.2',
                  'md5sum': '51a79a3f513de59531ab92f362285628'}
    remote_host = None
    cpu = 1
    memory = 1024
    login_password = ''
    network_info = {'ip_addr': '192.168.114.12',
                    'vswitch_name': 'xcatvsw2',
                    'gateway_v4': '192.168.114.1',
                    'netmask_v4': '255.255.255.0',
                    'broadcast_v4': '192.168.0.255',
                    'vdev': '1000',
                    'nic_id': 'ce71a70c-bbf3-480e-b0f7-01a0fcbbb44c',
                    'mac_addr': '02:00:00:0E:11:40',
                    }
    disks_list = [{'size': '3g',
                   'is_boot_disk': True,
                   'disk_pool': 'ECKD:xcateckd'}]


    create_guest(userid, image_path, image_meta,
                 remote_host, cpu, memory,
                 login_password, network_info, disks_list)


def create_guest(userid, image_path, image_meta,
                 remote_host, cpu, memory,
                 login_password, network_info, disks_list):
    """Deploy and provision a virtual machine.
    Input parameters:
    :param str userid:          USERID of the guest, no more than 8.
    :param str image_name:      path of the image file
    :param str image_meta:      os version of the image file
    :param str remote_host:     dedicate where the image comes from,
            the format is userid@ip_address,eg.root@192.168.111.111
            default value is None,which means local file system
    :param int cpu:             vcpu
    :param int memory:          memory
    :param str login_password:  login password
    :param dict network_info:   dict of network info.members:
            :ip_addr:                   ip address of vm
            :gateway:                   gateway of net
            :vswitch_name:              switch name
            :vdev:                      vdev
            :nic_id:                    nic identifier
            :mac_addr:                  mac address
            refer to do_test() for example
    :param list disks_list:     list of dikks to add.
    for example:disks_list = [{'size': '3g',
                       'is_boot_disk': True,
                       'disk_pool': 'ECKD:xcateckd'}]
    """

    # Import image to zvmclient
    image_url = "file://" + image_path
    sdkapi.image_import(image_url, image_meta, remote_host)
    os_version = image_meta['os_version']
    image_file_name = image_path.split('/')[-1]
    keywords = image_file_name.split('-')[-1]
    spawn_image_exist = sdkapi.image_query(keywords)
    if not spawn_image_exist:
        print "failed to import image or image not exist."

    image_name = sdkapi.image_query(keywords)[0]

    # Get OS distribution
    dist_manager = dist.LinuxDistManager()
    linuxdist = dist_manager.get_linux_dist(os_version)()

    # Prepare network configuration file to inject into vm
    ip_addr = network_info['ip_addr']
    network_interface_info = {'ip_addr': ip_addr,
                              'nic_vdev': network_info['vdev'],
                              'gateway_v4': network_info['gateway_v4'],
                              'broadcast_v4': network_info['broadcast_v4'],
                              'netmask_v4': network_info['netmask_v4']}
    transportfiles = configdrive.create_config_drive(network_interface_info,
                                                     os_version)
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
