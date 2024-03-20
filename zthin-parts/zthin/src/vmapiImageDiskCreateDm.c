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
#include "vmapiImage.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Image_Disk_Create_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageDiskCreateDmOutput

/**
 * Image_Disk_Create_DM SMAPI interface
 */
int smImage_Disk_Create_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber,
        char * imageDiskDeviceType, char * imageDiskAllocationType,
        char * allocationAreaNameOrVolser, char allocationUnitSize,
        int imageDiskSize, char * imageDiskMode, char imageDiskFormatting,
        char * imageDiskLabel, char * readPassword, char * writePassword,
        char * multiPassword, vmApiImageDiskCreateDmOutput ** outData) {
    const char * const functionName = "Image_Disk_Create_DM";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    char * stringCursor;  // Used for outData string area pointer
    int arrayCount;
    int totalStringSize;
    int rc;
    int sockDesc;
    int requestId;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4 + passwordLength + 4 +
            strlen(targetIdentifier) + 4 + strlen(imageDiskNumber) + 4 + strlen(imageDiskDeviceType) +
            4 + strlen(imageDiskAllocationType) + 4 + strlen(allocationAreaNameOrVolser) + 1 +
            4 + 4 + strlen(imageDiskMode) + 1 + 4 + strlen(imageDiskLabel) +
            4 + strlen(readPassword) + 4 + strlen(writePassword) + 4 + strlen(multiPassword);
    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];
    int i;

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

    tempSize = strlen(targetIdentifier);  // Target identifier 1..8 image name
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    tempSize = strlen(imageDiskNumber);  // Image disk number 1..4
    PUT_INT(tempSize, cursor);
    memcpy(cursor, imageDiskNumber, tempSize);
    cursor += tempSize;

    tempSize = strlen(imageDiskDeviceType);  // Image disk device type 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, imageDiskDeviceType, tempSize);
    cursor += tempSize;

    tempSize = strlen(imageDiskAllocationType);  // Image disk allocation type 1..10
    PUT_INT(tempSize, cursor);
    memcpy(cursor, imageDiskAllocationType, tempSize);
    cursor += tempSize;

    tempSize = strlen(allocationAreaNameOrVolser);  // Allocation area name or volser 0..8, 0..6 or 0..4
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, allocationAreaNameOrVolser, tempSize);
        cursor += tempSize;
    }

    *cursor = allocationUnitSize;  // Allocation Unit size
    cursor++;

    PUT_INT(imageDiskSize, cursor);  // Image disk size

    tempSize = strlen(imageDiskMode);  // Image disk mode 1..5
    PUT_INT(tempSize, cursor);
    memcpy(cursor, imageDiskMode, tempSize);
    cursor += tempSize;

    *cursor = imageDiskFormatting;  // Image disk formatting
    cursor++;

    tempSize = strlen(imageDiskLabel);  // Image disk label 0..6
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, imageDiskLabel, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(readPassword);  // Read password 0..8
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, readPassword, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(writePassword);  // Write password 0..8
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, writePassword, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(multiPassword);  // Multi password 0..8
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, multiPassword, tempSize);
        cursor += tempSize;
    }

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
