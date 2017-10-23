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

import msgs

fiveGigSize = (1024 * 5)
modId = 'GUT'


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
            # The size of the disk is not valid.
            msg = msgs.msg['0200'][1] % (modId, blocks)
            rh.printLn("ES", msg)
            results = msgs.msg['0200'][0]
        else:
            try:
                if lastChar == 'M':
                    blocks = (float(byteSize) * 1024 * 1024) / 512
                elif lastChar == 'G':
                    blocks = (float(byteSize) * 1024 * 1024 * 1024) / 512
                blocks = str(int(math.ceil(blocks)))
            except Exception:
                # Failed to convert to a number of blocks.
                msg = msgs.msg['0201'][1] % (modId, byteSize)
                rh.printLn("ES", msg)
                results = msgs.msg['0201'][0]
    elif blocks.strip('1234567890'):
        # Size is not an integer size of blocks.
        msg = msgs.msg['0202'][1] % (modId, blocks)
        rh.printLn("ES", msg)
        results = msgs.msg['0202'][0]

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
            # The size of the disk is not valid.
            msg = msgs.msg['0200'][1] % (modId, lastChar)
            rh.printLn("ES", msg)
            results = msgs.msg['0200'][0]
        else:
            try:
                if lastChar == 'M':
                    cyl = (float(byteSize) * 1024 * 1024) / 737280
                elif lastChar == 'G':
                    cyl = (float(byteSize) * 1024 * 1024 * 1024) / 737280
                cyl = str(int(math.ceil(cyl)))
            except Exception:
                # Failed to convert to a number of cylinders.
                msg = msgs.msg['0203'][1] % (modId, byteSize)
                rh.printLn("ES", msg)
                results = msgs.msg['0203'][0]
    elif cyl.strip('1234567890'):
        # Size is not an integer value.
        msg = msgs.msg['0204'][1] % (modId, cyl)
        rh.printLn("ES", msg)
        results = msgs.msg['0202'][0]

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


def getSizeFromPage(rh, page):
    """
    Convert a size value from page to a number with a magnitude appended.

    Input:
       Request Handle
       Size in page

    Output:
       Converted value with a magnitude
    """
    rh.printSysLog("Enter generalUtils.getSizeFromPage")

    bSize = float(page) * 4096
    mSize = cvtToMag(rh, bSize)

    rh.printSysLog("Exit generalUtils.getSizeFromPage, magSize: " + mSize)
    return mSize


def parseCmdline(rh, posOpsList, keyOpsList):
    """
    Parse the request command input.

    Input:
       Request Handle
       Positional Operands List.  This is a dictionary that contains
       an array for each subfunction.  The array contains a entry
       (itself an array) for each positional operand.
       That array contains:
          - Human readable name of the operand,
          - Property in the parms dictionary to hold the value,
          - Is it required (True) or optional (False),
          - Type of data (1: int, 2: string).
       Keyword Operands List.  This is a dictionary that contains
       an item for each subfunction.  The value for the subfunction is a
       dictionary that contains a key for each recognized operand.
       The value associated with the key is an array that contains
       the following:
          - the related ReqHandle.parms item that stores the value,
          - how many values follow the keyword, and
          - the type of data for those values (1: int, 2: string)

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter generalUtils.parseCmdline")

    # Handle any positional operands on the line.
    if rh.results['overallRC'] == 0 and rh.subfunction in posOpsList:
        ops = posOpsList[rh.subfunction]
        currOp = 0
        # While we have operands on the command line AND
        # we have more operands in the positional operand list.
        while rh.argPos < rh.totalParms and currOp < len(ops):
            key = ops[currOp][1]       # key for rh.parms[]
            opType = ops[currOp][3]    # data type
            if opType == 1:
                # Handle an integer data type
                try:
                    rh.parms[key] = int(rh.request[rh.argPos])
                except ValueError:
                    # keyword is not an integer
                    msg = msgs.msg['0001'][1] % (modId, rh.function,
                        rh.subfunction, (currOp + 1),
                        ops[currOp][0], rh.request[rh.argPos])
                    rh.printLn("ES", msg)
                    rh.updateResults(msgs.msg['0001'][0])
                    break
            else:
                rh.parms[key] = rh.request[rh.argPos]
            currOp += 1
            rh.argPos += 1

        if (rh.argPos >= rh.totalParms and currOp < len(ops) and
            ops[currOp][2] is True):
            # Check for missing required operands.
            msg = msgs.msg['0002'][1] % (modId, rh.function,
                rh.subfunction, ops[currOp][0], (currOp + 1))
            rh.printLn("ES", msg)
            rh.updateResults(msgs.msg['0002'][0])

    # Handle any keyword operands on the line.
    if rh.results['overallRC'] == 0 and rh.subfunction in keyOpsList:
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
                        storeIntoArray = False    # Assume single word
                        if opCnt < 0:
                            storeIntoArray = True
                            # Property is a list all of the rest of the parms.
                            opCnt = rh.totalParms - rh.argPos
                            if opCnt == 0:
                                # Need at least 1 operand value
                                opCnt = 1
                        elif opCnt > 1:
                            storeIntoArray = True
                        if opCnt + rh.argPos > rh.totalParms:
                            # keyword is missing its related value operand
                            msg = msgs.msg['0003'][1] % (modId, rh.function,
                                rh.subfunction, keyword)
                            rh.printLn("ES", msg)
                            rh.updateResults(msgs.msg['0003'][0])
                            break

                        """
                        Add the expected value to the property.
                        Take into account if there are more than 1.
                        """
                        if storeIntoArray:
                            # Initialize the list.
                            rh.parms[key] = []
                        for i in range(0, opCnt):
                            if opType == 1:
                                # convert from string to int and save it.
                                try:
                                    if not storeIntoArray:
                                        rh.parms[key] = (
                                            int(rh.request[rh.argPos]))
                                    else:
                                        rh.parms[key].append(int(
                                            rh.request[rh.argPos]))
                                except ValueError:
                                    # keyword is not an integer
                                    msg = (msgs.msg['0004'][1] %
                                        (modId, rh.function, rh.subfunction,
                                        keyword, rh.request[rh.argPos]))
                                    rh.printLn("ES", msg)
                                    rh.updateResults(msgs.msg['0004'][0])
                                    break
                            else:
                                # Value is a string, save it.
                                if not storeIntoArray:
                                    rh.parms[key] = rh.request[rh.argPos]
                                else:
                                    rh.parms[key].append(rh.request[rh.argPos])
                            rh.argPos += 1
                        if rh.results['overallRC'] != 0:
                            # Upper loop had an error break from loops.
                            break
                else:
                    # keyword is not in the subfunction's keyword list
                    msg = msgs.msg['0005'][1] % (modId, rh.function,
                        rh.subfunction, keyword)
                    rh.printLn("ES", msg)
                    rh.updateResults(msgs.msg['0005'][0])
                    break
            else:
                # Subfunction does not support keywords
                msg = (msgs.msg['0006'][1] % (modId, rh.function,
                    rh.subfunction, rh.request[rh.argPos]))
                rh.printLn("ES", msg)
                rh.updateResults(msgs.msg['0006'][0])
                break

    rh.printSysLog("Exit generalUtils.parseCmdLine, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']
