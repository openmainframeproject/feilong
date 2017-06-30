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

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/stat.h>
#include <sys/sem.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <pthread.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <dlfcn.h>
#include <ctype.h>
#include <arpa/inet.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <sys/stat.h>
#include <stdbool.h>
#include "vmapiQuery.h"
#include "smPublic.h"
#include "vmapiSystem.h"
#include "vmapiAsynchronous.h"
#include "smapiTableParser.h"
#include "smSocket.h"
#include "vmapiUnDocumented.h"
#include "wrapperutils.h"

#define TARGET_ALL "ALL"
#define VMAPILIB "libzthin.so"
#define USERS_LIST_FILE "users.list"
#define MIN_IDENTITY_NLEN         2  // Minimum length of IDENTITY statement name
#define MIN_MDISK_NLEN            1  // Minimum length of MDISK statement name
#define MIN_USER_NLEN             1  // Minimum length of USER statement name

// Prototype for functions
void errorLog(struct _vmApiInternalContext* vmapiContextP, const char * functionName, const char * lineNumber, int aRc,
        int aReason, const char* aLineP);
void errorLine(struct _vmApiInternalContext* vmapiContextP, const char* aLineP);

int vmbkendSockaddrFileInfo(struct _vmApiInternalContext* vmapiContextP, int readOrWrite, struct sockaddr_in *saddr);

// This function will add a timestamp and then write the data to the syslog
void logLine(struct _vmApiInternalContext* vmapiContextP, char aSeverity, const char* aLineP);
void outputLine(struct _vmApiInternalContext* vmapiContextP, const char* aLineP, int aLogFlag);

bool cacheOnlyModeChecked = false;  // True once we've checked the config file
bool persistentInCacheOnlyMode = false;  // True if we're in cache-only mode

smTrace externSmapiTraceFlags = { { 0 } };  // Externally visible storage for trace

// Semaphore locking fields for trace and the backend
enum SemaphoreIndex {
    ContextSemaphoreIndex = 0, TraceSemaphoreIndex = 1, BackendSemaphoreIndex = 2, NumberOfSemaphores
};

// Next two tables provide information on the amount of additional data that
// comes with each *VMEvent event (ie. datatype 0 data).
static const int vmeClassRows[4] = { 14, 6, 2, 2 };     // Number of rows in vmeventRemainders table
                                                        // for each event class
static const unsigned short int vmeventRemainders[][2] = {
                                // Number of additional data sent with each *VMEvent event which
                                // needs to be pulled from the sent data.
                                // This is in addition to the fields that we are processing.
                                // Class 0
        {0, 0},                 // Type 0 - no remaining data
        {1, 0},                 // Type 1 - no remaining data
        {2, 8+1},               // Type 2
        {3, 8+2},               // Type 3
        {4, 8},                 // Type 4
        {5, 8},                 // Type 5
        {6, 8},                 // Type 6
        {9, 0},                 // Type 9 - no remaining data
        {10, 0},                // Type 10 - no remaining data
        {11, 0},                // Type 11 - no remaining data
        {12, 0},                // Type 12 - no remaining data
        {13, 0},                // Type 13 - no remaining data
        {14, 0},                // Type 14 - no remaining data
        {15, 8},                // Type 15
                                // Don't forget to update the row count if you add rows to class 0
                                // Class 1
        {2, 8+1},               // Type 2
        {3, 8+2},               // Type 3
        {4, 8},                 // Type 4
        {6, 8},                 // Type 6
        {9, 0},                 // Type 9  - no remaining data
        {10, 0},                // Type 10 - no remaining data
                                // Don't forget to update the row count if you add rows to class 1
                                // Class 2
        {7, 0},                 // Type 7 - no remaining data
        {8, 8+8+1+1},           // Type 8
                                // Don't forget to update the row count if you add rows to class 2
                                // Class 3
        {7, 0},                 // Type 7 - no remaining data
        {8, 8+8+1+1},           // Type 8
                                // Don't forget to update the row count if you add rows to class 3
                                // Class 4
        {16, 8+8+2+1+1+2+1+1},  // Type 16
        {17, 8+8+2+1+1+2+1+1},  // Type 17
        {18, 8+8+2+1+1+2+1+1},  // Type 18
        {19, 8+8+2+1+1+2+1+1}   // Type 17
                                // Don't forget to update the row count if you add rows to class 4
};

/* Context ones */
static struct sembuf contextSemaphoreReserve[] = { { ContextSemaphoreIndex, -1,    SEM_UNDO } };
static const int contextSemaphoreReserveN = sizeof(contextSemaphoreReserve)    / sizeof(contextSemaphoreReserve[0]);

static struct sembuf contextSemaphoreRelease[] = { { ContextSemaphoreIndex, 1, SEM_UNDO } };
static const int contextSemaphoreReleaseN = sizeof(contextSemaphoreRelease)    / sizeof(contextSemaphoreRelease[0]);

/* Trace ones */
static struct sembuf traceSemaphoreReserve[] = { { TraceSemaphoreIndex, -1,    SEM_UNDO } };
static const int traceSemaphoreReserveN = sizeof(traceSemaphoreReserve)    / sizeof(traceSemaphoreReserve[0]);

static struct sembuf traceSemaphoreRelease[] = { { TraceSemaphoreIndex, 1, SEM_UNDO } };
static const int traceSemaphoreReleaseN = sizeof(traceSemaphoreRelease)    / sizeof(traceSemaphoreRelease[0]);

/* vmbackend ones */
static struct sembuf backendSemaphoreReserve[] = { { BackendSemaphoreIndex, -1, SEM_UNDO } };
static const int backendSemaphoreReserveN = sizeof(backendSemaphoreReserve) / sizeof(backendSemaphoreReserve[0]);

static struct sembuf backendSemaphoreRelease[] = { { BackendSemaphoreIndex, 1, SEM_UNDO } };
static const int backendSemaphoreReleaseN = sizeof(backendSemaphoreRelease) / sizeof(backendSemaphoreRelease[0]);

pthread_mutex_t mutex;
pthread_cond_t thread_initialized_cv;

typedef struct vmbkendMain_tdata {
    int thread_no;
    struct in_addr Addrs;
} vmbkend_tdata;

int vmbkendMain_Event_UnSubscribe(struct _vmApiInternalContext* vmapiContextP);

int vmbkendMain_Event_Subscribe(struct _vmApiInternalContext* vmapiContextP);

int vmbkendMain_setSmapiSubscribeEventData(
        struct _vmApiInternalContext* vmapiContextP, int outputBufferSize,
        int sockDesc, int requestId, char * cachePath);

int checkAbbreviation(const char* aStringP,
        const Abbreviation* anAbbreviationListP, int anAbbreviationN) {
    int x;
    int checkL;
    int stringL;

    int isAbbreviation = 0;
    if (aStringP == 0)
        return 0;

    stringL = strlen(aStringP);

    for (x = 0; x < anAbbreviationN; ++x) {
        checkL = anAbbreviationListP[x].minimum;
        if (checkL > stringL)
            continue;
        if (0 == strncasecmp(aStringP, anAbbreviationListP[x].nameP, checkL)) {
            isAbbreviation = 1;
            break;
        }
    }

    return isAbbreviation;
}

int checkBoolean(const char* aStringP) {
    const Abbreviation booleanTrues[] = { { "TRUE", 1 }, { "YES", 1 }, { "1", 1 } };
    return checkAbbreviation(aStringP, booleanTrues, (sizeof(booleanTrues) / sizeof(booleanTrues[0])));
}

int checkPrefixCommand(const char* aCommandP) {
    const Abbreviation prefixCommands[] = { { "REQUEST", 3 }, { "TOSYS", 5 }, { "TONODE", 6 }, { "ASUSER", 2 }, {
            "BYUSER", 2 }, { "FORUSER", 3 }, { "PRESET", 6 }, { "MULTIUSER", 5 }, { "ATNODE", 6 }, { "ATSYS", 5 } };

    return checkAbbreviation(aCommandP, prefixCommands, (sizeof(prefixCommands) / sizeof(prefixCommands[0])));
}

const char* contextGetMessageFilename(struct _vmApiInternalContext* vmapiContextP, char* aBufferP, int aBufferS) {
    char line[LINESIZE];
    int len = 0;
    const char* msgName = "messages";
    const char* msgSuffixName = ".eng";  // Language-dependent
    char* pathP = 0;
    int pathL = 0;

    // Obtain VMAPI environment variable
    memset(aBufferP, 0, aBufferS);
    pathP = getenv("VMAPI");

    if (pathP) {
        pathL = strlen(pathP);
        len = pathL + 12;  // Adjust once we know NLS file structure
        if (len > aBufferS) {
            sprintf(line, "contextGetMessageFilename: Insufficient path buffer size; needed %d, have %d.", len,
                    (aBufferS - 1));
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcContext, RsInternalBufferTooSmall, line);
        }
        strncpy(aBufferP, pathP, pathL);
        if (aBufferP[pathL - 1] == '/') {
            strcat(aBufferP, ".cimvm/");
        } else {
            strcat(aBufferP, "/.cimvm/");
        }
    } else {
        strcpy(aBufferP, "/root/.cimvm/");
    }

    strcat(aBufferP, msgName);  // Adjust when we know real NLS stuff
    strcat(aBufferP, msgSuffixName);

    return aBufferP;
}

int createDirectories(const char* aFilenameP) {
    int filenameL = strlen(aFilenameP);
    char filename[LINESIZE];
    char* sP = 0;
    char* eP = 0;

    if (filenameL >= (sizeof(filename) - 1))
        return 0;

    memset(filename, 0, sizeof(filename));
    strcpy(filename, aFilenameP);

    sP = filename;
    eP = filename + sizeof(filename) - 1;
    while ((sP < eP) && (sP = strchr(sP + 1, '/'))) {
        *sP = '\0';
        mkdir(filename, S_IRWXU);
        *sP = '/';
    }

    return 0;
}

int initializeThreadSemaphores(struct _vmApiInternalContext* vmapiContextP, const char* aContextNameP, int aCreateFlag) {
    char pathAndFile[PATHLENGTH + strlen(CACHE_SEMAPHORE_FILENAME)];
    int len = 0;
    char line[LINESIZE];
    union semun {
        int val;
        struct semid_ds* buf;
        ushort* array;
    } semArgument;
    int semInitRequired = 0;
    int pathLength = 0;
    char* pathPtr = 0;
    int rc = 0;

    memset(vmapiContextP->path, 0, sizeof(vmapiContextP->path));  // Clear out path string
    memset(pathAndFile, 0, sizeof(pathAndFile));

    // Save the name passed in into the context if specified
    if (strlen(aContextNameP) > 0) {
        strncpy(vmapiContextP->name, aContextNameP, sizeof(vmapiContextP->name) - 1);
    }

    // Obtain VMAPI environment variable
    pathPtr = getenv("ZTHIN_VAR");
    if (pathPtr) {  // ZTHIN_VAR is defined
        pathLength = strlen(pathPtr);
        len = pathLength + strlen(CACHE_SEMAPHORE_DIRECTORY);
        if (len > sizeof(pathAndFile)) {
            sprintf(line, "contextReserve: Insufficient path buffer size; needed %d, have %d.", len,
                    sizeof(pathAndFile) - 1);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcContext, RsInternalBufferTooSmall, line);
            return PROCESSING_ERROR;
        }
        strncpy(vmapiContextP->path, pathPtr, sizeof(vmapiContextP->path) - (strlen(CACHE_SEMAPHORE_DIRECTORY) + 2));
        len = strlen(vmapiContextP->path);
        if (vmapiContextP->path[len - 1] == '/') {
            strcat(vmapiContextP->path, CACHE_SEMAPHORE_DIRECTORY);  // Add on .vmapi/ directory
        } else {
            strcat(vmapiContextP->path, "/");
            strcat(vmapiContextP->path, CACHE_SEMAPHORE_DIRECTORY);
        }
    } else {
        // ZTHIN_VAR is undefined, set default
        strcpy(vmapiContextP->path, CACHE_PATH_DEFAULT);
    }

    // Create or obtain semaphore set
    strcpy(pathAndFile, vmapiContextP->path);
    strcat(pathAndFile, CACHE_SEMAPHORE_FILENAME);
    createDirectories(pathAndFile);

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
    sprintf(line, "initializeThreadSemaphores: Semaphore file name is %s\n", pathAndFile);
    TRACE_END_DEBUG(vmapiContextP, line);

    // Try to open or create a file that can be used for semaphore handle
    FILE* semFileP = fopen(pathAndFile, "r");
    if (!semFileP) {
        semFileP = fopen(pathAndFile, "w");
    }
    if (semFileP) {
        fclose(semFileP);
    }

    vmapiContextP->semKey = ftok(pathAndFile, 'V');
    vmapiContextP->semId = semget(vmapiContextP->semKey, 2, 0600);

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
    sprintf(line, "initializeThreadSemaphores: semKey = %ll \n", vmapiContextP->semKey);
    TRACE_END_DEBUG(vmapiContextP, line);

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
    sprintf(line, "initializeThreadSemaphores: semId = %d \n", vmapiContextP->semId);
    TRACE_END_DEBUG(vmapiContextP, line);

    if ((0 > vmapiContextP->semId) && (ENOENT == errno)) {
        semInitRequired = 1;
        vmapiContextP->semId = semget(vmapiContextP->semKey, NumberOfSemaphores, 0600 | IPC_CREAT);
    }

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
    sprintf(line, "initializeThreadSemaphores: semInitRequired = %d \n", semInitRequired);
    TRACE_END_DEBUG(vmapiContextP, line);
    if (0 > vmapiContextP->semId) {
        vmapiContextP->errnoSaved  = errno;
        sprintf(line, "contextReserve: Unable to create semaphore array identified by %s; errno=%d text: %s",
            pathAndFile, errno, strerror(errno));
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotCreated, line);
        return PROCESSING_ERROR;
    }

    if (semInitRequired) {
        semArgument.val = 1;
        rc = semctl(vmapiContextP->semId, TraceSemaphoreIndex, SETVAL, semArgument);
        if (0 > rc) {
            vmapiContextP->errnoSaved  = errno;
            sprintf(line, "Unable to initialize Trace semaphore; errno=%d text: %s", errno, strerror(errno));
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotCreated, line);
            return PROCESSING_ERROR;
        }

        rc = semctl(vmapiContextP->semId, BackendSemaphoreIndex, SETVAL, semArgument);
        if (0 > rc) {
            vmapiContextP->errnoSaved  = errno;
            sprintf(line, "Unable to initialize Backend semaphore; errno=%d text: %s", errno, strerror(errno));
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotCreated, line);
            return PROCESSING_ERROR;
        }
        rc = semctl(vmapiContextP->semId, ContextSemaphoreIndex, SETVAL, semArgument);
        if (0 > rc) {
            vmapiContextP->errnoSaved  = errno;
            sprintf(line, "Unable to initialize context semaphore; errno=%d text: %s", errno, strerror(errno));
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotCreated, line);
            return PROCESSING_ERROR;
        }
    }

    // Obtain the context semaphore before manipulating context related stuff
    rc = semop(vmapiContextP->semId, contextSemaphoreReserve, contextSemaphoreReserveN);
    if (rc < 0) {
        vmapiContextP->errnoSaved  = errno;
        sprintf(line, "contextReserve: semop (decrement) failed; errno=%d text: %s", errno, strerror(errno));
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotObtained, line);
        return PROCESSING_ERROR;
    }

    // Create or obtain context for the name passed in
    strcpy(pathAndFile, vmapiContextP->path);
    strcat(pathAndFile, CACHE_DIRECTORY);
    createDirectories(pathAndFile);

    // Release the Context semaphore after manipulating context related stuff
    rc = semop(vmapiContextP->semId, contextSemaphoreRelease, contextSemaphoreReleaseN);
    if (rc < 0) {
        vmapiContextP->errnoSaved  = errno;
        sprintf(line, "contextReserve: semop (increment) failed, errno=%d text: %s", errno, strerror(errno));
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsSemaphoreNotReleased, line);
        return PROCESSING_ERROR;
    }
    vmapiContextP->contextCreatedFlag = 1;  // Set flag to indicate context set up
    return 0;
}

