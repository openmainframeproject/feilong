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

#include "vmapiSystem.h"
#include "smSocket.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>

#define PARSER_TABLE_NAME      System_SCSI_Disk_Delete_Layout
#define OUTPUT_STRUCTURE_NAME  vmApiSystemSCSIDiskDeleteOutput

int smSystem_SCSI_Disk_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemSCSIDiskDeleteOutput** outData) {
    int tempSize;
    int keyValueSize = 0;
    int i;
    int rc;
    char * cursor;
    char* targetStart[3];

    const char * const functionName = "System_SCSI_Disk_Delete";
    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier);

    for (i = 0; i < keyValueCount; i++) {
        inputSize += strlen(keyValueArray[i]) + 1;
        keyValueSize += strlen(keyValueArray[i]) + 1;
    }

    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];

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

    tempSize = strlen(userid);  // UserId 1..8 or 0..8 chars
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
    targetStart[0] = targetIdentifier;  // Remember position relocateTarget for later tracing
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    for (i = 0; i < keyValueCount; i++) {  // Keyword=value terminated strings
        targetStart[i+1] = cursor;  // Remember position of parameter for later tracing
        tempSize = strlen(keyValueArray[i]) + 1;
        strcpy(cursor, keyValueArray[i]);
        cursor += tempSize;
    }

    // Trace the important SMAPI parameters for parser detail tracing
    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_PARAMETERS);
        sprintf(line, "System_SCSI_Disk_Delete SMAPI parms, userid: %s, %s, %ss\n", targetStart[0], targetStart[1], targetStart[2]);
    TRACE_END_DEBUG(vmapiContextP, line);

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}

