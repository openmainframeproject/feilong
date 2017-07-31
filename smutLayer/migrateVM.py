# MigrateVM functions for Systems Management Ultra Thin Layer
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

import generalUtils
import msgs
from vmUtils import invokeSMCLI

modId = 'MIG'
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'CANCEL': ['cancel', lambda rh: cancelMigrate(rh)],
    'HELP': ['help', lambda rh: help(rh)],
    'MODIFY': ['modify', lambda rh: modifyMigrate(rh)],
    'MOVE': ['move', lambda rh: moveVM(rh)],
    'STATUS': ['status', lambda rh: getStatus(rh)],
    'TEST': ['test', lambda rh: testMigrate(rh)],
    'VERSION': ['getVersion', lambda rh: getVersion(rh)],
    }

"""
List of positional operands based on subfunction.
Each subfunction contains a list which has a dictionary with the following
information for the positional operands:
  - Human readable name of the operand,
  - Property in the parms dictionary to hold the value,
  - Is it required (True) or optional (False),
  - Type of data (1: int, 2: string).
"""
posOpsList = {}

"""
List of additional operands/options supported by the various subfunctions.
The dictionary followng the subfunction name uses the keyword from the command
as a key.  Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
For example, the 'WAITFOR' subfunction has two keyword operands 'poll'
and 'maxwait', and each of them take one additional operand (time in seconds)
which is an int.
"""
keyOpsList = {
    'CANCEL': {'--showparms': ['showParms', 0, 0]},
    'HELP': {},
    'MODIFY': {
        '--maxquiesce': ['maxQuiesce', 1, 1],
        '--maxtotal': ['maxTotal', 1, 1],
        '--showparms': ['showParms', 0, 0]},
    'MOVE': {
        '--destination': ['dest', 1, 2],
        '--forcearch': ['forcearch', 0, 0],
        '--forcedomain': ['forcedomain', 0, 0],
        '--forcestorage': ['forcestorage', 0, 0],
        '--immediate': ['immediate', 0, 0],
        '--maxquiesce': ['maxQuiesce', 1, 1],
        '--maxtotal': ['maxTotal', 1, 1],
        '--showparms': ['showParms', 0, 0]},
    'STATUS': {
        '--all': ['all', 0, 0],
        '--incoming': ['incoming', 0, 0],
        '--outgoing': ['outgoing', 0, 0],
        '--showparms': ['showParms', 0, 0]},
    'TEST': {
        '--destination': ['dest', 1, 2],
        '--showparms': ['showParms', 0, 0]},
    'VERSION': {},
    }


def cancelMigrate(rh):
    """
    Cancel an existing VMRelocate request.

    Input:
       Request Handle with the following properties:
          function    - 'MIGRATEVM'
          subfunction - 'CANCEL'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.cancelMigrate")

    parms = ["-T", rh.userid, "-k", "action=CANCEL"]
    results = invokeSMCLI(rh, "VMRELOCATE", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        if results['rc'] == 8 and results['rs'] == 3000:
            if "1926" in results['response']:
                # No relocation in progress
                msg = msgs.msg['0419'][1] % (modId, rh.userid)
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0419'][0])
            else:
                # More details in message codes
                lines = results['response'].split("\n")
                for line in lines:
                    if "Details:" in line:
                        codes = line.split(' ', 1)[1]
                msg = msgs.msg['420'][1] % (modId, "VMRELOCATE Cancel",
                                            rh.userid, codes)
                rh.printLn("ES", msg)

    rh.printSysLog("Exit migrateVM.cancelMigrate, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def doIt(rh):
    """
    Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: migrateVM." +
            str(subfuncHandler[rh.subfunction][0]) + "(reqHandle)")
        rh.printLn("N", "  function: " + rh.function)
        rh.printLn("N", "  userid: " + rh.userid)
        rh.printLn("N", "  subfunction: " + rh.subfunction)
        rh.printLn("N", "  parms{}: ")
        for key in rh.parms:
            if key != 'showParms':
                rh.printLn("N", "    " + key + ": " + str(rh.parms[key]))
        rh.printLn("N", " ")

    # Call the subfunction handler
    subfuncHandler[rh.subfunction][1](rh)

    rh.printSysLog("Exit migrateVM.doIt, rc: " + str(rh.results['overallRC']))
    return rh.results['overallRC']


def getStatus(rh):
    """
    Get status of a VMRelocate request.

    Input:
       Request Handle with the following properties:
          function    - 'MIGRATEVM'
          subfunction - 'STATUS'
          userid      - userid of the virtual machine
          parms['all']       - If present, set status_target to ALL.
          parms['incoming']  - If present, set status_target to INCOMING.
          parms['outgoing']  - If present, set status_target to OUTGOING.
          if parms does not contain 'all', 'incoming' or 'outgoing', the
            status_target is set to 'USER <userid>'.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.getStatus")

    parms = ["-T", rh.userid]

    if 'all' in rh.parms:
        parms.extend(["-k", "status_target=ALL"])
    elif 'incoming' in rh.parms:
        parms.extend(["-k", "status_target=INCOMING"])
    elif 'outgoing' in rh.parms:
        parms.extend(["-k", "status_target=OUTGOING"])
    else:
        parms.extend(["-k", "status_target=USER " + rh.userid + ""])

    results = invokeSMCLI(rh, "VMRELOCATE_Status", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        if results['rc'] == 4 and results['rs'] == 3001:
            # No relocation in progress
            msg = msgs.msg['0419'][1] % (modId, rh.userid)
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0419'][0])
    else:
        rh.printLn("N", results['response'])

    rh.printSysLog("Exit migrateVM.getStatus, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getVersion(rh):
    """
    Get the version of this function.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printLn("N", "Version: " + version)
    return 0


