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


from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import log


_NetworkOPS = None
CONF = config.CONF
LOG = log.LOG


def get_networkops():
    global _NetworkOPS
    if _NetworkOPS is None:
        _NetworkOPS = NetworkOPS()
    return _NetworkOPS


class NetworkOPS(object):
    """Configuration check and manage MAC address API
       oriented towards SDK driver
    """
    def __init__(self):
        self.zvmclient = zvmclient.get_zvmclient()

    def create_port(self, vm_id, nic_id, mac_addr,
                    nic_vdev=CONF.zvm.default_nic_vdev):
        LOG.debug('Nic attributes: '
                  'ID is %(id)s, address is %(address)s, '
                  'vdev is %(vdev)s',
                  {'id': nic_id, 'address': mac_addr,
                   'vdev': nic_vdev})
        self.zvmclient.create_port(vm_id, nic_id, mac_addr, nic_vdev)

    def get_vm_nic_switch_info(self, vm_id):
        return self.zvmclient.get_vm_nic_switch_info(vm_id)

    def check_nic_coupled(self, key, vm_id):
        return self.zvmclient.check_nic_coupled(key, vm_id)

    def preset_vm_network(self, vm_id, ip_addr):
        self.zvmclient.preset_vm_network(vm_id, ip_addr)

    def update_ports(self, registered_ports):
        self.zvmclient.update_ports(registered_ports)
