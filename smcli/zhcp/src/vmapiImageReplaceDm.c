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

#define PARSER_TABLE_NAME     Image_Replace_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageReplaceDmOutput

/**
 * Image_Replace_DM SMAPI interface
 */
int smImage_Replace_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, int imageRecordArrayCount,
        vmApiImageRecord * imageRecordList,
        vmApiImageReplaceDmOutput ** outData) {
    const char * const functionName = "Image_Replace_DM";
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
            + passwordLength + 4 + strlen(targetIdentifier) + 4 /* imageRecordArrayLength */; /* Need to add in actual array data size */
    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];
    int i, totalArraySize;

    totalArraySize = 0;
    for (i = 0; i < imageRecordArrayCount; i++) {
        totalArraySize += imageRecordList[i].imageRecordLength + 4;
        inputSize += imageRecordList[i].imageRecordLength + 4;
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

    tempSize = strlen(targetIdentifier);  // Target identifier 1..8 image name
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    // Add in the length of image record array then the data if available
    PUT_INT(totalArraySize, cursor);

    if (totalArraySize > 0) {
        for (i = 0; i < imageRecordArrayCount; i++) {
            tempSize = imageRecordList[i].imageRecordLength;
            PUT_INT(tempSize, cursor);
            memcpy(cursor, imageRecordList[i].imageRecord, tempSize);
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
