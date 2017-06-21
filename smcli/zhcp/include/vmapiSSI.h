/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
