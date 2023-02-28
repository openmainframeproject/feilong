/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017,2018 IBM Corporation
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
#ifndef _VMAPI_VIRTUAL_H
#define _VMAPI_VIRTUAL_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Virtual_Channel_Connection_Create */
typedef struct _vmApiVirtualChannelConnectionCreateOutput {
    commonOutputFields common;
} vmApiVirtualChannelConnectionCreateOutput;

/* Parser table for Virtual_Channel_Connection_Create */
static  tableLayout Virtual_Channel_Connection_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualChannelConnectionCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Channel_Connection_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * coupledImageName,
        char * coupledImageDeviceNumber, vmApiVirtualChannelConnectionCreateOutput ** outData);

/* Virtual_Channel_Connection_Create_DM */
typedef struct _vmApiVirtualChannelConnectionCreateDmOutput {
    commonOutputFields common;
} vmApiVirtualChannelConnectionCreateDmOutput;

/* Parser table for Virtual_Channel_Connection_Create_DM */
static  tableLayout Virtual_Channel_Connection_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualChannelConnectionCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionCreateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Channel_Connection_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * coupledImageName,
        vmApiVirtualChannelConnectionCreateDmOutput ** outData);

/* Virtual_Channel_Connection_Delete */
typedef struct _vmApiVirtualChannelConnectionDeleteOutput {
    commonOutputFields common;
} vmApiVirtualChannelConnectionDeleteOutput;

/* Parser table for Virtual_Memory_Access_Add_DM */
static  tableLayout Virtual_Channel_Connection_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualChannelConnectionDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Channel_Connection_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualChannelConnectionDeleteOutput ** outData);

/* Virtual_Channel_Connection_Delete_DM */
typedef struct _vmApiVirtualChannelConnectionDeleteDmOutput {
    commonOutputFields common;
} vmApiVirtualChannelConnectionDeleteDmOutput;

/* Parser table for Virtual_Channel_Connection_Delete_DM */
static  tableLayout Virtual_Channel_Connection_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualChannelConnectionDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualChannelConnectionDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Channel_Connection_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualChannelConnectionDeleteDmOutput ** outData);

/* Virtual_Network_Adapter_Connect_LAN */
typedef struct _vmApiVirtualNetworkAdapterConnectLanOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterConnectLanOutput;

/* Parser table for Virtual_Network_Adapter_Connect_LAN */
static  tableLayout Virtual_Network_Adapter_Connect_LAN_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterConnectLanOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Connect_LAN(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * lanName, char * lanOwner,
        vmApiVirtualNetworkAdapterConnectLanOutput ** outData);

/* Virtual_Network_Adapter_Connect_LAN_DM */
typedef struct vmApiVirtualNetworkAdapterConnectLanDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterConnectLanDmOutput;

/* Parser table for Virtual_Network_Adapter_Connect_LAN_DM */
static  tableLayout Virtual_Network_Adapter_Connect_LAN_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterConnectLanDmOutput)},
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectLanDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Connect_LAN_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * lanName, char * lanOwner,
        vmApiVirtualNetworkAdapterConnectLanDmOutput ** outData);

/* Virtual_Network_Adapter_Connect_Vswitch */
typedef struct _vmApiVirtualNetworkAdapterConnectVswitchOutput {
     commonOutputFields common;
} vmApiVirtualNetworkAdapterConnectVswitchOutput;

/* Parser table for Virtual_Network_Adapter_Connect_Vswitch */
static  tableLayout Virtual_Network_Adapter_Connect_Vswitch_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterConnectVswitchOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Connect_Vswitch(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * switchName,
        vmApiVirtualNetworkAdapterConnectVswitchOutput ** outData);

/* Virtual_Network_Adapter_Connect_Vswitch_DM */
typedef struct _vmApiVirtualNetworkAdapterConnectVswitchDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterConnectVswitchDmOutput;

