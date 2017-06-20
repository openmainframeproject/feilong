# Request Handle for Systems Management Ultra Thin Layer
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

import changeVM
import cmdVM
import deleteVM
import getHost
import getVM
import logging
import logging.handlers
import makeVM
import migrateVM
import powerVM
import smapi
import sys
import shlex
import types
import vmUtils


class ReqHandle(object):
    """ Systems Management Ultra Thin Layer Request Handle.
    This class contains all information related to a specific request.
    All functions are passed this request handle.
    """


    funcHandler = {
                'CHANGEVM'  : [
                                lambda reqHandle: changeVM.showInvLines( reqHandle ),
                                lambda reqHandle: changeVM.showOperandLines( reqHandle ),
                                lambda reqHandle: changeVM.parseCmdline( reqHandle ),
                                lambda reqHandle: changeVM.doIt( reqHandle ),
                               ],
                'CMDVM'     : [
                                lambda reqHandle: cmdVM.showInvLines( reqHandle ),
                                lambda reqHandle: cmdVM.showOperandLines( reqHandle ),
                                lambda reqHandle: cmdVM.parseCmdline( reqHandle ),
                                lambda reqHandle: cmdVM.doIt( reqHandle ),
                               ],
                'DELETEVM'  : [
                                lambda reqHandle: deleteVM.showInvLines( reqHandle ),
                                lambda reqHandle: deleteVM.showOperandLines( reqHandle ),
                                lambda reqHandle: deleteVM.parseCmdline( reqHandle ),
                                lambda reqHandle: deleteVM.doIt( reqHandle ),
                               ],
                'GETHOST'    : [
                                lambda reqHandle: getHost.showInvLines( reqHandle ),
                                lambda reqHandle: getHost.showOperandLines( reqHandle ),
                                lambda reqHandle: getHost.parseCmdline( reqHandle ),
                                lambda reqHandle: getHost.doIt( reqHandle ),
                               ],
                'GETVM'      : [
                                lambda reqHandle: getVM.showInvLines( reqHandle ),
                                lambda reqHandle: getVM.showOperandLines( reqHandle ),
                                lambda reqHandle: getVM.parseCmdline( reqHandle ),
                                lambda reqHandle: getVM.doIt( reqHandle ),
                               ],
                'MAKEVM'     : [
                                lambda reqHandle: makeVM.showInvLines( reqHandle ),
                                lambda reqHandle: makeVM.showOperandLines( reqHandle ),
                                lambda reqHandle: makeVM.parseCmdline( reqHandle ),
                                lambda reqHandle: makeVM.doIt( reqHandle ),
                               ],
                'MIGRATEVM'  : [
                                lambda reqHandle: migrateVM.showInvLines( reqHandle ),
                                lambda reqHandle: migrateVM.showOperandLines( reqHandle ),
                                lambda reqHandle: migrateVM.parseCmdline( reqHandle ),
                                lambda reqHandle: migrateVM.doIt( reqHandle ),
                               ],
                'POWERVM'    : [
                                lambda reqHandle: powerVM.showInvLines( reqHandle ),
                                lambda reqHandle: powerVM.showOperandLines( reqHandle ),
                                lambda reqHandle: powerVM.parseCmdline( reqHandle ),
                                lambda reqHandle: powerVM.doIt( reqHandle ),
                               ],
                'SMAPI'      : [
                                lambda reqHandle: smapi.showInvLines( reqHandle ),
                                lambda reqHandle: smapi.showOperandLines( reqHandle ),
                                lambda reqHandle: smapi.parseCmdline( reqHandle ),
                                lambda reqHandle: smapi.doIt( reqHandle ),
                               ],
              }

    def __init__( self, **kwArgs ) :
        """ Constructor

        Input:
           captureLogs=<True|False>
                            Enables or disables log capture for all requests.
           cmdName=<cmdName>
                            Name of the command that is using ReqHandle.  This is only
                            used for the function help.  It defaults to "smutCmd.py".
           requestId=requestId
                            Optional request Id
           smut=<smutDaemon>
                            SMUT daemon, it it exists.
        """

        self.results = {
            'overallRC'    : 0,   # Overall return code for the function, e.g.
                                  #   0  - Everything went ok
                                  #   1  - Something in the SMCLI call failed
                                  #   2  - Something in the IUCVCLNT call failed
                                  #   3  - Something in a local vmcp call failed
                                  #   4  - Input validation error
                                  #   99 - Unexpected failure
            'rc'           : 0,   # Return code causing the return
            'rs'           : 0,   # Reason code causing the return
            'errno'        : 0,   # Errno value causing the return
            'strError'     : '',  # Error as a string value.
                                  #   Normally, this is the errno description.
            'response'     : [],  # Response strings
            'logEntries'   : [],  # Syslog entries related to this request
            }

        if 'smut' in kwArgs.keys() :
            self.daemon = kwArgs['smut']    # SMUT Daemon
            # Actual SysLog handling is done in SMUT.
        else :
            self.daemon = ''
            # Set up SysLog handling to be done by ReqHandle
            self.logger = logging.getLogger( __name__ )
            self.logger.setLevel( logging.DEBUG )
            self.handler = logging.handlers.SysLogHandler( address = '/dev/log' )
            self.formatter = logging.Formatter( '%(module)s.%(funcName)s: %(message)s' )
            self.handler.setFormatter( self.formatter )
            self.logger.addHandler( self.handler )
        
        if 'cmdName' in kwArgs.keys() :
            self.cmdName = kwArgs['cmdName']
        else :
            self.cmdName = 'smutCmd.py'

        if 'requestId' in kwArgs.keys() :
            self.requestId = kwArgs['requestId']   # String to identify the request in logs
        else :
            self.requestId = 'REQ_' + hex( id( self ) )[2:]
            # <todo>  Need to generate a default request Id

        self.function = ''            # Function being processed
        self.subfunction = ''         # Subfunction be processed (optional)
        self.userid = ''              # Target userid
        self.parms = {}               # Dictionary of additional parms
        self.argPos = 0               # Preparing to parse first command line argument

        # Capture & return Syslog entries
        if 'captureLogs' in kwArgs.keys() :
            self.captureLogs = kwArgs['captureLogs']
        else :
            self.captureLogs = False


    def driveFunction ( self ):
        """ Drive the function/subfunction call.
        
        Input:
           Self with request filled in.

        Output:
           Request Handle updated with the results.
           Overall return code - 0: successful, non-zero: error
        """

        if self.function == 'HELP' :
            # General help for all functions.
            self.printLn( "N", "" )
            self.printLn( "N", "Usage:" )
            self.printLn( "N", "  python " + self.cmdName + " --help" )
            for key in sorted( ReqHandle.funcHandler ) :
                ReqHandle.funcHandler[key][0]( self )
            self.printLn( "N", "" )
            self.printLn( "N", "Operand(s):" )
            for key in sorted( ReqHandle.funcHandler ) :
                ReqHandle.funcHandler[key][1]( self )
            self.printLn( "N", "" )
            self.updateResults( {}, reset=1 )
        elif self.function == 'VERSION' :
            # Version of ReqHandle.
            self.printLn( "N", "Version: " + version )
            self.updateResults( {}, reset=1 )
        else :
            # Some type of function/subfunction invocation.
            if self.function in self.funcHandler :
                # Invoke the functions doIt routine to route to the appropriate subfunction.
                self.funcHandler[self.function][3]( self )
            else :
                self.printLn( "ES", "Unrecognized function: " + self.function );
                self.updateResults( { 'overallRC': 4, 'rc': 200 } )

        return self.results


    def parseCmdline ( self, requestData ):
        """ Parse the request command string.
        
        Input:
           Self with request filled in.

        Output:
           Request Handle updated with the parsed information so that it is accessible
              via key/value pairs for later processing.
           Return code - 0: successful, non-zero: error
        """

        self.printSysLog( "Enter ReqHandle.parseCmdline" )

        # Save the request data based on the type of operand.
        if isinstance( requestData, types.ListType ) :
            self.requestString = ' '.join( requestData )  # Request as a string
            self.request = requestData                    # Request as a list
        elif isinstance( requestData, basestring ) :
            self.requestString = requestData              # Request as a string
            self.request = shlex.split( requestData )     # Request as a list
        else :
            self.printLn( "ES", "The request data is not in the supported type of " +
                               "either: list or string." )
            self.updateResults( { 'overallRC': 4, 'rc': '90' } )
            return self.results
        self.totalParms = len( self.request )   # Number of parms in the cmd

        #*************************************************
        # Handle the request, parse it or return an error.
        #*************************************************
        if self.totalParms == 0 :
            self.printLn( "E", "Too few command line arguments." )
            self.updateResults( { 'overallRC': 4, 'rc': 100 } )
        elif self.totalParms == 1 :
            self.function = self.request[0].upper()
            if self.function == 'HELP' or self.function == 'VERSION' :
                pass
            else :
                self.printLn( "E", "Function is not 'HELP' or 'Version'." )
                self.updateResults( { 'overallRC': 4, 'rc': 104 } )
        else :
            # Process based on the function operand.
            self.function = self.request[0].upper()
            if self.request[0] == 'HELP' or self.request[0] == 'VERSION' :
                pass
            else :
                # Handle the function related parms by calling the functions parser.
                if self.function in ReqHandle.funcHandler :
                    self.funcHandler[self.function][2]( self )
                else :
                    self.printLn( "ES", "Unrecognized function: " + self.function );
                    self.updateResults( { 'overallRC': 4, 'rc': 200 } )

        self.printSysLog( "Exit ReqHandle.parseCmdline, rc: " + str( self.results['overallRC'] ) )
        return self.results


    def printLn( self, respType, respString ) :
        """ Add one or lines of output to the response list.

        Input:
           Response type: One or more characters indicate type of response.
              E - Error message
              N - Normal message
              S - Output should be logged
        """

        header = ''
        if 'E' in respType :
            respString = '(Error) ' + respString
        if 'S' in respType :
            self.printSysLog( respString )
        self.results['response'] = self.results['response'] + respString.splitlines()
        return


    def printSysLog( self, logString ) :
        """ Log one or more lines.  Optionally, add the lines to logEntries list.

        Input:
           Strings to be logged.
        """

        if self.daemon == '' :
            self.logger.debug( self.requestId + ": " + logString )
        else :
            self.daemon.logger.debug( self.requestId + ": " + logString )

        if self.captureLogs == True :
            self.results['logEntries'].append( self.requestId + ": " + logString )
        return


    def updateResults( self, newResults, **kwArgs ) :
        """ Update the results related to this request excluding the 'response'
        and 'logEntries' values.  We specifically update (if present): overallRC,
        rc, rs, errno.

        Input:
           Dictionary containing the results to be updated or an empty dictionary the
              reset keyword was specified.
           Reset keyword:
              0 - Not a reset.  This is the default is reset keyword was not specified.
              1 - Reset failure related items in the result dictionary.
                  This exclude responses and log entries. 
              2 - Reset all result items in the result dictionary.

        Output:
           Request handle is updated with the results.
        """

        if 'reset' in kwArgs.keys() :
            reset = kwArgs['reset']
        else :
            reset = 0

        if reset == 0 :
            # Not a reset.  Set the keys from the provided dictionary.
            for key in newResults.keys() :
                if key == 'response' or key == 'logEntries' :
                    continue
                self.results[key] = newResults[key]
        elif reset == 1 :
            # Reset all failure related items.
            self.results['overallRC'] = 0
            self.results['rc'] = 0
            self.results['rs'] = 0
            self.results['errno'] = 0
            self.results['strError'] = ''
        elif reset == 2 :
            # Reset all results information including any responses and log entries.
            self.results['overallRC'] = 0
            self.results['rc'] = 0
            self.results['rs'] = 0
            self.results['errno'] = 0
            self.results['strError'] = ''
            self.results['logEntries'] = ''
            self.results['response'] = ''

        return