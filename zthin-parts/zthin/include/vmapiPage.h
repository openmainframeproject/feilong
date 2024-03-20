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
#ifndef VMAPIPAGE_H_
#define VMAPIPAGE_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* Page_or_Spool_Volume_Add */
typedef struct _vmApiPageOrSpoolVolumeAddOutput {
    commonOutputFields common;
} vmApiPageOrSpoolVolumeAddOutput;

/* Parser table for Page_or_Spool_Volume_Add */
static  tableLayout Page_or_Spool_Volume_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiPageOrSpoolVolumeAddOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPageOrSpoolVolumeAddOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPageOrSpoolVolumeAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiPageOrSpoolVolumeAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smPage_or_Spool_Volume_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiPageOrSpoolVolumeAddOutput ** outData);

#endif  /* VMAPIPAGE_H_ */
