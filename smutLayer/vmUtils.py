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
        rh.printLn("ES", "Command failed with rc: " + str(results['rc']) +
            ", cmd: '" + strCmd + "', out: '" + results['response'])

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
    """

    rh.printSysLog("Enter vmUtils.execCmdThruIUCV, userid: " +
                           userid + " cmd: " + strCmd)
    iucvpath = '/opt/zhcp/bin/IUCV/'
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
        results['overallRC'] = 2
        results['response'] = e.output
        results['rc'] = e.returncode

        match = re.search('Return code (.+?),', results['response'])
        if match:
            try:
                results['rc'] = int(match.group(1))
            except ValueError:
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + ",  return code is not an " +
                    "integer: " + match.group(1))

        match = re.search('Reason code (.+?)\.', results['response'])
        if match:
            try:
                results['rs'] = int(match.group(1))
            except ValueError:
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + ",  reason code is not an " +
                    "integer: " + match.group(1))

        if results['rc'] == 1:
            results['response'] = ("Issued command was not authorized or a " +
                "generic Linux error occurred, error details: " +
                results['response'])
        elif results['rc'] == 2:
            results['response'] = ("Parameter to iucvclient error, error " +
                "details: " + results['response'])
        elif results['rc'] == 4:
            results['response'] = ("IUCV socket error, error details: " +
                results['response'])
        elif results['rc'] == 8:
            results['response'] = ("Command executed failed, error details: " +
                results['response'])
        elif results['rc'] == 16:
            results['response'] = ("File Transport failed, error details: " +
                results['response'])
        elif results['rc'] == 32:
            results['response'] = ("File Transport failed, error details: " +
                results['response'])
        else:
            results['response'] = ("Unrecognized error, error details: " +
                results['response'])

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


def invokeSMCLI(rh, cmd):
    """
    Invoke SMCLI and parse the results.

    Input:
       Request Handle
       SMCLI command to issue, specified as a list.

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Output of the SMCLI command.

    Note:
       - If the 'Return Code:' and 'Reason Code:' strings do not contain
         an integer value then an error message is generated.  The values
         in the dictionary for the incorrect values remain as 0.
    """

    rh.printSysLog("Enter vmUtils.invokeSMCLI, userid: " + rh.userid +
        " function: " + cmd[1])

    results = {
              'overallRC': 0,
              'rc': 0,
              'rs': 0,
              'errno': 0,
              'response': [],
              'strError': '',
             }

    smcliPath = '/opt/zhcp/bin/'
    cmd[0] = smcliPath + cmd[0]

    try:
        results['response'] = subprocess.check_output(cmd, close_fds=True)
        results['overallRC'] = 0

    except CalledProcessError as e:
        results['response'] = e.output
        results['overallRC'] = 1

        match = re.search('Return Code: (.+?)\n', results['response'])
        if match:
            try:
                results['rc'] = int(match.group(1))
            except ValueError:
                strCmd = " ".join(cmd)
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + ",  return code is not an " +
                    "integer: " + match.group(1))

        match = re.search('Reason Code: (.+?)\n', results['response'])
        if match:
            try:
                results['rs'] = int(match.group(1))
            except ValueError:
                strCmd = " ".join(cmd)
                rh.printLn("ES", "Command failed: '" + strCmd + "', out: '" +
                    results['response'] + ",  reason code is not an " +
                    "integer: " + match.group(1))

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
