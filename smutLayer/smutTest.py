#!/usr/bin/env python
# Test logic for Systems Management Ultra Thin Layer
#
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

import argparse
import os
import re
import sys
import subprocess
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile

from smut import SMUT
from ReqHandle import ReqHandle

version = '1.0.0'         # Version of this script

longstring = '1' * 4096

"""
The following dictionary contains keys and values used as substitution
in the requests that are processed. Replaceable values are identified
in the requests by '<<<' and '>>>'.  The key within the '<<<' and '>>>'
is in the subs dictionary.
"""
subs = {
    '<<<safeID>>>': 'someid',           # An existing userid that can be
                                        #   started and stopped
    '<<<unsafePre>>>': 'STUS',          # A prefix for a userid that gets
                                        #   created and destroyed.  Tests
                                        #   add to the prefix to get an id.
    '<<<horribleID1>>>': 'g[][325$$$',  # A userid that makes SMAPI cry
                                        #   and beg for a swift death
    '<<<consoleID>>>': 'cons',          # An existing userid who has
                                        #   SP CONS * START in its profile or
                                        #   directory
    '<<<migrID>>>': 'someid',           # An existing userid that can be
                                        #   migrated
    '<<<unmigrID>>>': 'unmgr',          # An existing userid that cannot be
                                        #   migrated
    '<<<migrDest>>>': 'zvmhost',        # A z/VM host for migration into it
    '<<<pw>>>': 'password',             # password
    '<<<vmSize>>>': '2G',               # Virtual machine size
    '<<<pool3390>>>': 'POOL1',          # 3390 disk pool (keep this in
                                        #   uppercase for smutTest ease of use)
    '<<<size3390>>>': '1100',           # Size of a 3390 for system deploys
    '<<<pool9336>>>': 'POOL4',          # 9336 disk pool (keep this in
                                        # uppercase for smutTest ease of use)
    '<<<setupDisk>>>': '/opt/xcat/share/xcat/scripts/setupDisk',  # SetupDisk
    '<<<SimpleCfgFile>>>': '/install/zvm/POC/testImages/cfgdrive.tgz',
                                        # Simple tar file for the config drive
    '<<<simpleImage>>>': '/install/zvm/POC/testImages/' +
        'rhel67eckd_small_1100cyl.img',    # Small image file
    '<<<unpackScript>>>': '/opt/zthin/bin/unpackdiskimage',
                                        # Location of unpackdiskimage
    '<<<longString>>>': longstring,
}

# Add a substitution key for the userid of this system.
cmd = ["/sbin/vmcp", "query userid"]
try:
    subs['<<<localUserid>>>'] = subprocess.check_output(
        cmd,
        close_fds=True,
        stderr=subprocess.STDOUT).split()[0]
except:
    print("Could not find the userid of this system.")
    subs['<<<localUserid>>>'] = 'unknownUserid'

# Add a substitution key for the name of the aemod script that
# set the /etc/iucv_authorized_userid file to use our userid
# and create the script.
modFile = NamedTemporaryFile(delete=False)
subs['<<<aeModScript>>>'] = modFile.name

file = open(modFile.name, 'w')
file.write("#!/usr/bin/env bash\n")
file.write("echo -n $1 > /etc/iucv_authorized_userid\n")
file.close()

"""
A dictionary contains the elements needed to process a test.
This includes the following keys:
   description - Discriptive information to show when running the test.
   request     - Request to be passed to SMUT.
   out         - Input to grep to validate the output from a test.
                 Normally, this is a reqular expression.  The regular
                 expression is input to grep which scans and validates the
                 output.  If output is an empty string then the test
                 is assumed to have passed the output check.
   overallRC   - A single return code or a list of return codes to compare
                 against the overallRC property in the results.
                 If the test returns an overallRC value that matches one of
                 the specified values then it has passed the overallRC check.
   rc          - A single return code or a list of return codes.
                 If the test returns a return code that matches one of the
                 specified return codes then it has passed the
                  return code check.
   rs          - A single return code or a list of return codes.
                 If the test returns a return code that matches one of the
                 specified return codes then it has passed the
                 return code check.

Note: A test must pass all specified tests (e.g. output, rc, etc.)
      in order for the test to pass.
"""

