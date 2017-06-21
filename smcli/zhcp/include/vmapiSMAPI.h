/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef _VMAPI_SMAPI_H
#define _VMAPI_SMAPI_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* SMAPI_Status_Capture */
typedef struct _vmApiSMAPIStatusCaptureOutput  {
    commonOutputFields common;
}  vmApiSMAPIStatusCaptureOutput;

/* Parser table for SMAPI_Status_Capture */
static tableLayout SMAPI_Status_Capture_Layout = {
    {APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSMAPIStatusCaptureOutput) },
    { APITYPE_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSMAPIStatusCaptureOutput, common.requestId) },
    { APITYPE_RC_INT4,        4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSMAPIStatusCaptureOutput, common.returnCode) },
    { APITYPE_RS_INT4,        4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSMAPIStatusCaptureOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSMAPI_Status_Capture(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiSMAPIStatusCaptureOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