/**
 * Unit test code
 */
void dumpArea(struct _vmApiInternalContext* vmapiContextP, void * pstor, int len) {
    unsigned int offset, i, j, k;
    char trans[17];
    char line[LINESIZE];
    char phrase[80];
    unsigned char storByte;
    int transAvail;
    offset = 0;
    transAvail = 0;

    for (k = 0; k < sizeof(trans); k++) {
        trans[k] = '\0';
    }

    storByte = *((char *) pstor);
    sprintf(line, "=== dump of area %p for length %d ", pstor, len);
    for (i = 0; i < len; i++) {
        j = i % 16;
        if (j == 0) {
            if (transAvail) {
                sprintf(phrase, " %s", trans);
                strcat(line, phrase);
                for (k = 0; k < sizeof(trans); k++) {
                    trans[k] = '\0';
                }
                transAvail = 0;
            }
            strcat(line, "\n");
            logLine(vmapiContextP, LOGLINE_DEBUG, line);
            sprintf(line, "%6d %14p   ", offset, (pstor + offset));
            offset += 16;
        } else if (0 == (k = i % 4)) {
            strcat(line, " ");
        }

        storByte = *((char*) (pstor + i));
        if (isprint(storByte)) {
            trans[j] = storByte;
        } else {
            trans[j] = '.';
        }
        transAvail = 1;

        sprintf(phrase, "%02X", storByte);
        strcat(line, phrase);
    }

    if (transAvail) {
        for (k = j + 1; k < 16; k++) {
            if (0 == k % 4) {
                strcat(line, " ");
            }
            strcat(line, "  ");
        }
        sprintf(phrase, " %s", trans);
        strcat(line, phrase);
    }
    strcat(line, "\n");
    logLine(vmapiContextP, LOGLINE_DEBUG, line);
}

void errorLog(struct _vmApiInternalContext* vmapiContextP, const char * functionName, const char * lineNumber, int aRc,
        int aReason, const char* aLineP) {
    char line[LINESIZE];
    sprintf(line, "%s:%s %s", functionName, lineNumber, aLineP);

    vmapiContextP->rc = aRc;
    vmapiContextP->reason = aReason;
    errorLine(vmapiContextP, line);
}

void errorLine(struct _vmApiInternalContext* vmapiContextP, const char* aLineP) {
    // If this is the first error for this context, save it
    if (!vmapiContextP->firstFailureCaptured) {
        strncpy(vmapiContextP->strFirstFailureMsg, aLineP, FIRST_FAILURE_MESSAGE_MAX_LEN);
        vmapiContextP->strFirstFailureMsg[FIRST_FAILURE_MESSAGE_MAX_LEN] = '\0';
        vmapiContextP->firstFailureCaptured = 1;  // 1:true
    }
    outputLine(vmapiContextP, aLineP, 1);
}

char* getArg(int anIndex, int anArgc, const char** anArgvPP, const char* aDefaultP) {
    int x = anIndex;
    if (x > (anArgc - 1))
        return (char*) aDefaultP;

    return (char*) (anArgvPP[x] ? anArgvPP[x] : aDefaultP);
}

/**
 * Append data to a list
 */
void listAppendLine(struct _vmApiInternalContext* vmapiContextP, List* aListP, const char* aLineP) {
    int lineL = strlen(aLineP);
    Record* newRecordP = smMemoryGroupAlloc(vmapiContextP, sizeof(Record) + lineL + 1);
    if (newRecordP == 0)
        return;

    strncpy(newRecordP->data, aLineP, lineL);
    listAppendRecord(aListP, newRecordP);
}

/**
 * Append data to a list
 */
void listAppendRecord(List* aListP, Record* aRecordP) {
    if (aListP->firstP == 0) {
        aListP->firstP = aRecordP;
    } else {
        if (aListP->currentP == 0) {
            aListP->currentP = aListP->firstP;
            while (aListP->currentP->nextP) {
                aListP->currentP = aListP->currentP->nextP;
            }
        }

        aListP->currentP->nextP = aRecordP;
    }

    aListP->currentP = aRecordP;
    ++(aListP->size);
    aRecordP->nextP = 0;
}

/**
 * Delete the current record from the list
 */
void listDeleteCurrent(List* aListP) {
    Record* currentP = 0;
    Record* prevP = 0;

    if (aListP == 0)
        return;

    if (aListP->firstP == 0)
        return;

    // Current not set yet ?
    if (aListP->currentP == 0)
        return;

    currentP = aListP->currentP;
    if (aListP->firstP == aListP->currentP) {
        aListP->currentP = aListP->firstP->nextP;
        aListP->firstP = aListP->firstP->nextP;
    } else {
        // Find the record before aListP->currentP
        prevP = aListP->firstP;
        while (prevP && (prevP->nextP != currentP)) {
            prevP = prevP->nextP;
        }

        // Remove recordP from list
        if (prevP) {
            prevP->nextP = currentP->nextP;
        }
    }

    free(currentP);
    --(aListP->size);
}

/**
 * Dequeue a line from the front of the list
 */
Record* listDequeueRecord(List* aListP) {
    Record* recordP = 0;

    if (aListP == 0)
        return 0;

    if (aListP->firstP == 0)
        return 0;

    recordP = aListP->firstP;

    if (recordP == aListP->currentP) {
        aListP->currentP = recordP->nextP;
    }

    aListP->firstP = recordP->nextP;
    --(aListP->size);
    return recordP;
}

/**
 * Free all records from a list
 */
void listFree(List* aListP) {
    Record* recordP = aListP->firstP;
    Record* nextP = 0;

    while (recordP) {
        nextP = recordP->nextP;
        free(recordP);
        recordP = nextP;
    }

    aListP->firstP = 0;
    aListP->currentP = 0;
    aListP->size = 0;
}

/**
 * Return Append data to a list
 */
const char* listNextLine(List* aListP) {
    const Record* recordP = listNextRecord(aListP);
    if (recordP == 0)
        return 0;
    return recordP->data;
}

/**
 * Return Append data to a list
 */
const Record* listNextRecord(List* aListP) {
    if (aListP == 0)
        return 0;

    if (aListP->currentP == 0) {
        // This causes a wrap around after the 0 record was returned once,
        // that is, after "end of list" was returned once.
        aListP->currentP = aListP->firstP;
    } else {
        aListP->currentP = aListP->currentP->nextP;
    }

    return aListP->currentP;
}

/**
 * Free all records from a list
 */
void listReset(List* aListP) {
    if (aListP == 0)
        return;

    aListP->currentP = 0;
}

void logLine(struct _vmApiInternalContext* vmapiContextP, char aSeverity, const char* aLineP) {
    char line[LINESIZE];
    const char* prefix = "+         ";
    int prefixL = 0;
    int syslogSeverity = LOG_INFO;

    pid_t pidTrace;
    pthread_t myThread;
    int temp;

    pidTrace = getpid();
    myThread = pthread_self();

    switch (aSeverity) {
    case 'D':
        syslogSeverity = LOG_DEBUG;
        break;
    case 'E':
        syslogSeverity = LOG_ERR;
        break;
    case 'I':
        syslogSeverity = LOG_INFO;
        break;
    case 'N':
        syslogSeverity = LOG_NOTICE;
        break;
    case 'W':
        syslogSeverity = LOG_WARNING;
        break;
    case 'X':
        syslogSeverity = LOG_ERR;
        break;
    default:
        syslogSeverity = LOG_INFO;
        break;
    }

    if (vmapiContextP->printOffset <= 0) {
        sprintf(line, "%d.%p ", pidTrace, myThread);  // Add process id and blank
        temp = strlen(line);
        strncpy(line + temp, aLineP, LINESIZE - temp);
    } else {
        prefixL = 2 * vmapiContextP->printOffset;
        if (prefixL > 10)
            prefixL = 10;
        snprintf(line, LINESIZE, "%*.s%s\n", prefixL, prefix, aLineP);
    }

    openlog(NULL, 0, LOG_LOCAL4);
    syslog(syslogSeverity, "%s", line);
    closelog();
}

void outputLine(struct _vmApiInternalContext* vmapiContextP,
        const char* aLineP, int aLogFlag) {
    if (aLogFlag)
        logLine(vmapiContextP, ' ', aLineP);
    listAppendLine(vmapiContextP, &vmapiContextP->outputStream, aLineP);
}

/**
 * This function will read the trace file
 */
void readTraceFile(struct _vmApiInternalContext* vmapiContextP) {
    char pathAndFile[PATHLENGTH + strlen(TRACE_LEVELS_FILE)];
    char* pathP = 0;
    int pathLength = 0;
    unsigned int newTraceFlags[TRACE_AREAS_COUNT];
    unsigned int newTraceFlagFound[TRACE_AREAS_COUNT];
    char lineData[LINESIZE];
    int lineDataLength;
    char line[BUFLEN];
    FILE* traceFileP = 0;
    int keywordIndex;
    int traceSettingIndex;
    int x;
    char * targetPtr;

    // Return if this has been set up already
    if (vmapiContextP->smTraceDetails->traceFileRead) {
    	return;
    }

    // Init new trace flags array
    for (x = 0; x < TRACE_AREAS_COUNT; x++) {
        newTraceFlags[x] = 0;
        newTraceFlagFound[x] = 0;
    }

    // Get the path and file name string for the trace command input
    memset(pathAndFile, 0, sizeof(pathAndFile));
    strcpy(pathAndFile, TRACE_LEVELS_FILE_DIRECTORY);  // Initialize to default path
    strcat(pathAndFile, TRACE_LEVELS_FILE);  // Add on file name

    pathP = getenv("VMAPI");  // Is there a VMAPI environment variable set?
    if (pathP) {
        pathLength = strlen(pathP) + sizeof(TRACE_LEVELS_FILE) + 1;
        if (pathLength > sizeof(pathAndFile)) {
            sprintf(line, "readTraceFile: Insufficient path buffer size; needed %d, have %d.", pathLength, (int) sizeof(pathAndFile));
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcContext, RsInternalBufferTooSmall, line);
            return;
        }
        strncpy(pathAndFile, pathP, pathLength);
        if (pathAndFile[pathLength - 1] == '/') {
            strcat(pathAndFile, TRACE_LEVELS_FILE);
        } else {
            strcat(pathAndFile, "/");
            strcat(pathAndFile, TRACE_LEVELS_FILE);
        }
    }

    // Now open the file and figure out the trace flags to set/reset
    traceFileP = fopen(pathAndFile, "r");
    if (traceFileP) {
        vmapiContextP->smTraceDetails->traceFileRead = 1;  // Set flag that said we read/tried to read trace settings

        // Look for keywords and comments in the trace command file
        memset(lineData, 0, sizeof(lineData));
        while (fgets(lineData, sizeof(lineData), traceFileP)) {
            lineDataLength = strlen(lineData);
            // Ignore all 0 length input
            if (0 == lineDataLength) {
                printf("Ignoring trace options blank line");
                continue;
            }

            // Ignore comment lines - begin with '#'
            if (0 != strncmp(lineData, "#", 1)) {
                // Try to find a keyword match
                keywordIndex = -1;
                for (x = 0; x < TRACE_AREAS_COUNT; x++) {
                    if (0 == strncmp(lineData, TRACE_KEYWORDS[x],
                            strlen(TRACE_KEYWORDS[x]))) {
                        keywordIndex = x;
                        break;
                    }
                }

                // If no keyword found, log an error
                if (keywordIndex == -1) {
                    sprintf(line, "readTraceFile: Unknown keyword on line: <%s> \n", lineData);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                            RcFunction, RsFunctionUnknown, line);
                    fclose(traceFileP);
                    return;
                }

                targetPtr = strstr(lineData, "=");  // Find the = sign
                if (0 == targetPtr) {
                    sprintf(line, "readTraceFile: Missing = on line: <%s> \n", lineData);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                            RcFunction, RsFunctionUnknown, line);
                    fclose(traceFileP);
                    return;
                }

                // Look for a trace settings value
                traceSettingIndex = -1;
                for (x = 0; x < TRACE_LEVELS_COUNT; x++) {
                    if (0 != strstr(targetPtr, TRACE_LEVELS[x])) {
                        traceSettingIndex = x;
                        break;
                    }
                }

                // If no trace setting keyword found, log an error
                if (traceSettingIndex == -1) {
                    sprintf(line, "readTraceFile: Unknown trace setting on line: <%s> \n", lineData);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                            RcFunction, RsFunctionUnknown, line);
                    fclose(traceFileP);
                    return;
                }

                // Now set or reset the bits in the new trace flags variable
                if (TRACELEVEL_OFF == traceSettingIndex) {  // If the trace is to be turned off
                    newTraceFlags[keywordIndex] = 0;
                    newTraceFlagFound[keywordIndex] = 1;
                } else {
                    newTraceFlags[keywordIndex] |= TRACE_FLAG_VALUES[traceSettingIndex];
                    newTraceFlagFound[keywordIndex] = 1;
                }
            }

            memset(lineData, 0, sizeof(lineData));
        }

        // Set the trace flags pointed to from the context
        // If there was a keyword found otherwise skip setting it
        for (x = 0; x < TRACE_AREAS_COUNT; x++) {
            if (newTraceFlagFound[x]) {
                vmapiContextP->smTraceDetails->traceFlags[x] = newTraceFlags[x];
            }
        }

        fclose(traceFileP);
    }

    return;
}

