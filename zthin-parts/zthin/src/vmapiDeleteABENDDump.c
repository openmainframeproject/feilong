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
#include "../include/smSocket.h"
#include "../include/vmapiDelete.h"
#include "../include/smapiTableParser.h"

#define PARSER_TABLE_NAME     Delete_ABEND_Dump_Layout
#define OUTPUT_STRUCTURE_NAME vmApiDeleteABENDDumpOutput

int smDelete_ABEND_Dump(struct _vmApiInternalContext* vmapiContextP, char * userid,
    int passwordLength, char * password, char * targetIdentifier, int keyValueCount,
    char ** keyValueArray, vmApiDeleteABENDDumpOutput ** outData) {
    const char * const functionName = "Delete_ABEND_Dump";
    tableParserParms parserParms;
    int tempSize;
    int keyValueSize = 0;
    char * cursor;
    int rc;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier);
    char * inputP = 0;
    int i;

    // This API only takes one string, so just use the last one if multiple
    i = keyValueCount - 1;
    inputSize += strlen(keyValueArray[i]) + 1;
    keyValueSize += strlen(keyValueArray[i]) + 1;

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }
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

    i = keyValueCount -1;  // Just add on last parm string
    tempSize = strlen(keyValueArray[i]) + 1;
    memcpy(cursor, keyValueArray[i], tempSize);
    cursor += tempSize;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
