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
from generalUtils import parseCmdline
from vmUtils import invokeSMCLI

version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
    'CANCEL':  ['cancel', lambda reqHandle: cancelMigrate(reqHandle)],
    'HELP':    ['help', lambda reqHandle: help(reqHandle)],
    'MODIFY':  ['modify', lambda reqHandle: modifyMigrate(reqHandle)],
    'MOVE':    ['move', lambda reqHandle: moveVM(reqHandle)],
    'STATUS':  ['status', lambda reqHandle: getStatus(reqHandle)],
    'TEST':    ['test', lambda reqHandle: testMigrate(reqHandle)],
    'VERSION': ['getVersion', lambda reqHandle: getVersion(reqHandle)],
    }

# List of positional operands based on subfunction.
# Each subfunction contains a list which has a dictionary with the following
# information for the positional operands:
#   - Human readable name of the operand,
#   - Property in the parms dictionary to hold the value,
#   - Is it required (True) or optional (False),
#   - Type of data (1: int, 2: string).
posOpsList = {
             }

# List of additional operands/options supported by the various subfunctions.
# The dictionary followng the subfunction name uses the keyword from the command
# as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values (1: int, 2: string)
# For example, the 'WAITFOR' subfunction has two keyword operands 'poll'
# and 'maxwait', and each of them take one additional operand (time in seconds)
# which is an int.
keyOpsList = {
    'CANCEL': { 'showparms'    : ['showParms', 0, 0], },
    'HELP': {},
    'MODIFY': {
                        'maxquiesce'   : ['maxQuiesce', 1, 1],
                        'maxtotal'     : ['maxTotal', 1, 1],
                        'showparms'    : ['showParms', 0, 0], },
    'MOVE': {
                        'destination'  : ['dest', 1, 2],
                        'forcearch'    : ['forcearch', 0, 0],
                        'forcedomain'  : ['forcedomain', 0, 0],
                        'forcestorage' : ['forcestorage', 0, 0],
                        'immediate'    : ['immediate', 0, 0],
                        'maxquiesce'   : ['maxQuiesce', 1, 1],
                        'maxtotal'     : ['maxTotal', 1, 1],
                        'showparms'    : ['showParms', 0, 0], },
    'STATUS': {
                        'all'          : ['all', 0, 0],
                        'incoming'     : ['incoming', 0, 0],
                        'outgoing'     : ['outgoing', 0, 0],
                        'showparms'    : ['showParms', 0, 0], },
    'TEST': {
                        'destination'  : ['dest', 1, 2],
                        'showparms'    : ['showParms', 0, 0], },
    'VERSION': {},
    }



def cancelMigrate(reqHandle):
    """ Cancel an existing VMRelocate request.

    Input:
       Request Handle with the following properties:
          function    - 'MIGRATEVM'
          subfunction - 'CANCEL'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog("Enter migrateVM.cancelMigrate")

    cmd = ["smcli",
            "VMRELOCATE",
            "-T", reqHandle.userid,
            "-k", "action=CANCEL",
          ]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0 :
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit migrateVM.cancelMigrate, rc: " + str(results['overallRC']))
    return results['overallRC']


def doIt(reqHandle):
    """ Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter migrateVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] == True :
        reqHandle.printLn("N", "Invocation parameters: ")
        reqHandle.printLn("N", "  Routine: migrateVM." + str(subfuncHandler[reqHandle.subfunction][0]) + "(reqHandle)")
        reqHandle.printLn("N", "  function: " + reqHandle.function)
        reqHandle.printLn("N", "  userid: " + reqHandle.userid)
        reqHandle.printLn("N", "  subfunction: " + reqHandle.subfunction)
        reqHandle.printLn("N", "  parms{}: ")
        for key in reqHandle.parms :
            if key != 'showParms' :
                reqHandle.printLn("N", "    " + key + ": " + str(reqHandle.parms[key]))
        reqHandle.printLn("N", " ")

    # Call the subfunction handler
    subfuncHandler[reqHandle.subfunction][1](reqHandle)

    reqHandle.printSysLog("Exit migrateVM.doIt, rc: " + str(rc))
    return rc


