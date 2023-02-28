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

#include "smSocket.h"
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

#ifndef AF_IUCV
#define AF_IUCV         32
#endif

#ifndef PF_IUCV
#define PF_IUCV        AF_IUCV
#endif

struct sockaddr_iucv {
    sa_family_t siucv_family;
    unsigned short siucv_port; /* Reserved */
    unsigned int siucv_addr; /* Reserved */
    char siucv_nodeid[8]; /* Reserved */
    char siucv_userid[8]; /* Guest User Id */
    char siucv_name[8]; /* Application Name */
};

// This macro is used to check return values on close
// and do one retry if the close had an EINTR error
#define CHECK_SOCKET_CLOSE(_SOCKETID_) \
if (retValue)\
{\
    saveCloseErrno = errno;\
    sprintf(line, "close() error on socket %d return value %d errno %d\n", _SOCKETID_, retValue, saveCloseErrno);\
    errorLog(vmapiContextP, \
                     __func__, \
                     TO_STRING(__LINE__), \
                     RcIucv, \
                     retValue, \
                     line);\
    if (EINTR == saveCloseErrno)\
    {\
        retValue = close(_SOCKETID_);\
        if (retValue)\
        {\
            saveCloseErrno = errno;\
            sprintf(line, "retried close() error on socket %d return value %d errno %d\n", _SOCKETID_, retValue, saveCloseErrno);\
            errorLog(vmapiContextP, \
                             __func__, \
                             TO_STRING(__LINE__), \
                             RcIucv, \
                             retValue, \
                             line);\
        }\
    }\
}

static const char* default_IUCV_server = "VSMREQIU";
static const char* IUCV_programName = "DMSRSRQU";

int smSocketInitialize(struct _vmApiInternalContext* vmapiContextP,    int * sockId) {
#define RETRY_CONNECTION_LIMIT 10
    const int SLEEP_TIMES[RETRY_CONNECTION_LIMIT] = { 0, 0, 1, 1, 2, 2, 8, 8,
            16, 32 };
    /* Variables */
    int retValue;
    char line[LINESIZE];
    int length;
    int retryConnection;
    int saveErrno, saveCloseErrno;
    struct sockaddr_iucv serverSockAddr;
    struct timeval timeoutValue;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_SOCKET);
    // If the trace file has not been read yet, do it.
    if (!(vmapiContextP->smTraceDetails->traceFileRead)) {
        readTraceFile(vmapiContextP);
    }

    // Place holders for context and background starting
    if (1 != vmapiContextP->contextCreatedFlag) {
        retValue = initializeThreadSemaphores(vmapiContextP, "", 1);  // Create context using no name to override current context name
        if (retValue) {
            sprintf(line, "smSocketInitialize(): context reserve() returned error: %d\n", retValue);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
            return PROCESSING_ERROR;
        }
    }

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
       sprintf(line, "smSocketInitialize: initializeThreadSemaphores completed successfully.\n");
    TRACE_END_DEBUG(vmapiContextP, line);

