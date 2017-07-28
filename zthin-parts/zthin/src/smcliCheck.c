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

#include "smcliCheck.h"
#include "wrapperutils.h"

int checkAuthentication(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Check_Authentication";
    int rc;
    int option;
    int passWordLength = 0;
    char * passWord = NULL;
    char * userid = NULL;
    char strMsg[250];
    vmApiCheckAuthenticationOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "up";
    char tempStr[1];

    // Parse the command-line arguments
    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "u:p:h?")) != -1)
        switch (option) {
            case 'u':
                userid = optarg;
                break;

            case 'p':
                passWord = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Check_Authentication\n\n"
                    "SYNOPSIS\n"
                    "  smcli Check_Authentication\n\n"
                    "DESCRIPTION\n"
                    "  Use Check_Authentication to validate a userid/password pair.\n"
                    "  The following options are required:\n"
                    "    -u    User ID to validate. If the UserId is the same as the UserId of the \n"
                    "          zThin then the password is ignored\n"
                    "    -p    Password to validate\n");
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
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
    }

    if (!userid || !passWord) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }
    passWordLength = strlen(passWord);


    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Validating userid/password pair ... ", userid);

    rc = smCheck_Authentication(vmapiContextP, userid, passWordLength, passWord,
             &output);

    if (rc) {
        printAndLogProcessingErrors("Check_Authentication", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Check_Authentication", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}
