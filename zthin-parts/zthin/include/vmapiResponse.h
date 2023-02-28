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
#ifndef VMAPIRESPONSE_H_
#define VMAPIRESPONSE_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* Response_Recovery*/
typedef struct _vmApiResponseRecoveryOutput {
    commonOutputFields common;
    vmApiCStringInfo* responseData;
} vmApiResponseRecoveryOutput;

/* Parser table for Response_Recovery */
static tableLayout Response_Recovery_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiResponseRecoveryOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiResponseRecoveryOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiResponseRecoveryOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiResponseRecoveryOutput, common.reasonCode) },
    { APITYPE_C_STR_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,        4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smResponse_Recovery(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int failedRequestID, vmApiResponseRecoveryOutput ** outData);

#endif  /* VMAPIRESPONSE_H_ */
