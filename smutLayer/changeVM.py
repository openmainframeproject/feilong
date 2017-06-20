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
from generalUtils import parseCmdline
from vmUtils import invokeSMCLI
version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
    'ADD3390': ['add3390', lambda reqHandle: add3390(reqHandle)],
    'ADD9336': ['add9336', lambda reqHandle: add9336(reqHandle)],
    'AEMOD':   ['addAEMOD', lambda reqHandle: add9336(reqHandle)],
    'IPL':     ['addIPL', lambda reqHandle: addIPL(reqHandle)],
    'LOADDEV': ['addLOADDEV', lambda reqHandle: addLOADDEV(reqHandle)],
    'HELP':    ['help', lambda reqHandle: help(reqHandle)],
    'PUNCHFILE': ['punchFile', lambda reqHandle: punchFile(reqHandle)],
    'PURGERDR':  ['purgeRDR', lambda reqHandle: purgeRDR(reqHandle)],
    'VERSION': ['getVersion', lambda reqHandle: getVersion(reqHandle)],
}

# List of positional operands based on subfunction.
# Each subfunction contains a list which has a dictionary with the following
# information for the positional operands:
#   - Human readable name of the operand,
#   - Property in the parms dictionary to hold the value,
#   - Is it required (True) or optional (False),
#   - Type of data (1: int, 2: string).
posOpsList = {
    'ADD3390': [
        ['Disk pool name', 'diskPool', True, 2],
        ['Virtual address', 'vaddr', True, 2],
        ['Disk size', 'diskSize', True, 2],],
    'ADD9336': [
        ['Disk pool name', 'diskPool', True, 2],
        ['Virtual address', 'vaddr', True, 2],
        ['Disk size', 'diskSize', True, 2],],
    'AEMOD': [
        ['Activation Engine Modification Script',
         'aeScript', True, 2],],
    'IPL': [
        ['Virtual Address or NSS name', 'addrOrNSS', True, 2],],
    'PUNCHFILE': [
        ['File to punch', 'file', True, 2],]
 }

# List of additional operands/options supported by the various subfunctions.
# The dictionary following the subfunction name uses the keyword from the
# command as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values (1: int, 2: string)
keyOpsList = {
    'ADD3390': { 
        'filesystem':   ['fileSystem', 1, 2],
        'mode':         ['mode', 1, 2],
        'multipw':      ['multiPW', 1, 2],
        'readpw':       ['readPW', 1, 2],
        'showparms':    ['showParms', 0, 0],
        'writepw':      ['writePW', 1, 2],},
    'ADD9336': { 
        'filesystem':   ['fileSystem', 1, 2],
        'mode':         ['mode', 1, 2],
        'multipw':      ['multiPW', 1, 2],
        'readpw':       ['readPW', 1, 2],
        'showparms':    ['showParms', 0, 0],
        'writepw':      ['writePW', 1, 2],},
    'AEMOD': { 
        'invparms':     ['invParms', 1, 2],
    'showparms':        ['showParms', 0, 0],},
    'IPL': { 
        'loadparms':    ['loadParms', 1, 2],
        'parms':        ['parms', 1, 2],
        'showparms':    ['showParms', 0, 0],},
    'LOADDEV': { 
        'lun':          ['lun', 1, 2],
        'scpdata':      ['scpData', 1, 2],
        'scphexdata':   ['scpDataHex', 1, 2],
        'showparms':    ['showParms', 0, 0],
        'wwpn':         ['wwpn', 1, 2],},
    'HELP': {},
    'PUNCHFILE': { 
        'class':        ['class', 1, 2],
        'showparms':    ['showParms', 0, 0], },
    'PURGERDR': { 'showparms': ['showParms', 0, 0],},
    'VERSION': {},
  }



