# General Utilities for Systems Management Ultra Thin Layer
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

import math

fiveGigSize = (1024 * 5)


def cvtToBlocks(rh, diskSize):
    """
    Convert a disk storage value to a number of blocks.

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

    rh.printSysLog("Enter generalUtils.cvtToBlocks")
    blocks = 0
    results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0}

    blocks = diskSize.strip().upper()
    lastChar = blocks[-1]
    if lastChar == 'G' or lastChar == 'M':
        # Convert the bytes to blocks
        byteSize = blocks[:-1]
        if byteSize == '':
            rh.printLn("ES", "The size of the disk is not valid: " + lastChar)
            results['overallRC'] = 4
            results['rc'] = 4
            results['rs'] = 4
        else:
            try:
                if lastChar == 'M':
                    blocks = (float(byteSize) * 1024 * 1024) / 512
                elif lastChar == 'G':
                    blocks = (float(byteSize) * 1024 * 1024 * 1024) / 512
                blocks = str(int(math.ceil(blocks)))
            except:
                rh.printLn("ES", "Failed to convert " + diskSize +
                    " to a number of blocks")
                results['overallRC'] = 4
                results['rc'] = 4
                results['rs'] = 8
    elif blocks.strip('1234567890'):
        rh.printLn("ES", rh.parms['diskSize'] + " is not an integer size " +
            "of blocks.")
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 12

    rh.printSysLog("Exit generalUtils.cvtToBlocks, rc: " +
        str(results['overallRC']))
    return results, blocks


def cvtToCyl(rh, diskSize):
    """
    Convert a disk storage value to a number of cylinders.

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

    rh.printSysLog("Enter generalUtils.cvtToCyl")
    cyl = 0
    results = {'overallRC': 0, 'rc': 0, 'rs': 0, 'errno': 0}

    cyl = diskSize.strip().upper()
    lastChar = cyl[-1]
    if lastChar == 'G' or lastChar == 'M':
        # Convert the bytes to cylinders
        byteSize = cyl[:-1]
        if byteSize == '':
            rh.printLn("ES", "The size of the disk is not valid: " + lastChar)
            results['overallRC'] = 4
            results['rc'] = 4
            results['rs'] = 4
        else:
            try:
                if lastChar == 'M':
                    cyl = (float(byteSize) * 1024 * 1024) / 737280
                elif lastChar == 'G':
                    cyl = (float(byteSize) * 1024 * 1024 * 1024) / 737280
                cyl = str(int(math.ceil(cyl)))
            except:
                rh.printLn("ES", "Failed to convert " + diskSize +
                    " to a number of cylinders")
                results['overallRC'] = 4
                results['rc'] = 4
                results['rs'] = 8
    elif cyl.strip('1234567890'):
        rh.printLn("ES", rh.parms['diskSize'] + " is not an integer size " +
            "of cylinders.")
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 12

    rh.printSysLog("Exit generalUtils.cvtToCyl, rc: " +
        str(results['overallRC']))
    return results, cyl


