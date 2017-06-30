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
#ifndef _SM_PUBLIC_H
#define _SM_PUBLIC_H

#include <netinet/in.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <stdbool.h>
#include "smTraceAndError.h"

#define BUFLEN 256
#define MAXCACHENAMELEN 8+1+8  // eg. filename.direct
#define CACHEENTRYLEN BUFLEN+MAXCACHENAMELEN
#define PATHLENGTH 512
#define LENGTH_OF_USERID_LENGTH_FIELD 4
#define ALL_SCAN_FILES "*.scan"
#define PORT_FILENAME "vmbkend.UDP"
#define NO_OF_IPADDRS 10

/* The message key is used for logon and logoff */
#define MSGKEY 999
/* The message key is used for single system image state change */
#define MSGSSIKEY 998
/* The message key is used for guest machine relocation in Single System Image */
#define MSGRELKEY 997
/* The message key is used for indication of definition change in user directory */
#define MSGDEFKEY 996

/* Number of seconds to wait between polling to generate indications. */
#define pollingInterval 90

/* Message structure for Logon/Logoff */
typedef struct logMsgStruct {
    char userid[9];
    int eventType;
} log_message_struct;

/* Message structure for user directory definition change */
typedef struct dirChngMsgStruct {
    char userid[8 + 1];  // Userid being changed
    char userWord[16 + 1];  // Userword field from the event e.g. ADD, PURGE
} dir_chng_message_struct;

/* Message structure for single system image state change */
typedef struct ssiMsgStruct {
    int eventType;
    char ssiName[9];
    int preMode;
    int newMode;
} ssi_message_struct;

/* Message structure for system relocation */
typedef struct relMsgStruct {
    char userid[9];
    int eventType;
    char targetzVM[9];
    char sourcezVM[9];
    int reasonCode;
} rel_message_struct;

/* Message buffer for Logon/Logoff */
typedef struct logMsgBuf {
    long mType;
    log_message_struct messageStruct;
} log_message_buf;

/* Message buffer for user directory definition change */
typedef struct dirChngMsgBuf {
    long mType;
    dir_chng_message_struct messageStruct;
} dir_chng_message_buf;
/* Message buffer for single system image state change */
typedef struct ssiMsgBuf {
    long mType;
    ssi_message_struct messageStruct;
} ssi_message_buf;

/* Message buffer for system relocation */
typedef struct relMsgBuf {
    long mType;
    rel_message_struct messageStruct;
} rel_message_buf;

/* Data structure to character based information */
typedef struct _Record {
    struct _Record* nextP;
    char data[1];
} Record;

/* Data structure to keep lists of records */
typedef struct _List {
    Record* firstP;
    Record* currentP;
    int size;
} List;

/* When changing the following, do a search to check for impacts to array init, etc*/
enum Times {
    ConnectRetryLimit = 10,
    SEND_RETRY_LIMIT = 8,
    Delay = 10,
    ResponseRecoveryDelay = 2,
    MaxWaitCycleN = 10,
    SleepInterval = 15,
    Socket_Timeout = 240,
    Socket_Indication_Timeout = 500,
    ImageSetRange = 4096,
    LINESIZE = 512
};

#define MEMORY_ERROR -999
#define INVALID_DATA -2
#define PROCESSING_ERROR -3
#define OUTPUT_ERRORS_FOUND -4

#define SOCKET_OBTAIN_ERROR           -100
#define SOCKET_CONNECT_REFUSED_ERROR  -101
#define SOCKET_CONNECT_TRYAGAIN_ERROR -102
#define SOCKET_TIMEOUT_ERROR          -103
#define SOCKET_READ_ERROR             -104

#define SOCKET_WRITE_ERROR            -106

#define SOCKET_PROCESSING_ERROR       -108
#define SOCKET_NOT_CONNECTED_ERROR    -109
#define SOCKET_RETRY_NO_DATA          -110
#define SOCKET_RETRY_SMAPI_POSSIBLE   -111
#define CUSTOM_DEFINED_SOCKET_RETRY   100

