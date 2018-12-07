""" 
sample code that deploys a VM
"""

import os
import sys
import time

from zvmconnector import connector


client = connector.ZVMConnector(connection_type = 'rest', port = 8080)


def delete_guest(userid):
    """ Destroy a virtual machine.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    """
    # Check if the guest exists
    guest_list_info = client.send_request('guest_list')
    # the string 'userid' need to be coded as 'u'userid' in case of py2 interpreter
    userid_1 = (unicode(userid, "utf-8") if sys.version[0] == '2' else userid)
    
    if userid_1 not in guest_list_info['output']:
        RuntimeError("Userid %s does not exist." % userid)
       
    
    # Delete the guest
    guest_delete_info = client.send_request('guest_delete', userid)
    
    if guest_delete_info['overallRC']:
        print("\nFailed to delete guest %s." % userid)
    else:
        print("\nSucceeded to delete guest %s." % userid)
        
    
def describe_guest(userid):
    """ Get the basic information of virtual machine.
    
    Input parameters:
    :userid:    USERID of the guest, last 8 if length > 8
    """
    # Check if the guest exists
    guest_list_info = client.send_request('guest_list')
    userid_1 = (unicode(userid, "utf-8") if sys.version[0] == '2' else userid)
    
    if userid_1 not in guest_list_info['output']:
        raise RuntimeError("Guest %s does not exist!" % userid)
        
        
    guest_describe_info = client.send_request('guest_get_definition_info', userid)
    print("\nThe created guest %s's info are:\n%s\n" % 
                          (userid, guest_describe_info))


def import_image(image_path, os_version):
    """ Import the specific image.
    
    Input parameters:
    :image_path:    Image file name
    :os_version:    Operation System version. e.g. rhel7.4
    """
    image_name = os.path.basename(image_path)
    print("\nChecking if image %s exists ..." % image_name)

    image_query_info = client.send_request('image_query', imagename = image_name)
    if image_query_info['overallRC']:
        print("Importing image %s ..." % image_name)
        url = "file://" + image_path
        image_import_info = client.send_request('image_import', image_name, url, 
						{'os_version': os_version})
        if image_import_info['overallRC']:
            raise RuntimeError("Failed to import image %s! \n%s" % 
                               (image_name, image_import_info))
        else:
            print("Succeeded to import image %s " % image_name)
    else:
        print("Image %s already exists!" % image_name)
       
 
def create_guest(userid, cpu, memory, disks_list, profile):
    """ Create the userid.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    :cpu:               the number of vcpus
    :memory:            memory
    :disks_list:        list of disks to add
    :profile:           profile of the userid
    """
    # Check if the userid already exists
    guest_list_info = client.send_request('guest_list')
    userid_1 = (unicode(userid, "utf-8") if sys.version[0] == '2' else userid)
    
    if userid_1 in guest_list_info['output']:
        raise RuntimeError("Guest %s already exists!" % userid)

    # Create the guest
    print("\nCreating guest: %s ..." % userid)
    guest_create_info = client.send_request('guest_create', userid, cpu, memory, 
                                            disk_list = disks_list, 
                                            user_profile = profile)

    if guest_create_info['overallRC']:
        raise RuntimeError("Failed to create guest %s! \n%s" % 
                                            (userid, guest_create_info))
    else:
        print("Succeeded to create guest %s." % userid)
    
def deploy_guest(userid, image_name):
    """ Deploy image to root disk.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    :image_path:        Image file name
    """
    print("\nDeploying %s to %s ..." % (image_name, userid))
    guest_deploy_info = client.send_request('guest_deploy', userid, image_name)
    
    # if failed to deploy, then delete the guest
    if guest_deploy_info['overallRC']:
        print("\nFailed to deploy guest %s.\n%s" % (userid, guest_deploy_info))
        print("\nDeleting the guest %s that failed to deploy..." % userid)
        
        # call terminage_guest() to delete the guest that failed to deploy.
        delete_guest(userid)
        os._exit(0)
    else:
        print("Succeeded to deploy %s." % userid)
        
def create_network(userid, os_version, network_info):
    """ Create network device and configure network interface.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    :os_version:        os version of the image file
    :network_info:      dict of network info
    """
    print("\nConfiguring network interface for %s ..." % userid)
    network_create_info = client.send_request('guest_create_network_interface', 
                                              userid, os_version, network_info)
    
    if network_create_info['overallRC']:
        raise RuntimeError("Failed to create network for guest %s.\n%s" 
                                              % (userid, network_create_info))
    else:
        print("Succeeded to create network for guest %s." % userid)
    
    
def coupleTo_vswitch(userid, vswitch_name):
    """ Couple to vswitch.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    :network_info:      dict of network info
    """
    print("\nCoupleing to vswitch for %s ..." % userid)
    vswitch_info = client.send_request('guest_nic_couple_to_vswitch', 
                                       userid, '1000', vswitch_name)
    
    if vswitch_info['overallRC']:
        raise RuntimeError("Failed to couple to vswitch for guest %s.\n%s" 
                                               % (userid, vswitch_info))
    else:
        print("Succeeded to couple to vswitch for guest %s." % userid)
    
    
