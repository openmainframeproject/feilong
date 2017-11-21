# ChangeVM functions for Systems Management Ultra Thin Layer
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

import os.path
import re
import shutil
import tarfile
import tempfile

import generalUtils
import msgs
from vmUtils import disableEnableDisk, execCmdThruIUCV, installFS
from vmUtils import invokeSMCLI, isLoggedOn, punch2reader, purgeReader


modId = "CVM"
version = "1.0.0"

"""
List of subfunction handlers.
Each subfunction contains a list that has:
  Readable name of the routine that handles the subfunction,
  Code for the function call.
"""
subfuncHandler = {
    'ADD3390': ['add3390', lambda rh: add3390(rh)],
    'ADD9336': ['add9336', lambda rh: add9336(rh)],
    'AEMOD': ['addAEMOD', lambda rh: addAEMOD(rh)],
    'IPL': ['addIPL', lambda rh: addIPL(rh)],
    'LOADDEV': ['addLOADDEV', lambda rh: addLOADDEV(rh)],
    'HELP': ['help', lambda rh: help(rh)],
    'PUNCHFILE': ['punchFile', lambda rh: punchFile(rh)],
    'PURGERDR': ['purgeRDR', lambda rh: purgeRDR(rh)],
    'REMOVEDISK': ['removeDisk', lambda rh: removeDisk(rh)],
    'REMOVEIPL': ['removeIPL', lambda rh: removeIPL(rh)],
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
    'ADD3390': [
        ['Disk pool name', 'diskPool', True, 2],
        ['Virtual address', 'vaddr', True, 2],
        ['Disk size', 'diskSize', True, 2]],
    'ADD9336': [
        ['Disk pool name', 'diskPool', True, 2],
        ['Virtual address', 'vaddr', True, 2],
        ['Disk size', 'diskSize', True, 2]],
    'AEMOD': [
        ['Activation Engine Modification Script',
         'aeScript', True, 2]],
    'IPL': [
        ['Virtual Address or NSS name', 'addrOrNSS', True, 2]],
    'PUNCHFILE': [
        ['File to punch', 'file', True, 2]],
    'REMOVEDISK': [
        ['Virtual address', 'vaddr', True, 2]],
    'REMOVEIPL': [],
    }

"""
List of additional operands/options supported by the various subfunctions.
The dictionary following the subfunction name uses the keyword from the
command as a key.  Each keyword has a dictionary that lists:
  - the related parms item that stores the value,
  - how many values follow the keyword, and
  - the type of data for those values (1: int, 2: string)
"""
keyOpsList = {
    'ADD3390': {
        '--filesystem': ['fileSystem', 1, 2],
        '--mode': ['mode', 1, 2],
        '--multipw': ['multiPW', 1, 2],
        '--readpw': ['readPW', 1, 2],
        '--showparms': ['showParms', 0, 0],
        '--writepw': ['writePW', 1, 2]},
    'ADD9336': {
        '--filesystem': ['fileSystem', 1, 2],
        '--mode': ['mode', 1, 2],
        '--multipw': ['multiPW', 1, 2],
        '--readpw': ['readPW', 1, 2],
        '--showparms': ['showParms', 0, 0],
        '--writepw': ['writePW', 1, 2]},
    'AEMOD': {
        '--invparms': ['invParms', 1, 2],
        '--showparms': ['showParms', 0, 0]},
    'HELP': {},
    'IPL': {
        '--loadparms': ['loadParms', 1, 2],
        '--parms': ['parms', 1, 2],
        '--showparms': ['showParms', 0, 0]},
    'LOADDEV': {
        '--boot': ['boot', 1, 2],
        '--addr': ['addr', 1, 2],
        '--lun': ['lun', 1, 2],
        '--wwpn': ['wwpn', 1, 2],
        '--scpDataType': ['scpDataType', 1, 2],
        '--scpData': ['scpData', 1, 2],
        '--showparms': ['showParms', 0, 0]},
    'PUNCHFILE': {
        '--class': ['class', 1, 2],
        '--showparms': ['showParms', 0, 0], },
    'PURGERDR': {'--showparms': ['showParms', 0, 0]},
    'REMOVEDISK': {'--showparms': ['showParms', 0, 0]},
    'REMOVEIPL': {'--showparms': ['showParms', 0, 0]},
    'VERSION': {},
}