deployTests = [
    {
        'description': "Create a simple system: <<<unsafePre>>>1",
        'request': "MakeVM <<<unsafePre>>>1 directory <<<pw>>> " +
                   "<<<vmSize>>> g --ipl 100 --profile OSDFLT",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Purge the reader",
        'request': "ChangeVM <<<unsafePre>>>1 purgerdr",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk: 100",
        'request': "ChangeVM <<<unsafePre>>>1 add3390 <<<pool3390>>> 100 " +
            "<<<size3390>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Check out the user entry",
        'request': "GetVM <<<unsafePre>>>1 directory",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Unpack the image into the disk.",
        'request': "SHELL_TEST <<<unpackScript>>> <<<unsafePre>>>1 100 " +
            "<<<simpleImage>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Punch the config drive tar file to the system.",
        'request': "ChangeVM <<<unsafePre>>>1 punchfile " +
        "<<<SimpleCfgFile>>> --class x",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Send an aemod to allow IUCV access by this system.",
        'request': "ChangeVM <<<unsafePre>>>1 aemod <<<aeModScript>>> " +
            "--invparms <<<localUserid>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on the system and wait for to OS to come up.",
        'request': "PowerVM <<<unsafePre>>>1 on --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Send a commmand to a system.",
        'request': "CmdVM <<<unsafePre>>>1 cmd pwd",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Delete a system: <<<unsafePre>>>1",
        'request': "DeleteVM <<<unsafePre>>>1 directory",
        'out': "",
        'overallRC': [0],
    },
   ]

generalTests = [
    {
        'description': "Test Help Function",
        'request': "help",
        'overallRC': [0],
    },
    {
        'description': "Test no operands => error",
        'request': "",               # Request with no parms
        'overallRC': [4],
        'rc': [4],
        'rs': [9],
    },
    {
        'description': "Test Version",
        'request': "version",
        'out': "^Version:",
        'overallRC': [0],
    },
    {
        'description': "Test unrecognized operands",
        'request': "Steve is great",
        'overallRC': [4],
        'rc': [4],
        'rs': [7],
    },
    ]

hostTests = [
    {
        'description': "Get the list of disk pools.",
        'request': "GetHost diskpoolnames",
        'overallRC': [0],
    },
    {
        'description': "Get the space for all disk pools.",
        'request': "GetHost diskpoolspace",
        'out': "Total",
        'overallRC': [0],
    },
    {
        'description': "Get the space for a specific 3390 disk pool: " +
            "<<<pool3390>>>",
        'request': "GetHost diskpoolspace <<<pool3390>>>",
        'out': "^<<<pool3390>>> Total",
        'overallRC': [0],
    },
    {
        'description': "Get the space for a specific 9336 disk pool: " +
            "<<<pool9336>>>",
        'request': "GetHost diskpoolspace <<<pool9336>>>",
        'out': "^<<<pool9336>>> Total",
        'overallRC': [0],
    },
    {
        'description': "Get the FCP Device information.",
        'request': "GetHost fcpdevices",
        'out': "^FCP device number",
        'overallRC': [0],
    },
    {
        'description': "Get the general information.",
        'request': "GetHost general",
        'out': "",
        'overallRC': [0],
    },
    ]

iucvTests = [
    {
        'description': "Send a commmand to a system.",
        'request': "CmdVM <<<safeID>>> cmd pwd",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Send an failing commmand to a system.",
        'request': "CmdVM <<<safeID>>> cmd \"echo 'bob'|grep /john/\"",
        'out': "",
        'overallRC': [2],
        'rc': [8],
        'rs': [1],
    },
                    {
        'description': "Send an unknown commmand to a system.",
        'request': "CmdVM <<<safeID>>> cmd SteveIsGreat",
        'out': "",
        'overallRC': [2],
        'rc': [8],
        'rs': [127],
    },
    ]

migrateTests = [
    {
        'description': "Get status for a specific userid that " +
            "cannot be migrated: <<<unmigrID>>>",
        'request': "migrateVM <<<unmigrID>>> status",
        'overallRC': [99],
        'rc': [99],
        'rs': [419],
    },
    {
        'description': "Get all migration status for a host with " +
            "no active migrations.",
        'request': "migrateVM <<<unmigrID>>> status --all",
        'overallRC': [99],
        'rc': [99],
        'rs': [419],
    },
    {
        'description': ("Get incoming migration status for a host " +
            "with no active migrations."),
        'request': "migrateVM <<<unmigrID>>> status --incoming",
        'overallRC': [99],
        'rc': [99],
        'rs': [419],
    },
    {
        'description': "Get outgoing migration status for a host " +
            "with no active migrations.",
        'request': "migrateVM <<<unmigrID>>> status --outgoing",
        'overallRC': [99],
        'rc': [99],
        'rs': [419],
    },
    {
        'description': "Test a system for migration: <<<unmigrID>>>",
        'request': "migrateVM <<<unmigrID>>> test --destination " +
            "<<<migrDest>>>",
        'overallRC': [99],
        'rc': [99],
        'rs': [418],
    },
    {
        'description': "Cancel a migration",
        'request': "migrateVM <<<migrID>>> cancel",
        'overallRC': [99],
        'rc': [99],
        'rs': [419],
    },
    ]

