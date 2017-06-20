/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smSocket.h"
#include "vmapiVirtual.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Virtual_Network_Adapter_Create_Layout
#define OUTPUT_STRUCTURE_NAME vmApiVirtualNetworkAdapterCreateOutput

/**
 * Virtual_Network_Adapter_Create SMAPI interface
 */
int smVirtual_Network_Adapter_Create(
        struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier,
        char * imageDeviceNumber, char adapterType, int networkAdapterDevices,
        char * channelPathId, vmApiVirtualNetworkAdapterCreateOutput ** outData) {
    const char * const functionName = "Virtual_Network_Adapter_Create";
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
            imageDeviceNumber) + 1 /* adapterType */+ 4
            /* networking adapter devices */+ 4 + strlen(channelPathId);
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

    tempSize = strlen(targetIdentifier);  // Target identifier 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    tempSize = strlen(imageDeviceNumber);  // Image device number 1..4 chars
    PUT_INT(tempSize, cursor);
    memcpy(cursor, imageDeviceNumber, tempSize);
    cursor += tempSize;

    *cursor = adapterType;  // Adapter type byte
    cursor++;

    PUT_INT(networkAdapterDevices, cursor);  // Network adapter devices

    tempSize = strlen(channelPathId);  // Channel path id 0..2 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, channelPathId, tempSize);
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
