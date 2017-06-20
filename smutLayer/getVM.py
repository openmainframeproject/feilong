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

import generalUtils
from generalUtils import parseCmdline
import re
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
                    'CONSOLEOUTPUT' : [ 'getConsole', lambda reqHandle: getConsole( reqHandle ) ],
                    'DIRECTORY'     : [ 'getDirectory', lambda reqHandle: getDirectory( reqHandle ) ],
                    'HELP'          : [ 'help', lambda reqHandle: help( reqHandle ) ],
                    'ISREACHABLE'   : [ 'checkIsReachable', lambda reqHandle: checkIsReachable( reqHandle ) ],
                    'STATUS'        : [ 'getStatus', lambda reqHandle: getStatus( reqHandle ) ],
                    'VERSION'       : [ 'getVersion', lambda reqHandle: getVersion( reqHandle ) ],
                 }

# List of positional operands based on subfunction.
# Each subfunction contains a list which has a dictionary with the following
# information for the positional operands:
#   - Human readable name of the operand,
#   - Property in the parms dictionary to hold the value,
#   - Is it required (True) or optional (False),
#   - Type of data ( 1: int, 2: string ).
posOpsList = {}

# List of additional operands/options supported by the various subfunctions.
# The dictionary followng the subfunction name uses the keyword from the command
# as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values ( 1: int, 2: string )
keyOpsList = {
            'CONSOLEOUTPUT' : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'DIRECTORY'     : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'HELP'          : {},
            'ISREACHABLE'   : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'STATUS'        : {
                                'all'     : [ 'allBasic', 0, 0 ],
                                'cpu'     : [ 'cpu', 0, 0 ],
                                'memory'  : [ 'memory', 0, 0 ],
                                'power'   : [ 'power', 0, 0 ],
                                'showparms'   : [ 'showParms', 0, 0 ],
                              },
            'VERSION'       : {},
          }



def checkIsReachable( reqHandle ):
    """ Check if a virtual machine is reachable.

    Input:
       Request Handle

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getVM.checkIsReachable, userid: " + reqHandle.userid )

    strCmd = "echo 'ping'"
    results = execCmdThruIUCV( reqHandle, reqHandle.userid, strCmd )

    if results['overallRC'] == 0 :
        reqHandle.printLn( "N", reqHandle.userid + ": reachable" )
        reachable = 1
    else :
        reqHandle.printLn( "N", reqHandle.userid + ": unreachable" )
        reachable = 0

    reqHandle.updateResults( { "rs": reachable } )
    reqHandle.printSysLog( "Exit getVM.checkIsReachable, rc: 0" )
    return 0


def doIt( reqHandle ):
    """ Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog( "Enter getVM.doIt" )

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] == True :
        reqHandle.printLn( "N", "Invocation parameters: " )
        reqHandle.printLn( "N", "  Routine: getVM." + str( subfuncHandler[reqHandle.subfunction][0] ) + "( reqHandle )" )
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

    reqHandle.printSysLog( "Exit getVM.doIt, rc: " + str( rc ) )
    return rc


def getConsole( reqHandle ):
    """ Get the virtual machine's console output.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    
    reqHandle.printSysLog( "Enter getVM.getConsole" )

    reqHandle.printLn( "N",  "This subfunction is not implemented yet." )

    # Transfer the console to this virtual machine.
    cmd = [ "smcli",
        "Image_Console_Get",
        "-T", reqHandle.userid,
      ]

    results = invokeSMCLI( reqHandle, cmd )
    if results['overallRC'] == 0 :
        reqHandle.printLn( "N", results['response'] )
    else :
        strCmd = ' '.join( cmd )
        reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str( results['overallRC'] ) )
        reqHandle.updateResults( results )
        rc = results['overallRC']

    if results['overallRC'] == 0 :
        reqHandle.printSysLog( "May need to add onlining of the reader" )
        reqHandle.printSysLog( "Need to add set the reader class" )
        reqHandle.printSysLog( "Find the files for the target user" )
        reqHandle.printSysLog( "Read each file and write it out with printLn" )

    reqHandle.printSysLog( "Exit getVM.getConsole, rc: " + str( results['overallRC'] ) )
    return 0


def getDirectory( reqHandle ):
    """ Get the virtual machine's directory statements.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    cmd = [ "smcli",
            "Image_Query_DM",
            "-T", reqHandle.userid,
          ]

    results = invokeSMCLI( reqHandle, cmd )
    if results['overallRC'] == 0 :
        results['response'] = re.sub( '\*DVHOPT.*', '', results['response'] )
        reqHandle.printLn( "N", results['response'] )
    else :
        strCmd = ' '.join( cmd )
        reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str( results['overallRC'] ) )
        reqHandle.updateResults( results )
        rc = results['overallRC']

    return results['overallRC']


