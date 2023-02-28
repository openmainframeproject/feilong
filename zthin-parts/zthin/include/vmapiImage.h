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
#ifndef _VMAPI_IMAGE_H
#define _VMAPI_IMAGE_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Image_Activate */
typedef struct _vmApiImageFailing {
    char * imageName;
    int returnCode;
    int reasonCode;
} vmApiImageFailing;

typedef struct _vmApiImageActivate {
    commonOutputFields common;
    int activated;
    int notActivated;
    int failingArrayCount;
    vmApiImageFailing * failList;
} vmApiImageActivateOutput;

/* Parser table for Image_Activate */
static tableLayout Image_Activate_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageActivateOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, common.reasonCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, activated) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, notActivated) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, failList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActivateOutput, failingArrayCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageFailing) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, imageName) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, returnCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Activate(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageActivateOutput ** outData);

/* Image_Active_Configuration_Query */
typedef struct _vmApiImageCpuInfo {
    int cpuNumber;  // Or address
    char * cpuId;
    char cpuBase;  // Only supplied for Image_CPU_Query
    char cpuStatus;
    char cpuType;  // Only supplied for Image_CPU_Query
} vmApiImageCpuInfo;

typedef struct _vmApiImageDeviceInfo {
    char deviceType;
    char * deviceAddress;
} vmApiImageDeviceInfo;

typedef struct _vmApiImageActiveConfigurationQuery {
    commonOutputFields common;
    int memorySize;
    char memoryUnit;
    char shareType;
    char * shareValue;
    int numberOfCpus;
    int cpuInfoCount;
    vmApiImageCpuInfo * cpuList;
    int deviceCount;
    vmApiImageDeviceInfo * deviceList;
} vmApiImageActiveConfigurationQueryOutput;

/* Parser table for  Image_Active_Configuration_Query */
static tableLayout Image_Active_Configuration_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageActiveConfigurationQueryOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, common.reasonCode) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, memorySize) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, memoryUnit) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, shareType) },
    { APITYPE_STRING_LEN,         1,  5, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, shareValue) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, numberOfCpus) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, cpuList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, cpuInfoCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageCpuInfo) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuNumber) },
    { APITYPE_STRING_LEN,         1, 16, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuId) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuStatus) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, deviceList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageActiveConfigurationQueryOutput, deviceCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_2, NEST_LEVEL_1, sizeof(vmApiImageDeviceInfo) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_2, NEST_LEVEL_1, offsetof(vmApiImageDeviceInfo, deviceType) },
    { APITYPE_STRING_LEN,         4, 16, STRUCT_INDX_2, NEST_LEVEL_1, offsetof(vmApiImageDeviceInfo, deviceAddress) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Active_Configuration_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiImageActiveConfigurationQueryOutput ** outData);

/* Image_CPU_Define */
typedef struct _vmApiImageCpuDefineOutput {
    commonOutputFields common;
} vmApiImageCpuDefineOutput;

/* Parser table for Image_CPU_Define */
static tableLayout Image_CPU_Define_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuDefineOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Define(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * cpuAddress, char cpuType, vmApiImageCpuDefineOutput ** outData);

/* Image_CPU_Define_DM */
typedef struct _vmApiImageCpuDefineDmOutput {
    commonOutputFields common;
} vmApiImageCpuDefineDmOutput;

/* Parser table for Image_CPU_Define_DM */
static tableLayout Image_CPU_Define_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuDefineDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDefineDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Define_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * cpuAddress, char baseCpu, char * cpuId, char dedicateCpu, char cryptoCpu,
        vmApiImageCpuDefineDmOutput ** outData);

/* Image_CPU_Delete */
typedef struct _vmApiImageCpuDeleteOutput {
    commonOutputFields common;
} vmApiImageCpuDeleteOutput;

/* Parser table for Image_CPU_Delete */
static tableLayout Image_CPU_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * cpuAddress, vmApiImageCpuDeleteOutput ** outData);

/* Image_CPU_Delete_DM */
typedef struct _vmApiImageCpuDeleteDmOutput {
    commonOutputFields common;
} vmApiImageCpuDeleteDmOutput;