def getStatus(reqHandle):
    """ Get status of a VMRelocate request.

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

    reqHandle.printSysLog("Enter migrateVM.getStatus")

    cmd = ["smcli",
            "VMRELOCATE_Status",
            "-T", reqHandle.userid,
          ]

    if 'all' in reqHandle.parms :
        cmd.extend(["-k", "status_target=ALL"])
    elif 'incoming' in reqHandle.parms :
        cmd.extend(["-k", "status_target=INCOMING"])
    elif 'outgoing' in reqHandle.parms :
        cmd.extend(["-k", "status_target=OUTGOING"])
    else :
        cmd.extend(["-k", "status_target=USER " + reqHandle.userid + ""])

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0 :
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit migrateVM.getStatus, rc: " + str(results['overallRC']))
    return results['overallRC']


def getVersion(reqHandle):
    """ Get the version of this function.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printLn("N",  "Version: " + version)
    return 0


def help(reqHandle):
    """ Produce help output specifically for MigrateVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(reqHandle)
    showOperandLines(reqHandle)
    return 0


def modifyMigrate(reqHandle):
    """ Modify an existing VMRelocate request.

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

    reqHandle.printSysLog("Enter migrateVM.modifyMigrate")

    cmd = ["smcli",
            "VMRELOCATE_Modify",
            "-T", reqHandle.userid,
          ]

    if 'maxQuiesce' in reqHandle.parms :
        if reqHandle.parms['maxQuiesce'] == -1 :
            cmd.extend(["-k", "max_quiesce=NOLIMIT"])
        else :
            cmd.extend(["-k", "max_quiesce=" + str(reqHandle.parms['maxQuiesce'])])
    if 'maxTotal' in reqHandle.parms :
        if reqHandle.parms['maxTotal'] == -1 :
            cmd.extend(["-k", "max_total=NOLIMIT"])
        else :
            cmd.extend(["-k", "max_total=" + str(reqHandle.parms['maxTotal'])])

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0 :
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit migrateVM.modifyMigrate, rc: " + str(results['overallRC']))
    return results['overallRC']


def moveVM(reqHandle):
    """ Initiate a VMRelocate request to move a userid.

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

    reqHandle.printSysLog("Enter migrateVM.moveVM")

    cmd = ["smcli",
            "VMRELOCATE",
            "-T", reqHandle.userid,
            "-k", "action=MOVE",
          ]

    if 'dest' in reqHandle.parms :
        cmd.extend(["-k", "destination=" + reqHandle.parms['dest']])

    forceOption = ''
    if 'forcearch' in reqHandle.parms :
        forceOption = "ARCHITECTURE "
    if 'forcedomain' in reqHandle.parms :
        forceOption = forceOption + "DOMAIN "
    if 'forcestorage' in reqHandle.parms :
        forceOption = forceOption + "STORAGE "
    if forceOption != '' :
        cmd.extend(["-k", "\'force=" + forceOption + "\'"])

    if 'immediate' in reqHandle.parms:
        cmd.extend(["-k", "\'immediate=YES"])

    if 'maxQuiesce' in reqHandle.parms :
        if reqHandle.parms['maxQuiesce'] == -1 :
            cmd.extend(["-k", "max_quiesce=NOLIMIT"])
        else :
            cmd.extend(["-k", "max_quiesce=" + str(reqHandle.parms['maxQuiesce'])])
    if 'maxTotal' in reqHandle.parms :
        if reqHandle.parms['maxTotal'] == -1 :
            cmd.extend(["-k", "max_total=NOLIMIT"])
        else :
            cmd.extend(["-k", "max_total=" + str(reqHandle.parms['maxTotal'])])

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0 :
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit migrateVM.moveVM, rc: " + str(results['overallRC']))
    return results['overallRC']


def parseCmdline(reqHandle):
    """ Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter migrateVM.parseCmdline")

    if reqHandle.totalParms >= 2 :
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn("ES",  "Userid is missing")
        reqHandle.updateResults({ 'overallRC': 1 })
        reqHandle.printSysLog("Exit migrateVM.parseCmdLine, rc: " + rc)
        return 1

    if reqHandle.totalParms == 2 :
        reqHandle.subfunction = reqHandle.userid
        reqHandle.userid = ''

    if reqHandle.totalParms >= 3 :
        reqHandle.subfunction = reqHandle.request[2].upper()

    # Verify the subfunction is valid.
    if reqHandle.subfunction not in subfuncHandler :
        list = ', '.join(sorted(subfuncHandler.keys()))
        reqHandle.printLn("ES", "Subfunction is missing.  " +
                "It should be one of the following: " + list + ".")
        reqHandle.updateResults({ 'overallRC': 4 })
        rc = 4

    # Parse the rest of the command line.
    if rc == 0 :
        reqHandle.argPos = 3               # Begin Parsing at 4th operand
        rc = generalUtils.parseCmdline(reqHandle, posOpsList, keyOpsList)


    reqHandle.printSysLog("Exit migrateVM.parseCmdLine, rc: " + str(rc))
    return rc