/* Parser table for Virtual_Network_Adapter_Connect_Vswitch_DM */
static  tableLayout Virtual_Network_Adapter_Connect_Vswitch_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterConnectVswitchDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Connect_Vswitch_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char * switchName,
        vmApiVirtualNetworkAdapterConnectVswitchDmOutput ** outData);

/* Virtual_Network_Adapter_Connect_Vswitch_Extended */
typedef struct _vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput;

/* Parser table for Virtual_Network_Adapter_Connect_Vswitch_Extended */
static  tableLayout Virtual_Network_Adapter_Connect_Vswitch_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Connect_Vswitch_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput ** outData);

/* Virtual_Network_Adapter_Create */
typedef struct _vmApiVirtualNetworkAdapterCreateOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterCreateOutput;

/* Parser table for Virtual_Network_Adapter_Create */
static  tableLayout Virtual_Network_Adapter_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char adapterType, int networkAdapterDevices,
        char * channelPathId, vmApiVirtualNetworkAdapterCreateOutput ** outData);

/* Virtual_Network_Adapter_Create_DM */
typedef struct _vmApiVirtualNetworkAdapterCreateDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterCreateDmOutput;

/* Parser table for Virtual_Network_Adapter_Create_DM */
static  tableLayout Virtual_Network_Adapter_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, char adapterType, int networkAdapterDevices,
        char * channelPathId, char * macId, vmApiVirtualNetworkAdapterCreateDmOutput ** outData);

/* Virtual_Network_Adapter_Create_Extended */
typedef struct _vmApiVirtualNetworkAdapterCreateExtendedOutput {
     commonOutputFields common;
} vmApiVirtualNetworkAdapterCreateExtendedOutput;

/* Parser table for Virtual_Network_Adapter_Create_Extended */
static  tableLayout Virtual_Network_Adapter_Create_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterCreateExtendedOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Create_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkAdapterCreateExtendedOutput ** outData);

/* Virtual_Network_Adapter_Create_Extended_DM */
typedef struct _vmApiVirtualNetworkAdapterCreateExtendedDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterCreateExtendedDmOutput;

/* Parser table for Virtual_Network_Adapter_Create_Extended_DM */
static  tableLayout Virtual_Network_Adapter_Create_Extended_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterCreateExtendedDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterCreateExtendedDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Create_Extended_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkAdapterCreateExtendedDmOutput ** outData);

/* Virtual_Network_Adapter_Delete */
typedef struct _vmApiVirtualNetworkAdapterDeleteOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterDeleteOutput;

/* Parser table for Virtual_Network_Adapter_Delete */
static  tableLayout Virtual_Network_Adapter_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualNetworkAdapterDeleteOutput ** outData);

/* Virtual_Network_Adapter_Delete_DM */
typedef struct _vmApiVirtualNetworkAdapterDeleteDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterDeleteDmOutput;

/* Parser table for Virtual_Network_Adapter_Delete_DM */
static  tableLayout Virtual_Network_Adapter_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualNetworkAdapterDeleteDmOutput ** outData);

/* Virtual_Network_Adapter_Disconnect */
typedef struct vmApiVirtualNetworkAdapterDisconnectOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterDisconnectOutput;

/* Parser table for Virtual_Network_Adapter_Disconnect */
static  tableLayout Virtual_Network_Adapter_Disconnect_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterDisconnectOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Disconnect(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualNetworkAdapterDisconnectOutput ** outData);

/* Virtual_Network_Adapter_Disconnect_DM */
typedef struct _vmApiVirtualNetworkAdapterDisconnectDmOutput {
    commonOutputFields common;
} vmApiVirtualNetworkAdapterDisconnectDmOutput;

/* Parser table for Virtual_Network_Adapter_Disconnect_DM */
static  tableLayout Virtual_Network_Adapter_Disconnect_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterDisconnectDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterDisconnectDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Disconnect_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualNetworkAdapterDisconnectDmOutput ** outData);

/* Virtual_Network_Adapter_Query */
typedef struct _vmApiVirtualNetworkAdapter {
    char * imageDeviceNumber;
    char adapterType;
    int networkAdapterDevices;
    char adapterStatus;
    char * lanOwner;
    char * lanName;
} vmApiVirtualNetworkAdapter;

