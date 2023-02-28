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
#ifndef VMAPINAME_H
#define VMAPINAME_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Name_List_Add */
typedef struct _vmApiNameListAddOutput {
    commonOutputFields common;
} vmApiNameListAddOutput;

/* Parser table for Name_List_Add */
static tableLayout Name_List_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNameListAddOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListAddOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smName_List_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * name, vmApiNameListAddOutput ** outData);

/* Name_List_Destroy */
typedef struct _vmApiNameListDestroyOutput {
    commonOutputFields common;
} vmApiNameListDestroyOutput;

/* Parser table for Name_List_Destroy */
static tableLayout Name_List_Destroy_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNameListDestroyOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListDestroyOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListDestroyOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListDestroyOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smName_List_Destroy(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiNameListDestroyOutput ** outData);

/* Name_List_Query */
typedef struct _vmApiNameList {
    char * imageName;
} vmApiNameList;

typedef struct _vmApiNameListQuery {
    commonOutputFields common;
    int nameArrayCount;
    vmApiNameList * nameList;
} vmApiNameListQueryOutput;

/* Parser table for Name_List_Query */
static tableLayout Name_List_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNameListQueryOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListQueryOutput, nameList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListQueryOutput, nameArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiNameList) },
    { APITYPE_STRING_LEN,          1,64, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNameList, imageName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smName_List_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiNameListQueryOutput ** outData);

/* Name_List_Remove */
typedef struct _vmApiNameListRemoveOutput {
    commonOutputFields common;
} vmApiNameListRemoveOutput;

/* Parser table for Name_List_Remove */
static tableLayout Name_List_Remove_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiNameListRemoveOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListRemoveOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListRemoveOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiNameListRemoveOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smName_List_Remove(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * name, vmApiNameListRemoveOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif  // VMAPINAME_H