def getStatus( reqHandle ):
    """ Get the basic status of a virtual machine.

    Input:
       Request Handle with the following properties:
          function    - 'CMDVM'
          subfunction - 'CMD'
          userid      - userid of the virtual machine

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog( "Enter getVM.getStatus, userid: " + reqHandle.userid )
    

    reqHandle.printLn( "N",  "This subfunction is not implemented yet." )

    reqHandle.printSysLog( "Exit getVM.getStatus, rc: " + str( rc ) )
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
    """ Produce help output specifically for GetVM functions.

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
    reqHandle.printSysLog( "Enter getVM.parseCmdline" )

    if reqHandle.totalParms >= 2 :
        reqHandle.userid = reqHandle.request[1].upper()
    else:
        reqHandle.printLn( "ES",  "Userid is missing" )
        reqHandle.updateResults( { 'overallRC': 1 } )
        reqHandle.printSysLog( "Exit getVM.parseCmdLine, rc: " + rc )
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


    reqHandle.printSysLog( "Exit getVM.parseCmdLine, rc: " + str( rc ) )
    return rc


def showInvLines( reqHandle ) :
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N",  "Usage:" )
    reqHandle.printLn( "N",  "  python " + reqHandle.cmdName + " GetVM <userid>" )
    reqHandle.printLn( "N",  "                    [ consoleoutput | directory ]" )
    reqHandle.printLn( "N",  "  python " + reqHandle.cmdName + " GetVM <userid>" )
    reqHandle.printLn( "N",  "                    status [ all | cpu | memory | power ]" )
    reqHandle.printLn( "N",  "  python " + reqHandle.cmdName + " GetVM help" )
    reqHandle.printLn( "N",  "  python " + reqHandle.cmdName + " GetVM version" )
    return


def showOperandLines( reqHandle ) :
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP' :
        reqHandle.printLn( "N",  "  For the GetVM function:" )
    else :
        reqHandle.printLn( "N",  "Sub-Functions(s):" )
    reqHandle.printLn( "N",  "      consoleoutput - Obtains the console log from the virtual machine." )
    reqHandle.printLn( "N",  "      directory     - Displays the user directory lines for the virtual machine." )
    reqHandle.printLn( "N",  "      help          - Displays this help information." )
    reqHandle.printLn( "N",  "      isreachable   - Determine whether the virtual OS in a virtual machine" )
    reqHandle.printLn( "N",  "                      is reachable" )
    reqHandle.printLn( "N",  "      status        - show the log on/off status of the virtual machine" )
    reqHandle.printLn( "N",  "      version       - show the version of the power function" )
    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N",  "Operand(s):" )
    reqHandle.printLn( "N",  "      <userid>      - Userid of the target virtual machine" )
    reqHandle.printLn( "N",  "      status [ all | cpu | memory | power ]" )
    reqHandle.printLn( "N",  "                    - Returns information machine related to the number" )
    reqHandle.printLn( "N",  "                      of virtual CPUs, memory size, power status or all of the" )
    reqHandle.printLn( "N",  "                      information." )

    return
