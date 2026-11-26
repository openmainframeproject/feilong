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
#include "smcliEvent.h"
#include "wrapperutils.h"
#include <sys/ipc.h>
#include <sys/msg.h>
#include <errno.h>
#include <ctype.h>
#include <limits.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

int eventStreamAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Event_Stream_Add";
    // Parse the command-line arguments
    int option;
    int rc;
    long eventId;
    int eventIdSpecified = 0;
    char * image = NULL;
    int stringCount = 0;
    char ** stringArray = 0;
    int hexstringCount = 0;  // Allow hex character input some day?
    char ** hexstringArray;
    char * end;
    int arrayBytes = 0;
    const char * optString = "-T:d:e:h?";
    vmApiEventStreamAddOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tde";
    char tempStr[1];
    char strMsg[250];

    // Count up the max number of arguments to create the array
    opterr = 0;  // Supress messages
    while ((option = getopt(argC, argV, optString)) != -1) {
        arrayBytes = arrayBytes + sizeof(*stringArray);
    }

    optind = 1;  // Reset optind so getopt can rescan arguments
    opterr = 1;  // Enable messages

    if (arrayBytes > 0) {
        if (0 == (stringArray = malloc(arrayBytes)))return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    // Future enhancement is to allow hex char string input x:
    // Add - to getopt to force processing in order of options specified
    while ((option = getopt(argC, argV, "-T:d:e:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'd':
                stringArray[stringCount] = optarg;
                stringCount++;
                break;

            case 'e':
                eventIdSpecified = 1;
                eventId = strtol( optarg, &end, 10);
                if ( *end != '\0' ) {
                    printf( "\nERROR: Event Id must be an integer > 16777215\n" );
                    return 1;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Event_Stream_Add\n\n"
                    "SYNOPSIS\n"
                    "  smcli Event_Stream_Add [-T] image_name [-e] event_type \n"
                    "   [-d] 'event data'\n"
                    "DESCRIPTION\n"
                    "  Use Event_Stream_Add to put type 1 event data on *VMEVENT stream\n"
                    "  The following options are required:\n"
                    "    -T    The name of the authorized virtual machine for this API.\n"
                    "    -e    An integer id value > 16777215\n"
                    "    -d    quoted string containing the event data\n");
                FREE_MEMORY_CLEAR_POINTER(stringArray);
                printRCheaderHelp();
                return 0;

            case '?':
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                if (isprint (optopt)) {
                    sprintf(tempStr,"%c", optopt);
                    if (strstr(argumentsRequired, tempStr)) {
                        printf("This option requires an argument: -%c\n", optopt);
                    } else {
                        printf("Unknown option -%c\n", optopt);
                    }
                } else {
                    printf("Unknown option character \\x%x\n", optopt);
                }
                FREE_MEMORY_CLEAR_POINTER(stringArray);
                return 1;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(stringArray);
                return 1;
     }

     if (!image || ( !eventIdSpecified ) || !stringCount) {
         DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
         printf("\nERROR: Missing required options\n");
         if (arrayBytes > 0){
             FREE_MEMORY_CLEAR_POINTER(stringArray);
         }
         return 1;
     }

     if (( eventId < 16777215)) {
         DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
         printf( "\nERROR: Event Id must be an integer greater than 16777215\n" );
         if (arrayBytes > 0){
             FREE_MEMORY_CLEAR_POINTER(stringArray);
         };
         return 1;
     }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding event id %d event data.", eventId);

    rc = smEvent_Stream_Add(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
         image, (int) eventId, stringCount, stringArray, hexstringCount, hexstringArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Event_Stream_Add", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Event_Stream_Add", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

/* Set by signal handler so the loops exit cleanly on SIGINT/SIGTERM/SIGALRM */
static volatile sig_atomic_t eventSubscribe_stop = 0;

static void eventSubscribe_sighandler(int sig) {
    (void) sig;
    eventSubscribe_stop = 1;
}

/*
 * Write one event line to stdout and flush it, so a reader on a pipe gets
 * the event at once instead of when the stdio buffer fills.
 */
static void publishEvent(const char *line) {
    printf("%s", line);
    fflush(stdout);
}

/*
 * Non-blocking drain of the logon/logoff IPC queue.  Used only at startup
 * to discard stale messages left by an earlier run, and at teardown to flush
 * any final messages that arrived while the signal was being processed.
 *
 * If publish is 0 the messages are discarded instead of published.
 * Returns the number of messages consumed.
 */
static int drainLogonLogoff(int publish) {
    int total = 0;
    char linebuf[512];
    log_message_buf logBuf;
    int msqid = msgget(MSGKEY, 0);

    if (msqid < 0) {
        return 0;
    }

    while (msgrcv(msqid, &logBuf, sizeof(log_message_struct), 0, IPC_NOWAIT) > 0) {
        total++;
        if (!publish) {
            continue;
        }
        logBuf.messageStruct.userid[sizeof(logBuf.messageStruct.userid) - 1] = '\0';
        snprintf(linebuf, sizeof(linebuf), "EVENT %-8s userid=%s type=%d\n",
                 (logBuf.messageStruct.eventType == 0) ? "LOGON" : "LOGOFF",
                 logBuf.messageStruct.userid,
                 logBuf.messageStruct.eventType);
        publishEvent(linebuf);
    }

    return total;
}

/*
 * Block until one logon/logoff message arrives on the IPC queue, then
 * publish it.  Returns 1 if a message was published, 0 if interrupted by
 * a signal (SIGINT, SIGTERM, or SIGALRM), -1 on a hard queue error.
 */
static int waitAndPublish(void) {
    char linebuf[512];
    log_message_buf logBuf;
    int msqid = msgget(MSGKEY, 0);
    ssize_t n;

    if (msqid < 0) {
        return -1;
    }

    n = msgrcv(msqid, &logBuf, sizeof(log_message_struct), 0, 0 /* blocking */);
    if (n < 0) {
        if (errno == EINTR) {
            return 0;   /* interrupted by signal — caller checks eventSubscribe_stop */
        }
        fprintf(stderr, "ERROR: msgrcv failed (errno=%d)\n", errno);
        return -1;
    }

    logBuf.messageStruct.userid[sizeof(logBuf.messageStruct.userid) - 1] = '\0';
    snprintf(linebuf, sizeof(linebuf), "EVENT %-8s userid=%s type=%d\n",
             (logBuf.messageStruct.eventType == 0) ? "LOGON" : "LOGOFF",
             logBuf.messageStruct.userid,
             logBuf.messageStruct.eventType);
    publishEvent(linebuf);
    return 1;
}

int eventSubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    int option;
    long timeoutSeconds = 0;   /* 0 = run until signal */
    char *endP;
    struct sigaction sa;

    opterr = 0;
    while ((option = getopt(argC, argV, "t:h?")) != -1) {
        switch (option) {
            case 't':
                errno = 0;
                timeoutSeconds = strtol(optarg, &endP, 10);
                if (errno != 0 || endP == optarg || *endP != '\0'
                        || timeoutSeconds < 0 || timeoutSeconds > INT_MAX) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf("Usage: smcli Event_Subscribe [-t timeout_seconds]\n");
                    return 1;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Event_Subscribe\n\n"
                    "SYNOPSIS\n"
                    "  smcli Event_Subscribe [-t timeout_seconds]\n\n"
                    "DESCRIPTION\n"
                    "  NOTE: This command is an internal interface of the Feilong sdkserver.\n"
                    "  Its options and output format are not stable and may change without\n"
                    "  notice. Applications must use the Feilong REST API (GET /host/events)\n"
                    "  instead of calling this command.\n\n"
                    "  Subscribe to z/VM logon/logoff events.  The zthin event listener runs\n"
                    "  inside this process, so events are only collected while this command\n"
                    "  is running.  Each event is printed to stdout as a single line.\n"
                    "  Status and error messages are written to stderr.\n\n"
                    "  Event line format:\n"
                    "    EVENT LOGON    userid=<id> type=0\n"
                    "    EVENT LOGOFF   userid=<id> type=1\n\n"
                    "  Options:\n"
                    "    -t  How many seconds to listen before exiting (0 = run forever).\n"
                    "        Default: 0 (run until SIGINT/SIGTERM).\n");
                return 0;

            case '?':
            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                printf("Usage: smcli Event_Subscribe [-t timeout_seconds]\n");
                return 1;
        }
    }

    /*
     * Install signal handlers.  SA_RESTART is intentionally NOT set so that
     * SIGINT, SIGTERM, and SIGALRM all interrupt the blocking msgrcv() with
     * EINTR, which is how we exit the event loop without polling.
     */
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = eventSubscribe_sighandler;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGALRM, &sa, NULL);

    /*
     * Ensure the backend thread (vmbkendMain) is running.  It creates the IPC
     * queue and signals thread_initialized_cv before returning, so the queue
     * is guaranteed to exist by the time vmbkendCheck() returns.
     */
    vmbkendCheck(vmapiContextP);

    if (eventSubscribe_stop) {
        return 0;
    }

    if (msgget(MSGKEY, 0) < 0) {
        fprintf(stderr, "ERROR: Event queue not accessible (errno=%d). "
                "Check SMAPI connectivity.\n", errno);
        return 1;
    }

    /* Discard stale events left in the queue by an earlier run. */
    drainLogonLogoff(0);

    /*
     * Schedule an alarm if a timeout was requested.  SIGALRM is caught by
     * eventSubscribe_sighandler, which sets eventSubscribe_stop and causes
     * the blocking msgrcv() in waitAndPublish() to return EINTR.
     */
    if (timeoutSeconds > 0) {
        alarm((unsigned int) timeoutSeconds);
    }

    fprintf(stderr, "INFO: Listening for z/VM logon/logoff events. Press Ctrl-C to stop.\n");

    while (!eventSubscribe_stop) {
        if (waitAndPublish() < 0) {
            break;
        }
    }

    alarm(0);   /* cancel any pending alarm */
    drainLogonLogoff(1);

    fprintf(stderr, "INFO: Event_Subscribe stopped.\n");
    return 0;
}

int eventUnsubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    // Skip doing this since we do not support subscribe. (Requires a continuously open socket)
    int option;
    int rc = 0;
    printf("Not implemented.\n");
    return rc;
}
