import six
import datetime
import time

from oslo_service import loopingcall
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
                        