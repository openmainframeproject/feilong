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


HYPERVISOR_TYPE = 'zvm'
ARCHITECTURE = 's390x'
ALLOWED_VM_TYPE = 'zLinux'
XCAT_MGT = 'zvm'
PROV_METHOD = 'netboot'
ZVM_XCAT_GROUP = 'zvm'
ZVM_USER_DEFAULT_PRIVILEGE = 'G'
CONFIG_DRIVE_FORMAT = 'tgz'
DEFAULT_EPH_DISK_FMT = 'ext3'
DISK_FUNC_NAME = 'setupDisk'

XCAT_RINV_HOST_KEYWORDS = {
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

XCAT_DISKPOOL_KEYWORDS = {
    "disk_total": "Total:",
    "disk_used": "Used:",
    "disk_available": "Free:",
    }

XCAT_RESPONSE_KEYS = ('info', 'data', 'node', 'errorcode', 'error')

ZVM_VOLUMES_FILE = 'zvm_volumes'
ZVM_VOLUME_STATUS = ['free', 'in-use']
VOLUME_MULTI_PASS = 'MULTI'