char* strip(char* aLineP, char anOption, char aChar) {
    char* lineP = aLineP;
    char* lastP = 0;
    int lineL = 0;
    int x;

    if (lineP == 0)
        return lineP;

    // Strip leading chars
    if ((anOption == 'L') || (anOption == 'B')) {
        lineL = strlen(lineP);
        if (lineL > 0) {
            for (x = 0; x < lineL; ++x, ++lineP) {
                if (*lineP != aChar)
                    break;
            }
        }
    }

    // Strip trailing chars
    if ((anOption == 'T') || (anOption == 'B')) {
        lineL = strlen(lineP);
        if (lineL > 0) {
            lastP = lineP + lineL - 1;
            for (x = lineL; x > 0; --x, --lastP) {
                if (*lastP != aChar)
                    break;
                *lastP = 0;
            }
        }
    }

    return lineP;
}

void sysinfo(struct _vmApiInternalContext* vmapiContextP, int anArgc, const char** anArgvPP) {
    char buffer[LINESIZE];
    char* bufferP = 0;
    int len = 0;

    FILE* sysinfoP = fopen("/proc/sysinfo", "r");
    if (sysinfoP) {
        rewind(sysinfoP);
        while (bufferP = fgets(buffer, sizeof(buffer), sysinfoP)) {
            len = strlen(bufferP);
            if ((len > 0) && (bufferP[len - 1] == '\n')) {
                bufferP[len - 1] = 0;
            }
            outputLine(vmapiContextP, bufferP, 0);
        }
        fclose(sysinfoP);
    }
}

/**
 * This function removes the password field of USER and MDISK statements
 */
void hidePassword(char *directoryRecord) {
    char tempBuffer[100];
    char * savePtr;
    int length = strlen(directoryRecord);
    int nameLen;
    char replacedString[80];
    char * token;
    memcpy(tempBuffer, directoryRecord, length);
    tempBuffer[length]= '\0';
    token = strtok_r(tempBuffer, " ", &savePtr);

    if (token != NULL) {
        nameLen = strlen(token);
        if (((strncmp( token, "USER", nameLen ) == 0 ) &&
                (nameLen >= MIN_USER_NLEN)) ||
                ((strncmp(token, "IDENTITY", nameLen) == 0) &&
                (nameLen >= MIN_IDENTITY_NLEN))) {
            strcpy(replacedString, token);
            strcat(replacedString, " ");

            token = strtok_r(NULL, " ", &savePtr);
            strcat(replacedString, token);  // This is userid
            strcat(replacedString, " ");

            token = strtok_r(NULL, " ", &savePtr);
            strcat(replacedString, "*");  // This is password
            strcat(replacedString, " ");

            while (token != NULL) {
                token = strtok_r(NULL, " ", &savePtr);
                if (token != NULL) {
                    strcat(replacedString, token);  // This is userid
                    strcat(replacedString, " ");
                }
            }

            strcpy(directoryRecord, replacedString);
        } else if ((strncmp(token, "MDISK", nameLen) == 0) && (nameLen >= MIN_MDISK_NLEN)) {
                strcpy(replacedString, token);
                strcat(replacedString, " ");

                // MDISK address(VDEV) value
                token = strtok_r(NULL, " ", &savePtr);
                strcat(replacedString, token);
                strcat(replacedString, " ");

                // MDISK DEV type value
                token = strtok_r(NULL, " ", &savePtr);
                strcat(replacedString, token);
                strcat(replacedString, " ");

                token = strtok_r(NULL, " ", &savePtr);
                if (token != NULL) {
                    // DEVICE number value
                    if (strncasecmp(token, "DEVNO", strlen(token)) == 0) {
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        token = strtok_r(NULL, " ", &savePtr);
                        strcat(replacedString, token);
                        strcat(replacedString, " ");
                    } else if (strncasecmp(token, "V-DISK", strlen(token)) == 0) {
                        // V_DISK value in blocks
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        token = strtok_r(NULL, " ", &savePtr);
                        strcat(replacedString, token);
                        strcat(replacedString, " ");
                    } else if (strncasecmp(token, "T-DISK", strlen(token)) == 0) {
                        // T-DISK value in cylinders or blocks
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        token = strtok_r(NULL, " ", &savePtr);
                        strcat(replacedString, token);
                        strcat(replacedString, " ");
                    } else {
                        // CYL or BLK start
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        // CYL or BLK end
                        token = strtok_r(NULL, " " , &savePtr);
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        // Volume serial number
                        token = strtok_r(NULL, " ", &savePtr);
                        strcat(replacedString, token);
                        strcat(replacedString, " ");
                    }

                    token = strtok_r(NULL, " ", &savePtr);
                    if (token != NULL) {
                        // Access mode
                        strcat(replacedString, token);
                        strcat(replacedString, " ");

                        token = strtok_r(NULL, " ", &savePtr);
                        if (token != NULL) {
                            strcat(replacedString, "*");
                            strcat(replacedString, " ");

                            token = strtok_r(NULL, " ", &savePtr);
                            if (token != NULL) {
                                strcat(replacedString, "*");
                                strcat(replacedString, " ");

                                token = strtok_r(NULL, " ", &savePtr);
                                if (token != NULL) {
                                    strcat(replacedString, "*");
                                    strcat(replacedString, " ");
                                }
                            }
                        }

                        strcpy(directoryRecord, replacedString);
                    }
                }
            }
        }
}

int testDigit(char aChar) {
    static char digits[] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' };
    int x;
    for (x = 0; x < (sizeof(digits) / sizeof(digits[0])); ++x) {
        if (aChar == digits[x])
            return 1;
    }

    return 0;
}

const char* vmApiMessageText(vmApiInternalContext* contextP) {
    const char* noCtxMsgP = "(No message available - VmApi context missing)";
    const char* noMsgP = "(No message available for return/reason code pair)";
    int rc = 0;
    int rs = 0;
    const char* msgFilenameP = 0;
    FILE* msgFileP = 0;
    char* targetP = 0;
    char* rcP = 0;
    char* rsP = 0;
    char rcS[6];
    char rsS[6];

    if (contextP == 0)
        return noCtxMsgP;

    strcpy(contextP->emsg, noMsgP); /* Default */
    char filename[sizeof(contextP->path) + 15];  // Adjust once NLS filenames settled

    /**
     * Message text comes from the translatable message file
     */
    char resultLine[LINESIZE];
    int resultLineL = 0;
    msgFilenameP = contextGetMessageFilename(contextP, filename, sizeof(filename));
    if (msgFilenameP) {
        msgFileP = fopen(msgFilenameP, "r");
        if (msgFileP) {
            // Look for matching 'VMAPI rc reason' in message file
            while (fgets(resultLine, sizeof(resultLine), msgFileP)) {
                resultLineL = strlen(resultLine);
                if (0 != strncmp(resultLine, "#", 1)) {  // Ignore comment lines - begin with '#'
                    if (0 == strncmp(resultLine, "VMAPI", 5)) {  // Only if component is VMAPI strip off second word (rc) and third word (reason)
                        targetP = strstr(resultLine, " ");  // First blank
                        if (targetP) {
                            rcP = targetP + 1;
                            while (rcP && (*rcP != ' '))
                                ++rcP;  // First blank after RC

                            strncpy(rcS, targetP + 1, ((rcP) - (targetP + 1) + 1));
                            rc = atoi(rcS);

                            rsP = rcP + 1;  // Skip blank
                            while (rsP && (*rsP != ' '))
                                ++rsP;  // First blank after RS

                            strncpy(rsS, rcP + 1, ((rsP) - (rcP + 1) + 1));
                            rs = atoi(rsS);

                            if ((rc == contextP->rc)
                                    && (rs == contextP->reason)) {
                                strcpy(contextP->emsg, resultLine);
                                break;
                            }

                            /**
                             * If no specific reason code matches, use return-code-only
                             * message. This requires that the RS=0 message for a specific
                             * return code be placed as the last message for that return
                             * code in the message file.
                             */
                            if ((rc == contextP->rc) && (rs == 0)) {
                                strcpy(contextP->emsg, resultLine);
                                break;
                            }
                        }
                    }
                }
            }

            // If message file can't be opened or msg isn't in file, return
            // with the default message set above
            fclose(msgFileP);
        }
    }
    return contextP->emsg;
}

/**
 * Procedure: vmbkendcacheEntryInvalidate
 *
 * Purpose: Mark the specified cache entry as invalid.
 *
 * Input: Pointer to cache path
 *        Name of the user ID to invalidate
 *
 * Output:
 *   0: Invalidate performed successfully
 *   1: Invalidate unsuccessful because stat indicated ENOENT
 *   2: Invalidate unsuccessful because stat got some other error
 *   3: Invalidated by removing cache entry due to fopen failure
 *   4: The fopen failed and the remove failed also.
 *
 * Operation:
 *   Generate the name of the cache file based on the inputs.
 *   If the cache file can be opened, write 'Invalid' status to beginning.
 *   Else try to remove the file.
 */
int vmbkendCacheEntryInvalidate(struct _vmApiInternalContext* vmapiContextP, char *pathP, char *useridP) {
    char cacheEntry[CACHEENTRYLEN];
    int rc;
    int exitrc;
    struct stat statBuf;

    exitrc = 0;  // Initialize to success
    sprintf(cacheEntry, "%s%.8s.direct", pathP, useridP);

    // If the cache file doesn't exist, nothing to do
    rc = stat(cacheEntry, &statBuf);
    if (rc == -1) {
        // Can't continue but check the reason for the stat failing
        if (errno == ENOENT) {
            vmapiContextP->errnoSaved  = errno;
            return 1;
        } else {
            vmapiContextP->errnoSaved  = errno;
            return 2;
        }
    }

    rc = remove(cacheEntry);
    if (rc == -1) {
        exitrc = 4;
    } else {
        exitrc = 3;
    }
    return exitrc;
}

int vmbkendCheck(struct _vmApiInternalContext* vmapiContextP) {
    int rc;
    int backendSemaphoreValue = 0;
    void *vmapiPtr = NULL;

    rc = 0;
    pthread_t thread;
    pthread_attr_t attr;
    // Check if backend already running and return in this case
    backendSemaphoreValue = semctl(vmapiContextP->semId, BackendSemaphoreIndex, GETVAL, 0);

    if (1 != backendSemaphoreValue) {
        vmapiContextP->checkBackendFlag = 1;  // Mark the backend as running
        return rc;  // Backend running
    }

    // If vmbkend daemon not started, start it
    // Create a pthread and call the vmbkendMain
    vmapiPtr = (void*) dlopen(VMAPILIB, RTLD_NOW);  // Load the library
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
    pthread_mutex_lock(&mutex);
    rc = pthread_create(&thread, &attr, vmbkendMain, (void *) vmapiContextP);
    pthread_cond_wait(&thread_initialized_cv, &mutex);
    return 0;
}

/**
 * Procedure: vmbkendgetCachePath
 *
 * Purpose: Return the path to the $VMAPI/.vmapi/cache directory, where
 *          $VMAPI is the VMAPI environment variable.  If VMAPI is not
 *          defined, the current working directory '.' is used.
 *
 *          An example of the directory returned is as follows (note the
 *          slash at the end): /foo/bar/.vmapi/cache/
 *
 * Input: Pointer to string for where to put the cache path
 *
 * Output: None
 *
 * Operation:
 *   Get VMAPI environment variable.
 *   Pull together the cache directory using the VMAPI value.
 */
void vmbkendGetCachePath(struct _vmApiInternalContext* vmapiContextP, char *pathP) {
    char line[LINESIZE];
    int retValue;

    TRACE_ENTRY_FLOW(vmapiContextP , TRACEAREA_ZTHIN_GENERAL);
    // Obtain path to $VMAPI/.vmapi/cache
    // If no (context) path string call to initialize things
    if (1 != vmapiContextP->contextCreatedFlag) {
        retValue = initializeThreadSemaphores(vmapiContextP, "", 1);  // Create context using no name to override current context name
        if (retValue) {
            sprintf(line, "vmbkendGetCachePath(): context reserve() returned error: %d\n", retValue);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
            return;
        }
    }

    strcpy(pathP, vmapiContextP->path);
    strcat(pathP, CACHE_DIRECTORY);

    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendGetCachePath:  The cache path is (%s)\n", pathP);
        TRACE_END_DEBUG(vmapiContextP, line);

    TRACE_EXIT_FLOW(vmapiContextP , TRACEAREA_ZTHIN_GENERAL, 0);
    return;
}

