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

#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include "smSocket.h"
#include "vmapiEvent.h"
#include "smapiTableParser.h"

#define PARSER_TABLE_NAME     Event_Stream_Add_Layout
#define OUTPUT_STRUCTURE_NAME vmApiEventStreamAddOutput

/**
 * Event_Stream_Add SMAPI interface
 */
int smEvent_Stream_Add(struct _vmApiInternalContext* vmapiContextP, char * userid,
    int passwordLength, char * password, char * targetIdentifier, int eventId,
    int eventCharCount, char ** eventChars, int eventHexCharLength, char ** hexChars,
    vmApiEventStreamAddOutput ** outData) {

    const char * const functionName = "Event_Stream_Add";
    int tempSize;
    char * cursor;
    int i;
    int rc;

    int inputSize =                            // Input Parm field size based on:
                    4 +                        // Overall input length field
                    4 +                        // Length of function name
                    strlen(functionName) +     // Function name field
                    4 +                        // Length of userid
                    strlen(userid) +           // Userid field
                    4 +                        // Password length
                    passwordLength +           // Password field
                    4 +                        // Length of Target userid
                    strlen(targetIdentifier) + // Target userid field
                    4;                         // EventId field + data fields (added later)

    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];

    // Add data field size to the overall input length
    for (i = 0; i < eventCharCount; i++) {
        inputSize += strlen(eventChars[i]);
    }

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize)))
        return MEMORY_ERROR;
    cursor = inputP;
    PUT_INT(inputSize - 4, cursor);

    tempSize = strlen(functionName);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, functionName, tempSize);
    cursor += tempSize;

    tempSize = strlen(userid);  // Userid 1..8 or 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, userid, tempSize);
        cursor += tempSize;
    }

    tempSize = passwordLength;  // Password 1..200 or 0..200 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, password, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(targetIdentifier);  // Target identifier 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    tempSize = eventId;  // Event ID
    PUT_INT(tempSize, cursor);

    for (i = 0; i < eventCharCount; i++) {
        tempSize = strlen(eventChars[i]);
        memcpy(cursor, eventChars[i], tempSize);
        cursor += tempSize;
    }

    // Set the context flag that indicates a possible error buffer from SMAPI
    vmapiContextP->smapiErrorBufferPossible = ERROR_OUTPUT_BUFFER_POSSIBLE_WITH_LENGTH_FIELD;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
