/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smSocket.h"
#include "vmapiMetadata.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Metadata_Set_Layout
#define OUTPUT_STRUCTURE_NAME vmApiMetadataSetOutput

/**
 * Metadata_Set SMAPI interface
 */

int smMetadataSet(struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier, int keyValueCount,
        char ** nameArray, char ** dataArray, vmApiMetadataSetOutput ** outData) {
    const char * const functionName = "Metadata_Set";
    int tempSize;
    int metadataArraySize = 0;
    char * cursor;
    int i;
    int rc;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier) + 4;

    int metadataEntryStructureLengths[keyValueCount];
    for (i = 0; i < keyValueCount; i++) {
    	// Size of the metadataEntryStructure
    	inputSize += 4;
        metadataArraySize += 4;
        // Get metadata Name length
    	inputSize += 4;
        inputSize += strlen(nameArray[i]);
        metadataArraySize += 4;
        metadataArraySize += strlen(nameArray[i]);
        // Get metadata length
    	inputSize += 4;
        inputSize += strlen(dataArray[i]);
        metadataArraySize += 4;
        metadataArraySize += strlen(dataArray[i]);
        // Get the metadataEntryStructureLengths
        metadataEntryStructureLengths[i] = 4 + strlen(nameArray[i]) + 4 + strlen(dataArray[i]);
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

    tempSize = metadataArraySize;  // The metadataArraySize is metadata_entry_structure_length + name length + name
                                   // + data length +  data
    PUT_INT(tempSize, cursor);
    tempSize = metadataEntryStructureLengths[0];  // The metadata_entry_structure_length is the name length + name
                                                  // + data length +  data
    PUT_INT(tempSize, cursor);

    for (i = 0; i < keyValueCount; i++) {
    	// GET Name of metadata
        tempSize = strlen(nameArray[i]);
        PUT_INT(tempSize, cursor);
        memcpy(cursor, nameArray[i], tempSize);
        cursor += tempSize;
        //GET metadata
        tempSize = strlen(dataArray[i]);
        PUT_INT(tempSize, cursor);
        memcpy(cursor, dataArray[i], tempSize);
        cursor += tempSize;
        if ((i + 1) < keyValueCount) {
            tempSize = metadataEntryStructureLengths[i +1];  // The metadata_entry_structure_length is the name length + name
                                                             // + data length +  data
            PUT_INT(tempSize, cursor);

        }
    }

    // Set the context flag that indicates a possible error buffer from SMAPI
    vmapiContextP->smapiErrorBufferPossible = ERROR_OUTPUT_BUFFER_POSSIBLE_WITH_LENGTH_FIELD;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