powerTests = [
    {
        'description': "Test PowerVM VERSION.",
        'request': "PowerVM version",
        'out': "^Version:",
        'overallRC': [0],
    },
    {
        'description': "'PowerVM xxx JUNK' fails",
        'request': "PowerVM xxx junk",
        'out': "",
        'overallRC': [4],
    },
    {
        'description': "Power off a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> off --wait",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Check status of powered off system.",
        'request': "PowerVM <<<safeID>>> status",
        'out': "<<<safeID>>>: off",
        'overallRC': [0],
        'rc': [0],
        'rs': [1]
    },
    {
        'description': "Check isreachable of powered off system.",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: unreachable",
        'overallRC': [0],
        'rs': [0]
    },
    {
        'description': "Power off an already powered off system.",
        'request': "PowerVM <<<safeID>>> off",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> on",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power off a system with softOff option: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> softoff",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> on",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on a system that is on but not up: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> on --wait --state up",
        'out': "<<<safeID>>>: up",
        'overallRC': [0],
    },
    {
        'description': "Check status of powered on system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> status",
        'out': "<<<safeID>>>: on",
        'overallRC': [0],
        'rc': [0],
        'rs': [0]
    },
    {
        'description': "Check isreachable of powered on system: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Pause a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> pause",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of a paused system is unreachable: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: unreachable",
        'overallRC': [0],
        'rs': [0]
    },
    {
        'description': "Unpause a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> unpause",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of an unpaused system is reachable: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Reset a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> reset --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of an unpaused system is reachable: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Reboot a system: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> reboot --wait",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Reboot a system w/o waiting for the OS to be up: " +
            "<<<safeID>>>",
        'request': "PowerVM <<<safeID>>> reboot",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Wait for the OS to come up: <<<safeID>>>",
        'request': "PowerVM <<<safeID>>> wait --state up",
        'out': "<<<safeID>>>: up",
        'overallRC': [0],
        'rs': [0]
    },
    ]

shellTests = [
    {
        'description': "Issue a successful non-Test 1-line " +
            "output related SHELL function.",
        'request': "SHELL echo \'Hurray!\'",
        'overallRC': [0],
    },
    {
        'description': "Do a successful non-Test multi-line " +
            "output related SHELL function.",
        'request': "SHELL cat /etc/hosts",
        'overallRC': [0],
    },
    {
        'description': "Do an unsuccessful non-Test related SHELL function.",
        'request': "SHELL bob",
        'overallRC': [127],
    },
    {
        'description': "Issue a successful Test related SHELL function.",
        'request': "SHELL_TEST echo \'Hurray!\'",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Issue a successful Test related SHELL function.",
        'request': "SHELL_TEST cat /etc/hosts",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Issue an unsuccessful Test related SHELL function.",
        'request': "SHELL_TEST bob",
        'out': "",
        'overallRC': [127],
    },
    ]

smapiTests = [
    {
        'description': "Directory related query w/o operands.",
        'request': "smapi <<<safeID>>> api Image_Query_DM",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Disk pool query with operands.",
        'request': "smapi <<<safeID>>> api Image_Volume_Space_Query_DM " +
            "--operands '-q' 1 '-e' 1",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Failing disk pool query with operands.",
        'request': "smapi <<<safeID>>> api Image_Volume_Space_Query_DM " +
            "--operands '-q' 4 '-e' 1",
        'out': "",
        'overallRC': [8],
        'rc': [24],
        'rs': [1018],
    },
    ]

vmLCTests = [
    {
        'description': "Create a simple system: <<<unsafePre>>>2",
        'request': "makevm <<<unsafePre>>>2 directory smapi 2g g",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify system exists: <<<unsafePre>>>2",
        'request': "smapi <<<unsafePre>>>2 api Image_Query_DM",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Delete a system: <<<unsafePre>>>2",
        'request': "deletevm <<<unsafePre>>>2 directory",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify system no longer exists: <<<unsafePre>>>2",
        'request': "smapi <<<unsafePre>>>2 api Image_Query_DM",
        'out': "",
        'overallRC': [8],
        'rc': [400],
        'rs': [4],
    },
   ]

