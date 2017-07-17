# SMAPI functions for Systems Management Ultra Thin Layer
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

modId = 'SMP'
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'API': ['invokeSmapiApi', lambda rh: invokeSmapiApi(rh)],
    'HELP': ['help', lambda rh: help(rh)],
    'VERSION': ['getVersion', lambda rh: getVersion(rh)]}

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
    'API': [
        ['API Name', 'apiName', True, 2]]
     }

"""
List of additional operands/options supported by the various subfunctions.
The dictionary following the subfunction name uses the keyword from the
command as a key.
Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
"""
keyOpsList = {
    'API': {
        '--operands': ['operands', -1, 2],
        '--showparms': ['showParms', 0, 0]}
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

    rh.printSysLog("Enter smapi.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms']:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: smapi." +
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

    rh.printSysLog("Exit smapi.doIt, rc: " + str(rh.results['overallRC']))
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
    Produce help output specifically for SMAPI functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines(rh)
    showOperandLines(rh)
    return 0


def invokeSmapiApi(rh):
    """
    Invoke a SMAPI API.

    Input:
       Request Handle with the following properties:
          function    - 'SMAPI'
          subfunction - 'API'
          userid      - 'HYPERVISOR'
          parms['apiName']   - Name of API as defined by SMCLI
          parms['operands']  - List (array) of operands to send or
                               an empty list.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter smapi.invokeSmapiApi")
    if rh.userid != 'HYPERVISOR':
        userid = rh.userid
    else:
        userid = 'dummy'

    parms = ["-T", userid]
    if 'operands' in rh.parms:
        parms.extend(rh.parms['operands'])

    results = invokeSMCLI(rh, rh.parms['apiName'], parms)
    if results['overallRC'] == 0:
        rh.printLn("N", results['response'])
    else:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit smapi.invokeCmd, rc: " + str(rh.results['overallRC']))
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

    rh.printSysLog("Enter smapi.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit smapi.parseCmdLine, rc: " +
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

    rh.printSysLog("Exit smapi.parseCmdLine, rc: " +
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
    rh.printLn("N", "  python " + rh.cmdName + " SMAPI <userid> " +
        "api <apiName> [--operands <apiOperands>]")
    rh.printLn("N", "  python " + rh.cmdName + " SMAPI help")
    rh.printLn("N", "  python " + rh.cmdName + " SMAPI version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the " + rh.function + " function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      api           - Invoke a SMAPI API.")
    rh.printLn("N", "      help          - Displays this help information.")
    rh.printLn("N", "      version       - " +
        "show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      <userid>      - " +
        "Userid of the target virtual machine")
    rh.printLn("N", "      <apiName>     - Name of the API to invoke")
    rh.printLn("N", "      --operands <apiOperands> - Additional API operands")

    return