//    // If the backend is not marked as running, check it
//    if (!vmapiContextP->checkBackendFlag) {
//        retValue = vmbkendCheck(vmapiContextP);
//        if (retValue)
//            return retValue;  // if any error return
//    }


    /* Get a local socket.*/
    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "smSocketInitialize: trying to obtain local socket.\n");
    TRACE_END_DEBUG(vmapiContextP, line);

    *sockId = socket(PF_IUCV, SOCK_STREAM, IPPROTO_IP);
    if (*sockId == -1) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "smSocketInitialize(): socket() returned errno: %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, *sockId, line);
        return SOCKET_OBTAIN_ERROR;
    }

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "smSocketInitialize: local socket id %d obtained. Now trying connect loop. \n", *sockId);
    TRACE_END_DEBUG(vmapiContextP, line);

        /* Initialize the server IUCV socket structure */
    memset(&serverSockAddr, 0, sizeof(serverSockAddr));
    serverSockAddr.siucv_family = AF_IUCV;
    serverSockAddr.siucv_port = 0;
    serverSockAddr.siucv_addr = 0;
    memset(&serverSockAddr.siucv_nodeid, ' ', sizeof(serverSockAddr.siucv_nodeid));
    memset(&serverSockAddr.siucv_userid, ' ', sizeof(serverSockAddr.siucv_userid));
    memset(&serverSockAddr.siucv_name, ' ', sizeof(serverSockAddr.siucv_name));

    timeoutValue.tv_usec = 0;
    timeoutValue.tv_sec = 60;  // Changed to 60 now that af iucv and CMS are working better
    retValue = setsockopt(*sockId, SOL_SOCKET, SO_SNDTIMEO, (struct timeval *) &timeoutValue, sizeof(struct timeval));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): connect timeout returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(*sockId);
        CHECK_SOCKET_CLOSE(*sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    // Do we have an IUCV userid; or just use the default?
    // do not copy in the null terminator on strings
    length = strlen(vmapiContextP->IucvUserid);
    if (length <= 0 || length > 8) {
        memcpy(&serverSockAddr.siucv_userid, default_IUCV_server, strlen(default_IUCV_server));
    } else {
        memcpy(&serverSockAddr.siucv_userid, &vmapiContextP->IucvUserid, strlen(vmapiContextP->IucvUserid));
    }

    // Add in the iucv program name constant
    memcpy(&serverSockAddr.siucv_name[0], IUCV_programName, strlen(IUCV_programName));

    // Try to connect to the IUCV server
    for (retryConnection = 1;; retryConnection++) {
        retValue = connect(*sockId, (struct sockaddr *) &serverSockAddr, sizeof(serverSockAddr));
        if (retValue != 0) {
            saveErrno = errno;
            vmapiContextP->errnoSaved = errno;
            sprintf(line, "connect() of socket %d returned %d errno %d\n", *sockId, retValue, errno);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, retValue, line);
            // If we have exceeded the retry limit, then shutdown, close and return with error
            if (retryConnection >= RETRY_CONNECTION_LIMIT) {
                TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                    sprintf(line, "smSocketInitialize: connect retry limit exceeded.\n");
                TRACE_END_DEBUG(vmapiContextP, line);
                retValue = close(*sockId);
                CHECK_SOCKET_CLOSE(*sockId);
                switch (saveErrno) {
                    case ECONNREFUSED:
                        return SOCKET_CONNECT_REFUSED_ERROR;
                    case EAGAIN:
                        return SOCKET_CONNECT_TRYAGAIN_ERROR;
                    default:
                        return SOCKET_PROCESSING_ERROR;
                }  // end switch
            }

            // Is this an errno that we can retry? If so continue the loop
            switch (saveErrno) {
                case ECONNREFUSED:
                    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                        sprintf(line, "====>>ECONNREFUSED, going to close and retry connect.\n");
                    TRACE_END_DEBUG(vmapiContextP, line);

                case EAGAIN:
                    if (saveErrno == EAGAIN) {
                        TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                            sprintf(line, "====>>EAGAIN, going to close and retry connect.\n");
                        TRACE_END_DEBUG(vmapiContextP, line);
                    }

                    // close the current socket. Get a new one, and retry the connect.
                    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                        sprintf(line, "====>>closing the socket before retry.\n");
                    TRACE_END_DEBUG(vmapiContextP, line);
                    retValue = close(*sockId);
                    CHECK_SOCKET_CLOSE(*sockId);

                    // Delay for a while to give SMAPI some time to restart
                    if (SLEEP_TIMES[retryConnection] > 0) {
                        TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                            sprintf(line, "+++++++++ Sleeping for %d seconds\n", SLEEP_TIMES[retryConnection]);
                        TRACE_END_DEBUG(vmapiContextP, line);
                        sleep(SLEEP_TIMES[retryConnection]);
                    }

                    *sockId = socket(PF_IUCV, SOCK_STREAM, IPPROTO_IP);
                    if (*sockId == -1) {
                        vmapiContextP->errnoSaved = errno;
                        sprintf(line, "smSocketInitialize(): socket() returned errno: %d\n", errno);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, *sockId, line);
                        return SOCKET_OBTAIN_ERROR;
                    }
                    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                        sprintf(line, "smSocketInitialize: retry obtained new local socket id %d. Now retrying connect.\n", *sockId);
                    TRACE_END_DEBUG(vmapiContextP, line);
                    // Reset the return and reason codes in the context
                    vmapiContextP->rc = 0;
                    vmapiContextP->reason = 0;
                    continue;  // Try to connect again

                default:
                    break;  // Shutdown the socket and return with error, if errno is not listed
            }


            TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                sprintf(line, "====>>closing the socket \n");
            TRACE_END_DEBUG(vmapiContextP, line);

            retValue = close(*sockId);
            CHECK_SOCKET_CLOSE(*sockId);

            TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                sprintf(line, "====>>return from closing the socket \n");
            TRACE_END_DEBUG(vmapiContextP, line);

            TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, SOCKET_PROCESSING_ERROR);
            return SOCKET_PROCESSING_ERROR;
        }
        else
            break;  // Got a good connection, leave loop
    }

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "smSocketInitialize: Socket connect completed successfully.\n");
    TRACE_END_DEBUG(vmapiContextP, line);

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, 0);
    return 0;
}