vmModifyTests = [
    # >>>>>>>>> Create a simple system for logged off tests.
    {
        'description': "Create a simple system: <<<unsafePre>>>3",
        'request': "MakeVM <<<unsafePre>>>3 directory <<<pw>>> " +
                   "<<<vmSize>>> g --ipl 100 --profile OSDFLT",
        'out': "",
        'overallRC': [0],
    },
     {
        'description': "Add modifications to the activation engine",
        'request': 'ChangeVM <<<unsafePre>>>3 aemod <<<setupDisk>>> ' +
            '--invparms "action=addMdisk vaddr=101 filesys=ext4 ' +
            'mntdir=/mnt/ephemeral/0.0.0101"',

        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add unknown script mods to the activation engine",
        'request': 'ChangeVM <<<unsafePre>>>3 aemod BAD ' +
            '--invparms "action=addMdisk vaddr=101 filesys=ext4 ' +
            'mntdir=/mnt/ephemeral/0.0.0101"',

        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [400],
    },
    {
        'description': "Add modifications to activation engine for bad id",
        'request': 'ChangeVM BADID aemod <<<setupDisk>>> ' +
            '--invparms "action=addMdisk vaddr=101 filesys=ext4 ' +
            'mntdir=/mnt/ephemeral/0.0.0101"',

        'out': "",
        'overallRC': [4],
    },
    {
        'description': "Purge the reader: <<<unsafePre>>>3",
        'request': "ChangeVM <<<unsafePre>>>3 purgerdr",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with ext4: " +
            "<<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem ext4 " +
            "--readpw readpw --writepw writepw --multipw multipw",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with ext4: <<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with xfs: " +
            "<<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "102 100m --mode w --filesystem xfs",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with xfs: <<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 removedisk 102",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with swap: " +
            "<<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "103 100m --mode w --filesystem swap",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with swap: <<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 removedisk 103",
        'out': "",
        'overallRC': [0],
    },
    # >>>>>>>>> Tests that are related to active systems.
    {
        'description': "Add a 3390 disk for the root disk: <<<unsafePre>>>3",
        'request': "ChangeVM <<<unsafePre>>>3 add3390 <<<pool3390>>> 100 " +
            "<<<size3390>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Unpack the image into the disk: <<<unsafePre>>>3",
        'request': "SHELL_TEST <<<unpackScript>>> <<<unsafePre>>>3 100 " +
            "<<<simpleImage>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Punch the config drive tar file to the system: " +
            "<<<unsafePre>>>3",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile " +
        "<<<SimpleCfgFile>>> --class x",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Send an aemod to allow IUCV access by this system.",
        'request': "ChangeVM <<<unsafePre>>>3 aemod <<<aeModScript>>> " +
            "--invparms <<<localUserid>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on the system and wait for to OS to " +
            "come up: <<<unsafePre>>>3",
        'request': "PowerVM <<<unsafePre>>>3 on --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with ext4: " +
            "<<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "110 100m --mode w --filesystem ext4",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Online the 101 ECKD disk with ext4: " +
            "<<<unsafePre>>>3",
        'request': "CmdVM <<<unsafePre>>>3 cmd '/sbin/cio_ignore -r 110; " +
            "/sbin/chccwdev -e 110'",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with ext4: <<<unsafePre>>>3 110",
        'request': "changevm <<<unsafePre>>>3 removedisk 110",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with xfs: " +
            "<<<unsafePre>>>3",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "111 100m --mode w --filesystem xfs",
        'out': "",
        'overallRC': [0],
    },
    # Don't online the disk.  This makes the chccwdev fail but the
    # failure should be ignored.
    {
        'description': "Remove the 3390 disk with xfs: " +
            "<<<unsafePre>>>3 111",
        'request': "changevm <<<unsafePre>>>3 removedisk 111",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with swap: " +
            "<<<unsafePre>>>3 112",
        'request': "changevm <<<unsafePre>>>3 add3390 <<<pool3390>>> " +
            "112 100m --mode w --filesystem swap",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Online the 112 ECKD disk with swap: " +
            "<<<unsafePre>>>3",
        'request': "CmdVM <<<unsafePre>>>3 cmd '/sbin/cio_ignore -r 112; " +
            "/sbin/chccwdev -e 112'",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with swap: " +
            "<<<unsafePre>>>3 112",
        'request': "changevm <<<unsafePre>>>3 removedisk 112",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement",
        'request': "changevm <<<unsafePre>>>3 ipl 100",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with loadparms",
        'request': "changevm <<<unsafePre>>>3 ipl 100 --loadparms cl",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with loadparms",
        'request': "changevm <<<unsafePre>>>3 ipl 100 --loadparms lots",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with parms",
        'request': "changevm <<<unsafePre>>>3 ipl cms --parms autocr",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify IPL statement exists.",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "IPL CMS PARM AUTOCR",
        'overallRC': [0],
    },
    {
        'description': "Remove an IPL statement",
        'request': "changevm <<<unsafePre>>>3 removeipl",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add some loaddev statements",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex "
                   "--scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No datatype loaddev statements",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpData 1212",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [14],
    },
    {
        'description': "No data loaddev statements",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [14],
    },
    {
        'description': "Bad datatype loaddev statements",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType BAD --scpData 1212",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [16],
    },
    {
        'description': "Really long scp data",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex " +
                   "--scpData <<<longString>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No boot parm (keep old boot)",
        'request': "changevm <<<unsafePre>>>3 loaddev --addr 123411 " +
                   "--lun 12345678 --wwpn 5005076800aa0001 " +
                   "--scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No addr parm (keep old block address)",
        'request': "changevm <<<unsafePre>>>3 loaddev --lun " +
                   "12345678 --wwpn 5005076800aa0001 " +
                   "--scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No lun parm (keep old lun)",
        'request': "changevm <<<unsafePre>>>3 loaddev --wwpn " +
                   "5005076800aa0001 --scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No wwpn parm (keep old wwpn)",
        'request': "changevm <<<unsafePre>>>3 loaddev --scpDataType " +
                   "hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No parms (keep old parms)",
        'request': "changevm <<<unsafePre>>>3 loaddev",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev boot statements exist",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "LOADDEV BOOTPROG 0",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev addr statements exist",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "LOADDEV BR_LBA 0000000000123411",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev lun statements exist",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "LOADDEV LUN 0000000012345678",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev wwpn statements exist.",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "LOADDEV PORTNAME 5005076800AA0001",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev wwpn statements exist",
        'request': "smapi <<<unsafePre>>>3 api Image_Query_DM",
        'out': "LOADDEV SCPDATA HEX",
        'overallRC': [0],
    },
    {
        'description': "Delete statements",
        'request': "changevm <<<unsafePre>>>3 loaddev --boot DELETE " +
                   "--addr DELETE --lun DELETE --wwpn DELETE " +
                   "--scpDataType DELETE",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev statements are gone",
        'request': "SMAPI <<<unsafePre>>>3 API " +
                   "Image_SCSI_Characteristics_Query_DM",
        'out': "",
        'overallRC': [8],
        'rc': [0],
        'rs': [28],
    },
    {
        'description': "Successfully purge the reader: <<<unsafePre>>>3",
        'request': "changeVM <<<unsafePre>>>3 purgeRDR ",
        'overallRC': [0],
    },
    {
        'description': "Try to purge read of a bad id: <<<horribleID1>>>",
        'request': "changeVM <<<horribleID1>>> purgeRDR ",
        'out': "Syntax error in function parameter 8",
        'overallRC': [8],
        'rc': [24],
        'rs': [813]
    },
    {
        'description': "Punch the config drive tar file to the system.",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile <<<SimpleCfgFile>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with valid spool class.",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile <<<SimpleCfgFile>>>" +
            " --class b",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with an invalid userid and file.",
        'request': "ChangeVM <<<horribleID1>>> punchfile invalid.config",
        'out': "",
        'overallRC': [4],
        'rc': [7],
        'rs': [401],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with an invalid userid and spool class.",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile invalid.config" +
            " --class b*",
        'out': "",
        'overallRC': [4],
        'rc': [7],
        'rs': [401],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with an invalid userid.",
        'request': "ChangeVM <<<horribleID1>>> punchfile <<<SimpleCfgFile>>>" +
            " --class b",
        'out': "",
        'overallRC': [4],
        'rc': [7],
        'rs': [401],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with an invalid class.",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile <<<SimpleCfgFile>>>" +
            " --class b*",
        'out': "",
        'overallRC': [4],
        'rc': [8],
        'rs': [404],
    },
    {
        'description': "Punch the config drive tar file to the system" +
            " with an invalid file.",
        'request': "ChangeVM <<<unsafePre>>>3 punchfile invalid.config",
        'out': "",
        'overallRC': [4],
        'rc': [7],
        'rs': [401],
    },
    # >>>>>>>>> Clean up by destroying the system.
    {
        'description': "Delete the system: <<<unsafePre>>>3",
        'request': "deletevm <<<unsafePre>>>3 directory",
        'out': "",
        'overallRC': [0],
    },
   ]