typedef struct _vmApiVirtualNetworkAdapterQueryOutput {
    commonOutputFields common;
    int adapterArrayCount;
    vmApiVirtualNetworkAdapter * adapterList;
} vmApiVirtualNetworkAdapterQueryOutput;

/* Parser table for Virtual_Network_Adapter_Query */
static  tableLayout Virtual_Network_Adapter_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkAdapterQueryOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterQueryOutput, adapterList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkAdapterQueryOutput, adapterArrayCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVirtualNetworkAdapter) },
    { APITYPE_STRING_LEN,         1, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, imageDeviceNumber) },
    { APITYPE_INT1,               1, 1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, adapterType) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, networkAdapterDevices) },
    { APITYPE_INT1,               1, 1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, adapterStatus) },
    { APITYPE_STRING_LEN,         0, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, lanOwner) },
    { APITYPE_STRING_LEN,         0, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkAdapter, lanName) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * imageDeviceNumber, vmApiVirtualNetworkAdapterQueryOutput ** outData);

/* Virtual_Network_Adapter_Query_Extended Response structure*/
typedef struct _vmApiVirtualNetworkAdapterQueryExtended {
    commonOutputFields common;
    int responseCnt;
    vmApiCStringInfo* responseList;
} vmApiVirtualNetworkAdapterQueryExtendedOutput;

/* Parser table for Virtual_Network_Adapter_Query_Extended */
static tableLayout Virtual_Network_Adapter_Query_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof( vmApiVirtualNetworkAdapterQueryExtendedOutput ) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof( vmApiVirtualNetworkAdapterQueryExtendedOutput, common.requestId ) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof( vmApiVirtualNetworkAdapterQueryExtendedOutput, common.returnCode ) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof( vmApiVirtualNetworkAdapterQueryExtendedOutput, common.reasonCode ) },
    { APITYPE_C_STR_ARRAY_PTR,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof( vmApiVirtualNetworkAdapterQueryExtendedOutput, responseList ) },
    { APITYPE_C_STR_ARRAY_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof( vmApiVirtualNetworkAdapterQueryExtendedOutput, responseCnt ) },
    { APITYPE_C_STR_STRUCT_LEN,   4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof( vmApiCStringInfo ) },
    { APITYPE_C_STR_PTR,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof( vmApiCStringInfo, vmapiString ) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Adapter_Query_Extended( struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkAdapterQueryExtendedOutput ** outData );

/* Virtual_Network_LAN_Access */
typedef struct _vmApiVirtualNetworkLanAccessOutput {
    commonOutputFields common;
} vmApiVirtualNetworkLanAccessOutput;

/* Parser table for Virtual_Network_LAN_Access */
static  tableLayout Virtual_Network_LAN_Access_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkLanAccessOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_LAN_Access(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * lanName, char * lanOwner, char * accessOption, char * accessGrantName, char * promiscuity,
        vmApiVirtualNetworkLanAccessOutput ** outData);

/* Virtual_Network_LAN_Access_Query */
typedef struct _vmApiVirtualNetworkLanAccessQueryOutput {
    commonOutputFields common;
    int lanAccessCount;
    vmApiCStringInfo * lanAccessList;
} vmApiVirtualNetworkLanAccessQueryOutput;

/* Parser table for  Virtual_Network_LAN_Access_Query */
static  tableLayout Virtual_Network_LAN_Access_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkLanAccessQueryOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessQueryOutput, lanAccessList) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanAccessQueryOutput, lanAccessCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_LAN_Access_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * lanName, char * lanOwner,
        vmApiVirtualNetworkLanAccessQueryOutput ** outData);

/* Virtual_Network_LAN_Create */
typedef struct _vmApiVirtualNetworkLanCreateOutput {
      commonOutputFields common;
} vmApiVirtualNetworkLanCreateOutput;

