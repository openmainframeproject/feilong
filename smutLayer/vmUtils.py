# Virtual Machine Utilities for Systems Management Ultra Thin Layer
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
import sys
import subprocess
from subprocess import CalledProcessError
import time

import msgs

modId = 'VMU'
version = '1.0.0'         # Version of this script


def disableEnableDisk(rh, userid, vaddr, option):
    """
    Disable or enable a disk.

    Input:
       Request Handle:
          owning userid
          virtual address
          option ('-e': enable, '-d': disable)

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - rc from the chccwdev command or IUCV transmission.
          rs        - rs from the chccwdev command or IUCV transmission.
          results   - possible error message from the IUCV transmission.
    """

    rh.printSysLog("Enter vmUtils.disableEnableDisk, userid: " + userid +
        " addr: " + vaddr + " option: " + option)

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
              'response': ''
             }

    """
    Can't guarantee the success of online/offline disk, need to wait
    Until it's done because we may detach the disk after -d option
    or use the disk after the -e option
    """
    for secs in [0.1, 0.4, 1, 1.5, 3, 7, 15, 32, 30, 30,
                60, 60, 60, 60, 60]:
        strCmd = "/sbin/chccwdev " + option + " " + vaddr + " 2>&1"
        results = execCmdThruIUCV(rh, userid, strCmd)
        if results['overallRC'] == 0:
            break
        elif (results['overallRC'] == 2 and results['rc'] == 8 and
            results['rs'] == 1 and option == '-d'):
            # Linux does not know about the disk being disabled.
            # Ok, nothing to do.  Treat this as a success.
            results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'response': ''}
            break
        time.sleep(secs)

    rh.printSysLog("Exit vmUtils.disableEnableDisk, rc: " +
        str(results['overallRC']))
    return results


