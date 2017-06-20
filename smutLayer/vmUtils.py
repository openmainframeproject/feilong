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

version = '1.0.0'         # Version of this script

import re
import subprocess
from subprocess import CalledProcessError, check_output
import time

def execCmdThruIUCV( reqHandle, userid, strCmd ) :
    """ Send a command to a virtual machine using IUCV.

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

    reqHandle.printSysLog( "Enter vmUtils.execCmdThruIUCV, userid: " +
                           userid + " cmd: " + strCmd )
    iucvpath = '/opt/zhcp/bin/IUCV/'
    results = {
              'overallRC'     : 0,
              'rc'            : 0,
              'rs'            : 0,
              'errno'         : 0,
              'response'      : [],
             }

    strCmd = ( iucvpath + "iucvclnt " + userid + " '" + strCmd + "' 2>&1"  )
    try :
        results['response'] = subprocess.check_output(
                strCmd,
                stderr=subprocess.STDOUT,
                close_fds=True,
                shell=True )

    except CalledProcessError as e :
        results['overallRC'] = 2
        results['response'] = e.output
        results['rc'] = e.returncode

        match = re.search( 'Return code (.+?),', results['response'] )
        if match :
            try :
                results['rc'] = int( match.group(1) )
            except ValueError :
                reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] +
                                  ",  return code is not an integer: " + match.group(1) )

        match = re.search( 'Reason code (.+?)\.', results['response'] )
        if match :
            try :
                results['rs'] = int( match.group(1) )
            except ValueError :
                reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] +
                                  ",  reason code is not an integer: " + match.group(1) )

        if results['rc'] == 1 :
            results['response'] = "Issued command was not authorized or a generic Linux error occurred, error details: " + out
        elif results['rc'] == 2 :
            results['response'] = "Parameter to iucvclient error, error details: " + results['response']
        elif results['rc'] == 4 :
            results['response'] = "IUCV socket error, error details: " + results['response']
        elif results['rc'] == 8 :
            results['response'] = "Command executed failed, error details: " + results['response']
        elif results['rc'] == 16 :
            results['response'] = "File Transport failed, error details: " + results['response']
        elif results['rc'] == 32 :
            results['response'] = "File Transport failed, error details: " + results['response']
        else :
            results['response'] = "Unrecognized error, error details: " + results['response']

    reqHandle.printSysLog( "Exit vmUtils.execCmdThruIUCV, rc: " + str( results['rc'] ) )
    return results


def invokeSMCLI( reqHandle, cmd ) :
    """ Invoke SMCLI and parse the results.

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

    reqHandle.printSysLog( "Enter vmUtils.invokeSMCLI, userid: " + reqHandle.userid + " function: " + cmd[1] )

    results = {
              'overallRC'   : 0,
              'rc'          : 0,
              'rs'          : 0,
              'errno'       : 0,
              'response'    : [],
              'strError'    : '',
             }

    smcliPath = '/opt/zhcp/bin/'
    cmd[0] = smcliPath + cmd[0]

    try :
        results['response'] = subprocess.check_output( cmd, close_fds=True )
        results['overallRC'] = 0

    except CalledProcessError as e :
        results['response'] = e.output
        results['overallRC'] = 1

        match = re.search( 'Return Code: (.+?)\n', results['response'] )
        if match :
            try :
                results['rc'] = int( match.group(1) )
            except ValueError :
                reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] +
                                  ",  return code is not an integer: " + match.group(1) )

        match = re.search( 'Reason Code: (.+?)\n', results['response'] )
        if match :
            try :
                results['rs'] = int( match.group(1) )
            except ValueError :
                reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] +
                                  ",  reason code is not an integer: " + match.group(1) )

    reqHandle.printSysLog( "Exit vmUtils.invokeSMCLI, rc: " + str( results['overallRC'] ) )
    return results


