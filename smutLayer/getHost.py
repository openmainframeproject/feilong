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

import generalUtils
from generalUtils import parseCmdline
import sys
import subprocess
from subprocess import CalledProcessError, check_output
import time
import types
from vmUtils import execCmdThruIUCV, invokeSMCLI, waitForOSState, waitForVMState

version = "1.0.0"

# List of subfunction handlers.
# Each subfunction contains a list that has:
#   Readable name of the routine that handles the subfunction,
#   Code for the function call.
subfuncHandler = {
                    'DISKPOOLNAMES' : [ 'help', lambda reqHandle: getDiskPoolNames( reqHandle ) ],
                    'DISKPOOLSPACE' : [ 'help', lambda reqHandle: getDiskPoolSpace( reqHandle ) ],
                    'FCPDEVICES'    : [ 'help', lambda reqHandle: getFcpDevices( reqHandle ) ],
                    'GENERAL'       : [ 'help', lambda reqHandle: getGeneralInfo( reqHandle ) ],
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
                'DISKPOOLSPACE' : [
                                      [ 'Disk Pool Name', 'poolName', False, 2 ],
                                  ],
             }

# List of additional operands/options supported by the various subfunctions.
# The dictionary followng the subfunction name uses the keyword from the command
# as a key.  Each keyword has a dictionary that lists:
#   - the related parms item that stores the value,
#   - how many values follow the keyword, and
#   - the type of data for those values ( 1: int, 2: string )
keyOpsList = {
            'DISKPOOLNAMES' : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'DISKPOOLSPACE' : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'FCPDEVICES'    : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'GENERAL'       : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'HELP'          : { 'showparms'   : [ 'showParms', 0, 0 ], },
            'VERSION'       : { 'showparms'   : [ 'showParms', 0, 0 ], },
          }



def doIt( reqHandle ):
    """ Perform the requested function by invoking the subfunction handler.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getHost.doIt" )

    # Show the invocation parameters, if requested.
    if 'showParms' in reqHandle.parms and reqHandle.parms['showParms'] == True :
        reqHandle.printLn( "N", "Invocation parameters: " )
        reqHandle.printLn( "N", "  Routine: getHost." + str( subfuncHandler[reqHandle.subfunction][0] ) + "( reqHandle )" )
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

    reqHandle.printSysLog( "Exit getHost.doIt, rc: " + str( reqHandle.results['overallRC'] ) )
    return reqHandle.results['overallRC']


def getDiskPoolNames( reqHandle ):
    """ Obtain the list of disk pools known to the directory manager.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'DISKPOOLNAMES'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getHost.getDiskPoolNames" )

    cmd = [ "smcli",
        "Image_Volume_Space_Query_DM",
        "-q", "1",
        "-e", "3",
        "-T", "dummy" ]

    results = invokeSMCLI( reqHandle, cmd )
    if results['overallRC'] == 0 :
        for line in results['response'].splitlines() :
            poolName = line.partition(' ')[0]
            reqHandle.printLn( "N", poolName )
    else :
        strCmd = ' '.join( cmd )
        reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str( results['overallRC'] ) )
        reqHandle.updateResults( results )

    reqHandle.printSysLog( "Exit getHost.getDiskPoolNames, rc: " + str( reqHandle.results['overallRC'] ) )
    return reqHandle.results['overallRC']