/* Parser table for Virtual_Network_LAN_Create */
static  tableLayout Virtual_Network_LAN_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkLanCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanCreateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_LAN_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * lanName, char * lanOwner, char lanType,  // 1,2,3,4
        char transportType, vmApiVirtualNetworkLanCreateOutput ** outData);

/* Virtual_Network_LAN_Delete */
typedef struct _vmApiVirtualNetworkLanDeleteOutput {
    commonOutputFields common;
} vmApiVirtualNetworkLanDeleteOutput;

/* Parser table for Virtual_Network_LAN_Delete */
static  tableLayout Virtual_Network_LAN_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkLanDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_LAN_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * lanName, char * lanOwner, vmApiVirtualNetworkLanDeleteOutput ** outData);

/* Virtual_Network_LAN_Query */
typedef struct _vmApiVirtualNetworkConnectedAdapterInfo {
    char * adapterOwner;
    char * imageDeviceNumber;
} vmApiVirtualNetworkConnectedAdapterInfo;

typedef struct _vmApiVirtualNetworkLanInfo {
    char * lanName;
    char * lanOwner;
    char lanType;
    int connectedAdapterCount;
    vmApiVirtualNetworkConnectedAdapterInfo * connectedAdapterList;
} vmApiVirtualNetworkLanInfo;

typedef struct _vmApiVirtualNetworkLanQueryOutput {
    commonOutputFields common;
    int lanCount;
    vmApiVirtualNetworkLanInfo * lanList;
} vmApiVirtualNetworkLanQueryOutput;

/* Parser table for Virtual_Network_LAN_Query */
static  tableLayout Virtual_Network_LAN_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkLanQueryOutput) },
    { APITYPE_INT4,               4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanQueryOutput, lanList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkLanQueryOutput, lanCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVirtualNetworkLanInfo) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkLanInfo, lanName) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkLanInfo, lanOwner) },
    { APITYPE_INT1,               1, 1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkLanInfo, lanType) },
    { APITYPE_ARRAY_LEN,          4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkLanInfo, connectedAdapterList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVirtualNetworkLanInfo, connectedAdapterCount) },
    { APITYPE_STRUCT_LEN,         4, 4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiVirtualNetworkConnectedAdapterInfo) },
    { APITYPE_STRING_LEN,         1, 8, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiVirtualNetworkConnectedAdapterInfo, adapterOwner) },
    { APITYPE_STRING_LEN,         1, 4, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiVirtualNetworkConnectedAdapterInfo, imageDeviceNumber) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_LAN_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * lanName, char * lanOwner, vmApiVirtualNetworkLanQueryOutput ** outData);

/* Virtual_Network_OSA_Query */
typedef struct _vmApiVirtualNetworkOsaQueryOutput {
    commonOutputFields common;
    int arrayCount;
    vmApiCStringInfo* osaInfoStructure;
} vmApiVirtualNetworkOsaQueryOutput;

/* Parser table for Virtual_Network_OSA_Query */
static  tableLayout Virtual_Network_OSA_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkOsaQueryOutput) },
    { APITYPE_INT4,              4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkOsaQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkOsaQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,           4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkOsaQueryOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,   4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkOsaQueryOutput, osaInfoStructure) },
    { APITYPE_C_STR_ARRAY_COUNT, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkOsaQueryOutput, arrayCount) },
    { APITYPE_C_STR_STRUCT_LEN,  4, 4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,         4, 4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_OSA_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
    char * targetIdentifier, vmApiVirtualNetworkOsaQueryOutput ** outData);

/* Virtual_Network_VLAN_Query_Stats */
typedef struct _vmApiPsegArray_structure {
    // Contains blank delimited segment fields: vlanid, rx, rx_disc, tx, tx_disc
    vmApiCStringInfo* segmentStructure;
} vmApiPsegArray_structure;

typedef struct _vmApiPortNic_structure {
    // Contains blank delimited port/nic fields: type (PORT or NIC), port_name/nic_addr, num
    vmApiCStringInfo* portNicValues;
    int segmentCount;
    vmApiPsegArray_structure * segmentArray;
} vmApiPortNic_structure;

