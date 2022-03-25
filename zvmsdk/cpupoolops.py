# Copyright 2022 IBM Corp.
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

import re

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils


CONF = config.CONF
LOG = log.LOG


_CPUPOOLOPS = None


LIMITTYPES = ['CAP', 'LIMIT', 'NOLIM']
CPUTYPES = ['IFL', 'CP']
DEFAULTLIMITTYPE = 'NOLIM'
DEFAULTCPUTYPE = 'IFL'

DEFINECMD = 'DEFINE RESPOOL '
DELETECMD = 'DELETE CPUPOOL '
ADDCMD = 'SCH '
REMOVECMD = 'SCH '
QUERYCMD = 'QUERY CPUPOOL '
NOPOOL = 'NOPOOL'


class CpupoolVMCPOPS(object):
    def __init__(self):
        pass

    def _validate_cpupool_name(self, name):
        if len(name) > 8 or not len(name):
            err = ("cpu pool name length must between 0 and 8, "
                   "got %s instead" % name)
            raise exception.SDKInvalidInputFormat(msg=err)

    def _validate_and_get_limittype(self, limittype):
        if limittype and limittype.upper() not in LIMITTYPES:
            err = ("limit type must be one of %s, got %s "
                   "instead" % (LIMITTYPES, limittype))
            raise exception.SDKInvalidInputFormat(msg=err)

        if not limittype:
            return DEFAULTLIMITTYPE

        return limittype

    def _validate_and_get_cputype(self, cputype):
        if cputype and cputype.upper() not in CPUTYPES:
            err = ("cpu type must be one of %s, got %s "
                   "instead" % (CPUTYPES, cputype))
            raise exception.SDKInvalidInputFormat(msg=err)

        if not cputype:
            return DEFAULTCPUTYPE

        return cputype

    def _exec_vmcp_handle_ret(self, cpcmd):
        ret, out = utils.vmcp(cpcmd)

        if ret != 0:
            raise exception.ZVMVMCPExecutionFail(msg=out)

        return out

    def create(self, pool, limittype=None, limit=None, cputype=None):
        """
        define a cpupool:

        sample:

        def resp pool1 cpu cap 1
        Resource pool POOL1 is created
        """

        self._validate_cpupool_name(pool)
        lt = self._validate_and_get_limittype(limittype)
        ct = self._validate_and_get_cputype(cputype)

        cpcmd = DEFINECMD + pool + ' CPU ' + lt + ' '
        if limit:
            cpcmd += limit + ' '

        cpcmd += 'TYPE ' + ct
        self._exec_vmcp_handle_ret(cpcmd)

    def delete(self, pool):
        cpcmd = DELETECMD + pool
        self._exec_vmcp_handle_ret(cpcmd)

    def add(self, name, pool):
        """
        Add a user to a pool

        sch sjicic94 pool1
        User SJICIC94 has been added to resource pool POOL1
        """
        cpcmd = ADDCMD + name + ' ' + pool
        self._exec_vmcp_handle_ret(cpcmd)

    def remove(self, name):
        """
        Remove a user from a pool
        sch sjicic94 nopool
        User SJICIC94 has been removed from resource pool POOL1
        """
        cpcmd = REMOVECMD + name + ' ' + NOPOOL
        self._exec_vmcp_handle_ret(cpcmd)

    def _split_cpu_pool(self, resa):
        ret = []
        for lr in resa:
            a = {}
            item = lr.strip().split()
            a['name'] = item[0]
            a['cpu'] = item[1] + ' ' + item[2]
            a['type'] = item[3]
            a['storage'] = item[4]
            a['trim'] = item[5]
            a['members'] = item[6]
            ret.append(a)

        return ret

    def get_all(self):
        """
        Return all cpu pools
        Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   IFL  NoLimit  ----       0
        POOL2CPU    1.00 Cores   IFL  NoLimit  ----       0

        Return [{
            'name':'POOL1'
        }
        """
        cpcmd = QUERYCMD
        out = self._exec_vmcp_handle_ret(cpcmd)
        resa = out.split('\n')
        resa.pop(0)

        return self._split_cpu_pool(resa)

    def get(self, pool, including_members=False):
        """
        Get members from cpupool

        q cpupool pool1 members
        Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   IFL  NoLimit  ----       1
        The following users are members of resource pool POOL1:
        SJICIC94

        q cpupool pool1 members
        Pool Name       CPU     Type  Storage  Trim Members
        POOL1       1.00 Cores   IFL  NoLimit  ----       0
        Resource pool POOL1 has no members
        """

        no_member = 'has no members'
        has_member = 'The following users are members'

        cpcmd = QUERYCMD + pool
        if including_members:
            cpcmd += ' MEMBERS'
        out = self._exec_vmcp_handle_ret(cpcmd)

        # Check whether the return string has key sentence
        if re.search(no_member, out) or re.search(has_member, out):
            # contains keywording
            pass
        elif including_members:
            # This means we want to include members but
            # no key wording find
            msg = ("Invalid vmcp output got: %s" % out)
            raise exception.ZVMVMCPExecutionFail(msg=msg)

        resa = out.split('\n')
        resa.pop(0)

        # search for keyword and put into desired array
        detail = []
        members = []
        reach_member = False
        for s in resa:
            # we reach the member key sentence
            if s.find(has_member) >= 0:
                reach_member = True
                continue

            # indicate no members
            if s.find(no_member) >= 0:
                break

            if reach_member:
                members.append(s.strip())
            else:
                detail.append(s.strip())

        detail = self._split_cpu_pool(detail)

        return detail, members

    def get_pool_from_vm(self, name):
        """
        Get whether the VM belongs to a pool

        q cpupool user sjicic94
        User SJICIC94 is not in a resource pool
        q cpupool user sjicic94
        User SJICIC94 is in resource pool POOL1
        q cpupool user ji
        HCPLMC045E JI not logged on
        """
        cpcmd = QUERYCMD + 'USER ' + name
        out = self._exec_vmcp_handle_ret(cpcmd)

        not_in_pool = 'is not in a resource pool'
        in_pool = 'is in resource pool'

        if out.find(not_in_pool) >= 0:
            return ''

        if out.find(in_pool) >= 0:
            data = out.split()
            return data[6]

        # actually we should not reach here
        return ''


class CpupoolOPS(object):
    def __init__(self):
        pass

    @staticmethod
    def ops():
        return CpupoolVMCPOPS()


def get_cpupoolops():
    global _CPUPOOLOPS
    if _CPUPOOLOPS is None:
        _CPUPOOLOPS = CpupoolOPS.ops()
    return _CPUPOOLOPS