def execCmdThruIUCV(rh, userid, strCmd):
    """
    Send a command to a virtual machine using IUCV.

    Input:
       Request Handle
       Userid of the target virtual machine
       Command string to send

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, 2: failure
          rc        - RC returned from iucvclnt if overallRC != 0.
          rs        - RS returned from iucvclnt if overallRC != 0.
          errno     - Errno returned from iucvclnt if overallRC != 0.
          response  - Output of the iucvclnt command or this routine.

    Notes:
       1) This routine does not use the Request Handle printLn function.
          This is because an error might be expected and we might desire
          to suppress it.  Instead, any error messages are put in the
          response dictionary element that is returned.
    """

    rh.printSysLog("Enter vmUtils.execCmdThruIUCV, userid: " +
                           userid + " cmd: " + strCmd)
    iucvpath = '/opt/zthin/bin/IUCV/'
    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
              'errno': 0,
              'response': [],
             }

    strCmd = (iucvpath + "iucvclnt " + userid + " '" + strCmd + "' 2>&1")
    try:
        results['response'] = subprocess.check_output(
                strCmd,
                stderr=subprocess.STDOUT,
                close_fds=True,
                shell=True)

    except CalledProcessError as e:
        msg = []
        results['overallRC'] = 2
        results['rc'] = e.returncode

        match = re.search('Return code (.+?),', e.output)
        if match:
            try:
                results['rc'] = int(match.group(1))
            except ValueError:
                # Return code in response from IUCVCLNT is not an int.
                msg = msgs.msg['0311'][1] % (modId, userid, strCmd,
                    results['rc'], match.group(1), e.output)

        if not msg:
            # We got the rc. Now, get the rs.
            match = re.search('Reason code (.+?)\.', e.output)
            if match:
                try:
                    results['rs'] = int(match.group(1))
                except ValueError:
                    # Reason code in response from IUCVCLNT is not an int.
                    msg = msgs.msg['0312'][1] % (modId, userid, strCmd,
                        results['rc'], match.group(1), e.output)

        if msg:
            # Already produced an error message.
            pass
        elif results['rc'] == 1:
            # Command was not authorized or a generic Linux error.
            msg = msgs.msg['0313'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        elif results['rc'] == 2:
            # IUCV client parameter error.
            msg = msgs.msg['0314'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        elif results['rc'] == 4:
            # IUCV socket error
            msg = msgs.msg['0315'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        elif results['rc'] == 8:
            # Executed command failed
            msg = msgs.msg['0316'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        elif results['rc'] == 16:
            # File Transport failed
            msg = msgs.msg['0317'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        elif results['rc'] == 32:
            # IUCV server file was not found on this system.
            msg += msgs.msg['0318'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        else:
            # Unrecognized IUCV client error
            msg = msgs.msg['0319'][1] % (modId, userid, strCmd,
                results['rc'], results['rs'], e.output)
        results['response'] = msg

    rh.printSysLog("Exit vmUtils.execCmdThruIUCV, rc: " + str(results['rc']))
    return results


def getPerfInfo(rh, useridlist):
    """
    Get the performance information for a userid

    Input:
       Request Handle
       Userid to query <- may change this to a list later.

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Stripped and reformatted output of the SMCLI command.
    """
    rh.printSysLog("Enter vmUtils.getPerfInfo, userid: " + useridlist)
    parms = ["-T", rh.userid,
             "-c", "1"]
    results = invokeSMCLI(rh, "Image_Performance_Query", parms)
    if results['overallRC'] != 0:
        # SMCLI failed.
        rh.printLn("ES", results['response'])
        rh.printSysLog("Exit vmUtils.getPerfInfo, rc: " +
                       str(results['overallRC']))
        return results

    lines = results['response'].split("\n")
    try:
        for line in lines:
            if "Used CPU time:" in line:
                usedTime = line.split()[3].strip('"')
                # Value is in us, need make it seconds
                usedTime = int(usedTime) / 1000000
            if "Guest CPUs:" in line:
                totalCpu = line.split()[2].strip('"')
            if "Max memory:" in line:
                totalMem = line.split()[2].strip('"')
                # Value is in Kb, need to make it Mb
                totalMem = int(totalMem) / 1024
    except:
        msg = msgs.msg['0412'][1] % (modId, results['response'])
        rh.printLn("ES", msg)
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 412

    if results['overallRC'] == 0:
        memstr = "Total Memory: %iM\n" % totalMem
        procstr = "Processors: %s\n" % totalCpu
        timestr = "CPU Used Time: %i sec\n" % usedTime
        results['response'] = memstr + procstr + timestr
    rh.printSysLog("Exit vmUtils.getPerfInfo, rc: " +
                   str(results['rc']))
    return results


def installFS(rh, vaddr, mode, fileSystem):
    """
    Install a filesystem on a virtual machine's dasd.

    Input:
       Request Handle:
          userid - Userid that owns the disk
       Virtual address as known to the owning system.
       Access mode to use to get the disk.

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Output of the SMCLI command.
    """

    rh.printSysLog("Enter vmUtils.installFS, userid: " + rh.userid +
        " vaddr: " + str(vaddr) + " mode: " + mode + " file system: " +
        fileSystem)

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
              'errno': 0,
             }

    out = ''
    diskAccessed = False

    # Get access to the disk.
    try:
        cmd = ["/opt/zthin/bin/linkdiskandbringonline",
               rh.userid,
               vaddr,
               mode]
        out = subprocess.check_output(cmd, close_fds=True)
        diskAccessed = True
    except CalledProcessError as e:
        strCmd = ' '.join(cmd)
        rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
            e.returncode, e.output))
        results = msgs.msg['0415'][0]
        results['rs'] = e.returncode
        rh.updateResults(results)

    if results['overallRC'] == 0:
        """
        sample output:
        linkdiskandbringonline maint start time: 2017-03-03-16:20:48.011
        Success: Userid maint vdev 193 linked at ad35 device name dasdh
        linkdiskandbringonline exit time: 2017-03-03-16:20:52.150
        """
        match = re.search('Success:(.+?)\n', out)
        if match:
            parts = match.group(1).split()
            if len(parts) > 9:
                device = "/dev/" + parts[9]
            else:
                strCmd = ' '.join(cmd)
                rh.printLn("ES", msgs.msg['0416'][1] % (modId,
                    'Success:', 10, strCmd, out))
                results = msgs.msg['0416'][0]
                rh.updateResults(results)
        else:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", msgs.msg['0417'][1] % (modId,
                'Success:', strCmd, out))
            results = msgs.msg['0417'][0]
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # dasdfmt the disk
        try:
            cmd = ["/sbin/dasdfmt",
                "-y",
                "-b", "4096",
                "-d", "cdl",
                "-f", device]
            out = subprocess.check_output(cmd, close_fds=True)
        except CalledProcessError as e:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                e.returncode, e.output))
            results = msgs.msg['0415'][0]
            results['rs'] = e.returncode
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # Settle the devices so we can do the partition.
        strCmd = ("which udevadm &> /dev/null && " +
            "udevadm settle || udevsettle")
        try:
            subprocess.check_output(
                strCmd,
                stderr=subprocess.STDOUT,
                close_fds=True,
                shell=True)
        except CalledProcessError as e:
            rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                e.returncode, e.output))
            results = msgs.msg['0415'][0]
            results['rs'] = e.returncode
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # Prepare the partition with fdasd
        try:
            cmd = ["/sbin/fdasd", "-a", device]
            out = subprocess.check_output(cmd,
                stderr=subprocess.STDOUT, close_fds=True)
        except CalledProcessError as e:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                e.returncode, e.output))
            results = msgs.msg['0415'][0]
            results['rs'] = e.returncode
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # Install the file system into the disk.
        device = device + "1"       # Point to first partition
        if fileSystem != 'swap':
            if fileSystem == 'xfs':
                cmd = ["mkfs.xfs", "-f", device]
            else:
                cmd = ["mkfs", "-F", "-t", fileSystem, device]
            try:
                out = subprocess.check_output(cmd,
                    stderr=subprocess.STDOUT, close_fds=True)
                rh.printLn("N", "File system: " + fileSystem +
                    " is installed.")
            except CalledProcessError as e:
                strCmd = ' '.join(cmd)
                rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                    e.returncode, e.output))
                results = msgs.msg['0415'][0]
                results['rs'] = e.returncode
                rh.updateResults(results)
        else:
            rh.printLn("N", "File system type is swap. No need to install " +
                "a filesystem.")

    if diskAccessed:
        # Give up the disk.
        try:
            cmd = ["/opt/zthin/bin/offlinediskanddetach",
                   rh.userid,
                   vaddr]
            out = subprocess.check_output(cmd, close_fds=True)
        except CalledProcessError as e:
            strCmd = ' '.join(cmd)
            rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                e.returncode, e.output))
            results = msgs.msg['0415'][0]
            results['rs'] = e.returncode
            rh.updateResults(results)

    rh.printSysLog("Exit vmUtils.installFS, rc: " + str(results['rc']))
    return results


