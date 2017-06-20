/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef VMAPIEVENT_H_
#define VMAPIEVENT_H_
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

/* Event_Stream_Add  */
typedef struct _vmApiEventStreamAddOutput {
    commonOutputFields common;
} vmApiEventStreamAddOutput;

/* Parser table for Event_Stream_Add */
static tableLayout Event_Stream_Add_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiEventStreamAddOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventStreamAddOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventStreamAddOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventStreamAddOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smEvent_Stream_Add(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int eventId, int eventCharLength, char ** eventChars, int eventHexCharLength, char ** hexChars,  vmApiEventStreamAddOutput ** outData);

/* Event_Subscribe (Not implemented) */
typedef struct _vmApiEventSubscribeOutput {
    commonOutputFields common;
} vmApiEventSubscribeOutput;

/* Parser table for Event_Subscribe */
// The common.returnCode and common.reasonCode are only filled in for an error
static tableLayout Event_Subscribe_Layout = {
    { APITYPE_BASE_STRUCT_LEN,  4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiEventSubscribeOutput) },
    { APITYPE_INT4,             4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventSubscribeOutput, common.requestId) },
    { APITYPE_RC_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventSubscribeOutput, common.returnCode) },
    { APITYPE_RS_INT4,          4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventSubscribeOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smEvent_Subscribe(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int eventId, char ** eventChars, int eventHexCharLength, char ** hexChars, vmApiEventStreamAddOutput ** outData);

/* Event_Unsubscribe */
typedef struct _vmApiEventUnsubscribeOutput {
    commonOutputFields common;
} vmApiEventUnsubscribeOutput;

/* Parser table for vmApiEventUnsubscribeOutput */
// There is not a return and reason code for this API
static tableLayout Event_Unsubscribe_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiEventUnsubscribeOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiEventUnsubscribeOutput, common.requestId) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smEvent_Unsubscribe(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiEventUnsubscribeOutput ** outData);

#endif  //  VMAPIEVENT_H_
