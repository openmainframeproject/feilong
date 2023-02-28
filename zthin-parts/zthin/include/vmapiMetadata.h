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
#ifndef VMAPIMETADATA_H_
#define VMAPIMETADATA_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Metadata_Delete */
typedef struct _vmApiMetadataDeleteOutput {
    commonOutputFields common;
} vmApiMetadataDeleteOutput;

/* Parser table for Metadata_Delete */
static tableLayout Metadata_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiMetadataDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smMetadata_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * keywordlist, vmApiMetadataDeleteOutput ** outData);

/* Metadata_Get */
typedef struct _vmApiMetadataEntry {
	int metadataEntryStructureLength;
	int metadataEntryNameLength;
    char * metadataEntryName;
    int metadataLength;
    char * metadata;
} vmApiMetadataEntry;

typedef struct _vmApiMetadataGetOutput {
    commonOutputFields common;
    int metadataEntryCount;
    vmApiMetadataEntry * metadataEntryList;
} vmApiMetadataGetOutput;

/* Parser table for Metadata_Get */
static tableLayout Metadata_Get_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,    4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiMetadataGetOutput) },
    { APITYPE_INT4,                4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataGetOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataGetOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataGetOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataGetOutput, metadataEntryList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataGetOutput, metadataEntryCount) },
    { APITYPE_STRUCT_LEN,          4,    4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiMetadataEntry) },
    { APITYPE_STRING_LEN,          0, 1024, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiMetadataEntry, metadataEntryName) },
    { APITYPE_STRING_LEN,          0,   -1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiMetadataEntry, metadata) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smMetadataGet(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * keywordlist, vmApiMetadataGetOutput ** outData);

/* Metadata_Set */
typedef struct _vmApiMetadataSetOutput {
    commonOutputFields common;
} vmApiMetadataSetOutput;

/* Parser table for Metadata_Set */
static tableLayout Metadata_Set_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiMetadataSetOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSetOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSetOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSetOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smMetadataSet(struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier, int keyValueCount,
        char ** nameArray, char ** dataArray, vmApiMetadataSetOutput ** outData);

/* Metadata_Space_Query */

typedef struct _vmApiMetadataSpaceQueryOutput {
    commonOutputFields common;
    int metadataEntryCount;
    vmApiCStringInfo * metadataEntryList;
} vmApiMetadataSpaceQueryOutput;

/* Parser table for Metadata_Space_Query */
static tableLayout Metadata_Space_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,    4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiMetadataSpaceQueryOutput) },
    { APITYPE_INT4,                4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSpaceQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSpaceQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSpaceQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,     4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSpaceQueryOutput, metadataEntryList) },
    { APITYPE_C_STR_ARRAY_COUNT,   4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiMetadataSpaceQueryOutput, metadataEntryCount) },
    { APITYPE_C_STR_STRUCT_LEN,    4,    4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           4,    4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smMetadataSpaceQuery(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * keywordlist, vmApiMetadataSpaceQueryOutput ** outData);
#ifdef __cplusplus
}
#endif

#endif /* VMAPIMETADATA_H_ */
