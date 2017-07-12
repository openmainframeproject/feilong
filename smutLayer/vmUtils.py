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
          option ('-e': enable, 'd': disable)

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - 0: if we got status.  Otherwise, it is the
                        error return code from the commands issued.
          rs        - Based on rc value.  For rc==0, rs is:
                      0: if we determined it is logged on.
                      1: if we determined it is logged off.
    """

    rh.printSysLog("Enter vmUtils.disableEnableDisk, userid: " + userid +
        " addr: " + vaddr + " option: " + option)

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
             }

    """
    Can't guarantee the success of online/offline disk, need to wait
    Until it's done because we may detach the disk after -d option
    or use the disk after the -e option
    """
    cmdDone = False
    for secs in [1, 2, 3, 5, 8, 15, 22, 34, 60, 60, 60, 60, 60, 90, 120, 0]:
        strCmd = "/sbin/chccwdev " + option + " " + vaddr
        results = execCmdThruIUCV(rh, userid, strCmd)
        if results['overallRC'] == 0:
            cmdDone = True
            break
        if secs != 0:
            time.sleep(secs)

    if not cmdDone:
        # Pass along the results from the last failed command.
        rh.printLn("ES", results['response'])
        rh.updateResults(results)

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
        cmd = ["./linkdiskandbringonline", rh.userid, vaddr, mode]
        out = subprocess.check_output(cmd, close_fds=True)
        diskAccessed = True
    except CalledProcessError as e:
        out = e.output
        results['overallRC'] = 99
        results['rc'] = e.returncode
        strCmd = ' '.join(cmd)
        rh.printLn("ES", "Command failed with rc: " +
            str(e.returncode) + " response, cmd: '" + strCmd +
            "', out: '" + out)
        rh.updateResults(results)

    if results['overallRC'] == 0:
        """
        sample output:
        linkdiskandbringonline maint start time: 2017-03-03-16:20:48.011
        Success: Userid maint vdev 193 linked at ad35 device name dasdh
        linkdiskandbringonline exit time: 2017-03-03-16:20:52.150
        """
        match = re.search('Success:(.+?)', out)
        if match:
            try:
                parts = out.split()
                device = "/dev/" + parts[10]
            except ValueError:
                strCmd = ' '.join(cmd)
                results['overallRC'] = 99
                results['rc'] = e.returncode
                rh.printLn("ES", "Command did not return the expected " +
                    "response, cmd: '" + strCmd + "', out: '" +
                    results['response'])
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
            out = e.output
            results['overallRC'] = 99
            results['rc'] = e.returncode
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed with rc: " +
                str(e.returncode) + " response, cmd: '" + strCmd +
                "', out: '" + out)
            rh.updateResults(results)

    if results['overallRC'] == 0:
        # Prepare the partition with fdasd
        try:
            cmd = ["/sbin/fdasd", "-a", device]
            out = subprocess.check_output(cmd, close_fds=True)
        except CalledProcessError as e:
            out = e.output
            results['overallRC'] = 99
            results['rc'] = e.returncode
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed with rc: " +
                str(e.returncode) + " response, cmd: '" + strCmd +
                "', out: '" + out)
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
                out = subprocess.check_output(cmd, close_fds=True)
                rh.printLn("N", "File system: " + fileSystem +
                    " is installed.")
            except CalledProcessError as e:
                out = e.output
                results['overallRC'] = 99
                results['rc'] = e.returncode
                strCmd = ' '.join(cmd)
                rh.printLn("ES", "Command failed with rc: " +
                    str(e.returncode) + " response, cmd: '" + strCmd +
                    "', out: '" + out)
                rh.updateResults(results)
        else:
            rh.printLn("N", "File system type is swap. No need to install " +
                "a filesystem.")

    if diskAccessed:
        # Give up the disk.
        try:
            cmd = ["./offlinediskanddetach", rh.userid, vaddr]
            out = subprocess.check_output(cmd, close_fds=True)
        except CalledProcessError as e:
            out = e.output
            results['overallRC'] = 99
            results['rc'] = e.returncode
            strCmd = ' '.join(cmd)
            rh.printLn("ES", "Command failed with rc: " +
                str(e.returncode) + " response, cmd: '" + strCmd +
                "', out: '" + out)
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
            # Convert the overall rc from SMAPI to an int and pass
            # it along in the errno field.
            try:
                results['errno'] = int(codes[0])
            except ValueError:
                goodHeader = False
                results = msgs.msg['0304'][0]
                results['response'] = msgs.msg['0304'][1] % (modId,
                    api, codes[2], strCmd, rcHeader[0], rcHeader[1])

            # Convert the return code to an int.
            try:
                results['rc'] = int(codes[1])
            except ValueError:
                goodHeader = False
                results = msgs.msg['0302'][0]
                results['response'] = msgs.msg['0302'][1] % (modId,
                    api, codes[0], strCmd, rcHeader[0], rcHeader[1])

            # Convert the reason code to an int.
            try:
                results['rs'] = int(codes[2])
            except ValueError:
                goodHeader = False
                results = msgs.msg['0303'][0]
                results['response'] = msgs.msg['0303'][1] % (modId,
                    api, codes[1], strCmd, rcHeader[0], rcHeader[1])

        results['strError'] = rcHeader[1].lstrip()

        if goodHeader:
            results['overallRC'] = 1    # Set the overall RC
            # Produce a message that provides the error info.
            results['response'] = msgs.msg['0300'][1] % (modId,
                    api, results['rc'], results['rs'],
                    results['errno'], strCmd, smcliResp[1])

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
            rh.printLn("ES", "Command failed: '" + strCmd + "', rc: " +
                str(e.returncode) + " out: " + e.output)
            results['overallRC'] = 3
            results['rc'] = e.returncode

    rh.printSysLog("Exit vmUtils.isLoggedOn, overallRC: " +
        str(results['overallRC']) + " rc: " + str(results['rc']) +
        " rs: " + str(results['rs']))
    return results


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

    results = {
          'overallRC': 0,
          'rc': 0,
          'rs': 0,
          'errno': 0,
          'response': [],
          'strError': '',
         }

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
                'errno': 0,
                'response': [],
                'strError': '',
            }
    else:
        maxWait = maxQueries * sleepSecs
        rh.printLn("ES", "Userid '" + userid + "' did not enter the " +
            "expected operating system state of '" + desiredState + "' in " +
            str(maxWait) + " seconds.")
        results['overallRC'] = 99

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
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Updated with an error message if wait times out.

    Note:

    """

    rh.printSysLog("Enter vmUtils.waitForVMState, userid: " + userid +
                           " state: " + desiredState +
                           " maxWait: " + str(maxQueries) +
                           " sleepSecs: " + str(sleepSecs))

    results = {
          'overallRC': 0,
          'rc': 0,
          'rs': 0,
          'errno': 0,
          'response': [],
          'strError': '',
         }

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
                rh.printLn("ES", "Command failed: '" + strCmd + "', rc: " +
                    str(e.returncode) + " out: " + out)
                results['overallRC'] = 3
                results['rc'] = e.returncode
                break
        if i < maxQueries:
            # Sleep a bit before looping.
            time.sleep(sleepSecs)

    if stateFnd is True:
        results = {
                'overallRC': 0,
                'rc': 0,
                'rs': 0,
                'errno': 0,
                'response': [],
                'strError': '',
            }
    else:
        maxWait = maxQueries * sleepSecs
        rh.printLn("ES", "Userid '" + userid + "' did not enter the " +
            "expected virtual machine state of '" + desiredState + "' in " +
            str(maxWait) + " seconds.")
        results['overallRC'] = 99

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
          response  - Updated with an error message if wait times out.

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

    if results['overallRC'] == 0:
        rh.printLn("N", "Purged reader for " +
                   rh.userid + ".")
    else:
        rh.printLn("ES", results['response'])
        rh.updateResults(results)

    rh.printSysLog("Exit vmUtils.purgeReader, rc: " +
                   str(results['overallRC']))
    return results


