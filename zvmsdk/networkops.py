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


_NetworkOPS = None


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

    def clean_mac_switch_host(self, vm_id):
        """Clean vm records, including mac, host and switch table."""
        self.clean_mac_switch(vm_id)
        self.zvmclient.delete_host(vm_id)

    def clean_mac_switch(self, vm_id):
        """Clean vm records, including mac and switch table."""
        self.zvmclient.delete_mac(vm_id)
        self.zvmclient.delete_switch(vm_id)
