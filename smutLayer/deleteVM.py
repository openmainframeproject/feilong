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
import msgs
from vmUtils import invokeSMCLI, isLoggedOn

modId = "DVM"
version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
    'DIRECTORY': ['deleteMachine', lambda rh: deleteMachine(rh)],
    'HELP': ['help', lambda rh: help(rh)],
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
The dictionary followng the subfunction name uses the keyword from the
command as a key.  Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
"""
keyOpsList = {
    'DIRECTORY': {'--showparms': ['showParms', 0, 0]},
    'HELP': {},
    'VERSION': {},
    }


def deleteMachine(rh):
    """
    Delete a virtual machine from the user directory.

    Input:
       Request Handle with the following properties:
          function    - 'DELETEVM'
          subfunction - 'DIRECTORY'
          userid      - userid of the virtual machine to be deleted.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter deleteVM.deleteMachine")

    results = {'overallRC': 0, 'rc': 0, 'rs': 0}

    # Is image logged on ?
    state = 'on'    # Assume 'on'.
    results = isLoggedOn(rh, rh.userid)
    if results['overallRC'] != 0:
        # Cannot determine the log on/off state.
        # Message already included.  Act as if it is 'on'.
        pass
    elif results['rs'] == 0:
        # State is powered on.
        pass
    else:
        state = 'off'
        # Reset values for rest of subfunction
        results['overallRC'] = 0
        results['rc'] = 0
        results['rs'] = 0

    if state == 'on':
        parms = ["-T", rh.userid, "-f IMMED"]
        results = invokeSMCLI(rh, "Image_Deactivate", parms)
        if results['overallRC'] == 0:
            pass
        elif (results['overallRC'] == 8 and results['rc'] == 200 and
            (results['rs'] == 12 or results['rs'] == 16)):
            # Tolerable error.  Machine is already in or going into the state
            # that we want it to enter.
            rh.updateResults({}, reset=1)
        else:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)  # Use results returned by invokeSMCLI

    if results['overallRC'] == 0:
        parms = ["-T", rh.userid, "-e", "0"]
        results = invokeSMCLI(rh, "Image_Delete_DM", parms)
        if results['overallRC'] != 0:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)  # Use results returned by invokeSMCLI

    rh.printSysLog("Exit deleteVM.deleteMachine, rc: " +
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

    rh.printSysLog("Enter deleteVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: deleteVM." +
            str(subfuncHandler[rh.subfunction][0]) + "(reqHandle)")
        rh.printLn("N", "  function: " + rh.function)
        rh.printLn("N", "  userid: " + rh.userid)
        rh.printLn("N", "  subfunction: " + rh.subfunction)
        rh.printLn("N", "  parms{}: ")
        for key in rh.parms:
            if key != 'showParms':
                rh.printLn("N", "    " + key + ": " +
                    str(rh.parms[key]))
        rh.printLn("N", " ")

    # Call the subfunction handler
    subfuncHandler[rh.subfunction][1](rh)

    rh.printSysLog("Exit deleteVM.doIt, rc: " + str(rh.results['overallRC']))
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
    Produce help output specifically for DeleteVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(rh)
    showOperandLines(rh)
    return 0


def parseCmdline(rh):
    """
    Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter deleteVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit deleteVM.parseCmdLine, rc: " +
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

    rh.printSysLog("Exit deleteVM.parseCmdLine, rc: " +
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
        " DeleteVM <userid> directory")
    rh.printLn("N", "  python " + rh.cmdName + " DeleteVM help")
    rh.printLn("N", "  python " + rh.cmdName +
        " DeleteVM version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the DeleteVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      directory     - " +
        "Delete a virtual machine from the user directory.")
    rh.printLn("N", "      help          - " +
        "Displays this help information.")
    rh.printLn("N", "      version       - " +
        "Show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      <userid>      - " +
        "Userid of the target virtual machine")

    return
