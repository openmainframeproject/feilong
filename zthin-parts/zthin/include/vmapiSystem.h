/**
 * Copyright 2017, 2022 IBM Corporation
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
#ifndef VMAPISYSTEM_H
#define VMAPISYSTEM_H
#include <stddef.h>
#include "smPublic.h"
#include "smapiTableParser.h"

#ifdef __cplusplus
extern "C" {
#endif


/* System_Config_Syntax_Check */
typedef struct _vmApiSystemConfigSyntaxCheckOutput {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiSystemConfigSyntaxCheckOutput;

/* Parser table for System_Config_Syntax_Check */
static tableLayout System_Config_Syntax_Check_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemConfigSyntaxCheckOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemConfigSyntaxCheckOutput,  common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemConfigSyntaxCheckOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemConfigSyntaxCheckOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemConfigSyntaxCheckOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemConfigSyntaxCheckOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}};

int smSystem_Config_Syntax_Check(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemConfigSyntaxCheckOutput** outData);

/* System_Disk_Accessibility */
typedef struct _vmApiSystemDiskAccessibilityOutput {
    commonOutputFields common;
} vmApiSystemDiskAccessibilityOutput;

/* Parser table for System_Disk_Accessibility */
static  tableLayout System_Disk_Accessibility_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemDiskAccessibilityOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAccessibilityOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAccessibilityOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAccessibilityOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Disk_Accessibility(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemDiskAccessibilityOutput** outData);

/* System_Disk_Add */
typedef struct _vmApiSystemDiskAddOutput {
    commonOutputFields common;
} vmApiSystemDiskAddOutput;

/* Parser table for System_Disk_Add */
static tableLayout System_Disk_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemDiskAddOutput) },
    { APITYPE_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAddOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}};

int smSystem_Disk_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemDiskAddOutput** outData);


/* System_Disk_IO_Query */
typedef struct _vmApiSystemDiskIOQueryOutput {
    commonOutputFields common;
    int dasdInformationDataLength;
    char * dasdInformationData;
    int errorDataLength;
    char * errorData;
} vmApiSystemDiskIOQueryOutput;

/* Parser table for System_Disk_IO_Query */
static tableLayout System_Disk_IO_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemDiskIOQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, dasdInformationData) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, dasdInformationDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskIOQueryOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Disk_IO_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemDiskIOQueryOutput ** outData);


/* System_Disk_Query */
typedef struct _vmApiSystemDiskQueryOutput {
    commonOutputFields common;
    int diskInfoArrayCount;
    vmApiCStringInfo* diskIinfoStructure;
} vmApiSystemDiskQueryOutput;

/* Parser table for System_Disk_Query */
static  tableLayout System_Disk_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemDiskQueryOutput) },
    { APITYPE_INT4,               4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskQueryOutput, diskIinfoStructure) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemDiskQueryOutput, diskInfoArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Disk_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemDiskQueryOutput ** outData);

/* System_EQID_Query */
typedef struct _vmApiSystemEQIDQueryOutput {
    commonOutputFields common;
    int eqidArrayLength;
    int eqidArrayCount;
    vmApiCStringInfo* eqidInfoStructureArray;
    int errorDataLength;
    char * errorData;
} vmApiSystemEQIDQueryOutput;

// Parser table for  System_EQID_Query
static  tableLayout System_EQID_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemEQIDQueryOutput) },
    { APITYPE_INT4,               4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, common.reasonCode) },
    { APITYPE_INT4,               4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, eqidArrayLength) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, eqidInfoStructureArray) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, eqidArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    {APITYPE_ERROR_BUFF_PTR,      4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, errorData) },
    {APITYPE_ERROR_BUFF_LEN,      4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemEQIDQueryOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_EQID_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemEQIDQueryOutput ** outData);

/* System_FCP_Free_Query */
typedef struct _vmApiSystemFCPFreeQueryOutput {
    commonOutputFields common;
    int fcpArrayCount;
    vmApiCStringInfo* fcpStructure;
} vmApiSystemFCPFreeQueryOutput;

