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

#define PARSER_TABLE_NAME     Image_Disk_Copy_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageDiskCopyDmOutput

/**
 * Image_Disk_Copy_DM
 */
int smImage_Disk_Copy_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber,
        char * sourceImageName, char * sourceImageDiskNumber,
        char * imageDiskAllocationType, char * allocationAreaName,
        char * imageDiskMode, char * readPassword, char * writePassword,
        char * multiPassword, vmApiImageDiskCopyDmOutput ** outData) {
    const char * const functionName = "Image_Disk_Copy_DM";
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
            imageDiskNumber) + 4 + strlen(sourceImageName) + 4 + strlen(
            sourceImageDiskNumber) + 4 + strlen(imageDiskAllocationType) + 4
            + strlen(allocationAreaName) + 4 + strlen(imageDiskMode) + 4
            + strlen(readPassword) + 4 + strlen(writePassword) + 4 + strlen(
            multiPassword);
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

    tempSize = strlen(sourceImageName);  // Image name 1..8
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, sourceImageName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(sourceImageDiskNumber);  // Source image disk number 1..4
    PUT_INT(tempSize, cursor);
    memcpy(cursor, sourceImageDiskNumber, tempSize);
    cursor += tempSize;

    tempSize = strlen(imageDiskAllocationType);  // Image allocation type 0..10
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, imageDiskAllocationType, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(allocationAreaName);  // Allocation area name 0..10
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, allocationAreaName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(imageDiskMode);  // Image disk mode 0..5
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, imageDiskMode, tempSize);
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
