# MakeVM functions for Systems Management Ultra Thin Layer
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
from tempfile import mkstemp
import os
import sys
import subprocess
from subprocess import CalledProcessError, check_output
import time
from vmUtils import execCmdThruIUCV, invokeSMCLI, waitForOSState, waitForVMState

version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
                    'DIRECTORY'     : [ 'createVM', lambda reqHandle: createVM( reqHandle ) ],
                    'HELP'          : [ 'help', lambda reqHandle: help( reqHandle ) ],
                    'VERSION'       : [ 'getVersion', lambda reqHandle: getVersion( reqHandle ) ],
                 }

# List of positional operands based on subfunction.
# Each subfunction contains a list which has a dictionary with the following
# information for the positional operands:
#   - Human readable name of the operand,
#   - Property in the parms dictionary to hold the value,
#   - Is it required (True) or optional (False),
#   - Type of data ( 1: int, 2: string ).
posOpsList = {
                'DIRECTORY'       : [
                                      [ 'password', 'pw', True, 2 ],
                                      [ 'Primary Memory Size (e.g. 2G)', 'priMemSize', True, 2 ],
                                      [ 'Privilege Class(es)', 'privClasses', True, 2 ],
                                  ],
             }

# List of additional operands/options supported by the various subfunctions.
# The dictionary followng the subfunction name uses the keyword from the command
# as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values ( 1: int, 2: string )
keyOpsList = {
            'DIRECTORY'     : { 
                                'cpus'        : [ 'cpuCnt', 1, 1 ],
                                'ipl'         : [ 'ipl', 1, 2 ],
                                'logonby'     : [ 'byUsers', 1, 2 ],
                                'maxMemSize'  : [ 'maxMemSize', 1, 2 ],
                                'profile'     : [ 'profName', 1, 2 ],
                                'showparms'   : [ 'showParms', 0, 0 ], },
            'HELP'          : {},
            'VERSION'       : {},
             }



def createVM( reqHandle ):
    """ Create a virtual machine in z/VM.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter makeVM.createVM" )

    dirLines = []
    dirLines.append( "USER " + reqHandle.userid + " " + reqHandle.parms['pw'] + " " +
                    reqHandle.parms['priMemSize'] + " " + reqHandle.parms['maxMemSize'] + " " +
                    reqHandle.parms['privClasses'] )
    if 'profName' in reqHandle.parms :
        dirLines.append( "INCLUDE " + reqHandle.parms['profName'] )
    dirLines.append( "CPU 00 BASE" )

    if 'cpuCnt' in reqHandle.parms :
        for i in range( 1, reqHandle.parms['cpuCnt'] ) :
            dirLines.append( "CPU %0.2X" % i )

    if 'ipl' in reqHandle.parms :
        dirLines.append( "IPL %0.4s" % reqHandle.parms['ipl'] )

    if 'byUsers' in reqHandle.parms :
        for user in reqHandle.parms['byUsers'] :
            dirLines.append( "LOGONBY " + user )

    # Construct the temporary file for the USER entry.
    fd, tempFile = mkstemp()
    os.write( fd, '\n'.join( dirLines ) + '\n' )
    os.close(fd)

    cmd = [ "smcli",
        "Image_Create_DM",
        "-T", reqHandle.userid,
        "-f", tempFile ]

    results = invokeSMCLI( reqHandle, cmd )
    if results['overallRC'] != 0 :
        strCmd = ' '.join( cmd )
        reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str( results['overallRC'] ) )
        reqHandle.updateResults( results )

    os.remove( tempFile )

    reqHandle.printSysLog( "Exit makeVM.createVM, rc: " + str( results['overallRC'] ) )
    return results['overallRC']


def doIt( reqHandle ):
    """ Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog( "Enter makeVM.doIt" )

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] == True :
        reqHandle.printLn( "N", "Invocation parameters: " )
        reqHandle.printLn( "N", "  Routine: makeVM." + str( subfuncHandler[reqHandle.subfunction][0] ) + "( reqHandle )" )
        reqHandle.printLn( "N", "  function: " + reqHandle.function )
        reqHandle.printLn( "N", "  userid: " + reqHandle.userid )
        reqHandle.printLn( "N", "  subfunction: " + reqHandle.subfunction )
        reqHandle.printLn( "N", "  parms{}: " )
        for key in reqHandle.parms :
            if key != 'showParms' :
                reqHandle.printLn( "N", "    " + key + ": " + str( reqHandle.parms[key] ) )
        reqHandle.printLn( "N", " " )

    # Call the subfunction handler
    subfuncHandler[reqHandle.subfunction][1]( reqHandle )

    reqHandle.printSysLog( "Exit makeVM.doIt, rc: " + str( rc ) )
    return rc


def getVersion( reqHandle ):
    """ Get the version of this function.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printLn( "N",  "Version: " + version )
    return 0


def help( reqHandle ):
    """ Produce help output specifically for MakeVM functions.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    showInvLines( reqHandle )
    showOperandLines( reqHandle )
    return 0


def parseCmdline( reqHandle ):
    """ Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog( "Enter makeVM.parseCmdline" )

    if reqHandle.totalParms >= 2 :
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn( "ES",  "Userid is missing" )
        reqHandle.updateResults( { 'overallRC': 1 } )
        reqHandle.printSysLog( "Exit makeVM.parseCmdLine, rc: " + rc )
        return 1

    if reqHandle.totalParms == 2 :
        reqHandle.subfunction = reqHandle.userid
        reqHandle.userid = ''

    if reqHandle.totalParms >= 3 :
        reqHandle.subfunction = reqHandle.request[2].upper()

    # Verify the subfunction is valid.
    if reqHandle.subfunction not in subfuncHandler :
        list = ', '.join( sorted( subfuncHandler.keys() ) )
        reqHandle.printLn( "ES", "Subfunction is missing.  " +
                "It should be one of the following: " + list + "." )
        reqHandle.updateResults( { 'overallRC': 4 } )
        rc = 4

    # Parse the rest of the command line.
    if rc == 0 :
        reqHandle.argPos = 3               # Begin Parsing at 4th operand
        rc = generalUtils.parseCmdline( reqHandle, posOpsList, keyOpsList )

    if 'byUsers' in reqHandle.parms :
        users = []
        for user in reqHandle.parms['byUsers'].split(' ') :
            users.append( user )
        reqHandle.parms['byUsers'] = []
        reqHandle.parms['byUsers'].extend( users )

    if 'maxMemSize' not in reqHandle.parms :
        reqHandle.parms['maxMemSize'] = reqHandle.parms['priMemSize']

    reqHandle.printSysLog( "Exit makeVM.parseCmdLine, rc: " + str( rc ) )
    return rc


def showInvLines( reqHandle ) :
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N", "Usage:" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " MakeVM <userid> directory" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " MakeVM help" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " MakeVM version" )
    return


def showOperandLines( reqHandle ) :
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP' :
        reqHandle.printLn( "N", "  For the MakeVM function:" )
    else :
        reqHandle.printLn( "N", "Sub-Functions(s):" )
    reqHandle.printLn( "N", "      directory     - Create a virtual machine in the z/VM user directory." )
    reqHandle.printLn( "N", "      help          - Displays this help information." )
    reqHandle.printLn( "N", "      version       - show the version of the power function" )
    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N", "Operand(s):" )
    reqHandle.printLn( "N", "      <userid>      - Userid of the target virtual machine" )

    return
