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


class ComputeAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self.vmops = vmops._get_vmops()

    def power_on(self, vm_id):
        """Power on a virtual machine."""
        self.vmops.power_on(vm_id)

    def get_power_state(self, vm_id):
        """Returns power state."""
        return self.vmops.get_power_state(vm_id)

    def get_vm_info(self, vm_id):
        """Returns a dict containing:
        :param power_state: the running state, one of on | off
        :param max_mem_kb: (int) the maximum memory in KBytes allowed
        :param mem_kb: (int) the memory in KBytes used by the instance
        :param num_cpu: (int) the number of virtual CPUs for the instance
        :param cpu_time_ns: (int) the CPU time used in nanoseconds
        """
        return self.vmops.get_info(vm_id)