def cvtToMag(rh, size):
    """
    Convert a size value to a number with a magnitude appended.

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

    rh.printSysLog("Enter generalUtils.cvtToMag")

    mSize = ''
    size = size / (1024 * 1024)

    if size > (1024 * 5):
        # Size is greater than 5G. Using "G" magnitude.
        size = size / 1024
        mSize = "%.1fG" % size
    else:
        # Size is less than or equal 5G. Using "M" magnitude.
        mSize = "%.1fM" % size

    rh.printSysLog("Exit generalUtils.cvtToMag, magSize: " + mSize)
    return mSize


def parseCmdline(rh, posOpsList, keyOpsList):
    """
    Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rc = 0
    rh.printSysLog("Enter generalUtils.parseCmdline")

    # Handle any positional operands on the line.
    if rc == 0 and rh.subfunction in posOpsList:
        ops = posOpsList[rh.subfunction]
        currOp = 0
        while rh.argPos < rh.totalParms and currOp < len(ops):
            key = ops[currOp][1]
            opType = ops[currOp][3]
            if opType == 1:
                try:
                    rh.parms[key] = int(rh.request[rh.argPos])
                except ValueError:
                    # keyword is not an integer
                    rh.printLn("ES", rh.function + " " + rh.subfunction +
                        " subfunction's operand at position " +
                        str(currOp + 1) + " (" + ops[currOp][0] +
                        ") is not an integer: " + rh.request[rh.argPos])
                    rh.updateResults({'overallRC': 4})
                    rc = 4
                    break
            else:
                rh.parms[key] = rh.request[rh.argPos]
            currOp += 1
            rh.argPos += 1

        if (rh.argPos >= rh.totalParms and currOp < len(ops) and
            ops[currOp][2] is True):
            # Check for missing required operands.
            rh.printLn("ES", rh.function + "'s " + rh.subfunction +
               " subfunction is missing positional operand number " +
               " (" + ops[currOp][0] + " operand).")
            rh.updateResults({'overallRC': 4})
            rc = 4

    # Handle any keyword operands on the line.
    if rc == 0 and rh.subfunction in keyOpsList:
        while rh.argPos < rh.totalParms:
            if rh.request[rh.argPos] in keyOpsList[rh.subfunction]:
                keyword = rh.request[rh.argPos]
                rh.argPos += 1
                ops = keyOpsList[rh.subfunction]
                if keyword in ops:
                    key = ops[keyword][0]
                    opCnt = ops[keyword][1]
                    opType = ops[keyword][2]
                    if opCnt == 0:
                        # Keyword has no additional value
                        rh.parms[key] = True
                    else:
                        # Keyword has values following it.
                        if opCnt < 0:
                            # Property is a list all of the rest of the parms.
                            opCnt = rh.totalParms - rh.argPos
                            if opCnt == 0:
                                # Need at least 1 operand value
                                opCnt = 1
                        if opCnt + rh.argPos > rh.totalParms:
                            # keyword is missing its related value operand
                            rh.printLn("ES", rh.function + " " +
                                rh.subfunction + " subfunction's " +
                                keyword + " operand is missing a value")
                            rh.updateResults({'overallRC': 4})
                            rc = 4
                            break

                        """
                        Add the expected value to the property.
                        Take into account if there are more than 1.
                        """
                        if opCnt > 1:
                            # Initialize the list.
                            rh.parms[key] = []
                        for i in range(0, opCnt):
                            if opType == 1:
                                # convert from string to int and save it.
                                try:
                                    if opCnt == 1:
                                        rh.parms[key] = (
                                            int(rh.request[rh.argPos]))
                                    else:
                                        rh.parms[key].append(int(
                                            rh.request[rh.argPos]))
                                except ValueError:
                                    # keyword is not an integer
                                    rh.printLn("ES", rh.function + " " +
                                        rh.subfunction + " subfunction's " +
                                        keyword + " operand value is not an " +
                                        "integer: " + rh.request[rh.argPos])
                                    rh.updateResults({'overallRC': 4})
                                    rc = 4
                                    break
                            else:
                                # Value is a string, save it.
                                if opCnt == 1:
                                    rh.parms[key] = rh.request[rh.argPos]
                                else:
                                    rh.parms[key].append(rh.request[rh.argPos])
                            rh.argPos += 1
                        if rc != 0:
                            # Upper loop had an error break from loops.
                            break
                else:
                    # keyword is not in the subfunction's keyword list
                    rh.printLn("ES", rh.function + "'s subfunction " +
                        rh.subfunction + " does not recognize: " +
                        rh.request[rh.argPos])
                    rh.updateResults({'overallRC': 4})
                    rc = 4
                    break
            else:
                # Subfunction does not support keywords
                rh.printLn("ES", rh.function + "'s subfunction " +
                    rh.subfunction + " does not recognize: " +
                    rh.request[rh.argPos])
                rh.updateResults({'overallRC': 4})
                rc = 4
                break

    rh.printSysLog("Exit generalUtils.parseCmdLine, rc: " + str(rc))
    return rc
