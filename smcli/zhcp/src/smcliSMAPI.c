/**
 * IBM (C) Copyright 2013, 2017 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
                return 1;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
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
        printAndLogSmapiCallReturnCode("SMAPI_Status_Capture", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
    	rc = printAndLogSmapiReturnCodeReasonCodeDescription("SMAPI_Status_Capture", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    
    return rc;
}
