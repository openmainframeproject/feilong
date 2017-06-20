/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */


#include "vmapiUnDocumented.h"
#include "smSocket.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>

#define PARSER_TABLE_NAME     Image_Performance_Query_Layout

int smImage_Performance_Query(struct _vmApiInternalContext* vmapiContextP,
        char* userid, int passwordLength, char* password,
        char* targetIdentifier, int guestCount, vmApiCStringInfo guests[],
        vmApiImagePerformanceQueryOutput** outData) {
    const char* const functionName = "Image_Performance_Query";
    int tempSize;
    char* cursor;
    int rc = 0;
    int functionNameLength = strlen(functionName);
    int useridLength = strlen(userid);
    int targetIdentifierLength = strlen(targetIdentifier);
    int i;

    // Target list's length is one byte (the null terminator) for each entry,
    // plus the sum of the lengths of the target strings themselves.
    int guestListSize = guestCount;
    for (i = 0; i < guestCount; i++) {
        guestListSize += strlen(guests[i].vmapiString);
    }

    int inputSize = 4 + 4 + functionNameLength + 4 + useridLength + 4
            + passwordLength + 4 + targetIdentifierLength + guestListSize;
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

    int guestNameLength;
    for (i = 0; i < guestCount; i++) {
        guestNameLength = strlen(guests[i].vmapiString) + 1;
        memcpy(cursor, guests[i].vmapiString, guestNameLength);
        cursor += guestNameLength;
    }

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // integer table
            TO_STRING(PARSER_TABLE_NAME),  // string name of the table
            (char * *) outData);

    return rc;
}