def invokeSMCLI(rh, api, parms):
    """
    Invoke SMCLI and parse the results.

    Input:
       Request Handle
       API name,
       SMCLI parms as an array

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - String output of the SMCLI command.

    Note:
       - If the first three words of the header returned from smcli
         do not do not contain words that represent valid integer
         values or contain too few words then one or more error
         messages are generated. THIS SHOULD NEVER OCCUR !!!!
    """

    rh.printSysLog("Enter vmUtils.invokeSMCLI, userid: " + rh.userid +
        " function: " + api)

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
              'errno': 0,
              'response': [],
              'strError': '',
             }

    cmd = []
    cmd.append('/opt/zthin/bin/smcli')
    cmd.append(api)
    cmd.append('--addRCheader')

    try:
        smcliResp = subprocess.check_output(cmd + parms,
            close_fds=True).split('\n', 1)
        results['response'] = smcliResp[1]
        results['overallRC'] = 0
        results['rc'] = 0

    except CalledProcessError as e:
        strCmd = " ".join(cmd + parms)

        # Break up the RC header into its component parts.
        smcliResp = e.output.split('\n', 1)
        if len(smcliResp) != 2:
            # Only a header line, no data.
            smcliResp[1] = ''

        # Split the header into its component pieces.
        rcHeader = smcliResp[0].split('(details)', 1)
        if len(rcHeader) < 2:
            # No data after the details tag.
            rcHeader[1] = ''
        codes = rcHeader[0].split(' ')

        # Validate the rc, rs, and errno.
        if len(codes) < 3:
            # Unexpected number of codes.  Need at least 3.
            results = msgs.msg['0301'][0]
            results['response'] = msgs.msg['0301'][1] % (modId, api,
                strCmd, rcHeader[0], rcHeader[1])
        else:
            goodHeader = True
            # Convert the first word (overall rc from SMAPI) to an int
            # and set the SMUT overall rc based on this value.
            orcError = False
            try:
                results['overallRC'] = int(codes[0])
                if results['overallRC'] not in [8, 24, 25]:
                    orcError = True
            except ValueError:
                goodHeader = False
                orcError = True
            if orcError:
                results['overallRC'] = 25    # SMCLI Internal Error
                results = msgs.msg['0302'][0]
                results['response'] = msgs.msg['0302'][1] % (modId,
                    api, codes[0], strCmd, rcHeader[0], rcHeader[1])

            # Convert the second word to an int and save as rc.
            try:
                results['rc'] = int(codes[1])
            except ValueError:
                goodHeader = False
                results = msgs.msg['0303'][0]
                results['response'] = msgs.msg['0303'][1] % (modId,
                    api, codes[1], strCmd, rcHeader[0], rcHeader[1])

            # Convert the second word to an int and save it as either
            # the rs or errno.
            try:
                word3 = int(codes[2])
                if results['overallRC'] == 8:
                    results['rs'] = word3    # Must be an rs
                elif results['overallRC'] == 25:
                    results['errno'] = word3    # Must be the errno
                # We ignore word 3 for everyone else and default to 0.
            except ValueError:
                goodHeader = False
                results = msgs.msg['0304'][0]
                results['response'] = msgs.msg['0304'][1] % (modId,
                    api, codes[1], strCmd, rcHeader[0], rcHeader[1])

        results['strError'] = rcHeader[1].lstrip()

        if goodHeader:
            # Produce a message that provides the error info.
            results['response'] = msgs.msg['0300'][1] % (modId,
                    api, results['overallRC'], results['rc'],
                    results['rs'], results['errno'],
                    strCmd, smcliResp[1])

    except Exception as e:
        # All other exceptions.
        strCmd = " ".join(cmd + parms)
        results = msgs.msg['0305'][0]
        results['response'] = msgs.msg['0305'][1] % (modId, strCmd, 
            type(e).__name__, str(e))

    rh.printSysLog("Exit vmUtils.invokeSMCLI, rc: " +
        str(results['overallRC']))
    return results


