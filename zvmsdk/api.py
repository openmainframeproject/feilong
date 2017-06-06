# Copyright 2017 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from zvmsdk import vmops
from zvmsdk import hostops
from zvmsdk import config
from zvmsdk import monitor
from zvmsdk import networkops
from zvmsdk import imageops
from zvmsdk import exception


CONF = config.CONF


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self._vmops = vmops.get_vmops()
        self._hostops = hostops.get_hostops()
        self._networkops = networkops.get_networkops()
        self._imageops = imageops.get_imageops()
        self._monitor = monitor.get_monitor()

    def guest_start(self, vm_id):
        """Power on a virtual machine.

        :param vm_id: the id of the vm to be power on

        :returns: None
        """
        self._vmops.guest_start(vm_id)

    def guest_get_power_state(self, guest_id):
        """Returns power state."""
        return self._vmops.get_power_state(guest_id)

    def guest_get_info(self, guest_id):
        """Returns a dict containing:

        :param power_state: the running state, one of on | off
        :param max_mem_kb: (int) the maximum memory in KBytes allowed
        :param mem_kb: (int) the memory in KBytes used by the instance
        :param num_cpu: (int) the number of virtual CPUs for the instance
        :param cpu_time_ns: (int) the CPU time used in nanoseconds
        """
        return self._vmops.get_info(guest_id)

    def host_get_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        return self._hostops.get_info()

    def host_diskpool_get_info(self, disk_pool=CONF.zvm.disk_pool):
        """ Retrieve diskpool information.

        :returns: Dictionary describing diskpool usage info
        """
        diskpool_name = disk_pool.split(':')[1]
        return self._hostops.diskpool_get_info(diskpool_name)

    def host_list_guests(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        return self._hostops.list_guests()

    def guest_deploy(self, user_id, image_name, transportfiles=None,
                     vdev=None):
        """ Deploy the image to vm.

        :param user_id: the user id of the vm
        :param image_name: the name of image that used to deploy the vm
        :param transportfiles: the files that used to customize the vm
        :param vdev: the device that image will be deploy to

        """
        return self._vmops.guest_deploy(user_id, image_name,
                                        transportfiles, vdev)

    def guest_create_nic(self, vm_id, nic_info, ip_addr=None):
        """ Create the nic for the vm, add NICDEF record into the user direct.

        :param vm_id: the user id of the vm
        :param nic_info: the list used to contain nic info,
               including nic id and mac address
               format sample: [{'nic_id': XXX, 'mac_addr': YYY}]
        :param ip_addr: IP address of the vm

        """
        if len(nic_info) == 0:
            msg = ("no nic info is provided to create nic")
            raise exception.ZVMInvalidInput(msg)

        self._networkops.create_nic(vm_id, nic_info, ip_addr=ip_addr)

    def guest_get_nic_switch_info(self, user_id):
        """ Return the nic and switch pair for the specified vm.

        :param user_id: the user id of the vm

        :returns: Dictionary describing nic and switch info
        """
        return self._networkops.get_vm_nic_switch_info(user_id)

    def guest_get_definition_info(self, userid, **kwargs):
        """Get definition info for the specified guest vm, also could be used
        to check specific info.

        :param str userid: the user id of the guest vm
        :param dict kwargs: Dictionary used to check specific info in user
                            direct. Valid keywords for kwargs:
                            nic_coupled=<vdev>, where <vdev> is the virtual
                            device number of the nic to be checked the couple
                            status.
        :returns: Dictionary describing user direct and check info result
        :rtype: dict
        """
        return self._vmops.get_definition_info(userid, **kwargs)

    def image_import(self, image_file_path, os_version):
        """import image to z/VM according to the file path and os_version

        :param image_file_path:the absolute path for image file
        :param os_version:the os version of the image

        """
        self._imageops.image_import(image_file_path, os_version)

    def guest_create(self, userid, vcpus, memory, disk_list=[],
                     user_profile=None):
        """create a vm in z/VM

        :param userid: (str) the userid of the vm to be created
        :param vcpus: (int) amount of vcpus
        :param memory: (int) size of memory
        :param disk_list: (dict) a list of disks info for the guest, it has
               one dictionary that contain some of the below keys for each
               disk, the root disk should be the first element in the list.
               {'size': str,
               'format': str,
               'is_boot_disk': bool,
               'disk_pool': str}

               For example:
               [{'size': '1g',
               'is_boot_disk': True,
               'disk_pool': 'ECKD:eckdpool1'},
               {'size': '200000',
               'disk_pool': 'FBA:fbapool1',
               'format': 'ext3'}]
               In this case it will create one disk 0100(in case the vdev
               for root disk is 0100) with size 1g from ECKD disk pool
               eckdpool1 for guest , then set IPL 0100 in guest's user
               directory, and it will create 0101 with 200000 blocks from
               FBA disk pool fbapool1, and formated with ext3.
        :param user_profile: the profile for the guest
        """
        self._vmops.create_vm(userid, vcpus, memory, disk_list, user_profile)

    def image_get_root_disk_size(self, image_file_name):
        """Get the root disk size of the image

        :param image_file_name: the image file name in image Repository
        :returns: the disk size in units CYL or BLK
        """
        return self._imageops.image_get_root_disk_size(image_file_name)

    def guest_nic_couple_to_vswitch(self, vswitch_name, switch_port_name,
                                    userid, persist=True):
        """ Couple nic device to specified vswitch.

        :param vswitch_name: the name of the vswitch
        :param switch_port_name: the interface id
        :param userid: the user's name who owns the port
        :param persist: whether keep the change in the permanent
               configuration for the system

        """
        self._networkops.couple_nic_to_vswitch(vswitch_name, switch_port_name,
                                               userid, persist)

    def guest_nic_uncouple_from_vswitch(self, vswitch_name, switch_port_name,
                                        userid, persist=True):
        """ Couple nic device to specified vswitch.

        :param vswitch_name: the name of the vswitch
        :param switch_port_name: the interface id
        :param userid: the user's name who owns the port
        :param persist: whether keep the change in the permanent
               configuration for the system

        """
        self._networkops.uncouple_nic_from_vswitch(vswitch_name,
                                                   switch_port_name,
                                                   userid, persist)

    def vswitch_get_list(self):
        """ Get the vswitch list.

        :returns: vswitch name list
        """
        return self._networkops.get_vswitch_list()

    def vswitch_create(self, name, rdev,
                       controller='*', connection=1,
                       queue_mem=8, router=0, network_type=2, vid=0,
                       port_type=1, update=1, gvrp=2, native_vid=1):
        """ Create vswitch.

        :param name: the vswitch name
        :param rdev: the real device number
        :param controller: the vswitch's controller
        :param connection: 0-unspecified 1-Actice 2-non-Active
        :param queue_mem: the max number of megabytes on a single port
        :param router: 0-unspecified 1-nonrouter 2-prirouter
        :param network_type: 0-unspecified 1-IP 2-ethernet
        :param vid: 1-4094 for access port defaut vlan
        :param port_type: 0-unspecified 1-access 2-trunk
        :param update: 0-unspecified 1-create 2-create and add to system
               configuration file 3-add to system configuration
        :param gvrp: 0-unspecified 1-gvrp 2-nogvrp
        :param native_vid: the native vlan id

        """
        self._networkops.add_vswitch(name, rdev,
                                     controller, connection, queue_mem,
                                     router, network_type, vid,
                                     port_type, update, gvrp, native_vid)

    def image_query(self, imagekeyword=None):
        """Get the list of image names in image repository

        :param imagekeyword: The key strings that can be used to uniquely
               retrieve an image, if not specified, all image names will be
               listed

        :returns: A list that contains image names
        """
        return self._imageops.image_query(imagekeyword)

    def guest_get_console_output(self, userid):
        """Get the console output of the guest virtual machine.

        :param str userid: the user id of the vm
        :returns: console log string
        :rtype: str
        """
        return self._vmops.get_console_output(userid)

    def guest_delete(self, userid):
        """Delete guest
        :param userid: the user id of the vm

        """
        return self._vmops.delete_vm(userid)

    def guest_inspect_cpus(self, userid_list):
        """Get the cpu statistics of the guest virtual machines

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the cpu statistics of the vm
                  in the form {'UID1':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx
                  },
                  'UID2':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx
                  }
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        # parsed_uid_list = [uid.upper() for uid in userid_list]
        return self._monitor.inspect_cpus(userid_list)
