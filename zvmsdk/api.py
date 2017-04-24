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
from zvmsdk import networkops


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self.vmops = vmops._get_vmops()
        self.networkops = networkops._get_networkops()

    def power_on(self, vm_id):
        self.vmops.power_on(vm_id)

    def get_power_state(self, vm_id):
        return self.vmops.get_power_state(vm_id)

    def clean_mac_switch_host(self, node_name):
        return self.clean_mac_switch_host(node_name)

    def clean_mac_switch(self, node_name):
        return self.clean_mac_switch(node_name)