typedef struct _vmApiVirtualNetworkVLANQueryStatsOutput {
    commonOutputFields common;
    int portNicArrayCount;
    vmApiPortNic_structure * portNicList;
} vmApiVirtualNetworkVLANQueryStatsOutput;

/* Parser table for Virtual_Network_VLAN_Query_Stats */
static tableLayout Virtual_Network_VLAN_Query_Stats_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVLANQueryStatsOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVLANQueryStatsOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVLANQueryStatsOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVLANQueryStatsOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVLANQueryStatsOutput, portNicList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVLANQueryStatsOutput, portNicArrayCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiPortNic_structure) },
    { APITYPE_C_STR_PTR,          1, 24, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPortNic_structure, portNicValues) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPortNic_structure, segmentArray) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiPortNic_structure, segmentCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiPsegArray_structure) },
    { APITYPE_C_STR_PTR,          1, 50, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiPsegArray_structure, segmentStructure) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_VLAN_Query_Stats(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password,  char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVLANQueryStatsOutput ** outData);

/* Virtual_Network_Vswitch_Create */
typedef struct _vmApiVirtualNetworkVswitchCreateOutput {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchCreateOutput;

/* Parser table for Virtual_Network_Vswitch_Create */
static  tableLayout Virtual_Network_Vswitch_Create_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchCreateOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Create(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * switchName, char * realDeviceAddress, char * portName,
        char * controllerName, char connectionValue, int queueMemoryLimit, char routingValue, char transportType, int vlanId,
        char portType, char updateSystemConfigIndicator, char * systemConfigName, char * systemConfigType, char * parmDiskOwner,
        char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName, char * altSystemConfigType,
        char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword, char gvrpValue,
        int nativeVlanId, vmApiVirtualNetworkVswitchCreateOutput ** outData);

/* Virtual_Network_Vswitch_Create_Extended */
typedef struct _vmApiVirtualNetworkVswitchCreateExtendedOutput {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchCreateExtendedOutput;

/* Parser table for Virtual_Network_Vswitch_Create_Extended */
static  tableLayout Virtual_Network_Vswitch_Create_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchCreateExtendedOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateExtendedOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateExtendedOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchCreateExtendedOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Create_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchCreateExtendedOutput ** outData);

/* Virtual_Network_Vswitch_Delete */
typedef struct _vmApiVirtualNetworkVswitchDeleteOutput {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchDeleteOutput;

/* Parser table for Virtual_Network_Vswitch_Delete */
static  tableLayout Virtual_Network_Vswitch_Delete_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Delete(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char * switchName, char updateSystemConfigIndicator, char * systemConfigName,
        char * systemConfigType, char * parmDiskOwner, char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName,
        char * altSystemConfigType, char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword,
        vmApiVirtualNetworkVswitchDeleteOutput ** outData);

/* Virtual_Network_Vswitch_Delete_Extended */
typedef struct _vmApiVirtualNetworkVswitchDeleteExtendedOutput {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchDeleteExtendedOutput;

/* Parser table for Virtual_Network_Vswitch_Delete_Extended */
static  tableLayout Virtual_Network_Vswitch_Delete_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchDeleteOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchDeleteOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Delete_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchDeleteExtendedOutput ** outData);

/* Virtual_Network_Vswitch_Query */
typedef struct _vmApiConnectedAdapterInfo {
    int userVlanId;
} vmApiVlanInfo;

typedef struct _vmApiAuthorizedUserInfo {
    char * grantUserid;
    int vlanCount;
    vmApiVlanInfo * vlanList;
} vmApiAuthorizedUserInfo;

typedef struct _vmApiRealDeviceInfo {
    int realDeviceAddress;
    char * controllerName;
    char * portName;
    char deviceStatus;
    char deviceErrorStatus;
} vmApiRealDeviceInfo;

typedef struct _vmApiVswitchInfo {
    char * switchName;
    char transportType;
    char portType;
    int queueMemoryLimit;
    char routingValue;
    int vlanId;
    int nativeVlanId;
    unsigned long long macId;
    char grvpRequestAttribute;
    char grvpEnabledAttribute;
    char switchStatus;
    int realDeviceCount;
    vmApiRealDeviceInfo * realDeviceList;
    int authorizedUserCount;
    vmApiAuthorizedUserInfo * authorizedUserList;
    int connectedAdapterCount;
    vmApiVirtualNetworkConnectedAdapterInfo * connectedAdapterList;  // Shares common structure with Virtual network lan query
} vmApiVswitchInfo;

typedef struct _vmApiVirtualNetworkVswitchQueryOutput {
    commonOutputFields common;
    int vswitchCount;
    vmApiVswitchInfo * vswitchList;
} vmApiVirtualNetworkVswitchQueryOutput;

/* Parser table for Virtual_Network_Vswitch_Query */
static  tableLayout Virtual_Network_Vswitch_Query_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchQueryOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryOutput, vswitchList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryOutput, vswitchCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVswitchInfo) },
    { APITYPE_STRING_LEN,         1,  8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, switchName) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, transportType) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, portType) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, queueMemoryLimit) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, routingValue) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, vlanId) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, nativeVlanId) },
    { APITYPE_INT8,               8,  8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, macId) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, grvpRequestAttribute) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, grvpEnabledAttribute) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, switchStatus) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, realDeviceList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, realDeviceCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiRealDeviceInfo) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiRealDeviceInfo, realDeviceAddress) },
    { APITYPE_STRING_LEN,         0, 71, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiRealDeviceInfo, controllerName) },
    { APITYPE_STRING_LEN,         0, 16, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiRealDeviceInfo, portName) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiRealDeviceInfo, deviceStatus) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiRealDeviceInfo, deviceErrorStatus) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, authorizedUserList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, authorizedUserCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_3, NEST_LEVEL_2, sizeof(vmApiAuthorizedUserInfo) },
    { APITYPE_STRING_LEN,         1,  8, STRUCT_INDX_3, NEST_LEVEL_2, offsetof(vmApiAuthorizedUserInfo, grantUserid) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_3, NEST_LEVEL_2, offsetof(vmApiAuthorizedUserInfo, vlanList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_3, NEST_LEVEL_2, offsetof(vmApiAuthorizedUserInfo, vlanCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_4, NEST_LEVEL_3, sizeof(vmApiVlanInfo) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_4, NEST_LEVEL_3, offsetof(vmApiVlanInfo, userVlanId) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, connectedAdapterList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitchInfo, connectedAdapterCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_5, NEST_LEVEL_2, sizeof(vmApiVirtualNetworkConnectedAdapterInfo) },
    { APITYPE_STRING_LEN,         1,  8, STRUCT_INDX_5, NEST_LEVEL_2, offsetof(vmApiVirtualNetworkConnectedAdapterInfo, adapterOwner) },
    { APITYPE_STRING_LEN,         1,  4, STRUCT_INDX_5, NEST_LEVEL_2, offsetof(vmApiVirtualNetworkConnectedAdapterInfo, imageDeviceNumber) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Query(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * switchName, vmApiVirtualNetworkVswitchQueryOutput ** outData);

/* Virtual_Network_Vswitch_Query_Byte_Stats */
typedef struct _vmApiVirtualNetworkVswitchQueryByteStatsOutput {
    commonOutputFields common;
    int stringCount;
    vmApiCStringInfo * stringList;
} vmApiVirtualNetworkVswitchQueryByteStatsOutput;

/* Parser table for Virtual_Network_VSwitch_Query_Byte_Stats */
static tableLayout Virtual_Network_Vswitch_Query_Byte_Stats_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,   4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchQueryByteStatsOutput) },
    { APITYPE_INT4,                4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryByteStatsOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryByteStatsOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryByteStatsOutput, common.reasonCode) },
    { APITYPE_C_STR_ARRAY_PTR,     4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryByteStatsOutput, stringList) },
    { APITYPE_C_STR_ARRAY_COUNT,   4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryByteStatsOutput, stringCount) },
    { APITYPE_C_STR_STRUCT_LEN,    4,   4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiCStringInfo) },
    { APITYPE_C_STR_PTR,           4,   4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiCStringInfo, vmapiString) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Query_Byte_Stats(
        struct _vmApiInternalContext* vmapiContextP, char * userid,
        int passwordLength, char * password, char * targetIdentifier,
        int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchQueryByteStatsOutput ** outData);

