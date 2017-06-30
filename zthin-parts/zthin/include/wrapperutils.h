/**
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
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "vmapiAsynchronous.h"
#include "vmapiAuthorization.h"
#include "vmapiCheck.h"
#include "vmapiDelete.h"
#include "vmapiDirectory.h"
#include "vmapiEvent.h"
#include "vmapiImage.h"
#include "vmapiImageDefinition.h"
#include "vmapiMetadata.h"
#include "vmapiName.h"
#include "vmapiNetwork.h"
#include "vmapiPage.h"
#include "vmapiProcess.h"
#include "vmapiProfile.h"
#include "vmapiPrototype.h"
#include "vmapiQuery.h"
#include "vmapiResponse.h"
#include "vmapiShared.h"
#include "vmapiSMAPI.h"
#include "vmapiSSI.h"
#include "vmapiStatic.h"
#include "vmapiSystem.h"
#include "vmapiVirtual.h"
#include "vmapiVMRelocate.h"
#include "vmapiVMRM.h"
#include "vmapiUnDocumented.h"

void releaseContext(vmApiInternalContext* context);
void initializeContext(vmApiInternalContext* context, smMemoryGroupContext* memContext);
int isImageNameInvalid(char* imageName);
int isProfileNameInvalid(char* profileName);
int isDevNumberInvalid(char* devNumber);
void trim(char * s);
void convertEBCDICtoASCII(struct _vmApiInternalContext *vmapiContextP, char *ebcdicString, char *asciiString);
void convertASCIItoEBCDIC(struct _vmApiInternalContext *vmapiContextP, char *asciiString, char *ebcdicString);
unsigned char ASCIItoEBCDIC(const unsigned char c);
unsigned char EBCDICtoASCII(const unsigned char c);
void printRCheaderHelp();

// Routines for saving output messages for print at the end. See wrapperutils.c
int addMessageToBuffer(struct _smMessageCollector *firstMsgCollectorP, char * msg);
int printMessageBuffersAndRelease(struct _smMessageCollector *firstMsgCollectorP);

// The new error handling methods, status string is used only for functions that printed a "starting ..." status message
// Pass in "" for functions that do not have such a message.
void printAndLogProcessingErrors(const char * class, int rc, struct _vmApiInternalContext *vmapiContextP, char * statusString, int justHeader);
int printAndLogSmapiReturnCodeReasonCodeDescription(const char * class, int returnCode, int reasonCode,
         struct _vmApiInternalContext *vmapiContextP, char * statusString);
int printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer(const char * class, int rc, int returnCode, int reasonCode,
         int errorLength, char * errorBuffer, struct _vmApiInternalContext* vmapiContextP, char * statusString);

void printSmapiDescriptionAndLogError(const char * class, int rc, int rs, struct _vmApiInternalContext* vmapiContextP, int newHeader);

/* For development use to aid in debugging code */
#define LOG(format) syslog(LOG_LOCAL5 | LOG_INFO, "%d.%lu %s %s: " format, getpid(), pthread_self(), __FILE__, __FUNCTION__)
#define LOGA(format, args) syslog(LOG_LOCAL5 | LOG_INFO, "%d.%lu %s %s: " format, getpid(), pthread_self(), __FILE__, __FUNCTION__, args)

/* This macro will clear out the context and memory structures */
#define INIT_CONTEXT_AND_MEMORY(_CONTEXT_, _MEMORYCONTEXT_, _TRACEFLAGS_, _RC_) { \
    memset(_CONTEXT_, 0, sizeof(*(_CONTEXT_))); \
    memset(_MEMORYCONTEXT_, 0, sizeof(*(_MEMORYCONTEXT_))); \
    (_CONTEXT_)->memContext = _MEMORYCONTEXT_; \
    (_CONTEXT_)->smTraceDetails = (struct _smTrace *) _TRACEFLAGS_; \
    _RC_ = smMemoryGroupInitialize(_CONTEXT_); \
    if (0 == _RC_) { \
        readTraceFile(_CONTEXT_); \
    } else { \
        logLine(_CONTEXT_, 'E', "Unexpected smMemoryGroupInitializeError!"); \
    } \
}

/* This macro will free the memory from the memory structures */
#define FREE_CONTEXT_MEMORY(_CONTEXT_) { \
    smMemoryGroupFreeAll(_CONTEXT_);\
    smMemoryGroupTerminate(_CONTEXT_);\
}

/* This macro will free the memory if this pointer is not null */
#define FREE_MEMORY_CLEAR_POINTER(_PTR_) { \
    if (_PTR_ != NULL) { \
        free(_PTR_);\
        _PTR_ = NULL; \
     }\
}

/* Define the sleep time in seconds to wait for asynch operations before recheck */
#define SLEEP_ASYNCH_DEFAULT 15

/* Define the number of times to retry a sleep loop for asynch recheck */
#define SLEEP_ASYNCH_RETRIES 12