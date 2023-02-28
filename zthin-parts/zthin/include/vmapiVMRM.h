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
#ifndef VMAPIVMRM_H
#define VMAPIVMRM_H
#include <stddef.h>
#include "smPublic.h"
#include "smapiTableParser.h"


#ifdef __cplusplus
extern "C" {
#endif

/* VMRM_Configuration_Query */
typedef struct _vmApiVmrmConfigurationQuery {
    commonOutputFields common;
    char * configurationFile;
    int configurationFileLength;
} vmApiVmrmConfigurationQueryOutput;

/* Parser table for VMRM_Configuration_Query */
static tableLayout VMRM_Configuration_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVmrmConfigurationQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_LEN,     1, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationQueryOutput, configurationFile) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationQueryOutput, configurationFileLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRM_Configuration_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password, char * targetIdentifier,
        char * configurationFileName, char * configurationFileType, char * configurationDirName, vmApiVmrmConfigurationQueryOutput ** outData);

/* VMRM_Configuration_Update */
typedef struct _vmApiVmrmConfigurationLogRecordInfo {
    char * logRecord;
    int logRecordLength;
} vmApiVmrmConfigurationLogRecordInfo;

typedef struct _vmApiVmrmConfigurationUpdateOutput {
    commonOutputFields common;
    int logRecordCount;
    vmApiVmrmConfigurationLogRecordInfo * logRecordInfoList;
} vmApiVmrmConfigurationUpdateOutput;

typedef struct _vmApiUpdateRecord {
    int updateRecordLength;
    char * updateRecord;
} vmApiUpdateRecord;

/* Parser table for VMRM_Configuration_Update */
static tableLayout VMRM_Configuration_Update_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVmrmConfigurationUpdateOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationUpdateOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationUpdateOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationUpdateOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationUpdateOutput, logRecordInfoList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmConfigurationUpdateOutput, logRecordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVmrmConfigurationLogRecordInfo) },
    { APITYPE_CHARBUF_LEN,         1, -1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVmrmConfigurationLogRecordInfo, logRecord) },
    { APITYPE_CHARBUF_COUNT,       4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVmrmConfigurationLogRecordInfo, logRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRM_Configuration_Update(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password, char * targetIdentifier, 
        char * configurationFileName, char * configurationFileType, char * configurationDirName, char syncheckOnly, 
        int updateRecordCount, vmApiUpdateRecord * updateRecordList, vmApiVmrmConfigurationUpdateOutput ** outData);

/* VMRM_Measurement_Query */
typedef struct _vmApiVmrmMeasurementQueryWorkloadInfo {
    char * workloadRecord;
    int workloadRecordLength;
} vmApiVmrmMeasurementQueryWorkloadInfo;

typedef struct _vmApiVmrmMeasurementQueryOutput {
    commonOutputFields common;
    char * queryTimestamp;
    char * fileName;
    char * fileTimestamp;
    int workloadCount;
    vmApiVmrmMeasurementQueryWorkloadInfo * workloadInfoList;
} vmApiVmrmMeasurementQueryOutput;

/* Parser table for VMRM_Measurement_Query */
static tableLayout VMRM_Measurement_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVmrmMeasurementQueryOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,          1, 17, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, queryTimestamp) },
    { APITYPE_STRING_LEN,          1, 20, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, fileName) },
    { APITYPE_STRING_LEN,          1, 17, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, fileTimestamp) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, workloadInfoList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVmrmMeasurementQueryOutput, workloadCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVmrmMeasurementQueryWorkloadInfo) },
    { APITYPE_CHARBUF_LEN,         1, 35, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVmrmMeasurementQueryWorkloadInfo, workloadRecord) },
    { APITYPE_CHARBUF_COUNT,       1,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVmrmMeasurementQueryWorkloadInfo, workloadRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVMRM_Measurement_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiVmrmMeasurementQueryOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif  // VMAPIVMRM_H