/* Parser table for Image_CPU_Delete_DM */
static tableLayout Image_CPU_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * cpuAddress, vmApiImageCpuDeleteDmOutput ** outData);

/* Image_CPU_Query */
typedef struct _vmApiImageCpuQuery {
    commonOutputFields common;
    int numberOfCpus;
    int cpuInfoCount;
    vmApiImageCpuInfo * cpuList;
} vmApiImageCpuQueryOutput;

/* Parser table for Image_CPU_Query */
static tableLayout Image_CPU_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuQueryOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, common.reasonCode) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, numberOfCpus) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, cpuList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryOutput, cpuInfoCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageCpuInfo) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuNumber) },
    { APITYPE_STRING_LEN,         1, 16, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuId) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuBase) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuStatus) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageCpuInfo, cpuType) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageCpuQueryOutput ** outData);

/* Image_CPU_Query_DM */
typedef struct _vmApiImageCpuQueryDm {
    commonOutputFields common;
    char * cpuAddress;
    char baseCpu;
    char * cpuId;
    char cpuDedicate;
    char cpuCrypto;
} vmApiImageCpuQueryDmOutput;

/* Parser table for Image_CPU_Query_DM */
static tableLayout Image_CPU_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuQueryDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,      1, 2, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, cpuAddress) },
    { APITYPE_INT1,            1, 1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, baseCpu) },
    { APITYPE_STRING_LEN,      0, 6, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, cpuId) },
    { APITYPE_INT1,            1, 1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, cpuDedicate) },
    { APITYPE_INT1,            1, 1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuQueryDmOutput, cpuCrypto) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * cpuAddress, vmApiImageCpuQueryDmOutput ** outData);

/* Image_CPU_Set_Maximum_DM */
typedef struct _vmApiImageCpuSetMaximumDmOutput {
    commonOutputFields common;
} vmApiImageCpuSetMaximumDmOutput;

/* Parser table for Image_CPU_Set_Maximum_DM */
static tableLayout Image_CPU_Set_Maximum_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCpuSetMaximumDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuSetMaximumDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuSetMaximumDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCpuSetMaximumDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_CPU_Set_Maximum_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int maxCpus, vmApiImageCpuSetMaximumDmOutput ** outData);

/* Image_Create_DM */
typedef struct _vmApiImageRecord {
    int imageRecordLength;
    char * imageRecord;
} vmApiImageRecord;

typedef struct _vmApiImageCreateDm {
    commonOutputFields common;
    int operationId;
} vmApiImageCreateDmOutput;

/* Parser table for Image_Create_DM */
static tableLayout Image_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCreateDmOutput, common.reasonCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageCreateDmOutput, operationId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * prototypeName, int initialPasswordLength, char * initialPassword,
        char * initialAccountNumber, int imageRecordCount, vmApiImageRecord * imageRecordList, vmApiImageCreateDmOutput ** outData);

/* Image_Deactivate */
typedef struct _vmApiImageDeactivate {
    commonOutputFields common;
    int deactivated;
    int notDeactivated;
    int failingArrayCount;
    vmApiImageFailing * failList;
} vmApiImageDeactivateOutput;

/* Parser table for Image_Deactivate */
static tableLayout Image_Deactivate_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeactivateOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, common.reasonCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, deactivated) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, notDeactivated) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, failList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeactivateOutput, failingArrayCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageFailing) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, imageName) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, returnCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Deactivate(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * forceTimeLength, vmApiImageDeactivateOutput ** outData);

/* Image_Delete_DM */
typedef struct _vmApiImageDeleteDm {
    commonOutputFields common;
    int operationId;
} vmApiImageDeleteDmOutput;

/* Parser table for Image_Delete_DM */
static tableLayout Image_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeleteDmOutput, common.reasonCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeleteDmOutput, operationId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char dataSecurityErase, vmApiImageDeleteDmOutput ** outData);

