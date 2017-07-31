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
    '0017': [{'overallRC': 4, 'rc': 4, 'rs': 17},    # dict is not used
            "ULT%s0017W The maxwait time %i sec is not evenly divisible " +
            "by the poll interval %i sec.  Maximum wait time will be %i " +
            "sec or %i poll intervals."],

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
    # 0205-0299: Available

    # SMCLI and SMAPI related messages.
    '0300': [{'overallRC': 1},    # dict is not used.
            "ULT%s0300E SMAPI API failed: %s, overall rc: %s, rc: %s, " +
            "rs: %s, errno: %s, cmd: %s, out: %s"],
    '0301': [{'overallRC': 1, 'rc': 301, 'rs': 0},
            "ULT%s0301E SMAPI API failed: %s, response header does not " +
            "have the expected 3 values before the (details) string. " +
            "cmd: %s, response header: %s, out: %s"],
    '0302': [{'overallRC': 25, 'rc': 302, 'rs': 0},
            "ULT%s0302E SMAPI API failed: %s, word 1 in " +
            "the response header is not an integer or in the range of " +
            "expected values. word 1: %s, cmd: %s, response " +
            "header: %s, out: %s"],
    '0303': [{'overallRC': 1, 'rc': 303, 'rs': 0},
            "ULT%s0303E SMAPI API failed: %s, word 2 in the response " +
            "header is not an integer. word 2: %s, cmd: %s, response " +
            "header: %s, out: %s"],
    '0304': [{'overallRC': 1, 'rc': 304, 'rs': 0},
            "ULT%s0304E SMAPI API failed: %s, word 3 in the response " +
            "header is not an integer. word 3: %s, cmd: %s, response " +
            "header: %s, out: %s"],
    # 0305-0310: Available

    # IUCV related messages
    '0311': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0311E On %s, command sent through IUCV failed, " +
            "rc in response string is not an integer. " +
            "cmd: %s, rc: %s, out: %s"],
    '0312': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0312E On %s, command sent through IUCV failed, " +
            "reason code in response string is not an integer. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0313': [{'overallRC': 2, 'rc': 1},      # dict is not used.
            "ULT%s0313E On %s, command sent through IUCV was not " +
            "authorized or a generic Linux error occurred. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0314': [{'overallRC': 2, 'rc': 2},      # dict is not used.
            "ULT%s0314E IUCV client parameter error sending command to %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0315': [{'overallRC': 2, 'rc': 4},      # dict is not used.
            "ULT%s0315E IUCV socket error sending command to %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0316': [{'overallRC': 2, 'rc': 8},      # dict is not used.
            "ULT%s0316E On %s, command sent through IUCV failed. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0317': [{'overallRC': 2, 'rc': 16},     # dict is not used.
            "ULT%s0317E File transport failure while sending " +
            "command to %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0318': [{'overallRC': 2, 'rc': 32},     # dict is not used.
            "ULT%s0318E On %s, IUCV server file was not found. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
    '0319': [{'overallRC': 2},               # dict is not used.
            "ULT%s0319E Unrecognized IUCV client error encountered " +
            "while sending a command through IUCV to $s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],

    '0400': [{'overallRC': 4, 'rc': 4, 'rs': 400},
            "ULT%s0400E The worker script %s does not exist."],
    '0401': [{'overallRC': 4, 'rc': 7, 'rs': 401},
            "ULT%s0401E Failed to punch %s file to guest: %s, out: %s"],
    '0402': [{'overallRC': 4, 'rc': 5, 'rs': 402},
            "ULT%s0402E No information was found for the specified " +
            "pool(s): %s"],
    '0403': [{'overallRC': 4, 'rc': 99, 'rs': 403},
            "ULT%s0403E  %s"],
    '0404': [{'overallRC': 4, 'rc': 8, 'rs': 404},
            "ULT%s0404E Failed to spool the punch to the specified class %s" +
            ", out:%s "],
    '0405': [{'overallRC': 4, 'rc': 6, 'rs': 405},
            "ULT%s0405E Unable to obtain information related to: " +
            "%s. Command used was: %s. Output was: %s"],
    '0406': [{'overallRC': 4, 'rc': 9, 'rs': 406},
            "ULT%s0406E Failed to punch %s because of VMUR timeout "],
    '0407': [{'overallRC': 4, 'rc': 4, 'rs': 407},     # dict is not used.
            "ULT%s0407W Unable to spool reader to all classes, " +
            "it is possible that there may be additional console " +
            "files available that are not listed in the response. " +
            "Response from %s is %s"],
    '0408': [{'overallRC': 4, 'rc': 4, 'rs': 408},
            "ULT%s0408E Error getting list of files in the reader " +
            "to search for logs from user %s. Response from %s is %s"],
    '0409': [{'overallRC': 4, 'rc': 4, 'rs': 409},
            "ULT%s0409E Unable to get console log for user %s " +
            "the userid is either not logged on or is not spooling " +
            "its console.  Error rc=rs=8 returned from " +
            "Image_Console_Get."],
    '0410': [{'overallRC': 4, 'rc': 4, 'rs': 410},
            "ULT%s0410E Unable to get console log for user %s " +
            "no spool files were found in our reader from this " +
            "user, it is possible another process has already " +
            "received them."],
    '0411': [{'overallRC': 4, 'rc': 4, 'rs': 411},
            "ULT%s0411E Unable to receive console output file. " +
            "Reader not online.  /sys/bus/ccw/drivers/vmur/0.0.000c" +
            "/online = 0"],
    '0412': [{'overallRC': 4, 'rc': 4, 'rs': 412},     # dict is not used.
            "ULT%s0412E Malformed reply from SMAPI, unable to fill " +
            "in performance information.  Response is %s"],
    '0413': [{'overallRC': 99, 'rc': 99, 'rs': 413},
            "ULT%s0413E Userid '%s' did not enter the expected " +
            "operating system state of '%s' in %i seconds."],
    '0414': [{'overallRC': 99, 'rc': 99, 'rs': 414},
            "ULT%s0414E Userid '%s' did not enter the expected " +
            "virtual machine state of '%s' in %i seconds."],
    '0415': [{'overallRC': 3, 'rc': 415},    # rs comes from failing rc
            "ULT%s0415E Command failed: '%s', rc: %i out: %s"],
    '0416': [{'overallRC': 99, 'rc': 99, 'rs': 416},
            "ULT%s0416E Command returned a response " +
            "containing '%s' but did not have at least %i words " +
            "following it. cmd: '%s', out: '%s'"],
    '0417': [{'overallRC': 99, 'rc': 99, 'rs': 417},
            "ULT%s0417E Command did not return the expected response " +
            "containing '%s', cmd: '%s', out: '%s'"],
    '0418': [{'overallRC': 99, 'rc': 99, 'rs': 418},
            "ULT%s0418E Userid %s is not logged on to this system."],
    '0419': [{'overallRC': 99, 'rc': 99, 'rs': 419},
            "ULT%s0419E A relocation is not in progress for userid %s."],
    '0420': [{'overallRC': 99, 'rc': 99, 'rs': 420},     # dict is not used.
            "ULT%s0420E An error occurred issuing a %s for userid %s.\n" +
            "Please look up message(s): %s in the CP Messages book for " +
            "more information."],
    # 5000-6100: Reserved for SMCLI
    }