void *vmbkendMain(void *data) {
    int serverSock;
    struct sockaddr_in serverSockaddr;
    struct sockaddr_in serverSockaddr1;
    struct sockaddr_in clientSockaddr;
    struct sockaddr_in notificationSocketInfo;
    struct sockaddr_in previousSockaddr;
    struct sembuf operations[1];
    int socklen;
    int rc;
    int clientLen;
    int bytesRead;
    int x;
    int msqid;  // Message queue Id
    int smrc;
    unsigned int useridLength;
    unsigned int cmdLength;
    unsigned int ourPort;
    char readBuffer[BUFLEN];
    char userID[BUFLEN];
    char cmd[BUFLEN];
    char path[BUFLEN + 1];
    char cacheUserID[ 8 + 1 ];
    char cachePath[BUFLEN + 1];
    char cacheFile[BUFLEN + 1];
    char line[LINESIZE + LINESIZE];
    char ourIpAddr[20];
    vmbkend_tdata *tdata;
    time_t ltime;
    smMemoryGroupContext localMemoryGroup;
    smMemoryGroupContext * saveMemoryGroup;
    vmApiAsynchronousNotificationEnableDmOutput * ptrEnableOutputData;
    vmApiAsynchronousNotificationDisableDmOutput * ptrDisableOutputData;
    vmApiInternalContext *vmapiContextP;
    vmApiInternalContext vmapiContext;
    smMemoryGroupContext memContext;
    extern struct _smTrace externSmapiTraceFlags;

    pthread_mutex_lock(&mutex);

    // Expand the macro for time being
    memset(&vmapiContext, 0, sizeof(*(&vmapiContext)));
    memset(&memContext, 0, sizeof(*(&memContext)));
    (&vmapiContext)->memContext = &memContext;
    (&vmapiContext)->smTraceDetails
            = (struct _smTrace *) &externSmapiTraceFlags;
    smrc = smMemoryGroupInitialize(&vmapiContext);

    if (0 == smrc) {
        readTraceFile(&vmapiContext);
    } else {
        logLine(&vmapiContext, 'E', "Unexpected smMemoryGroupInitializeError!");
    }
    vmapiContextP = &vmapiContext;

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "Inside back end thread \n");
    TRACE_END_DEBUG(vmapiContextP, line);

    tdata = (vmbkend_tdata *) data;

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "vmbkendMain: Thread data --> at %d:%s", tdata->thread_no, inet_ntoa(tdata->Addrs));
    TRACE_END_DEBUG(vmapiContextP, line);

    sprintf(ourIpAddr, "%s", inet_ntoa(tdata->Addrs));
    if (1 != vmapiContextP->contextCreatedFlag) {
        rc = initializeThreadSemaphores(vmapiContextP, "", 1);  // Create context using no name to override current context name
    }

    // Indicate this is the backend
    vmapiContextP->isBackend = 1;

    // Obtain the Backend semaphore to before manipulating context related stuff
    operations[0].sem_num = BackendSemaphoreIndex;
    operations[0].sem_op = -1;
    operations[0].sem_flg = SEM_UNDO;
    rc = semop(vmapiContextP->semId, operations, sizeof(operations) / sizeof(operations[0]));
    if (rc < 0) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain: semop (decrement) failed, errno=%d text: %s", errno, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    // OK, ready to go
    time(&ltime);
    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "vmbkendMain: Entry to --> at %s", ctime(&ltime));
    TRACE_END_DEBUG(vmapiContextP, line);

    // Build path to the cache directory
    memset(path, 0, sizeof(cachePath));
    vmbkendGetCachePath(vmapiContextP, cachePath);

    // Call routine to remove the cache
    vmbkendRemoveEntireCache(vmapiContextP, cachePath);

    // Do the necessary socket server setup
    serverSock = socket(AF_INET, SOCK_DGRAM, 0);
    exit_if_error(Socket, serverSock, serverSock);

    memset(&serverSockaddr, 0, sizeof serverSockaddr);

    // Read and use any previous port number that may have been set by a
    // previous run of vmbkend. If no previous run or error, the value zero
    // is returned.
    vmbkendSockaddrFileInfo(vmapiContextP, 0, &previousSockaddr);
    serverSockaddr.sin_port = previousSockaddr.sin_port;
    serverSockaddr.sin_family = AF_INET;
    serverSockaddr.sin_addr.s_addr = htonl(INADDR_ANY);

    rc = bind(serverSock, (struct sockaddr *) &serverSockaddr, sizeof serverSockaddr);

    if (-1 == rc) {  // Bind failure
        if (0 == serverSockaddr.sin_port) {
            // The bind for an ephemeral port failed
            exit_if_error(Bind, rc, serverSock);
        } else {
            // We used a previous port and this failed, retry the bind for any ephemeral port.
            memset(&serverSockaddr, 0, sizeof serverSockaddr);
            serverSockaddr.sin_port = 0;
            serverSockaddr.sin_addr.s_addr = htonl(tdata->Addrs.s_addr);
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                TRACE_END_DEBUG(vmapiContextP, "vmbkendMain:  Retrying bind for sin_port <0>\n");
            rc = bind(serverSock, (struct sockaddr *) &serverSockaddr,
                    sizeof serverSockaddr);

            exit_if_error(Bind, rc, serverSock);
        }
    }

    memset(&serverSockaddr1, 0, sizeof serverSockaddr1);
    socklen = sizeof serverSockaddr1;

    rc = getsockname(serverSock, (struct sockaddr *) &serverSockaddr1, &socklen);
    exit_if_error(Getsockname, rc, serverSock);

    // Show the IP address for our system
    get_myaddress(&notificationSocketInfo);

    notificationSocketInfo.sin_addr.s_addr = tdata->Addrs.s_addr;
    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);

    // Show what port number we are listening on
    sprintf(line, "vmbkendMain: Listening on %s:%u", inet_ntoa(notificationSocketInfo.sin_addr),
            (unsigned) ntohs(serverSockaddr1.sin_port));
    TRACE_END_DEBUG(vmapiContextP, line);

    // Set port for notification
    notificationSocketInfo.sin_port = serverSockaddr1.sin_port;

    // If we used different information from a previous run then:
    // - Write new info to the file PORT_FILENAME
    // - Unregister old info with the directory manager.
    if ((previousSockaddr.sin_port != notificationSocketInfo.sin_port)
            || (previousSockaddr.sin_addr.s_addr != notificationSocketInfo.sin_addr.s_addr)) {
        // Write new info to PORT_FILENAME
        vmbkendSockaddrFileInfo(vmapiContextP, 1, &notificationSocketInfo);

        // If previous registration, unregister it
        if (0 != previousSockaddr.sin_port) {
            sprintf(ourIpAddr, "%s", inet_ntoa(previousSockaddr.sin_addr));
            ourPort = previousSockaddr.sin_port;

            saveMemoryGroup = vmapiContextP->memContext;
            vmapiContextP->memContext = &localMemoryGroup;
            smMemoryGroupInitialize(vmapiContextP);

            rc = smAsynchronous_Notification_Disable_DM(vmapiContextP, "",  // IUCV userid and password not needed
                    0,          // Password length
                    "",         // Password
                    "ALL",      // Target identifier
                    1,          // Entity_type directory
                    2,          // UDP communication_type,
                    ourPort,    // Port_number,
                    ourIpAddr,  // IP_address string,
                    1,          // ASCII encoding,
                    0,          // Subscriber_data_length,
                    "",         // Subscriber_data,
                    &ptrDisableOutputData);
            if (0 != rc || 0 != ptrDisableOutputData->common.returnCode) {
                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "vmbkendMain: call to asynch unregister got rc1 %d rc2 %d \n", rc, ptrDisableOutputData->common.returnCode);
                TRACE_END_DEBUG(vmapiContextP, line);

                smMemoryGroupFreeAll(vmapiContextP);
                smMemoryGroupTerminate(vmapiContextP);
                vmapiContextP->memContext = saveMemoryGroup;
                close(serverSock);
                pthread_exit(NULL);
            }
            smMemoryGroupFreeAll(vmapiContextP);
            smMemoryGroupTerminate(vmapiContextP);
            vmapiContextP->memContext = saveMemoryGroup;
        }
    }  // Used different port number

    // Call asynchronous notify RPC to register with the directory manager
    sprintf(ourIpAddr, "%s", inet_ntoa(notificationSocketInfo.sin_addr));
    ourPort = notificationSocketInfo.sin_port;

    saveMemoryGroup = vmapiContextP->memContext;
    vmapiContextP->memContext = &localMemoryGroup;
    smMemoryGroupInitialize(vmapiContextP);

    rc = smAsynchronous_Notification_Enable_DM(vmapiContextP, "",  // IUCV userid and password not needed
            0,          // Password length
            "",         // Password
            "ALL",      // Target identifier
            1,          // Entity_type directory
            1,          // Include subscription type
            2,          // UDP subscription_type
            ourPort,    // Port_number
            ourIpAddr,  // IP_address
            1,          // ASCII encoding
            0,          // Subscriber_data_length
            "",         // Subscriber_data
            &ptrEnableOutputData);
    if (0 == rc && 0 != ptrEnableOutputData->common.returnCode) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain: call to asynch register got rc1 %d rc2 %d and rs %d\n",
                rc, ptrEnableOutputData->common.returnCode, ptrEnableOutputData->common.reasonCode);
        TRACE_END_DEBUG(vmapiContextP, line);

        // If Subscription exists, do not do anything
        if (!ptrEnableOutputData->common.returnCode == 428) {
            smMemoryGroupFreeAll(vmapiContextP);
            smMemoryGroupTerminate(vmapiContextP);
            vmapiContextP->memContext = saveMemoryGroup;
            close(serverSock);
            pthread_exit(NULL);
        }
    } else if (0 != rc) {
        smMemoryGroupFreeAll(vmapiContextP);
        smMemoryGroupTerminate(vmapiContextP);
        vmapiContextP->memContext = saveMemoryGroup;
        close(serverSock);
        pthread_exit(NULL);
    }

    // Create msqId for directory change indication
    if ((msqid = msgget(MSGDEFKEY, IPC_CREAT | 0666) ) < 0) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "msgget for directory change error, key: %d, errno: %d text: %s", MSGDEFKEY, errno, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
        // We can still process other events if we get a message get error so
        // we don't need to leave the routine until all events have been processed.
    }
    smMemoryGroupFreeAll(vmapiContextP);
    smMemoryGroupTerminate(vmapiContextP);
    vmapiContextP->memContext = saveMemoryGroup;

    // Wait for and handle incoming requests from the directory manager
    pthread_cond_signal(&thread_initialized_cv);
    pthread_mutex_unlock(&mutex);
    for (;;) {
        time(&ltime);

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain:  About to receive on  %s", ctime(&ltime));
        TRACE_END_DEBUG(vmapiContextP, line);

        // UDP
        memset(readBuffer, 0, sizeof readBuffer);
        memset(&clientSockaddr, 0, sizeof clientSockaddr);
        clientLen = sizeof clientSockaddr;
        bytesRead = 0;
        useridLength = 0;

        bytesRead = recvfrom(serverSock, readBuffer, sizeof(readBuffer), 0, (struct sockaddr *) &clientSockaddr,
                &clientLen);

        if (bytesRead == -1) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "vmbkendMain:  recvfrom got errno %d text: %s\n", errno, strerror(errno));
            TRACE_END_DEBUG(vmapiContextP, line);
            break;
        } continue_if_error(Recvfrom, bytesRead, bytesRead);

        strcpy(path, cachePath);

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain:  Read %d bytes from %s at time: %s\n",
                bytesRead, inet_ntoa(clientSockaddr.sin_addr), ctime(&ltime));
        TRACE_END_DEBUG(vmapiContextP, line);

        // If the message is too small, this is an error, go get the next message
        if (bytesRead <= LENGTH_OF_USERID_LENGTH_FIELD) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "vmbkendMain:  Message is too short");
            TRACE_END_DEBUG(vmapiContextP, line);
            continue;
        }

        // Pull out the userid length
        useridLength = *(int *) &readBuffer;
        useridLength = ntohl(useridLength);

        // Get the userid
        memset(userID, 0, sizeof userID);
        strncpy(userID, readBuffer + 4, useridLength);

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain:  User ID length is >%d< and User ID is >%s<\n", useridLength, userID);
        TRACE_END_DEBUG(vmapiContextP, line);

        // Get the command length
        cmdLength = *(int *) (readBuffer + 4 + useridLength);
        cmdLength = ntohl(cmdLength);

        // Get the command
        memset(cmd, 0, sizeof cmd);
        strncpy(cmd, readBuffer + 4 + useridLength + 4, cmdLength);

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain:  Command is >%s<\n", cmd);
        TRACE_END_DEBUG(vmapiContextP, line);
        if (strcasecmp(cmd, "add") == 0 || strcasecmp(cmd, "purge") == 0) {
            vmbkendCacheEntryInvalidate(vmapiContextP, path, USERS_LIST_FILE);
        }

        // Invalidate the cache entry
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain:  Invalidating cache for user ID (%s)\n", userID);
        TRACE_END_DEBUG(vmapiContextP, line);

        for (x = 0; x < useridLength; ++x) {
            cacheUserID[x] = tolower(userID[x]);
        }
        cacheUserID[useridLength] = '\0';  // Make the copy be a string

        // Unfortunately, we're not told if this is a
        // USER/IDENTITY/SUBCONFIG entry or a PROFILE entry, so invalidate both to be safe.
        strcpy(cacheFile, cacheUserID);
        strcat(cacheFile, ".image");
        vmbkendCacheEntryInvalidate(vmapiContextP, path, cacheFile);
        strcpy(cacheFile, cacheUserID);
        strcat(cacheFile, ".profile");
        vmbkendCacheEntryInvalidate(vmapiContextP, path, cacheFile);

        // If cmd is in 'add', 'purge', 'replace', send message for directory change indication.
        if ( strcasecmp(cmd, "add") == 0 || strcasecmp(cmd, "purge") == 0 || strcasecmp(cmd, "replace") == 0 ) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_VMEVENT_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Directory Change Event detected %s %s\n", userID, cmd);
            TRACE_END_DEBUG(vmapiContextP, line);

            // Send a message to cause a Directory Changed indication to be created.
            if ((msqid = msgget(MSGDEFKEY, 0666)) < 0) {
                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "msgget for directory change error, key: %d, errno: %d text: %s", MSGDEFKEY, errno, strerror(errno));
                TRACE_END_DEBUG(vmapiContextP, line);
                // We can still process other events if we get a message get error so
                // we don't need to leave the routine until all events have been processed.
            } else {
                dir_chng_message_struct msgDirChng;
                dir_chng_message_buf msgDirChngBuf;
                size_t buf_length;
                strcpy(msgDirChng.userid, userID);
                strcpy(msgDirChng.userWord, cmd);
                buf_length = sizeof(dir_chng_message_struct);
                msgDirChngBuf.mType = 1;
                msgDirChngBuf.messageStruct = msgDirChng;
                if (msgsnd(msqid, &msgDirChngBuf, buf_length, IPC_NOWAIT) < 0) {
                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "msgsnd for directory change error, queue: %d, userid: %s, userWord: %s, bufLen: %d\n",
                            msqid, msgDirChng.userid, msgDirChng.userWord, (int) buf_length);
                    TRACE_END_DEBUG(vmapiContextP, line);

                    // We can still process other events if we get a message send error so
                    // we don't need to leave the routine until all events have been processed.
                } else {
                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "msgsnd for directory change, queue: %d, userid: %s, userWord: %s, buflen: %d\n",
                            msqid, msgDirChng.userid, msgDirChng.userWord, (int) buf_length);
                    TRACE_END_DEBUG(vmapiContextP, line);
                }
            }
        }
    }

    // Call asynchronous notify RPC to unregister with the directory manager
    sprintf(ourIpAddr, "%s", inet_ntoa(notificationSocketInfo.sin_addr));
    ourPort = notificationSocketInfo.sin_port;

    saveMemoryGroup = vmapiContextP->memContext;
    vmapiContextP->memContext = &localMemoryGroup;
    smMemoryGroupInitialize(vmapiContextP);

    rc = smAsynchronous_Notification_Disable_DM(vmapiContextP, "",  // IUCV userid and password not needed
            0,          // Password length
            "",         // password
            "ALL",      // Target identifier
            1,          // Entity_type directory
            2,          // UDP communication_type,
            ourPort,    // Port_number,
            ourIpAddr,  // IP_address,
            1,          // ASCII encoding,
            0,          // Subscriber_data_length,
            "",         // Subscriber_data,
            &ptrDisableOutputData);
    if (0 != rc || 0 != ptrDisableOutputData->common.returnCode) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain: call to asynch unregister got rc1 %d rc2 %d \n",
                rc, ptrDisableOutputData->common.returnCode);
        TRACE_END_DEBUG(vmapiContextP, line);

        smMemoryGroupFreeAll(vmapiContextP);
        smMemoryGroupTerminate(vmapiContextP);
        vmapiContextP->memContext = saveMemoryGroup;
        close(serverSock);
        pthread_exit(NULL);
    }

    smMemoryGroupFreeAll(vmapiContextP);
    smMemoryGroupTerminate(vmapiContextP);
    vmapiContextP->memContext = saveMemoryGroup;

    // Close the server socket
    rc = close(serverSock);
    exit_if_error(Close, rc, rc);
    pthread_exit(NULL);
}

