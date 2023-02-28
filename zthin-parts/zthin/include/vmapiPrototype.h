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
#ifndef _VMAPI_PROTOTYPE_H
#define _VMAPI_PROTOTYPE_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Prototype_Create_DM */
typedef struct _vmApiPrototypeRecordList {
    char * recordName;
    int recordNameLength;
} vmApiPrototypeRecordList;

typedef struct  _vmApiPrototypeCreateDmOutput {
    commonOutputFields common;
} vmApiPrototypeCreateDmOutput;

/* Parser table for Prototype_Create_DM */
static tableLayout Prototype_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPrototypeCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeCreateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPrototype_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int recordArrayCount, vmApiPrototypeRecordList * recordArrayData,
        vmApiPrototypeCreateDmOutput ** outData);

/* Prototype_Delete_DM */
typedef struct  _vmApiPrototypeDeleteDmOutput {
    commonOutputFields common;
} vmApiPrototypeDeleteDmOutput;

/* Parser table for Prototype_Delete_DM */
static tableLayout Prototype_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPrototypeDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPrototype_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiPrototypeDeleteDmOutput ** outData);

/* Prototype_Name_Query_DM */
typedef struct _vmApiPrototypeNameList {
    char * name;
} vmApiPrototypeNameList;

typedef struct _vmApiPrototypeNameQueryDm {
    commonOutputFields common;
    int nameArrayCount;
    vmApiPrototypeNameList * nameList;
} vmApiPrototypeNameQueryDmOutput;

/* Parser table for Prototype_Name_Query_DM */
static tableLayout Prototype_Name_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPrototypeNameQueryDmOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeNameQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeNameQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeNameQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeNameQueryDmOutput, nameList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeNameQueryDmOutput, nameArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiPrototypeNameList) },
    { APITYPE_STRING_LEN,          1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPrototypeNameList, name) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPrototype_Name_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiPrototypeNameQueryDmOutput ** outData);

/* Prototype_Query_DM */
typedef struct _vmApiPrototypeQueryDm {
    commonOutputFields common;
    int recordArrayCount;
    vmApiPrototypeRecordList * recordList;
} vmApiPrototypeQueryDmOutput;

/* Parser table for Prototype_Query_DM */
static tableLayout Prototype_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPrototypeQueryDmOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeQueryDmOutput, recordList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeQueryDmOutput, recordArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiPrototypeRecordList) },
    { APITYPE_CHARBUF_LEN,         1, 72, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPrototypeRecordList, recordName) },
    { APITYPE_CHARBUF_COUNT,       4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPrototypeRecordList, recordNameLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPrototype_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiPrototypeQueryDmOutput ** outData);

/* Prototype_Replace_DM */
typedef struct _vmApiPrototypeReplaceDmOutput {
    commonOutputFields common;
} vmApiPrototypeReplaceDmOutput;

/* Parser table for Prototype_Replace_DM */
static tableLayout Prototype_Replace_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPrototypeReplaceDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeReplaceDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeReplaceDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPrototypeReplaceDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPrototype_Replace_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int recordArrayCount, vmApiPrototypeRecordList * recordArrayData,
        vmApiPrototypeReplaceDmOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
