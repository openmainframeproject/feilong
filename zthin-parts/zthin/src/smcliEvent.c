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
#include "smcliEvent.h"
#include "wrapperutils.h"

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
                return 1;
                break;

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
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(stringArray);
                return 1;
                break;
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

int eventSubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    // Skip doing this since it requires a continuously open socket
    int rc = 0;
    printf("Not implemented.\n");
    return rc;
}

int eventUnsubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    // Skip doing this since we do not support subscribe. (Requires a continuously open socket)
    int option;
    int rc = 0;
    printf("Not implemented.\n");
    return rc;
}