/**
 * Procedure: vmbkendremoveCachedScanFiles
 *
 * Purpose: Remove the .scan files
 *
 * Input: Pointer to cache path
 *
 * Output: None
 *
 * Operation:
 *   Build the rm command from the input path
 *   Issue the rm command via system()
 */
int vmbkendRemoveCachedScanFiles(struct _vmApiInternalContext* vmapiContextP, char *pathP) {
    char command[300];
    char line[LINESIZE];

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    // Build the remove command
    sprintf(command, "rm -f %s%s", pathP, ALL_SCAN_FILES);

    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
    sprintf(line, "vmbkendRemoveCachedScanFiles:  About to issue: system(%s)\n", command);
    TRACE_END_DEBUG(vmapiContextP, line);

    if (system(command)) {
        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendRemoveCachedScanFiles:  Error removing scan files, errno 0x%X: reason(%s)\n",
                errno, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, 0);

    return 0;
}

/**
 * Procedure: vmbkendremoveEntireCache
 *
 * Purpose: Remove all cache entries from the cache directory
 *
 * Input: Pointer to the cache directory
 *
 * Output: None
 *
 * Operation:
 *   Build rm command from input cache directory
 *   Issue the rm command via system()
 */
void vmbkendRemoveEntireCache(struct _vmApiInternalContext* vmapiContextP, char *cachePathP) {
    char command[300];
    char line[LINESIZE];

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    /* Build the remove command */
    sprintf(command, "rm -rf %s*", cachePathP);

    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
    sprintf(line, "vmbkendRemoveEntireCache:  About to issue: system(%s)\n", command);
    TRACE_END_DEBUG(vmapiContextP, line);

    if (system(command)) {
        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendRemoveEntireCache:  Error removing file, errno 0x%X: reason(%s)\n", errno, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, 0);
}

/**
 * Procedure: vmbkendSockaddrFileInfo
 *
 * Purpose: Save new or retrieve previous bind information to or from the file
 *          defined by $VMAPI/PORT_FILENAME.
 *
 * Input: int readOrWrite: 0 = read it; 1 = write it
 *        sockaddr_in saddr: If readOrWrite is read, then on input this is
 *                           is the address of where to store the retrieved bind info.
 *                           If readOrWrite is write, then on input this is the address of
 *                           the sockaddr_in containing the bind info to save.
 *
 * Output: RC = 0 (Success): If read then saddr contains the read value. If write, then the file is updated.
 *         RC = -1 (Failure): If read, saddr value returned is zeroes. If write, saddr is unchanged.
 *
 * Operation:
 *   Get the path to the file $VMAPI/.vmapi/PORT_FILENAME
 *   Open the file read or write based on the value of readOrWrite input
 *   If error:
 *   - If read, set saddr to zeroes
 *   - Return -1
 *   If read, then read the info. Else, write the info. Close the file.
 */
int vmbkendSockaddrFileInfo(struct _vmApiInternalContext* vmapiContextP, int readOrWrite, struct sockaddr_in *saddr) {
    int rc = 0;
    FILE *fileP = (FILE *) NULL;
    char fName[BUFLEN + 1];
    char line[LINESIZE];

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    strcpy(fName, vmapiContextP->path);
    strcat(fName, PORT_FILENAME);

    TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
    sprintf(line, "vmbkendSockaddrFileInfo:  PORT_FILENAME %s \n", fName);
    TRACE_END_DEBUG(vmapiContextP, line);

    errno = 0;
    if (0 == readOrWrite) {  // Read
        /* If error reading record, return saddr value of zeroes */
        memset(saddr, 0, sizeof(struct sockaddr_in));
        fileP = fopen(fName, "r");
    } else {
        fileP = fopen(fName, "w");
    }

    if (fileP == (FILE *) NULL) {
        vmapiContextP->errnoSaved = errno;
        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendSockaddrFileInfo:  Errno %d opening %s for %s() text: %s\n",
                errno, fName, (readOrWrite == 0 ? "read" : "write"), strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);

        rc = -1;
        goto exit_error2;
    }

    if (readOrWrite == 0) {  // Read
        if (EOF == fscanf(fileP, "%x:%hu", &(saddr->sin_addr.s_addr),
                &(saddr->sin_port))) {
            /* If error reading record, return saddr value of zeroes */
            vmapiContextP->errnoSaved = errno;
            memset(saddr, 0, sizeof(struct sockaddr_in));
            TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
            sprintf(line, "vmbkendSockaddrFileInfo:  Errno %d reading file %s text: %s\n", errno, fName, strerror(errno));
            TRACE_END_DEBUG(vmapiContextP, line);

            rc = -1;
            goto exit_error1;
        }

        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendSockaddrFileInfo:  Read %x:%hu\n", saddr->sin_addr.s_addr, saddr->sin_port);
        TRACE_END_DEBUG(vmapiContextP, line);
    } else {  // Write
        if (-1 == fprintf(fileP, "%x:%hu", saddr->sin_addr.s_addr, saddr->sin_port)) {
            vmapiContextP->errnoSaved = errno;
            TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
            sprintf(line, "vmbkendSockaddrFileInfo:  Errno %d writing %x:%hu to %s text: %s\n", errno, saddr->sin_addr.s_addr, saddr->sin_port, fName, strerror(errno));
            TRACE_END_DEBUG(vmapiContextP, line);

            rc = -1;
            goto exit_error1;
        }

        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendSockaddrFileInfo:  Wrote %x:%hu\n",
                saddr->sin_addr.s_addr, saddr->sin_port);
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    exit_error1: if (EOF == fclose(fileP)) {
        TRACE_START(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendSockaddrFileInfo:  Errno %d closing file %s() text: %s\n", errno, fName, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    exit_error2: TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL, rc);

    return (rc);
}

void waitForPendingWorkunits(struct _vmApiInternalContext* vmapiContextP, int waitIntervalInSeconds) {  // 0 = wait forever
    int maxRc = 0;
    int maxReason = 0;
    int x = 0;
    int workunitsPending = 1;
    int workunitId;
    int duration;
    int interval;
    int rc;
    time_t startTime;

    smMemoryGroupContext localMemoryGroup;
    smMemoryGroupContext * saveMemoryGroup;
    vmApiQueryAsynchronousOperationDmOutput * ptrQueryAsynchOutputData;

    /* duration == 0 is assumed as infinite duration */
    duration = waitIntervalInSeconds;
    time(&startTime);

    while (workunitsPending && duration >= 0) {
        workunitsPending = 0;
        for (x = 0; (x < (sizeof(vmapiContextP->pendingWorkunits)
                / sizeof(vmapiContextP->pendingWorkunits[0]))); ++x) {
            if (vmapiContextP->pendingWorkunits[x] == 0)
                continue;

            workunitId = vmapiContextP->pendingWorkunits[x];

            vmapiContextP->rc = 0;
            vmapiContextP->reason = 0;

            saveMemoryGroup = vmapiContextP->memContext;
            vmapiContextP->memContext = &localMemoryGroup;

            smMemoryGroupInitialize(vmapiContextP);
            if (0 != (rc = smQuery_Asychronous_Operation_DM(vmapiContextP,
                    "",  // UserId is not required for IUCV
                    0,   // Length 0, no password of IUCV
                    "",  // No password
                    vmapiContextP->useridForAsynchNotification, workunitId, &ptrQueryAsynchOutputData))) {
                // ? Add a specific message for internal error here
            }

            vmapiContextP->rc = ptrQueryAsynchOutputData->common.returnCode;
            vmapiContextP->reason = ptrQueryAsynchOutputData->common.reasonCode;

            // Since the only result data we care about is the return and reason codes, we can
            // free any working memory now.
            smMemoryGroupFreeAll(vmapiContextP);
            smMemoryGroupTerminate(vmapiContextP);
            vmapiContextP->memContext = saveMemoryGroup;

            /* Check for finished operation */
            if ((vmapiContextP->rc == 0) && (vmapiContextP->reason == 100)) {
                vmapiContextP->pendingWorkunits[x] = 0;
                continue;
            }

            /* Check for ongoing operation */
            if ((vmapiContextP->rc == 0) && (vmapiContextP->reason == 104)) {
                workunitsPending = 1; /* At least this one */
                continue;
            }

            /* Check for failed operation */
            if ((vmapiContextP->rc == 0) && (vmapiContextP->reason == 108)) {
                vmapiContextP->rc = 200; /* Set failed image operation error code         */
                vmapiContextP->reason = 0;
            }

            /**
             * Here when an error occurred.
             *
             * The work unit is assumed to be either finished or failed, that
             * is it is not assumed to be ongoing any more.
             */
            if ((vmapiContextP->rc == maxRc) && (vmapiContextP->reason > maxReason)) {
                maxReason = vmapiContextP->reason;
            } else if (vmapiContextP->rc > maxRc) {
                maxRc = vmapiContextP->rc;
                maxReason = vmapiContextP->reason;
            }
        }

        interval = SleepInterval;
        if ((duration > 0) && (interval > duration))
            interval = duration;

        if (workunitsPending && (interval > 0)) {
            sleep(interval);
        }

        if (duration > 0) {
            duration -= interval;
            /* Since == 0 is assumed to be indefinite set -1 in this case */
            if (duration == 0)
                duration = -1;
        }
    }
    /* FIXME: Quickfix to overcome problems on tmcc system */
    sleep(5);

    vmapiContextP->rc = maxRc;
    vmapiContextP->reason = maxReason;
}

/**
 * A valid cache file has good time interval and no "INVALID" PAS0304
 * file is closed for stat to work
 */
int cacheFileValid(struct _vmApiInternalContext* vmapiContextP,    const char* cFNameP) {
    int defaultTimeLimit = 5000;  // Seconds = approx 1.5 hours
    int timeLimit = 0;
    struct stat statbuf;
    time_t currentTime;
    double fileAgeSeconds = 0;
    time_t fileTime = 0;

    if (getenv("EPP_CACHE_TIMELIMIT")) {
        timeLimit = atoi(getenv("EPP_CACHE_TIMELIMIT"));
    } else {
        timeLimit = defaultTimeLimit;
    }

    if (-1 == time(&currentTime))
        return 0; /* Current time failed */

    if (-1 == stat(cFNameP, &statbuf))
        return 0; /* Stat failed */

    fileTime = statbuf.st_mtime;

    fileAgeSeconds = difftime(currentTime, fileTime);

    if ((fileAgeSeconds < 0) || (fileAgeSeconds > timeLimit)) {
        return 0;
    }

    return 1;
}

void  *vmbkendMain_iucv(void *context) {
    int rc;
    int smrc = 0;
    int msqid, dirChng_msqid, ssi_msqid, rel_msqid;
    int msgflg = IPC_CREAT | 0666;
    char line[LINESIZE + LINESIZE];
    char path[BUFLEN + 1];
    char cachePath[BUFLEN + 1];
    struct sembuf operations[1];
    time_t ltime;
    smMemoryGroupContext localMemoryGroup;
    smMemoryGroupContext * saveMemoryGroup;
    vmApiInternalContext *vmapiContextP;
    vmApiInternalContext vmapiContext;
    smMemoryGroupContext memContext;
    extern struct _smTrace externSmapiTraceFlags;
    pthread_mutex_lock(&mutex);

    memset(&vmapiContext, 0, sizeof(*(&vmapiContext)));
    memset(&memContext, 0, sizeof(*(&memContext)));
    (&vmapiContext)->memContext = &memContext;
    (&vmapiContext)->smTraceDetails
            = (struct _smTrace *) &externSmapiTraceFlags;
    smrc = smMemoryGroupInitialize(&vmapiContext);

    if (0 == smrc) {
        readTraceFile(&vmapiContext);
    } else {
        logLine(&vmapiContext, 'E', "Unexpected smMemoryGroupInitializeError!");
    }

    vmapiContextP = &vmapiContext;

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "Inside back end thread \n");
        TRACE_END_DEBUG(vmapiContextP, line);

    if (1 != vmapiContextP->contextCreatedFlag) {
        rc = initializeThreadSemaphores(vmapiContextP, "", 1);  // Create context using no name to override current context name
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "Inside back end thread retValue = %d \n", rc);
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    /* Indicate this is the backend */
    vmapiContextP->isBackend = 1;

    /* Obtain the backend semaphore to before manipulating context related stuff */
    operations[0].sem_num = BackendSemaphoreIndex;
    operations[0].sem_op = -1;
    operations[0].sem_flg = SEM_UNDO;
    rc = semop(vmapiContextP->semId, operations,
            sizeof(operations) / sizeof(operations[0]));
    if (rc < 0) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain_iucv: semop (decrement) failed, errno=%d text: %s", errno, strerror(errno));
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    /* OK ready to go */
    time(&ltime);
    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "vmbkendMain_iucv: Entry to --> at %s", ctime(&ltime));
        TRACE_END_DEBUG(vmapiContextP, line);

    /* Build path to the cache directory */
    memset(path, 0, sizeof(cachePath));
    vmbkendGetCachePath(vmapiContextP, cachePath);

    /* Call routine to remove the cache */
    vmbkendRemoveEntireCache(vmapiContextP, cachePath);

    pthread_cond_signal(&thread_initialized_cv);
    pthread_mutex_unlock(&mutex);

    /* Periodically check at least while there is at least one indication subscriber */
    for (;;) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "%s %s: --- Monitoring Directory Notifications... \n",
                __FILE__, __FUNCTION__);
        TRACE_END_DEBUG(vmapiContextP, line);

        // Creating message queue to send LOGON/LOGOFF notifications to indication thread
        if ((msqid = msgget(MSGKEY, msgflg)) < 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Logon/logoff msgget error");
            TRACE_END_DEBUG(vmapiContextP, line);
            break;
        }

        // Creating message queue to send SSI notifications to indication thread
        if ((ssi_msqid = msgget(MSGSSIKEY, msgflg)) < 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "SSI msgget error");
            TRACE_END_DEBUG(vmapiContextP, line);
            break;
        }

        // Creating message queue to send Directory Change notifications to indication thread
        if ((dirChng_msqid = msgget(MSGDEFKEY, msgflg)) < 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Definition change msgget error");
            TRACE_END_DEBUG(vmapiContextP, line);
            break;
        }

        // Creating message queue to send Relocation notifications to indication thread
        if ((rel_msqid = msgget(MSGRELKEY, msgflg)) < 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Relocation msgget error");
            TRACE_END_DEBUG(vmapiContextP, line);
            break;
        }

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "Msg Queue Ids, logon/off: %d, DirChange: %d,  SSI: %d, Relo: %d ",
                msqid, dirChng_msqid, ssi_msqid, rel_msqid);
        TRACE_END_DEBUG(vmapiContextP, line);

        saveMemoryGroup = vmapiContextP->memContext;
        vmapiContextP->memContext = &localMemoryGroup;
        smMemoryGroupInitialize(vmapiContextP);

        smrc = vmbkendMain_Event_UnSubscribe(&vmapiContext);

        smMemoryGroupFreeAll(vmapiContextP);
        smMemoryGroupTerminate(vmapiContextP);
        vmapiContextP->memContext = saveMemoryGroup;

        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "%s %s: vmbkendMain_Event_UnSubscribe Value inside Thread = %d \n",
                __FILE__, __FUNCTION__, smrc);
        TRACE_END_DEBUG(vmapiContextP, line);

        if (smrc == 0) {
            saveMemoryGroup = vmapiContextP->memContext;
            vmapiContextP->memContext = &localMemoryGroup;
            smMemoryGroupInitialize(vmapiContextP);

            smrc = vmbkendMain_Event_Subscribe(&vmapiContext);

            smMemoryGroupFreeAll(vmapiContextP);
            smMemoryGroupTerminate(vmapiContextP);
            vmapiContextP->memContext = saveMemoryGroup;

            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "%s %s: vmbkendMain_Event_Subscribe Value inside Thread = %d \n",
                    __FILE__, __FUNCTION__, smrc);
            TRACE_END_DEBUG(vmapiContextP, line);
        }

        // Sleep for sometime
        if (smrc != 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "%s %s: vmbkendMain Event_Subscribe/UnSubscribe Failed: Waiting for %d Sec, smrc = %d \n",
                    __FILE__, __FUNCTION__, pollingInterval, smrc);
            TRACE_END_DEBUG(vmapiContextP, line);
            sleep(pollingInterval);
            rc = 0;
            smrc = 0;
        }
    }

    saveMemoryGroup = vmapiContextP->memContext;
    vmapiContextP->memContext = &localMemoryGroup;
    smMemoryGroupInitialize(vmapiContextP);

    smrc = vmbkendMain_Event_UnSubscribe(&vmapiContext);

    if (smrc != 0) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "%s %s: vmbkendMain_Event_UnSubscribe Failed at end of Thread = %d \n",
                __FILE__, __FUNCTION__, smrc);
        TRACE_END_DEBUG(vmapiContextP, line);
    }

    smMemoryGroupFreeAll(vmapiContextP);
    smMemoryGroupTerminate(vmapiContextP);
    vmapiContextP->memContext = saveMemoryGroup;

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    TRACE_END_DEBUG(vmapiContextP, "vmbkendMain_iucv:  About to close() server socket\n");
    pthread_exit(NULL);
}