int smSocketWrite(struct _vmApiInternalContext* vmapiContextP, int sockId, char * data, int dataLen) {
    int retValue;
    char line[LINESIZE];
    struct timeval timeoutValue;
    int onValue = 1;
    int saveErrno, saveCloseErrno;
    unsigned long ulTimeoutSeconds;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_SOCKET);
    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_BUFFER_OUT);
        dumpArea(vmapiContextP, data, dataLen);
    TRACE_END;

    if (vmapiContextP->socketTimeout == -1) {
        // no valid timeout value passed
        ulTimeoutSeconds = Socket_Timeout;
    } else {
        ulTimeoutSeconds = vmapiContextP->socketTimeout;
    }

    // Set the send socket timeout value
    timeoutValue.tv_usec = 0;
    timeoutValue.tv_sec = ulTimeoutSeconds;
    retValue = setsockopt(sockId, SOL_SOCKET, SO_SNDTIMEO, (struct timeval *) &timeoutValue, sizeof(struct timeval));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): send timeout returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(sockId);
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    // Set the reuse socket address value
    onValue = 1;
    retValue = setsockopt(sockId, SOL_SOCKET, SO_REUSEADDR, (int *) &onValue,
            sizeof(int));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): reuse addr returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(sockId);
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    /* Write the data to the socket */
    while (dataLen > 0) {
        retValue = send(sockId, (void *) data, dataLen, 0);
        if (retValue < 0) {
            saveErrno = errno;
            vmapiContextP->errnoSaved = errno;
            // Log a special message and set the return and reason code if a timeout
            if (errno == EAGAIN) {
                sprintf(line, "smSocketWrite(): timeout errno %d\n", errno);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsSocketTimeout, line);
            } else {
                sprintf(line, "smSocketWrite(): send() returned errno %d\n", errno);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
            }
            retValue = close(sockId);
            CHECK_SOCKET_CLOSE(sockId);
            if (saveErrno == EAGAIN)
                return SOCKET_TIMEOUT_ERROR;
            if (saveErrno == ENOTCONN)
                return SOCKET_NOT_CONNECTED_ERROR;
            return SOCKET_WRITE_ERROR;
        }
        data = data + retValue;
        dataLen = dataLen - retValue;
    }
    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, 0);
    return 0;
}

