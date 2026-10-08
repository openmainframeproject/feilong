/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 */
#include "smSocket.h"
#include "vmapiImage.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Image_Rename_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiImageRenameDmOutput

/**
 * Image_Rename_DM SMAPI interface
 * Renames a VM by executing: DIRM FOR <old_name> CHNGID TO <new_name>
 */
int smImage_Rename_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * newImageName,
        vmApiImageRenameDmOutput ** outData) {
    
    const char * const functionName = "Image_Rename_DM";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    int rc;

    fprintf(stderr, "[DEBUG] %s enter\n", functionName);
    fprintf(stderr, "[DEBUG] %s userid='%s' passwordLength=%d\n",
            functionName, userid, passwordLength);
    fprintf(stderr, "[DEBUG] %s targetIdentifier='%s' newImageName='%s'\n",
            functionName, targetIdentifier, newImageName);

    char * newVar = "new_image_name=";
    char * newVarFull = malloc(strlen(newVar) + strlen(newImageName) + 1);
    if (newVarFull) {
        strcpy(newVarFull, newVar);
        strcat(newVarFull, newImageName);
    }
    fprintf(stderr, "[DEBUG] %s targetIdentifier='%s' newImageName='%s'\n",
            functionName, targetIdentifier, newVarFull);
    // Calculate input buffer size
    // Format: function_name + userid + password + target_identifier + new_image_name
    int inputSize = 4 + 4 + strlen(functionName) +
                    4 + strlen(userid) +
                    4 + passwordLength +
                    4 + strlen(targetIdentifier) +
                    4 + strlen(newVarFull);
    
    char * inputP = 0;

    fprintf(stderr, "[DEBUG] %s inputSize=%d\n", functionName, inputSize);

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }
    

    cursor = inputP;
    PUT_INT(inputSize - 4, cursor);

    // Add function name
    tempSize = strlen(functionName);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, functionName, tempSize);
    cursor += tempSize;

    // Add userid (authorizing user, can be empty)
    tempSize = strlen(userid);
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, userid, tempSize);
        cursor += tempSize;
    }

    // Add password (can be empty)
    tempSize = passwordLength;
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, password, tempSize);
        cursor += tempSize;
    }

    // Add target identifier (current VM name)
    tempSize = strlen(targetIdentifier);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    // Add new image name
    tempSize = strlen(newVarFull);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, newVarFull, tempSize);
    cursor += tempSize;


    // Send SMAPI request and parse response
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,
            TO_STRING(PARSER_TABLE_NAME),
            (char * *) outData);

    if (!rc && outData && *outData) {
        fprintf(stderr, "[DEBUG] %s SMAPI returnCode=%d reasonCode=%d\n",
                functionName,
                (*outData)->common.returnCode,
                (*outData)->common.reasonCode);
    }
    
    return rc;
}