def showInvLines(reqHandle):
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '' :
        reqHandle.printLn("N", "Usage:")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM <userid> cancel")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + " MigrateVM help")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM <userid> modify [maxtotal <maxVal>]")
    reqHandle.printLn("N", "                    [maxquiesce <maxQVal>]")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM <userid> move destination <ssiMember>")
    reqHandle.printLn("N", "                    [immediate] [ forcearch] " +
                      "[ forcedomain] [ forcestorage]")
    reqHandle.printLn("N", "                    [maxtotal <maxVal>] " +
                      "[ maxquiesce <maxQVal>]")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM <userid> status [all | incoming | outgoing]")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM <userid> test destination <ssiMember>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
                      " MigrateVM version")
    return


def showOperandLines(reqHandle):
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP':
        reqHandle.printLn("N",  "  For the MigrateVM function:")
    else:
        reqHandle.printLn("N", "Sub-Functions(s):")
    reqHandle.printLn("N", "      cancel   - cancels the relocation of the specified virtual machine.")
    reqHandle.printLn("N", "      help     - Displays this help information.")
    reqHandle.printLn("N", "      modify   - modifies the time limits associated with the relocation already")
    reqHandle.printLn("N", "                 in progress .")
    reqHandle.printLn("N", "      move     - moves the specified virtual machine, while it continues to run,")
    reqHandle.printLn("N", "                 to the specified system within the SSI cluster.")
    reqHandle.printLn("N", "      status   - requests information about relocations currently in progress.")
    reqHandle.printLn("N", "      test     - tests the specified virtual machine and reports whether or not")
    reqHandle.printLn("N", "                             it is eligible to be relocated to the specified system.")
    reqHandle.printLn("N", "      version  - show the version of the power function")
    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Operand(s):")
    reqHandle.printLn("N", "      all                  - All relocations")
    reqHandle.printLn("N", "      destination <dest>   - Specifies the SSI name of the target destination")
    reqHandle.printLn("N", "                             z/VM system ")
    reqHandle.printLn("N", "      forcearch            - force relocations past architecture checks.")
    reqHandle.printLn("N", "      forcedomain          - force relocations past domain checks.")
    reqHandle.printLn("N", "      forcestorage         - force relocations past storage checks.")
    reqHandle.printLn("N", "      immediate            - causes the VMRELOCATE command to do one early pass")
    reqHandle.printLn("N", "                             through virtual machine storage and then go")
    reqHandle.printLn("N", "                             directly to the quiesce stage.")
    reqHandle.printLn("N", "      incoming             - In-coming relocations")
    reqHandle.printLn("N", "      maxquiesce <maxQVal> - indicates the maximum quiesce time (in seconds)")
    reqHandle.printLn("N", "                             for this relocation.")
    reqHandle.printLn("N", "      maxtotal <maxVal>    - indicates the maximum total time (in seconds) for")
    reqHandle.printLn("N", "                             relocation to complete.")
    reqHandle.printLn("N", "      outgoing             - Out-going relocations")
    reqHandle.printLn("N", "      <userid>             - Userid of the target virtual machine")

    return


def testMigrate(reqHandle):
    """ Test the ability to use VMRelocate on the target userid.

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

    reqHandle.printSysLog("Enter migrateVM.testMigrate")

    cmd = ["smcli",
            "VMRELOCATE",
            "-T", reqHandle.userid,
            "-k", "action=TEST",
          ]

    if 'dest' in reqHandle.parms:
        cmd.extend(["-k", "destination=" + reqHandle.parms['dest']])

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0:
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit migrateVM.testMigrate, rc: " + str(results['overallRC']))
    return results['overallRC']
