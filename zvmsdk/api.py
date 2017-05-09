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
