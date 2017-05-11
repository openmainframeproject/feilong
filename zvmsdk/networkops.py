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

    def clean_network_resource(self, vm_id):
        self.zvmclient.clean_network_resource(vm_id)

    def get_admin_created_vsw(self):
        return self.zvmclient.get_admin_created_vsw()

    def couple_nic_to_vswitch(self, vswitch_name, switch_port_name,
                              userid, persist):
        self.zvmclient.couple_nic_to_vswitch(vswitch_name, switch_port_name,
                                             userid, persist)

    def uncouple_nic_from_vswitch(self, vswitch_name, switch_port_name,
                                  userid, persist):
        self.zvmclient.uncouple_nic_from_vswitch(vswitch_name,
                                                 switch_port_name,
                                                 userid, persist)

    def add_vswitch(self, name, rdev,
                    controller, connection,
                    queue_mem, router, network_type, vid,
                    port_type, update, gvrp, native_vid):
        self.zvmclient.add_vswitch(name, rdev,
                                   controller, connection, queue_mem,
                                   router, network_type, vid,
                                   port_type, update, gvrp, native_vid)

    def host_get_port_list(self):
        return self.zvmclient.host_get_port_list()

    def guest_port_get_user_info(self, port_id):
        return self.zvmclient.guest_port_get_user_info(port_id)

    def host_put_user_direct_online(self):
        self.zvmclient.host_put_user_direct_online()

    def host_add_nic_to_user_direct(self, user_id, port_id,
                                    mac, switch_name):
        self.zvmclient.host_add_nic_to_user_direct(user_id,
                                                          port_id, mac,
                                                          switch_name)

    def vswitch_bound_port(self, port_id, network_type,
                           vswitch_name, vlan_id, userid):
        self.zvmclient.port_bound(port_id, network_type,
                                         vswitch_name, vlan_id, userid)

    def vswitch_unbound_port(self, port_id, vswitch_name, userid):
        self.zvmclient.port_unbound(port_id, vswitch_name, userid)

    def vswitch_update_port_info(self, port, vswitch, vlan):
        return self.zvmclient.vswitch_update_port_info(port, vswitch, vlan)