int smSocketRead(struct _vmApiInternalContext* vmapiContextP, int sockId, char * buff, int len) {
    // Variables
    int retValue;
    int lenRead;
    int retryNoData;
    char line[LINESIZE];
    retryNoData = 0;
    struct timeval timeoutValue;
    unsigned long ulTimeoutSeconds;
    long ulTimeoutSecondsRequested = 0;
    char * ptrTimeOutValue;
    int onValue = 1;
    void * buffPtr;
    int buffLength;
    int saveErrno, saveCloseErrno;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_SOCKET);
    buffPtr = (void *) buff;
    buffLength = len;

    ulTimeoutSeconds = Socket_Timeout;

    /* Oobtain read timeout environment variable */
    ptrTimeOutValue = getenv("ZVMMAP_READ_TIMEOUT_SECONDS");
    if (ptrTimeOutValue) {
        ulTimeoutSecondsRequested = atol(ptrTimeOutValue);
        if (ulTimeoutSecondsRequested > 0) {
            ulTimeoutSeconds = ulTimeoutSecondsRequested;
            TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                sprintf(line, "Socket read timeout set from enviromentVariable. %lu seconds.\n", ulTimeoutSeconds);
            TRACE_END_DEBUG(vmapiContextP, line);
        }
    }

    // overwrite timeout value if specified --timeout option
    if (vmapiContextP->socketTimeout == -1) {
        // no valid timeout value passed, nothing to do
    } else {
        ulTimeoutSeconds = vmapiContextP->socketTimeout;
    }

    // Set the read socket timeout value
    timeoutValue.tv_usec = 0;
    timeoutValue.tv_sec = ulTimeoutSeconds;
    retValue = setsockopt(sockId, SOL_SOCKET, SO_RCVTIMEO, (struct timeval *) &timeoutValue, sizeof(struct timeval));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): receive timeout returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(sockId);
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    // Set the reuse socket address value
    onValue = 1;
    retValue = setsockopt(sockId, SOL_SOCKET, SO_REUSEADDR, (int *) &onValue, sizeof(int));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): reuse addr returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(sockId);
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    /* Read the data from the socket */
    lenRead = 0;
    while (lenRead < len) {
        retValue = recv(sockId, buffPtr, buffLength, 0);
        if (retValue < 0) {
            saveErrno = errno;
            vmapiContextP->errnoSaved = errno;
            // Log a special message and set the return and reason code if a timeout
            if (errno == EAGAIN) {
                sprintf(line, "smSocketRead(): timeout errno %d\n", errno);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsSocketTimeout, line);
            } else {
                sprintf(line, "smSocketRead(): recv() returned errno %d\n", errno);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
            }
            retValue = close(sockId);
            CHECK_SOCKET_CLOSE(sockId);
            if (saveErrno == EAGAIN)
                return SOCKET_TIMEOUT_ERROR;
            if (saveErrno == ENOTCONN)
                return SOCKET_NOT_CONNECTED_ERROR;
            return SOCKET_READ_ERROR;
        }

        // No data returned? Retry 10 times if we haven't received any data
        if (retValue == 0) {
            retryNoData++;
            if (retryNoData > 10 && lenRead == 0) {
                sprintf(line, "smSocketRead(): recv() returned no data after 10 retries.\n");
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                retValue = close(sockId);
                CHECK_SOCKET_CLOSE(sockId);
                return SOCKET_READ_ERROR;
            }
        }
        lenRead += retValue;
        buffPtr += retValue;
        buffLength -= retValue;
    }  // end while more data to read

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_BUFFER_IN);
        dumpArea(vmapiContextP, buff, lenRead);
    TRACE_END;

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "smSocketRead(): read %d bytes of data \n", lenRead);
    TRACE_END_DEBUG(vmapiContextP, line);

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, 0);
    /* Return */
    return 0;
}

