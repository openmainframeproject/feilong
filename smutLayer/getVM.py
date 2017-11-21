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
import subprocess

import generalUtils
import msgs
from vmUtils import execCmdThruIUCV, getPerfInfo, invokeSMCLI
from vmUtils import isLoggedOn

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
       overallRC - 0: determined the status, non-zero: some weird failure
                                             while trying to execute a command
                                             on the guest via IUCV
       rc - RC returned from execCmdThruIUCV
       rs - 0: not reachable, 1: reachable
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

    # Transfer the console to this virtual machine.
    parms = ["-T", rh.userid]
    results = invokeSMCLI(rh, "Image_Console_Get", parms)

    if results['overallRC'] != 0:
        if (results['overallRC'] == 8 and results['rc'] == 8 and
            results['rs'] == 8):
            # Give a more specific message.  Userid is either
            # not logged on or not spooling their console.
            msg = msgs.msg['0409'][1] % (modId, rh.userid)
        else:
            msg = results['response']
        rh.updateResults(results)    # Use results from invokeSMCLI
        rh.printLn("ES", msg)
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    # Check whether the reader is online
    with open('/sys/bus/ccw/drivers/vmur/0.0.000c/online', 'r') as myfile:
        out = myfile.read().replace('\n', '')
        myfile.close()

    # Nope, offline, error out and exit
    if int(out) != 1:
        msg = msgs.msg['0411'][1]
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0411'][0])
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    # We should set class to *, otherwise we will get errors like:
    # vmur: Reader device class does not match spool file class
    cmd = ["sudo", "/sbin/vmcp", "spool reader class *"]
    strCmd = ' '.join(cmd)
    rh.printSysLog("Invoking: " + strCmd)
    try:
        subprocess.check_output(
            cmd,
            close_fds=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # If we couldn't change the class, that's not fatal
        # But we want to warn about possibly incomplete
        # results
        msg = msgs.msg['0407'][1] % (modId, strCmd, e.output)
        rh.printLn("WS", msg)
    except Exception as e:
        # All other exceptions.
        # If we couldn't change the class, that's not fatal
        # But we want to warn about possibly incomplete
        # results
        rh.printLn("ES", msgs.msg['0422'][1] % (modId, strCmd,
            type(e).__name__, str(e)))
        rh.printLn("ES", msgs.msg['0423'][1] % modId, strCmd,
            type(e).__name__, str(e))

    # List the spool files in the reader
    cmd = ["/usr/sbin/vmur", "list"]
    strCmd = ' '.join(cmd)
    rh.printSysLog("Invoking: " + strCmd)
    try:
        files = subprocess.check_output(
            cmd,
            close_fds=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # Uh oh, vmur list command failed for some reason
        msg = msgs.msg['0408'][1] % (modId, rh.userid,
                                     strCmd, e.output)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0408'][0])
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']
    except Exception as e:
        # All other exceptions.
        rh.printLn("ES", msgs.msg['0421'][1] % (modId, strCmd,
            type(e).__name__, str(e)))
        rh.updateResults(msgs.msg['0421'][0])
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    # Now for each line that contains our user and is a
    # class T console file, add the spool id to our list
    spoolFiles = files.split('\n')
    outstr = ""
    for myfile in spoolFiles:
        if (myfile != "" and
                myfile.split()[0] == rh.userid and
                myfile.split()[2] == "T" and
                myfile.split()[3] == "CON"):

            fileId = myfile.split()[1]
            outstr += fileId + " "

    # No files in our list
    if outstr == "":
        msg = msgs.msg['0410'][1] % (modId, rh.userid)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0410'][0])
        rh.printSysLog("Exit getVM.parseCmdLine, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    # Output the list
    rh.printLn("N", "List of spool files containing "
               "console logs from %s: %s" % (rh.userid, outstr))

    rh.results['overallRC'] = 0
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

    parms = ["-T", rh.userid]
    results = invokeSMCLI(rh, "Image_Query_DM", parms)
    if results['overallRC'] == 0:
        results['response'] = re.sub('\*DVHOPT.*', '', results['response'])
        rh.printLn("N", results['response'])
    else:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
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

    rh.printSysLog("Enter getVM.getStatus, userid: " + rh.userid)

    results = isLoggedOn(rh, rh.userid)
    if results['rc'] != 0:
        # Uhoh, can't determine if guest is logged on or not
        rh.updateResults(results)
        rh.printSysLog("Exit getVM.getStatus, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    if results['rs'] == 1:
        # Guest is logged off, everything is 0
        powerStr = "Power state: off"
        memStr = "Total Memory: 0M"
        usedMemStr = "Used Memory: 0M"
        procStr = "Processors: 0"
        timeStr = "CPU Used Time: 0 sec"

    else:
        powerStr = "Power state: on"

    if 'power' in rh.parms:
        # Test here to see if we only need power state
        # Then we can return early
        rh.printLn("N", powerStr)
        rh.updateResults(results)
        rh.printSysLog("Exit getVM.getStatus, rc: " +
                       str(rh.results['overallRC']))
        return rh.results['overallRC']

    if results['rs'] != 1:
        # Guest is logged on, go get more info
        results = getPerfInfo(rh, rh.userid)

        if results['overallRC'] != 0:
            # Something went wrong in subroutine, exit
            rh.updateResults(results)
            rh.printSysLog("Exit getVM.getStatus, rc: " +
                           str(rh.results['overallRC']))
            return rh.results['overallRC']
        else:
            # Everything went well, response should be good
            memStr = results['response'].split("\n")[0]
            usedMemStr = results['response'].split("\n")[1]
            procStr = results['response'].split("\n")[2]
            timeStr = results['response'].split("\n")[3]

    # Build our output string according
    # to what information was asked for
    if 'memory' in rh.parms:
        outStr = memStr + "\n" + usedMemStr
    elif 'cpu' in rh.parms:
        outStr = procStr + "\n" + timeStr
    else:
        # Default to all
        outStr = powerStr + "\n" + memStr + "\n" + usedMemStr
        outStr += "\n" + procStr + "\n" + timeStr
    rh.printLn("N", outStr)
    rh.printSysLog("Exit getVM.getStatus, rc: " +
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
        " GetVM <userid> [ consoleoutput | directory | isreachable ]")
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