def add3390(reqHandle):
    """ Adds a 3390 (ECKD) disk to a virtual machine's directory entry.

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

    reqHandle.printSysLog("Enter changeVM.add3390")

    reqHandle.printLn("N",  "This subfunction is partially implemented.")

    reqHandle.printLn("N",  "China team: Do we need to support" +
                      "'autog' as the virtual address?")

    results,cyl = generalUtils.cvtToCyl(reqHandle, reqHandle.parms['diskSize'])
    if results['overallRC'] != 0:
        # message already sent.  Only need to update the final results.
        reqHandle.updateResults(results)

    if results['overallRC'] == 0:
        cmd = ["smcli",
            "Image_Disk_Create_DM",
            "-T", reqHandle.userid,
            "-v", reqHandle.parms['vaddr'],
            "-t", "3390",
            "-a", "AUTOG",
            "-r", reqHandle.parms['diskPool'],
            "-u", "1",
            "-z", cyl,
            "-f", "1",]

        if 'mode' in reqHandle.parms:
            cmd.extend(["-m", reqHandle.parms['mode']])
        else:
            cmd.extend(["-m", 'W'])
        if 'readPW' in reqHandle.parms:
            cmd.extend(["-R", reqHandle.parms['readPW']])
        if 'writePW' in reqHandle.parms:
            cmd.extend(["-W", reqHandle.parms['writePW']])
        if 'multiPW' in reqHandle.parms:
            cmd.extend(["-M", reqHandle.parms['multiPW']])

        results = invokeSMCLI(reqHandle, cmd)

        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd +
                "', out: '" + results['response'] + 
                "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    reqHandle.printLn("N",  "Setting up the file system is not supported yet!")

    reqHandle.printSysLog("Exit changeVM.add3390, rc: " +
        str(results['overallRC']))

    return results['overallRC']


def add9336(reqHandle):
    """ Adds a 9336 (FBA) disk to virtual machine's directory entry.

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

    reqHandle.printSysLog("Enter changeVM.add9336")
    
    reqHandle.printLn("N",  "This subfunction is partially implemented.")

    results,blocks = generalUtils.cvtToBlocks(reqHandle,
        reqHandle.parms['diskSize'])
    if results['overallRC'] != 0:
        # message already sent.  Only need to update the final results.
        reqHandle.updateResults(results)

    if results['overallRC'] == 0:
        cmd = ["smcli",
                "Image_Disk_Create_DM",
                "-T", reqHandle.userid,
                "-v", reqHandle.parms['vaddr'],
                "-t", "9336",
                "-a", "AUTOG",
                "-r", reqHandle.parms['diskPool'],
                "-u", "1",
                "-z", blocks,
                "-f", "1",]

        if 'mode' in reqHandle.parms:
            cmd.extend(["-m", reqHandle.parms['mode']])
        else:
            cmd.extend(["-m", 'W'])
        if 'readPW' in reqHandle.parms:
            cmd.extend(["-R", reqHandle.parms['readPW']])
        if 'writePW' in reqHandle.parms:
            cmd.extend(["-W", reqHandle.parms['writePW']])
        if 'multiPW' in reqHandle.parms:
            cmd.extend(["-M", reqHandle.parms['multiPW']])

        results = invokeSMCLI(reqHandle, cmd)

        if results['overallRC'] != 0:
            strCmd = ' '.join(cmd)
            reqHandle.printLn("ES",  "Command failed: '" + strCmd +
                "', out: '" + results['response'] + 
                "', rc: " + str(results['overallRC']))
            reqHandle.updateResults(results)

    reqHandle.printLn("N",  "Setting up the file system is not supported yet")

    reqHandle.printSysLog("Exit changeVM.add9336, rc: " +
        str(results['overallRC']))
    return results['overallRC']


def addAEMOD(reqHandle):
    """ Send an Activation Modification Script to the virtual machine.

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
    reqHandle.printSysLog("Enter changeVM.addAEMOD")

    reqHandle.printLn("N",  "This subfunction is not implemented yet.")

    reqHandle.printSysLog("Exit changeVM.addAEMOD, rc: " + str(rc))
    return 0


def addIPL(reqHandle):
    """ Sets the IPL statement in the virtual machine's directory entry.

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
    reqHandle.printSysLog("Enter changeVM.addIPL")

    reqHandle.printLn("N",  "This subfunction is not implemented yet.")

    reqHandle.printSysLog("Exit changeVM.addIPL, rc: " + str(rc))
    return 0


