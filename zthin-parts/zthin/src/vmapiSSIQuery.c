/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017 IBM Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "vmapiSSI.h"
#include "smSocket.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>

#define PARSER_TABLE_NAME   SSI_Query_Layout

int smSSI_Query(struct _vmApiInternalContext* vmapiContextP, vmApiSSIQueryOutput** outData) {
    const char* const functionName = "SSI_Query";
    const char* const ALL = "ALL";
    int tempSize;
    int inputSize;
    int rc = 0;
    int functionNameLength = strlen(functionName);
    char* cursor;
    char* inputP = 0;

    inputSize = 4 +  // Space for input parm length
            4 +  // Function name length
            functionNameLength +  // Function name
            4 +  // UserId length
            0 +  // UserId
            4 +  // Password length
            0 +  // Password
            4 +  // Target identifier length
            strlen(ALL);   // Target identifier

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }

    // Move in size of input buffer
    cursor = inputP;
    PUT_INT(inputSize-4, cursor);

    // Fill in the SMAPI function name info
    PUT_INT(functionNameLength, cursor);
    memcpy(cursor, functionName, functionNameLength);
    cursor += functionNameLength;

    // Fill in the userid info - Not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the password info - Not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the target identifier info
    tempSize = strlen(ALL);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, ALL, tempSize);
    cursor += tempSize;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // integer table
            TO_STRING(PARSER_TABLE_NAME),  // string name of the table
            (char * *) outData);

    // If we got the data then set up the pointer for fast access
    return rc;
}