/**
 * Issue and Event_Unsubscribe to remove SMAPI event notifications
 */
int vmbkendMain_Event_UnSubscribe(struct _vmApiInternalContext* vmapiContextP) {
    const char * const functionName = "Event_Unsubscribe";
    const int SLEEP_TIMES[SEND_RETRY_LIMIT] = { 0, 8, 16, 16, 15, 15, 15, 15 };
    char line[LINESIZE];
    char * cursor;
    char * inputP = 0;
    int tempSize = 0;
    int rc = 0;
    int sockDesc;
    int requestId;
    int j;
    int inputSize =
            4 +                            // Space for input parameter length
            4 +                            // Function name length
            strlen(functionName) +         // Function name
            4 +                            // UserId length
            0 +                            // UserId - not specified
            4 +                            // Password length
            0 +                            // Password - not specified
            4 +                            // Target identifier length
            strlen(TARGET_ALL);            // Target identifier


    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize)))
        return MEMORY_ERROR;

    // Move in size of input buffer
    cursor = inputP;
    PUT_INT(inputSize-4, cursor);

    // Fill in the SMAPI function name info
    tempSize = strlen(functionName);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, functionName, tempSize);
    cursor += tempSize;

    // Fill in the userid info - not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the password info - not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the target identifier info
    tempSize = strlen(TARGET_ALL);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, TARGET_ALL, tempSize);
    cursor += tempSize;

    // Initialize our socket
    if (0 != (rc = smSocketInitialize(vmapiContextP, &sockDesc))) {
        FREE_MEMORY(inputP);
        return rc;
    }

    // Retry the send if the error detected is Ok to retry
    for (j = 0;; j++) {
        if (0 != (rc = smSocketWrite(vmapiContextP, sockDesc, inputP, inputSize))) {
            if (rc == SOCKET_NOT_CONNECTED_ERROR) {
                if (j < SEND_RETRY_LIMIT) {
                    // Delay for a while to give SMAPI some time to restart
                    if (SLEEP_TIMES[j] > 0) {
                        sleep(SLEEP_TIMES[j]);
                    }
                    continue;
                }

                // Change the internal return code to general write one
                rc = SOCKET_WRITE_ERROR;
            }

            FREE_MEMORY(inputP);
            return rc;
        }

        break;
    }

    FREE_MEMORY(inputP);

    // Get the request Id
    if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char*) &requestId, 4))) {
        sprintf(line, "UnSubscribe Socket %d receive of the requestId failed with RC = %d \n", sockDesc, rc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
        return rc;
    }

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "UnSubscribe Request Id succeeded  %u \n", requestId);
    TRACE_END_DEBUG(vmapiContextP, line);

    // Wait on a read for SMAPI to close the socket. This will ensure that SMAPI has processed
    // the unsubscribe request. The read will fail after SMAPI completes its work.
    do {
        rc = smSocketReadLoop(vmapiContextP, sockDesc, (char*) &line, 1, SOCKET_ERROR_OK);
    } while (rc == CUSTOM_DEFINED_SOCKET_RETRY);
    return 0;
}

/**
 * Establish a socket and subscribe for event notification from SMAPI. Read
 * event notifications and drive the event processing.
 */
int vmbkendMain_Event_Subscribe(struct _vmApiInternalContext* vmapiContextP) {
    int tempSize = 0;
    int rc = 0;
    int sockDesc;
    int requestId;
    int j;
    const int SLEEP_TIMES[SEND_RETRY_LIMIT] = { 0, 8, 16, 16, 15, 15, 15, 15 };
    const char * const functionName = "Event_Subscribe";
    char * cursor;
    char line[LINESIZE];
    char cachePath[BUFLEN + 1] = "";  // Path to the directory cache
    char * inputP = 0;
    int inputSize =
            4 +                            // Space for input parm length
            4 +                            // Function name length
            strlen(functionName) +         // Function name
            4 +                            // UserId length
            0 +                            // UserId - not specified
            4 +                            // Password length
            0 +                            // Password - not specified
            4 +                            // Target identifier length
            strlen(TARGET_ALL) +           // Target identifier
            4 +                            // Matchkey length
            0;                             // Matchkey - not specified

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    // Build path to the cache directory.
    vmbkendGetCachePath(vmapiContextP, cachePath);
    if (strlen(cachePath) == 0) {
        // Error has already been logged
        rc = -1;  // Force an exit from normal processing
        goto exit_vmbkendMain_Event_Subscribe;  // Exit from routine
    }

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        rc = MEMORY_ERROR;
        goto exit_vmbkendMain_Event_Subscribe;  // Exit from routine
    }

    // Move in size of input buffer
    cursor = inputP;
    PUT_INT(inputSize-4, cursor);

    // Fill in the SMAPI function name info
    tempSize = strlen(functionName);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, functionName, tempSize);
    cursor += tempSize;

    // Fill in the userid info - not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the password info - not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Fill in the target identifier info
    tempSize = strlen(TARGET_ALL);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, TARGET_ALL, tempSize);
    cursor += tempSize;

    // Fill in the info related to the matchkey, length set to 0 - matchkey is not specified
    tempSize = 0;
    PUT_INT(tempSize, cursor);

    // Initialize our socket
    if (0 != (rc = smSocketInitialize(vmapiContextP, &sockDesc))) {
        sockDesc = 0;  // No socket to terminate on exit
        goto exit_vmbkendMain_Event_Subscribe;  // Exit from this routine
    }

    // Write a message to SMAPI indicating what event information we want
    for (j = 0;; j++) {
        if (0 != (rc = smSocketWrite(vmapiContextP, sockDesc, inputP, inputSize))) {
            // Retry the send if the error detected is Ok to retry
            if (rc == SOCKET_NOT_CONNECTED_ERROR) {
                if (j < SEND_RETRY_LIMIT) {
                    // Delay for a while to give SMAPI some time to restart
                    if (SLEEP_TIMES[j] > 0) {
                        sleep(SLEEP_TIMES[j]);
                    }
                    continue;
                }
                // Change the internal return code to general write one
                rc = SOCKET_WRITE_ERROR;
            }
            goto exit_vmbkendMain_Event_Subscribe;  // Exit from this routine
        }
        break;
    }

    // Get the request id which identifies communication on this socket related to this
    // subscribe for event notification.
    if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char*) &requestId, 4))) {
        sprintf(line, "Event_Subscribe Socket %d receive of the requestId failed with RC = %d \n", sockDesc, rc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
        goto exit_vmbkendMain_Event_Subscribe;  // Exit from this routine
    }

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "Event_Subscribe receive of Request Id succeeded %u \n", requestId);
    TRACE_END_DEBUG(vmapiContextP, line);

    // Loop reading and processing notifications on the established socket.
    // Each notification begins with a length of the output.
    // We hope to stay in this loop and lower level subroutines for the life of the
    // zThin agent run.
    for (;;) {
        if (0 != (rc = smSocketReadLoop(vmapiContextP, sockDesc, (char *) &tempSize, 4, 0))) {
            if (rc != CUSTOM_DEFINED_SOCKET_RETRY) {
                sprintf(line, "Event_Subscribe Socket %d receive of the output length failed with RC = %d \n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                break;  // Force an exit from the read loop.
            }
        }

        // If we successfully receive an event indication (got an output length) then send it for processing
        if (rc == 0) {
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event_Subscribe new event length received: %d \n", tempSize);
            TRACE_END_DEBUG(vmapiContextP, line);

            // Call to read the data
            rc = vmbkendMain_setSmapiSubscribeEventData(vmapiContextP, tempSize, sockDesc, requestId, cachePath);
            if (rc != 0) {
                break;  // Force an exit from the read loop
            }
        }
    }

    // Final cleanup and return from this subroutine
exit_vmbkendMain_Event_Subscribe:
    // If we still have a socket then cleanup after it
    // This will only occur if we encountered a memory error or SMAPI rejected the
    // subscribe request.
    if ((sockDesc != 0) && ((rc == MEMORY_ERROR) || (rc == PROCESSING_ERROR))) {
        rc = smSocketTerminate(vmapiContextP, sockDesc);
        if ((rc != 0) && (rc != SOCKET_PROCESSING_ERROR)) {
            sprintf(line, "Event_Subscribe Socket %d terminate failed with RC = %d \n", sockDesc, rc);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
        } else {
            rc = 0;  // SOCKET_PROCESSING_ERROR is an acceptable RC
        }
    }

    FREE_MEMORY(inputP);  // Release free storage
    return rc;
}

/**
 * On the established socket, receive the event information for the specified length and process it
 */