/* Return and reason codes */
enum ReturnCodes {
    RcWarning = 4,
    RcContext = -1,   // Context related errors
    RcSession = -2,   // Session related errors
    RcFunction = -3,  // Errors invoking functions
    RcRuntime = -4,   // General runtime errors
    RcIucv = -5,      // Error caused by IUCV, reason code is IUCV return value
    RcCp = -6,        // CP command invocation errors
    RcCpint = -7,     // CPint invocation
    RcNoMemory = -8   // Out of memory and no context yet
};

enum GeneralReasonCodes {
    RsInternalBufferTooSmall = 10000,
    RsNoMemory = 10001,
    RsSemaphoreNotCreated = 10011,
    RsSemaphoreNotObtained = 10012,
    RsSemaphoreNotReleased = 10013,
    RsSocketAddrIdFileNotOpened = 10014,
    RsUnableToOpenLog = 10100,
    RsSocketTimeout = 10110,
    RsUnexpected = 10200
};

enum ContextReasonCodes {
    RsNoHostname = 1,
    RsNoHostId = 2,
    RsNoServerAssociation = 3,
    RsNoUserid = 4,
    RsInvalidVmapiServerVersion = 5,
    RsInvalidServerName = 6
};

enum SessionReasonCodes {
    RsUnableToReadSessionContext = 1,
    RsUnableToWriteSessionContext = 2
};

enum FunctionReasonCodes {
    RsFunctionNotSpecified = 1,
    RsFunctionUnknown = 2,
    RsFunctionNotImplemented = 3,
    RsInvalidNumberOfArguments = 4,
    RsFunctionNotSupported = 5,
    RsInvalidArgument = 24
};

enum RuntimeReasonCodes {
    RsUnableToOpenLog22 = 1
};

typedef struct _smMemoryGroupContext {
    int arraySize;
    int lastChunk;
    void ** chunks;
} smMemoryGroupContext;

/* Structure for saving message output until all processed*/
typedef struct _smMessageCollector {
    int bufferSize;
    int stringCount;
    int bytesLeft;
    char * nextAvail;
    struct _smMessageCollector * nextMessageCollector;
    struct _smMessageCollector * previousMessageCollector;
    char * messageData;
} smMessageCollector;

#define MESSAGE_BUFFER_SIZE 2048

#define JUST_HEADER 1

#define CACHE_PATH_DEFAULT "/var/opt/zthin/.vmapi/"
#define CACHE_SEMAPHORE_DIRECTORY ".vmapi/"
#define CACHE_SEMAPHORE_FILENAME "vmapi.sem"
#define CACHE_DIRECTORY  ".cache/"
#define CACHE_DIRECTORY_FOR_USER "cache/"
#define CACHE_FILE_EXTENSION_FOR_USER ".cache"
#define CACHE_INSTANCEID_FILE_EXTENSION_FOR_USER ".id"
#define CACHE_SMAPI_LEVEL_FILE "/var/opt/zthin/smapi.level"

#define RETURN_CODE_HEADER_KEYWORD "--addRCheader"

#define FREE_MEMORY(_mempointer_) \
  if (_mempointer_) \
    {                  \
      free(_mempointer_); \
      _mempointer_ = NULL; \
    }


#define INIT_MESSAGE_BUFFER(_messageStructPtr_, _bytecount_, _charbufferPtr_ ) \
  (_messageStructPtr_)->bufferSize = _bytecount_; \
  (_messageStructPtr_)->stringCount = 0; \
  (_messageStructPtr_)->bytesLeft = _bytecount_; \
  (_messageStructPtr_)->nextAvail = _charbufferPtr_; \
  (_messageStructPtr_)->nextMessageCollector = NULL; \
  (_messageStructPtr_)->previousMessageCollector = NULL; \
  (_messageStructPtr_)->messageData = _charbufferPtr_; \
  memset(_charbufferPtr_, 0, _bytecount_);


