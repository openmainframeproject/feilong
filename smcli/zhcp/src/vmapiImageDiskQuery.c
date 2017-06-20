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

#define PARSER_TABLE_NAME     Image_Disk_Query_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageDiskQueryOutput

/**
 * Authorization_List_Query SMAPI interface
 */
int smImage_Disk_Query(struct _vmApiInternalContext* vmapiContextP,
    char * userid, int passwordLength, char * password,
    char * targetIdentifier, int keyValueCount,
    char ** keyValueArray, vmApiImageDiskQueryOutput ** outData) {
    const char * const functionName = "Image_Disk_Query";
    tableParserParms parserParms;
    int tempSize;
    int keyValueSize = 0;
    char * cursor;
    int rc;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier);
    char * inputP = 0;
    int i;

    // This API only takes one string, so just use the last one if multiple
    i = keyValueCount -1;
    inputSize += strlen(keyValueArray[i]) + 1;
    keyValueSize += strlen(keyValueArray[i]) + 1;

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

    i = keyValueCount -1;  // Just add on last parm string
    tempSize = strlen(keyValueArray[i]) + 1;
    strcpy(cursor, keyValueArray[i]);
    cursor += tempSize;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