int smSocketReadLoop(struct _vmApiInternalContext* vmapiContextP, int sockId, char * buff, int len, int readMod) {
    int retValue;
    int lenRead;
    int retryNoData;
    char line[LINESIZE];
    retryNoData = 0;
    struct timeval timeoutValue;
    unsigned long ulTimeoutSeconds;
    long ulTimeoutSecondsRequested = 0;
    char * ptrTimeOutValue;
    void * buffPtr;
    int buffLength;
    int saveErrno, saveCloseErrno;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_SOCKET);

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "--> Inside smSocketReadLoop:.\n");
    TRACE_END_DEBUG(vmapiContextP, line);

    buffPtr = (void *) buff;
    buffLength = len;

    ulTimeoutSeconds = Socket_Indication_Timeout;

    /* Obtain read timeout environment variable */
    ptrTimeOutValue = getenv("ZTHIN_READ_INDICATION_TIMEOUT_SECONDS");
    if (ptrTimeOutValue) {
        ulTimeoutSecondsRequested = atol(ptrTimeOutValue);
        if (ulTimeoutSecondsRequested > 0) {
            ulTimeoutSeconds = ulTimeoutSecondsRequested;
            TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                sprintf(line, "Socket read indication timeout set from enviromentVariable. %lu seconds.\n", ulTimeoutSeconds);
            TRACE_END_DEBUG(vmapiContextP, line);
        }
    }

    // Set the read socket timeout value
    timeoutValue.tv_usec = 0;
    timeoutValue.tv_sec = ulTimeoutSeconds;
    retValue = setsockopt(sockId, SOL_SOCKET, SO_RCVTIMEO, (struct timeval *) &timeoutValue, sizeof(struct timeval));
    if (retValue < 0) {
        vmapiContextP->errnoSaved = errno;
        sprintf(line, "setsockopt(): receive timeout returned errno %d\n", errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
        retValue = close(sockId);
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    /* Read the data from the socket */
    lenRead = 0;
    while (lenRead < len) {
        retValue = recv(sockId, buffPtr, buffLength, 0);

        TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
            sprintf(line, "--> return value of recv inside socketReadLoop = %d \n", retValue);
        TRACE_END_DEBUG(vmapiContextP, line);

        if (retValue < 0) {
            vmapiContextP->errnoSaved = errno;
            saveErrno = errno;
            // Log a special message and set the return and reason code if a timeout
            if (errno == EAGAIN) {
                TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                    sprintf(line, "--> Errno inside socketReadLoop = %d for recv() return value = %d \n", errno, retValue);
                TRACE_END_DEBUG(vmapiContextP, line);
                return CUSTOM_DEFINED_SOCKET_RETRY;

            } else {
                if (readMod != SOCKET_ERROR_OK) {
                    sprintf(line, "smSocketRead(): recv() returned errno %d\n", errno);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, errno, line);
                }
            }

            retValue = close(sockId);
            CHECK_SOCKET_CLOSE(sockId);
            if (saveErrno == EAGAIN)
                return SOCKET_TIMEOUT_ERROR;
            if (saveErrno == ENOTCONN)
                return SOCKET_NOT_CONNECTED_ERROR;
            if (readMod == SOCKET_ERROR_OK)
                return 0;
            return SOCKET_READ_ERROR;
        }

        TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
            sprintf(line, "smSocketRead(): retValue %d \n", retValue);
        TRACE_END_DEBUG(vmapiContextP, line);
        // No data returned? Retry 100 times if we haven't received any data
        if (retValue == 0) {
            retryNoData++;
            if (retryNoData > 100 && lenRead == 0) {
                TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
                    sprintf(line, "--> Errno inside socketReadLoop = %d for recv() return value = %d \n", errno, retValue);
                TRACE_END_DEBUG(vmapiContextP, line);
                return CUSTOM_DEFINED_SOCKET_RETRY;
            }
        }
        lenRead += retValue;
        buffPtr += retValue;
        buffLength -= retValue;
    }

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_BUFFER_IN);
        dumpArea(vmapiContextP, buff, lenRead);
    TRACE_END;

    TRACE_START(vmapiContextP, TRACEAREA_SOCKET, TRACELEVEL_DETAILS);
        sprintf(line, "smSocketRead(): read %d bytes of data \n", lenRead);
    TRACE_END_DEBUG(vmapiContextP, line);

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, 0);

    return 0;
}

int smSocketTerminate(struct _vmApiInternalContext* vmapiContextP, int sockId) {
    int retValue;
    char line[LINESIZE];
    int saveCloseErrno;

    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_SOCKET);

    /* Shutdown and Close the socket */
    retValue = shutdown(sockId, SHUT_RDWR);
    if ((retValue != 0) && (errno != 107)) {
        sprintf(line, "smSocketTerminate(): shutdown() returned %d, errno: %d\n", retValue, errno);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, retValue, line);
    }

    retValue = close(sockId);
    if (retValue != 0) {
        CHECK_SOCKET_CLOSE(sockId);
        return SOCKET_PROCESSING_ERROR;
    }

    TRACE_EXIT_FLOW(vmapiContextP, TRACEAREA_SOCKET, 0);
    return 0;
}
