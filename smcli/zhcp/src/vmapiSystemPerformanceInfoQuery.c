/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */


#include "vmapiUnDocumented.h"
#include "smSocket.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>

#define PARSER_TABLE_NAME     System_Performance_Info_Query_Layout

int smSystem_Performance_Info_Query(struct _vmApiInternalContext* vmapiContextP, char* userid, int passwordLength,
        char* password, char* targetIdentifier, vmApiSystemPerformanceInfoQueryOutput** outData) {
    const char* const functionName = "System_Performance_Info_Query";
    int tempSize;
    char* cursor;
    int rc = 0;
    int functionNameLength = strlen(functionName);
    int useridLength = strlen(userid);
    int targetIdentifierLength = strlen(targetIdentifier);

    int inputSize = 4 + 4 + functionNameLength + 4 + useridLength + 4
        + passwordLength + 4 + targetIdentifierLength;

    char* inputP = 0;
    int i;

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

    // Target Identifier
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