guestTests = [
    {
        'description': "Power on a system: <<<consoleID>>>",
        'request': "PowerVM <<<consoleID>>> on",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Get the console log of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> consoleoutput",
        'out': "List of spool files containing console logs " +
               "from <<<consoleID>>>:",
        'overallRC': [0],
    },
    {
        'description': "Get the status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --all",
        'out': "CPU Used Time:",
        'overallRC': [0],
    },
    {
        'description': "Get the power status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --power",
        'out': "Power state: on",
        'overallRC': [0],
    },
    {
        'description': "Get the memory status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --memory",
        'out': "Total Memory:",
        'overallRC': [0],
    },
    {
        'description': "Get the cpu status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --cpu",
        'out': "Processors:",
        'overallRC': [0],
    },
    {
        'description': "Power off the system: <<<consoleID>>>",
        'request': "PowerVM <<<consoleID>>> off",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Get the status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status",
        'out': "CPU Used Time: 0 sec",
        'overallRC': [0],
    },
    {
        'description': "Get the power status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --power",
        'out': "Power state: off",
        'overallRC': [0],
    },
    {
        'description': "Get the memory status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --memory",
        'out': "Total Memory: 0M",
        'overallRC': [0],
    },
    {
        'description': "Get the cpu status of the system: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> status --cpu",
        'out': "Processors: 0",
        'overallRC': [0],
    },
    {
        'description': "Verify no console log is available: <<<consoleID>>>",
        'request': "getvm <<<consoleID>>> consoleoutput",
        'out': "",
        'overallRC': [8],
        'rc': [8],
        'rs': [8]
    },
   ]


