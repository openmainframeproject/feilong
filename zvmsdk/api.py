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


CONF = config.CONF


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self):
        self._vmops = vmops.get_vmops()
        self._hostops = hostops.get_hostops()

    def power_on(self, vm_id):
        self._vmops.power_on(vm_id)

    def get_power_state(self, vm_id):
        return self._vmops.get_power_state(vm_id)

    def get_host_info(self, host):
        """ Retrieve host information including host, memory, disk etc.
        :param host:
            the name of the host which the caller want to get resources from
        :returns: Dictionary describing resources
        """
        return self._hostops.get_host_info(host)

    def get_diskpool_info(self, host, pool=CONF.zvm.diskpool):
        """ Retrieve diskpool information.
        :param host: the name of the host which owns the diskpool
        :param pool: the name of the diskpool which the caller wants
            to get the usage info
        :returns: Dictionary describing diskpool usage info
        """
        return self._hostops.get_diskpool_info(host, pool)

    def list_vms(self):
        """Return the names of all the VMs known to the virtualization
        layer, as a list.
        """
        return self._hostops.get_vm_list()
