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
#ifndef VMAPIDELETE_H
#define VMAPIDELETE_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Delete_ABEND_Dump */
typedef struct _vmApiDeleteABENDDumpOutput {
    commonOutputFields common;
} vmApiDeleteABENDDumpOutput;

/* Parser table for Delete_ABEND_Dump  */
static tableLayout Delete_ABEND_Dump_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiDeleteABENDDumpOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiDeleteABENDDumpOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiDeleteABENDDumpOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiDeleteABENDDumpOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smDelete_ABEND_Dump(struct _vmApiInternalContext* vmapiContextP, char * userid,
    int passwordLength, char * password, char * targetIdentifier, int keyValueCount,
    char ** keyValueArray, vmApiDeleteABENDDumpOutput ** outData);


#ifdef __cplusplus
}
#endif

#endif  // VMAPIDELETE_H