/* Virtual_Network_Vswitch_Query_Extended */
typedef struct _real_device_info_struct {
    // Blank delimited fields for: virtual_device_address, controller_name, port_name,
    // device_status, device_error_status
    vmApiCStringInfo* realDeviceFields;
} real_device_info_structure;

typedef struct _authorized_user_struct {
    // Blank delmited fields for: port_num, grant_userid, promiscuous_mode,
    // osd_sim, vlan_count, "vlan ids, vlan ids", (as many as the vlan_count)
    vmApiCStringInfo* authUserFields;
} authorized_user_structure;

typedef struct _connected_adapter_structure {
    // Blank delimited fields for: adapter_owner, adapter_vdev, adapter_macaddr,
    // adapter_type
    vmApiCStringInfo* connAdapterFields;
} connected_adapter_structure;

typedef struct _uplink_NIC_structure {
    // Blank delmited fields for: uplink_NIC_userid, uplink_NIC_vdev, uplink_NIC_error_status;
    vmApiCStringInfo* uplinkNICFields;
} uplink_NIC_structure;

typedef struct _global_member_structure {
    // Blank delmited fields for: member name, member state;
    vmApiCStringInfo* globalmemberFields;
} global_member_structure;

typedef struct _vswitch_array_struct {
    int attrLength;
    vmApiCStringInfo* vswitchAttributes;
    int realDeviceCount;
    real_device_info_structure * realDeviceList;
    int authUserCount;
    authorized_user_structure * authUserList;
    int adapterCount;
    connected_adapter_structure * connAdapterList;
    int uplinkNicCount;
    uplink_NIC_structure * uplinkNicList;
    int globalMemberCount;
    global_member_structure * globalMemberList;
} vswitch_array_structure;

