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


CONF = config.CONF


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self._vmops = vmops.get_vmops()
        self._hostops = hostops.get_hostops()
        self._networkops = networkops.get_networkops()

    def power_on(self, vm_id):
        """Power on a virtual machine."""
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
        """Return the names of all the VMs known to the virtualization
        layer, as a list.
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

    def couple_nic_to_vswitch(self, vswitch_name, switch_port_name,
                              zhcp, userid, dm=True, immdt=True):
        """ Couple nic device to specified vswitch.
        :param vswitch_name: the name of the vswitch
        :param switch_port_name: the interface id
        :param zhcp: the zhcp node name
        :param userid: the user's name who owns the port
        :param dm: whether to change the user directory entry
        :param immdt: wehther to take effect in active configuration
        """
        self._networkops.couple_nic_to_vswitch(vswitch_name, switch_port_name,
                                               zhcp, userid, dm, immdt)

    def uncouple_nic_from_vswitch(self, vswitch_name, switch_port_name,
                                  zhcp, userid, dm=True, immdt=True):
        """ Couple nic device to specified vswitch.
        :param vswitch_name: the name of the vswitch
        :param switch_port_name: the interface id
        :param zhcp: the zhcp's node name
        :param userid: the user's name who owns the port
        :param dm: whether to change the user directory entry
        :param immdt: wehther to take effect in active configuration
        """
        self._networkops.uncouple_nic_from_vswitch(vswitch_name,
                                                   switch_port_name,
                                                   zhcp, userid, dm, immdt)

    def get_admin_created_vsw(self):
        """ Get the vswitch which is created by the admin."""
        self._networkops.get_admin_created_vsw()

    def add_vswitch(self, zhcp, name, rdev,
                    controller='*', connection=1,
                    queue_mem=8, router=0, network_type=2, vid=0,
                    port_type=1, update=1, gvrp=2, native_vid=1):
        """ Create vswitch.
        :param zhcp: the zhcp's node name
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
                       configuration file
        :param gvrp: 0-unspecified 1-gvrp 2-nogvrp
        :param native_vid: the native vlan id
        """
        self._networkops.add_vswitch(zhcp, name, rdev,
                                     controller, connection, queue_mem,
                                     router, network_type, vid,
                                     port_type, update, gvrp, native_vid)
