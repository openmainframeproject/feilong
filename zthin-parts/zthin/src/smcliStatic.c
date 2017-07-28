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
#include "smcliStatic.h"
#include "wrapperutils.h"

int staticImageChangesActivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    int rc;
    int option;
    char * image = NULL;
    vmApiStaticImageChangesActivateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Static_Image_Changes_Activate_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Static_Image_Changes_Activate_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Static_Image_Changes_Activate_DM to enable changes to the source\n"
                    "  directory to be made available to virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Enabling changes to %s's directory... ", image);

    rc = smStatic_Image_Changes_Activate_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Static_Image_Changes_Activate_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Static_Image_Changes_Activate_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int staticImageChangesDeactivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    int rc;
    int option;
    char * image = NULL;
    vmApiStaticImageChangesDeactivateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Static_Image_Changes_Deactivate_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Static_Image_Changes_Deactivate_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Static_Image_Changes_Deactivate_DM to prevent changes to the\n"
                    "  source directory from being made available to virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Preventing changes to %s's directory... ", image);

    rc = smStatic_Image_Changes_Deactivate_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Static_Image_Changes_Deactivate_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Static_Image_Changes_Deactivate_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int staticImageChangesImmediateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    int rc;
    int option;
    char * image = NULL;
    vmApiStaticImageChangesImmediateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Static_Image_Changes_Immediate_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Static_Image_Changes_Immediate_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Static_Image_Changes_Immediate_DM to make changes to the source\n"
                    "  directory immediately available to virtual images regardless of the\n"
                    "  current status of static image changes (active or inactive).\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Making changes to %s's directory immediately available... ", image);

    rc = smStatic_Image_Changes_Immediate_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Static_Image_Changes_Immediate_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Static_Image_Changes_Immediate_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}
