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


import six
import datetime
import time

from oslo_utils import timeutils

from zvmsdk import client as zvmclient
from zvmsdk import utils as zvmutils
from zvmsdk import config
from zvmsdk import log
from zvmsdk import exception


_NetworkOPS = None
CONF = config.CONF
LOG = log.LOG


def _get_networkops():
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

    def clean_mac_switch_host(self, node_name):
        """Clean node records, including mac, host and switch table."""
        self.clean_mac_switch(node_name)
        self.zvmclient.delete_host(node_name)

    def clean_mac_switch(self, node_name):
        """Clean node records, including mac and switch table."""
        self.zvmclient.delete_mac(node_name)
        self.zvmclient.delete_switch(node_name)