def add3390(rh):
    """
    Adds a 3390 (ECKD) disk to a virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'ADD3390'
          userid      - userid of the virtual machine
          parms['diskPool']   - Disk pool
          parms['diskSize']   - size of the disk in cylinders or bytes.
          parms['fileSystem'] - Linux filesystem to install on the disk.
          parms['mode']       - Disk access mode
          parms['multiPW']    - Multi-write password
          parms['readPW']     - Read password
          parms['vaddr']      - Virtual address
          parms['writePW']    - Write password

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.add3390")
    results, cyl = generalUtils.cvtToCyl(rh, rh.parms['diskSize'])
    if results['overallRC'] != 0:
        # message already sent.  Only need to update the final results.
        rh.updateResults(results)

    if results['overallRC'] == 0:
        parms = [
            "-T", rh.userid,
            "-v", rh.parms['vaddr'],
            "-t", "3390",
            "-a", "AUTOG",
            "-r", rh.parms['diskPool'],
            "-u", "1",
            "-z", cyl,
            "-f", "1"]
        hideList = []

        if 'mode' in rh.parms:
            parms.extend(["-m", rh.parms['mode']])
        else:
            parms.extend(["-m", 'W'])
        if 'readPW' in rh.parms:
            parms.extend(["-R", rh.parms['readPW']])
            hideList.append(len(parms) - 1)
        if 'writePW' in rh.parms:
            parms.extend(["-W", rh.parms['writePW']])
            hideList.append(len(parms) - 1)
        if 'multiPW' in rh.parms:
            parms.extend(["-M", rh.parms['multiPW']])
            hideList.append(len(parms) - 1)

        results = invokeSMCLI(rh,
                              "Image_Disk_Create_DM",
                              parms,
                              hideInLog=hideList)

        if results['overallRC'] != 0:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)  # Use results returned by invokeSMCLI

    if (results['overallRC'] == 0 and 'fileSystem' in rh.parms):
        results = installFS(
            rh,
            rh.parms['vaddr'],
            rh.parms['mode'],
            rh.parms['fileSystem'],
            "3390")

    if results['overallRC'] == 0:
        results = isLoggedOn(rh, rh.userid)
        if results['overallRC'] != 0:
            # Cannot determine if VM is logged on or off.
            # We have partially failed.  Pass back the results.
            rh.updateResults(results)
        elif results['rs'] == 0:
            # Add the disk to the active configuration.
            parms = [
                "-T", rh.userid,
                "-v", rh.parms['vaddr'],
                "-m", rh.parms['mode']]

            results = invokeSMCLI(rh, "Image_Disk_Create", parms)
            if results['overallRC'] == 0:
                rh.printLn("N", "Added dasd " + rh.parms['vaddr'] +
                    " to the active configuration.")
            else:
                # SMAPI API failed.
                rh.printLn("ES", results['response'])
                rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit changeVM.add3390, rc: " +
                   str(rh.results['overallRC']))

    return rh.results['overallRC']


def add9336(rh):
    """
    Adds a 9336 (FBA) disk to virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'ADD9336'
          userid      - userid of the virtual machine
          parms['diskPool']   - Disk pool
          parms['diskSize']   - size of the disk in blocks or bytes.
          parms['fileSystem'] - Linux filesystem to install on the disk.
          parms['mode']       - Disk access mode
          parms['multiPW']    - Multi-write password
          parms['readPW']     - Read password
          parms['vaddr']      - Virtual address
          parms['writePW']    - Write password

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.add9336")
    results, blocks = generalUtils.cvtToBlocks(rh, rh.parms['diskSize'])
    if results['overallRC'] != 0:
        # message already sent.  Only need to update the final results.
        rh.updateResults(results)

    if results['overallRC'] == 0:
        parms = [
            "-T", rh.userid,
            "-v", rh.parms['vaddr'],
            "-t", "9336",
            "-a", "AUTOG",
            "-r", rh.parms['diskPool'],
            "-u", "1",
            "-z", blocks,
            "-f", "1"]
        hideList = []

        if 'mode' in rh.parms:
            parms.extend(["-m", rh.parms['mode']])
        else:
            parms.extend(["-m", 'W'])
        if 'readPW' in rh.parms:
            parms.extend(["-R", rh.parms['readPW']])
            hideList.append(len(parms) - 1)
        if 'writePW' in rh.parms:
            parms.extend(["-W", rh.parms['writePW']])
            hideList.append(len(parms) - 1)
        if 'multiPW' in rh.parms:
            parms.extend(["-M", rh.parms['multiPW']])
            hideList.append(len(parms) - 1)

        results = invokeSMCLI(rh,
                              "Image_Disk_Create_DM",
                              parms,
                              hideInLog=hideList)

        if results['overallRC'] != 0:
            # SMAPI API failed.
            rh.printLn("ES", results['response'])
            rh.updateResults(results)    # Use results from invokeSMCLI

    if (results['overallRC'] == 0 and 'fileSystem' in rh.parms):
        # Install the file system
        results = installFS(
            rh,
            rh.parms['vaddr'],
            rh.parms['mode'],
            rh.parms['fileSystem'],
            "9336")

    if results['overallRC'] == 0:
        results = isLoggedOn(rh, rh.userid)
        if (results['overallRC'] == 0 and results['rs'] == 0):
            # Add the disk to the active configuration.
            parms = [
                "-T", rh.userid,
                "-v", rh.parms['vaddr'],
                "-m", rh.parms['mode']]

            results = invokeSMCLI(rh, "Image_Disk_Create", parms)
            if results['overallRC'] == 0:
                rh.printLn("N", "Added dasd " + rh.parms['vaddr'] +
                    " to the active configuration.")
            else:
                # SMAPI API failed.
                rh.printLn("ES", results['response'])
                rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit changeVM.add9336, rc: " +
                   str(rh.results['overallRC']))
    return rh.results['overallRC']


