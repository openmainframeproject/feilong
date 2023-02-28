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
#ifndef VMAPISSI_H_
#define VMAPISSI_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* SSI_Query */
typedef struct _vmApiSSIQueryOutput  {
    commonOutputFields common;
    char * ssi_name;
    char * ssi_mode;
    char * cross_system_timeouts;
    char * ssi_pdr;
    int ssiInfoCount;
    vmApiCStringInfo* ssiInfo;
} vmApiSSIQueryOutput;

/* Parser table for SSI_Query */
static tableLayout SSI_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSSIQueryOutput) },
    { APITYPE_INT4,              4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_PTR,         1,  8, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, ssi_name) },
    { APITYPE_C_STR_PTR,         4,  6, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, ssi_mode) },
    { APITYPE_C_STR_PTR,         7,  8, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, cross_system_timeouts) },
    { APITYPE_C_STR_PTR,         6, 14, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, ssi_pdr) },
    { APITYPE_C_STR_ARRAY_PTR,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, ssiInfo) },
    { APITYPE_C_STR_ARRAY_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSSIQueryOutput, ssiInfoCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_SSI_Query(struct _vmApiInternalContext* vmapiContextP, vmApiSSIQueryOutput** outData);

#endif  /* VMAPISSI_H_ */
