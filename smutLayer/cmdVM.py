# CmdVM functions for Systems Management Ultra Thin Layer
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
import types
from vmUtils import execCmdThruIUCV

version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'CMD':      ['invokeCmd', lambda rh: invokeCmd(rh)],
    'HELP':     ['help', lambda rh: help(rh)],
    'VERSION':  ['getVersion', lambda rh: getVersion(rh)],
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
posOpsList = {
    'CMD': [
               ['Command to send', 'cmd', True, 2],
           ],
}

"""
List of additional operands/options supported by the various subfunctions.
The dictionary followng the subfunction name uses the keyword from the command
as a key.  Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
"""
keyOpsList = {
    'CMD': { 
        '--showparms': ['showParms', 0, 0],
    },
}

def doIt(rh):
    """
    Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    rh.printSysLog("Enter cmdVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: cmdVM." +
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

    rh.printSysLog("Exit cmdVM.doIt, rc: " + str(rc))
    return rc

def getVersion(rh):
    """
    Get the version of this function.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printLn("N",  "Version: " + version)
    return 0

def help(rh):
    """
    Produce help output specifically for CmdVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(rh)
    showOperandLines(rh)
    return 0

def invokeCmd(rh):
    """
    Invoke the command in the virtual machine's operating system.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine
          parms['cmd']   - Command to send

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter cmdVM.invokeCmd, userid: " + rh.userid)

    results = execCmdThruIUCV(rh, rh.userid, rh.parms['cmd'])

    if results['overallRC'] == 0:
        rh.printLn("N", results['response'])
    else:
        if isinstance(rh.parms['cmd'], types.ListType):
            cmdString = ' '.join(rh.parms['cmd'])
        else:
            cmdString = rh.parms['cmd']
        rh.printLn("ES",  "Command failed: '" + cmdString + "', out: '" +
            results['response'] + "', rc: " + str(results['overallRC']))
        rh.updateResults(results)

    rh.printSysLog("Exit cmdVM.invokeCmd, rc: " + str(results['overallRC']))
    return results['overallRC']

def parseCmdline(rh):
    """
    Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    rh.printSysLog("Enter cmdVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        rh.printLn("ES",  "Userid is missing")
        rh.updateResults({ 'overallRC': 1 })
        rh.printSysLog("Exit cmdVM.parseCmdLine, rc: " + rc)
        return 1

    if rh.totalParms == 2:
        rh.subfunction = rh.userid
        rh.userid = ''

    if rh.totalParms >= 3:
        rh.subfunction = rh.request[2].upper()

    # Verify the subfunction is valid.
    if rh.subfunction not in subfuncHandler:
        list = ', '.join(sorted(subfuncHandler.keys()))
        rh.printLn("ES", "Subfunction is missing.  " +
                "It should be one of the following: " + list + ".")
        rh.updateResults({ 'overallRC': 4 })
        rc = 4

    # Parse the rest of the command line.
    if rc == 0:
        rh.argPos = 3               # Begin Parsing at 4th operand
        rc = generalUtils.parseCmdline(rh, posOpsList, keyOpsList)

    rh.printSysLog("Exit cmdVM.parseCmdLine, rc: " + str(rc))
    return rc

def showInvLines(rh):
    """
    Produce help output related to command synopsis

    Input:
       Request Handle
    """

    if rh.subfunction != '':
        rh.printLn("N", "Usage:")
    rh.printLn("N", "  python " + rh.cmdName +
        " CmdVM <userid> cmd <cmdToSend>")
    rh.printLn("N", "  python " + rh.cmdName +
        " CmdVM help")
    rh.printLn("N", "  python " + rh.cmdName +
        " CmdVM version")
    return

def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N",  "  For the CmdVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      cmd           - " +
        "Send a command to a virtual machine's operating system.")
    rh.printLn("N", "      help          - " +
        "Displays this help information.")
    rh.printLn("N", "      version       - " +
        "show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N",  "Operand(s):")
    rh.printLn("N", "      <userid>      - " +
        "Userid of the target virtual machine")
    rh.printLn("N", "      <cmdToSend>   - " +
        "Command to send to the virtual machine's OS.")

    return
