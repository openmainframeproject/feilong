/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smSocket.h"
#include "vmapiUnDocumented.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     System_IO_Query_Layout
#define OUTPUT_STRUCTURE_NAME vmApiSystemIoQueryOutput

/**
 * System_IO_Query SMAPI interface
 */
int smSystem_IO_Query(struct _vmApiInternalContext* vmapiContextP,
        char * realDeviceAddress, vmApiSystemIoQueryOutput ** outData) {
    const char * const functionName = "System_IO_Query";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    char * stringCursor;  // Used for outData string area pointer
    int arrayCount;
    int totalStringSize;
    int rc;
    int sockDesc;
    int requestId;

    int inputSize = 4 + 1 + strlen(functionName) + 1 /* null term */+ strlen(
            realDeviceAddress) + 1 /* null term */;
    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];
    int i;

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize)))
        return MEMORY_ERROR;
    cursor = inputP;
    PUT_INT(inputSize - 4, cursor);

    *cursor = 0xFF;  // Separator
    cursor++;

    tempSize = strlen(functionName);
    strcpy(cursor, functionName);
    cursor += tempSize + 1;

    tempSize = strlen(realDeviceAddress);
    strcpy(cursor, realDeviceAddress);
    cursor += tempSize + 1;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
