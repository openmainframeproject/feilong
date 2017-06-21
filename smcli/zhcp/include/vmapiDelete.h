/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
