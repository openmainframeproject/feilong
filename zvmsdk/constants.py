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

import types


HYPERVISOR_TYPE = 'zvm'
ARCHITECTURE = 's390x'
ALLOWED_VM_TYPE = 'zLinux'
PROV_METHOD = 'netboot'
ZVM_USER_DEFAULT_PRIVILEGE = 'G'
CONFIG_DRIVE_FORMAT = 'tgz'
DEFAULT_EPH_DISK_FMT = 'ext3'
DISK_FUNC_NAME = 'setupDisk'

RINV_HOST_KEYWORDS = {
    "zvm_host": "z/VM Host:",
    "zhcp": "zHCP:",
    "cec_vendor": "CEC Vendor:",
    "cec_model": "CEC Model:",
    "hypervisor_os": "Hypervisor OS:",
    "hypervisor_name": "Hypervisor Name:",
    "architecture": "Architecture:",
    "lpar_cpu_total": "LPAR CPU Total:",
    "lpar_cpu_used": "LPAR CPU Used:",
    "lpar_memory_total": "LPAR Memory Total:",
    "lpar_memory_used": "LPAR Memory Used:",
    "lpar_memory_offline": "LPAR Memory Offline:",
    "ipl_time": "IPL Time:",
    }

DISKPOOL_KEYWORDS = {
    "disk_total": "Total:",
    "disk_used": "Used:",
    "disk_available": "Free:",
    }

SET_VSWITCH_KEYWORDS = ["grant_userid", "user_vlan_id",
                        "revoke_userid", "real_device_address",
                        "port_name", "controller_name",
                        "connection_value", "queue_memory_limit",
                        "routing_value", "port_type", "persist",
                        "gvrp_value", "mac_id", "uplink",
                        "nic_userid", "nic_vdev",
                        "lacp", "interval", "group_rdev",
                        "iptimeout", "port_isolation", "promiscuous",
                        "MAC_protect", "VLAN_counters"]

ZVM_VOLUMES_FILE = 'zvm_volumes'
ZVM_VOLUME_STATUS = ['free', 'in-use']
VOLUME_MULTI_PASS = 'MULTI'

POWER_STATE_ON = u'on'
POWER_STATE_OFF = u'off'

DATABASE_VOLUME = 'sdk_volume.sqlite'
DATABASE_NETWORK = 'sdk_network.sqlite'
DATABASE_GUEST = 'sdk_guest.sqlite'
DATABASE_IMAGE = 'sdk_image.sqlite'

_TSTR = types.StringTypes
_TNONE = types.NoneType
_TSTR_OR_NONE = (types.StringType, types.UnicodeType, types.NoneType)
_TSTR_OR_TUNI = (types.StringType, types.UnicodeType)
_INT_OR_NONE = (int, types.NoneType)
_INT_OR_TSTR = (int, types.StringType, types.UnicodeType)
_TUSERID = 'TYPE_USERID'
# Vswitch name has same rule with userid
_TVSWNAME = _TUSERID
_TUSERID_OR_LIST = (_TUSERID, list)

IMAGE_TYPE = {
    'DEPLOY': 'netboot',
    'CAPTURE': 'staging'}

SDK_DATA_PATH = '/var/lib/zvmsdk/'