/* Parser table for  System_FCP_Free_Query */
static  tableLayout System_FCP_Free_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemFCPFreeQueryOutput) },
    { APITYPE_INT4,               4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemFCPFreeQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemFCPFreeQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemFCPFreeQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemFCPFreeQueryOutput, fcpStructure) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemFCPFreeQueryOutput, fcpArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_FCP_Free_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemFCPFreeQueryOutput ** outData);

/* System_Image_Performance_Query */
typedef struct _vmApiSystemImagePerformanceRecord {
    unsigned int        recordVersion;
    unsigned int        guestFlags;
    unsigned long long  usedCPUTime;
    unsigned long long  elapsedTime;
    unsigned long long  minMemory;
    unsigned long long  maxMemory;
    unsigned long long  sharedMemory;
    unsigned long long  usedMemory;
    unsigned int        activeCPUsInCEC;
    unsigned int        logicalCPUsInVM;
    unsigned int        guestCPUs;
    unsigned int        minCPUCount;
    unsigned int        maxCPULimit;
    unsigned int        processorShare;
    unsigned int        samplesCPUInUse;
    unsigned int        samplesCPUDelay;
    unsigned int        samplesPageWait;
    unsigned int        samplesIdle;
    unsigned int        samplesOther;
    unsigned int        samplesTotal;
    char*               guestName;
} vmApiSystemImagePerformanceRecord;

typedef struct _vmApiSystemImagePerformanceQuery {
    commonOutputFields common;
    int performanceRecordCount;
    vmApiSystemImagePerformanceRecord* performanceRecords;
} vmApiSystemImagePerformanceQueryOutput;

/* Parser table for Image_Performance_Query */
static tableLayout System_Image_Performance_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemImagePerformanceQueryOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemImagePerformanceQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemImagePerformanceQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemImagePerformanceQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_COUNT,        4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemImagePerformanceQueryOutput, performanceRecords) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemImagePerformanceQueryOutput, performanceRecordCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiSystemImagePerformanceRecord) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, recordVersion) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, guestFlags) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, usedCPUTime) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, elapsedTime) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, minMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, maxMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, sharedMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, usedMemory) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, activeCPUsInCEC) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, logicalCPUsInVM) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, guestCPUs) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, minCPUCount) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, maxCPULimit) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, processorShare) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesCPUInUse) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesCPUDelay) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesPageWait) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesIdle) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesOther) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, samplesTotal) },
    { APITYPE_FIXED_STR_PTR,      8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemImagePerformanceRecord, guestName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Image_Performance_Query(struct _vmApiInternalContext* vmapiContextP, char* userid, int passwordLength, char* password,
        char* targetIdentifier, vmApiSystemImagePerformanceQueryOutput** outData);

/* System_Information_Query */
typedef struct _vmApiSystemInformationQueryOutput {
    commonOutputFields common;
    int systemInformationDataLength;
    char * systemInformationData;
} vmApiSystemInformationQueryOutput;

/* Parser table for System_Information_Query */
static tableLayout System_Information_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemInformationQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInformationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInformationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInformationQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInformationQueryOutput, systemInformationData) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInformationQueryOutput, systemInformationDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Information_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiSystemInformationQueryOutput ** outData);


/* System_Page_Utilization_Query */
typedef struct _vmApiPagingVolumeRecord {
    char * volid;
    char * rdev;
    char * totalPages;
    char * pagesInUse;
    char * percentUsed;
    char * drained;
}vmApiPagingVolumeRecord;

typedef struct _vmApiSystemPageUtilizationQueryOutput {
    commonOutputFields common;
    int systemPageInfomationLength;
    char * systemPageInformation;
} vmApiSystemPageUtilizationQueryOutput;

/* Parser table for System_Page_Utilization_Query */
static tableLayout System_Page_Utilization_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemPageUtilizationQueryOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPageUtilizationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPageUtilizationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPageUtilizationQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,        0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPageUtilizationQueryOutput, systemPageInformation) },
    { APITYPE_CHARBUF_COUNT,      4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPageUtilizationQueryOutput, systemPageInfomationLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Page_Utilization_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiSystemPageUtilizationQueryOutput ** outData);

