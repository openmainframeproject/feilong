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


_HOSTOPS = None
CONF = config.CONF
LOG = log.LOG


def get_hostops():
    global _HOSTOPS
    if _HOSTOPS is None:
        _HOSTOPS = HOSTOps()
    return _HOSTOPS


class HOSTOps(object):

    def __init__(self):
        self._zvmclient = zvmclient.get_zvmclient()

    def get_host_info(self, host):
        return self._zvmclient.get_host_info(host)

    def get_diskpool_info(self, host, pool=CONF.zvm.diskpool):
        return self._zvmclient.get_diskpool_info(host, pool)

    def get_vm_list(self):
        return self._zvmclient.get_vm_list()
