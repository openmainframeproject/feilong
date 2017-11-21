# GetHost functions for Systems Management Ultra Thin Layer
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

import os
import types
import subprocess

import generalUtils
import msgs
from vmUtils import invokeSMCLI

modId = 'GHO'
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'DISKPOOLNAMES': ['help', lambda rh: getDiskPoolNames(rh)],
    'DISKPOOLSPACE': ['help', lambda rh: getDiskPoolSpace(rh)],
    'FCPDEVICES': ['help', lambda rh: getFcpDevices(rh)],
    'GENERAL': ['help', lambda rh: getGeneralInfo(rh)],
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
posOpsList = {
    'DISKPOOLSPACE': [
                          ['Disk Pool Name', 'poolName', False, 2]
                     ]
    }

"""
List of additional operands/options supported by the various subfunctions.
The dictionary followng the subfunction name uses the keyword from the
command as a key.  Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
"""
keyOpsList = {
    'DISKPOOLNAMES': {'--showparms': ['showParms', 0, 0]},
    'DISKPOOLSPACE': {'--showparms': ['showParms', 0, 0]},
    'FCPDEVICES': {'--showparms': ['showParms', 0, 0]},
    'GENERAL': {'--showparms': ['showParms', 0, 0]},
    'HELP': {'--showparms': ['showParms', 0, 0]},
    'VERSION': {'--showparms': ['showParms', 0, 0]},
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

    rh.printSysLog("Enter getHost.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: getHost." +
            str(subfuncHandler[rh.subfunction][0]) + "(rh)")
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

    rh.printSysLog("Exit getHost.doIt, rc: " + str(rh.results['overallRC']))
    return rh.results['overallRC']


def getDiskPoolNames(rh):
    """
    Obtain the list of disk pools known to the directory manager.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'DISKPOOLNAMES'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getHost.getDiskPoolNames")

    parms = ["-q", "1", "-e", "3", "-T", "dummy"]
    results = invokeSMCLI(rh, "Image_Volume_Space_Query_DM", parms)
    if results['overallRC'] == 0:
        for line in results['response'].splitlines():
            poolName = line.partition(' ')[0]
            rh.printLn("N", poolName)
    else:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit getHost.getDiskPoolNames, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getDiskPoolSpace(rh):
    """
    Obtain disk pool space information for all or a specific disk pool.

    Input:
       Request Handle with the following properties:
          function            - 'GETHOST'
          subfunction         - 'DISKPOOLSPACE'
          parms['poolName']   - Name of the disk pool. Optional,
                                if not present then information for all
                                disk pools is obtained.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getHost.getDiskPoolSpace")

    results = {'overallRC': 0}

    if 'poolName' not in rh.parms:
        poolNames = ["*"]
    else:
        if isinstance(rh.parms['poolName'], types.ListType):
            poolNames = rh.parms['poolName']
        else:
            poolNames = [rh.parms['poolName']]

    if results['overallRC'] == 0:
        # Loop thru each pool getting total.  Do it for query 2 & 3
        totals = {}
        for qType in ["2", "3"]:
            parms = [
                "-q", qType,
                "-e", "3",
                "-T", "DUMMY",
                "-n", " ".join(poolNames)]

            results = invokeSMCLI(rh, "Image_Volume_Space_Query_DM", parms)
            if results['overallRC'] == 0:
                for line in results['response'].splitlines():
                    parts = line.split()
                    if len(parts) == 9:
                        poolName = parts[7]
                    else:
                        poolName = parts[4]
                    if poolName not in totals:
                        totals[poolName] = {"2": 0., "3": 0.}

                    if parts[1][:4] == "3390":
                        totals[poolName][qType] += int(parts[3]) * 737280
                    elif parts[1][:4] == "9336":
                        totals[poolName][qType] += int(parts[3]) * 512
            else:
                # SMAPI API failed.
                rh.printLn("ES", results['response'])
                rh.updateResults(results)    # Use results from invokeSMCLI
                break

        if results['overallRC'] == 0:
            if len(totals) == 0:
                # No pool information found.
                msg = msgs.msg['0402'][1] % (modId, " ".join(poolNames))
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0402'][0])
            else:
                # Produce a summary for each pool
                for poolName in sorted(totals):
                    total = totals[poolName]["2"] + totals[poolName]["3"]
                    rh.printLn("N", poolName + " Total: " +
                        generalUtils.cvtToMag(rh, total))
                    rh.printLn("N", poolName + " Used: " +
                        generalUtils.cvtToMag(rh, totals[poolName]["3"]))
                    rh.printLn("N", poolName + " Free: " +
                        generalUtils.cvtToMag(rh, totals[poolName]["2"]))

    rh.printSysLog("Exit getHost.getDiskPoolSpace, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getFcpDevices(rh):
    """
    Lists the FCP device channels that are active, free, or offline.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'FCPDEVICES'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter getHost.getFcpDevices")

    parms = ["-T", "dummy"]
    results = invokeSMCLI(rh, "System_WWPN_Query", parms)
    if results['overallRC'] == 0:
        rh.printLn("N", results['response'])
    else:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit getHost.getFcpDevices, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def getGeneralInfo(rh):
    """
    Obtain general information about the host.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'GENERAL'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok
       Return code - 4: problem getting some info
    """

    rh.printSysLog("Enter getHost.getGeneralInfo")

    # Get host using VMCP
    rh.results['overallRC'] = 0
    cmd = ["sudo", "/sbin/vmcp", "query userid"]
    strCmd = ' '.join(cmd)
    rh.printSysLog("Invoking: " + strCmd)
    try:
        host = subprocess.check_output(
            cmd,
            close_fds=True,
            stderr=subprocess.STDOUT).split()[2]
    except subprocess.CalledProcessError as e:
        msg = msgs.msg['0405'][1] % (modId, "Hypervisor Name",
                                     strCmd, e.output)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
        host = "no info"
    except Exception as e:
        # All other exceptions.
        rh.printLn("ES", msgs.msg['0421'][1] % (modId, strCmd,
            type(e).__name__, str(e)))
        rh.updateResults(msgs.msg['0421'][0])
        host = "no info"

    # Get a bunch of info from /proc/sysinfo
    lparCpuTotal = "no info"
    lparCpuUsed = "no info"
    cecModel = "no info"
    cecVendor = "no info"
    hvInfo = "no info"
    with open('/proc/sysinfo', 'r') as myFile:
        for num, line in enumerate(myFile, 1):
            # Get total physical CPU in this LPAR
            if "LPAR CPUs Total" in line:
                lparCpuTotal = line.split()[3]
            # Get used physical CPU in this LPAR
            if "LPAR CPUs Configured" in line:
                lparCpuUsed = line.split()[3]
            # Get CEC model
            if "Type:" in line:
                cecModel = line.split()[1]
            # Get vendor of CEC
            if "Manufacturer:" in line:
                cecVendor = line.split()[1]
            # Get hypervisor type and version
            if "VM00 Control Program" in line:
                hvInfo = line.split()[3] + " " + line.split()[4]
    if lparCpuTotal == "no info":
        msg = msgs.msg['0405'][1] % (modId, "LPAR CPUs Total",
                                     "cat /proc/sysinfo", "not found")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
    if lparCpuUsed == "no info":
        msg = msgs.msg['0405'][1] % (modId, "LPAR CPUs Configured",
                                     "cat /proc/sysinfo", "not found")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
    if cecModel == "no info":
        msg = msgs.msg['0405'][1] % (modId, "Type:",
                                     "cat /proc/sysinfo", "not found")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
    if cecVendor == "no info":
        msg = msgs.msg['0405'][1] % (modId, "Manufacturer:",
                                     "cat /proc/sysinfo", "not found")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
    if hvInfo == "no info":
        msg = msgs.msg['0405'][1] % (modId, "VM00 Control Program",
                                     "cat /proc/sysinfo", "not found")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])

    # Get processor architecture
    arch = str(os.uname()[4])

    # Get LPAR memory total & offline
    parm = ["-T", "dummy", "-k", "STORAGE="]

    lparMemTotal = "no info"
    lparMemStandby = "no info"
    results = invokeSMCLI(rh, "System_Information_Query", parm)
    if results['overallRC'] == 0:
        for line in results['response'].splitlines():
            if "STORAGE=" in line:
                lparMemOnline = line.split()[0]
                lparMemStandby = line.split()[4]
                lparMemTotal = lparMemOnline.split("=")[2]
                lparMemStandby = lparMemStandby.split("=")[1]
    else:
        # SMAPI API failed, so we put out messages
        # 300 and 405 for consistency
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        msg = msgs.msg['0405'][1] % (modId, "LPAR memory",
            "(see message 300)", results['response'])
        rh.printLn("ES", msg)

    # Get LPAR memory in use
    parm = ["-T", "dummy", "-k", "detailed_cpu=show=no"]

    lparMemUsed = "no info"
    results = invokeSMCLI(rh, "System_Performance_Information_Query",
                          parm)
    if results['overallRC'] == 0:
        for line in results['response'].splitlines():
            if "MEMORY_IN_USE=" in line:
                lparMemUsed = line.split("=")[1]
                lparMemUsed = generalUtils.getSizeFromPage(rh, lparMemUsed)
    else:
        # SMAPI API failed, so we put out messages
        # 300 and 405 for consistency
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI
        msg = msgs.msg['0405'][1] % (modId, "LPAR memory in use",
            "(see message 300)", results['response'])
        rh.printLn("ES", msg)

    # Get IPL Time
    ipl = ""
    cmd = ["sudo", "/sbin/vmcp", "query cplevel"]
    strCmd = ' '.join(cmd)
    rh.printSysLog("Invoking: " + strCmd)
    try:
        ipl = subprocess.check_output(
            cmd,
            close_fds=True,
            stderr=subprocess.STDOUT).split("\n")[2]
    except subprocess.CalledProcessError as e:
        msg = msgs.msg['0405'][1] % (modId, "IPL Time",
                                     strCmd, e.output)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0405'][0])
    except Exception as e:
        # All other exceptions.
        rh.printLn("ES", msgs.msg['0421'][1] % (modId, strCmd,
            type(e).__name__, str(e)))
        rh.updateResults(msgs.msg['0421'][0])

    # Create output string
    outstr = "z/VM Host: " + host
    outstr += "\nArchitecture: " + arch
    outstr += "\nCEC Vendor: " + cecVendor
    outstr += "\nCEC Model: " + cecModel
    outstr += "\nHypervisor OS: " + hvInfo
    outstr += "\nHypervisor Name: " + host
    outstr += "\nLPAR CPU Total: " + lparCpuTotal
    outstr += "\nLPAR CPU Used: " + lparCpuUsed
    outstr += "\nLPAR Memory Total: " + lparMemTotal
    outstr += "\nLPAR Memory Offline: " + lparMemStandby
    outstr += "\nLPAR Memory Used: " + lparMemUsed
    outstr += "\nIPL Time: " + ipl

    rh.printLn("N", outstr)
    rh.printSysLog("Exit getHost.getGeneralInfo, rc: " +
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
    Produce help output specifically for GetHost functions.

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

    rh.printSysLog("Enter getHost.parseCmdline")

    rh.userid = ''

    if rh.totalParms >= 2:
        rh.subfunction = rh.request[1].upper()

    # Verify the subfunction is valid.
    if rh.subfunction not in subfuncHandler:
        # Subfunction is missing.
        subList = ', '.join(sorted(subfuncHandler.keys()))
        msg = msgs.msg['0011'][1] % (modId, subList)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0011'][0])

    # Parse the rest of the command line.
    if rh.results['overallRC'] == 0:
        rh.argPos = 2               # Begin Parsing at 3rd operand
        generalUtils.parseCmdline(rh, posOpsList, keyOpsList)

    rh.printSysLog("Exit getHost.parseCmdLine, rc: " +
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
    rh.printLn("N", "  python " + rh.cmdName + " GetHost " +
        "diskpoolnames")
    rh.printLn("N", "  python " + rh.cmdName + " GetHost " +
        "diskpoolspace <poolName>")
    rh.printLn("N", "  python " + rh.cmdName + " GetHost fcpdevices")
    rh.printLn("N", "  python " + rh.cmdName + " GetHost general")
    rh.printLn("N", "  python " + rh.cmdName + " GetHost help")
    rh.printLn("N", "  python " + rh.cmdName + " GetHost version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the GetHost function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      diskpoolnames - " +
        "Returns the names of the directory manager disk pools.")
    rh.printLn("N", "      diskpoolspace - " +
        "Returns disk pool size information.")
    rh.printLn("N", "      fcpdevices    - " +
        "Lists the FCP device channels that are active, free, or")
    rh.printLn("N", "                      offline.")
    rh.printLn("N", "      general       - " +
        "Returns the general information related to the z/VM")
    rh.printLn("N", "                      hypervisor environment.")
    rh.printLn("N", "      help          - Returns this help information.")
    rh.printLn("N", "      version       - Show the version of this function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
    rh.printLn("N", "      <poolName>    - Name of the disk pool.")

    return