/* Image_Device_Dedicate */
typedef struct _vmApiImageDeviceDedicateOutput {
    commonOutputFields common;
} vmApiImageDeviceDedicateOutput;

/* Parser table for Image_Device_Dedicate */
static tableLayout Image_Device_Dedicate_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeviceDedicateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Device_Dedicate(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, char * realDeviceNumber, char readonly,
        vmApiImageDeviceDedicateOutput ** outData);

/* Image_Device_Dedicate_DM */
typedef struct _vmApiImageDeviceDedicateDmOutput {
    commonOutputFields common;
} vmApiImageDeviceDedicateDmOutput;

/* Parser table for Image_Device_Dedicate_DM */
static tableLayout Image_Device_Dedicate_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeviceDedicateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceDedicateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Device_Dedicate_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, char * realDeviceNumber, char readonly,
        vmApiImageDeviceDedicateDmOutput ** outData);

/* Image_Device_Reset */
typedef struct _vmApiImageDeviceResetOutput {
    commonOutputFields common;
} vmApiImageDeviceResetOutput;

/* Parser table for Image_Device_Reset */
static tableLayout Image_Device_Reset_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeviceResetOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceResetOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceResetOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceResetOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Device_Reset(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, vmApiImageDeviceResetOutput ** outData);

/* Image_Device_Undedicate */
typedef struct _vmApiImageDeviceUndedicateOutput {
    commonOutputFields common;
} vmApiImageDeviceUndedicateOutput;

/* Parser table for Image_Device_Undedicate */
static tableLayout Image_Device_Undedicate_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeviceUndedicateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Device_Undedicate(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, vmApiImageDeviceUndedicateOutput ** outData);

/* Image_Device_Undedicate_DM */
typedef struct _vmApiImageDeviceUndedicateDmOutput {
    commonOutputFields common;
} vmApiImageDeviceUndedicateDmOutput;

/* Parser table for Image_Device_Undedicate_DM */
static tableLayout Image_Device_Undedicate_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDeviceUndedicateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDeviceUndedicateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Device_Undedicate_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, vmApiImageDeviceUndedicateDmOutput ** outData);

/* Image_Disk_Copy */
typedef struct _vmApiImageDiskCopyOutput {
    commonOutputFields common;
} vmApiImageDiskCopyOutput;

/* Parser table for Image_Disk_Copy */
static tableLayout Image_Disk_Copy_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskCopyOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Copy(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, vmApiImageDiskCopyOutput ** outData);

/* Image_Disk_Copy_DM */
typedef struct _vmApiImageDiskCopyDm {
    commonOutputFields common;
    int operationId;
} vmApiImageDiskCopyDmOutput;

/* Parser table for Image_Disk_Copy_DM */
static tableLayout Image_Disk_Copy_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskCopyDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyDmOutput, common.reasonCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCopyDmOutput, operationId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Copy_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char * sourceImageName, char * sourceImageDiskNumber,
        char * imageDiskAllocationType, char * allocationAreaName, char * imageDiskMode, char * readPassword,
        char * writePassword, char * multiPassword, vmApiImageDiskCopyDmOutput ** outData);

/* Image_Disk_Create */
typedef struct _vmApiImageDiskCreateOutput {
    commonOutputFields common;
} vmApiImageDiskCreateOutput;

/* Parser table for Image_Disk_Create */
static tableLayout Image_Disk_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char * imageDiskMode, vmApiImageDiskCreateOutput ** outData);

/* Image_Disk_Create_DM */
typedef struct _vmApiImageDiskCreateDm {
    commonOutputFields common;
    int operationId;
} vmApiImageDiskCreateDmOutput;

/* Parser table for Image_Disk_Create_DM */
static tableLayout Image_Disk_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateDmOutput, common.reasonCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskCreateDmOutput, operationId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char * imageDiskDeviceType, char * imageDiskAllocationType,
        char * allocationAreaNameOrVolser, char allocationUnitSize, int imageDiskSize, char * imageDiskMode, char imageDiskFormatting,
        char * imageDiskLabel, char * readPassword, char * writePassword, char * multiPassword,
        vmApiImageDiskCreateDmOutput ** outData);

