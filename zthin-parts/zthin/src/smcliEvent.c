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
#include <sys/stat.h>
#include <errno.h>
#include <fcntl.h>
#include <ctype.h>
#include <limits.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/*
 * Path of the named pipe (FIFO) where every event line is written.
 *
 * The FIFO is a kernel object: the file at this path is only a name, and no
 * event data is stored on disk.  The data sits in a fixed-size kernel pipe
 * buffer, which is 64 KB by default on Linux, and it is discarded once every
 * process has closed the FIFO.  When the buffer is full (the consumer is not
 * reading fast enough), further writes fail and the event is dropped.
 */
#define EVENT_PIPE_PATH "/tmp/zvm_events_host.fifo"

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

/* Set by signal handler so the loops exit cleanly on SIGINT/SIGTERM */
static volatile sig_atomic_t eventSubscribe_stop = 0;

static void eventSubscribe_sighandler(int sig) {
    (void) sig;
    eventSubscribe_stop = 1;
}

/*
 * Open (creating it if needed) the event FIFO.
 *
 * The FIFO is created with the default mode 0666 (subject to the umask).
 * After opening, it is verified to be a
 * FIFO owned by the effective user, so a pre-created file or symlink at the
 * well-known path is rejected.  It is opened O_RDWR so the write end is always
 * open (readers never see EOF) and O_NONBLOCK so a full pipe can never stall
 * the subscriber.
 *
 * Returns the fd, or -1 (with a message on stderr) on failure.
 */
static int openEventPipe(void) {
    struct stat st;
    int fd;

    if (mkfifo(EVENT_PIPE_PATH, 0666) < 0 && errno != EEXIST) {
        fprintf(stderr, "ERROR: Could not create named pipe %s (errno=%d)\n", EVENT_PIPE_PATH, errno);
        return -1;
    }

    fd = open(EVENT_PIPE_PATH, O_RDWR | O_NONBLOCK | O_NOFOLLOW);
    if (fd < 0) {
        fprintf(stderr, "ERROR: Could not open named pipe %s (errno=%d)\n", EVENT_PIPE_PATH, errno);
        return -1;
    }

    if (fstat(fd, &st) < 0 || !S_ISFIFO(st.st_mode) || st.st_uid != geteuid()) {
        fprintf(stderr, "ERROR: %s is not a FIFO owned by the current user\n", EVENT_PIPE_PATH);
        close(fd);
        return -1;
    }

    return fd;
}

/*
 * Write one event line to stdout and to the FIFO.  The line is well below
 * PIPE_BUF, so the write is all-or-nothing.  If the FIFO is full (no reader
 * keeping up) the event is dropped on the FIFO and a warning is written to stderr.
 */
static void publishEvent(int pipe_fd, const char *line) {
    printf("%s", line);
    fflush(stdout);
    if (write(pipe_fd, line, strlen(line)) < 0) {
        fprintf(stderr, "WARNING: Event not written to named pipe (errno=%d): %s", errno, line);
    }
}

/*
 * Drain the logon/logoff IPC queue without blocking.  Each message is
 * published as a single line:
 *
 *   EVENT LOGON    userid=<id> type=0
 *   EVENT LOGOFF   userid=<id> type=1
 *
 * If pipe_fd is negative the messages are discarded instead of published.
 * Returns the number of messages read.
 */
static int drainLogonLogoff(int pipe_fd) {
    int total = 0;
    char linebuf[512];
    log_message_buf logBuf;
    int msqid = msgget(MSGKEY, 0);

    if (msqid < 0) {
        return 0;
    }

    while (msgrcv(msqid, &logBuf, sizeof(log_message_struct), 0, IPC_NOWAIT) > 0) {
        total++;
        if (pipe_fd < 0) {
            continue;
        }
        logBuf.messageStruct.userid[sizeof(logBuf.messageStruct.userid) - 1] = '\0';
        snprintf(linebuf, sizeof(linebuf), "EVENT %-8s userid=%s type=%d\n",
                 (logBuf.messageStruct.eventType == 0) ? "LOGON" : "LOGOFF",
                 logBuf.messageStruct.userid,
                 logBuf.messageStruct.eventType);
        publishEvent(pipe_fd, linebuf);
    }

    return total;
}

int eventSubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    int option;
    int pipe_fd;
    int waited;
    long timeoutSeconds = 0;   /* 0 = run until signal */
    char *endP;
    time_t deadline = 0;
    struct sigaction sa;
    struct timespec ts;

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
                    "  Subscribe to z/VM logon/logoff events.  The zthin event listener runs\n"
                    "  inside this process, so events are only collected while this command\n"
                    "  is running.  Each event is printed to stdout as a single line and also\n"
                    "  written to the named pipe " EVENT_PIPE_PATH ".\n"
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

    /* Install signal handlers first so Ctrl-C / SIGTERM also interrupts the startup wait. */
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = eventSubscribe_sighandler;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    pipe_fd = openEventPipe();
    if (pipe_fd < 0) {
        return 1;
    }

    /*
     * Ensure the backend thread (vmbkendMain) is running.  It creates the IPC
     * queue and starts the thread that subscribes to events from SMAPI.
     */
    vmbkendCheck(vmapiContextP);

    /* Wait up to 10 seconds (50 * 200 ms) for the logon/logoff queue to appear. */
    ts.tv_sec = 0;
    ts.tv_nsec = 200000000L;
    for (waited = 0; waited < 50 && !eventSubscribe_stop; waited++) {
        if (msgget(MSGKEY, 0) >= 0) {
            break;
        }
        nanosleep(&ts, NULL);
    }

    if (eventSubscribe_stop) {
        close(pipe_fd);
        return 0;
    }

    if (msgget(MSGKEY, 0) < 0) {
        fprintf(stderr, "ERROR: Event queue not accessible after waiting (errno=%d). "
                "Check SMAPI connectivity.\n", errno);
        close(pipe_fd);
        return 1;
    }

    /* Discard events left in the queue by an earlier run so they are not replayed. */
    drainLogonLogoff(-1);

    if (timeoutSeconds > 0) {
        deadline = time(NULL) + (time_t) timeoutSeconds;
    }

    fprintf(stderr, "INFO: Listening for z/VM logon/logoff events. Press Ctrl-C to stop.\n");
    fprintf(stderr, "INFO: Writing events to named pipe: %s\n", EVENT_PIPE_PATH);

    ts.tv_nsec = 100000000L;   /* 100 ms */
    while (!eventSubscribe_stop) {
        if (timeoutSeconds > 0 && time(NULL) >= deadline) {
            break;
        }
        drainLogonLogoff(pipe_fd);
        nanosleep(&ts, NULL);
    }

    drainLogonLogoff(pipe_fd);
    close(pipe_fd);

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
