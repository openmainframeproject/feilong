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
#ifndef _VMAPI_AUTHORIZATION_H
#define _VMAPI_AUTHORIZATION_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Authorization_List_Add */
typedef struct _vmApiAuthorizationListAddOutput {
    commonOutputFields common;
} vmApiAuthorizationListAddOutput;

/* Parser table for Authorization_List_Add */
static tableLayout Authorization_List_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAuthorizationListAddOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListAddOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smAuthorization_List_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * for_id, char * function_id, vmApiAuthorizationListAddOutput ** outData);

/* Authorization_List_Query */
typedef struct _vmApiAuthorizationRecord {
    char * requestingUserid;
    char requestingListIndicator;
    char * forUserid;
    char forListIndicator;
    char * functionName;
    char functionListIndicator;
} vmApiAuthorizationRecord;

typedef struct _vmApiAuthorizationListQueryOutput {
    commonOutputFields common;
    int authorizationRecordCount;
    vmApiAuthorizationRecord * authorizationRecordList;
} vmApiAuthorizationListQueryOutput;

/* Parser table for Authorization_List_Query */
static tableLayout Authorization_List_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAuthorizationListQueryOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListQueryOutput, authorizationRecordList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListQueryOutput, authorizationRecordCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiAuthorizationRecord) },
    { APITYPE_STRING_LEN,         0, 64, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, requestingUserid) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, requestingListIndicator) },
    { APITYPE_STRING_LEN,         0, 64, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, forUserid) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, forListIndicator) },
    { APITYPE_STRING_LEN,         0, 64, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, functionName) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAuthorizationRecord, functionListIndicator) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smAuthorization_List_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * for_id, char * function_id, vmApiAuthorizationListQueryOutput ** outData);

/* Authorization_List_Remove */
typedef struct _vmApiAuthorizationListRemoveOutput {
    commonOutputFields common;
} vmApiAuthorizationListRemoveOutput;

/* Parser table for Authorization_List_Remove */
static tableLayout Authorization_List_Remove_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAuthorizationListRemoveOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListRemoveOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListRemoveOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAuthorizationListRemoveOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};
int smAuthorization_List_Remove(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * for_id, char * function_id, vmApiAuthorizationListRemoveOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
