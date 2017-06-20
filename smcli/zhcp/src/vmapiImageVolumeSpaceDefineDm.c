/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smSocket.h"
#include "vmapiImage.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Image_Volume_Space_Define_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageVolumeSpaceDefineDmOutput

/**
 * Image_Volume_Space_Define_DM SMAPI interface
 */
int smImage_Volume_Space_Define_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, char functionType, char * regionName,
        char * imageVolumeId, int startCyl, int regionSize, char * groupName,
        char deviceType, vmApiImageVolumeSpaceDefineDmOutput ** outData) {
    const char * const functionName = "Image_Volume_Space_Define_DM";
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
            + passwordLength + 4 + strlen(targetIdentifier) + 1
            /* Function type */ + 4 + strlen(regionName) + 4 + strlen(
            imageVolumeId) + 4 /* Start cyl */+ 4 /* Region size */+ 4 + strlen(
            groupName) + 1 /* DeviceType */;
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

    *cursor = functionType;  // Function type
    cursor++;

    tempSize = strlen(regionName);  // Region name 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, regionName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(imageVolumeId);  // Image volume id 0..6 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, imageVolumeId, tempSize);
        cursor += tempSize;
    }

    PUT_INT(startCyl, cursor);  // Start cylinder

    PUT_INT(regionSize, cursor);  // Region size

    tempSize = strlen(groupName);  // Group name 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, groupName, tempSize);
        cursor += tempSize;
    }

    *cursor = deviceType;
    cursor++;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
