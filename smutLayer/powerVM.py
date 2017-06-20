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

import generalUtils
from generalUtils import parseCmdline
import subprocess
from subprocess import CalledProcessError
import time
from vmUtils import execCmdThruIUCV,invokeSMCLI,waitForOSState,waitForVMState

version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
    'HELP': ['help', lambda reqHandle: help(reqHandle)],
    'ISREACHABLE': ['checkIsReachable', 
        lambda reqHandle: checkIsReachable(reqHandle)],
    'OFF': ['deactivate', lambda reqHandle: deactivate(reqHandle)],
    'ON': ['activate', lambda reqHandle: activate(reqHandle)],
    'PAUSE': ['pause', lambda reqHandle: pause(reqHandle)],
    'REBOOT': ['reboot', lambda reqHandle: reboot(reqHandle)],
    'RESET': ['reset', lambda reqHandle: reset(reqHandle)],
    'SOFTOFF': ['softDeactivate', lambda reqHandle: softoff(reqHandle)],
    'STATUS': ['getStatus', lambda reqHandle: getStatus(reqHandle)],
    'UNPAUSE': ['unpause', lambda reqHandle: unpause(reqHandle)],
    'VERSION': ['getVersion', lambda reqHandle: getVersion(reqHandle)],
    'WAIT': ['wait', lambda reqHandle: wait(reqHandle)],
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
# For example, the 'WAIT' subfunction has a 'poll' operand that takes
# one additional operand (time in seconds) which is an int.
# While the 'showparms' operand is just the keyword and has no additional
# value portion.
keyOpsList = {
    'HELP' : {},
    'ISREACHABLE': {
        'showparms': ['showParms', 0, 0],
        },
    'OFF': {
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'wait': ['wait', 0, 0],
        },
    'ON': {
        'state': ['desiredState', 1, 2],
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'wait': ['wait', 0, 0],
        },
    'PAUSE': { 'showparms': ['showParms', 0, 0],
        },
    'REBOOT': {
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'wait': ['wait', 0, 0],
        },
    'RESET': {
        'state': ['desiredState', 1, 2],
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'state': ['desiredState', 1, 2],
        'wait': ['wait', 0, 0],
        },
    'SOFTOFF': {
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'wait': ['wait', 0, 0],
        },
    'STATUS': {
        'showparms': ['showParms', 0, 0],
        },
    'UNPAUSE': {
        'showparms': ['showParms', 0, 0],
        },
    'VERSION': {},
    'WAIT': {
        'maxwait': ['maxWait', 1, 1],
        'poll': ['poll', 1, 1],
        'showparms': ['showParms', 0, 0],
        'state': ['desiredState', 1, 2],
        },
    }


