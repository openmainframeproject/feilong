# Power functions for Systems Management Ultra Thin Layer
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

import time

import generalUtils
import msgs
from vmUtils import execCmdThruIUCV, invokeSMCLI
from vmUtils import isLoggedOn
from vmUtils import waitForOSState, waitForVMState

modId = 'PVM'
vmOSUpStates = ['on', 'up']
vmOSUpDownStates = ['down', 'off', 'on', 'up']
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'HELP': ['help', lambda rh: help(rh)],
    'ISREACHABLE': ['checkIsReachable',
        lambda rh: checkIsReachable(rh)],
    'OFF': ['deactivate', lambda rh: deactivate(rh)],
    'ON': ['activate', lambda rh: activate(rh)],
    'PAUSE': ['pause', lambda rh: pause(rh)],
    'REBOOT': ['reboot', lambda rh: reboot(rh)],
    'RESET': ['reset', lambda rh: reset(rh)],
    'SOFTOFF': ['softDeactivate', lambda rh: softDeactivate(rh)],
    'STATUS': ['getStatus', lambda rh: getStatus(rh)],
    'UNPAUSE': ['unpause', lambda rh: unpause(rh)],
    'VERSION': ['getVersion', lambda rh: getVersion(rh)],
    'WAIT': ['wait', lambda rh: wait(rh)],
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
For example, the 'WAIT' subfunction has a 'poll' operand that takes
one additional operand (time in seconds) which is an int.
While the 'showparms' operand is just the keyword and has no additional
value portion.
"""
keyOpsList = {
    'HELP': {},
    'ISREACHABLE': {
        '--showparms': ['showParms', 0, 0]},
    'OFF': {
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--wait': ['wait', 0, 0]},
    'ON': {
        '--state': ['desiredState', 1, 2],
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--wait': ['wait', 0, 0]},
    'PAUSE': {'--showparms': ['showParms', 0, 0]},
    'REBOOT': {
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--wait': ['wait', 0, 0]},
    'RESET': {
        '--state': ['desiredState', 1, 2],
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--wait': ['wait', 0, 0]},
    'SOFTOFF': {
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--wait': ['wait', 0, 0]},
    'STATUS': {
        '--showparms': ['showParms', 0, 0]
        },
    'UNPAUSE': {
        '--showparms': ['showParms', 0, 0]},
    'VERSION': {},
    'WAIT': {
        '--maxwait': ['maxWait', 1, 1],
        '--poll': ['poll', 1, 1],
        '--showparms': ['showParms', 0, 0],
        '--state': ['desiredState', 1, 2]},
    }


def activate(rh):
    """
    Activate a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'ON'
          userid      - userid of the virtual machine
          parms['desiredState']   - Desired state. Optional,
                                    unless 'maxQueries' is specified.
          parms['maxQueries']     - Maximum number of queries to issue.
                                    Optional.
          parms['maxWait']        - Maximum time to wait in seconds. Optional,
                                    unless 'maxQueries' is specified.
          parms['poll']           - Polling interval in seconds. Optional,
                                    unless 'maxQueries' is specified.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    rh.printSysLog("Enter powerVM.activate, userid: " + rh.userid)

    parms = ["-T", rh.userid]
    smcliResults = invokeSMCLI(rh, "Image_Activate", parms)
    if smcliResults['overallRC'] == 0:
        pass
    elif (smcliResults['overallRC'] == 8 and
        smcliResults['rc'] == 200 and smcliResults['rs'] == 8):
        pass    # All good.  No need to change the ReqHandle results.
    else:
        # SMAPI API failed.
        rh.printLn("ES", smcliResults['response'])
        rh.updateResults(smcliResults)    # Use results from invokeSMCLI

    if rh.results['overallRC'] == 0 and 'maxQueries' in rh.parms:
        # Wait for the system to be in the desired state of:
        # OS is 'up' and reachable or VM is 'on'.
        if rh.parms['desiredState'] == 'up':
            results = waitForOSState(
                rh,
                rh.userid,
                rh.parms['desiredState'],
                maxQueries=rh.parms['maxQueries'],
                sleepSecs=rh.parms['poll'])
        else:
            results = waitForVMState(
                rh,
                rh.userid,
                rh.parms['desiredState'],
                maxQueries=rh.parms['maxQueries'],
                sleepSecs=rh.parms['poll'])

        if results['overallRC'] == 0:
            rh.printLn("N", "%s: %s" %
                (rh.userid, rh.parms['desiredState']))
        else:
            rh.updateResults(results)

    rh.printSysLog("Exit powerVM.activate, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def checkIsReachable(rh):
    """
    Check if a virtual machine is reachable.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'ISREACHABLE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       overallRC - 0: determined the status, non-zero: some weird failure
                                             while trying to execute a command
                                             on the guest via IUCV
       rc - RC returned from execCmdThruIUCV
       rs - 0: not reachable, 1: reachable
    """

    rh.printSysLog("Enter powerVM.checkIsReachable, userid: " +
        rh.userid)

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
    rh.printSysLog("Exit powerVM.checkIsReachable, rc: 0")
    return 0


def deactivate(rh):
    """
    Deactivate a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'OFF'
          userid      - userid of the virtual machine
          parms['maxQueries']     - Maximum number of queries to issue.
                                    Optional.
          parms['maxWait']        - Maximum time to wait in seconds. Optional,
                                    unless 'maxQueries' is specified.
          parms['poll']           - Polling interval in seconds. Optional,
                                    unless 'maxQueries' is specified.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.deactivate, userid: " +
        rh.userid)

    parms = ["-T", rh.userid, "-f", "IMMED"]
    results = invokeSMCLI(rh, "Image_Deactivate", parms)
    if results['overallRC'] == 0:
        pass
    elif (results['overallRC'] == 8 and results['rc'] == 200 and
        (results['rs'] == 12 or results['rs'] == 16)):
        # Tolerable error.  Machine is already in or going into the state
        # we want it to enter.
        rh.printLn("N", rh.userid + ": off")
        rh.updateResults({}, reset=1)
    else:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    if results['overallRC'] == 0 and 'maxQueries' in rh.parms:
        results = waitForVMState(
            rh,
            rh.userid,
            'off',
            maxQueries=rh.parms['maxQueries'],
            sleepSecs=rh.parms['poll'])
        if results['overallRC'] == 0:
            rh.printLn("N", rh.userid + ": off")
        else:
            rh.updateResults(results)

    rh.printSysLog("Exit powerVM.deactivate, rc: " +
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

    rh.printSysLog("Enter powerVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: powerVM." +
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

    rh.printSysLog("Exit powerVM.doIt, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getStatus(rh):
    """
    Get the power (logon/off) status of a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'STATUS'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       results['overallRC'] - 0: ok, non-zero: error
       if ok:
          results['rc'] - 0: for both on and off cases
          results['rs'] - 0: powered on
          results['rs'] - 1: powered off
    """

    rh.printSysLog("Enter powerVM.getStatus, userid: " +
        rh.userid)

    results = isLoggedOn(rh, rh.userid)
    if results['overallRC'] != 0:
        # Unexpected error
        pass
    elif results['rs'] == 0:
        rh.printLn("N", rh.userid + ": on")
    else:
        rh.printLn("N", rh.userid + ": off")

    rh.updateResults(results)

    rh.printSysLog("Exit powerVM.getStatus, rc: " +
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
    Produce help output specifically for PowerVM functions.

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

    rh.printSysLog("Enter powerVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit powerVM.parseCmdLine, rc: " +
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

    waiting = 0
    if rh.results['overallRC'] == 0:
        if rh.subfunction == 'WAIT':
            waiting = 1
            if rh.parms['desiredState'] not in vmOSUpDownStates:
                # Desired state is not: down, off, on or up.
                msg = msgs.msg['0013'][1] % (modId,
                    rh.parms['desiredState'], ", ".join(vmOSUpDownStates))
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0013'][0])

    if (rh.results['overallRC'] == 0 and 'wait' in rh.parms):
        waiting = 1
        if 'desiredState' not in rh.parms:
            if rh.subfunction in ['ON', 'RESET', 'REBOOT']:
                rh.parms['desiredState'] = 'up'
            else:
                # OFF and SOFTOFF default to 'off'.
                rh.parms['desiredState'] = 'off'

    if rh.results['overallRC'] == 0 and waiting == 1:
        if rh.subfunction == 'ON' or rh.subfunction == 'RESET':
            if ('desiredState' not in rh.parms or
                  rh.parms['desiredState'] not in vmOSUpStates):
                # Desired state is not: on or up.
                msg = msgs.msg['0013'][1] % (modId,
                    rh.parms['desiredState'], ", ".join(vmOSUpStates))
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0013'][0])

        if rh.results['overallRC'] == 0:
            if 'maxWait' not in rh.parms:
                rh.parms['maxWait'] = 300
            if 'poll' not in rh.parms:
                rh.parms['poll'] = 15
            rh.parms['maxQueries'] = (rh.parms['maxWait'] +
                rh.parms['poll'] - 1) / rh.parms['poll']
            # If we had to do some rounding, give a warning
            # out to the command line user that the wait
            # won't be what they expected.
            if rh.parms['maxWait'] % rh.parms['poll'] != 0:
                msg = msgs.msg['0017'][1] % (modId,
                    rh.parms['maxWait'], rh.parms['poll'],
                    rh.parms['maxQueries'] * rh.parms['poll'],
                    rh.parms['maxQueries'])
                rh.printLn("W", msg)

    rh.printSysLog("Exit powerVM.parseCmdLine, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def pause(rh):
    """
    Pause a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'PAUSE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.pause, userid: " + rh.userid)

    parms = ["-T", rh.userid, "-k", "PAUSE=YES"]
    results = invokeSMCLI(rh, "Image_Pause", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit powerVM.pause, rc: " + str(rh.results['overallRC']))
    return rh.results['overallRC']


def reboot(rh):
    """
    Reboot a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'REBOOT'
          userid      - userid of the virtual machine
          parms['desiredState']   - Desired state. Optional, unless
                                    'maxQueries' is specified.
          parms['maxQueries']     - Maximum number of queries to issue.
                                    Optional.
          parms['maxWait']        - Maximum time to wait in seconds. Optional,
                                    unless 'maxQueries' is specified.
          parms['poll']           - Polling interval in seconds. Optional,
                                    unless 'maxQueries' is specified.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.reboot, userid: " + rh.userid)

    strCmd = "shutdown -r now"
    results = execCmdThruIUCV(rh, rh.userid, strCmd)
    if results['overallRC'] != 0:
        # Command failed to execute using IUCV.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)

    if rh.results['overallRC'] == 0:
        # Wait for the OS to go down
        results = waitForOSState(rh, rh.userid, "down",
            maxQueries=30, sleepSecs=10)
        if results['overallRC'] == 0:
            rh.printLn("N", rh.userid + ": down (interim state)")

    if rh.results['overallRC'] == 0 and 'maxQueries' in rh.parms:
        results = waitForOSState(rh,
                                  rh.userid,
                                  'up',
                                  maxQueries=rh.parms['maxQueries'],
                                  sleepSecs=rh.parms['poll'])
        if results['overallRC'] == 0:
            rh.printLn("N", rh.userid + ": up")
        else:
            rh.updateResults(results)

    rh.printSysLog("Exit powerVM.reboot, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def reset(rh):
    """
    Reset a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'RESET'
          userid      - userid of the virtual machine
          parms['maxQueries']     - Maximum number of queries to issue.
                                    Optional.
          parms['maxWait']        - Maximum time to wait in seconds. Optional,
                                    unless 'maxQueries' is specified.
          parms['poll']           - Polling interval in seconds. Optional,
                                    unless 'maxQueries' is specified.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.reset, userid: " + rh.userid)

    # Log off the user
    parms = ["-T", rh.userid]
    results = invokeSMCLI(rh, "Image_Deactivate", parms)
    if results['overallRC'] != 0:
        if results['rc'] == 200 and results['rs'] == 12:
            # Tolerated error.  Machine is already in the desired state.
            results['overallRC'] = 0
            results['rc'] = 0
            results['rs'] = 0
        else:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)    # Use results from invokeSMCLI

    # Wait for the logoff to complete
    if results['overallRC'] == 0:
        results = waitForVMState(rh, rh.userid, "off",
            maxQueries=30, sleepSecs=10)

    # Log the user back on
    if results['overallRC'] == 0:
        parms = ["-T", rh.userid]
        results = invokeSMCLI(rh, "Image_Activate", parms)
        if results['overallRC'] != 0:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)    # Use results from invokeSMCLI

    if results['overallRC'] == 0 and 'maxQueries' in rh.parms:
        if rh.parms['desiredState'] == 'up':
            results = waitForOSState(
                rh,
                rh.userid,
                rh.parms['desiredState'],
                maxQueries=rh.parms['maxQueries'],
                sleepSecs=rh.parms['poll'])
        else:
            results = waitForVMState(
                rh,
                rh.userid,
                rh.parms['desiredState'],
                maxQueries=rh.parms['maxQueries'],
                sleepSecs=rh.parms['poll'])
        if results['overallRC'] == 0:
            rh.printLn("N", rh.userid + ": " +
                       rh.parms['desiredState'])
        else:
            rh.updateResults(results)

    rh.printSysLog("Exit powerVM.reset, rc: " +
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
        " PowerVM <userid>")
    rh.printLn("N", "                    [isreachable | pause | " +
        "status | unpause]")
    rh.printLn("N", "  python " + rh.cmdName +
        " PowerVM <userid>")
    rh.printLn("N", "                    [on | reset] --wait --state " +
        "[on | up] --maxwait <secs>")
    rh.printLn("N", "                    --poll <secs>")
    rh.printLn("N", "  python " + rh.cmdName +
        " PowerVM <userid>")
    rh.printLn("N", "                    [off | reboot | softoff] " +
        "--maxwait <secs> --poll <secs>")
    rh.printLn("N", "  python " + rh.cmdName + " PowerVM " +
        "<userid> wait")
    rh.printLn("N", "                    --state [down | on | off | up] " +
        "--maxwait <secs>")
    rh.printLn("N", "                    --poll <secs>")
    rh.printLn("N", "  python " + rh.cmdName + " PowerVM help")
    rh.printLn("N", "  python " + rh.cmdName + " PowerVM version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the PowerVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      help        - Displays this help " +
        "information.")
    rh.printLn("N", "      isreachable - Determine whether the " +
        "virtual OS in a virtual machine")
    rh.printLn("N", "                    is reachable")
    rh.printLn("N", "      on          - Log on the virtual machine")
    rh.printLn("N", "      off         - Log off the virtual machine")
    rh.printLn("N", "      pause       - Pause a virtual machine")
    rh.printLn("N", "      reboot      - Issue a shutdown command to " +
        "reboot the OS in a virtual")
    rh.printLn("N", "                    machine")
    rh.printLn("N", "      reset       - Power a virtual machine off " +
        "and then back on")
    rh.printLn("N", "      softoff     - Issue a shutdown command to " +
        "shutdown the OS in a virtual")
    rh.printLn("N", "                    machine and then log the " +
        "virtual machine off z/VM.")
    rh.printLn("N", "      status      - show the log on/off status " +
        "of the virtual machine")
    rh.printLn("N", "      unpause     - Unpause a virtual machine")
    rh.printLn("N", "      wait        - Wait for the virtual machine " +
        "to go into the specified")
    rh.printLn("N", "                    state of either:")
    rh.printLn("N", "                       down: virtual machine's " +
        "OS is not reachable with IUCV")
    rh.printLn("N", "                       off: virtual machine is " +
        "logged off")
    rh.printLn("N", "                       on: virtual machine is " +
        "logged on")
    rh.printLn("N", "                       up: virtual machine's OS " +
        "is reachable with IUCV")
    rh.printLn("N", "      version     - show the version of the " +
        "power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      <userid>    - Userid of the target " +
        "virtual machine")
    rh.printLn("N", "      --maxwait <secs> - " +
        "Maximum time in seconds to wait")
    rh.printLn("N", "      --poll <secs> - " +
        "Seconds to wait between polling")
    rh.printLn("N", "      --state [down | off | on | up] - " +
        "Desired state for virtual machine")
    rh.printLn("N", "                    (on or off) or for the operating " +
        "system (down or up).")
    rh.printLn("N", "      --wait      - wait for the machine to go into " +
        "the desired state.")

    return


