# Power functions for Systems Management Ultra Thin Layer
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

import sys
import subprocess
from subprocess import CalledProcessError, check_output

fiveGigSize = (1024 * 5)

def cvtToBlocks(reqHandle, diskSize):
    """ Convert a disk storage value to a number of blocks.

    Input:
       Request Handle
       Size of disk in bytes

    Output:
       Results structure:
          overallRC - Overall return code for the function:
                      0  - Everything went ok
                      4  - Input validation error
          rc        - Return code causing the return. Same as overallRC.
          rs        - Reason code causing the return.
          errno     - Errno value causing the return. Always zero.
       Converted value in blocks
    """

    reqHandle.printSysLog("Enter generalUtils.cvtToBlocks")
    blocks = 0
    results = { 'overallRC' : 0, 'rc' : 0, 'rs' : 0, 'errno' : 0 }

    blocks = diskSize.strip().upper()
    lastChar = blocks[-1]
    if lastChar == 'G' or lastChar == 'M' :
        # Convert the bytes to blocks
        byteSize = blocks[:-1]
        if byteSize == '' :
            reqHandle.printLn("ES", "The size of the disk is not valid: " + lastChar)
            results['overallRC'] = 4
            results['rc'] = 4
            results['rs'] = 4
        else :
            try:
                if lastChar == 'M' :
                    blocks = (float(byteSize) * 1024 * 1024) / 512
                elif lastChar == 'G' :
                    blocks = (float(byteSize) * 1024 * 1024 * 1024) / 512
                blocks = str(int(math.ceil(blocks)))
            except:
                reqHandle.printLn("ES", "Failed to convert " + diskSize + " to a number of blocks")
                results['overallRC'] = 4
                results['rc'] = 4
                results['rs'] = 8
    elif blocks.strip('1234567890') :
        reqHandle.printLn("ES", reqHandle.parms['diskSize'] + " is not an integer size of blocks.")
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 12

    reqHandle.printSysLog("Exit generalUtils.cvtToBlocks, rc: " + str(results['overallRC']))
    return results, blocks


def cvtToCyl(reqHandle, diskSize):
    """ Convert a disk storage value to a number of cylinders.

    Input:
       Request Handle
       Size of disk in bytes

    Output:
       Results structure:
          overallRC - Overall return code for the function:
                      0  - Everything went ok
                      4  - Input validation error
          rc        - Return code causing the return. Same as overallRC.
          rs        - Reason code causing the return.
          errno     - Errno value causing the return. Always zero.
       Converted value in cylinders
    """

    reqHandle.printSysLog("Enter generalUtils.cvtToCyl")
    cyl = 0
    results = { 'overallRC' : 0, 'rc' : 0, 'rs' : 0, 'errno' : 0 }

    cyl = diskSize.strip().upper()
    lastChar = cyl[-1]
    if lastChar == 'G' or lastChar == 'M' :
        # Convert the bytes to cylinders
        byteSize = cyl[:-1]
        if byteSize == '' :
            reqHandle.printLn("ES", "The size of the disk is not valid: " + lastChar)
            results['overallRC'] = 4
            results['rc'] = 4
            results['rs'] = 4
        else :
            try:
                if lastChar == 'M' :
                    cyl = (float(byteSize) * 1024 * 1024) / 737280
                elif lastChar == 'G' :
                    cyl = (float(byteSize) * 1024 * 1024 * 1024) / 737280
                cyl = str(int(math.ceil(cyl)))
            except:
                reqHandle.printLn("ES", "Failed to convert " + diskSize + " to a number of cylinders")
                results['overallRC'] = 4
                results['rc'] = 4
                results['rs'] = 8
    elif cyl.strip('1234567890') :
        reqHandle.printLn("ES", reqHandle.parms['diskSize'] + " is not an integer size of cylinders.")
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 12

    reqHandle.printSysLog("Exit generalUtils.cvtToCyl, rc: " + str(results['overallRC']))
    return results, cyl


def cvtToMag(reqHandle, size):
    """ Convert a size value to a number with a magnitude appended.

    Input:
       Request Handle
       Size bytes

    Output:
       Results structure:
          overallRC - Overall return code for the function:
                      0  - Everything went ok
                      4  - Input validation error
          rc        - Return code causing the return. Same as overallRC.
          rs        - Reason code causing the return.
          errno     - Errno value causing the return. Always zero.
       Converted value with a magnitude
    """

    reqHandle.printSysLog("Enter generalUtils.cvtToMag")

    mSize = ''
    size = size / (1024 * 1024)

    if size > (1024*5) :
        # Size is greater than 5G. Using "G" magnitude.
        size = size / 1024
        mSize = "%.1fG" % size
    else :
        # Size is less than or equal 5G. Using "M" magnitude.
        mSize = "%.1fM" % size

    reqHandle.printSysLog("Exit generalUtils.cvtToMag, magSize: " + mSize)
    return mSize