int vmbkendMain_setSmapiSubscribeEventData(struct _vmApiInternalContext* vmapiContextP, int outputBufferSize, int sockDesc, int requestId, char * cachePath ) {
    unsigned char * smapiOutputP = 0;
    short unsigned int eventClass;              // 2 byte Event Class
    short unsigned int eventType;               // 2 byte Event type
    int tempSize;
    int rc = 0;
    int preMode;                                // Integer form of previous mode info
    int newMode;                                // Integer form of new mode info
    int eventDataType;                          // 4 Byte
    int eventID;                                // 4 Byte Event ID for type 1 event data
    int useridLength;
    int userWordLength;
    int readLen;                                // Length to read
    int i = 0;
    int sizeOfUnreadData;
    int sizeOfSubdata;
    int request_id;
    int return_code = 0;
    int reason_code = 0;
    int startRow;
    int endRow;
    int typeFnd;
    int actualSize = 0;
    int totalToRead;
    int x = 0;
    // Message queue related variables
    int msqid;
    int msgflg = 0666;
    char cacheUserID[ 8 + 1 ];
    char cacheFile[BUFLEN + 1];
    char line[LINESIZE];
    char userWord[16+1];                        // Max 16 chars plus string terminator
    char userid[8+1];                           // Max userid plus string terminator
    char systemId[8+1];                         // Max system id plus string terminator
    char eventReasonCode;
    char ssiName[8+1];                          // SSI Name
    char modes[2];                              // Modes - 2 one character mode fields
    log_message_struct logStruct;
    dir_chng_message_struct msgDirChng;
    ssi_message_struct msgSSI;
    rel_message_struct msgRelocateSys;
    log_message_buf logBuf;
    dir_chng_message_buf msgDirChngBuf;
    ssi_message_buf msgSSIBuf;
    rel_message_buf msgRelocateSysBuf;
    size_t buf_length;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    // Obtain storage to receive the data passed from SMAPI
    tempSize = ntohl(outputBufferSize);
    if (0 == (smapiOutputP = malloc(tempSize))) {
        sprintf(line, "Insufficient memory (request=%d bytes)\n", tempSize);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, line);
        rc = MEMORY_ERROR;
        goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
    }

    // If SMAPI passed only 12 bytes of data then they are returning an error
    // and we have to pull down the rest of the error data to log it.
    if (tempSize == 12) {
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "Error encountered receiving event data.\n");
        TRACE_END_DEBUG(vmapiContextP, line);
        if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &request_id, sizeof(request_id)))) {
            sprintf(line, "Event_Subscribe receive of request ID on socket %d failed with RC: %d\n", sockDesc, rc);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
            goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
        } else {
            actualSize = actualSize + sizeof(request_id);
        }

        if (request_id == requestId) {
            // Obtain the SMAPI return code
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &return_code, sizeof(return_code)))) {
                sprintf(line, "Event_Subscribe receive of SMAPI rc on socket %d failed with RC: %d\n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
            } else {
                actualSize = actualSize + sizeof(return_code);
            }

            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event_Subscribe subscribe failed with SMAPI RC: %d\n", return_code);
            TRACE_END_DEBUG(vmapiContextP, line);

            // Obtain the SMAPI reason code
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &reason_code, sizeof(reason_code)))) {
                sprintf(line, "Event_Subscribe receive of SMAPI rs failed with RC: %d\n", rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
            } else {
                actualSize = actualSize + sizeof(reason_code);
            }

            // Log the final information from SMAPI and go exit from the routine
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event_Subscribe failed with SMAPI reason code: %d\n", reason_code);
            TRACE_END_DEBUG(vmapiContextP, line);
            rc = PROCESSING_ERROR;  // Indicate an error so sockets gets terminated
            goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
        } else {
            // We never expect to get data from SMAPI for a different subscribe ID
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event_Subscribe failed because of different subscribe ids: %d %d\n", request_id, requestId);
            TRACE_END_DEBUG(vmapiContextP, line);
            rc = PROCESSING_ERROR;  // Indicate an error so sockets gets terminated
            goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
        }
    }

    /**
     * Normal event processing of data from SMAPI. Begin processing the event by
     * obtaining the event type and loop processing all data for this event
     */
    /* Obtain the event data type */
    if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &eventDataType, sizeof(eventDataType)))) {
        sprintf(line, "Event_Subscribe receive of event data type on socket %d failed with RC: %d\n", sockDesc, rc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
        goto exit_vmbkendMain_setSmapiSubscribeEventData;   // Exit from routine
    } else {
        actualSize = actualSize + sizeof(eventDataType);
    }

    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
    sprintf(line, "Event_Subscribe event data type: %d \n", eventDataType);
    TRACE_END_DEBUG(vmapiContextP, line);

    // Loop to process all data for this event
    while (tempSize > actualSize) {
        // Handle Data Type 1 events which includes directory change notification
        if (eventDataType == 1) {
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &eventID, sizeof(eventID)))) {
                sprintf(line, "Event_Subscribe receive of event ID on socket %d failed with RC: %d\n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;   // Exit from routine
            } else {
                actualSize = actualSize + sizeof(eventID);
            }

            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event_Subscribe event ID: %d \n", eventID);
            TRACE_END_DEBUG(vmapiContextP, line);

            // EventId = 1 events: Handle directory related change notifications
            if (eventID == 1) {
                // Get the userid length
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &useridLength, sizeof(useridLength)))) {
                    sprintf(line, "Event_Subscribe receive of userid length on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + sizeof(useridLength);
                }

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "useridLength : %d \n", useridLength);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Get the userid
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, useridLength))) {
                    sprintf(line, "Event_Subscribe receive of event userid on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + useridLength;
                }

                for (i = 0; i < useridLength; i++) {
                    userid[i] = smapiOutputP[i];
                }
                userid[i] = '\0';  // Make userid a string for future string operations

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "DATA : %s \n", userid);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Get the user word length
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &userWordLength, sizeof(userWordLength)))) {
                    sprintf(line, "Event_Subscribe receive of userword length on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + sizeof(userWordLength);
                }

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "userWordLength : %d \n", userWordLength);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Get the user word
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &userWord, userWordLength))) {
                    sprintf(line, "Event_Subscribe receive of userword on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;   // Exit from routine
                } else {
                    actualSize = actualSize + userWordLength;
                }
                userWord[userWordLength] = '\0';  // Make userWord a string for future string operations

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "userWord : %s \n", userWord);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Get the subdata length
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &sizeOfSubdata, sizeof(sizeOfSubdata)))) {
                    sprintf(line, "Event_Subscribe receive of subdata length on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + sizeof(sizeOfSubdata);
                }

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "sizeOfSubdata : %d \n", sizeOfSubdata);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Get the subdata and throw it away
                if ( sizeOfSubdata > 0 ) {
                    if ( 0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &line, sizeOfSubdata)) ) {
                        sprintf(line, "Event_Subscribe receive of subdata on socket %d failed with RC: %d\n", sockDesc, rc);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                    } else {
                        actualSize = actualSize + sizeOfSubdata;
                    }
                }

                // If the entry is being added or removed then invalidate the list of users.
                if (strcasecmp(userWord, "add") == 0 || strcasecmp(userWord, "purge") == 0) {
                    vmbkendCacheEntryInvalidate(vmapiContextP, cachePath, USERS_LIST_FILE);
                }

                // Invalidate the cache entry
                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "vmbkendMain_iucv:  Invalidating cache for user ID (%s)\n", userid);
                TRACE_END_DEBUG(vmapiContextP, line);

                for (x = 0; x < useridLength; ++x) {
                    cacheUserID[x] = tolower(userid[x]);
                }
                cacheUserID[useridLength] = '\0';    // Make the copy be a string

                // Unfortunately, we're not told if this is a
                // USER/IDENTITY/SUBCONFIG entry or a PROFILE
                // entry, so invalidate both to be safe.
                strcpy(cacheFile, cacheUserID);
                strcat(cacheFile, ".image");
                vmbkendCacheEntryInvalidate(vmapiContextP, cachePath, cacheFile);
                strcpy(cacheFile, cacheUserID);
                strcat(cacheFile, ".profile");
                vmbkendCacheEntryInvalidate(vmapiContextP, cachePath, cacheFile);

                // Send a message to the indication provider
                if ((msqid = msgget(MSGDEFKEY, msgflg)) < 0) {
                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "msgget for directory change error, key: %d, errno: %d text: %s", MSGDEFKEY, errno, strerror(errno));
                    TRACE_END_DEBUG(vmapiContextP, line);

                    // We can still process other events if we get a message get error so
                    // we don't need to leave the routine until all events have been processed.
                } else {
                    strcpy(msgDirChng.userid, userid);
                    strcpy(msgDirChng.userWord, userWord);
                    buf_length = sizeof(dir_chng_message_struct);
                    msgDirChngBuf.mType = 1;
                    msgDirChngBuf.messageStruct = msgDirChng;
                    if (msgsnd(msqid, &msgDirChngBuf, buf_length, IPC_NOWAIT) < 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgsnd for directory change error, queue: %d, userid: %s, userWord: %s, bufLen: %d\n",
                                msqid, msgDirChng.userid, msgDirChng.userWord, (int) buf_length);
                        TRACE_END_DEBUG(vmapiContextP, line);

                        // We can still process other events if we get a message send error so
                        // we don't need to leave the routine until all events have been processed.
                    } else {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgsnd for directory change, queue: %d, userid: %s, userWord: %s, buflen: %d\n",
                                msqid, msgDirChng.userid, msgDirChng.userWord, (int) buf_length);
                        TRACE_END_DEBUG(vmapiContextP, line);
                    }
                }
            }

            // Prepare to strip off all remaining data in this transmission.
            sizeOfUnreadData = tempSize - actualSize;
        } else if (eventDataType == 0) {  // Handle *VMEvent Change Notifications
            // Obtain the event class.
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc,
                    (char *) &eventClass, sizeof(eventClass)))) {
                sprintf(line, "Event_Subscribe receive of event class on socket %d failed with RC: %d\n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
            } else {
                actualSize = actualSize + sizeof(eventClass);
            }

            // Obtain the event type.
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) &eventType, sizeof(eventType)))) {
                sprintf(line, "Event_Subscribe receive of event type on socket %d failed with RC: %d\n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
            } else {
                actualSize = actualSize + sizeof(eventType);
            }

            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
            sprintf(line, "Event Class: %hu, Type: %hu \n", eventClass, eventType);
            TRACE_END_DEBUG(vmapiContextP, line);

            // Event Class 0: Event Types: 0-1 and 9-14 have userid info along with other useful information.
            if ((eventClass == 0) && ((eventType <= 1) || ((eventType >= 9) && (eventType <= 14)))) {
                // Receive the userid for the correct length.
                readLen = 8;  // Userid field is always 8 chars of data
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                    sprintf(line, "Event_Subscribe receive of event userid on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + readLen;
                }

                for (i = 0; i < readLen; i++) {
                    userid[i] = EBCDICtoASCII(smapiOutputP[i]);
                    if (userid[i] == ' ') {
                        userid[i] = '\0';  // Convert blanks to string terminators to strip blanks
                    }
                }
                userid[i] = '\0';  // Ensure userid is a string for later processing

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "Userid : %s \n", userid);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Handle the system id for event class 0, event type 9 - 12
                if ((eventType >= 9) && (eventType <= 12)) {
                    // Receive the system for the correct length
                    readLen = 8;  // System id field is always 8 chars of data
                    if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                        sprintf(line, "Event_Subscribe receive of system ID on socket %d failed with RC: %d\n", sockDesc, rc);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                    } else {
                        actualSize = actualSize + readLen;
                    }

                    for (i = 0; i < readLen; i++) {
                        systemId[i] = EBCDICtoASCII(smapiOutputP[i]);
                        if (systemId[i] == ' ') {
                            systemId[i] = '\0';  // Convert blanks to string terminators to strip blanks
                        }
                    }
                    systemId[i] = '\0';  // Ensure userid is a string for later processing

                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "System ID: %s\n", systemId);
                    TRACE_END_DEBUG(vmapiContextP, line);
                }

                // Handle the system id for event class 0, event type 13 - 14
                if ((eventType >= 13) && (eventType <= 14)) {
                    // Receive the system for the correct length.
                    readLen = 1;  // Reason code field is always 1 char of data
                    if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                        sprintf(line, "Event_Subscribe receive of event 0, 13-14 reason code on socket %d failed with RC: %d \n", sockDesc, rc);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                    } else {
                        actualSize = actualSize + readLen;
                    }

                    eventReasonCode = *smapiOutputP;

                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "Event reason code : %c \n", eventReasonCode);
                    TRACE_END_DEBUG(vmapiContextP, line);
                }  // End pulling data for Event Class 0, Event Types: 0-1 and 9-14
            } else if ((eventClass == 1) && (eventType >= 9) && (eventType <= 10)) {
                // Event Class 1: Event Types: 9-10 have userid info along with other useful information.
                readLen = 8;  // UserId field is always 8 chars of data
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                    sprintf(line, "Event_Subscribe receive of event userid on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + readLen;
                }

                for (i = 0; i < readLen; i++) {
                    userid[i] = EBCDICtoASCII(smapiOutputP[i]);
                    if ( userid[i] == ' ' ) {
                        userid[i] = '\0';         // Convert blanks to string terminators to strip blanks
                    }
                }
                userid[i] = '\0';  // Ensure userid is a string for later processing

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "Userid : %s \n", userid);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Receive the system for the correct length
                readLen = 8;  // System Id field is always 8 chars of data
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                    sprintf(line, "Event_Subscribe receive of system ID on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + readLen;
                }

                for (i = 0; i < readLen; i++) {
                    systemId[i] = EBCDICtoASCII(smapiOutputP[i]);
                    if (systemId[i] == ' ') {
                        systemId[i] = '\0';  // Convert blanks to string terminators to strip blanks
                    }
                }
                systemId[i] = '\0';  // Ensure userid is a string for later processing

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "System ID: %s\n", systemId);
                TRACE_END_DEBUG(vmapiContextP, line);
                // End pulling data for Event Class 1, Event Types: 9-10
            } else if (((eventClass == 2) || (eventClass == 3)) && (eventType == 7)) {
                // Event Class 2 & 3: Event Type: 7 has SSI name along with previous and new modes.
                // Receive the SSI name for the correct length.
                readLen = 8;  // SSI name field is always 8 chars of data
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, readLen))) {
                    sprintf(line, "Event_Subscribe receive of event SSI name on socket %d failed with RC: %d\n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + readLen;
                }

                for (i = 0; i < readLen; i++) {
                    ssiName[i] = EBCDICtoASCII(smapiOutputP[i]);
                    if (ssiName[i] == ' ') {
                        ssiName[i] = '\0';  // Convert blanks to string terminators to strip blanks
                    }
                }
                ssiName[i] = '\0';  // Ensure userid is a string for later processing

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "ssiName : %s \n", ssiName);
                TRACE_END_DEBUG(vmapiContextP, line);

                // Receive the 2 one byte SSI modes.
                readLen = 2;  // 2 mode fields
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, modes, readLen))) {
                    sprintf(line, "Event_Subscribe receive of receive of event SSI name on socket %d failed with RC: %d \n", sockDesc, rc);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                    goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
                } else {
                    actualSize = actualSize + readLen;
                }

                preMode = (int) modes[0];
                newMode = (int) modes[1];

                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                sprintf(line, "previous mode: %d, new mode: %d\n", preMode, newMode);
                TRACE_END_DEBUG(vmapiContextP, line);
            }  // End pulling data for Event Class 2 & 3, Event Type: 7

            // Determine the length of the rest of the unread data for this
            // event on the current transmission.
            if (eventClass <= 4) {
                typeFnd = 0;  // Assume type is not in table

                // Determine start and end row for this class in the table
                startRow = 0;
                for (i = 0; i < eventClass; ++i) {
                    startRow = startRow + vmeClassRows[i];
                }
                endRow = startRow + vmeClassRows[eventClass];

                // Check the table for this event class
                for (i = startRow; i < endRow; ++i) {
                    if (eventType == vmeventRemainders[i][0]) {
                        typeFnd = 1;
                        sizeOfUnreadData = vmeventRemainders[i][1];
                        break;
                    }
                }

                // Handle where event type is not found for this class
                if (typeFnd == 0) {
                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_ERROR);
                    sprintf(line, "Unrecognized event class %d event type %d received from SMAPI\n",
                            eventClass, eventType);
                    TRACE_END_DEBUG(vmapiContextP, line);

                    // Can't find the type so need to strip off all of data
                    sizeOfUnreadData = tempSize - actualSize;
                }
            } else {
                TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_ERROR);
                sprintf(line, "Unrecognized event class %d received from SMAPI\n", eventClass);
                TRACE_END_DEBUG(vmapiContextP, line);

                // We have no info on the size of other event classes so just take the rest of the data
                sizeOfUnreadData = tempSize - actualSize;
            }

            totalToRead = tempSize - actualSize;

            // Event information has been received. There may be others on the same send waiting
            // to be received but we have to react to this one now.
            if (eventClass == 0) {
                // Event Class 0: Event Types: 0-1 are logon/off indications
                if ((eventType == 0) || (eventType == 1)) {
                    // Send a message to cause a logon/off indication to be created.
                    if ((msqid = msgget(MSGKEY, msgflg)) < 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgget for logon/off error, key: %d, errno: %d, text: %s", MSGKEY, errno, strerror(errno));
                        TRACE_END_DEBUG(vmapiContextP, line);
                        // We can still process other events if we get a message get error so
                        // we don't need to leave the routine until all events have been processed.
                    } else {
                        strcpy(logStruct.userid, userid);
                        logStruct.eventType = eventType;
                        buf_length = sizeof(log_message_struct);
                        logBuf.mType = 1;
                        logBuf.messageStruct = logStruct;
                        if (msgsnd(msqid, &logBuf, buf_length, IPC_NOWAIT) < 0) {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for logon/off error, queue:%d, userid: %s, eventType: %d, buflen: %d\n", msqid,
                                    logStruct.userid, logStruct.eventType, (int) buf_length);
                            TRACE_END_DEBUG(vmapiContextP, line);
                            // We can still process other events if we get a message send error so
                            // we don't need to leave the routine until all events have been processed.
                        } else {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for logon/off, queue:%d, userid: %s, eventType: %d, buflen: %d\n", msqid,
                                    logStruct.userid, logStruct.eventType, (int) buf_length);
                            TRACE_END_DEBUG(vmapiContextP, line);
                        }
                    }
                // End handler for event class 0, event types: 0-1
                } else if ((eventType >= 9) && (eventType <= 14)) {
                    // Event Class 0: Event Types: 9-14 are relocation status indications
                    // Send a message to cause a relocation status indication to be created.
                    if ((msqid = msgget(MSGRELKEY, msgflg)) < 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgget for vmrelocate error, key: %d, errno: %d text: %s", MSGRELKEY, errno, strerror(errno));
                        TRACE_END_DEBUG(vmapiContextP, line);
                        // We can still process other events if we get a message get error so
                        // we don't need to leave the routine until all events have been processed.
                    } else {
                        // Fill in the common information for the message
                        buf_length = sizeof(rel_message_struct);
                        strcpy(msgRelocateSys.userid, userid);
                        msgRelocateSys.eventType = eventType;

                        // Fill in the event type unique information
                        if ((eventType == 9) || (eventType == 11)) {
                            strcpy(msgRelocateSys.targetzVM, systemId);
                        } else if ((eventType == 10) || (eventType == 12)) {
                            strcpy(msgRelocateSys.sourcezVM, systemId);
                        } else if ((eventType == 13) || (eventType == 14)) {
                            msgRelocateSys.reasonCode = (int) eventReasonCode;
                        }
                        msgRelocateSysBuf.mType = 1;
                        msgRelocateSysBuf.messageStruct = msgRelocateSys;
                        if (msgsnd(msqid, &msgRelocateSysBuf, buf_length, IPC_NOWAIT) < 0) {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for vmrelocate error, queue: %d, userid: %s, eventType: %d, buflen: %d\n",
                                    msqid, msgRelocateSys.userid, msgRelocateSys.eventType, (int) buf_length);
                            TRACE_END_DEBUG(vmapiContextP, line);

                        // We can still process other events if we get a message send error so
                        // we don't need to leave the routine until all events have been processed.
                        } else {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for vmrelocate, queue: %d, userid: %s, eventType: %d, buflen: %d\n",
                                    msqid, msgRelocateSys.userid, msgRelocateSys.eventType, (int) buf_length);
                            TRACE_END_DEBUG(vmapiContextP, line);
                        }
                    }
                }
            } else if ((eventClass == 1) && (eventType >= 9) && (eventType <= 10)) {
                // Event Class 1: Event Types: 9-10 are more relocation status indications
                // Send a message to cause a relocation status indication to be created.
                if ((msqid = msgget(MSGRELKEY, msgflg)) < 0) {
                    TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                    sprintf(line, "msgget for vmrelocate error, key: %d, errno: %d text: %s", MSGRELKEY, errno, strerror(errno));
                     TRACE_END_DEBUG(vmapiContextP, line);
                    // We can still process other events if we get a message get error so
                    // we don't need to leave the routine until all events have been processed.
                } else {
                    // Fill in the common information for the message
                    buf_length = sizeof(rel_message_struct);
                    strcpy(msgRelocateSys.userid, userid);
                    msgRelocateSys.eventType = eventType;

                    // Fill in the event type unique information
                    if (eventType == 9) {
                        strcpy(msgRelocateSys.targetzVM, systemId);
                    } else if (eventType == 10) {
                        strcpy(msgRelocateSys.sourcezVM, systemId);
                    }

                    msgRelocateSysBuf.mType = 1;
                    msgRelocateSysBuf.messageStruct = msgRelocateSys;
                    if (msgsnd(msqid, &msgRelocateSysBuf, buf_length, IPC_NOWAIT) < 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgsnd for vmrelocate error, queue: %d, userid: %s, eventType: %d, buflen: %d\n",
                                msqid, msgRelocateSys.userid, msgRelocateSys.eventType, (int) buf_length);
                        TRACE_END_DEBUG(vmapiContextP, line);

                        // We can still process other events if we get a message send error so
                        // we don't need to leave the routine until all events have been processed.
                    }
                }
            } else if ((eventClass == 2) || (eventClass == 3)) {
                // Event Class 2 and 3: Event Types: 7 is an SSI indication
                if ((eventType == 7)) {
                    // Send a message to cause an SSI status indication to be created.
                    if ((msqid = msgget(MSGSSIKEY, msgflg)) < 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                        sprintf(line, "msgget for SSI error, key: %d, errno: %d text: %s", MSGSSIKEY, errno, strerror(errno));
                        TRACE_END_DEBUG(vmapiContextP, line);

                        // We can still process other events if we get a message get error so
                        // we don't need to leave the routine until all events have been processed.
                    } else {
                        // Fill in the common information for the message
                        buf_length = sizeof(ssi_message_struct);
                        msgSSI.eventType = eventType;
                        strcpy(msgSSI.ssiName, ssiName);
                        msgSSI.preMode = preMode;
                        msgSSI.newMode = newMode;
                        msgSSIBuf.mType = 1;
                        msgSSIBuf.messageStruct = msgSSI;
                        if (msgsnd(msqid, &msgSSIBuf, buf_length, IPC_NOWAIT) < 0) {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for SSI error, key:%d, ssiName: %s, eventType: %d, buflen: %d, errno: %d text: %s\n",
                                    msqid, msgSSI.ssiName, msgSSI.eventType, (int) buf_length , errno, strerror(errno));
                            TRACE_END_DEBUG(vmapiContextP, line);

                            // We can still process other events if we get a message send error so
                            // we don't need to leave the routine until all events have been processed.
                        } else {
                            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
                            sprintf(line, "msgsnd for SSI, key: %d, ssiName: %s, eventType: %d, buflen: %d\n", msqid,
                                    msgSSI.ssiName, msgSSI.eventType, (int) buf_length);
                            TRACE_END_DEBUG(vmapiContextP, line);
                        }
                    }
                }
            }
        } else {
            // Handle unrecognized event data types.
            TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_ERROR);
            sprintf(line, "Unrecognized event data type received from SMAPI: %d\n", eventDataType);
            TRACE_END_DEBUG(vmapiContextP, line);
            sizeOfUnreadData = tempSize - actualSize;  // Remove all remaining data
        }

        // Strip off data from the transmission.  We will either strip off all remaining data or
        // just the remaining data for a single event in a multiple event transmission.
        TRACE_START(vmapiContextP, TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD, TRACELEVEL_DETAILS);
        sprintf(line, "Event unread: %d, total unread: %d \n", sizeOfUnreadData, totalToRead);
        TRACE_END_DEBUG(vmapiContextP, line);

        if (sizeOfUnreadData > 0) {
            if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *) smapiOutputP, sizeOfUnreadData))) {
                sprintf(line, "Event_Subscribe receive of remaining VMEvent data failed on socket %d with RC: %d\n", sockDesc, rc);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                goto exit_vmbkendMain_setSmapiSubscribeEventData;  // Exit from routine
            } else {
                actualSize = actualSize + sizeOfUnreadData;
            }
        }
    }

    // Final cleanup and return from this subroutine