def punch2Reader(rh, userid, file, spoolClass):
    """
    Punch a file to the Reader.

    Input:
       Request Handle
       userid of the VM reader to be punched
       file to be punched

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from commands issued if overallRC = 0.
          rs        - RS returned from commands issued if overallRC = 0.
          errno     - Errno returned from commands issued if overallRC = 0.
          response  - Updated with an error message if wait times out.

    Note:

    """
    rh.printSysLog("Enter vmUtils.punch2Reader, userid: " + rh.userid)
    results = {'overallRC': 0,
               'rc': 0,
               'rs': 0,
               'response': []}
    spoolId = 0
    # Setting rc to time out rc code as default and its changed during runtime
    results['rc'] = 9
    # Punch to the current user intially and then change the spool class.
    for secs in [1, 2, 3, 5, 10]:
        cmd = ["vmur", "punch", "-r", file]
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
        msg = msgs.msg['0401'][1] % (modId,
                                        file,
                                        userid, results['response'])
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0401'][0])

    if results['rc'] == 9:
        # Failure due to vmur timeout
        msg = msgs.msg['0406'][1] % (modId,
                                        file)
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
                # Do not update the results here,its already error handling
            except CalledProcessError as e:
                msg = msgs.msg['0401'][1] % (modId,
                                             file,
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
                                         file,
                                         userid, e.output)
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0401'][0])
            # Transfer failed so delete the punched file from current userid
            cmd = ["vmcp", "purge", "rdr", spoolId[0]]
            try:
                results['response'] = subprocess.check_output(cmd,
                                            close_fds=True,
                                            stderr=subprocess.STDOUT)
                # Do not update the results here,its already error handling
            except CalledProcessError as e:
                msg = msgs.msg['0401'][1] % (modId,
                                             file,
                                             userid, e.output)
                rh.printLn("ES", msg)

    rh.printSysLog("Exit vmUtils.punch2Reader, rc: " +
                   str(rh.results['overallRC']))
    return rh.results
