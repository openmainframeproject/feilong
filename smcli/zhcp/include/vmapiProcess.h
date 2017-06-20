/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef VMAPIPROCESS_H_
#define VMAPIPROCESS_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* Process_ABEND_Dump */
typedef struct _vmApiProcessAbendDumpOutput {
    commonOutputFields common;
} vmApiProcessAbendDumpOutput;

/* Parser table for Process_ABEND_Dump */
static  tableLayout Process_ABEND_Dump_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProcessAbendDumpOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProcessAbendDumpOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProcessAbendDumpOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProcessAbendDumpOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProcess_ABEND_Dump(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiProcessAbendDumpOutput ** outData);

#endif  /* VMAPIPROCESS_H_ */
