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
        # Explain: An error was detected while parsing the command.
        #   The indicated operand is not an integer.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax so that the indicated operand is
        #   an integer, e.g., 10 and reissue the command.
    '0002': [{'overallRC': 4, 'rc': 4, 'rs': 2},
            "ULT%s0002E %s's %s subfunction is missing positional " +
            "operand (%s) at position %i."],
        # Explain: An error was detected while parsing the command.
        #   A positional operand is missing.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax by specifying the missing operand
        #   and reissue the command.
    '0003': [{'overallRC': 4, 'rc': 4, 'rs': 3},
            "ULT%s0003E %s's %s subfunction %s keyword operand is " +
            "missing a value."],
        # Explain: An error was detected while parsing the command.
        #   A keyword operand that requires a value was specified without
        #   the value.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to provide a value for the specified
        #   keyword operand and reissue the command.
    '0004': [{'overallRC': 4, 'rc': 4, 'rs': 4},
            "ULT%s0004E %s's %s subfunction %s keyword operand is not " +
            "an integer: %s"],
        # Explain: An error was detected while parsing the command.
        #   The specified operand for a keyword is not an integer.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax so that the keyword operand is
        #   an integer, e.g., 10 and reissue the command.
    '0005': [{'overallRC': 4, 'rc': 4, 'rs': 5},
            "ULT%s0005E %s's %s subfunction does not recognize keyword: %s"],
        # Explain: An error was detected while parsing the command.
        #   An unrecognized keyword was encountered.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to specify a recognized keyword
        #   and reissue the command.
    '0006': [{'overallRC': 4, 'rc': 4, 'rs': 6},
            "ULT%s0006E %s's %s subfunction encountered an unknown " +
            "operand: %s"],
        # Explain:  An error was detected while parsing the command.
        #   An unknown operand was encountered.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax and reissue the command.
    '0007': [{'overallRC': 4, 'rc': 4, 'rs': 7},
            "ULT%s0007E Unrecognized function: %s"],
        # Explain:  An error was detected while parsing the command.
        #   The specified function is not known.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax and reissue the command.
    '0008': [{'overallRC': 4, 'rc': 4, 'rs': 8},
            "ULT%s0008E Specified function is not 'HELP' or 'VERSION': %s"],
        # Explain: An error was detected while parsing the command.
        #   The specified function was not 'HELP' or 'VERSION' which are the
        #   only valid functions for a command of the specified length.
        # SysAct: Processing of the function terminates.
        # UserResp: Correct the syntax and reissue the command.
    '0009': [{'overallRC': 4, 'rc': 4, 'rs': 9},
            "ULT%s0009E Too few arguments specified."],
        # Explain: An error was detected while parsing the command.
        #   The minimum number of arguments were not provided for the command.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax and reissue the command.
    '0010': [{'overallRC': 4, 'rc': 4, 'rs': 10},
        "ULT%s0010E Userid is missing"],
        # Explain: An error was detected while parsing the command.
        #   A userid operand was not specified.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax and specify the userid along
        #   with any other required operands and reissue the command.
    '0011': [{'overallRC': 4, 'rc': 4, 'rs': 11},
        "ULT%s0011E Subfunction is missing. It should be one of " +
        "the following: %s"],
        # Explain: An error was detected while parsing the command.
        #   The name of the subfunction was not specified.
        # SysAct: Processing of the function terminates.
        # UserResp: Correct the syntax and specify the userid along
        #   with any other required operands and reissue the command.
    '0012': [{'overallRC': 4, 'rc': 4, 'rs': 12},
        "ULT%s0012E The request data is not one of the supported types " +
        "of list or string: %s"],
        # Explain: The ReqHandle parseCmdline method was called with
        #   the request passed in a variable that was not a
        #   list or base string.  Only these types of variables are
        #   supported for passing of the request to be parsed.
        # SysAct: Processing of the function terminates.
        # UserResp: Correct the calling function to use either a
        #   list or base string to hold the request to be processed
        #   and reinvoke the call.
    '0013': [{'overallRC': 4, 'rc': 4, 'rs': 13},
        "ULT%s0010E The desired state was: %s. Valid states are: %s"],
        # Explain: An error was detected while parsing the command.
        #   The state operand value is not one of the accepted values.
        #   The valid values are shown in the message.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to use one of the valid states
        #   and reissue the command.
    '0014': [{'overallRC': 4, 'rc': 4, 'rs': 14},
        "ULT%s0014E The option %s was specified but the option %s " +
        "was not specified.  These options must both be specified."],
        # Explain: An error was detected while parsing the command.
        #   An option was specified which required a related
        #   option that was not specified.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to specify both options and
        #   reissue the command.
    '0015': [{'overallRC': 4, 'rc': 4, 'rs': 15},
            "ULT%s0015E The file system was not 'ext2', 'ext3', " +
            "'ext4', 'xfs' or 'swap': %s"],
        # Explain: An error was detected while parsing the command.
        #   The type of file system does not match one of the valid
        #   values.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to use a valid file system type
        #   and reissue the command.
    '0016': [{'overallRC': 4, 'rc': 4, 'rs': 16},
            "ULT%s0016E The scp Data Type was not 'hex', 'ebcdic', " +
            "or 'delete': %s"],
        # Explain: An error was detected while parsing the command.
        #   The value specified for the scp data type is not one of the
        #   recognized values.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the syntax to use a valid scp data type and
        #   reissue the command.
    '0017': [{'overallRC': 4, 'rc': 4, 'rs': 17},    # dict is not used
            "ULT%s0017W The maxwait time %i sec is not evenly divisible " +
            "by the poll interval %i sec.  Maximum wait time will be %i " +
            "sec or %i poll intervals."],
        # Explain: When trying to determine how many polling intervals
        #   to wait for a desired guest power state, it was found that the
        #   specified maximum wait time was not evenly divisible by the
        #   number of polling interval seconds.  The program instead
        #   rounded the maximum wait time up to be evenly divisble
        #   by the polling interval.
        # SysAct: Processing of the function continues with the
        #   new wait time.
        # UserResp: If the wait time is unacceptably long, invoke
        #   the function with a maximum wait time and polling
        #   interval time which are evenly divisible and of an
        #   acceptable duration.

    # 0200-0299: Utility Messages
    '0200': [{'overallRC': 4, 'rc': 4, 'rs': 200},
            "ULT%s0200E The size of the disk is not valid: %s"],
        # Explain: An error was encountered while attempting
        #   to convert the size of a disk from bytes to cylinders
        #   (for 3390 type disks) or bytes to blocks (for FBA type disks).
        #   This error can be caused by specifying the size as only a
        #   magnitude, (e.g., 'G' or 'M') instead of an integer
        #   appended to a magnitude (e.g., '20G').
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the disk size to specify a disk magnitude
        #   that includes the integer portion of the size in addition
        #   to the magnitude and reissue the command.
    '0201': [{'overallRC': 4, 'rc': 4, 'rs': 201},
            "ULT%s0201E Failed to convert %s to a number of blocks."],
        # Explain: An error was encountered while attempting
        #   to convert the size of a disk from bytes to blocks.
        #   The size ended with a magnitude character and should have
        #   had an integer value prepended to the magnitude character
        #   (e.g. '10M' or '10G').
        #   The probable cause of the error is that the integer
        #   portion of the size contains a non-numeric character.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the disk size to specify a valid value
        #   and reissue the command.
    '0202': [{'overallRC': 4, 'rc': 4, 'rs': 202},
            "ULT%s0202E %s is not an integer size of blocks."],
        # Explain: An error was encountered while attempting
        #   to convert the size of a disk from bytes to blocks.
        #   The size did not end with a valid magnitude character
        #   (i.e., 'M' or 'G') so it was treated as an integer
        #   value (e.g. '100000').  The probable cause of this
        #   error is that the size contains non-numeric
        #   characters.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the disk size to specify a valid value
        #   and reissue the command.
    '0203': [{'overallRC': 4, 'rc': 4, 'rs': 203},
            "ULT%s0203E Failed to convert %s to a number of cylinders."],
        # Explain: An error was encountered while attempting
        #   to convert the size of a disk from bytes to cylinders.
        #   The size ended with a magnitude character and should have
        #   had an integer value prepended to the magnitude character
        #   (e.g. '10M' or '10G').
        #   The probable cause of the error is that the integer
        #   portion of the size contains non-numeric characters.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the disk size to specify a valid value
        #   and reissue the command.
    '0204': [{'overallRC': 4, 'rc': 4, 'rs': 204},
            "ULT%s0204E %s is not an integer size of cylinders."],
        # Explain: An error was encountered while attempting
        #   to convert the size of a disk from bytes to cylinders.
        #   The size did not end with a valid magnitude character
        #   (i.e., 'M' or 'G') so it was treated as an integer
        #   value (e.g. '100000').  The probable cause of this
        #   error is that the size contains non-numeric
        #   characters.
        # SysAct: Processing of the subfunction terminates.
        # UserResp: Correct the disk size to specify a valid value
        #   and reissue the command.
    # 0205-0299: Available

    # SMCLI and SMAPI related messages.
    '0300': [{'overallRC': 8},    # dict is not used.
            "ULT%s0300E SMAPI API failed: %s, overall rc: %s, rc: %s, " +
            "rs: %s, errno: %s, cmd: %s, out: %s"],
        # Explain: The smcli program was invoked to call z/VM SMAPI for
        #   the indicated API.  An error was encountered.  The overall rc
        #   indicates the location of the problem:
        #   8  - SMAPI returned the error.  The rc and rs values are
        #        the values provided by SMAPI.  The z/VM Systems
        #        Management Application Programming book provides
        #        additional documentation related to the return code and
        #        reason code in the API description and in the "Return
        #        and Reason Code Summary" chapter.
        #   24 - The smcli program identified a parameter validation
        #        error.  A message will indicate what was detected.
        #        It could be a missing parameter, invalid parameter, etc.
        #        Invoke the smcli program using the -h parameter and the
        #        API name shown in the error message to obtain additional
        #        invocation help, e.g. "./smcli Image_Query_DM -h".
        #        In addition, the z/VM Systems Management Application
        #        Programming book provides additional documentation
        #        related to the return code and reason code in the API
        #        description.
        #   25 - The smcli program encountered an internal error.
        #        The rc and errno contains information related to the
        #        problem.  The error message from the smcli invocation
        #        and log entries in the system log provide the most
        #        useful information to debug this error.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the problem using the
        #   information described in the explanation section.  Reinvoke
        #   the function after you correct the problem.
    '0301': [{'overallRC': 25, 'rc': 301, 'rs': 0},
            "ULT%s0301E SMAPI API failed: %s, response header does not " +
            "have the expected 3 values before the (details) string. " +
            "cmd: %s, response header: %s, out: %s"],
        # Explain: The smcli program was invoked to call z/VM SMAPI for
        #   the indicated API.  The expected response from the smcli
        #   program has a header that contains 3 integers followed by
        #   the string '(details)'.  The response returned by the program
        #   does not have the expected header.  This indicates a problem
        #   in the smcli program or a problem invoking the smcli program.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure.  If it is not a
        #   Linux permission problem then investigate a possible coding
        #   error in the smcli program.  Correct the problem and reinvoke
        #   the function.
    '0302': [{'overallRC': 25, 'rc': 302, 'rs': 0},
            "ULT%s0302E SMAPI API failed: %s, word 1 in " +
            "the response header is not an integer or in the range of " +
            "expected values. word 1: %s, cmd: %s, response " +
            "header: %s, out: %s"],
        # Explain: The smcli program was invoked to call z/VM SMAPI for
        #   the indicated API.  The expected response from the smcli
        #   program has a header that contains 3 integers followed by
        #   the string '(details)'.  The first word should provide the
        #   overall return code of the smcli invocation that indicates
        #   where the failure occurred.  However, it does not represent
        #   an integer value or is not the expected error values of
        #   8, 24 or 25.  This indicates a problem in the smcli program.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure.
        #   Investigate a possible coding error in the smcli program.
        #   Correct the problem and reinvoke the function.
    '0303': [{'overallRC': 25, 'rc': 303, 'rs': 0},
            "ULT%s0303E SMAPI API failed: %s, word 2 in the response " +
            "header is not an integer. word 2: %s, cmd: %s, response " +
            "header: %s, out: %s"],
        # Explain: The smcli program was invoked to call z/VM SMAPI for
        #   the indicated API.  The expected response from the smcli
        #   program has a header that contains 3 integers followed by
        #   the string '(details)'.  The second word should provide the
        #   specific return code of the smcli invocation.  However, it
        #   does not represent an integer value.  This indicates a
        #   problem in the smcli program.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure.
        #   You may need an update to the smcli program.
        #   Correct the problem and reinvoke the function.
    '0304': [{'overallRC': 25, 'rc': 304, 'rs': 0},
            "ULT%s0304E SMAPI API failed: %s, word 3 in the response " +
            "header is not an integer. word 3: %s, cmd: %s, response " +
            "header: %s, out: %s"],
        # Explain: The smcli program was invoked to call z/VM SMAPI for
        #   the indicated API.  The expected response from the smcli
        #   program has a header that contains 3 integers followed by
        #   the string '(details)'.  The third word should provide
        #   the reason code or errno, depending on the error.  However,
        #   it does not represent an integer value.  This indicates
        #   a problem in the smcli program.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure.
        #   You may need an update to the smcli program.
        #   Correct the problem and reinvoke the function.
    '0305': [{'overallRC': 99, 'rc': 305, 'rs': 0},
            "ULT%s0305E Exception received on an attempt to " +
            "communicate with SMAPI, cmd: %s, exception: %s, " +
            "details: %s"],
        # Explain: The function attempted to invoke the smcli
        #   program to communicate with z/VM SMAPI.  This failed
        #   due to the exception shown in the message.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure using
        #   the exception and exception details provided in the message.
        #   Reinvoke the function after correcting the problem.
    # 0306-0310: Available

    # IUCV related messages
    '0311': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0311E On %s, command sent through IUCV failed, " +
            "rc in response string is not an integer. " +
            "cmd: %s, rc: %s, out: %s"],
        # Explain: The IUCV client returned a non-integer return
        #   code value.
        # SysAct: Processing of the function terminates.
        # UserResp: Contact the support team with the information
        #   included in the message.  Investigate the problem in the
        #   IUCVCLNT program, fix the code and reinvoke the function.
    '0312': [{'overallRC': 2, 'rc': 2, 'rs': 99},    # dict is not used.
            "ULT%s0312E On %s, command sent through IUCV failed, " +
            "reason code in response string is not an integer. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCV client returned a non-integer reason
        #   code value.
        # SysAct: Processing of the function terminates.
        # UserResp: Contact the support team with the information
        #   included in the message.  The IUCVCLNT program is the probable
        #   cause of the failure.  This will require a code change.
    '0313': [{'overallRC': 2, 'rc': 1},      # dict is not used.
            "ULT%s0313E On %s, command sent through IUCV was not " +
            "authorized or a generic Linux error occurred. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The command that was sent to the target system failed.
        #   The cause of the failure is either a Linux permission problem
        #   for the command being executed or a generic Linux error.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information included in the message to determine
        #   the cause of the failure on the target system and correct the
        #   problem.  After correcting the problem, you should be able to
        #   reinvoke the failing function.
    '0314': [{'overallRC': 2, 'rc': 2},      # dict is not used.
            "ULT%s0314E IUCV client parameter error sending command to %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCVCLNT program communicates with managed
        #   systems using IUCV.  The program detected invocation
        #   errors.  This can be caused by a problem in the level of the
        #   IUCVCLNT program or the function that invoked it.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information included in the message to determine
        #   the cause of the failure.  This could require the support
        #   team to provide a code change to either the IUCVCLNT program
        #   or the code that invoked it.
    '0315': [{'overallRC': 2, 'rc': 4},      # dict is not used.
            "ULT%s0315E IUCV socket error sending command to %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCVCLNT program communicates with managed
        #   systems using IUCV.  The program encountered an IUCV
        #   communication failure when it attempted to send a
        #   command to the managed system.
        #   This is probably caused by a failure in the managed system
        #   that prevents the system from receiving the command.
        #   One cause could be that the system logged off z/VM.
        #   Another cause is that the managed system is not running the
        #   related IUCV daemon or has not authorized access by
        #   the system contacting it in the /etc/iucv_authorized_userid
        #   file.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information included in the message to
        #   determine the cause of the failure.  Reinvoke the function
        #   after you correct the problem.
    '0316': [{'overallRC': 2, 'rc': 8},      # dict is not used.
            "ULT%s0316E On %s, command sent through IUCV failed. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The command that was sent to the target system failed.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information included in the message to
        #   determine the cause of the failure.  Reinvoke the function
        #   after you correct the problem.
    '0317': [{'overallRC': 2, 'rc': 16},     # dict is not used.
            "ULT%s0317E File transport failure while processing " +
            "command for %s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCVCLNT program failed to send a file to
        #   the target system.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information included in the message to
        #   determine the cause of the failure.  Reinvoke the function
        #   after you correct the problem.
    '0318': [{'overallRC': 2, 'rc': 32},     # dict is not used.
            "ULT%s0318E On %s, IUCV server file was not found. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCVCLNT program failed to find the IUCVSERV
        #   file on the local system.  This file is expected to exist
        #   in the same directory as the IUCVCLNT program.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the reason that the IUCVSERV file could
        #   not be located and correct the problem.  Reinvoke the
        #   function after you correct the problem.
    '0319': [{'overallRC': 2},               # dict is not used.
            "ULT%s0319E Unrecognized IUCV client error encountered " +
            "while sending a command through IUCV to $s. " +
            "cmd: %s, rc: %s, rs: %s, out: %s"],
        # Explain: The IUCVCLNT program returned a non-zero return code
        #   that does not correspond to a recognized error value.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the error using the
        #   information in the message.  Log files on the local system
        #   and the target system may contain useful information to
        #   identify the failure.  Reinvoke the function after you
        #   correct the problem.

    # General subfunction processing messages
    '0400': [{'overallRC': 4, 'rc': 4, 'rs': 400},
            "ULT%s0400E The worker script %s does not exist."],
        # Explain: The activation engine modification script specified
        #   for "aeScript" cannot be found.
        # SysAct: Processing of the function ends with no action
        #   taken.
        # UserResp: Correct the function call to point to an existing script
        #   and reinvoke the function.
    '0401': [{'overallRC': 4, 'rc': 7, 'rs': 401},
            "ULT%s0401E Failed to punch %s file to guest: %s, out: %s"],
        # Explain: The vmur punch command failed for the specified
        #   reason.
        # SysAct: Processing of the function ends with no action
        #   taken.
        # UserResp: Look up the reason the vmur command failed, correct
        #   the problem and reinvoke the function.
    '0402': [{'overallRC': 4, 'rc': 5, 'rs': 402},
            "ULT%s0402E No information was found for the specified " +
            "pool(s): %s"],
        # Explain: Image_Volume_Space_Query_DM returned successfully
        #   but the list of pools of the specified names was empty.
        # SysAct: Processing terminates with an error.
        # UserResp:  Correct the function call to query existing pools and
        #   reinvoke the function.
    '0403': [{'overallRC': 4, 'rc': 99, 'rs': 403},     # dict is not used.
            "ULT%s0403E  Failed to purge reader file %s, out: %s"],
        # Explain: The vmcp purge reader file command failed.
        #   The system was already in the process of cleaning up from a
        #   failed attempt to punch a file, so the error processing
        #   continues.
        # SysAct: Error processing continues.
        # UserResp: Manually clean up the specified reader file using
        #   CP commands to avoid problems with old files or spool space
        #   filling up.
    '0404': [{'overallRC': 4, 'rc': 8, 'rs': 404},
            "ULT%s0404E Failed to spool the punch to the specified class %s" +
            ", out:%s "],
        # Explain: The vmcp change reader command failed with the
        #   specified output.
        # SysAct: Processing of the function ends with no action
        #   taken.
        # UserResp: Look up the reason the change reader command failed
        #   in the CP messages book or vmcp help.  Correct the problem
        #   and reinvoke the function.
    '0405': [{'overallRC': 4, 'rc': 6, 'rs': 405},
            "ULT%s0405E Unable to obtain information related to: " +
            "%s. Command used was: %s. Output was: %s"],
        # Explain: While gathering hypervisor information, one of the
        #   commands used failed and that piece of information could
        #   not be queried.
        # SysAct: The getHost GENERAL function returns "no info" for
        #   the specified hypervisor information.
        # UserResp: If the information is needed, investigate the
        #   failure, correct it and reinvoke the function.
    '0406': [{'overallRC': 4, 'rc': 9, 'rs': 406},
            "ULT%s0406E Failed to punch %s because of VMUR timeout "],
        # Explain: When punching a file to the reader, the vmur punch
        #   command is issued up to 5 times with increasing timeouts.
        #   This error comes after the 5th try if the vmur command
        #   was still unsuccessful.
        # SysAct:  Processing of the function ends with no action taken.
        # UserResp: This error could be because of another process
        #   also issuing vmur commands at the same time.  Wait a few
        #   seconds and reinvoke the function.
    '0407': [{'overallRC': 4, 'rc': 4, 'rs': 407},     # dict is not used.
            "ULT%s0407W Unable to spool reader to all classes, " +
            "it is possible that there may be additional console " +
            "files available that are not listed in the response. " +
            "Response from %s is %s"],
        # Explain: The vmcp spool reader class * command was not
        #   successful.  This means the reader could not be changed
        #   to get files of all classes, and thus there could be
        #   files that are ignored.
        # SysAct: Processing of the function continues.
        # UserResp: If missing files are suspected, investigate the
        #   cause of the failure in the CP messages book or vmcp
        #   help and reinvoke the function.
    '0408': [{'overallRC': 4, 'rc': 4, 'rs': 408},
            "ULT%s0408E Error getting list of files in the reader " +
            "to search for logs from user %s. Response from %s is %s"],
        # Explain: The vmur list command failed.  The list of files
        #   in the user's reader could not be determined.
        # SysAct:  Processing of the function ends with no action taken.
        # UserResp: Investigate the failure in vmur and correct the
        #   problem, then reinvoke the function.
    '0409': [{'overallRC': 4, 'rc': 4, 'rs': 409},
            "ULT%s0409E Unable to get console log for user %s. " +
            "The userid is either: not logged on, not spooling " +
            "its console, or has not created any console output. " +
            "Error rc=rs=8 returned from " +
            "Image_Console_Get."],
        # Explain: The Image_Console_Get SMAPI call returned that
        #   there were no spool files available for that user.
        # SysAct: Processing of the function ends with no action taken.
        # UserResp: Check that the user is logged on, has issued a
        #   SPOOL CONSOLE command and has done some actions that
        #   would result in console output, then reinvoke the function.
    '0410': [{'overallRC': 4, 'rc': 4, 'rs': 410},
            "ULT%s0410E Unable to get console log for user %s " +
            "no spool files were found in our reader from this " +
            "user, it is possible another process has already " +
            "received them."],
        # Explain: The Image_Console_Get SMAPI call should have
        #   put files of class T and "CON" with the userid as the
        #   filename in our reader.  However no files were found
        #   in the vmur list output with these characteristcs.
        # SysAct: Processing of the function ends with no action taken.
        # UserResp: Likely another process in this virtual machine
        #   has already processed the spool files. They are gone.
    '0411': [{'overallRC': 4, 'rc': 4, 'rs': 411},
            "ULT%s0411E Unable to receive console output file. " +
            "Reader not online.  /sys/bus/ccw/drivers/vmur/0.0.000c" +
            "/online = 0"],
        # Explain: The reader is typically at virtual device address
        #   x'000C'.  Linux does not believe this device is online.
        # SysAct:  Processing of the function ends with no action taken.
        # UserResp: If the reader is at a different virtual device
        #   address, update the SMUT code to recognize the alternative
        #   device address, otherwise bring the reader at x'000C' online
        #   to Linux.  Then, reinvoke the function.
    '0412': [{'overallRC': 4, 'rc': 4, 'rs': 412},     # dict is not used.
            "ULT%s0412E Malformed reply from SMAPI, unable to fill " +
            "in performance information, exception: %s, " +
            "details: %s, Response: %s"],
        # Explain: An error was encountered while processing the
        #   response information from the SMAPI Image_Performance_Query
        #   API.  The response is not in the expected format.
        #   The exception that occurred during processing of the
        #   response, its details and the response are included
        #   in the message.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure.  A code change
        #   may be needed in the function or in the z/VM SMAPI code.
        #   After correcting the code, reinvoke the function.
    '0413': [{'overallRC': 99, 'rc': 99, 'rs': 413},
            "ULT%s0413E Userid '%s' did not enter the expected " +
            "operating system state of '%s' in %i seconds."],
        # Explain: The managed system did not enter the operating
        #   system state that was shown in the message in the
        #   maximum number of seconds allowed for this to happen.
        #   The maximum number of seconds a combination of the,
        #   specified or defaulted, polling interval and maximum
        #   maximum number of polling attempts.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure and correct
        #   the cause.
    '0414': [{'overallRC': 99, 'rc': 99, 'rs': 414},
            "ULT%s0414E Userid '%s' did not enter the expected " +
            "virtual machine state of '%s' in %i seconds."],
        # Explain: The managed system did not enter the virtual
        #   machine log on/off state that was shown in the message
        #   in the maximum number of seconds allowed for this to happen.
        #   The maximum number of seconds a combination of the,
        #   specified or defaulted, polling interval and maximum
        #   maximum number of polling attempts.
        # SysAct: Processing of the function terminates.
        # UserResp: Determine the cause of the failure and correct
        #   the cause.
    '0415': [{'overallRC': 3, 'rc': 415},    # rs comes from failing rc
            "ULT%s0415E Command failed: '%s', rc: %i out: %s"],
        # Explain: The indicated command failed.  The return code
        #   and output from the command are shown.
        # SysAct: Function processing terminates.
        # UserResp: Use the information provided with the message
        #   to determine the cause of the failure and correct the
        #   problem.  Reinvoke the function after you correct the
        #   problem.
    '0416': [{'overallRC': 99, 'rc': 99, 'rs': 416},
            "ULT%s0416E Command returned a response " +
            "containing '%s' but did not have at least %i words " +
            "following it. cmd: '%s', out: '%s'"],
        # Explain: A command was invoked that returned a successful
        #   return code indication.  The response contained the
        #   expected string but did not contain the expected number
        #   of words that follow the string.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information provided in the message
        #   to determine the cause of the problem and correct it.
        #   Reinvoke the function after you correct the problem.
    '0417': [{'overallRC': 99, 'rc': 99, 'rs': 417},
            "ULT%s0417E Command did not return the expected response " +
            "containing '%s', cmd: '%s', out: '%s'"],
        # Explain: A command was invoked that returned a successful
        #   return code indication.  The response did not contain the
        #   expected string.
        # SysAct: Processing of the function terminates.
        # UserResp: Use the information provided in the message
        #   to determine the reason the identified string was not
        #   present in the response to identify the cause.
        #   Reinvoke the function after you correct the problem.
    '0418': [{'overallRC': 99, 'rc': 99, 'rs': 418},
            "ULT%s0418E Userid %s is not logged on to this system."],
        # Explain: A CP message HCP0045E was returned, indicating the
        #   userid specified is not logged on to this z/VM system,
        #   thus it cannot be relocated.
        # SysAct:  Processing of the function ends with no action taken.
        # UserResp: Correct the function call to specify a correct userid and
        #   reinvoke the function.
    '0419': [{'overallRC': 99, 'rc': 99, 'rs': 419},
            "ULT%s0419E A relocation is not in progress for userid %s."],
        # Explain: An attempt was made to query or cancel a relocation
        #   for a user, but the SMAPI command indicated that no
        #   relocation was in progress.
        # SysAct:  Processing of the function ends with no action taken.
        # UserResp: Reinvoke the function for a relocation that is in
        #   progress.
    '0420': [{'overallRC': 99, 'rc': 99, 'rs': 420},     # dict is not used.
            "ULT%s0420E An error occurred issuing a %s for userid %s. " +
            "Please look up message(s): %s in the CP Messages book for " +
            "more information."],
        # Explain: The VMRELOCATE command returns a list of messages
        #   containing all the problems encountered when trying to issue
        #   the command.
        # SysAct:   Processing of the function ends with no action taken.
        # UserResp: Look up the codes provided in the CP messages book,
        #   correct the problems and reinvoke the function.
    '0421': [{'overallRC': 99, 'rc': 421, 'rs': 0},
            "ULT%s0421E Exception received on an attempt to " +
            "execute a cmd: %s, exception: %s, " +
            "details: %s"],
        # Explain: The command indicated by the message failed.
        #   The error message contains exception name and details
        #   contained in the exception.
        # SysAct:   Processing of the function ends with no further
        #   action taken.
        # UserResp: Use the information in the message to determine
        #   the cause of the error and correct the problem.
        #   Reinvoke the function after you have corrected the problem.
    '0422': [{'overallRC': 99, 'rc': 422, 'rs': 0},
            "ULT%s0422W Exception received on an attempt to " +
            "execute a cmd: %s, exception: %s, " +
            "details: %s. Will attempt to continue processing."],
        # Explain: While trying to execute a vmcp command, an error
        #   occurred. However the vmcp command was not central
        #   to processing the subfunction, so processing
        #   continues.
        # SysAct: Function processing continues.
        # UserResp: If there is reason to suspect the function did
        #   not execute completely, investigate the error.  Otherwise
        #   ignore this message.
    '0423': [{'overallRC': 4, 'rc': 4, 'rs': 423},    # dict is not used.
            "ULT%s0423W Unable to spool reader to all classes, " +
            "it is possible that there may be additional console " +
            "files available that are not listed in the response. " +
            "Command: %s, exception %s, details %s.  Will attempt " +
            "to continue processing."],
        # Explain: The vmcp spool reader class * command was not
        #   successful.  This means the reader could not be changed
        #   to get files of all classes, and thus there could be
        #   files that are ignored.  The exception was of a different
        #   type than in message 407.
        # SysAct: Processing of the function continues.
        # UserResp: If missing files are suspected, investigate the
        #   cause of the failure in the CP messages book or vmcp
        #   help and reinvoke the function.
    '0424': [{'overallRC': 4, 'rc': 4, 'rs': 424},
            "ULT%s0424E Failed to transfer %s file to guest: %s, out: %s"],
        # Explain: The vmcp transfer command failed for the specified
        #   reason.
        # SysAct: Processing of the function ends with no action
        #   taken.
        # UserResp: Look up the reason the vmcp transfer command failed,
        #   correct the problem and reinvoke the function.
    # 5000-6100: Reserved for SMCLI
    }