/* System_Performance_Information_Query */
typedef struct _vmApiSystemPerformanceInformationQueryOutput {
    commonOutputFields common;
    int systemPerformanceInformationDataLength;
    char * systemPerformanceInformationData;
    int errorDataLength;
    char * errorData;
} vmApiSystemPerformanceInformationQueryOutput;

/* Parser table for System_Performance_Information_Query */
static tableLayout System_Performance_Information_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemPerformanceInformationQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, systemPerformanceInformationData) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, systemPerformanceInformationDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInformationQueryOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Performance_Information_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiSystemPerformanceInformationQueryOutput ** outData);

/* System_Performance_Threshold_Disable */
typedef struct _vmApiSystemPerformanceThresholdDisableOutput {
    commonOutputFields common;
} vmApiSystemPerformanceThresholdDisableOutput;

/* Parser table for System_Performance_Threshold_Disable */
static tableLayout System_Performance_Threshold_Disable_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemPerformanceThresholdDisableOutput) },
    { APITYPE_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdDisableOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdDisableOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdDisableOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Performance_Threshold_Disable(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char* targetIdentifier, char * eventType, vmApiSystemPerformanceThresholdDisableOutput** outData);


/* System_Performance_Threshold_Enable */
typedef struct _vmApiSystemPerformanceThresholdEnableOutput {
    commonOutputFields common;
} vmApiSystemPerformanceThresholdEnableOutput;

/* Parser table for System_Performance_Threshold_Enable */
static tableLayout System_Performance_Threshold_Enable_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemPerformanceThresholdEnableOutput) },
    { APITYPE_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdEnableOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdEnableOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceThresholdEnableOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Performance_Threshold_Enable(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char* targetIdentifier, char * eventType, vmApiSystemPerformanceThresholdEnableOutput** outData);


/* System_Processor_Query */
typedef struct _vmApiSystemProcessorArray {
    char * systemProcessorInfo;
} vmApiSystemProcessorArray;

typedef struct _vmApiSystemProcessorQueryOutput {
    commonOutputFields common;
    char * partitionMode;
    int systemProcessorArrayCount;
    vmApiSystemProcessorArray * systemProcessorArray;
    int errorDataLength;
    char * errorData;
} vmApiSystemProcessorQueryOutput;

/* Parser table for System_Processor_Query */
static tableLayout System_Processor_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemProcessorQueryOutput) },
    { APITYPE_INT4,               4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,         4, 10,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, partitionMode) },
    { APITYPE_ARRAY_LEN,          4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, systemProcessorArray) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, systemProcessorArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4,  STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiSystemProcessorArray) },
    { APITYPE_STRING_LEN,       15, 31,  STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiSystemProcessorArray, systemProcessorInfo) },
    { APITYPE_ERROR_BUFF_PTR,     4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,     4,  4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemProcessorQueryOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Processor_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char* targetIdentifier, vmApiSystemProcessorQueryOutput** outData);


/* System_RDR_File_Manage */
typedef struct _vmApiSystemRDRFileManageOutput {
    commonOutputFields common;
} vmApiSystemRDRFileManageOutput;

/* Parser table for System_RDR_File_Manage */
static tableLayout System_RDR_File_Manage_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemRDRFileManageOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemRDRFileManageOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemRDRFileManageOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemRDRFileManageOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_RDR_File_Manage(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemRDRFileManageOutput** outData);

/* System_SCSI_Disk_Add */
typedef struct _vmApiSystemSCSIDiskAddOutput {
    commonOutputFields common;
} vmApiSystemSCSIDiskAddOutput;

/* Parser table for System_SCSI_Disk_Add */
static tableLayout System_SCSI_Disk_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemSCSIDiskAddOutput) },
    { APITYPE_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskAddOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_SCSI_Disk_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemSCSIDiskAddOutput** outData);

/* System_SCSI_Disk_Delete */
typedef struct _vmApiSystemSCSIDiskDeleteOutput {
    commonOutputFields common;
} vmApiSystemSCSIDiskDeleteOutput;

