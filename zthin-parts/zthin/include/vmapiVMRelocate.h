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
#ifndef VMAPIVMRELOCATE_H_
#define VMAPIVMRELOCATE_H_
#include <stddef.h>
#include "smPublic.h"
#include "smapiTableParser.h"

/* VMRELOCATE */
typedef struct _vmApiVMRelocate {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiVMRelocateOutput;

/* Parser table for VMRELOCATE */
static tableLayout VMRELOCATE_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVMRelocateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRELOCATE(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* relocateTarget, int keyValueCount, char ** keyValueArray, vmApiVMRelocateOutput** outData);

/* VMRELOCATE_Image_Attributes */
typedef struct _vmApiVMRelocateImageAttributes {
    commonOutputFields common;
} vmApiVMRelocateImageAttributesOutput;

/* Parser table for VMRELOCATE_Image_Attributes */
static tableLayout VMRELOCATE_Image_Attributes_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVMRelocateImageAttributesOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateImageAttributesOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateImageAttributesOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateImageAttributesOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRELOCATE_Image_Attributes(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* relocateTarget, int keyValueCount, char ** keyValueArray, vmApiVMRelocateImageAttributesOutput** outData);

/* VMRELOCATE_Modify */
typedef struct _vmApiVMRelocateModify {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiVMRelocateModifyOutput;

/* Parser table for VMRELOCATE_Modify */
static tableLayout VMRELOCATE_Modify_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVMRelocateModifyOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateModifyOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateModifyOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateModifyOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateModifyOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateModifyOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRELOCATE_Modify(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* relocateTarget, int keyValueCount, char ** keyValueArray, vmApiVMRelocateModifyOutput** outData);

/* VMRELOCATE_Status */
typedef struct _vmApiVMRelocateStatus {
    commonOutputFields common;
    int statusArrayCount;
    vmApiCStringInfo* statusArray;
} vmApiVMRelocateStatusOutput;

/* Parser table for VMRELOCATE_Status */
static tableLayout VMRELOCATE_Status_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVMRelocateStatusOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateStatusOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateStatusOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateStatusOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateStatusOutput, statusArray) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVMRelocateStatusOutput, statusArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRELOCATE_Status(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* relocateTarget, int keyValueCount, char ** keyValueArray, vmApiVMRelocateStatusOutput** outData);
#endif  // VMAPIVMRELOCATE_H_
