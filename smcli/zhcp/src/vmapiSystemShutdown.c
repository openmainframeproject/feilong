/**
 * IBM (C) Copyright 2013, 2016 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */

#include "vmapiSystem.h"
#include "smSocket.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>

#define PARSER_TABLE_NAME      System_Shutdown_Layout
#define OUTPUT_STRUCTURE_NAME  vmApiSystemShutdownOutput

int smSystem_Shutdown(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemShutdownOutput** outData) {
    int tempSize;
    int keyValueSize = 0;
    int i;
    int rc;
    char * cursor;

    const char * const functionName = "System_Shutdown";
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
    if (0 == (inputP = malloc(inputSize)))
        return MEMORY_ERROR;
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
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    for ( i = 0; i < keyValueCount; i++ ) {  // Keyword = value terminated strings
        tempSize = strlen(keyValueArray[i]) + 1;
        strcpy(cursor, keyValueArray[i]);
        cursor += tempSize;
    }

    // Trace the important SMAPI parameters for parser detail tracing
    TRACE_START(vmapiContextP, TRACEAREA_ZHCP_GENERAL, TRACELEVEL_PARAMETERS);
        sprintf(line, "System_Shutdown SMAPI parms, userid: %s,", targetIdentifier);
        for ( i = 0; i < keyValueCount; i++ ) {
            sprintf(line+strlen(line), " %s,", keyValueArray[i]);
        }
        sprintf(line+strlen(line), "\n");
    TRACE_END_DEBUG(vmapiContextP, line);

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