typedef struct _vmApiVirtualNetworkVswitchQueryExtendedOutput {
    commonOutputFields common;
    int vswitchArrayCountCalculated;
    vswitch_array_structure * vswitchList;
} vmApiVirtualNetworkVswitchQueryExtendedOutput;

/* Parser table for Virtual_Network_VSwitch_Query_Extended */
static tableLayout Virtual_Network_VSwitch_Query_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchQueryExtendedOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryExtendedOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryExtendedOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryExtendedOutput, common.reasonCode) },
    { APITYPE_ARRAY_COUNT,        4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryExtendedOutput, vswitchList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryExtendedOutput, vswitchArrayCountCalculated) },

    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vswitch_array_structure) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, attrLength) },
    { APITYPE_C_STR_PTR,          1,200, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, vswitchAttributes) },

    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, realDeviceList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, realDeviceCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(real_device_info_structure) },
    { APITYPE_C_STR_PTR,          0, 90, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(real_device_info_structure, realDeviceFields) },


    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, authUserList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, authUserCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_3, NEST_LEVEL_3, sizeof(authorized_user_structure) },
    { APITYPE_C_STR_PTR,          0, -1, STRUCT_INDX_3, NEST_LEVEL_3, offsetof(authorized_user_structure, authUserFields) },


    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, connAdapterList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, adapterCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_4, NEST_LEVEL_4, sizeof(connected_adapter_structure) },
    { APITYPE_C_STR_PTR,          0, 41, STRUCT_INDX_4, NEST_LEVEL_4, offsetof(connected_adapter_structure, connAdapterFields) },

    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, uplinkNicList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, uplinkNicCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_5, NEST_LEVEL_5, sizeof(uplink_NIC_structure) },
    { APITYPE_C_STR_PTR,          0, 15, STRUCT_INDX_5, NEST_LEVEL_5, offsetof(uplink_NIC_structure, uplinkNICFields) },

    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, globalMemberList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vswitch_array_structure, globalMemberCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN,4,  4, STRUCT_INDX_6, NEST_LEVEL_6, sizeof(global_member_structure) },
    { APITYPE_C_STR_PTR,          0, 15, STRUCT_INDX_6, NEST_LEVEL_6, offsetof(global_member_structure, globalmemberFields) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Query_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchQueryExtendedOutput ** outData);

