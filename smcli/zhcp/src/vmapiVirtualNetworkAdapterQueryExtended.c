/**
 * IBM (C) Copyright 2015 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smSocket.h"
#include "vmapiVirtual.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Virtual_Network_Adapter_Query_Extended_Layout
#define OUTPUT_STRUCTURE_NAME vmApiVirtualNetworkAdapterQueryExtendedOutput

/**
 * Virtual_Network_Adapter_Query_Extended SMAPI interface
 */
int smVirtual_Network_Adapter_Query_Extended(
    struct _vmApiInternalContext* vmapiContextP,
    char * userid,
    int passwordLength,
    char * password,
    char * targetIdentifier,
    int keyValueCount,
    char ** keyValueArray,
    vmApiVirtualNetworkAdapterQueryExtendedOutput ** outData) {

    const char * const functionName = "Virtual_Network_Adapter_Query_Extended";

    char * cursor;                // Ptr to next slot in input parm buffer
    int i;                        // Index
    char * inputP = 0;            // SMAPI input parameter buffer
    int keyValueSize = 0;         // Size of the key parameter area
    int rc;                       // Return code for this function
    int tempSize;                 // Temporary work buffer

    int inputSize = 4 + 4 + strlen( functionName ) + 4 + strlen( userid ) +
        4 + passwordLength + 4 + strlen( targetIdentifier ) +
        sizeof( keyValueSize );

    for ( i = 0; i < keyValueCount; i++ ) {
        inputSize += strlen( keyValueArray[i] ) + 1;
        keyValueSize += strlen( keyValueArray[i] ) + 1;
    }

    // Build SMAPI input parameter buffer
    if ( 0 == ( inputP = malloc( inputSize ) ) )
        return MEMORY_ERROR;

    cursor = inputP;
    PUT_INT( inputSize - 4, cursor );

    tempSize = strlen( functionName );
    PUT_INT( tempSize, cursor );
    memcpy( cursor, functionName, tempSize );
    cursor += tempSize;

    tempSize = strlen( userid );  // Userid 1..8 or 0..8 chars
    PUT_INT( tempSize, cursor );
    if ( tempSize > 0 ) {
        memcpy( cursor, userid, tempSize );
        cursor += tempSize;
    }

    tempSize = passwordLength;  // Password 1..200 or 0..200 chars
    PUT_INT( tempSize, cursor );
    if ( tempSize > 0 ) {
        memcpy( cursor, password, tempSize );
        cursor += tempSize;
    }

    tempSize = strlen( targetIdentifier );  // Target identifier 1..8
    PUT_INT( tempSize, cursor );
    memcpy( cursor, targetIdentifier, tempSize );
    cursor += tempSize;

    PUT_INT( keyValueSize, cursor );      // Total key value size

    for ( i = 0; i < keyValueCount; i++ ) {  // 'Keyword=value' null terminated strings
        tempSize = strlen( keyValueArray[i] ) + 1;
        strcpy( cursor, keyValueArray[i] );
        cursor += tempSize;
    }

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer( vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,             // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);

    return rc;
}
