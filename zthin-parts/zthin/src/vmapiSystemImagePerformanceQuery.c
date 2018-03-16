/**
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

#define PARSER_TABLE_NAME     System_Image_Performance_Query_Layout

int smSystem_Image_Performance_Query(struct _vmApiInternalContext* vmapiContextP,
        char* userid, int passwordLength, char* password, char* targetIdentifier,
        vmApiSystemImagePerformanceQueryOutput** outData) {
    const char* const functionName = "System_Image_Performance_Query";
    int tempSize;
    char* cursor;
    int rc = 0;
    int functionNameLength = strlen(functionName);
    int useridLength = strlen(userid);
    int targetIdentifierLength = strlen(targetIdentifier);
    int i;

    int inputSize = 4 + 4 + functionNameLength + 4 + useridLength + 4
            + passwordLength + 4 + targetIdentifierLength;
    char* inputP = 0;

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }
    cursor = inputP;
    PUT_INT(inputSize-4, cursor);

    // Function Name
    PUT_INT(functionNameLength, cursor);
    memcpy(cursor, functionName, functionNameLength);
    cursor += functionNameLength;

    // User ID
    PUT_INT(useridLength, cursor);
    if (useridLength) {
        memcpy(cursor, userid, useridLength);
        cursor += useridLength;
    }

    // Password
    PUT_INT(passwordLength, cursor);
    if (passwordLength) {
        memcpy(cursor, password, passwordLength);
        cursor += passwordLength;
    }

    // Target Identifiers
    PUT_INT(targetIdentifierLength, cursor);
    if (targetIdentifierLength) {
        memcpy(cursor, targetIdentifier, targetIdentifierLength);
        cursor += targetIdentifierLength;
    }

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // integer table
            TO_STRING(PARSER_TABLE_NAME),  // string name of the table
            (char * *) outData);

    return rc;
}