def grant_user(userid, vswitch_name):
    """ Grant user.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    :network_info:      dict of network info
    """
    print("\nGranting user %s ..." % userid)
    user_grant_info = client.send_request('vswitch_grant_user', vswitch_name, userid)
    
    if user_grant_info['overallRC']:
        raise RuntimeError("Failed to grant user %s." %userid)
    else:
        print("Succeeded to grant user %s." % userid)
    
    
def start_guest(userid):
    """ Power on the vm.
    
    Input parameters:
    :userid:            USERID of the guest, last 8 if length > 8
    """
    # Check the power state before starting guest
    power_state_info = client.send_request('guest_get_power_state', userid)
    print("\nPower state is: %s" % power_state_info['output'])
    
    # start guest
    guest_start_info = client.send_request('guest_start', userid)
    
    if guest_start_info['overallRC']:
        raise RuntimeError('Failed to start guest %s.\n%s' 
                                              % (userid, guest_start_info))
    else:
        print("Succeeded to start guest %s." % userid)
    
    # Check the power state after starting guest
    power_state_info = client.send_request('guest_get_power_state', userid)
    print("Power state is: %s" % power_state_info['output'])
    
    if guest_start_info['overallRC']:
        print("Guest_start error: %s" % guest_start_info)
    
        
def _run_guest(userid, image_path, os_version, profile, 
               cpu, memory, network_info, vswitch_name, disks_list):
    """ Deploy and provide a virtual machine.
      
    Input parameters:
    :userid:                USERID of the guest, no more than 8
    :image_path:            image file path
    :os_version:            os version of the image file
    :profile:               profile of the userid
    :cpu:                   the number of vcpus
    :memory:                memory
    :network_info:          dict of network info. Members are:
        :ip_addr:                ip address of vm
        :gateway:                gateway of network
        :cidr:                   CIDR
    :vswitch_name:          vswitch name
    :disks_list:            list of disks to add. For example:
        disks_list = [{'size': '3g', 
                        'is_boot_disk': True, 
                        'disk_pool': 'ECDK: xcateckd'}]
    """
    print("#################################### Start deploying a virtual machine ####################################")
    
    # Import image if not exists
    import_image(image_path, os_version)
    
    # Start time
    spawn_start = time.time()
    
    # Create guest
    create_guest(userid, cpu, memory, disks_list, profile)
    
    # Deploy image to root disk
    image_name = os.path.basename(image_path)
    deploy_guest(userid, image_name)
    
    # Create network device and configure network interface
    create_network(userid, os_version, network_info)
    
    # Couple to vswitch
    coupleTo_vswitch(userid, vswitch_name)
    
    # Grant user
    grant_user(userid, vswitch_name)
    
    # Power on the vm
    start_guest(userid)
    
    # End the time
    spawn_time = time.time() - spawn_start
    print("Instance-%s spawned succeeded in %s seconds" % 
          (userid, spawn_time))
    
    # Describe guest
    describe_guest(userid)


def _user_input_properties():
    """ User input the properties of guest, image, and network. """
    global GUEST_USERID
    global GUEST_PROFILE
    global GUEST_VCPUS
    global GUEST_MEMORY
    global GUEST_ROOT_DISK_SIZE
    global DISK_POOL
    global IMAGE_PATH
    global IMAGE_OS_VERSION
    global GUEST_IP_ADDR
    global GATEWAY
    global CIDR
    global VSWITCH_NAME
    global NETWORK_INFO
    global DISKS_LIST
    
    pythonVersion = sys.version[0]
    print("Your python interpreter's version is %s." % pythonVersion)
    
    if pythonVersion == '2':
        print("Input properties with string type in ''.")
    else:
        print("Input properties without ''.")

    print("#################################### Please input guest properties ####################################")
    
    GUEST_USERID = input("guest_userid = ")
    GUEST_PROFILE = input("guest_profile = ")
    GUEST_VCPUS = int(input("guest_vcpus = "))
    GUEST_MEMORY = int(input("guest_memory (in Megabytes) = "))
    GUEST_ROOT_DISK_SIZE = int(input("guest_root_disk_size (in Gigabytes) = "))
    GUEST_POOL = input("disk_pool = ")
    print("\n")

    IMAGE_PATH = input("image_path = ")
    IMAGE_OS_VERSION = input("image_os_version = ")
    print("\n")
    
    GUEST_IP_ADDR = input("guest_ip_addr = ")
    GATEWAY = input("gateway = ")
    CIDR = input("cidr = ")
    VSWITCH_NAME = input("vswitch_name = ")
    
    NETWORK_INFO = [{'ip_addr': GUEST_IP_ADDR, 'gateway_addr': GATEWAY, 'cidr': CIDR}]
    DISKS_LIST = [{'size': '%dg' % GUEST_ROOT_DISK_SIZE, 
                   'is_boot_disk': True, 
                   'disk_pool': GUEST_POOL}]

    
############################################################################# 
##              A sample for quickly deploy and start a virtual guest.       
############################################################################# 
def run_guest():
    
    # user input the properties of guest, image and network
    _user_input_properties()
    
    # run a guest
    _run_guest(GUEST_USERID, IMAGE_PATH, IMAGE_OS_VERSION, GUEST_PROFILE, 
               GUEST_VCPUS, GUEST_MEMORY, NETWORK_INFO, VSWITCH_NAME, DISKS_LIST)
    