testSets = {
    'DEPLOY': [
        'Full deploy image tests',
        deployTests],
    'GENERAL': [
        'Tests that are not specific to a particular function.',
        generalTests],
    'GUEST': [
        'Guest tests that are not covered under other functions.',
        guestTests],
    'HOST': [
        'Host related tests',
        hostTests],
    'IUCV': [
        'Send commands to VM over IUCV',
        iucvTests],
    'LIFECYCLE': [
        'VM Life Cycle related tests',
        vmLCTests],
    'MIGRATE': [
        'VM Migration related tests',
        migrateTests],
    'MODIFY': [
        'Modify a VM',
        vmModifyTests],
    'POWER': [
        'VM Power function tests',
        powerTests],
    'SMAPI': [
        'SMAP API invocation tests',
        smapiTests],
    }


def localize(localFile, subs, testSets):
    """
    Perform localization of substitution variables and test sets.
    This allows the invoker to extend or modify defined tests
    without modifying this file.

    Input:
       Name of local tailorization file (without .py)
          e.g. smutTestLocal for smutTestLocal.py file.
       Substitution dictionary to be updated.
       Test set dictionary to be updated.

    Output:
       None

    Note:
       - Upon exit the substitution and test set dictionary
         have been updated with the data from the localization
         file.
    """
    try:
        smutTestLocal = __import__(localFile, fromlist=["*"])
    except Exception as e:
        print(e)
        return 1

    # Apply local overrides to the subs dictionary.
    if len(smutTestLocal.localSubs) > 0:
        print("Localizing localSubs dictionary.")
        for key in smutTestLocal.localSubs:
            print "Localizing " + key + ": " + smutTestLocal.localSubs[key]
            subs[key] = smutTestLocal.localSubs[key]
    else:
        print("No local overrides exist for the subs dictionary.")

    # Apply local overrides to the testSets dictionary.
    if len(smutTestLocal.localTestSets) > 0:
        print "Localizing the test sets."
        if 'clear:testSets' in smutTestLocal.localTestSets:
            print("Removing all original test sets.")
            testSets.clear()
        for key in smutTestLocal.localTestSets:
            if key == 'clear:testSets':
                continue
            print "Localizing test set: " + key
            testSets[key] = smutTestLocal.localTestSets[key]
    else:
        print "No local test sets exist."

    return 0


