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
#ifndef _VMAPI_QUERY_H
#define _VMAPI_QUERY_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Query_ABEND_Dump */
typedef struct _vmApiAbendDumpInfo {
    char abend_dump_loc;
    char * abend_dump_id;
    char * abend_dump_date;
    char * abend_dump_dist;
} vmApiAbendDumpInfo;

typedef struct _vmApiQueryAbendDumpOutput {
    commonOutputFields common;
    int dumpStrCount;
    vmApiAbendDumpInfo *abendDumpStructure;
} vmApiQueryAbendDumpOutput;

/* Parser table for Query_ABEND_Dump */
static tableLayout Query_ABEND_Dump_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryAbendDumpOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAbendDumpOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAbendDumpOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAbendDumpOutput, common.reasonCode) },
    { APITYPE_ARRAY_NO_LENGTH,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAbendDumpOutput, abendDumpStructure) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAbendDumpOutput, dumpStrCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiAbendDumpInfo) },
    { APITYPE_INT1,                1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAbendDumpInfo, abend_dump_loc) },
    { APITYPE_FIXED_STR_PTR,       8,  8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAbendDumpInfo, abend_dump_id) },
    { APITYPE_FIXED_STR_PTR,      10, 10, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAbendDumpInfo, abend_dump_date) },
    { APITYPE_FIXED_STR_PTR,       8,  8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiAbendDumpInfo, abend_dump_dist) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smQuery_ABEND_Dump(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiQueryAbendDumpOutput** outData);

/* Query_All_DM */
typedef struct _vmApiDirectoryEntryRecord {
    int directoryEntryRecordLength;
    char * directoryEntryRecord;
} vmApiDirectoryEntryRecord;

typedef struct _vmapiDirectoryEntryStructure {
    int directoryEntryType;
    char * directoryEntryId;
    int directoryEntryDataLength;
    char * directoryEntryData;
    int directoryEntryArrayCount;
    vmApiDirectoryEntryRecord *directoryEntryRecordArray;
} vmapiDirectoryEntryStructure;

typedef struct _vmApiQueryAllDmOutput {
    commonOutputFields common;
    int directoryEntriesArrayCount;
    vmapiDirectoryEntryStructure *directoryEntryArray;
} vmApiQueryAllDmOutput;


/* Parser table for Query_All_DM when Format equals YES*/
static tableLayout Query_All_DM_YES_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryAllDmOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, directoryEntryArray) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, directoryEntriesArrayCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmapiDirectoryEntryStructure) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryType) },
    { APITYPE_STRING_LEN,         1, 10, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryId) },
    { APITYPE_CHARBUF_PTR,        0, -1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryData) },
    { APITYPE_CHARBUF_COUNT,      4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

/* Parser table for Query_All_DM when Format equals NO*/
static tableLayout Query_All_DM_NO_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryAllDmOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, directoryEntryArray) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAllDmOutput, directoryEntriesArrayCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmapiDirectoryEntryStructure) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryType) },
    { APITYPE_STRING_LEN,         1, 10, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryId) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryRecordArray) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmapiDirectoryEntryStructure, directoryEntryArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiDirectoryEntryRecord) },
    { APITYPE_CHARBUF_LEN,        1, 80, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiDirectoryEntryRecord, directoryEntryRecord) },
    { APITYPE_CHARBUF_COUNT,      4,  4, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiDirectoryEntryRecord, directoryEntryRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smQuery_All_DM_NO(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiQueryAllDmOutput** outData);

int smQuery_All_DM_YES(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiQueryAllDmOutput** outData);


/* Query_API_Functional_Level */
typedef struct _vmApiQueryApiFunctionalLevelOutput {
    commonOutputFields common;
} vmApiQueryApiFunctionalLevelOutput;

/* Parser table for Query_API_Functional_Level */
static tableLayout Query_API_Functional_Level_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryApiFunctionalLevelOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryApiFunctionalLevelOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryApiFunctionalLevelOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryApiFunctionalLevelOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smQuery_API_Functional_Level(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiQueryApiFunctionalLevelOutput ** outData);

/* Query_Asychronous_Operation_DM */
typedef struct _vmApiQueryAsynchronousOperationDmOutput {
    commonOutputFields common;
} vmApiQueryAsynchronousOperationDmOutput;

/* Parser table for Query_Asychronous_Operation_DM */
static tableLayout Query_Asynchronous_Operation_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryAsynchronousOperationDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAsynchronousOperationDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAsynchronousOperationDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryAsynchronousOperationDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smQuery_Asychronous_Operation_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int operationId, vmApiQueryAsynchronousOperationDmOutput ** outData);

/* Query_Directory_Manager_Level_DM */
typedef struct _vmApiQueryDirectoryManagerLevelDm {
    commonOutputFields common;
    char * directoryManagerLevel;
    int directoryManagerLevelLength;
} vmApiQueryDirectoryManagerLevelDmOutput;

/* Parser table for Query_Directory_Manager_Level_DM */
static tableLayout Query_Directory_Manager_Level_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,   4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiQueryDirectoryManagerLevelDmOutput) },
    { APITYPE_INT4,            4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryDirectoryManagerLevelDmOutput, common.requestId) },
    { APITYPE_INT4,            4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryDirectoryManagerLevelDmOutput, common.returnCode) },
    { APITYPE_INT4,            4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryDirectoryManagerLevelDmOutput, common.reasonCode) },
    { APITYPE_CHARBUF_LEN,     1, 100, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryDirectoryManagerLevelDmOutput, directoryManagerLevel) },
    { APITYPE_CHARBUF_COUNT,   1, 100, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiQueryDirectoryManagerLevelDmOutput, directoryManagerLevelLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smQuery_Directory_Manager_Level_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiQueryDirectoryManagerLevelDmOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