/* Image_Disk_Delete */
typedef struct _vmApiImageDiskDeleteOutput {
    commonOutputFields common;
} vmApiImageDiskDeleteOutput;

/* Parser table for Image_Disk_Delete */
static tableLayout Image_Disk_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, vmApiImageDiskDeleteOutput ** outData);

/* Image_Disk_Delete_DM */
typedef struct _vmApiImageDiskDeleteDm {
    commonOutputFields common;
    int operationId;
} vmApiImageDiskDeleteDmOutput;

/* Parser table for Image_Disk_Delete_DM */
static tableLayout Image_Disk_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteDmOutput, common.reasonCode) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskDeleteDmOutput, operationId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char dataSecurityErase, vmApiImageDiskDeleteDmOutput ** outData);

/* Image_Disk_Query */
typedef struct _vmApiImageDiskDASD {
    char * vdev;
    char * rdev;
    char accessType;
    char * devtype;
    long long size;
    char cylOrBlocks;
    char * volid;
} vmApiImageDiskDASD;

typedef struct _vmApiImageDiskQuery {
    commonOutputFields common;
    int dasdCount;
    vmApiImageDiskDASD * dasdList;
} vmApiImageDiskQueryOutput;

/* Parser table for Image_Disk_Query */
static tableLayout Image_Disk_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskQueryOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_NO_LENGTH,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskQueryOutput, dasdList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskQueryOutput, dasdCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageDiskDASD) },
    { APITYPE_FIXED_STR_PTR,       4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, vdev) },
    { APITYPE_FIXED_STR_PTR,       4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, rdev) },
    { APITYPE_INT1,                1, 1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, accessType) },
    { APITYPE_FIXED_STR_PTR,       4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, devtype) },
    { APITYPE_INT8,                8, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, size) },
    { APITYPE_INT1,                1, 1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, cylOrBlocks) },
    { APITYPE_C_STR_PTR,           1, 6, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDiskDASD, volid) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiImageDiskQueryOutput ** outData);

/* Image_Disk_Share */
typedef struct _vmApiImageDiskShareOutput {
    commonOutputFields common;
    int operationId;
} vmApiImageDiskShareOutput;

/* Parser table for Image_Disk_Share */
static tableLayout Image_Disk_Share_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskShareOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Share(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char * targetImageName, char * targetImageDiskNumber, char * readWriteMode,
        char * optionalPassword, vmApiImageDiskShareOutput ** outData);

/* Image_Disk_Share_DM */
typedef struct _vmApiImageDiskShareDmOutput {
    commonOutputFields common;
    int operationId;
} vmApiImageDiskShareDmOutput;

/* Parser table for Image_Disk_Share_DM */
static tableLayout Image_Disk_Share_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskShareDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskShareDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Share_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * targetImageDiskNumber, char * targetImageName, char * imageDiskNumber, char * readWriteMode,
        char * optionalPassword, vmApiImageDiskShareDmOutput ** outData);

/* Image_Disk_Unshare */
typedef struct _vmApiImageDiskUnshareOutput {
    commonOutputFields common;
} vmApiImageDiskUnshareOutput;

/* Parser table for Image_Disk_Unshare */
static tableLayout Image_Disk_Unshare_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskUnshareOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Unshare(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, vmApiImageDiskUnshareOutput ** outData);

/* Image_Disk_Unshare_DM */
typedef struct _vmApiImageDiskUnshareDmOutput {
    commonOutputFields common;
} vmApiImageDiskUnshareDmOutput;

/* Parser table for Image_Disk_Unshare_DM */
static tableLayout Image_Disk_Unshare_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageDiskUnshareDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageDiskUnshareDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Disk_Unshare_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDiskNumber, char * targetImageName, char * targetImageDiskNumber,
        vmApiImageDiskUnshareDmOutput ** outData);

/* Image_IPL_Delete_DM */
typedef struct _vmApiImageIplDeleteDmOutput {
    commonOutputFields common;
} vmApiImageIplDeleteDmOutput;