def help(rh):
    """
    Produce help output specifically for MigrateVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(rh)
    showOperandLines(rh)
    return 0


def modifyMigrate(rh):
    """
    Modify an existing VMRelocate request.

    Input:
       Request Handle with the following properties:
          function    - 'MIGRATEVM'
          subfunction - 'MODIFY'
          userid      - userid of the virtual machine
          parms['maxQuiesce'] - maximum quiesce time in seconds,
                                or -1 to indicate no limit.
          parms['maxTotal']   - maximum total time in seconds,
                                or -1 to indicate no limit.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.modifyMigrate")

    parms = ["-T", rh.userid]

    if 'maxQuiesce' in rh.parms:
        if rh.parms['maxQuiesce'] == -1:
            parms.extend(["-k", "max_quiesce=NOLIMIT"])
        else:
            parms.extend(["-k", "max_quiesce=" + str(rh.parms['maxQuiesce'])])
    if 'maxTotal' in rh.parms:
        if rh.parms['maxTotal'] == -1:
            parms.extend(["-k", "max_total=NOLIMIT"])
        else:
            parms.extend(["-k", "max_total=" + str(rh.parms['maxTotal'])])

    results = invokeSMCLI(rh, "VMRELOCATE_Modify", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        if results['rc'] == 8 and results['rs'] == 3010:
            if "1926" in results['response']:
                # No relocations in progress
                msg = msgs.msg['0419'][1] % (modId, rh.userid)
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0419'][0])
            else:
                # More details in message codes
                lines = results['response'].split("\n")
                for line in lines:
                    if "Details:" in line:
                        codes = line.split(' ', 1)[1]
                msg = msgs.msg['0420'][1] % (modId, "VMRELOCATE Modify",
                                             rh.userid, codes)
                rh.printLn("ES", msg)

    rh.printSysLog("Exit migrateVM.modifyMigrate, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def moveVM(rh):
    """
    Initiate a VMRelocate request to move a userid.

    Input:
       Request Handle with the following properties:
          function    - 'MIGRATEVM'
          subfunction - 'MOVE'
          userid      - userid of the virtual machine
          parms['destination']  - target SSI member
          parms['forcearch']    - if present, force=architecture is set.
          parms['forcedomain']  - if present, force=domain is set.
          parms['forcestorage'] - if present, force=storage is set.
          parms['immediate']    - if present, immediate=YES is set.
          parms['maxquiesce']   - maximum quiesce time in seconds,
                                  or -1 to indicate no limit.
          parms['maxTotal']     - maximum total time in seconds,
                                  or -1 to indicate no limit.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.moveVM")

    parms = ["-T", rh.userid, "-k", "action=MOVE"]

    if 'dest' in rh.parms:
        parms.extend(["-k", "destination=" + rh.parms['dest']])

    forceOption = ''
    if 'forcearch' in rh.parms:
        forceOption = "ARCHITECTURE "
    if 'forcedomain' in rh.parms:
        forceOption = forceOption + "DOMAIN "
    if 'forcestorage' in rh.parms:
        forceOption = forceOption + "STORAGE "
    if forceOption != '':
        parms.extend(["-k", "\'force=" + forceOption + "\'"])

    if 'immediate' in rh.parms:
        parms.extend(["-k", "\'immediate=YES"])

    if 'maxQuiesce' in rh.parms:
        if rh.parms['maxQuiesce'] == -1:
            parms.extend(["-k", "max_quiesce=NOLIMIT"])
        else:
            parms.extend(["-k", "max_quiesce=" + str(rh.parms['maxQuiesce'])])
    if 'maxTotal' in rh.parms:
        if rh.parms['maxTotal'] == -1:
            parms.extend(["-k", "max_total=NOLIMIT"])
        else:
            parms.extend(["-k", "max_total=" + str(rh.parms['maxTotal'])])

    results = invokeSMCLI(rh, "VMRELOCATE", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        if results['rc'] == 8 and results['rs'] == 3000:
            if "0045" in results['response']:
                # User not logged on
                msg = msgs.msg['0418'][1] % (modId, rh.userid)
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0418'][0])
            else:
                # More details in message codes
                lines = results['response'].split("\n")
                for line in lines:
                    if "Details:" in line:
                        codes = line.split(' ', 1)[1]
                msg = msgs.msg['0420'][1] % (modId, "VMRELOCATE Move",
                                             rh.userid, codes)
                rh.printLn("ES", msg)

    rh.printSysLog("Exit migrateVM.moveVM, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def parseCmdline(rh):
    """
    Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit migrateVM.parseCmdLine, rc: " +
            rh.results['overallRC'])
        return rh.results['overallRC']

    if rh.totalParms == 2:
        rh.subfunction = rh.userid
        rh.userid = ''

    if rh.totalParms >= 3:
        rh.subfunction = rh.request[2].upper()

    # Verify the subfunction is valid.
    if rh.subfunction not in subfuncHandler:
        # Subfunction is missing.
        subList = ', '.join(sorted(subfuncHandler.keys()))
        msg = msgs.msg['0011'][1] % (modId, subList)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0011'][0])

    # Parse the rest of the command line.
    if rh.results['overallRC'] == 0:
        rh.argPos = 3               # Begin Parsing at 4th operand
        generalUtils.parseCmdline(rh, posOpsList, keyOpsList)

    rh.printSysLog("Exit migrateVM.parseCmdLine, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def showInvLines(rh):
    """
    Produce help output related to command synopsis

    Input:
       Request Handle
    """

    if rh.subfunction != '':
        rh.printLn("N", "Usage:")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM <userid> cancel")
    rh.printLn("N", "  python " + rh.cmdName + " MigrateVM help")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM <userid> modify [--maxtotal <maxVal>]")
    rh.printLn("N", "                    [--maxquiesce <maxQVal>]")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM <userid> move --destination <ssiMember>")
    rh.printLn("N", "                    [--immediate] [--forcearch] " +
                      "[--forcedomain] [--forcestorage]")
    rh.printLn("N", "                    [--maxtotal <maxVal>] " +
                      "[--maxquiesce <maxQVal>]")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM <userid> status " +
                      "[--all | --incoming | --outgoing]")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM <userid> test --destination <ssiMember>")
    rh.printLn("N", "  python " + rh.cmdName +
                      " MigrateVM version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the MigrateVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      cancel   - " +
        "cancels the relocation of the specified virtual machine.")
    rh.printLn("N", "      help     - Displays this help information.")
    rh.printLn("N", "      modify   - " +
        "modifies the time limits associated with the relocation already")
    rh.printLn("N", "                 in progress .")
    rh.printLn("N", "      move     - " +
        "moves the specified virtual machine, while it continues to run,")
    rh.printLn("N", "                 " +
        "to the specified system within the SSI cluster.")
    rh.printLn("N", "      status   - requests information about " +
        "relocations currently in progress.")
    rh.printLn("N", "      test     - tests the specified virtual machine " +
        "and reports whether or not")
    rh.printLn("N", "                 " +
        "it is eligible to be relocated to the specified system.")
    rh.printLn("N", "      version  - show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      --all                  - All relocations")
    rh.printLn("N", "      --destination <dest>   - " +
        "Specifies the SSI name of the target destination")
    rh.printLn("N", "                               z/VM system ")
    rh.printLn("N", "      --forcearch            - " +
        "force relocations past architecture checks.")
    rh.printLn("N", "      --forcedomain          - " +
        "force relocations past domain checks.")
    rh.printLn("N", "      --forcestorage         - " +
        "force relocations past storage checks.")
    rh.printLn("N", "      --immediate            - " +
        "causes the VMRELOCATE command to do one early")
    rh.printLn("N", "                               " +
        "pass through virtual machine storage and then go")
    rh.printLn("N", "                               " +
        "directly to the quiesce stage.")
    rh.printLn("N", "      --incoming             - Incoming relocations")
    rh.printLn("N", "      --maxquiesce <maxQVal> - " +
        "indicates the maximum quiesce time (in seconds)")
    rh.printLn("N", "                               for this relocation.")
    rh.printLn("N", "      --maxtotal <maxVal>    - " +
        "indicates the maximum total time (in seconds)")
    rh.printLn("N", "                               " +
        "for relocation to complete.")
    rh.printLn("N", "      --outgoing             - Out-going relocations")
    rh.printLn("N", "      <userid>               - " +
        "Userid of the target virtual machine")

    return


def testMigrate(rh):
    """
    Test the ability to use VMRelocate on the target userid.

    Input:
       Request Handle with the following properties:
          function       - 'MIGRATEVM'
          subfunction    - 'TEST'
          userid         - userid of the virtual machine
          parms['dest']  - Target SSI system.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter migrateVM.testMigrate")

    parms = ["-T", rh.userid, "-k", "action=TEST"]

    if 'dest' in rh.parms:
        parms.extend(["-k", "destination=" + rh.parms['dest']])

    results = invokeSMCLI(rh, "VMRELOCATE", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        if results['rc'] == 4 and results['rs'] == 3000:
            if "0045" in results['response']:
                # User not logged on
                msg = msgs.msg['0418'][1] % (modId, rh.userid)
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0418'][0])
            else:
                # More details in message codes
                lines = results['response'].split("\n")
                for line in lines:
                    if "Details:" in line:
                        codes = line.split(' ', 1)[1]
                msg = msgs.msg['0420'][1] % (modId, "VMRELOCATE Move",
                                             rh.userid, codes)

    rh.printSysLog("Exit migrateVM.testMigrate, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']
