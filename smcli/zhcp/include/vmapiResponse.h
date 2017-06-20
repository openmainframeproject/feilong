/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
