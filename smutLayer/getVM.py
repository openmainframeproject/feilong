# GetVM functions for Systems Management Ultra Thin Layer
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

import re

import generalUtils
import msgs
from vmUtils import execCmdThruIUCV, invokeSMCLI

modId = 'GVM'
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'CONSOLEOUTPUT': ['getConsole', lambda rh: getConsole(rh)],
    'DIRECTORY': ['getDirectory', lambda rh: getDirectory(rh)],
    'HELP': ['help', lambda rh: help(rh)],
    'ISREACHABLE': ['checkIsReachable', lambda rh: checkIsReachable(rh)],
    'STATUS': ['getStatus', lambda rh: getStatus(rh)],
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
"""
keyOpsList = {
    'CONSOLEOUTPUT': {'--showparms': ['showParms', 0, 0]},
    'DIRECTORY': {'--showparms': ['showParms', 0, 0]},
    'HELP': {},
    'ISREACHABLE': {'--showparms': ['showParms', 0, 0]},
    'STATUS': {
        '--all': ['allBasic', 0, 0],
        '--cpu': ['cpu', 0, 0],
        '--memory': ['memory', 0, 0],
        '--power': ['power', 0, 0],
        '--showparms': ['showParms', 0, 0]},
    'VERSION': {},
    }


def checkIsReachable(rh):
    """
    Check if a virtual machine is reachable.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getVM.checkIsReachable, userid: " + rh.userid)

    strCmd = "echo 'ping'"
    results = execCmdThruIUCV(rh, rh.userid, strCmd)

    if results['overallRC'] == 0:
        rh.printLn("N", rh.userid + ": reachable")
        reachable = 1
    else:
        # A failure from execCmdThruIUCV is acceptable way of determining
        # that the system is unreachable.  We won't pass along the
        # error message.
        rh.printLn("N", rh.userid + ": unreachable")
        reachable = 0

    rh.updateResults({"rs": reachable})
    rh.printSysLog("Exit getVM.checkIsReachable, rc: 0")
    return 0


def doIt(rh):
    """
    Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: getVM." +
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

    rh.printSysLog("Exit getVM.doIt, rc: " + str(rh.results['overallRC']))
    return rh.results['overallRC']


def getConsole(rh):
    """
    Get the virtual machine's console output.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getVM.getConsole")

    rh.printLn("N", "This subfunction is not implemented yet.")

    # Transfer the console to this virtual machine.
    cmd = ["smcli",
        "Image_Console_Get",
        "-T", rh.userid]

    results = invokeSMCLI(rh, cmd)
    if results['overallRC'] == 0:
        rh.printLn("N", results['response'])
    else:
        # SMAPI API failed.
        strCmd = ' '.join(cmd)
        msg = msgs.msg['0300'][1] % (modId, strCmd,
            results['overallRC'], results['response'])
        rh.printLn("ES", msg)
        rh.updateResults(results)    # Use results from invokeSMCLI

    if results['overallRC'] == 0:
        rh.printSysLog("May need to add onlining of the reader")
        rh.printSysLog("Need to add set the reader class")
        rh.printSysLog("Find the files for the target user")
        rh.printSysLog("Read each file and write it out with printLn")

    rh.printSysLog("Exit getVM.getConsole, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getDirectory(rh):
    """
    Get the virtual machine's directory statements.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    rh.printSysLog("Enter getVM.getDirectory")

    cmd = ["smcli",
            "Image_Query_DM",
            "-T", rh.userid]

    results = invokeSMCLI(rh, cmd)
    if results['overallRC'] == 0:
        results['response'] = re.sub('\*DVHOPT.*', '', results['response'])
        rh.printLn("N", results['response'])
    else:
        # SMAPI API failed.
        strCmd = ' '.join(cmd)
        msg = msgs.msg['0300'][1] % (modId, strCmd,
            results['overallRC'], results['response'])
        rh.printLn("ES", msg)
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit getVM.getDirectory, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getStatus(rh):
    """
    Get the basic status of a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    rh.printSysLog("Enter getVM.getStatus, userid: " + rh.userid)

    rh.printLn("N", "This subfunction is not implemented yet.")

    rh.printSysLog("Exit getVM.getStatus, rc: " + str(rc))
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

    rh.printLn("N", "Version: " + version)
    return 0


def help(rh):
    """
    Produce help output specifically for GetVM functions.

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

    rh.printSysLog("Enter getVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
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

    rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
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
        " GetVM <userid> [ consoleoutput | directory ]")
    rh.printLn("N", "  python " + rh.cmdName +
        " GetVM <userid>")
    rh.printLn("N", "                    " +
        "status [ --all | --cpu | --memory | --power ]")
    rh.printLn("N", "  python " + rh.cmdName + " GetVM help")
    rh.printLn("N", "  python " + rh.cmdName + " GetVM version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the GetVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      consoleoutput - " +
        "Obtains the console log from the virtual machine.")
    rh.printLn("N", "      directory     - " +
        "Displays the user directory lines for the virtual machine.")
    rh.printLn("N", "      help          - " +
        "Displays this help information.")
    rh.printLn("N", "      isreachable   - " +
        "Determine whether the virtual OS in a virtual machine")
    rh.printLn("N", "                      is reachable")
    rh.printLn("N", "      status        - " +
        "show the log on/off status of the virtual machine")
    rh.printLn("N", "      version       - " +
        "show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      <userid>      - " +
        "Userid of the target virtual machine")
    rh.printLn("N", "      [ --all | --cpu | " +
        "--memory | --power ]")
    rh.printLn("N", "                    - " +
        "Returns information machine related to the number")
    rh.printLn("N", "                      " +
        "of virtual CPUs, memory size, power status or all of the")
    rh.printLn("N", "                      information.")

    return