def parseCmdline(reqHandle, posOpsList, keyOpsList):
    """ Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    reqHandle.printSysLog("Enter generalUtils.parseCmdline")

    # Handle any positional operands on the line.
    if rc == 0 and reqHandle.subfunction in posOpsList :
        ops = posOpsList[reqHandle.subfunction]
        currOp = 0
        while reqHandle.argPos < reqHandle.totalParms and currOp < len(ops) :
            key = ops[currOp][1]
            opType = ops[currOp][3]
            if opType == 1 :
                try :
                    reqHandle.parms[key] = int (reqHandle.request[reqHandle.argPos])
                except ValueError :
                    # keyword is not an integer
                    reqHandle.printLn("ES", reqHandle.function + " " + reqHandle.subfunction +
                                       " subfunction's operand at position " + str(currOp+1) +
                                       " (" + ops[currOp][0] + 
                                       ") is not an integer: " + reqHandle.request[reqHandle.argPos])
                    reqHandle.updateResults({ 'overallRC': 4 })
                    rc = 4
                    break
            else :
                reqHandle.parms[key] = reqHandle.request[reqHandle.argPos]
            currOp += 1
            reqHandle.argPos += 1
        #print(str(reqHandle.argPos) + " " + str(reqHandle.totalParms) + " " + str(currOp) + " " + str(len(ops)))
        
        if (reqHandle.argPos >= reqHandle.totalParms and currOp < len(ops) and ops[currOp][2] == True) :
            # Check for missing required operands.
            reqHandle.printLn("ES", reqHandle.function + "'s " + reqHandle.subfunction +
               " subfunction is missing positional operand number " + 
               " (" + ops[currOp][0] + " operand).")
            reqHandle.updateResults({ 'overallRC': 4 })
            rc = 4

    # Handle any keyword operands on the line.
    if rc == 0 and reqHandle.subfunction in keyOpsList :
        while reqHandle.argPos < reqHandle.totalParms :
            if reqHandle.request[reqHandle.argPos] in keyOpsList[reqHandle.subfunction] :
                keyword = reqHandle.request[reqHandle.argPos]
                #print("Key: " + keyword)
                reqHandle.argPos += 1
                ops = keyOpsList[reqHandle.subfunction]
                if keyword in ops :
                    key = ops[keyword][0]
                    opCnt = ops[keyword][1]
                    opType = ops[keyword][2]
                    if opCnt == 0 :
                        # Keyword is just a keyword without an additional value
                        reqHandle.parms[key] = True
                    else :
                        # Keyword has values following it.
                        if opCnt < 0 :
                            # Property is a list made up of all of the rest of the parms.
                            opCnt = reqHandle.totalParms - reqHandle.argPos
                            if opCnt == 0 :
                                # Need at least 1 operand value
                                opCnt = 1
                        if opCnt + reqHandle.argPos > reqHandle.totalParms :
                            # keyword is missing its related value operand
                            reqHandle.printLn("ES", reqHandle.function + " " + reqHandle.subfunction + " subfunction's " +
                                               keyword + " operand is missing a value")
                            reqHandle.updateResults({ 'overallRC': 4 })
                            rc = 4
                            break

                        # Add the expected value to the property.  Take into account if there are more than 1.
                        if opCnt > 1 :
                            # Initialize the list.
                            reqHandle.parms[key] = []
                        for i in range(0, opCnt) :
                            #print "Value: " + reqHandle.request[reqHandle.argPos]
                            if opType == 1 :
                                # Value is an int, convert from string and save it.
                                try:
                                    if opCnt == 1 :
                                        reqHandle.parms[key] = int (reqHandle.request[reqHandle.argPos])
                                    else :
                                        reqHandle.parms[key].append(int (reqHandle.request[reqHandle.argPos]))
                                except ValueError :
                                    # keyword is not an integer
                                    reqHandle.printLn("ES", reqHandle.function + " " + reqHandle.subfunction +
                                                       " subfunction's " + keyword +
                                                       " operand value is not an integer: " + reqHandle.request[reqHandle.argPos])
                                    reqHandle.updateResults({ 'overallRC': 4 })
                                    rc = 4
                                    break
                            else :
                                # Value is a string, save it.
                                if opCnt == 1 :
                                    reqHandle.parms[key] = reqHandle.request[reqHandle.argPos]
                                else :
                                    reqHandle.parms[key].append(reqHandle.request[reqHandle.argPos])
                            reqHandle.argPos += 1
                        if rc != 0 :
                            # Upper loop had an error continue break from loops.
                            break


                    #print("key: " + key + " opCnt: " + str(opCnt) + " opType: " + str(opType))
    
                else :
                    # keyword is not in the subfunction's keyword list
                    reqHandle.printLn("ES", reqHandle.function + "'s subfunction " + reqHandle.subfunction +
                                       " does not recognize: " + reqHandle.request[reqHandle.argPos])
                    reqHandle.updateResults({ 'overallRC': 4 })
                    rc = 4
                    break
            else :
                # Subfunction does not support keywords
                reqHandle.printLn("ES", reqHandle.function + "'s subfunction " + reqHandle.subfunction +
                                   " does not recognize: " + reqHandle.request[reqHandle.argPos])
                reqHandle.updateResults({ 'overallRC': 4 })
                rc = 4
                break
            # Prepare to handle the next operand
            #reqHandle.argPos += 1

    reqHandle.printSysLog("Exit generalUtils.parseCmdLine, rc: " + str(rc))
    return rc
