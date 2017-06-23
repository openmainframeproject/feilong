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

import generalUtils
import os.path
import shutil
import tarfile
import tempfile
from vmUtils import disableEnableDisk, execCmdThruIUCV, installFS
from vmUtils import invokeSMCLI, isLoggedOn
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
        '--lun': ['lun', 1, 2],
        '--scpdata': ['scpData', 1, 2],
        '--scphexdata': ['scpDataHex', 1, 2],
        '--showparms': ['showParms', 0, 0],
        '--wwpn': ['wwpn', 1, 2]},
    'PUNCHFILE': {
        '--class': ['class', 1, 2],
        '--showparms': ['showParms', 0, 0], },
    'PURGERDR': {'--showparms': ['showParms', 0, 0]},
    'REMOVEDISK': {'--showparms': ['showParms', 0, 0]},
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
        cmd = ["smcli",
               "Image_Disk_Create_DM",
               "-T", rh.userid,
               "-v", rh.parms['vaddr'],
               "-t", "3390",
               "-a", "AUTOG",
               "-r", rh.parms['diskPool'],
               "-u", "1",
               "-z", cyl,
               "-f", "1"]

        if 'mode' in rh.parms:
            cmd.extend(["-m", rh.parms['mode']])
        else:
            cmd.extend(["-m", 'W'])
        if 'readPW' in rh.parms:
            cmd.extend(["-R", rh.parms['readPW']])
        if 'writePW' in rh.parms:
            cmd.extend(["-W", rh.parms['writePW']])
        if 'multiPW' in rh.parms:
            cmd.extend(["-M", rh.parms['multiPW']])

        results = invokeSMCLI(rh, cmd)

        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed: '" + strCmd +
                       "', out: '" + results['response'] +
                       "', rc: " + str(results['overallRC']))
            rh.updateResults(results)

    if (results['overallRC'] == 0 and 'filesystem' in rh.parms):
        results = installFS(
            rh,
            rh.parms['vaddr'],
            rh.parms['mode'],
            rh.parms['fileSystem'])

    if results['overallRC'] == 0:
        results = isLoggedOn(rh, rh.userid)
        if (results['overallRC'] == 0 and results['rs'] == 0):
            # Add the disk to the active configuration.
            cmd = ["smcli",
                "Image_Disk_Create",
                "-T", rh.userid,
                "-v", rh.parms['vaddr'],
                "-m", rh.parms['mode']]

            results = invokeSMCLI(rh, cmd)
            if results['overallRC'] == 0:
                rh.printLn("N", "Added dasd " + rh.parms['vaddr'] +
                    " to the active configuration.")
            else:
                strCmd = ' '.join(cmd)
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + "', rc: " +
                    str(results['overallRC']))
                rh.updateResults(results)

    rh.printSysLog("Exit changeVM.add3390, rc: " +
                   str(results['overallRC']))

    return results['overallRC']


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
        cmd = ["smcli",
               "Image_Disk_Create_DM",
               "-T", rh.userid,
               "-v", rh.parms['vaddr'],
               "-t", "9336",
               "-a", "AUTOG",
               "-r", rh.parms['diskPool'],
               "-u", "1",
               "-z", blocks,
               "-f", "1"]

        if 'mode' in rh.parms:
            cmd.extend(["-m", rh.parms['mode']])
        else:
            cmd.extend(["-m", 'W'])
        if 'readPW' in rh.parms:
            cmd.extend(["-R", rh.parms['readPW']])
        if 'writePW' in rh.parms:
            cmd.extend(["-W", rh.parms['writePW']])
        if 'multiPW' in rh.parms:
            cmd.extend(["-M", rh.parms['multiPW']])

        results = invokeSMCLI(rh, cmd)

        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed: '" + strCmd +
                       "', out: '" + results['response'] +
                       "', rc: " + str(results['overallRC']))
            rh.updateResults(results)

    if (results['overallRC'] == 0 and 'filesystem' in rh.parms):
        # Install the file system
        results = installFS(
            rh,
            rh.parms['vaddr'],
            rh.parms['mode'],
            rh.parms['fileSystem'])

    if results['overallRC'] == 0:
        results = isLoggedOn(rh, rh.userid)
        if (results['overallRC'] == 0 and results['rs'] == 0):
            # Add the disk to the active configuration.
            cmd = ["smcli",
                "Image_Disk_Create",
                "-T", rh.userid,
                "-v", rh.parms['vaddr'],
                "-m", rh.parms['mode']]

            results = invokeSMCLI(rh, cmd)
            if results['overallRC'] == 0:
                rh.printLn("N", "Added dasd " + rh.parms['vaddr'] +
                    " to the active configuration.")
            else:
                strCmd = ' '.join(cmd)
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + "', rc: " +
                    str(results['overallRC']))
                rh.updateResults(results)

    rh.printSysLog("Exit changeVM.add9336, rc: " +
                   str(results['overallRC']))
    return results['overallRC']


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
       Return code - 0: ok, non-zero: error
    """
    rc = 0
    rh.printSysLog("Enter changeVM.addAEMOD")
    invokeScript = "invokeScript.sh"
    trunkFile = "aemod.doscript"
    fileClass = "X"
    tempDir = tempfile.mkdtemp()

    conf = "#!/bin/bash \n"
    parm = "/bin/bash %s %s \n" % (rh.parms['aeScript'], rh.parms['invParms'])

    fh = open(tempDir + "/" + invokeScript, "w")
    fh.write(conf)
    fh.write(parm)
    fh.close()

    if os.path.isfile(rh.parms['aeScript']):
        # Get the short name of our activation engine modifier script
        if rh.parms['aeScript'].startswith("/"):
            s = rh.parms['aeScript']
            tmpAEScript = s[s.rindex("/") + 1:]
        else:
            tmpAEScript = rh.parms['aeScript']
        # Copy the mod script to our temp directory
        shutil.copyfile(rh.parms['aeScript'], tempDir + "/" + tmpAEScript)
        # Generate the tar package for punch

        with tarfile.open(tempDir + "/" + trunkFile, "w") as tar:
            tar.add(tempDir, arcname=os.path.basename(tempDir))

        # Punch file to reader
        rh.parms['class'] = fileClass
        rh.parms['file'] = trunkFile
        results = punchFile(rh)
        if results != 0:
            rh.printLn("ES", "Failed to punch file to guest: '" +
                       "Guest " + rh.userid + "out " + results)
            shutil.rmtree(tempDir)
            rh.updateResults(results)
            return
    else:
        rh.printLn("ES", "The worker script " +
                   rh.parms['aeScript'] + " does not exist.")
        shutil.rmtree(tempDir)
        return

    rh.printSysLog("Exit changeVM.addAEMOD, rc: " + str(rc))
    return 0


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
    rc = 0
    rh.printSysLog("Enter changeVM.addIPL")

    rh.printLn("N", "This subfunction is not implemented yet.")

    rh.printSysLog("Exit changeVM.addIPL, rc: " + str(rc))
    return 0


def addLOADDEV(rh):
    """
    Sets the LOADDEV statement in the virtual machine's directory entry.

    Input:
       Request Handle with the following properties:
          function    - 'CHANGEVM'
          subfunction - 'ADDLOADDEV'
          userid      - userid of the virtual machine
          parms['scpDataHex'] - SCP data in hex
          parms['lun']        - One to eight-byte logical unit number
                                of the FCP-I/O device.
          parms['scpData']    - Designates information to be passed to the
                                program is loaded during guest IPL.
          parms['wwpn']       - World-Wide Port Number

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    rc = 0
    rh.printSysLog("Enter changeVM.addLOADDEV")

    rh.printLn("N", "This subfunction is not implemented yet.")

    rh.printSysLog("Exit changeVM.addLOADDEV, rc: " + str(rc))
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

    rc = 0
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

    rh.printSysLog("Exit changeVM.doIt, rc: " + str(rc))
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
        rh.printLn("ES", "Userid is missing")
        rh.updateResults({'overallRC': 4})
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
        list = ', '.join(sorted(subfuncHandler.keys()))
        rh.printLn("ES", "Subfunction is missing.  " +
            "It should be one of the following: " + list + ".")
        rh.updateResults({'overallRC': 4})

    # Parse the rest of the command line.
    if rh.results['overallRC'] == 0:
        rh.argPos = 3               # Begin Parsing at 4th operand
        generalUtils.parseCmdline(rh, posOpsList, keyOpsList)

    if rh.results['overallRC'] == 0:
        if rh.subfunction in ['ADD3390', 'ADD9336']:
            if ('fileSystem' in rh.parms and rh.parms['fileSystem'] not in
                ['ext2', 'ext3', 'ext4', 'xfs', 'swap']):
                rh.printLn("ES", "The file system was not 'ext2', " +
                    "'ext3', 'ext4', 'xfs' or 'swap': " +
                    rh.parms['fileSystem'] + ".")
                rh.updateResults({'overallRC': 4})

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
    rc = 0
    rh.printSysLog("Enter changeVM.punchFile")

    rh.printLn("N", "This subfunction is not implemented yet.")

    rh.printSysLog("Exit changeVM.punchFile, rc: " + str(rc))
    return 0


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
    rc = 0
    rh.printSysLog("Enter changeVM.purgeRDR")

    rh.printLn("N", "This subfunction is not implemented yet.")

    rh.printSysLog("Exit changeVM.purgeRDR, rc: " + str(rc))
    return 0


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
    rc = 0
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
                # Error message already produced
                pass
            else:
                # Pass along the failure information.
                rh.updateResults(results)

    if results['overallRC'] == 0 and loggedOn:
        strCmd = ["/sbin/vmcp detach " + rh.parms['vaddr']]
        results = execCmdThruIUCV(rh, rh.userid, strCmd)
        if results['overallRC'] != 0:
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # Remove the disk from the user entry.
        cmd = ["smcli",
            "Image_Disk_Delete_DM",
            "-T", rh.userid,
            "-v", rh.parms['vaddr'],
            "-e", "0"]

        results = invokeSMCLI(rh, cmd)
        if results['overallRC'] == 0:
            rh.printLn("N", "Removed dasd " + rh.parms['vaddr'] +
                " from the user directory.")
        else:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                results['response'] + "', rc: " +
                str(results['overallRC']))
            rh.updateResults(results)

    else:
        # Unexpected error.  Message already sent.
        rh.updateResults(results)

    rh.printSysLog("Exit changeVM.removeDisk, rc: " + str(rc))
    return 0


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
    rh.printLn("N", "                    <diskSize3390> mode <mode> " +
               "readpw <read_pw>")
    rh.printLn("N", "                    writepw <write_pw> multipw " +
               "<multi_pw> filesystem <fsType>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> add9336 <diskPool> <vAddr>")
    rh.printLn("N", "                    <diskSize9336> mode <mode> " +
               "readpw <read_pw>")
    rh.printLn("N", "                    writepw <write_pw> " +
               "multipw <multi_pw> filesystem <fsType>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> aemod <aeScript> invparms <invParms>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> IPL <addrOrNSS> loadparms <loadParms>")
    rh.printLn("N", "                    parms <parmString>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> LOADDEV wwpn <wwpn> lun <lun>")
    rh.printLn("N", "                    scphexdata <scp_hex> " +
               "scpdata <scp_data>")
    rh.printLn("N", "  python " + rh.cmdName +
               " ChangeVM <userid> punchFile <file> class <class>")
    rh.printLn("N", "  python " + rh.cmdName +
        " ChangeVM <userid> purgeRDR")
    rh.printLn("N", "  python " + rh.cmdName +
        " ChangeVM <userid> removedisk <vAddr>")
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
    rh.printLn("N", "      version       - " +
               "show the version of the power function")
    if rh.subfunction != '':
        rh.printLn("N", "Operand(s):")
        rh.printLn("N", "      <addrOrNSS>           - " +
                   "Specifies the virtual address or NSS name")
        rh.printLn("N", "                              to IPL.")
        rh.printLn("N", "      <aeScript>            - " +
                   "aeScript is the fully qualified file")
        rh.printLn("N", "                              " +
                   "specification of the script to be sent")
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
        rh.printLn("N", "      --scpdata <scp_data>  - " +
                   "Provides the SCP data information.")
        rh.printLn("N", "      --scphexdata <scp_hex> - " +
                   "Provides the SCP data information as hexadecimal")
        rh.printLn("N", "                              " +
                   "representation of UTF-8 data.")
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