def addLOADDEV(reqHandle):
    """ Sets the LOADDEV statement in the virtual machine's directory entry.

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
    reqHandle.printSysLog("Enter changeVM.addLOADDEV")
    
    reqHandle.printLn("N",  "This subfunction is not implemented yet.")

    reqHandle.printSysLog("Exit changeVM.addLOADDEV, rc: " + str(rc))
    return 0


def doIt(reqHandle):
    """ Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter changeVM.doIt")

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] == True:
        reqHandle.printLn("N", "Invocation parameters: ")
        reqHandle.printLn("N", "  Routine: changeVM." +
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

    reqHandle.printSysLog("Exit changeVM.doIt, rc: " + str(rc))
    return rc


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
    """ Produce help output specifically for ChangeVM functions.

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

    rc = 0
    reqHandle.printSysLog("Enter changeVM.parseCmdline")

    if reqHandle.totalParms >= 2:
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn("ES",  "Userid is missing")
        reqHandle.updateResults({ 'overallRC': 1 })
        reqHandle.printSysLog("Exit changeVM.parseCmdLine, rc: " + rc)
        return 1

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
        rc = 4

    # Parse the rest of the command line.
    if rc == 0:
        reqHandle.argPos = 3               # Begin Parsing at 4th operand
        rc = generalUtils.parseCmdline(reqHandle, posOpsList, keyOpsList)


    reqHandle.printSysLog("Exit changeVM.parseCmdLine, rc: " + str(rc))
    return rc


def punchFile(reqHandle):
    """ Punch a file to a virtual reader of the specified virtual machine.

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
    reqHandle.printSysLog("Enter changeVM.punchFile")
    
    reqHandle.printLn("N",  "This subfunction is not implemented yet.")

    reqHandle.printSysLog("Exit changeVM.punchFile, rc: " + str(rc))
    return 0


def purgeRDR(reqHandle):
    """ Purge the reader belonging to the virtual machine.

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
    reqHandle.printSysLog("Enter changeVM.purgeRDR")
    
    reqHandle.printLn("N",  "This subfunction is not implemented yet.")

    reqHandle.printSysLog("Exit changeVM.purgeRDR, rc: " + str(rc))
    return 0


def showInvLines(reqHandle):
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Usage:")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> add3390 <diskPool> <vAddr>")
    reqHandle.printLn("N", "                    <diskSize3390> mode <mode> " +
        "readpw <read_pw>")
    reqHandle.printLn("N", "                    writepw <write_pw> multipw " +
        "<multi_pw> filesystem <fsType>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> add9336 <diskPool> <vAddr>")
    reqHandle.printLn("N", "                    <diskSize9336> mode <mode> " +
        "readpw <read_pw>")
    reqHandle.printLn("N", "                    writepw <write_pw> " +
        "multipw <multi_pw> filesystem <fsType>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> aemod <aeScript> invparms <invParms>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> IPL <addrOrNSS> loadparms <loadParms>")
    reqHandle.printLn("N", "                    parms <parmString>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> LOADDEV wwpn <wwpn> lun <lun>")
    reqHandle.printLn("N", "                    scphexdata <scp_hex> " +
        "scpdata <scp_data>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> punchFile <file> class <class>")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM <userid> purgeRDR")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName + " ChangeVM help")
    reqHandle.printLn("N", "  python " + reqHandle.cmdName +
        " ChangeVM version")
    return


def showOperandLines(reqHandle):
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP':
        reqHandle.printLn("N", "  For the ChangeVM function:")
    else:
        reqHandle.printLn("N", "Sub-Functions(s):")
    reqHandle.printLn("N", "      add3390       - Add a 3390 (ECKD) disk " +
        "to a virtual machine's directory")
    reqHandle.printLn("N", "                      entry.")
    reqHandle.printLn("N", "      add9336       - Add a 9336 (FBA) disk " +
        "to virtual machine's directory")
    reqHandle.printLn("N", "                      entry.")
    reqHandle.printLn("N", "      aemod         - Sends an activation " +
        "engine script to the managed virtual")
    reqHandle.printLn("N", "                      machine.")
    reqHandle.printLn("N", "      help          - Displays this help " +
        "information.")
    reqHandle.printLn("N", "      ipl           - Sets the IPL statement in " +
        "the virtual machine's")
    reqHandle.printLn("N", "                      directory entry.")
    reqHandle.printLn("N", "      loaddev       - Sets the LOADDEV statement "+
        "in the virtual machine's")
    reqHandle.printLn("N", "                      directory entry.")
    reqHandle.printLn("N", "      punchfile     - Punch a file to a virtual " +
        "reader of the specified")
    reqHandle.printLn("N", "                      virtual machine.")
    reqHandle.printLn("N", "      purgerdr      - Purges the reader " +
        "belonging to the virtual machine.")
    reqHandle.printLn("N", "      version       - show the version of the power function")
    if reqHandle.subfunction != '':
        reqHandle.printLn("N", "Operand(s):")
        reqHandle.printLn("N", "      <addrOrNSS>           - Specifies the virtual address or NSS name")
        reqHandle.printLn("N", "                              to IPL.")
        reqHandle.printLn("N", "      <aeScript>            - aeScript is the fully qualified file")
        reqHandle.printLn("N", "                              specification of the script to be sent")
        reqHandle.printLn("N", "      class <class>         - The class is optional and specifies the spool")
        reqHandle.printLn("N", "                              class for the reader file.")
        reqHandle.printLn("N", "      <diskPool>            - Specifies the directory manager disk pool to")
        reqHandle.printLn("N", "                              use to obtain the disk.")
        reqHandle.printLn("N", "      <diskSize3390>        - Specifies the size of the ECKD minidisk.  ")
        reqHandle.printLn("N", "      <diskSize9336>        - Specifies the size of the FBA type minidisk.")
        reqHandle.printLn("N", "      <file>                - File to punch to the target system.")
        reqHandle.printLn("N", "      filesystem <fsType>   - Specifies type of filesystem to be created on")
        reqHandle.printLn("N", "                              the minidisk.")
        reqHandle.printLn("N", "      invparms <invParms>   - Specifies the parameters to be specified in the")
        reqHandle.printLn("N", "                              invocation script to call the aeScript.")
        reqHandle.printLn("N", "      loadparms <loadParms> - Specifies a 1 to 8-character load parameter that")
        reqHandle.printLn("N", "                              is used by the IPL'd system.")
        reqHandle.printLn("N", "      lun <lun>             - One to eight-byte logical unit number of the")
        reqHandle.printLn("N", "                              FCP-I/O device.")
        reqHandle.printLn("N", "      mode <mode>           - Specifies the access mode for the minidisk.")
        reqHandle.printLn("N", "      multipw <multi_pw>    - Specifies the password that allows sharing the")
        reqHandle.printLn("N", "                              minidisk in multiple-write mode.")
        reqHandle.printLn("N", "      parms <parmString>    - Specifies a parameter string to pass to the")
        reqHandle.printLn("N", "                              virtual machine in general-purpose registers at")
        reqHandle.printLn("N", "                              user's the completion of the IPL.")
        reqHandle.printLn("N", "      readpw <read_pw>      - Specifies the password that allows sharing the")
        reqHandle.printLn("N", "                              minidisk in read mode.")
        reqHandle.printLn("N", "      scpdata <scp_data>    - Provides the SCP data information.")
        reqHandle.printLn("N", "      scphexdata <scp_hex>  - Provides the SCP data information as hexadecimal")
        reqHandle.printLn("N", "                              representation of UTF-8 data.")
        reqHandle.printLn("N", "      <userid>              - Userid of the target virtual machine.")
        reqHandle.printLn("N", "      <vAddr>               - Virtual address of the device.")
        reqHandle.printLn("N", "      writepw <write_pw>    - Specifies is the password that allows sharing")
        reqHandle.printLn("N", "                              the minidisk in write mode.")
        reqHandle.printLn("N", "      wwpn <wwpn>           - The world-wide port number.")

    return
