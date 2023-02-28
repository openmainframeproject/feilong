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
#include "smSocket.h"
#include "vmapiVMRM.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     VMRM_Configuration_Update_Layout
#define OUTPUT_STRUCTURE_NAME vmApiVmrmConfigurationUpdateOutput

/**
 * VMRM_Configuration_Update SMAPI interface
 */
int smVMRM_Configuration_Update(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * configurationFileName,
        char * configurationFileType, char * configurationDirName,
        char syncheckOnly, int updateRecordCount, 
        vmApiUpdateRecord * updateRecordList,
        vmApiVmrmConfigurationUpdateOutput ** outData) {
    const char * const functionName = "VMRM_Configuration_Update";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    char * stringCursor;  // Used for outData string area pointer
    int arrayCount;
    int totalStringSize;
    int rc;
    int sockDesc;
    int requestId;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier) + 4 + strlen(
            configurationFileName) + 4 + strlen(configurationFileType) + 4
            + strlen(configurationDirName) + 1 + 4;
    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];
    int i;
    int updateFileLength;


    updateFileLength = 0;
    for (i = 0; i < updateRecordCount; i++) {
        updateFileLength += updateRecordList[i].updateRecordLength;
        inputSize += updateRecordList[i].updateRecordLength;
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

    tempSize = strlen(configurationFileName);  // Configuration file name 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, configurationFileName, tempSize);
    cursor += tempSize;

    tempSize = strlen(configurationFileType);  // Configuration file type 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, configurationFileType, tempSize);
    cursor += tempSize;

    tempSize = strlen(configurationDirName);  // Configuration SFS directory name 1..153
    PUT_INT(tempSize, cursor);
    memcpy(cursor, configurationDirName, tempSize);
    cursor += tempSize;

    *cursor = syncheckOnly;
    cursor++;

    // Add in the length of update record array 
    PUT_INT(updateFileLength, cursor);

    // Add in the update record array
    if (updateFileLength > 0) {
        for (i = 0; i < updateRecordCount; i++) {
            tempSize = updateRecordList[i].updateRecordLength;
            memcpy(cursor, updateRecordList[i].updateRecord, tempSize);
            cursor += tempSize;
        }
    }

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
