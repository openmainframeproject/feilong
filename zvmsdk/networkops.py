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

    def create_nic(self, vm_id, vdev=None, nic_id=None,
                   mac_addr=None, ip_addr=None, active=False,
                   persist=True):
        self.zvmclient.create_nic(vm_id, vdev=vdev, nic_id=nic_id,
                                  mac_addr=mac_addr, ip_addr=ip_addr,
                                  active=active, persist=persist)

    def get_vm_nic_vswitch_info(self, vm_id):
        return self.zvmclient.get_vm_nic_vswitch_info(vm_id)

    def get_vswitch_list(self):
        return self.zvmclient.get_vswitch_list()

    def couple_nic_to_vswitch(self, vswitch_name, nic_vdev,
                              userid, persist=True):
        self.zvmclient.couple_nic_to_vswitch(vswitch_name, nic_vdev,
                                             userid, persist)

    def uncouple_nic_from_vswitch(self, vswitch_name, nic_vdev,
                                  userid, persist=True):
        self.zvmclient.uncouple_nic_from_vswitch(vswitch_name,
                                                 nic_vdev,
                                                 userid, persist)

    def add_vswitch(self, name, rdev,
                    controller, connection,
                    queue_mem, router, network_type, vid,
                    port_type, update, gvrp, native_vid):
        self.zvmclient.add_vswitch(name, rdev,
                                   controller, connection, queue_mem,
                                   router, network_type, vid,
                                   port_type, update, gvrp, native_vid)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        self.zvmclient.grant_user_to_vswitch(vswitch_name, userid)

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        self.zvmclient.revoke_user_from_vswitch(vswitch_name, userid)

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        self.zvmclient.set_vswitch_port_vlan_id(vswitch_name, userid, vlan_id)

    def update_nic_definition(self, user_id, nic_vdev, mac, switch_name):
        self.zvmclient.update_nic_definition(user_id, nic_vdev, mac,
                                             switch_name)

    def set_vswitch(self, vswitch_name, **kwargs):
        self.zvmclient.set_vswitch(vswitch_name, **kwargs)

    def delete_vswitch(self, vswitch_name, update=1):
        self.zvmclient.delete_vswitch(vswitch_name, update)
