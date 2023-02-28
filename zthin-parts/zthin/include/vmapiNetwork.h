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

#ifndef VMAPINETWORK_H_
#define VMAPINETWORK_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Network_IP_Interface_Create */
typedef struct _vmApiNetworkIPInterfaceCreateOutput {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiNetworkIPInterfaceCreateOutput;

/* Parser table for Network_IP_Interface_Create */
static tableLayout Network_IP_Interface_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNetworkIPInterfaceCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceCreateOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceCreateOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceCreateOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smNetwork_IP_Interface_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiNetworkIPInterfaceCreateOutput ** outData);

/* Network_IP_Interface_Modify */
typedef struct _vmApiNetworkIPInterfaceModifyOutput {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiNetworkIPInterfaceModifyOutput;

/* Parser table for Network_IP_Interface_Modify */
static tableLayout Network_IP_Interface_Modify_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNetworkIPInterfaceModifyOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceModifyOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceModifyOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceModifyOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceModifyOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceModifyOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smNetwork_IP_Interface_Modify(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiNetworkIPInterfaceModifyOutput ** outData);

/* Network_IP_Interface_Query */
typedef struct _vmApiNetworkIPInterfaceQueryOutput {
    commonOutputFields common;
    int interfaceConfigArrayLength;
    int interfaceConfigArrayCount;
    vmApiCStringInfo* interfaceConfigArray;
} vmApiNetworkIPInterfaceQueryOutput;

/* Parser table for Network_IP_Interface_Query */
static tableLayout Network_IP_Interface_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNetworkIPInterfaceQueryOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, common.reasonCode) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, interfaceConfigArrayLength) },
    { APITYPE_C_STR_ARRAY_PTR,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, interfaceConfigArray) },
    { APITYPE_C_STR_ARRAY_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceQueryOutput, interfaceConfigArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smNetwork_IP_Interface_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiNetworkIPInterfaceQueryOutput ** outData);

/* Network_IP_Interface_Remove */
typedef struct _vmApiNetworkIPInterfaceRemoveOutput {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiNetworkIPInterfaceRemoveOutput;

/* Parser table for Network_IP_Interface_Remove */
static tableLayout Network_IP_Interface_Remove_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNetworkIPInterfaceRemoveOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceRemoveOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceRemoveOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceRemoveOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceRemoveOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNetworkIPInterfaceRemoveOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smNetwork_IP_Interface_Remove(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiNetworkIPInterfaceRemoveOutput ** outData);

#ifdef __cplusplus
}
#endif
#endif /* VMAPINETWORK_H_ */