/* Parser table for Image_IPL_Delete_DM  */
static tableLayout Image_IPL_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageIplDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_IPL_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageIplDeleteDmOutput ** outData);

/* Image_IPL_Query_DM */
typedef struct _vmApiImageIplQueryDm {
    commonOutputFields common;
    char * savedSystem;
    char * loadParameter;
    char * parameters;
} vmApiImageIplQueryDmOutput;

/* Parser table for Image_IPL_Query_DM */
static tableLayout Image_IPL_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageIplQueryDmOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,      1,  8, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, savedSystem) },
    { APITYPE_STRING_LEN,      0, 10, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, loadParameter) },
    { APITYPE_STRING_LEN,      0, 64, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplQueryDmOutput, parameters) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_IPL_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageIplQueryDmOutput ** outData);

/* Image_IPL_Set_DM */
typedef struct _vmApiImageIplSetDmOutput {
    commonOutputFields common;
} vmApiImageIplSetDmOutput;

/* Parser table for Image_IPL_Set_DM  */
static tableLayout Image_IPL_Set_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageIplSetDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplSetDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplSetDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageIplSetDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_IPL_Set_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * savedSystem, char * loadParameter, char * parameterString,
        vmApiImageIplSetDmOutput ** outData);

/* Image_Lock_DM */
typedef struct _vmApiImageLockDmOutput {
    commonOutputFields common;
} vmApiImageLockDmOutput;

/* Parser table for Image_Lock_DM  */
static tableLayout Image_Lock_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageLockDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Lock_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * deviceAddress, vmApiImageLockDmOutput ** outData);

/* Image_Lock_Query_DM */
typedef struct _vmApiImageDevLockInfoRecord {
    char * devAddressDevLockedBy;
} vmApiImageDevLockInfoRecord;

typedef struct _vmApiImageLockQueryDm {
    commonOutputFields common;
    int lockInfoStructureLength;
    char * lockedTypeImageLockedBy;
    int lockedDevArrayLength;
    int imageDevLockInfoRecordCount;
    vmApiImageDevLockInfoRecord * lockDevList;
} vmApiImageLockQueryDmOutput;

/* Parser table for Image_Lock_Query_DM */
static tableLayout Image_Lock_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageLockQueryDmOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, common.reasonCode) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, lockInfoStructureLength) },
    { APITYPE_C_STR_PTR,           1, 17, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, lockedTypeImageLockedBy) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, lockedDevArrayLength) },
    { APITYPE_ARRAY_NO_LENGTH,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, lockDevList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageLockQueryDmOutput, imageDevLockInfoRecordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageDevLockInfoRecord) },
    { APITYPE_C_STR_PTR,           1, 13, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageDevLockInfoRecord, devAddressDevLockedBy) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Lock_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageLockQueryDmOutput ** outData);

/* Image_MDISK_Link_Query */
typedef struct _vmApiImageMDISKLinkQueryOutput {
    commonOutputFields common;
    int mdiskLinkCount;
    vmApiCStringInfo * mdiskLinkList;
} vmApiImageMDISKLinkQueryOutput;

/* Parser table for Image_MDISK_Link_Query */
static tableLayout Image_MDISK_Link_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageMDISKLinkQueryOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageMDISKLinkQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageMDISKLinkQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageMDISKLinkQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageMDISKLinkQueryOutput, mdiskLinkList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageMDISKLinkQueryOutput, mdiskLinkCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           1, 29, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_MDISK_Link_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * vdev, vmApiImageMDISKLinkQueryOutput ** outData);

/* Image_Name_Query_DM */
typedef struct _vmApiImageName {
    char * imageName;
} vmApiImageName;

typedef struct _vmApiImageNameQueryDm {
    commonOutputFields common;
    int nameCount;
    vmApiImageName * nameList;
} vmApiImageNameQueryDmOutput;