#define TO_STRING2(_data_) \
     #_data_
#define TO_STRING(_data_) \
     TO_STRING2(_data_)

#define FIRST_FAILURE_MESSAGE_MAX_LEN 250

typedef struct _vmApiInternalContext {
    char serverName[256];
    int pendingWorkunits[10];
    struct _smTrace * smTraceDetails;  // Trace and error flags, locations, etc
    char userid[9];
    char IucvUserid[9];
    char useridForAsynchNotification[9];
    smMemoryGroupContext * memContext;
    char vmapiServerVersion[4];
    int maxServerRpcVersion;
    int contextCreatedFlag;
    char strFirstFailureMsg[FIRST_FAILURE_MESSAGE_MAX_LEN + 1];
    int firstFailureCaptured;
    int rc;
    int reason;
    int printOffset;
    int execDepth;
    int isBackend;
    int checkBackendFlag;
    int smapiReturnCode;           // Used by parser code to detect error buffer possibility
    int smapiReasonCode;           // "
    int smapiErrorBufferPossible;  // 0 = none, 1 = with no length, 2 = with length
    key_t semKey;
    int semId;
    FILE* logFileP;
    FILE* contextFileP;
    List inputStream;
    List outputStream;
    List errorStream;
    char path[PATHLENGTH];
    char name[256];
    char emsg[LINESIZE];
    char hostid[20];
    char password[9];
    int instanceId;
    char tag[256];
    int resolveHostName;
    int errnoSaved;
    int addRcHeader;
} vmApiInternalContext;

#define DOES_CALLER_WANT_RC_HEADER_ALLOK(_globalcontextptr_) \
  if (_globalcontextptr_->addRcHeader) \
    {                  \
      printf("0 0 0 (details) None\n"); \
    }

#define DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(_globalcontextptr_, _smapirc_, _smapirs_) \
  if (_globalcontextptr_->addRcHeader) \
    {                  \
      printf("0 %d %d (details) None\n",_smapirc_, _smapirs_); \
    }

#define DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(_globalcontextptr_) \
  if (_globalcontextptr_->addRcHeader) \
    {                  \
      printf("24 0 0 (details) Input error\n"); \
    }

#define DOES_CALLER_WANT_RC_HEADER_FOR_OUTPUT_ERRORS(_globalcontextptr_, _apiString_) \
  if (_globalcontextptr_->addRcHeader) \
    {                  \
      printAndLogProcessingErrors(_apiString_, OUTPUT_ERRORS_FOUND, _globalcontextptr_, "", JUST_HEADER); \
    }

typedef struct _Abbreviation {
    char* nameP;
    int minimum;
} Abbreviation;

/* Internal data structure to keep minidisk data */
typedef struct _Minidisk {
    struct _Minidisk* nextP;
    int address;
    char type[8];
    int location;
    int extent;
    char volser[8];
    char mode[4];
    int processFlag;
} Minidisk;

/* All SMAPI calls need userid, password, and passwordLength */
typedef struct _smapiDefaultInputs  {
    char *userid;
    char *password;
    int passwordLength;
} smapiDefaultInputs;

/* Internal data structure to keep dedicate data */
typedef struct _Dedicate {
    struct _Dedicate* nextP;
    int vnum;
    int rnum;
} Dedicate;

#ifndef break_if_error
  #define break_if_error(FUNC, CODE, SOCK) { \
  if (CODE < 0) { \
    perror(#FUNC "() failed"); \
    if (SOCK != -1) { \
      close(SOCK); \
      SOCK = -1; \
    } \
    break; }}
#endif /* ndef break_if_error */

#ifndef continue_if_error
  #define continue_if_error(FUNC, CODE, SOCK) { \
  if (CODE < 0) { \
    perror(#FUNC "() failed"); \
    if (SOCK != -1) { \
      close(SOCK); \
      SOCK = -1; \
    } \
    continue; }}
#endif /* ndef continue_if_error */