def runTest(smut, test):
    """
    Drive a test and validate the results.

    Input:
       SMUT daemon object
       Dictionary element for the test to drive.

    Output:
       Final test score - 0: failed, 1: passed,
    """
    global args

    if test['request'][0:10] != 'SHELL_TEST':
        reqHandle = ReqHandle(cmdName=sys.argv[0], captureLogs=True)
        results = reqHandle.parseCmdline(test['request'])
        if results['overallRC'] == 0:
            results = reqHandle.driveFunction()
    else:
        # Issue a function that is not considered a test.
        results = {
            'overallRC': 0,
            'rc': 0,
            'rs': 0,
            'errno': 0,
            'strError': '',
            'response': [],
            'logEntries': [],
            }

        shellCmd = test['request'][11:]
        try:
            results['response'] = subprocess.check_output(
                    shellCmd,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                    shell=True)
        except CalledProcessError as e:
            results['response'] = e.output
            results['overallRC'] = e.returncode
        except Exception as e:
            # All other exceptions.
            if 'output' in e:
                results['response'] = e.output
            else:
                results['response'] = ('Exception encountered: %s, ' +
                    "details: %s" % (type(e).__name__, str(e)))
            if 'returncode' in e:
                results['overallRC'] = e.returncode
            else:
                results['overallRC'] = -9999999

        if isinstance(results['response'], basestring):
            results['response'] = [results['response']]

    print("    Overall rc:  %s" % results['overallRC'])
    print("            rc:  %s" % results['rc'])
    print("            rs:  %s" % results['rs'])

    if len(results['response']) > 0:
        print("    Response:")
        for line in results['response']:
            print("        " + line)
    else:
        print("    Response: None returned")

    # Validate the response strings
    respScore = 1    # Assume the response tests passed.
    if 'out' in test.keys() and len(test['out']) > 0:
        # Expect a response let's test it.
        if len(results['response']) == 0:
            # No response returned when one was expected -> failed
            respScore = 0
        else:
            # Test the response to see it matches an expected response

            # Put the response into a file.  This avoids problems with
            # having special characters in the response that would
            # cause the shell to complain or get confused.
            tempFile = NamedTemporaryFile(delete=False)
            file = open(tempFile.name, 'w')
            for line in results['response']:
                file.write(line + '\n')
            file.close()

            cmd = ['grep', ''.join(test['out']), tempFile.name]

            try:
                junk = subprocess.check_output(cmd, close_fds=True)
                if junk == '':
                    respScore = 0
            except:
                respScore = 0
            os.remove(tempFile.name)
    else:
        pass    # No responses listed, treat as a match

    # Validate the Overall return code
    orcScore = 0          # Assume RC is not a desired one
    if 'overallRC' not in test.keys():
        orcScore = 1      # No special value, assume it passed
    elif len(test['overallRC']) == 1:
        if test['overallRC'][0] == results['overallRC']:
            orcScore = 1
    else:
        for wanted in test['overallRC']:
            if results['overallRC'] == wanted:
                orcScore = 1
                break

    # Validate the failure return code
    rcScore = 0          # Assume RC is not a desired one
    if 'rc' not in test.keys():
        rcScore = 1      # No special value, assume it passed
    elif len(test['rc']) == 1:
        if test['rc'][0] == results['rc']:
            rcScore = 1
    else:
        for wanted in test['rc']:
            if results['rc'] == wanted:
                rcScore = 1
                break

    # Validate the failure reason code
    rsScore = 0          # Assume RC is not a desired one
    if 'rs' not in test.keys():
        rsScore = 1      # No special value, assume it passed
    elif len(test['rs']) == 1:
        if test['rs'][0] == results['rs']:
            rsScore = 1
    else:
        for wanted in test['rs']:
            if results['rs'] == wanted:
                rsScore = 1
                break

    # Determine the final score and show the success or failure of the test
    if respScore != 1 or orcScore != 1 or rcScore != 1 or rsScore != 1:
        testScore = 0
        if len(results['logEntries']) != 0:
            print("    Log Entries:")
            for line in results['logEntries']:
                print("        " + line)
        print("    Test Status: FAILED")
        if respScore != 1:
            print("        Response Validation: FAILED")
        if orcScore != 1:
            print("        Overall RC Validation: FAILED")
        if rcScore != 1:
            print("        rc Validation: FAILED")
        if rsScore != 1:
            print("        rs Validation: FAILED")
    else:
        testScore = 1
        if args.showLog is True and len(results['logEntries']) != 0:
            print("    Log Entries:")
            for line in results['logEntries']:
                print("        " + line)
        print("    Test Status: PASSED")

    return testScore


def driveTestSet(smut, setId, setToTest):
    """
    Drive a set of test.

    Input:
       SMUT daemon object
       Dictionary element for the test to drive.

    Global:
        Count of tests
        Count of passed tests
        Count of failed tests
        List of failed Tests

    Output:
       Global values changed
    """
    global args
    global cnt
    global passed
    global failed
    global failedTests

    print(" ")
    print("******************************************************************")
    print("******************************************************************")
    print("Beginning Test Set: " + setToTest[0])
    print("******************************************************************")
    print("******************************************************************")
    localCnt = 0
    localPassed = 0
    localFailed = 0
    failInfo = []

    for test in setToTest[1]:
        if args.listParms is True:
            print(test['request'])
            continue
        if test['request'][0:6] == 'SHELL ':
            # Issue a function that is not considered a test.
            shellCmd = test['request'][6:]
            shellRC = 0
            try:
                out = subprocess.check_output(
                        shellCmd,
                        stderr=subprocess.STDOUT,
                        close_fds=True,
                        shell=True)
                out = "".join(out)

            except CalledProcessError as e:
                out = e.output
                shellRC = e.returncode
            except Exception as e:
                # All other exceptions.
                if 'output' in e:
                    out = e.output
                else:
                    out = ('Exception encountered: %s, ' +
                        "details: %s" % (type(e).__name__, str(e)))
                if 'returncode' in e:
                    shellRC = e.returncode
                else:
                    shellRC = -9999999

            if isinstance(out, basestring):
                out = [out]

            shellOk = 0
            if 'overallRC' in test:
                for testRC in test['overallRC']:
                    if shellRC == testRC:
                        shellOk = 1
                        break
            if shellOk == 0:
                print("***Warning*** A non test related shell function " +
                    "returned rc: " + str(shellRC) +
                        " out: " + ''.join(out))
        else:
            localCnt += 1
            print("")
            cntInfo = "%i/%i" % (localCnt, (cnt + localCnt))
            print("Test %s: %s" % (cntInfo, test['description']))
            testScore = runTest(smut, test)
            if testScore == 1:
                localPassed += 1
            else:
                localFailed += 1
                failInfo.append(cntInfo)

    cnt += localCnt
    passed += localPassed
    failed += localFailed

    print(" ")
    print("Status of this set: " +
            str(localCnt) + " run, " +
            str(localPassed) + " passed, " +
            str(localFailed) + " failed.")
    if localFailed > 0:
        failedTests.append(setId + ": " + " ".join(failInfo))


