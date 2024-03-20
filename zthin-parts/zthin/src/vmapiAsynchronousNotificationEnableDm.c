/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017 IBM Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "smSocket.h"
#include "vmapiAsynchronous.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Asynchronous_Notification_Enable_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiAsynchronousNotificationEnableDmOutput

/**
 * Asynchronous_Notification_Enable_DM SMAPI interface
 */
int smAsynchronous_Notification_Enable_DM(
        struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier,
        char entity_type, char subscription_type, char communication_type,
        int port_number, char * ip_address, char encoding,
        int subscriber_data_length, char * subscriber_data,
        vmApiAsynchronousNotificationEnableDmOutput ** outData) {
    const char * const functionName = "Asynchronous_Notification_Enable_DM";
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
            + passwordLength + 4 + strlen(targetIdentifier) + 1 + 1 + 1 + 4 + 4
            + strlen(ip_address) + 1 + 4 + subscriber_data_length;

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

    *cursor = entity_type;  // Entity_type int1
    cursor++;

    *cursor = subscription_type;  // Subscription_type int1
    cursor++;

    *cursor = communication_type;  // Communication_type int1
    cursor++;

    PUT_INT(port_number, cursor);  // Port_number int4

    tempSize = strlen(ip_address);  // IP_address 7..15 chars
    PUT_INT(tempSize, cursor);
    memcpy(cursor, ip_address, tempSize);
    cursor += tempSize;

    *cursor = encoding;  // Encoding
    cursor++;

    tempSize = subscriber_data_length;  // Subscriber_data 0..64 chars
    PUT_INT(tempSize, cursor);
    memcpy(cursor, subscriber_data, tempSize);
    cursor += tempSize;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
