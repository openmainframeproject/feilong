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

    def power_on(self, vm_id):
        """Power on a virtual machine.

        :param vm_id: the id of the vm to be power on

        :returns: None
        """
        self._vmops.power_on(vm_id)

    def get_power_state(self, vm_id):
        """Returns power state."""
        return self._vmops.get_power_state(vm_id)

    def get_vm_info(self, vm_id):
        """Returns a dict containing:

        :param power_state: the running state, one of on | off
        :param max_mem_kb: (int) the maximum memory in KBytes allowed
        :param mem_kb: (int) the memory in KBytes used by the instance
        :param num_cpu: (int) the number of virtual CPUs for the instance
        :param cpu_time_ns: (int) the CPU time used in nanoseconds
        """
        return self._vmops.get_info(vm_id)

    def get_host_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        return self._hostops.get_host_info()

    def get_diskpool_info(self, diskpool_name=CONF.zvm.diskpool):
        """ Retrieve diskpool information.

        :returns: Dictionary describing diskpool usage info
        """
        return self._hostops.get_diskpool_info(diskpool_name)

    def list_vms(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        return self._hostops.get_vm_list()

    def deploy_image_to_vm(self, user_id, image_name, transportfiles=None,
                           vdev=None):
        """ Deploy the image to vm.

        :param user_id: the user id of the vm
        :param image_name: the name of image that used to deploy the vm
        :param transportfiles: the files that used to customize the vm
        :param vdev: the device that image will be deploy to

        """
        return self._vmops.deploy_image_to_vm(user_id, image_name,
                                              transportfiles=None, vdev=None)

    def create_port(self, vm_id, nic_info):
        """ Create the nic for the vm.

        :param vm_id: the user id of the vm
        :param nic_info: the list used to contain nic info,
                         including nic id and mac address
                         format sample: [{'nic_id': XXX, 'mac_addr': YYY}]

        """
        if len(nic_info) == 0:
            msg = ("no nic info is provided to create port")
            raise exception.ZVMInvalidInput(msg)
            return

        nic_vdev = CONF.zvm.default_nic_vdev
        for nic_item in nic_info:
            nic_id = nic_item['nic_id']
            mac_addr = nic_item['mac_addr']
            self._networkops.create_port(vm_id, nic_id, mac_addr, nic_vdev)
            nic_vdev = str(hex(int(nic_vdev, 16) + 3))[2:]

    def preset_vm_network(self, vm_id, ip_addr):
        """ Add ip/host name for vm.

        :param vm_id: the user id of the vm
        :param ip_addr: the ip address of the vm

        """
        return self._networkops.preset_vm_network(vm_id, ip_addr)

    def get_vm_nic_switch_info(self, user_id):
        """ Return the nic and switch pair for the specified vm.

        :param user_id: the user id of the vm

        :returns: Dictionary describing nic and switch info
        """
        return self._networkops.get_vm_nic_switch_info(user_id)

    def check_nic_coupled(self, key, user_id):
        """ whether the specified nic has already been defined in a vm and
            coupled to a switch.

        :param user_id: the user id of the vm
        :param key: nic device number

        :returns: If it is defined and coupled to a switch, return True.
                  Otherwise, return False
        """
        return self._networkops.check_nic_coupled(key, user_id)

    def clean_network_resource(self, user_id):
        """Clean the network resource (mac. switch, host) for the vm.

        :param user_id: the user id of the vm

        """
        return self._networkops.clean_network_resource(user_id)

    def check_image_exist(self, image_uuid):
        """check if the image exist in z/VM.
        """
        return self._imageops.check_image_exist(image_uuid)

    def validate_vm_id(self, userid):
        return self._vmops.validate_vm_id(userid)

    def get_image_name(self, image_uuid):
        """get the osimage name in z/VM.
        """
        return self._imageops.get_image_name(image_uuid)

    def import_spawn_image(self, image_file_path, os_version):
        """import image to z/VM according to the file path and os_version

        :param image_file_path:the absolute path for image file
        :param os_version:the os version of the image

        """
        self._imageops.import_spawn_image(image_file_path, os_version)

    def create_vm(self, userid, vcpus, memory,
                  spawn_image_name, root_gb, eph_disks):
        """create a vm in z/VM

        :param userid:the userid of the vm to be created
        :param vcpus: amount of vcpus
        :param memory: size of memory
        :param root_gb: size(GB) of mdisk of the vm, if set 0, will use
        the value in configuration files(zvm.root_disk_units)
        :param eph_disks:
        :param spawn_image_name:the name in tabdump tables

        """
        self._vmops.create_vm(userid, vcpus, memory,
                              spawn_image_name, root_gb, eph_disks)

    def couple_nic_to_vswitch(self, vswitch_name, switch_port_name,
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

    def uncouple_nic_from_vswitch(self, vswitch_name, switch_port_name,
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

    def get_admin_created_vsw(self):
        """ Get the vswitch which is created by the admin."""
        self._networkops.get_admin_created_vsw()

    def add_vswitch(self, name, rdev,
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
                       configuration file, 3 add to system configuration
        :param gvrp: 0-unspecified 1-gvrp 2-nogvrp
        :param native_vid: the native vlan id
        """
        self._networkops.add_vswitch(name, rdev,
                                     controller, connection, queue_mem,
                                     router, network_type, vid,
                                     port_type, update, gvrp, native_vid)
