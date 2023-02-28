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
#ifndef _VMAPI_PROFILE_H
#define _VMAPI_PROFILE_H
#include "smPublic.h"
#include "smapiTableParser.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Profile_Create_DM */
typedef struct _vmApiProfileCreateDmOutput {
    commonOutputFields common;
} vmApiProfileCreateDmOutput;

typedef struct _vmApiProfileRecord {
    int profileRecordLength;
    char * recordData;
} vmApiProfileRecord;

/* Parser table for Profile_Create_DM */
static tableLayout Profile_Create_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileCreateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileCreateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileCreateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileCreateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Create_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int profileRecordCount, vmApiProfileRecord * profileRecordList,
        vmApiProfileCreateDmOutput ** outData);

/* Profile_Delete_DM */
typedef struct _vmApiProfileDeleteDmOutput {
    commonOutputFields common;
} vmApiProfileDeleteDmOutput;

/* Parser table for Profile_Delete_DM */
static tableLayout Profile_Delete_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileDeleteDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileDeleteDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileDeleteDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileDeleteDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Delete_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileDeleteDmOutput ** outData);

/* Profile_Lock_DM */
typedef struct _vmApiProfileLockDmOutput {
    commonOutputFields common;
} vmApiProfileLockDmOutput;

/* Parser table for Profile_Locke_DM */
static tableLayout Profile_Lock_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileLockDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Lock_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileLockDmOutput ** outData);

/* Profile_Lock_Query_DM */
typedef struct _vmApiProfileDevLockInfoRecord {
    char * devAddressDevLockedBy;
} vmApiProfileDevLockInfoRecord;

typedef struct _vmApiProfileLockQueryDm {
    commonOutputFields common;
    int lockInfoStructureLength;
    char * lockedTypeProfileLockedBy;
    int lockedDevArrayLength;
    int profileDevLockInfoRecordCount;
    vmApiProfileDevLockInfoRecord * lockDevList;
} vmApiProfileLockQueryDmOutput;

/* Parser table for Profile_Lock_Query_DM */
static tableLayout Profile_Lock_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileLockQueryDmOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, common.reasonCode) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, lockInfoStructureLength) },
    { APITYPE_C_STR_PTR,           1, 17, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, lockedTypeProfileLockedBy) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, lockedDevArrayLength) },
    { APITYPE_ARRAY_NO_LENGTH,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, lockDevList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileLockQueryDmOutput, profileDevLockInfoRecordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiProfileDevLockInfoRecord) },
    { APITYPE_C_STR_PTR,           1, 13, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiProfileDevLockInfoRecord, devAddressDevLockedBy) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Lock_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileLockQueryDmOutput ** outData);

/* Profile_Query_DM */
typedef struct _vmApiProfileQueryDmOutput {
    commonOutputFields common;
    int profileRecordCount;
    vmApiProfileRecord * profileRecordList;
} vmApiProfileQueryDmOutput;

/* Parser table for Profile_Query_DM */
static tableLayout Profile_Query_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN,     4,  4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileQueryDmOutput) },
    { APITYPE_INT4,                4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileQueryDmOutput, common.requestId) },
    { APITYPE_RC_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileQueryDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,             4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileQueryDmOutput, common.reasonCode) },
    { APITYPE_ARRAY_LEN,           4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileQueryDmOutput, profileRecordList) },
    { APITYPE_ARRAY_STRUCT_COUNT,  4,  4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileQueryDmOutput, profileRecordCount) },
    { APITYPE_NOBUFFER_STRUCT_LEN, 4,  4, STRUCT_INDX_1, NEST_LEVEL_1, sizeof(vmApiProfileRecord) },
    { APITYPE_CHARBUF_LEN,         0, 80, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiProfileRecord, recordData) },
    { APITYPE_CHARBUF_COUNT,       0,  4, STRUCT_INDX_1, NEST_LEVEL_1, offsetof(vmApiProfileRecord, profileRecordLength) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Query_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileQueryDmOutput ** outData);

/* Profile_Replace_DM */
typedef struct _vmApiProfileReplaceDmOutput {
    commonOutputFields common;
} vmApiProfileReplaceDmOutput;

/* Parser table for Profile_Replace_DM */
static tableLayout Profile_Replace_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileReplaceDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileReplaceDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileReplaceDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileReplaceDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Replace_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, int profileRecordCount, vmApiProfileRecord * profileRecordList,
        vmApiProfileReplaceDmOutput ** outData);

/* Profile_Unlock_DM */
typedef struct _vmApiProfileUnlockDmOutput {
    commonOutputFields common;
} vmApiProfileUnlockDmOutput;

/* Parser table for Profile_Unlock_DM */
static tableLayout Profile_Unlock_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiProfileUnlockDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileUnlockDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileUnlockDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiProfileUnlockDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smProfile_Unlock_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileUnlockDmOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
