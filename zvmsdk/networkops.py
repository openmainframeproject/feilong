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

    def create_port(self, vm_id, nic_info, ip_addr=None):
        self.zvmclient.create_port(vm_id, nic_info, ip_addr=ip_addr)

    def get_vm_nic_switch_info(self, vm_id):
        return self.zvmclient.get_vm_nic_switch_info(vm_id)
    def update_ports(self, registered_ports):
        self.zvmclient.update_ports(registered_ports)

    def clean_network_resource(self, user_id):
        self.zvmclient.clean_network_resource(user_id)

    def get_admin_created_vsw(self):
        self.zvmclient.get_admin_created_vsw()

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

    def update_nic_definition(self, user_id, port_id, mac, switch_name):
        LOG.debug("Adding NIC for %(user)s, vswitch: %(vswitch)s," +
                  " mac: %(mac)s, port_id: %(port)s",
                  {'user': user_id, 'vswitch': switch_name,
                   "mac": mac, "port": port_id})
        self.zvmclient.update_nic_definition(user_id, port_id, mac,
                                             switch_name)