def addAEMOD(rh):
    """
    Send an Activation Modification Script to the virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'AEMOD'
          userid      - userid of the virtual machine
          parms['aeScript']   - File specification of the AE script
          parms['invparms']   - invparms operand

    Output:
       Request Handle updated with the results.
       Return code - 0: ok
       Return code - 4: input error, rs - 11 AE script not found
    """
    rh.printSysLog("Enter changeVM.addAEMOD")
    invokeScript = "invokeScript.sh"
    trunkFile = "aemod.doscript"
    fileClass = "X"
    tempDir = tempfile.mkdtemp()

    if os.path.isfile(rh.parms['aeScript']):
        # Get the short name of our activation engine modifier script
        if rh.parms['aeScript'].startswith("/"):
            s = rh.parms['aeScript']
            tmpAEScript = s[s.rindex("/") + 1:]
        else:
            tmpAEScript = rh.parms['aeScript']

        # Copy the mod script to our temp directory
        shutil.copyfile(rh.parms['aeScript'], tempDir + "/" + tmpAEScript)

        # Create the invocation script.
        conf = "#!/bin/bash \n"
        baseName = os.path.basename(rh.parms['aeScript'])
        parm = "/bin/bash %s %s \n" % (baseName, rh.parms['invParms'])

        fh = open(tempDir + "/" + invokeScript, "w")
        fh.write(conf)
        fh.write(parm)
        fh.close()

        # Generate the tar package for punch
        tar = tarfile.open(tempDir + "/" + trunkFile, "w")
        for file in os.listdir(tempDir):
            tar.add(tempDir + "/" + file, arcname=file)
        tar.close()

        # Punch file to reader
        punch2reader(rh, rh.userid, tempDir + "/" + trunkFile, fileClass)
        shutil.rmtree(tempDir)

    else:
        # Worker script does not exist.
        shutil.rmtree(tempDir)
        msg = msgs.msg['0400'][1] % (modId, rh.parms['aeScript'])
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0400'][0])

    rh.printSysLog("Exit changeVM.addAEMOD, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def addIPL(rh):
    """
    Sets the IPL statement in the virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'IPL'
          userid      - userid of the virtual machine
          parms['addrOrNSS']  - Address or NSS name
          parms['loadparms']  - Loadparms operand (optional)
          parms['parms']      - Parms operand (optional)

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.addIPL")

    parms = ["-T", rh.userid, "-s", rh.parms['addrOrNSS']]

    if 'loadparms' in rh.parms:
        parms.extend(["-l", rh.parms['loadparms']])
    if 'parms' in rh.parms:
        parms.extend(["-p", rh.parms['parms']])

    results = invokeSMCLI(rh, "Image_IPL_Set_DM", parms)

    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit changeVM.addIPL, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def addLOADDEV(rh):
    """
    Sets the LOADDEV statement in the virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'ADDLOADDEV'
          userid      - userid of the virtual machine
          parms['boot']       - Boot program number
          parms['addr']       - Logical block address of the boot record
          parms['lun']        - One to eight-byte logical unit number
                                of the FCP-I/O device.
          parms['wwpn']       - World-Wide Port Number
          parms['scpDataType'] - SCP data type
          parms['scpData']    - Designates information to be passed to the
                                program is loaded during guest IPL.

          Note that any of the parms may be left blank, in which case
          we will not update them.


    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    rh.printSysLog("Enter changeVM.addLOADDEV")

    # scpDataType and scpData must appear or disappear concurrently
    if ('scpData' in rh.parms and 'scpDataType' not in rh.parms):
        msg = msgs.msg['0014'][1] % (modId, "scpData", "scpDataType")
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0014'][0])
        return
    if ('scpDataType' in rh.parms and 'scpData' not in rh.parms):
        if rh.parms['scpDataType'].lower() == "delete":
            scpDataType = 1
        else:
            # scpDataType and scpData must appear or disappear
            # concurrently unless we're deleting data
            msg = msgs.msg['0014'][1] % (modId, "scpDataType", "scpData")
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0014'][0])
            return

    scpData = ""
    if 'scpDataType' in rh.parms:
        if rh.parms['scpDataType'].lower() == "hex":
            scpData = rh.parms['scpData']
            scpDataType = 3
        elif rh.parms['scpDataType'].lower() == "ebcdic":
            scpData = rh.parms['scpData']
            scpDataType = 2
        # scpDataType not hex, ebcdic or delete
        elif rh.parms['scpDataType'].lower() != "delete":
            msg = msgs.msg['0016'][1] % (modId, rh.parms['scpDataType'])
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0016'][0])
            return
    else:
        # Not specified, 0 for do nothing
        scpDataType = 0
        scpData = ""

    if 'boot' not in rh.parms:
        boot = ""
    else:
        boot = rh.parms['boot']
    if 'addr' not in rh.parms:
        block = ""
    else:
        block = rh.parms['addr']
    if 'lun' not in rh.parms:
        lun = ""
    else:
        lun = rh.parms['lun']
        # Make sure it doesn't have the 0x prefix
        lun.replace("0x", "")
    if 'wwpn' not in rh.parms:
        wwpn = ""
    else:
        wwpn = rh.parms['wwpn']
        # Make sure it doesn't have the 0x prefix
        wwpn.replace("0x", "")

    parms = [
        "-T", rh.userid,
        "-b", boot,
        "-k", block,
        "-l", lun,
        "-p", wwpn,
        "-s", str(scpDataType)]

    if scpData != "":
        parms.extend(["-d", scpData])

    results = invokeSMCLI(rh, "Image_SCSI_Characteristics_Define_DM", parms)

    # SMAPI API failed.
    if results['overallRC'] != 0:
        rh.printLn("ES", results['response'])
        rh.updateResults(results)

    rh.printSysLog("Exit changeVM.addLOADDEV, rc: " +
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

    rh.printSysLog("Enter changeVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in rh.parms and rh.parms['showParms'] is True:
        rh.printLn("N", "Invocation parameters: ")
        rh.printLn("N", "  Routine: changeVM." +
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

    rh.printSysLog("Exit changeVM.doIt, rc: " +
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
    Produce help output specifically for ChangeVM functions.

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

    rh.printSysLog("Enter changeVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit changeVM.parseCmdLine, rc: " +
            str(rh.results['overallRC']))
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

    if rh.results['overallRC'] == 0:
        if rh.subfunction in ['ADD3390', 'ADD9336']:
            if ('fileSystem' in rh.parms and rh.parms['fileSystem'] not in
                ['ext2', 'ext3', 'ext4', 'xfs', 'swap']):
                # Invalid file system specified.
                msg = msgs.msg['0015'][1] % (modId, rh.parms['fileSystem'])
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0015'][0])

    rh.printSysLog("Exit changeVM.parseCmdLine, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def punchFile(rh):
    """
    Punch a file to a virtual reader of the specified virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'PUNCHFILE'
          userid      - userid of the virtual machine
          parms['class']    - Spool class (optional)
          parms['file']     - Filespec of the file to punch.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.punchFile")

    # Default spool class in "A" , if specified change to specified class
    spoolClass = "A"
    if 'class' in rh.parms:
        spoolClass = str(rh.parms['class'])

    punch2reader(rh, rh.userid, rh.parms['file'], spoolClass)

    rh.printSysLog("Exit changeVM.punchFile, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def purgeRDR(rh):
    """
    Purge the reader belonging to the virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'PURGERDR'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.purgeRDR")
    results = purgeReader(rh)
    rh.updateResults(results)
    rh.printSysLog("Exit changeVM.purgeRDR, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def removeDisk(rh):
    """
    Remove a disk from a virtual machine.

    Input:
       Request Handle with the following properties:
          function         - 'CHANGEVM'
          subfunction      - 'REMOVEDISK'
          userid           - userid of the virtual machine
          parms['vaddr']   - Virtual address

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.removeDisk")

    results = {'overallRC': 0, 'rc': 0, 'rs': 0}

    # Is image logged on
    loggedOn = False
    results = isLoggedOn(rh, rh.userid)
    if results['overallRC'] == 0:
        if results['rs'] == 0:
            loggedOn = True

            results = disableEnableDisk(
                rh,
                rh.userid,
                rh.parms['vaddr'],
                '-d')
            if results['overallRC'] != 0:
                rh.printLn("ES", results['response'])
                rh.updateResults(results)

    if results['overallRC'] == 0 and loggedOn:
        strCmd = "sudo /sbin/vmcp detach " + rh.parms['vaddr']
        results = execCmdThruIUCV(rh, rh.userid, strCmd)
        if results['overallRC'] != 0:
            if re.search('(^HCP\w\w\w040E)', results['response']):
                # Device does not exist, ignore the error
                results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
            else:
                rh.printLn("ES", results['response'])
                rh.updateResults(results)

    if results['overallRC'] == 0:
        # Remove the disk from the user entry.
        parms = [
            "-T", rh.userid,
            "-v", rh.parms['vaddr'],
            "-e", "0"]

        results = invokeSMCLI(rh, "Image_Disk_Delete_DM", parms)
        if results['overallRC'] != 0:
            if (results['overallRC'] == 8 and results['rc'] == 208 and
                    results['rs'] == 36):
                # Disk does not exist, ignore the error
                results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
            else:
                # SMAPI API failed.
                rh.printLn("ES", results['response'])
                rh.updateResults(results)    # Use results from invokeSMCLI

    else:
        # Unexpected error.  Message already sent.
        rh.updateResults(results)

    rh.printSysLog("Exit changeVM.removeDisk, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def removeIPL(rh):
    """
    Sets the IPL statement in the virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'REMOVEIPL'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter changeVM.removeIPL")

    parms = ["-T", rh.userid]
    results = invokeSMCLI(rh, "Image_IPL_Delete_DM", parms)

    if results['overallRC'] != 0:
        # SMAPI API failed.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)    # Use results from invokeSMCLI

    rh.printSysLog("Exit changeVM.removeIPL, rc: " +
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
               " ChangeVM <userid> add3390 <diskPool> <vAddr>")
    rh.printLn("N", "                    <diskSize3390> --mode " +
               "<mode> --readpw <read_pw>")
    rh.printLn("N", "                    --writepw <write_pw> " +
               "--multipw <multi_pw> --filesystem <fsType>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> add9336 <diskPool> <vAddr>")
    rh.printLn("N", "                    <diskSize9336> --mode " +
               "<mode> --readpw <read_pw>")
    rh.printLn("N", "                    --writepw <write_pw> " +
               "--multipw <multi_pw> --filesystem <fsType>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> aemod <aeScript> --invparms <invParms>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> IPL <addrOrNSS> --loadparms <loadParms>")
    rh.printLn("N", "                    --parms <parmString>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> loaddev --boot <boot> --addr <addr>")
    rh.printLn("N", "                     --wwpn <wwpn> --lun <lun> " +
               "--scpdatatype <scpDatatype> --scpdata <scp_data>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> punchFile <file> --class <class>")
    rh.printLn("N", "  python " + rh.cmdName +
        " ChangeVM <userid> purgeRDR")
    rh.printLn("N", "  python " + rh.cmdName +
        " ChangeVM <userid> removedisk <vAddr>")
    rh.printLn("N", "  python " + rh.cmdName +
        " ChangeVM <userid> removeIPL <vAddr>")
    rh.printLn("N", "  python " + rh.cmdName + " ChangeVM help")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM version")
    return


def showOperandLines(rh):
    """
    Produce help output related to operands.

    Input:
       Request Handle
    """

    if rh.function == 'HELP':
        rh.printLn("N", "  For the ChangeVM function:")
    else:
        rh.printLn("N", "Sub-Functions(s):")
    rh.printLn("N", "      add3390       - Add a 3390 (ECKD) disk " +
               "to a virtual machine's directory")
    rh.printLn("N", "                      entry.")
    rh.printLn("N", "      add9336       - Add a 9336 (FBA) disk " +
               "to virtual machine's directory")
    rh.printLn("N", "                      entry.")
    rh.printLn("N", "      aemod         - Sends an activation " +
               "engine script to the managed virtual")
    rh.printLn("N", "                      machine.")
    rh.printLn("N", "      help          - Displays this help " +
               "information.")
    rh.printLn("N", "      ipl           - Sets the IPL statement in " +
               "the virtual machine's")
    rh.printLn("N", "                      directory entry.")
    rh.printLn("N", "      loaddev       - Sets the LOADDEV statement " +
               "in the virtual machine's")
    rh.printLn("N", "                      directory entry.")
    rh.printLn("N", "      punchfile     - Punch a file to a virtual " +
               "reader of the specified")
    rh.printLn("N", "                      virtual machine.")
    rh.printLn("N", "      purgerdr      - Purges the reader " +
        "belonging to the virtual machine.")
    rh.printLn("N", "      removedisk    - " +
        "Remove an mdisk from a virtual machine.")
    rh.printLn("N", "      removeIPL     - " +
        "Remove an IPL from a virtual machine's directory entry.")
    rh.printLn("N", "      version       - " +
               "show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
        rh.printLn("N", "      -addr <addr>          - " +
                   "Specifies the logical block address of the")
        rh.printLn("N", "                              " +
                   "boot record.")
        rh.printLn("N", "      <addrOrNSS>           - " +
                   "Specifies the virtual address or NSS name")
        rh.printLn("N", "                              to IPL.")
        rh.printLn("N", "      <aeScript>            - " +
                   "aeScript is the fully qualified file")
        rh.printLn("N", "                              " +
                   "specification of the script to be sent")
        rh.printLn("N", "      --boot <boot>         - " +
                   "Boot program number")
        rh.printLn("N", "      --class <class>       - " +
                   "The class is optional and specifies the spool")
        rh.printLn("N", "                              " +
                   "class for the reader file.")
        rh.printLn("N", "      <diskPool>            - " +
                   "Specifies the directory manager disk pool to")
        rh.printLn("N", "                              " +
                   "use to obtain the disk.")
        rh.printLn("N", "      <diskSize3390>        - " +
                   "Specifies the size of the ECKD minidisk.  ")
        rh.printLn("N", "      <diskSize9336>        - " +
                   "Specifies the size of the FBA type minidisk.")
        rh.printLn("N", "      <file>                - " +
                   "File to punch to the target system.")
        rh.printLn("N", "      --filesystem <fsType> - " +
                   "Specifies type of filesystem to be created on")
        rh.printLn("N", "                              the minidisk.")
        rh.printLn("N", "      --invparms <invParms> - " +
                   "Specifies the parameters to be specified in the")
        rh.printLn("N", "                              " +
                   "invocation script to call the aeScript.")
        rh.printLn("N", "      --loadparms <loadParms> - " +
                   "Specifies a 1 to 8-character load parameter that")
        rh.printLn("N", "                                " +
                   "is used by the IPL'd system.")
        rh.printLn("N", "      --lun <lun>           - " +
                   "One to eight-byte logical unit number of the")
        rh.printLn("N", "                              FCP-I/O device.")
        rh.printLn("N", "      --mode <mode>         - " +
                   "Specifies the access mode for the minidisk.")
        rh.printLn("N", "      --multipw <multi_pw>  - " +
                   "Specifies the password that allows sharing the")
        rh.printLn("N", "                              " +
                   "minidisk in multiple-write mode.")
        rh.printLn("N", "      --parms <parmString>  - " +
                   "Specifies a parameter string to pass to the")
        rh.printLn("N", "                              " +
                   "virtual machine in general-purpose registers at")
        rh.printLn("N", "                              " +
                   "user's the completion of the IPL.")
        rh.printLn("N", "      --readpw <read_pw>    - " +
                   "Specifies the password that allows sharing the")
        rh.printLn("N", "                              " +
                   "minidisk in read mode.")
        rh.printLn("N", "      --scpdata <scpdata>   - " +
                   "Provides the SCP data information.")
        rh.printLn("N", "      --scpdatatype <scpdatatype> - " +
                   "Specifies whether the scp data is in hex,")
        rh.printLn("N", "                              " +
                   "EBCDIC, or should be deleted.")
        rh.printLn("N", "      <userid>              - " +
                   "Userid of the target virtual machine.")
        rh.printLn("N", "      <vAddr>               - " +
                   "Virtual address of the device.")
        rh.printLn("N", "      --writepw <write_pw>  - " +
                   "Specifies is the password that allows sharing")
        rh.printLn("N", "                              " +
                   "the minidisk in write mode.")
        rh.printLn("N", "      --wwpn <wwpn>         - " +
                   "The world-wide port number.")

    return
