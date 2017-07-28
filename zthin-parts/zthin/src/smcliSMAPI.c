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

#include "smcliSMAPI.h"
#include "wrapperutils.h"

int smapiStatusCapture(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "SMAPI_Status_Capture";
    int rc;
    int option;
    char * profile = NULL;
    vmApiSMAPIStatusCaptureOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                profile = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  SMAPI_Status_Capture\n\n"
                    "SYNOPSIS\n"
                    "  smcli SMAPI_Status_Capture [-T] target_name\n\n"
                    "DESCRIPTION\n"
                    "  Use SMAPI_Status_Capture to capture data to assist with identification and\n"
                    "  resolution of a problem with the SMAPI servers.\n"
                    "  The following options are required:\n"
                    "    -T    The name of the target used for authorization.\n");
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
                return 1;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!profile) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Checking SMAPI status... ");

    rc = smSMAPI_Status_Capture(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            profile, &output);

    if (rc) {
        printAndLogProcessingErrors("SMAPI_Status_Capture", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
    	rc = printAndLogSmapiReturnCodeReasonCodeDescription("SMAPI_Status_Capture", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    
    return rc;
}