def getDiskPoolSpace( reqHandle ):
    """ Obtain disk pool space information for all or a specific disk pool.

    Input:
       Request Handle with the following properties:
          function            - 'GETHOST'
          subfunction         - 'DISKPOOLSPACE'
          parms['poolName']   - Name of the disk pool. Optional, if not present then
                                information for all disk pools is obtained.

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getHost.getDiskPoolSpace" )

    results = { 'overallRC'     : 0, }

    if 'poolName' not in reqHandle.parms :
        poolNames = [ "*" ]
    else :
        if isinstance( reqHandle.parms['poolName'], types.ListType ) :
            poolNames = reqHandle.parms['poolName']
        else :
            poolNames = [ reqHandle.parms['poolName'] ]

    if results['overallRC'] == 0 :
        # Loop thru each pool getting total.  Do it for query 2 & 3
        totals = {}
        for qType in [ "2", "3" ] :
            cmd = [ "smcli",
                "Image_Volume_Space_Query_DM",
                "-q", qType,
                "-e", "3",
                "-T", "DUMMY",
                "-n", " ".join(poolNames) ]
    
            results = invokeSMCLI( reqHandle, cmd )
            if results['overallRC'] == 0 :
                for line in results['response'].splitlines() :
                    parts = line.split()
                    if len( parts ) == 9 :
                        poolName = parts[7]
                    else :
                        poolName = parts[4]
                    if poolName not in totals :
                        totals[poolName] = { "2" : 0., "3" : 0. }

                    if parts[1][:4] == "3390" :
                        totals[poolName][qType] += int( parts[3] ) * 737280
                    elif parts[1][:4] == "9336" :
                        totals[poolName][qType] += int( parts[3] ) * 512
            else :
                strCmd = ' '.join( cmd )
                reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                          "', rc: " + str( results['overallRC'] ) )
                reqHandle.updateResults( results )
                break

        if results['overallRC'] == 0 :
            if len( totals ) == 0 :
                reqHandle.printLn( "ES",  "No information was found for the specified pool(s): " + " ".join(poolNames) )
                reqHandle.updateResults( { 'overallRC' : 99, 'rc' : 8 } )
            else :
                # Produce a summary for each pool
                for poolName in sorted( totals ) :
                    total = totals[poolName]["2"] + totals[poolName]["3"]
                    reqHandle.printLn( "N", poolName + " Total: " + generalUtils.cvtToMag( reqHandle, total ) )
                    reqHandle.printLn( "N", poolName + " Used: " + generalUtils.cvtToMag( reqHandle, totals[poolName]["3"] ) )
                    reqHandle.printLn( "N", poolName + " Free: " + generalUtils.cvtToMag( reqHandle, totals[poolName]["2"] ) )

    reqHandle.printSysLog( "Exit getHost.getDiskPoolSpace, rc: " + str( reqHandle.results['overallRC'] ) )
    return reqHandle.results['overallRC']


def getFcpDevices( reqHandle ):
    """ Lists the FCP device channels that are active, free, or offline.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'FCPDEVICES'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getHost.getFcpDevices" )
    
    cmd = [ "smcli",
        "System_WWPN_Query",
        "-T", "bob" ]

    results = invokeSMCLI( reqHandle, cmd )
    if results['overallRC'] == 0 :
        reqHandle.printLn( "N", results['response'] )
    else :
        strCmd = ' '.join( cmd )
        reqHandle.printLn( "ES",  "Command failed: '" + strCmd + "', out: '" + results['response'] + 
                                  "', rc: " + str( results['overallRC'] ) )
        reqHandle.updateResults( results )

    reqHandle.printSysLog( "Exit getHost.getFcpDevices, rc: " + str( reqHandle.results['overallRC'] ) )
    return reqHandle.results['overallRC']


def getGeneralInfo( reqHandle ):
    """ Obtain general information about the host.

    Input:
       Request Handle with the following properties:
          function    - 'GETHOST'
          subfunction - 'GENERAL'

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """

    reqHandle.printSysLog( "Enter getHost.getGeneralInfo" )

    reqHandle.printLn( "N",  "This subfunction is not implemented yet." )

    reqHandle.printSysLog( "Exit getHost.getGeneralInfo, rc: " + str( 1111 ) )
    return 1111


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
    """ Produce help output specifically for GetHost functions.

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
    reqHandle.printSysLog( "Enter getHost.parseCmdline" )

    reqHandle.userid = ''

    if reqHandle.totalParms >= 2 :
        reqHandle.subfunction = reqHandle.request[1].upper()

    # Verify the subfunction is valid.
    if reqHandle.subfunction not in subfuncHandler :
        list = ', '.join( sorted( subfuncHandler.keys() ) )
        reqHandle.printLn( "ES", "Subfunction is missing.  " +
                "It should be one of the following: " + list + "." )
        reqHandle.updateResults( { 'overallRC': 4 } )
        rc = 4

    # Parse the rest of the command line.
    if rc == 0 :
        reqHandle.argPos = 2               # Begin Parsing at 3rd operand
        rc = generalUtils.parseCmdline( reqHandle, posOpsList, keyOpsList )

    reqHandle.printSysLog( "Exit getHost.parseCmdLine, rc: " + str( rc ) )
    return rc


def showInvLines( reqHandle ) :
    """ Produce help output related to command synopsis
    
    Input:
       Request Handle
    """

    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N",  "Usage:" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost <userid> diskpoolnames" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost <userid> diskpoolspace <poolName>" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost <userid> fcpdevices" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost <userid> general" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost help" )
    reqHandle.printLn( "N", "  python " + reqHandle.cmdName + " GetHost version" )
    return


def showOperandLines( reqHandle ) :
    """ Produce help output related to operands.
    
    Input:
       Request Handle
    """

    if reqHandle.function == 'HELP' :
        reqHandle.printLn( "N", "  For the GetHost function:" )
    else :
        reqHandle.printLn( "N",  "Sub-Functions(s):" )
    reqHandle.printLn( "N", "      diskpoolnames - Returns the names of the directory manager disk pools." )
    reqHandle.printLn( "N", "      diskpoolspace - Returns disk pool size information." )
    reqHandle.printLn( "N", "      fcpdevices    - Lists the FCP device channels that are active, free, or" )
    reqHandle.printLn( "N", "                      offline." )
    reqHandle.printLn( "N", "      general       - Returns the general information related to the z/VM" )
    reqHandle.printLn( "N", "                      hypervisor environment." )
    reqHandle.printLn( "N", "      help          - Returns this help information." )
    reqHandle.printLn( "N", "      version       - Show the version of this function" )
    if reqHandle.subfunction != '' :
        reqHandle.printLn( "N", "Operand(s):" )
    reqHandle.printLn( "N", "      <userid>      - Userid of the target virtual machine" )
    reqHandle.printLn( "N", "      <poolName>    - Name of the disk pool." )

    return