#ifndef exit_if_error
  #define exit_if_error(FUNC, CODE, SOCK) { \
  if (CODE < 0) { \
    perror(#FUNC "() failed"); \
    if (SOCK != -1) { \
      close(SOCK); \
      SOCK = -1; \
    } \
    return; }}
#endif /* ndef exit_if_error */

/* Macros to retrieve or default argument */
#define ARG(x) getArg(x, anArgc, anArgvPP, "")
#define ARG_DEFAULT(x, aDefaultP) getArg(x, anArgc, anArgvPP, aDefaultP)

// Macro to print out an encoded byte
// Print spaces through }, except for %, the rest print %xx values
#ifndef encode_print
  #define encode_print(DATA_CHAR) { \
  if ((DATA_CHAR < 0x1F) ||\
      (DATA_CHAR == 0x25) ||\
      (DATA_CHAR > 0x7D)) {\
          printf("%%%02.2x",DATA_CHAR);\
      } else { \
          printf("%c",DATA_CHAR);\
  }\
}
#endif

/* Utility functions */
int checkAbbreviation(const char* aStringP, const Abbreviation* anAbbreviationListP, int anAbbreviationN);
int checkBoolean(const char* aStringP);
int checkPrefixCommand(const char* aCommandP);
int initializeThreadSemaphores(struct _vmApiInternalContext* vmapiContextP, const char* aContextNameP, int aCreateFlag);
int getSmapiLevel(struct _vmApiInternalContext* vmapiContextP, char * image, int * smapilevel);
int createDirectories(const char* aFilenameP);
void dumpArea(struct _vmApiInternalContext* vmapiContextP, void * pstor, int len);
Dedicate* getDedicates();
Minidisk* getMinidisks();
int isOSA(struct _vmApiInternalContext* vmapiContextP, char* rdev);
void listAppendLine(struct _vmApiInternalContext* vmapiContextP, List* aListP, const char* aLineP);
void listAppendRecord(List* aListP, Record* aRecordP);
void listDeleteCurrent(List* aListP);
Record* listDequeueRecord(List* aListP);
const char* listNextLine(List* aListP);
const Record* listNextRecord(List* aListP);
void listFree(List* aListP);
void listReset(List* aListP);
void readTraceFile(struct _vmApiInternalContext* vmapiContextP);
void *smMemoryGroupAlloc(struct _vmApiInternalContext* vmapiContextP, size_t size);
int smMemoryGroupFreeAll(struct _vmApiInternalContext* vmapiContextP);
int smMemoryGroupInitialize(struct _vmApiInternalContext* vmapiContextP);
void *smMemoryGroupRealloc(struct _vmApiInternalContext* vmapiContextP, void * chunk, size_t size);
int smMemoryGroupTerminate(struct _vmApiInternalContext* vmapiContextP);
char* strip(char* aLineP, char anOption, char aChar);
void sysinfo(struct _vmApiInternalContext* vmapiContextP, int anArgc, const char**anArgvPP);
int testDigit(char aChar);
const char* vmApiMessageText(struct _vmApiInternalContext* vmapiContextP);
int vmbkendCacheEntryInvalidate(struct _vmApiInternalContext* vmapiContextP, char *pathP, char *useridP);
int vmbkendCheck(struct _vmApiInternalContext* vmapiContextP);
void vmbkendGetCachePath(struct _vmApiInternalContext* vmapiContextP, char *pathP);
void *vmbkendMain(void* vmapiContextP);
void *vmbkendMain_iucv(void* vmapiContextP);
int vmbkendRemoveCachedScanFiles(struct _vmApiInternalContext* vmapiContextP, char *pathP);
void vmbkendRemoveEntireCache(struct _vmApiInternalContext* vmapiContextP, char *cachePathP);
void waitForPendingWorkunits(struct _vmApiInternalContext* vmapiContextP, int waitIntervalInSeconds);  // 0 = wait forever
int cacheFileValid(struct _vmApiInternalContext* vmapiContextP, const char* cFName);

#endif