/* Virtual_Network_Vswitch_Query_Stats */
typedef struct _vmApiVswitchPsegArray_structure {
    // Contains blank delimited segment fields: vlanid, rx, rx_disc, tx, tx_disc,
    // activated_TOD, config_update_TOD, vlan_interfaces, vlan_deletes, device_type, device_addr, device_status
    vmApiCStringInfo* segmentData;
} vmApiVswitchPsegArray_structure;

typedef struct _vmApiVswitch_structure {
    char * vswitchName;
    int segmentCount;
    vmApiVswitchPsegArray_structure * segmentArray;
} vmApiVswitch_structure;

typedef struct _vmApiVirtualNetworkVswitchQueryStatsOutput {
    commonOutputFields common;
    int vswitchArrayCount;
    vmApiVswitch_structure * vswitchList;
} vmApiVirtualNetworkVswitchQueryStatsOutput;

/* Parser table for Virtual_Network_VSwitch_Query_Stats */
static tableLayout Virtual_Network_Vswitch_Query_Stats_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,   4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchQueryStatsOutput) },
    { APITYPE_INT4,                4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryStatsOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryStatsOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryStatsOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryStatsOutput, vswitchList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,   4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchQueryStatsOutput, vswitchArrayCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,   4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiVswitch_structure) },
    { APITYPE_STRING_LEN,          1,   8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitch_structure, vswitchName) },
    { APITYPE_ARRAY_LEN,           4,   4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitch_structure, segmentArray) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,   4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiVswitch_structure, segmentCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,   4, STRUCT_INDX_2, NEST_LEVEL_2, sizeof(vmApiVswitchPsegArray_structure) },
    { APITYPE_C_STR_PTR,           1, 111, STRUCT_INDX_2, NEST_LEVEL_2, offsetof(vmApiVswitchPsegArray_structure, segmentData) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Query_Stats(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchQueryStatsOutput ** outData);

/* Virtual_Network_Vswitch_Set */
typedef struct _vmApiVirtualNetworkVswitchSetOutput {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchSetOutput;

/* Parser table for Virtual_Network_Vswitch_Set */
static tableLayout Virtual_Network_Vswitch_Set_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchSetOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Set(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char * switchName, char * grantUserid, char * userVlanId, char * revokeUserid,
        char * realDeviceAddress, char * portName, char * controllerName, char connectionValue, int queueMemoryLimit,
        char routingValue, char portType, char updateSystemConfigIndicator, char * systemConfigName, char * systemConfigType,
        char * parmDiskOwner, char * parmDiskNumber, char * parmDiskPassword, char * altSystemConfigName,
        char * altSystemConfigType, char * altParmDiskOwner, char * altParmDiskNumber, char * altParmDiskPassword, char gvrpValue,
        char * macId, vmApiVirtualNetworkVswitchSetOutput ** outData);

/* Virtual_Network_Vswitch_Set_Extended */
typedef struct _vmApiVirtualNetworkVswitchSetExtended {
    commonOutputFields common;
} vmApiVirtualNetworkVswitchSetExtendedOutput;

/* Parser table for Virtual_Network_Vswitch_Set_Extended */
static tableLayout Virtual_Network_Vswitch_Set_Extended_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiVirtualNetworkVswitchSetExtendedOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetExtendedOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetExtendedOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiVirtualNetworkVswitchSetExtendedOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smVirtual_Network_Vswitch_Set_Extended(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char* targetIdentifier, int keyValueCount, char ** keyValueArray,
        vmApiVirtualNetworkVswitchSetExtendedOutput** outData);

#ifdef __cplusplus
}
#endif

#endif