exit_vmbkendMain_setSmapiSubscribeEventData:
    FREE_MEMORY(smapiOutputP);
    return rc;
}

/**
 * Get SMAPI level will check the cached file to see if it exists and if exists, check the date.
 * If the file does not exist or it is older than a day, it will call SMAPI to get the current level
 * and then store that in the file.
 *
 * A return code non 0 implies that an unexpected error occurred.
 */
int getSmapiLevel(struct _vmApiInternalContext* vmapiContextP, char * image, int * pSmapiLevel) {
    int defaultTimeLimit = 86400;  // seconds = approx 24 hours
    int createFile = 0;
    int rc = 0;
    struct stat statbuf;
    time_t currentTime;
    double fileAgeSeconds = 0;
    time_t fileTime = 0;
    unsigned int x = 0;
    vmApiQueryApiFunctionalLevelOutput * output;
    FILE *myStream;
    char outlevel[20];

    if (-1 == time(&currentTime)) {
        vmapiContextP->errnoSaved  = errno;
        printf("ERROR: Time function failed. Errno: %d text: %s\n", errno, strerror(errno));
        return 1;  /* Current time failed */
    }

    if (-1 == stat(CACHE_SMAPI_LEVEL_FILE, &statbuf)) {
        if (errno != ENOENT) {
            vmapiContextP->errnoSaved  = errno;
            printf("ERROR: File stat error on %s Errno: %d text: %s\n", CACHE_SMAPI_LEVEL_FILE, errno, strerror(errno));
            return 1;  /* Stat failed */
        }
        createFile = 1;
    }
    if (!createFile) {
        fileTime = statbuf.st_mtime;
        fileAgeSeconds = difftime(currentTime, fileTime);
        if ((fileAgeSeconds < 0) || (fileAgeSeconds > defaultTimeLimit)) {
            createFile = 1;
        }
    }
    if (createFile) {
        rc = smQuery_API_Functional_Level(vmapiContextP, "", 0, "", image, &output);
        // Handle the RC that comes back from making the SMAPI API call. If RC then the call to SMAPI failed
        if (rc) {
            printAndLogProcessingErrors("Query_API_Functional_Level", rc, vmapiContextP, "", 0);
            return 1;
        } else {
            if (output->common.returnCode != 0) {
                // Handle SMAPI return code and reason code
                rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_API_Functional_Level", output->common.returnCode,
                        output->common.reasonCode, vmapiContextP, "");
                return 1;
            }
        }

        *pSmapiLevel = output->common.reasonCode;
        myStream = fopen(CACHE_SMAPI_LEVEL_FILE, "w");
        if (myStream == NULL) {
            vmapiContextP->errnoSaved  = errno;
            printf("ERROR: fopen failed for %s errno:%d text: %s\n", CACHE_SMAPI_LEVEL_FILE, errno, strerror(errno));
            return 1;
        }

        sprintf(outlevel, "%d", *pSmapiLevel);
        rc = fputs(outlevel, myStream);
        if (rc < 0) {
            vmapiContextP->errnoSaved  = errno;
            printf("ERROR: fputs errno %d text: %s\n", errno, strerror(errno));
            return 1;
        }

        fclose(myStream);
        return 0;
    }

    // Need to read the file and get the SMAPI level
    myStream = fopen(CACHE_SMAPI_LEVEL_FILE, "r");
    if (myStream == NULL) {
        vmapiContextP->errnoSaved  = errno;
        printf("ERROR: fopen failed for %s errno:%d text: %s\n", CACHE_SMAPI_LEVEL_FILE, errno, strerror(errno));
        return 1;
    }

    if (NULL == (fgets(outlevel, sizeof(outlevel), myStream))) {
        vmapiContextP->errnoSaved  = errno;
        printf("ERROR: fgets errno %d text: %s\n", errno, strerror(errno));
        return 1;
    }

    fclose(myStream);
    *pSmapiLevel = atoi(outlevel);
    return 0;
}