/* Parser table for Image_Name_Query_DM */
static tableLayout Image_Name_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageNameQueryDmOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageNameQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageNameQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageNameQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageNameQueryDmOutput, nameList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageNameQueryDmOutput, nameCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageName) },
    { APITYPE_STRING_LEN,          1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageName, imageName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Name_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageNameQueryDmOutput ** outData);

/* Image_Password_Set_DM */
typedef struct _vmApiImagePasswordSetDmOutput {
    commonOutputFields common;
} vmApiImagePasswordSetDmOutput;

/* Parser table for Image_Password_Set_DM   */
static tableLayout Image_Password_Set_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImagePasswordSetDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePasswordSetDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePasswordSetDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePasswordSetDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Password_Set_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int imagePasswordLength, char * imagePassword, vmApiImagePasswordSetDmOutput ** outData);

/* Image_Pause */
typedef struct _vmApiImagePauseOutput {
    commonOutputFields common;
} vmApiImagePauseOutput;

/* Parser table for Image_Pause   */
static tableLayout Image_Pause_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImagePauseOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePauseOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePauseOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImagePauseOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Pause(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imagePauseOrBegin, vmApiImagePauseOutput ** outData);

/* Image_Query_Activate_Time */
typedef struct _vmApiImageQueryActivateTime {
    commonOutputFields common;
    char * imageName;
    char * activationDate;
    char * activationTime;
} vmApiImageQueryActivateTimeOutput;

/* Parser table for Image_Query_Activate_Time */
static tableLayout Image_Query_Activate_Time_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageQueryActivateTimeOutput) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, common.requestId) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, common.returnCode) },
    { APITYPE_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,      1,  8, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, imageName) },
    { APITYPE_STRING_LEN,      8, 10, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, activationDate) },
    { APITYPE_STRING_LEN,      8,  8, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryActivateTimeOutput, activationTime) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Query_Activate_Time(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char dateFormat, vmApiImageQueryActivateTimeOutput ** outData);

/* Image_Query_DM */
typedef struct _vmApiImageQueryDm {
    commonOutputFields common;
    int imageRecordCount;
    vmApiImageRecord * imageRecordList;
} vmApiImageQueryDmOutput;

/* Parser table for Image_Query_DM */
static tableLayout Image_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageQueryDmOutput) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryDmOutput, common.requestId) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryDmOutput, common.returnCode) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryDmOutput, imageRecordList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageQueryDmOutput, imageRecordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageRecord) },
    { APITYPE_CHARBUF_LEN,         1, 80, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageRecord, imageRecord) },
    { APITYPE_CHARBUF_COUNT,       4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageRecord, imageRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageQueryDmOutput ** outData, bool readFromCache);

/* Image_Recycle */
typedef struct _vmApiImageRecycle {
    commonOutputFields common;
    int recycled;
    int notRecycled;
    int failingArrayCount;
    vmApiImageFailing * failList;
} vmApiImageRecycleOutput;

/* Parser table for Image_Recycle */
static tableLayout Image_Recycle_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageRecycleOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, common.reasonCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, recycled) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, notRecycled) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, failList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageRecycleOutput, failingArrayCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageFailing) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, imageName) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, returnCode) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageFailing, reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Recycle(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageRecycleOutput ** outData);

/* Image_Replace_DM */
typedef struct _vmApiImageReplaceDmOutput {
    commonOutputFields common;
} vmApiImageReplaceDmOutput;

/* Parser table for Image_Replace_DM   */
static tableLayout Image_Replace_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageReplaceDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageReplaceDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageReplaceDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageReplaceDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};
int smImage_Replace_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int imageRecordArrayCount, vmApiImageRecord * imageRecordList, vmApiImageReplaceDmOutput ** outData);

/* Image_SCSI_Characteristics_Define_DM */
typedef struct _vmApiImageScsiCharacteristicsDefineDmOutput {
    commonOutputFields common;
} vmApiImageScsiCharacteristicsDefineDmOutput;

