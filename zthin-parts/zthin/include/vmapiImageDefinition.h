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
#ifndef _VMAPI_IMAGE_DEFINITION_H
#define _VMAPI_IMAGE_DEFINITION_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Image_Definition_Async_Updates */
typedef struct _vmApiImageDefinitionAsyncUpdatesOutput {
    commonOutputFields common;
} vmApiImageDefinitionAsyncUpdatesOutput;

/* Parser table for Image_Definition_Async_Updates */
static tableLayout Image_Definition_Async_Updates_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDefinitionAsyncUpdatesOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionAsyncUpdatesOutput, common.requestId) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionAsyncUpdatesOutput, common.returnCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionAsyncUpdatesOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Definition_Async_Updates(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiImageDefinitionAsyncUpdatesOutput ** outData);

/* Image_Definition_Create_DM */
typedef struct _vmApiImageDefinitionCreateDM {
    commonOutputFields common;
    int asynchIdLength;
    char * asynchIds;
    int errorDataLength;
    char * errorData;
} vmApiImageDefinitionCreateDMOutput;

/* Parser table for Image_Definition_Create_DM */
static tableLayout Image_Definition_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDefinitionCreateDMOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, asynchIds) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, asynchIdLength) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionCreateDMOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Definition_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiImageDefinitionCreateDMOutput ** outData);

/* Image_Definition_Delete_DM */
typedef struct _vmApiImageDefinitionDeleteDM {
    commonOutputFields common;
    int asynchIdLength;
    char * asynchIds;
    int errorDataLength;
    char * errorData;
} vmApiImageDefinitionDeleteDMOutput;

/* Parser table for Image_Definition_Delete_DM */
static tableLayout Image_Definition_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDefinitionDeleteDMOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, asynchIds) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, asynchIdLength) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionDeleteDMOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Definition_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiImageDefinitionDeleteDMOutput ** outData);

/* Image_Definition_Query_DM */
typedef struct _vmApiImageDefinitionQueryDM {
    commonOutputFields common;
    int directoryDataLength;
    char * directoryInfo;
    int errorDataLength;
    char * errorData;
} vmApiImageDefinitionQueryDMOutput;

/* Parser table for Image_Definition_Query_DM */
static tableLayout Image_Definition_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDefinitionQueryDMOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, directoryInfo) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, directoryDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionQueryDMOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Definition_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * keywordlist, vmApiImageDefinitionQueryDMOutput ** outData);

/* Image_Definition_Update_DM */
typedef struct _vmApiImageDefinitionUpdateDM {
    commonOutputFields common;
    int asynchIdLength;
    char * asynchIds;
    int errorDataLength;
    char * errorData;
} vmApiImageDefinitionUpdateDMOutput;

/* Parser table for Image_Definition_Update_DM */
static tableLayout Image_Definition_Update_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDefinitionUpdateDMOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, asynchIds) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, asynchIdLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDefinitionUpdateDMOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Definition_Update_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiImageDefinitionUpdateDMOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
