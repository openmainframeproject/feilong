# DeleteVM functions for Systems Management Ultra Thin Layer
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
import subprocess
from subprocess import CalledProcessError
from vmUtils import invokeSMCLI

version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
    'DIRECTORY': ['deleteMachine', 
        lambda reqHandle: deleteMachine(reqHandle) ],
    'HELP': [ 'help', lambda reqHandle: help(reqHandle) ],
    'VERSION': [ 'getVersion', lambda reqHandle: getVersion(reqHandle) ],
    }

# List of positional operands based on subfunction.
# Each subfunction contains a list which has a dictionary with the following
# information for the positional operands:
#   - Human readable name of the operand,
#   - Property in the parms dictionary to hold the value,
#   - Is it required (True) or optional (False),
#   - Type of data (1: int, 2: string).
posOpsList = {}

# List of additional operands/options supported by the various subfunctions.
# The dictionary followng the subfunction name uses the keyword from the
# command as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values (1: int, 2: string)
keyOpsList = {
    'DIRECTORY': {'showparms': ['showParms', 0, 0],},
    'HELP': {},
    'VERSION': {},
    }



def deleteMachine(reqHandle):
    """ Delete a virtual machine from the user directory.

    Input:
       Request Handle with the following properties:
          function    - 'DELETEVM'
          subfunction - 'DIRECTORY'
          userid      - userid of the virtual machine to be deleted.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog("Enter deleteVM.deleteMachine")

    results = { 'overallRC': 0 }

    # Is image logged on
    state = 'off'
    cmd = ("/sbin/vmcp q user " + reqHandle.userid + " 2>/dev/null | " +
              "sed 's/HCP\w\w\w045E.*/off/' | sed 's/HCP\w\w\w361E.*/off/' | "
              + "sed 's/" + reqHandle.userid + ".*/on/'")
    try:
        state = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                close_fds=True,
                shell=True)

    except CalledProcessError as e:
        # The last SED would have to fail for the exception to be thrown.
        out = e.output
        cmdRC = e.returncode
        reqHandle.printLn("ES",  "Command failed: '" + cmd + "', rc: " +
            str(cmdRC) + " out: " + out)
        state = 'off'       # Treat state as off for this weird case

    if state == 'on':
        cmd = [ "smcli",
            "Image_Deactivate",
            "-T", reqHandle.userid,
            "-f IMMED" ]
    
        results = invokeSMCLI(reqHandle, cmd)
        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd +
                "', out: '" + results['response'] +
                "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    if results['overallRC'] == 0:
        cmd = [ "smcli",
            "Image_Delete_DM",
            "-T", reqHandle.userid,
            "-e", "0" ]
    
        results = invokeSMCLI(reqHandle, cmd)
        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd + 
                "', out: '" + results['response'] + 
                "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit deleteVM.deleteMachine, rc: " +
        str(results['overallRC']))
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
    reqHandle.printSysLog("Enter deleteVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] is True:
        reqHandle.printLn("N", "Invocation parameters: ")
        reqHandle.printLn("N", "  Routine: deleteVM." +
            str(subfuncHandler[reqHandle.subfunction][0]) + "(reqHandle)")
        reqHandle.printLn("N", "  function: " + reqHandle.function)
        reqHandle.printLn("N", "  userid: " + reqHandle.userid)
        reqHandle.printLn("N", "  subfunction: " + reqHandle.subfunction)
        reqHandle.printLn("N", "  parms{}: ")
        for key in reqHandle.parms:
            if key != 'showParms':
                reqHandle.printLn("N", "    " + key + ": " +
                    str(reqHandle.parms[key]))
        reqHandle.printLn("N", " ")

    # Call the subfunction handler
    subfuncHandler[reqHandle.subfunction][1](reqHandle)

    reqHandle.printSysLog("Exit deleteVM.doIt, rc: " + str(rc))
    return rc


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
    """ Produce help output specifically for DeleteVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(reqHandle)
    showOperandLines(reqHandle)
    return 0


def parseCmdline(reqHandle):
    """ Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter deleteVM.parseCmdline")

    if reqHandle.totalParms >= 2:
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn("ES",  "Userid is missing")
        reqHandle.updateResults({ 'overallRC': 1 })
        reqHandle.printSysLog("Exit deleteVM.parseCmdLine, rc: " + rc)
        return 1

    if reqHandle.totalParms == 2:
        reqHandle.subfunction = reqHandle.userid
        reqHandle.userid = ''

    if reqHandle.totalParms >= 3:
        reqHandle.subfunction = reqHandle.request[2].upper()

    # Verify the subfunction is valid.
    if reqHandle.subfunction not in subfuncHandler:
        list = ', '.join(sorted(subfuncHandler.keys()))
        reqHandle.printLn("ES", "Subfunction is missing.  " +
                "It should be one of the following: " + list + ".")
        reqHandle.updateResults({ 'overallRC': 4 })
        rc = 4

    # Parse the rest of the command line.
    if rc == 0:
        reqHandle.argPos = 3               # Begin Parsing at 4th operand
        rc = generalUtils.parseCmdline(reqHandle, posOpsList, keyOpsList)


    reqHandle.printSysLog("Exit deleteVM.parseCmdLine, rc: " + str(rc))
    return rc


def showInvLines(reqHandle):
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Usage:")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " DeleteVM <userid> directory")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + " DeleteVM help")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + 
        " DeleteVM version")
    return


def showOperandLines(reqHandle):
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP':
        reqHandle.printLn("N",  "  For the DeleteVM function:")
    else:
        reqHandle.printLn("N", "Sub-Functions(s):")
    reqHandle.printLn("N", "      directory     - Delete a virtual machine from the user directory.")
    reqHandle.printLn("N", "      help          - Displays this help information.")
    reqHandle.printLn("N", "      version       - Show the version of the power function")
    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Operand(s):")
    reqHandle.printLn("N", "      <userid>      - Userid of the target virtual machine")

    return