"""
******************************************************************************
 main routine
******************************************************************************
"""

# Parse the input and assign it to the variables.
parser = argparse.ArgumentParser()
parser.add_argument('--listareas',
                    dest='listAreas',
                    action='store_true',
                    help='List names of the test set areas.')
parser.add_argument('--listparms',
                    dest='listParms',
                    action='store_true',
                    help='List the command being run.')
parser.add_argument('--local',
                    default='smutTestLocal',
                    dest='localFile',
                    help="Localization file or 'none'.")
parser.add_argument('--showlog',
                    dest='showLog',
                    action='store_true',
                    help='Show log entries for successful tests.')
parser.add_argument('setsToRun',
                    metavar='N',
                    nargs='*',
                    help='Test sets to run')
args = parser.parse_args()

if args.localFile != 'none':
    # Perform the localization.
    print("Localization file specified as: " + args.localFile)
    print("Importing " + args.localFile)
    rc = localize(args.localFile, subs, testSets)
    if rc != 0:
        exit(2)
else:
    print("No localization will be performed.")

# The next lines produce the code that allows the regular expressions to work.
regSubs = dict((re.escape(k), v) for k, v in subs.iteritems())
pattern = re.compile("|".join(regSubs.keys()))

smut = SMUT()
smut.enableLogCapture()              # Capture request related logs

passed = 0
failed = 0
failedTests = []
cnt = 0

# Temporary Preparation for punchFile Test. Create a sample config file.
f = open("sample.config", "w+")
f.write("This is sample config file for punchFile Test")
f.close()

if args.listAreas is True:
    for key in sorted(testSets):
        print key + ": " + testSets[key][0]
else:
    # Initialize the environment.  Online the punch.
    cmd = "/sbin/cio_ignore -r d; /sbin/chccwdev -e d"
    try:
        subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            close_fds=True,
            shell=True)

    except CalledProcessError as e:
        print("Warning: Failed to enable the punch, " +
            "cmd: %s, rc: %i, out: %s" %
            (cmd, e.returncode, e.output))

    except Exception as e:
        # All other exceptions.
        if 'output' in e:
            out = e.output
        else:
            out = ('Exception encountered: %s, ' +
                "details: %s" % (type(e).__name__, str(e)))
        if 'returncode' in e:
            eRC = e.returncode
        else:
            eRC = -9999999
        print("Warning: Failed to enable the punch, " +
            "cmd: %s, rc: %i, %s" %
            (cmd, eRC, out))

    # Perform the substitution change to all requests and responses
    for key in testSets:
        for test in testSets[key][1]:
            test['description'] = pattern.sub(lambda m:
                regSubs[re.escape(m.group(0))], test['description'])
            test['request'] = pattern.sub(lambda m:
                regSubs[re.escape(m.group(0))], test['request'])
            if 'out' in test:
                test['out'] = pattern.sub(lambda m:
                    regSubs[re.escape(m.group(0))], test['out'])

    # Determine the tests to run based on the first argument.
    tests = []
    if len(args.setsToRun) > 0:
        for key in args.setsToRun:
            key = key.upper()
            if key in testSets:
                driveTestSet(smut, key, testSets[key])
            else:
                print("The following tests set was not recognized: " + key)
    else:
        for key in sorted(testSets):
            driveTestSet(smut, key, testSets[key])

    # Cleanup the work files.
    if (os.path.exists("sample.config")):
        os.remove("sample.config")
    if (os.path.exists(subs['<<<aeModScript>>>'])):
        os.remove(subs['<<<aeModScript>>>'])

    print("")
    print("******************************************************************")
    print("Attempted: %s" % cnt)
    print("Passed:    %s" % passed)
    print("Failed:    %s" % failed)
    print("Failed Test(s): " + str(failedTests))
    print("******************************************************************")

    if failed == 0:
        exit(0)
    else:
        exit(1)