/* Parser table for Image_SCSI_Characteristics_Define_DM    */
static tableLayout Image_SCSI_Characteristics_Define_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageScsiCharacteristicsDefineDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsDefineDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsDefineDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsDefineDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_SCSI_Characteristics_Define_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * bootProgram, char * brLba, char * lun, char * portName,
        char scpDatatype, int scpDataLength, char * scpData, vmApiImageScsiCharacteristicsDefineDmOutput ** outData);

/* Image_SCSI_Characteristics_Query_DM */
typedef struct _vmApiImageScsiCharacteristicsQueryDm {
    commonOutputFields common;
    char * bootProgramNumber;
    char * br_LBA;
    char * lun;
    char * port;
    char   scpDataType;
    char * scpData;
    int scpDataLength;
} vmApiImageScsiCharacteristicsQueryDmOutput;

/* Parser table for Image_SCSI_Characteristics_Query_DM */
static tableLayout Image_SCSI_Characteristics_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4,    4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageScsiCharacteristicsQueryDmOutput) },
    { APITYPE_INT4,            4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, common.reasonCode) },
    { APITYPE_STRING_LEN,      0,    6, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, bootProgramNumber) },
    { APITYPE_STRING_LEN,      0,   16, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, br_LBA) },
    { APITYPE_STRING_LEN,      0,   16, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, lun) },
    { APITYPE_STRING_LEN,      0,   16, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, port) },
    { APITYPE_INT1,            1,    1, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, scpDataType) },
    { APITYPE_CHARBUF_LEN,     0, 4102, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, scpData) },
    { APITYPE_CHARBUF_COUNT,   0,    4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageScsiCharacteristicsQueryDmOutput, scpDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_SCSI_Characteristics_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiImageScsiCharacteristicsQueryDmOutput ** outData);

/* Image_Status_Query */
typedef struct _vmApiImageStatusQuery {
    commonOutputFields common;
    int imageNameCount;
    vmApiImageName * imageNameList;
} vmApiImageStatusQueryOutput;

/* Parser table for Image_Status_Query */
static tableLayout Image_Status_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageStatusQueryOutput) },
    { APITYPE_INT4,                4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageStatusQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageStatusQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageStatusQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageStatusQueryOutput, imageNameList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageStatusQueryOutput, imageNameCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageName) },
    { APITYPE_STRING_LEN,          1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageName, imageName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Status_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageStatusQueryOutput ** outData);

/* Image_Unlock_DM */
typedef struct _vmApiImageUnlockDmOutput {
    commonOutputFields common;
} vmApiImageUnlockDmOutput;

/* Parser table for Image_Unlock_DM     */
static tableLayout Image_Unlock_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageUnlockDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageUnlockDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageUnlockDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageUnlockDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Unlock_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * deviceAddress, vmApiImageUnlockDmOutput ** outData);

/* Image_Volume_Add */
typedef struct _vmApiImageVolumeAddOutput {
    commonOutputFields common;
} vmApiImageVolumeAddOutput;

/* Parser table for Image_Volume_Add  */
static tableLayout Image_Volume_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeAddOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeAddOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumer, char * imageVolumeLabel, char * systemConfigName,
        char * systemConfigType, char * parmDiskOwner, char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName,
        char * altSystemConfigType, char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword,
        vmApiImageVolumeAddOutput ** outData);

/* Image_Volume_Delete */
typedef struct _vmApiImageVolumeDeleteOutput {
    commonOutputFields common;
} vmApiImageVolumeDeleteOutput;

/* Parser table for Image_Volume_Delete     */
static tableLayout Image_Volume_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumer, char * imageVolumeLabel, char * systemConfigName,
        char * systemConfigType, char * parmDiskOwner, char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName,
        char * altSystemConfigType, char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword,
        vmApiImageVolumeDeleteOutput ** outData);

/* Image_Volume_Share */
typedef struct _vmApiImageVolumeShareOutput {
    commonOutputFields common;
} vmApiImageVolumeShareOutput;

/* Parser table for Image_Volume_Share     */
static tableLayout Image_Volume_Share_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeShareOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeShareOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeShareOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeShareOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Share(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int keyValueCount, char ** keyValueArray, vmApiImageVolumeShareOutput ** outData);

