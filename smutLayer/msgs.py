# Messages for Systems Management Ultra Thin Layer
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


"""
List of modules that use these messages and their module id.
ModId  Module
-----  --------------------
CVM    changeVM.py
CMD    cmdVM.py
DVM    deleteVM.py
GUT    generalUtils.py
GHO    getHost.py
GVM    getVM.py
MVM    makeVM.py
MIG    migrateVM.py
PVM    powerVM.py
RQH    ReqHandle.py
SMC    Reserved for smcli
SMP    smapi.py
VMU    vmUtils.py

List of messages.  Message id is the key.
Messages are grouped by their message number.
Each message is defined in a array that provides:
    - Dictionary of values for the result structure,
      e.g. {'overallRC': 4, 'rc': 100}
      The keys in the dictionary can contain: 'overallRC', 'rc', 'rs'
      'errno', and 'strError'.  These allow us to use the dictionary to
      update the ReqHandle results dictionary.
    - Message text (may contain substitution directives, e.g. %s, %i)
"""
msg = {
    # 0001-0099: Parsing Messages
    '0001': [{'overallRC': 4, 'rc': 4, 'rs': 1},
            "ULT%s0001E %s %s subfunction's operand at position %i (%s) " +
            "is not an integer: %s"],
    '0002': [{'overallRC': 4, 'rc': 4, 'rs': 2},
            "ULT%s0002E %s's %s subfunction is missing positional " +
            "operand (%s) at position %i."],
    '0003': [{'overallRC': 4, 'rc': 4, 'rs': 3},
            "ULT%s0003E %s's %s subfunction %s keyword operand is " +
            "missing a value."],
    '0004': [{'overallRC': 4, 'rc': 4, 'rs': 4},
            "ULT%s0004E %s's %s subfunction %s keyword operand is not " +
            "an integer: %s"],
    '0005': [{'overallRC': 4, 'rc': 4, 'rs': 5},
            "ULT%s0005E %s's %s subfunction does not recognize keyword: %s"],
    '0006': [{'overallRC': 4, 'rc': 4, 'rs': 6},
            "ULT%s0006E %s's %s subfunction encountered an unknown " +
            "operand: %s"],
    '0007': [{'overallRC': 4, 'rc': 4, 'rs': 7},
            "ULT%s0007E Unrecognized function: %s"],
    '0008': [{'overallRC': 4, 'rc': 4, 'rs': 8},
            "ULT%s0008E Specified function is not 'HELP' or 'Version': %s"],
    '0009': [{'overallRC': 4, 'rc': 4, 'rs': 9},
            "ULT%s0009E Too few arguments specified."],
    '0010': [{'overallRC': 4, 'rc': 4, 'rs': 10},
        "ULT%s0010E Userid is missing"],
    '0011': [{'overallRC': 4, 'rc': 4, 'rs': 11},
        "ULT%s0011E Subfunction is missing. It should be one of " +
        "the following: %s"],
    '0012': [{'overallRC': 4, 'rc': 4, 'rs': 12},
        "ULT%s0012E The request data is not one of the supported types " +
        "of list or string: %s"],
    '0013': [{'overallRC': 4, 'rc': 4, 'rs': 13},
        "ULT%s0010E The desired state was: %s. Valid states are: %s"],
    '0014': [{'overallRC': 4, 'rc': 4, 'rs': 14},
        "ULT%s0014E The option %s was specified but the option %s " +
        "was not specified.  These options must both be specified."],
    '0015': [{'overallRC': 4, 'rc': 4, 'rs': 15},
            "ULT%s0015E The file system was not 'ext2', 'ext3', " +
            "'ext4', 'xfs' or 'swap': %s"],
    '0016': [{'overallRC': 4, 'rc': 4, 'rs': 16},
            "ULT%s0016E The scp Data Type was not 'hex', 'ebcdic', " +
            "or 'delete': %s"],

    # 0200-0299: Utility Messages
    '0200': [{'overallRC': 4, 'rc': 4, 'rs': 200},
            "ULT%s0200E The size of the disk is not valid: %s"],
    '0201': [{'overallRC': 4, 'rc': 4, 'rs': 201},
            "ULT%s0201E Failed to convert %s to a number of blocks."],
    '0202': [{'overallRC': 4, 'rc': 4, 'rs': 202},
            "ULT%s0202E %s is not an integer size of blocks."],
    '0203': [{'overallRC': 4, 'rc': 4, 'rs': 203},
            "ULT%s0203E Failed to convert %s to a number of cylinders."],
    '0204': [{'overallRC': 4, 'rc': 4, 'rs': 204},
            "ULT%s0204E %s is not an integer size of cylinders."],
    # 0205-0209: Available

    '0300': [{'overallRC': 1, 'rc': 99, 'rs': 99},    # dict is not used.
            "ULT%s0300E SMAPI API failed: %s, rc: %s, out: %s"],
    # 0301-0309: Available
    '0310': [{'overallRC': 2, 'rc': 99, 'rs': 99},    # dict is not used.
            "ULT%s0310E On %s, command: %s, failed with rc: %s, out: %s"],
    '0311': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0311E On %s, command sent thru IUCV failed, rc: %s, " +
            "rc in response string is not an integer: %s, cmd: %s, out: %s"],
    '0312': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0312E On %s, command sent thru IUCV failed, rc: %s, " +
            "reason code in response string is not an integer: %s, " +
            "cmd: %s, out: %s"],
    '0313': [{'overallRC': 2, 'rc': 1},      # dict is not used.
            "ULT%s0313E Issued command was not authorized or a generic " +
            "Linux error occurred, error details: %s"],
    '0314': [{'overallRC': 2, 'rc': 2},      # dict is not used.
            "ULT%s0314E IUCV client parameter error, error details: %s"],
    '0315': [{'overallRC': 2, 'rc': 4},      # dict is not used.
            "ULT%s0315E IUCV socket error, error details: %s"],
    '0316': [{'overallRC': 2, 'rc': 8},      # dict is not used.
            "ULT%s0316E Executed command failed, error details: %s"],
    '0317': [{'overallRC': 2, 'rc': 16},     # dict is not used.
            "ULT%s0317E File Transport failed, error details: %s"],
    '0318': [{'overallRC': 2, 'rc': 32},     # dict is not used.
            "ULT%s0318E IUCV server file was not found on this system, "
            "error details: %s"],
    '0319': [{'overallRC': 2},               # dict is not used.
            "ULT%s0319E Unrecognized IUCV client error, error details: "],

    '0400': [{'overallRC': 4, 'rc': 4, 'rs': 400},
            "ULT%s0400E The worker script %s does not exist."],
    '0401': [{'overallRC': 4, 'rc': 99, 'rs': 401},    # dict is not used.
            "ULT%s0401E Failed to punch %s file to guest: %s, out: %s"],
    '0402': [{'overallRC': 4, 'rc': 5, 'rs': 402},
            "ULT%s0402E No information was found for the specified " +
            "pool(s): %s"],
    '0403': [{'overallRC': 4, 'rc': 99, 'rs': 403},
            "ULT%s0403E  %s"],
    '0404': [{'overallRC': 4, 'rc': 6, 'rs': 404},
            "ULT%s0404E No information was found for the host information " +
            "parameter: %s. Command used was %s. Output was %s."],
    # 5000-5999: Reserved for SMCLI
    }
