/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
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