def softDeactivate(rh):
    """
    Deactivate a virtual machine by first shutting down Linux and
    then log it off.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'SOFTOFF'
          userid      - userid of the virtual machine
          parms['maxQueries']     - Maximum number of queries to issue.
                                    Optional.
          parms['maxWait']        - Maximum time to wait in seconds.
                                    Optional,
                                    unless 'maxQueries' is specified.
          parms['poll']           - Polling interval in seconds. Optional,
                                    unless 'maxQueries' is specified.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.softDeactivate, userid: " +
        rh.userid)

    strCmd = "echo 'ping'"
    iucvResults = execCmdThruIUCV(rh, rh.userid, strCmd)

    if iucvResults['overallRC'] == 0:
        # We could talk to the machine, tell it to shutdown nicely.
        strCmd = "shutdown -h now"
        iucvResults = execCmdThruIUCV(rh, rh.userid, strCmd)
        if iucvResults['overallRC'] == 0:
            time.sleep(15)
        else:
            # Shutdown failed.  Let CP take down the system
            # after we log the results.
            rh.printSysLog("powerVM.softDeactivate " + rh.userid +
                " is unreachable. Treating it as already shutdown.")
    else:
        # Could not ping the machine.  Treat it as a success
        # after we log the results.
        rh.printSysLog("powerVM.softDeactivate " + rh.userid +
            " is unreachable. Treating it as already shutdown.")

    # Tell z/VM to log off the system.
    parms = ["-T", rh.userid]
    smcliResults = invokeSMCLI(rh, "Image_Deactivate", parms)
    if smcliResults['overallRC'] == 0:
        pass
    elif (smcliResults['overallRC'] == 8 and smcliResults['rc'] == 200 and
        (smcliResults['rs'] == 12 or + smcliResults['rs'] == 16)):
        # Tolerable error.
        # Machine is already logged off or is logging off.
        rh.printLn("N", rh.userid + " is already logged off.")
    else:
        # SMAPI API failed.
        rh.printLn("ES", smcliResults['response'])
        rh.updateResults(smcliResults)    # Use results from invokeSMCLI

    if rh.results['overallRC'] == 0 and 'maxQueries' in rh.parms:
        # Wait for the system to log off.
        waitResults = waitForVMState(
            rh,
            rh.userid,
            'off',
            maxQueries=rh.parms['maxQueries'],
            sleepSecs=rh.parms['poll'])
        if waitResults['overallRC'] == 0:
            rh.printLn("N", "Userid '" + rh.userid +
                " is in the desired state: off")
        else:
            rh.updateResults(waitResults)

    rh.printSysLog("Exit powerVM.softDeactivate, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def unpause(rh):
    """
    Unpause a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'UNPAUSE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.unpause, userid: " + rh.userid)

    parms = ["-T", rh.userid, "-k", "PAUSE=NO"]

    results = invokeSMCLI(rh, "Image_Pause", parms)
    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit powerVM.unpause, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def wait(rh):
    """
    Wait for the virtual machine to go into the specified state.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'WAIT'
          userid      - userid of the virtual machine
          parms['desiredState']   - Desired state
          parms['maxQueries']     - Maximum number of queries to issue
          parms['maxWait']        - Maximum time to wait in seconds
          parms['poll']           - Polling interval in seconds

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter powerVM.wait, userid: " + rh.userid)

    if (rh.parms['desiredState'] == 'off' or
        rh.parms['desiredState'] == 'on'):
        results = waitForVMState(
            rh,
            rh.userid,
            rh.parms['desiredState'],
            maxQueries=rh.parms['maxQueries'],
            sleepSecs=rh.parms['poll'])
    else:
        results = waitForOSState(
            rh,
            rh.userid,
            rh.parms['desiredState'],
            maxQueries=rh.parms['maxQueries'],
            sleepSecs=rh.parms['poll'])

    if results['overallRC'] == 0:
        rh.printLn("N", rh.userid + ": " + rh.parms['desiredState'])
    else:
        rh.updateResults(results)

    rh.printSysLog("Exit powerVM.wait, rc: " + str(rh.results['overallRC']))
    return rh.results['overallRC']