def activate(reqHandle):
    """ Activate a virtual machine.

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
    reqHandle.printSysLog("Enter powerVM.activate, userid: "+reqHandle.userid)

    cmd = ["smcli",
            "Image_Activate",
            "-T", reqHandle.userid]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] == 0:
        pass
    elif results['rc'] == 200 and results['rs'] == 8:
        reqHandle.updateResults({}, reset=1)
    else:
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" +
            results['response'] + "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    if results['overallRC'] == 0 and 'maxQueries' in reqHandle.parms:
        if reqHandle.parms['desiredState'] == 'up':
            results = waitForOSState(
                reqHandle,
                reqHandle.userid,
                reqHandle.parms['desiredState'],
                maxQueries=reqHandle.parms['maxQueries'],
                sleepSecs=reqHandle.parms['poll'])
        else:
            results = waitForVMState(
                reqHandle, 
                reqHandle.userid,
                reqHandle.parms['desiredState'],
                maxQueries=reqHandle.parms['maxQueries'],
                sleepSecs=reqHandle.parms['poll'])
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the desired state: " + reqHandle.parms['desiredState'])

    reqHandle.printSysLog("Exit powerVM.activate, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def checkIsReachable(reqHandle):
    """ Check if a virtual machine is reachable.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'ISREACHABLE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: Always ok
    """

    reqHandle.printSysLog("Enter powerVM.checkIsReachable, userid: " +
        reqHandle.userid)

    strCmd = "echo 'ping'"
    results = execCmdThruIUCV(reqHandle, reqHandle.userid, strCmd)

    if results['overallRC'] == 0:
        reqHandle.printLn("N",  reqHandle.userid + ": reachable")
        reachable = 1
    else:
        reqHandle.printLn("N",  reqHandle.userid + ": unreachable")
        reachable = 0

    reqHandle.updateResults({ "rs": reachable })
    reqHandle.printSysLog("Exit powerVM.checkIsReachable, rc: 0")
    return 0


def deactivate(reqHandle):
    """ Deactivate a virtual machine.

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

    reqHandle.printSysLog("Enter powerVM.deactivate, userid: " +
        reqHandle.userid)

    cmd = ["smcli",
            "Image_Deactivate",
            "-T", reqHandle.userid,
            "-f", "IMMED"]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] == 0:
        pass
    elif results['rc'] == 200 and (results['rs'] == 12 or results['rs'] == 16):
        # Tolerable error.  Machine is already in or going into the state 
        # we want it to enter.
        reqHandle.printLn("N", reqHandle.userid + " is already logged off.")
        reqHandle.updateResults({}, reset=1)
    else:
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" + 
            results['response'] + "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    if results['overallRC'] == 0 and 'maxQueries' in reqHandle.parms:
        results = waitForVMState(
            reqHandle, 
            reqHandle.userid,
            'off',
            maxQueries=reqHandle.parms['maxQueries'],
            sleepSecs=reqHandle.parms['poll'])
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the desired state: off")
        else:
            reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.deactivate, rc: " +
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
    reqHandle.printSysLog("Enter powerVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] is True:
        reqHandle.printLn("N", "Invocation parameters: ")
        reqHandle.printLn("N", "  Routine: powerVM." +
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

    reqHandle.printSysLog("Exit powerVM.doIt, rc: " + str(rc))
    return rc


def getStatus(reqHandle):
    """ Get the power (logon/off) status of a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'STATUS'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog("Enter powerVM.getStatus, userid: " +
        reqHandle.userid)

    cmd = ("/sbin/vmcp q user " + reqHandle.userid + " 2>/dev/null | " +
            "sed 's/HCP\w\w\w045E.*/off/' | sed 's/HCP\w\w\w361E.*/off/' | " +
            "sed 's/" + reqHandle.userid + ".*/on/'")
    try:
        out = subprocess.check_output(
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
        reqHandle.updateResults({ 'overallRC': 3, 'rc': cmdRC })

    if reqHandle.results['overallRC'] == 0:
        reqHandle.printLn("N",  reqHandle.userid + ": " + out)

    reqHandle.printSysLog("Exit powerVM.getStatus, rc: " +
        str(reqHandle.results['overallRC']))
    return reqHandle.results['overallRC']


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
    """ Produce help output specifically for PowerVM functions.

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

    reqHandle.printSysLog("Enter powerVM.parseCmdline")

    if reqHandle.totalParms >= 2:
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn("ES",  "Userid is missing")
        reqHandle.updateResults({ 'overallRC': 4 })
        reqHandle.printSysLog("Exit powerVM.parseCmdLine, rc: " +
            reqHandle.results['overallRC'])
        return reqHandle.results['overallRC']

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

    # Parse the rest of the command line.
    if reqHandle.results['overallRC'] == 0:
        reqHandle.argPos = 3               # Begin Parsing at 4th operand
        generalUtils.parseCmdline(reqHandle, posOpsList, keyOpsList)

    waiting = 0
    if reqHandle.results['overallRC'] == 0:
        if reqHandle.subfunction == 'WAIT':
            waiting = 1
            if reqHandle.parms['desiredState'] not in ['down','off','on','up']:
                reqHandle.printLn("ES", "The desired state was not 'down'," +
                    "'off', 'on' or 'up': " + reqHandle.parms['desiredState'] +
                    ".")
                reqHandle.updateResults({ 'overallRC': 4 })

    if (reqHandle.results['overallRC'] == 0 and 'wait' in reqHandle.parms):
        waiting = 1
        if 'desiredState' not in reqHandle.parms:
            if reqHandle.subfunction in ['ON', 'RESET', 'REBOOT']:
                reqHandle.parms['desiredState'] = 'up'
            else:
                # OFF and SOFTOFF default to 'off'.
                reqHandle.parms['desiredState'] = 'off'

    if reqHandle.results['overallRC'] == 0 and waiting == 1:
        if reqHandle.subfunction == 'ON' or reqHandle.subfunction == 'RESET':
            if ('desiredState' not in reqHandle.parms or
                  reqHandle.parms['desiredState'] not in ['on', 'up']):
                reqHandle.printLn("ES", "The desired state was not 'on' or 'up': " +
                    reqHandle.parms['desiredState'] + ".")
                reqHandle.updateResults({ 'overallRC': 4 })

        if reqHandle.results['overallRC'] == 0:
            if 'maxWait' not in reqHandle.parms:
                reqHandle.parms['maxWait'] = 300
            if 'poll' not in reqHandle.parms:
                reqHandle.parms['poll'] = 15
            reqHandle.parms['maxQueries'] = (reqHandle.parms['maxWait'] +
                reqHandle.parms['poll'] - 1) / reqHandle.parms['poll']

    reqHandle.printSysLog("Exit powerVM.parseCmdLine, rc: " +
        str(reqHandle.results['overallRC']))
    return reqHandle.results['overallRC']


def pause(reqHandle):
    """ Pause a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'PAUSE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter powerVM.pause, userid: " + reqHandle.userid)

    cmd = ["smcli",
            "Image_Pause",
            "-T", reqHandle.userid,
            "-k", "PAUSE=YES"]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0:
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" +
            results['response'] + "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)
        rc = results['overallRC']

    reqHandle.printSysLog("Exit powerVM.pause, rc: " + str(rc))
    return rc


def reboot(reqHandle):
    """ Reboot a virtual machine.

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

    reqHandle.printSysLog("Enter powerVM.reboot, userid: " + reqHandle.userid)

    strCmd = "shutdown -r now"
    results = execCmdThruIUCV(reqHandle, reqHandle.userid, strCmd)
    if results['overallRC'] != 0:
        reqHandle.printLn("ES",  "Command: '" + strCmd + "' failed. ', out: '"+
            results['response'] + "', rc: " + str(results['overallRC']))

    if results['overallRC'] == 0:
        # Wait for the OS to go down
        results = waitForOSState(reqHandle, reqHandle.userid, "down",
            maxQueries=30, sleepSecs=10)
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the interim state: down")

    if results['overallRC'] == 0 and 'maxQueries' in reqHandle.parms:
        results = waitForOSState(reqHandle, 
                                  reqHandle.userid,
                                  'up',
                                  maxQueries=reqHandle.parms['maxQueries'],
                                  sleepSecs=reqHandle.parms['poll'])
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the desired state: up")
        else:
            reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.reboot, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def reset(reqHandle):
    """ Reset a virtual machine.

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

    reqHandle.printSysLog("Enter powerVM.reset, userid: " + reqHandle.userid)

    # Log off the user
    cmd = ["smcli",
            "Image_Deactivate",
            "-T", reqHandle.userid]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0:
        if results['rc'] == 200 and results['rs'] == 12:
            # Tolerated error.  Machine is already in the desired state.
            results['overallRC'] = 0
            results['rc'] = 0
            results['rs'] = 0
        else:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '"
                + reqHandle.results['response'] + "', rc: " +
                str(reqHandle.results['overallRC']))
            reqHandle.updateResults(results)

    # Wait for the logoff to complete
    if results['overallRC'] == 0:
        results = waitForVMState(reqHandle, reqHandle.userid, "off",
            maxQueries=30, sleepSecs=10)

    # Log the user back on
    if results['overallRC'] == 0:
        cmd = ["smcli",
            "Image_Activate",
            "-T", reqHandle.userid]

        results = invokeSMCLI(reqHandle, cmd)
        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '"
                + results['response'] + "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    if results['overallRC'] == 0 and 'maxQueries' in reqHandle.parms:
        if reqHandle.parms['desiredState'] == 'up':
            results = waitForOSState(
                reqHandle, 
                reqHandle.userid,
                reqHandle.parms['desiredState'],
                maxQueries=reqHandle.parms['maxQueries'],
                sleepSecs=reqHandle.parms['poll'])
        else:
            results = waitForVMState(
                reqHandle, 
                reqHandle.userid,
                reqHandle.parms['desiredState'],
                maxQueries=reqHandle.parms['maxQueries'],
                sleepSecs=reqHandle.parms['poll'])
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the desired state: " + reqHandle.parms['desiredState'])
        else:
            reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.reset, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def showInvLines(reqHandle):
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '':
        reqHandle.printLn("N",  "Usage:")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " PowerVM <userid>")
    reqHandle.printLn("N", "                    [isreachable | pause | " +
        "status | unpause]")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " PowerVM <userid>")
    reqHandle.printLn("N", "                    [on | reset] wait state " +
        "[on | up] maxwait <secs>")
    reqHandle.printLn("N", "                    poll <secs>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " PowerVM <userid>")
    reqHandle.printLn("N", "                    [off | reboot | softoff] " +
        "wait maxwait <secs> poll <secs>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + " PowerVM " +
        "<userid> wait")
    reqHandle.printLn("N", "                    state [down | on | off | up] "+
        "maxwait <secs> poll <secs>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + " PowerVM help")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +" PowerVM version")
    return


def showOperandLines(reqHandle):
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP':
        reqHandle.printLn("N", "  For the PowerVM function:")
    else:
        reqHandle.printLn("N",  "Sub-Functions(s):")
    reqHandle.printLn("N", "      help        - Displays this help " +
        "information.")
    reqHandle.printLn("N", "      isreachable - Determine whether the " +
        "virtual OS in a virtual machine")
    reqHandle.printLn("N", "                    is reachable")
    reqHandle.printLn("N", "      on          - Log on the virtual machine")
    reqHandle.printLn("N", "      off         - Log off the virtual machine")
    reqHandle.printLn("N", "      pause       - Pause a virtual machine")
    reqHandle.printLn("N", "      reboot      - Issue a shutdown command to " +
        "reboot the OS in a virtual")
    reqHandle.printLn("N", "                    machine")
    reqHandle.printLn("N", "      reset       - Power a virtual machine off " +
        "and then back on")
    reqHandle.printLn("N", "      softoff     - Issue a shutdown command to " +
        "shutdown the OS in a virtual")
    reqHandle.printLn("N", "                    machine and then log the " +
        "virtual machine off z/VM.")
    reqHandle.printLn("N", "      status      - show the log on/off status " +
        "of the virtual machine")
    reqHandle.printLn("N", "      unpause     - Unpause a virtual machine")
    reqHandle.printLn("N", "      wait        - Wait for the virtual machine " +
        "to go into the specified")
    reqHandle.printLn("N", "                    state of either:")
    reqHandle.printLn("N", "                       down: virtual machine's " +
        "OS is not reachable with IUCV")
    reqHandle.printLn("N", "                       off: virtual machine is " +
        "logged off")
    reqHandle.printLn("N", "                       on: virtual machine is " +
        "logged on")
    reqHandle.printLn("N", "                       up: virtual machine's OS "+
        "is reachable with IUCV")
    reqHandle.printLn("N", "      version     - show the version of the " +
        "power function")
    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Operand(s):")
    reqHandle.printLn("N", "      <userid>    - Userid of the target " +
        "virtual machine")
    reqHandle.printLn("N", "      maxwait <secs> - Maximum time in seconds " +
        "to wait")
    reqHandle.printLn("N", "      poll <secs> - Seconds to wait between " +
        "polling")

    return


def softDeactivate(reqHandle):
    """ Deactivate a virtual machine by first shutting down Linux and
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

    reqHandle.printSysLog("Enter powerVM.softDeactivate, userid: " +
        reqHandle.userid)

    strCmd = "echo 'ping'"
    results = execCmdThruIUCV(reqHandle, reqHandle.userid, strCmd)

    if results['overallRC'] != 0:
        # We could talk to the machine, tell it to shutdown nicely.
        strCmd = "shutdown -h now"
        results = execCmdThruIUCV(reqHandle, reqHandle.userid, strCmd)

    if results['overallRC'] != 0:
        # Tell z/VM to log off the system after we give it a 15 second lead.
        time.sleep(15)
        cmd = ["smcli",
                "Image_Deactivate",
                "-T", reqHandle.userid]

        results = invokeSMCLI(reqHandle, cmd)
        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '"
                + results['response'] + "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    if results['overallRC'] == 0 and 'maxQueries' in reqHandle.parms:
        # Wait for the system to log off.
        results = waitForVMState(
            reqHandle, 
            reqHandle.userid,
            'off',
            maxQueries=reqHandle.parms['maxQueries'],
            sleepSecs=reqHandle.parms['poll'])
        if results['overallRC'] == 0:
            reqHandle.printLn("N", "Userid '" + reqHandle.userid +
                " is in the desired state: off")
        else:
            reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.softDeactivate, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def unpause(reqHandle):
    """ Unpause a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'UNPAUSE'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog("Enter powerVM.unpause, userid: " + reqHandle.userid)

    cmd = ["smcli",
            "Image_Pause",
            "-T", reqHandle.userid,
            "-k", "PAUSE=NO"]

    results = invokeSMCLI(reqHandle, cmd)
    if results['overallRC'] != 0:
        strCmd = ' '.join(cmd)
        reqHandle.printLn("ES",  "Command failed: '" + strCmd + "', out: '" +
            results['response'] + "', rc: " + str(results['overallRC']))
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.unpause, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def wait(reqHandle):
    """ Wait for the virtual machine to go into the specified state.

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

    reqHandle.printSysLog("Enter powerVM.wait, userid: " + reqHandle.userid)

    if (reqHandle.parms['desiredState'] == 'off' or
        reqHandle.parms['desiredState'] == 'on'):
        results = waitForVMState(
            reqHandle,
            reqHandle.userid,
            reqHandle.parms['desiredState'],
            maxQueries=reqHandle.parms['maxQueries'],
            sleepSecs=reqHandle.parms['poll'])
    else:
        results = waitForOSState(
            reqHandle, 
            reqHandle.userid,
            reqHandle.parms['desiredState'],
            maxQueries=reqHandle.parms['maxQueries'],
            sleepSecs=reqHandle.parms['poll'])

    if results['overallRC'] == 0:
        reqHandle.printLn("N",  "Userid '" + reqHandle.userid +
            "' is in the desired state: '" + reqHandle.parms['desiredState'] +
            "'.")
    else:
        reqHandle.updateResults(results)

    reqHandle.printSysLog("Exit powerVM.wait, rc: "+str(results['overallRC']))
    return results['overallRC']
