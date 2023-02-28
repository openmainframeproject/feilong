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
#ifndef VMAPIUNDOCUMENTED_H_
#define VMAPIUNDOCUMENTED_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* Image_IPL_Device_Query */
typedef struct _vmApiImageIplDeviceQueryOutput {
    commonOutputFields common;
    char * iplDevice;
} vmApiImageIplDeviceQueryOutput;

/* Parser table for  Image_IPL_Device_Query */
static tableLayout Image_IPL_Device_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageIplDeviceQueryOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeviceQueryOutput, common.requestId)},
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeviceQueryOutput, common.returnCode)},
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeviceQueryOutput, common.reasonCode)},
    { APITYPE_C_STR_PTR,       4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeviceQueryOutput, iplDevice)},
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smImage_IPL_Device_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, vmApiImageIplDeviceQueryOutput ** outData);

/* Image_Performance_Query */
typedef struct _vmApiImagePerformanceRecord {
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
} vmApiImagePerformanceRecord;

typedef struct _vmApiImagePerformanceQuery {
    commonOutputFields common;
    int performanceRecordCount;
    vmApiImagePerformanceRecord* performanceRecords;
} vmApiImagePerformanceQueryOutput;

/* Parser table for Image_Performance_Query */
static tableLayout Image_Performance_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImagePerformanceQueryOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePerformanceQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePerformanceQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePerformanceQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_COUNT,        4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePerformanceQueryOutput, performanceRecords) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePerformanceQueryOutput, performanceRecordCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImagePerformanceRecord) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, recordVersion) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, guestFlags) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, usedCPUTime) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, elapsedTime) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, minMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, maxMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, sharedMemory) },
    { APITYPE_INT8,               8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, usedMemory) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, activeCPUsInCEC) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, logicalCPUsInVM) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, guestCPUs) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, minCPUCount) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, maxCPULimit) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, processorShare) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesCPUInUse) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesCPUDelay) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesPageWait) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesIdle) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesOther) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, samplesTotal) },
    { APITYPE_FIXED_STR_PTR,      8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImagePerformanceRecord, guestName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Performance_Query(struct _vmApiInternalContext* vmapiContextP, char* userid, int passwordLength, char* password,
        char* targetIdentifier, int guestCount, vmApiCStringInfo guests[], vmApiImagePerformanceQueryOutput** outData);

/* IPaddr_Get */
typedef struct _vmApiIPAddr_GetOutput {
    commonOutputFields common;
    int ipCount;
    vmApiCStringInfo * ipList;  // Should only be one item in the list
} vmApiIPaddrGetOutput;

/* Parser table for  IPaddr_Get */
static tableLayout IPaddr_Get_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiIPaddrGetOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiIPaddrGetOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiIPaddrGetOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiIPaddrGetOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiIPaddrGetOutput, ipList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiIPaddrGetOutput, ipCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smIPaddr_Get(struct _vmApiInternalContext* vmapiContextP, vmApiIPaddrGetOutput ** outData);

/* System_Info_Query */
typedef struct _vmApiSystemInfoQueryOutput {
    commonOutputFields common;
    char * timezone;
    char * time;
    char * vmVersion;
    char * cpGenTime;
    char * cpIplTime;
    char * realStorageSize;
} vmApiSystemInfoQueryOutput;

/* Parser table for  Virtual_Network_Query_OSA */
static tableLayout System_Info_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemInfoQueryOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_PTR,       4, 43, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, timezone) },
    { APITYPE_C_STR_PTR,       4, 43, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, time) },
    { APITYPE_C_STR_PTR,       4, 80, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, vmVersion) },
    { APITYPE_C_STR_PTR,       4, 43, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, cpGenTime) },
    { APITYPE_C_STR_PTR,       4, 43, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, cpIplTime) },
    { APITYPE_C_STR_PTR,       4, 80, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemInfoQueryOutput, realStorageSize) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Info_Query(struct _vmApiInternalContext* vmapiContextP, vmApiSystemInfoQueryOutput ** outData);

/* System_IO_Query */
typedef struct _vmApiSystemIoQueryOutput {
    commonOutputFields common;
    int chipidCount;
    vmApiCStringInfo * chipidList;
} vmApiSystemIoQueryOutput;

