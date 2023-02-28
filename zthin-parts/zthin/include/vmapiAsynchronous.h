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
#ifndef _VMAPI_ASYNCHRONOUS_H
#define _VMAPI_ASYNCHRONOUS_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Asynchronous_Notification_Disable_DM */
typedef struct _vmApiAsynchronousNotificationDisableDmOutput {
    commonOutputFields common;
} vmApiAsynchronousNotificationDisableDmOutput;

/* Parser table for Asynchronous_Notification_Disable_DM */
static tableLayout Asynchronous_Notification_Disable_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAsynchronousNotificationDisableDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationDisableDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationDisableDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationDisableDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smAsynchronous_Notification_Disable_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, char entity_type, char communication_type, int port_number,
        char * ip_address, char encoding, int subscriber_data_length, char * subscriber_data, vmApiAsynchronousNotificationDisableDmOutput ** outData);

/* Asynchronous_Notification_Enable_DM */
typedef struct _vmApiAsynchronousNotificationEnableDmOutput {
    commonOutputFields common;
} vmApiAsynchronousNotificationEnableDmOutput;

/* Parser table for Asynchronous_Notification_Enable_DM */
static tableLayout Asynchronous_Notification_Enable_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAsynchronousNotificationEnableDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationEnableDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationEnableDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationEnableDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smAsynchronous_Notification_Enable_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password, char * targetIdentifier,
        char entity_type, char subscription_type, char communication_type, int port_number, char * ip_address, char encoding,
        int subscriber_data_length, char * subscriber_data, vmApiAsynchronousNotificationEnableDmOutput ** outData);

/* Asynchronous_Notification_Query_DM */
typedef struct _vmApiNotification {
    char * userid;
    char subscriptionType;
    char communicationType;
    int portNumber;
    char * ipAddress;
    char encoding;
    int subscriberDataLength;
    char * subscriberData;
} vmApiNotification;

typedef struct _vmApiAsynchronousNotificationQueryDmOutput {
    commonOutputFields common;
    int notificationCount;
    vmApiNotification * notificationList;
} vmApiAsynchronousNotificationQueryDmOutput;

/* Parser table for Asynchronous_Notification_Query_DM */
static tableLayout Asynchronous_Notification_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,    4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiAsynchronousNotificationQueryDmOutput) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,            4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,          4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationQueryDmOutput, notificationList) },
    { APITYPE_ARRAY_STRUCT_COUNT, 4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiAsynchronousNotificationQueryDmOutput, notificationCount) },
    { APITYPE_STRUCT_LEN,         4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiNotification) },
    { APITYPE_STRING_LEN,         1,  8, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, userid) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, subscriptionType) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, communicationType) },
    { APITYPE_INT4,               4,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, portNumber) },
    { APITYPE_STRING_LEN,         7, 15, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, ipAddress) },
    { APITYPE_INT1,               1,  1, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, encoding) },
    { APITYPE_CHARBUF_LEN,        0, 64, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, subscriberData) },
    { APITYPE_CHARBUF_COUNT,      0,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiNotification, subscriberDataLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smAsynchronous_Notification_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, char entity_type, char communication_type, int port_number, char * ip_address, char encoding, int subscriber_data_length,
        char * subscriber_data, vmApiAsynchronousNotificationQueryDmOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
