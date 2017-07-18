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

import os
import re
import sys
import subprocess
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile

from smut import SMUT
from ReqHandle import ReqHandle

version = '1.0.0'         # Version of this script

"""
The try/except section will import local overrides for the subs and testSets
structures if the exist.  This allows for extensions to the defined tests
without modifying this file.
"""
try:
    print("Importing smutTestLocal.py")
    import smutTestLocal
    print("Localizing localSubs dictionary.")
    localSubs = smutTestLocal.localSubs
    print("Localizing localSubs dictionary.")
    localTestSets = smutTestLocal.localTestSets
    print("Localization is complete.")
except:
    print("No localization will be performed.")
    localSubs = {}
    localTestSets = {}

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
    '<<<unsafeID1>>>': 'TSTUSER1',      # A userid that gets created and
                                        #   destroyed
    '<<<horribleID1>>>': 'g[][325$$$',  # A userid that makes SMAPI cry
                                        #   and beg for a swift death
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
    '<<<SimpleCfgFile>>>': '/install/zvm/POC/testImages/cfgdrive.tar',
                                        # Simple tar file for the config drive
    '<<<simpleImage>>>': '/install/zvm/POC/testImages/' +
        'rhel67eckd_small_225M.img',    # Small image file
    '<<<unpackScript>>>': '/opt/zthin/bin/unpackdiskimage',
                                        # Location of unpackdiskimage
    '<<<longString>>>': longstring,
}

# Apply local overrides to the subs dictionary.
if len(localSubs) > 0:
    for key in localSubs:
        print "Localizing " + key + ": " + localSubs[key]
        subs[key] = localSubs[key]
else:
    print("No local overrides exist for the subs dictionary.")

# The next lines produce the code that allows the regular expressions to work.
subs = dict((re.escape(k), v) for k, v in subs.iteritems())
pattern = re.compile("|".join(subs.keys()))

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
        'description': "Create a simple system.",
        'request': "MakeVM <<<unsafeID1>>> directory <<<pw>>> " +
                   "<<<vmSize>>> g --ipl 100 --profile OSDFLT",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk.",
        'request': "ChangeVM <<<unsafeID1>>> add3390 <<<pool3390>>> 100 " +
            "<<<size3390>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Check out the user entry",
        'request': "GetVM <<<unsafeID1>>> directory",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Unpack the image into the disk.",
        'request': "SHELL_TEST <<<unpackScript>>> <<<unsafeID1>>> 100 " +
            "<<<simpleImage>>>",
        'out': "",
        'overallRC': [0],
    },
     {
        'description': "Add modifications to the activation engine",
        'request': 'ChangeVM <<<unsafeID1>>> aemod <<<setupDisk>>> ' +
            '--invparms "action=addMdisk vaddr=101 filesys=ext4 ' +
            'mntdir=/mnt/ephemeral/0.0.0101"',

        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add unknown script mods to the activation engine",
        'request': 'ChangeVM <<<unsafeID1>>> aemod BAD ' +
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
        'description': "Purge the reader",
        'request': "ChangeVM <<<unsafeID1>>> purgerdr",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Punch the config drive tar file to the system.",
        'request': "ChangeVM <<<unsafeID1>>> punchfile <<<SimpleCfgFile>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on the system and wait for to OS to come up.",
        'request': "PowerVM <<<safeID>>> on --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Send a commmand to a system.",
        'request': "CmdVM <<<safeID>>> cmd pwd",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Delete a system.",
        'request': "DeleteVM <<<unsafeID1>>> directory",
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
        'description': "Get the space for a specific disk pools.",
        'request': "GetHost diskpoolspace <<<pool3390>>>",
        'out': "^<<<pool3390>>> Total",
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
            "cannot be migrated.",
        'request': "migrateVM <<<unmigrID>>> status",
        'overallRC': [1],
        'rc': [4],
        'rs': [3001],
    },
    {
        'description': "Get all migration status for a host with " +
            "no active migrations.",
        'request': "migrateVM <<<unmigrID>>> status --all",
        'overallRC': [1],
        'rc': [4],
        'rs': [3001],
    },
    {
        'description': ("Get incoming migration status for a host with no " +
            "active migrations."),
        'request': "migrateVM <<<unmigrID>>> status --incoming",
        'overallRC': [1],
        'rc': [4],
        'rs': [3001],
    },
    {
        'description': "Get outgoing migration status for a host with no " +
            "active migrations.",
        'request': "migrateVM <<<unmigrID>>> status --outgoing",
        'overallRC': [1],
        'rc': [4],
        'rs': [3001],
    },
    {
        'description': "Test a system for migration",
        'request': "migrateVM <<<unmigrID>>> test --destination " +
            "<<<migrDest>>>",
        'overallRC': [1],
        'rc': [4],
        'rs': [3000],
    },
    {
        'description': "Cancel a migration",
        'request': "migrateVM <<<migrID>>> cancel",
        'overallRC': [1],
        'rc': [4],
        'rs': [3001],
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
        'description': "Power off the system.",
        'request': "PowerVM <<<safeID>>> off --wait",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Check status of powered off system.",
        'request': "PowerVM <<<safeID>>> status",
        'out': "^<<<safeID>>>: off",
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
        'description': "Power on the system.",
        'request': "PowerVM <<<safeID>>> on --wait",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Check status of powered on system.",
        'request': "PowerVM <<<safeID>>> status",
        'out': "^<<<safeID>>>: on",
        'overallRC': [0],
        'rc': [0],
        'rs': [0]
    },
    {
        'description': "Check isreachable of powered on system.",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Power on the an already powered on system.",
        'request': "PowerVM <<<safeID>>> on",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Pause a system.",
        'request': "PowerVM <<<safeID>>> pause",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of a paused system is unreachable.",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: unreachable",
        'overallRC': [0],
        'rs': [0]
    },
    {
        'description': "Unpause a system.",
        'request': "PowerVM <<<safeID>>> unpause",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of an unpaused system is reachable.",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Reset a system.",
        'request': "PowerVM <<<safeID>>> reset --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Isreachable of an unpaused system is reachable.",
        'request': "PowerVM <<<safeID>>> isreachable",
        'out': "<<<safeID>>>: reachable",
        'overallRC': [0],
        'rs': [1]
    },
    {
        'description': "Reboot a system.",
        'request': "PowerVM <<<safeID>>> reboot --wait",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Reboot a system w/o waiting for the OS to be up",
        'request': "PowerVM <<<safeID>>> reboot",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Wait for the OS to come up.",
        'request': "PowerVM <<<safeID>>> wait --state up",
        'out': "",
        'overallRC': [0],
        'rs': [0]
    },
    ]