/* Parser table for  Virtual_Network_Query_OSA */
static tableLayout System_IO_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemIoQueryOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemIoQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemIoQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemIoQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemIoQueryOutput, chipidList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemIoQueryOutput, chipidCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_IO_Query(struct _vmApiInternalContext* vmapiContextP, char * realDeviceAddress, vmApiSystemIoQueryOutput ** outData);

/* System_Performance_Info_Query */
typedef struct _vmApiSystemPerformanceInfoQuery {
    commonOutputFields common;
    int performanceFieldCount;
    vmApiCStringInfo* performanceInfo;
} vmApiSystemPerformanceInfoQueryOutput;

/* Parser table for System_Performance_Info_Query */
static tableLayout System_Performance_Info_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiSystemPerformanceInfoQueryOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInfoQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInfoQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInfoQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInfoQueryOutput, performanceInfo) },
    { APITYPE_C_STR_ARRAY_COUNT,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiSystemPerformanceInfoQueryOutput, performanceFieldCount) },
    { APITYPE_C_STR_STRUCT_LEN,    4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smSystem_Performance_Info_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiSystemPerformanceInfoQueryOutput** outData);

/* Virtual_Network_Query_LAN */
typedef struct _vmApiVirtualNetworkQueryLanOutput {
    commonOutputFields common;
    int lanCount;
    vmApiCStringInfo * lanList;
} vmApiVirtualNetworkQueryLanOutput;

/* Parser table for  Virtual_Network_Query_LAN */
static tableLayout Virtual_Network_Query_LAN_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkQueryLanOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryLanOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryLanOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryLanOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryLanOutput, lanList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryLanOutput, lanCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Query_LAN(struct _vmApiInternalContext* vmapiContextP, vmApiVirtualNetworkQueryLanOutput ** outData);

/* Virtual_Network_Query_OSA */
typedef struct _vmApiVirtualNetworkQueryOsaOutput {
    commonOutputFields common;
    int osaCount;
    vmApiCStringInfo * osaList;
} vmApiVirtualNetworkQueryOsaOutput;

/* Parser table for  Virtual_Network_Query_OSA */
static tableLayout Virtual_Network_Query_OSA_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkQueryOsaOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryOsaOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryOsaOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryOsaOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryOsaOutput, osaList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkQueryOsaOutput, osaCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Query_OSA(struct _vmApiInternalContext* vmapiContextP, vmApiVirtualNetworkQueryOsaOutput ** outData);

/* Virtual_Network_Vswitch_Query_IUO_Stats */
typedef struct _vmApiVirtualNetworkVswitchQueryIUOStatsOutput {
    commonOutputFields common;
    int stringCount;
    vmApiCStringInfo * stringList;
} vmApiVirtualNetworkVswitchQueryIUOStatsOutput;

/* Parser table for Virtual_Network_VSwitch_Query_IUO_Stats */
static tableLayout Virtual_Network_Vswitch_Query_IUO_Stats_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,   4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput) },
    { APITYPE_INT4,                4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,     4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput, stringList) },
    { APITYPE_C_STR_ARRAY_COUNT,   4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryIUOStatsOutput, stringCount) },
    { APITYPE_C_STR_STRUCT_LEN,    4,   4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           4,   4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Query_IUO_Stats(
        struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier,
        int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchQueryIUOStatsOutput ** outData);

/* xCAT_Commands_IUO */
typedef struct _vmApiXCATCommandsIUOOutput {
    commonOutputFields common;
    int XCATCommandsIUODataLength;
    char * XCATCommandsIUOData;
    int errorDataLength;
    char * errorData;
} vmApiXCATCommandsIUOOutput;

/* Parser table for xCAT_Commands_IUO */
static tableLayout xCAT_Commands_IUO_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiXCATCommandsIUOOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, common.reasonCode) },
    { APITYPE_CHARBUF_PTR,     0, -1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, XCATCommandsIUOData) },
    { APITYPE_CHARBUF_COUNT,   4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, XCATCommandsIUODataLength) },
    { APITYPE_ERROR_BUFF_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, errorDataLength) },
    { APITYPE_ERROR_BUFF_PTR,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiXCATCommandsIUOOutput, errorData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0}
};

int smXCAT_Commands_IUO(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * command, vmApiXCATCommandsIUOOutput ** outData);

#endif  /* VMAPIUNDOCUMENTED_H_ */
