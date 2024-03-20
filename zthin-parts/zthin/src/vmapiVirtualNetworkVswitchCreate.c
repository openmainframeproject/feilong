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
#include "vmapiVirtual.h"
#include "smapiTableParser.h"
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>

#define PARSER_TABLE_NAME     Virtual_Network_Vswitch_Create_Layout
#define OUTPUT_STRUCTURE_NAME vmApiVirtualNetworkVswitchCreateOutput

/**
 * Virtual_Network_Vswitch_Create SMAPI interface
 */
int smVirtual_Network_Vswitch_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * switchName, char * realDeviceAddress, char * portName,
        char * controllerName, char connectionValue, int queueMemoryLimit, char routingValue, char transportType, int vlanId,
        char portType, char updateSystemConfigIndicator, char * systemConfigName, char * systemConfigType, char * parmDiskOwner,
        char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName, char * altSystemConfigType,
        char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword, char gvrpValue,
        int nativeVlanId, vmApiVirtualNetworkVswitchCreateOutput ** outData) {
    const char * const functionName = "Virtual_Network_Vswitch_Create";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    char * stringCursor;  // Used for outData string area pointer
    int arrayCount;
    int totalStringSize;
    int rc;
    int sockDesc;
    int requestId;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4 + passwordLength + 4 + strlen(targetIdentifier) +
            4 + strlen(switchName) + 4 + strlen(realDeviceAddress) + 4 + strlen(portName) + 4 + strlen(controllerName) +
            1 + 4 + 1 + 1 + 4 + 1 + 1 + 4 + strlen(systemConfigName) + 4 + strlen(systemConfigType) + 4 + strlen(parmDiskOwner) +
            4 + strlen(parmDiskNumber) + 4 + strlen(parmDiskPassword) + 4 + strlen(altSystemConfigName) + 4 +
            strlen(altSystemConfigType) + 4 + strlen(altParmDiskOwner) + 4 + strlen(altParmDiskNumber) + 4 +
            strlen(altParmDiskPassword) + 1 + 4;
    char * inputP = 0;
    char * smapiOutputP = 0;
    char line[LINESIZE];
    int i;

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }
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

    tempSize = strlen(switchName);  // Switch name 1..8
    PUT_INT(tempSize, cursor);
    memcpy(cursor, switchName, tempSize);
    cursor += tempSize;

    tempSize = strlen(realDeviceAddress);  // Real device address 0..14 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, realDeviceAddress, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(portName);  // Port name 0..26 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, portName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(controllerName);  // Controller name 0..8
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, controllerName, tempSize);
        cursor += tempSize;
    }

    *cursor = connectionValue;  // Connection value byte
    cursor++;

    PUT_INT(queueMemoryLimit, cursor);  // Queue memory limit

    *cursor = routingValue;  // Routing value byte
    cursor++;

    *cursor = transportType;  // Transport type byte
    cursor++;

    PUT_INT(vlanId, cursor);  // Vlan id

    *cursor = portType;  // Port type byte
    cursor++;

    *cursor = updateSystemConfigIndicator;  // Update system config indicator byte
    cursor++;

    tempSize = strlen(systemConfigName);  // System config name 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, systemConfigName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(systemConfigType);  // System config type 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, systemConfigType, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(parmDiskOwner);  // Parm disk owner 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, parmDiskOwner, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(parmDiskNumber);  // Parm disk number 0..4 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, parmDiskNumber, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(parmDiskPassword);  // Parm disk password 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, parmDiskPassword, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(altSystemConfigName);  // Alt system config name 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, altSystemConfigName, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(altSystemConfigType);  // Alt system config type 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, altSystemConfigType, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(altParmDiskOwner);  // Alt parm disk owner 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, altParmDiskOwner, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(altParmDiskNumber);  // Alt parm disk number 0..4 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, altParmDiskNumber, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(altParmDiskPassword);  // Alt parm disk password 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, altParmDiskPassword, tempSize);
        cursor += tempSize;
    }

    *cursor = gvrpValue;
    cursor++;

    PUT_INT(nativeVlanId, cursor);  // Native VLAN Id

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);
    return rc;
}