def isLoggedOn(rh, userid):
    """
    Determine whether a virtual machine is logged on.

    Input:
       Request Handle:
          userid being queried

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - 0: if we got status.  Otherwise, it is the
                        error return code from the commands issued.
          rs        - Based on rc value.  For rc==0, rs is:
                      0: if we determined it is logged on.
                      1: if we determined it is logged off.
    """

    rh.printSysLog("Enter vmUtils.isLoggedOn, userid: " + userid)

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
             }

    cmd = ["/sbin/vmcp", "query", "user", userid]
    try:
        subprocess.check_output(
            cmd,
            close_fds=True,
            stderr=subprocess.STDOUT)
    except CalledProcessError as e:
        match = re.search('(^HCP\w\w\w045E|^HCP\w\w\w361E)', e.output)
        if match:
            # Not logged on
            results['rs'] = 1
        else:
            # Abnormal failure
            strCmd = ' '.join(cmd)
            rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                e.returncode, e.output))
            results = msgs.msg['0415'][0]
            results['rs'] = e.returncode

    rh.printSysLog("Exit vmUtils.isLoggedOn, overallRC: " +
        str(results['overallRC']) + " rc: " + str(results['rc']) +
        " rs: " + str(results['rs']))
    return results


def punch2reader(rh, userid, fileLoc, spoolClass):
    """
    Punch a file to a virtual reader of the specified virtual machine.

    Input:
       Request Handle - for general use and to hold the results
       userid         - userid of the virtual machine
       fileLoc        - File to send
       spoolClass     - Spool class

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter punch2reader.punchFile")
    results = {}

    # Setting rc to time out rc code as default and its changed during runtime
    results['rc'] = 9

    # Punch to the current user intially and then change the spool class.
    for secs in [1, 2, 3, 5, 10]:
        cmd = ["vmur", "punch", "-r", fileLoc]
        try:
            results['response'] = subprocess.check_output(cmd,
                                        close_fds=True,
                                        stderr=subprocess.STDOUT)
            results['rc'] = 0
            rh.updateResults(results)
            break
        except CalledProcessError as e:
            results['response'] = e.output
            # Check if we have concurrent instance of vmur active
            if results['response'].find("A concurrent instance of vmur" +
                " is already active") == -1:
                # Failure in VMUR punch update the rc
                results['rc'] = 7
                break
            else:
                # if concurrent vmur is active try after sometime
                    rh.printSysLog("Punch in use. Retrying after " +
                                        str(secs) + " seconds")
                    time.sleep(secs)

    if results['rc'] == 7:
        # Failure while issuing vmur command (For eg: invalid file given)
        msg = msgs.msg['0401'][1] % (modId, fileLoc, userid,
                                     results['response'])
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0401'][0])

    elif results['rc'] == 9:
        # Failure due to vmur timeout
        msg = msgs.msg['0406'][1] % (modId, fileLoc)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0406'][0])

    if rh.results['overallRC'] == 0:
        # On VMUR success change the class of the spool file
        spoolId = re.findall(r'\d+', str(results['response']))
        cmd = ["vmcp", "change", "rdr", str(spoolId[0]), "class", spoolClass]
        try:
            results['response'] = subprocess.check_output(cmd,
                                        close_fds=True,
                                        stderr=subprocess.STDOUT)
            rh.updateResults(results)
        except CalledProcessError as e:
            msg = msgs.msg['0404'][1] % (modId,
                                         spoolClass,
                                         e.output)
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0404'][0])
            # Class change failed
            # Delete the punched file from current userid
            cmd = ["vmcp", "purge", "rdr", spoolId[0]]
            try:
                results['response'] = subprocess.check_output(cmd,
                                            close_fds=True,
                                            stderr=subprocess.STDOUT)
            # We only need to issue the printLn.
            # Don't need to change return/reason code values
            except CalledProcessError as e:
                msg = msgs.msg['0401'][1] % (modId,
                                             fileLoc,
                                             userid, e.output)
                rh.printLn("ES", msg)

    if rh.results['overallRC'] == 0:
        # Transfer the file from current user to specified user
        cmd = ["vmcp", "transfer", "*", "rdr", str(spoolId[0]), "to",
                userid, "rdr"]
        try:
            results['response'] = subprocess.check_output(cmd,
                                        close_fds=True,
                                        stderr=subprocess.STDOUT)
            rh.updateResults(results)
        except CalledProcessError as e:
            msg = msgs.msg['0401'][1] % (modId,
                                         fileLoc,
                                         userid, e.output)
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0401'][0])
            # Transfer failed so delete the punched file from current userid
            cmd = ["vmcp", "purge", "rdr", spoolId[0]]
            try:
                results['response'] = subprocess.check_output(cmd,
                                            close_fds=True,
                                            stderr=subprocess.STDOUT)
                # We only need to issue the printLn.
                # Don't need to change return/reason code values
            except CalledProcessError as e:
                msg = msgs.msg['0401'][1] % (modId,
                                             fileLoc,
                                             userid, e.output)
                rh.printLn("ES", msg)

    rh.printSysLog("Exit vmUtils.punch2reader, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']


def waitForOSState(rh, userid, desiredState, maxQueries=90, sleepSecs=5):
    """
    Wait for the virtual OS to go into the indicated state.

    Input:
       Request Handle
       userid whose state is to be monitored
       Desired state, 'up' or 'down', case sensitive
       Maximum attempts to wait for desired state before giving up
       Sleep duration between waits

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from execCmdThruIUCV if overallRC = 0.
          rs        - RS returned from execCmdThruIUCV if overallRC = 0.
          errno     - Errno returned from execCmdThruIUCV if overallRC = 0.
          response  - Updated with an error message if wait times out.

    Note:

    """

    rh.printSysLog("Enter vmUtils.waitForOSState, userid: " + userid +
                           " state: " + desiredState +
                           " maxWait: " + str(maxQueries) +
                           " sleepSecs: " + str(sleepSecs))

    results = {}

    strCmd = "echo 'ping'"
    stateFnd = False

    for i in range(1, maxQueries + 1):
        results = execCmdThruIUCV(rh, rh.userid, strCmd)
        if results['overallRC'] == 0:
            if desiredState == 'up':
                stateFnd = True
                break
        else:
            if desiredState == 'down':
                stateFnd = True
                break

        if i < maxQueries:
            time.sleep(sleepSecs)

    if stateFnd is True:
        results = {
                'overallRC': 0,
                'rc': 0,
                'rs': 0,
            }
    else:
        maxWait = maxQueries * sleepSecs
        rh.printLn("ES", msgs.msg['0413'][1] % (modId, userid,
            desiredState, maxWait))
        results = msgs.msg['0413'][0]

    rh.printSysLog("Exit vmUtils.waitForOSState, rc: " +
        str(results['overallRC']))
    return results


def waitForVMState(rh, userid, desiredState, maxQueries=90, sleepSecs=5):
    """
    Wait for the virtual machine to go into the indicated state.

    Input:
       Request Handle
       userid whose state is to be monitored
       Desired state, 'on' or 'off', case sensitive
       Maximum attempts to wait for desired state before giving up
       Sleep duration between waits

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.

    Note:

    """

    rh.printSysLog("Enter vmUtils.waitForVMState, userid: " + userid +
                           " state: " + desiredState +
                           " maxWait: " + str(maxQueries) +
                           " sleepSecs: " + str(sleepSecs))

    results = {}

    cmd = ["/sbin/vmcp", "query", "user", userid]
    stateFnd = False

    for i in range(1, maxQueries + 1):
        try:
            out = subprocess.check_output(
                cmd,
                close_fds=True,
                stderr=subprocess.STDOUT)
            if desiredState == 'on':
                stateFnd = True
                break
        except CalledProcessError as e:
            match = re.search('(^HCP\w\w\w045E|^HCP\w\w\w361E)', e.output)
            if match:
                # Logged off
                if desiredState == 'off':
                    stateFnd = True
                    break
            else:
                # Abnormal failure
                out = e.output
                strCmd = ' '.join(cmd)
                rh.printLn("ES", msgs.msg['0415'][1] % (modId, strCmd,
                    e.returncode, out))
                results = msgs.msg['0415'][0]
                results['rs'] = e.returncode
                break
        if i < maxQueries:
            # Sleep a bit before looping.
            time.sleep(sleepSecs)

    if stateFnd is True:
        results = {
                'overallRC': 0,
                'rc': 0,
                'rs': 0,
            }
    else:
        maxWait = maxQueries * sleepSecs
        rh.printLn("ES", msgs.msg['0414'][1] % (modId, userid,
            desiredState, maxWait))
        results = msgs.msg['0414'][0]

    rh.printSysLog("Exit vmUtils.waitForVMState, rc: " +
        str(results['overallRC']))
    return results


def purgeReader(rh):
    """
    Purge reader of the specified userid.

    Input:
       Request Handle

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Updated with an error message.

    Note:

    """
    rh.printSysLog("Enter vmUtils.purgeRDR, userid: " + rh.userid)
    results = {'overallRC': 0,
               'rc': 0,
               'rs': 0,
               'response': []}
    # Temporarily use this SMAPI to purge the reader
    # We've asked for a new one to do this
    parms = ['-T', rh.userid, '-c', 'cmd=PURGE %s RDR ALL' % rh.userid]

    results = invokeSMCLI(rh, "xCAT_Commands_IUO", parms)

    if results['overallRC'] != 0:
        rh.printLn("ES", results['response'])
        rh.updateResults(results)

    rh.printSysLog("Exit vmUtils.purgeReader, rc: " +
                   str(results['overallRC']))
    return results