/* Parser table for System_SCSI_Disk_Delete */
static tableLayout System_SCSI_Disk_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemSCSIDiskDeleteOutput) },
    { APITYPE_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Disk_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemSCSIDiskDeleteOutput** outData);

/* System_SCSI_Disk_Query */
typedef struct _vmApiSystemSCSIDiskQueryOutput {
    commonOutputFields common;
    int scsiInfoArrayCount;
    int fcpArrayCount;
    vmApiCStringInfo* scsiInfoStructure;
    vmApiCStringInfo* fcpStructure;
} vmApiSystemSCSIDiskQueryOutput;

/* Parser table for  System_SCSI_Disk_Query */
static  tableLayout System_SCSI_Disk_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemSCSIDiskQueryOutput) },
    { APITYPE_INT4,               4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskQueryOutput, scsiInfoStructure) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4,  STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSCSIDiskQueryOutput, scsiInfoArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4,  STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4,  STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiSystemSCSIDiskQueryOutput, fcpStructure) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4,  STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiSystemSCSIDiskQueryOutput, fcpArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4,  STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4,  STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_SCSI_Disk_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemSCSIDiskQueryOutput ** outData);


/* System_Service_Query */
typedef struct _vmApiSystemServiceQuery {
    commonOutputFields common;
    int systemServiceQueryDataLength;
    char * systemServiceQueryData;
    int errorDataLength;
    char * errorData;
} vmApiSystemServiceQueryOutput;

/* Parser table for System_Service_Query */
static tableLayout System_Service_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemServiceQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, systemServiceQueryData) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, systemServiceQueryDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemServiceQueryOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Service_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemServiceQueryOutput ** outData);

/* System_Shutdown */
typedef struct _vmApiSystemShutdownOutput {
    commonOutputFields common;
    int errorDataLength;
    char * errorData;
} vmApiSystemShutdownOutput;

/* Parser table for System_Disk_Add */
static tableLayout System_Shutdown_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemShutdownOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemShutdownOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemShutdownOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemShutdownOutput, common.reasonCode) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemShutdownOutput, errorData) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemShutdownOutput, errorDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_Shutdown(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char* targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemShutdownOutput** outData);

/* System_Spool_Utilization_Query */
typedef struct _vmApiSpoolInfomation {
    char * totalSpoolPages;
    char * totalSpoolPagesInUse;
    char * totalSpoolPercentUsed;
    int spoolVolumeArrayCount;
    vmApiCStringInfo * spoolVolumeStructure;
} vmApiSpoolInfomation;

typedef struct _vmApiSystemSpoolUtilizationQueryOutput {
    commonOutputFields common;
    int systemSpoolInformationCount;
    vmApiCStringInfo * systemSpoolInformation;
} vmApiSystemSpoolUtilizationQueryOutput;

/* Parser table for System_Spool_Utilization_Query */
static tableLayout System_Spool_Utilization_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemSpoolUtilizationQueryOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSpoolUtilizationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSpoolUtilizationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSpoolUtilizationQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSpoolUtilizationQueryOutput, systemSpoolInformation) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemSpoolUtilizationQueryOutput, systemSpoolInformationCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           1, 75, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE,       0, 0, 0, 0 }
};

int smSystem_Spool_Utilization_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiSystemSpoolUtilizationQueryOutput ** outData);

/* System_WWPN_Query */
typedef struct _vmApiSystemWWPNQueryOutput {
    commonOutputFields common;
    int wwpnArrayCount;
    vmApiCStringInfo* wwpnStructure;
} vmApiSystemWWPNQueryOutput;

/* Parser table for  System_WWPN_Query */
static  tableLayout System_WWPN_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemWWPNQueryOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemWWPNQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemWWPNQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemWWPNQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemWWPNQueryOutput, wwpnStructure) },
    { APITYPE_C_STR_ARRAY_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemWWPNQueryOutput, wwpnArrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,   4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,          4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smSystem_WWPN_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiSystemWWPNQueryOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif  // VMAPISYSTEM_H