shellTests = [
    {
        'description': "Issue a successful non-Test 1-line output related " +
            "SHELL function.",
        'request': "SHELL echo \'Hurray!\'",
        'overallRC': [0],
    },
    {
        'description': "Do a successful non-Test multi-line output related " +
            "SHELL function.",
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
    ]

vmLCTests = [
    {
        'description': "Create a simple system.",
        'request': "makevm <<<unsafeID1>>> directory smapi 2g g",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify system exists.",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Delete a system.",
        'request': "deletevm <<<unsafeID1>>> directory",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify system no longer exists.",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "",
        'overallRC': [1],
        'rc': [400],
        'rs': [4],
    },
   ]

vmModifyTests = [
    # >>>>>>>>> Create a simple system for logged off tests.
    {
        'description': "Create a simple system.",
        'request': "makevm <<<unsafeID1>>> directory smapi 2g g",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with ext4.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem ext4",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with ext4.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with xfs.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem xfs",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with xfs.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with swap.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem swap",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with swap.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    # >>>>>>>>> Tests that are related to active systems.
    {
        'description': "Add a 3390 disk for the root disk.",
        'request': "ChangeVM <<<unsafeID1>>> add3390 <<<pool3390>>> 100 " +
            "<<<size3390>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Unpack the image into the disk.",
        'request': "SHELL_TEST <<<unpackScript>>> <<<unsafeID1>>> 100 " +
            "<<<simpleImage>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Power on the system and wait for to OS to come up.",
        'request': "PowerVM <<<safeID>>> on --wait --state up",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with ext4.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem ext4",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with ext4.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with xfs.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem xfs",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with xfs.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add a 3390 disk to the system with swap.",
        'request': "changevm <<<unsafeID1>>> add3390 <<<pool3390>>> " +
            "101 100m --mode w --filesystem swap",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Remove the 3390 disk with swap.",
        'request': "changevm <<<unsafeID1>>> removedisk 101",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement",
        'request': "changevm <<<unsafeID1>>> ipl 100",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with loadparms",
        'request': "changevm <<<unsafeID1>>> ipl 100 --loadparms cl",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with loadparms",
        'request': "changevm <<<unsafeID1>>> ipl 100 --loadparms lots",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add/change an IPL statement with parms",
        'request': "changevm <<<unsafeID1>>> ipl cms --parms autocr",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify IPL statement exists.",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "IPL CMS PARM AUTOCR",
        'overallRC': [0],
    },
    {
        'description': "Remove an IPL statement",
        'request': "changevm <<<unsafeID1>>> removeipl",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Add some loaddev statements",
        'request': "changevm <<<unsafeID1>>> loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex "
                   "--scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No datatype loaddev statements",
        'request': "changevm <<<unsafeID1>>> loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpData 1212",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [14],
    },
    {
        'description': "No data loaddev statements",
        'request': "changevm <<<unsafeID1>>> loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [14],
    },
    {
        'description': "Bad datatype loaddev statements",
        'request': "changevm <<<unsafeID1>>> loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType BAD --scpData 1212",
        'out': "",
        'overallRC': [4],
        'rc': [4],
        'rs': [16],
    },
    {
        'description': "Really long scp data",
        'request': "changevm <<<unsafeID1>>> loaddev --boot 0 " +
                   "--addr 123411 --lun 12345678 --wwpn " +
                   "5005076800aa0001 --scpDataType hex " +
                   "--scpData <<<longString>>>",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No boot parm (keep old boot)",
        'request': "changevm <<<unsafeID1>>> loaddev --addr 123411 " +
                   "--lun 12345678 --wwpn 5005076800aa0001 " +
                   "--scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No addr parm (keep old block address)",
        'request': "changevm <<<unsafeID1>>> loaddev --lun " +
                   "12345678 --wwpn 5005076800aa0001 " +
                   "--scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No lun parm (keep old lun)",
        'request': "changevm <<<unsafeID1>>> loaddev --wwpn " +
                   "5005076800aa0001 --scpDataType hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No wwpn parm (keep old wwpn)",
        'request': "changevm <<<unsafeID1>>> loaddev --scpDataType " +
                   "hex --scpData 1212",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "No parms (keep old parms)",
        'request': "changevm <<<unsafeID1>>> loaddev",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev boot statements exist",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "LOADDEV BOOTPROG 0",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev addr statements exist",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "LOADDEV BR_LBA 0000000000123411",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev lun statements exist",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "LOADDEV LUN 0000000012345678",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev wwpn statements exist",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "LOADDEV PORTNAME 5005076800AA0001",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev wwpn statements exist",
        'request': "smapi <<<unsafeID1>>> api Image_Query_DM",
        'out': "LOADDEV SCPDATA HEX",
        'overallRC': [0],
    },
    {
        'description': "Delete statements",
        'request': "changevm <<<unsafeID1>>> loaddev --boot DELETE " +
                   "--addr DELETE --lun DELETE --wwpn DELETE " +
                   "--scpDataType DELETE",
        'out': "",
        'overallRC': [0],
    },
    {
        'description': "Verify loaddev statements are gone",
        'request': "SMAPI <<<unsafeID1>>> API " +
                   "Image_SCSI_Characteristics_Query_DM",
        'out': "",
        'overallRC': [1],
        'rc': [0],
        'rs': [28],
    },
    {
        'description': "Successfully purge the reader.",
        'request': "changeVM <<<unsafeID1>>> purgeRDR ",
        'overallRC': [0],
    },
    {
        'description': "Try to purge read of a bad id.",
        'request': "changeVM <<<horribleID1>>> purgeRDR ",
        'out': "Syntax error in function parameter 8",
        'overallRC': [1],
        'rc': [24],
        'rs': [813]
    },
    # >>>>>>>>> Clean up by destroying the system.
    {
        'description': "Delete the system.",
        'request': "deletevm <<<unsafeID1>>> directory",
        'out': "",
        'overallRC': [0],
    },
   ]


testSets = {
    'DEPLOY': [
        'Full deploy image tests',
        deployTests],
    'GENERAL': [
        'Tests that are not specific to a particular function.',
        generalTests],
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

# Apply local overrides to the testSets dictionary.
if len(localTestSets) > 0:
    print "Localizing the test sets."
    for key in localTestSets:
        print "Localizing test set: " + key
        testSets[key] = localTestSets[key]
else:
    print "No local test sets exist."


def runTest(smut, test):
    """
    Drive a test and validate the results.

    Input:
       SMUT daemon object
       Dictionary element for the test to drive.

    Output:
       Final test score - 0: failed, 1: passed,
    """

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
            # Last SED would have to fail for the exception to be thrown.
            results['response'] = e.output
            results['overallRC'] = e.returncode

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
            except CalledProcessError as e:
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
    global cnt
    global passed
    global failed
    global failedTests
    global listParms

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
        if listParms is True:
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
                # Last SED would have to fail for the exception to be thrown.
                out = e.output
                shellRC = e.returncode

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
smut = SMUT()
smut.enableLogCapture()              # Capture request related logs

passed = 0
failed = 0
failedTests = []
cnt = 0
listParms = False

if len(sys.argv) > 1 and sys.argv[1].upper() == '--LISTAREAS':
    for key in sorted(testSets):
        print key + ": " + testSets[key][0]
else:
    # Perform the substitution change to all requests and responses
    for key in testSets:
        for test in testSets[key][1]:
            test['request'] = pattern.sub(lambda m:
                subs[re.escape(m.group(0))], test['request'])
            if 'out' in test:
                test['out'] = pattern.sub(lambda m:
                    subs[re.escape(m.group(0))], test['out'])

    # Determine the tests to run based on the first argument.
    tests = []
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            key = sys.argv[i].upper()
            if key == '--LISTPARMS':
                listParms = True
                pass
            elif key in testSets:
                driveTestSet(smut, key, testSets[key])
            else:
                print("The following tests set was not recognized: " + key)
    else:
        for key in sorted(testSets):
            driveTestSet(smut, key, testSets[key])

    print("")
    print("******************************************************************")
    print("Attempted: %s" % cnt)
    print("Passed:    %s" % passed)
    print("Failed:    %s" % failed)
    print("Failed Test(s): " + str(failedTests))
    print("******************************************************************")