/* Image_Volume_Space_Define_DM */
typedef struct _vmApiImageVolumeSpaceDefineDmOutput {
    commonOutputFields common;
} vmApiImageVolumeSpaceDefineDmOutput;

/* Parser table for Image_Volume_Space_Define_DM  */
static tableLayout Image_Volume_Space_Define_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeSpaceDefineDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Space_Define_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char functionType, char * regionName, char * imageVolumeId, int startCyl, int regionSize,
        char * groupName, char deviceType, vmApiImageVolumeSpaceDefineDmOutput ** outData);

/* Image_Volume_Space_Define_Extended_DM */
typedef struct _vmApiImageVolumeSpaceDefineExtendedDmOutput {
    commonOutputFields common;
} vmApiImageVolumeSpaceDefineExtendedDmOutput;

/* Parser table for Image_Volume_Space_Define_Extended_DM  */
static tableLayout Image_Volume_Space_Define_Extended_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeSpaceDefineExtendedDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineExtendedDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineExtendedDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceDefineExtendedDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Space_Define_Extended_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiImageVolumeSpaceDefineExtendedDmOutput ** outData);

/* Image_Volume_Space_Query_DM */
typedef struct _vmApiImageVolumeSpaceQueryDm {
    commonOutputFields common;
    int recordCount;
    vmApiImageRecord * recordList;
} vmApiImageVolumeSpaceQueryDmOutput;

/* Parser table for Image_Volumn_Space_Query_DM */
static tableLayout Image_Volume_Space_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeSpaceQueryDmOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceQueryDmOutput, common.requestId) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceQueryDmOutput, common.returnCode) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceQueryDmOutput, recordList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceQueryDmOutput, recordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiImageRecord) },
    { APITYPE_CHARBUF_LEN,         1, -1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageRecord, imageRecord) },
    { APITYPE_CHARBUF_COUNT,       4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiImageRecord, imageRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Space_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char queryType, char entryType, char * entryNames, vmApiImageVolumeSpaceQueryDmOutput ** outData);

/* Image_Volume_Space_Query_Extended_DM */
typedef struct _vmApiVolumeSpaceQueryExtendedDmOutput {
    commonOutputFields common;
    int volumeSpaceCount;
    vmApiCStringInfo * volumeSpaceList;
} vmApiVolumeSpaceQueryExtendedDmOutput;

/* Parser table for  Image_Volume_Space_Query_Extended_DM */
static tableLayout Image_Volume_Space_Query_Extended_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVolumeSpaceQueryExtendedDmOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVolumeSpaceQueryExtendedDmOutput, common.requestId) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVolumeSpaceQueryExtendedDmOutput, common.returnCode) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVolumeSpaceQueryExtendedDmOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVolumeSpaceQueryExtendedDmOutput, volumeSpaceList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVolumeSpaceQueryExtendedDmOutput, volumeSpaceCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Space_Query_Extended_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVolumeSpaceQueryExtendedDmOutput ** outData);

/* Image_Volume_Space_Remove_DM */
typedef struct _vmApiImageVolumeSpaceRemoveDmOutput {
    commonOutputFields common;
} vmApiImageVolumeSpaceRemoveDmOutput;

/* Parser table for Image_Volume_Space_Remove_DM  */
static tableLayout Image_Volume_Space_Remove_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageVolumeSpaceRemoveDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceRemoveDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceRemoveDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageVolumeSpaceRemoveDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Volume_Space_Remove_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char functionType, char * regionName, char * imageVolumeId, char * groupName,
        vmApiImageVolumeSpaceRemoveDmOutput ** outData);

typedef struct _vmApiImageConsoleGetOutput {
    commonOutputFields common;
} vmApiImageConsoleGetOutput;

/* Parser table for Image_Console_Get  */
static tableLayout Image_Console_Get_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiImageConsoleGetOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageConsoleGetOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageConsoleGetOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiImageConsoleGetOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smImage_Console_Get(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiImageConsoleGetOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