def waitForOSState( reqHandle, userid, desiredState, maxQueries=90, sleepSecs=5 ) :
    """ Wait for the virtual OS to go into the indicated state.

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

    rc = 0
    reqHandle.printSysLog( "Enter vmUtils.waitForOSState, userid: " + userid +
                           " state: " + desiredState +
                           " maxWait: " + str( maxQueries ) +
                           " sleepSecs: " + str( sleepSecs ) )

    results = {
          'overallRC'   : 0,
          'rc'          : 0,
          'rs'          : 0,
          'errno'       : 0,
          'response'    : [],
          'strError'    : '',
         }

    strCmd = "echo 'ping'"
    stateFnd = False

    for i in range( 1, maxQueries+1 ) :
        results = execCmdThruIUCV( reqHandle, reqHandle.userid, strCmd )
        if results['overallRC'] == 0 :
            if desiredState == 'up' :
                stateFnd = True
                break
        else :
            if desiredState == 'down' :
                stateFnd = True
                break

        if i < maxQueries :
            time.sleep( sleepSecs )

    if stateFnd == True :
        results = {
                'overallRC'   : 0,
                'rc'          : 0,
                'rs'          : 0,
                'errno'       : 0,
                'response'    : [],
                'strError'    : '',
            }
    else :
        maxWait = maxQueries * sleepSecs
        reqHandle.printLn( "ES",  "Userid '" + userid + "' did not enter the expected " +
                           "operating system state of '" + desiredState + "' in " +
                            str( maxWait ) + " seconds." )
        results['overallRC'] = 99

    reqHandle.printSysLog( "Exit vmUtils.waitForOSState, rc: " + str( results['overallRC'] ) )
    return results


def waitForVMState( reqHandle, userid, desiredState, maxQueries=90, sleepSecs=5 ) :
    """ Wait for the virtual machine to go into the indicated state.

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

    rc = 0
    reqHandle.printSysLog( "Enter vmUtils.waitForVMState, userid: " + userid +
                           " state: " + desiredState +
                           " maxWait: " + str( maxQueries ) +
                           " sleepSecs: " + str( sleepSecs ) )

    results = {
          'overallRC'   : 0,
          'rc'          : 0,
          'rs'          : 0,
          'errno'       : 0,
          'response'    : [],
          'strError'    : '',
         }

    cmd = ( "/sbin/vmcp q user " + userid + " 2>/dev/null | " +
            "sed 's/HCP\w\w\w045E.*/off/' | " +
            "sed 's/HCP\w\w\w361E.*/off/' | " +
            "sed 's/" + userid + ".*/on/'" )
    stateFnd = False

    for i in range( 1, maxQueries+1 ) :
        try :
            currState = subprocess.check_output(
                            cmd,
                            stderr=subprocess.STDOUT,
                            close_fds=True,
                            shell=True )

        except CalledProcessError as e :
            # The last SED would have to fail for the exception to be thrown.
            currState = e.output
            results['rc'] = e.returncode
            reqHandle.printLn( "ES",  "Command failed: '" + cmd + "', rc: " + str( rc ) )
            results['overallRC'] = 3
            break

        currState = currState.rstrip()
        if currState == desiredState :
            stateFnd = True
            break
        else :
            if i < maxQueries :
                time.sleep( sleepSecs )

    if stateFnd == True :
        results = {
                'overallRC'   : 0,
                'rc'          : 0,
                'rs'          : 0,
                'errno'       : 0,
                'response'    : [],
                'strError'    : '',
            }
    else :
        maxWait = maxQueries * sleepSecs
        reqHandle.printLn( "ES",  "Userid '" + userid + "' did not enter the expected " +
                           "virtual machine state of '" + desiredState + "' in " +
                            str( maxWait ) + " seconds." )
        results['overallRC'] = 99

    reqHandle.printSysLog( "Exit vmUtils.waitForVMState, rc: " + str( results['overallRC'] ) )
    return results