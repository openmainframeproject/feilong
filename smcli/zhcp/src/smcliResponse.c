/**
 * IBM (C) Copyright 2013, 2017 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#include "smcliResponse.h"
#include "wrapperutils.h"

int responseRecovery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Response_Recovery";
    int rc;
    int option;
    int failedRequestID = 0;
    char * image = NULL;
    vmApiResponseRecoveryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:f:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'f':
                failedRequestID = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Response_Recovery\n\n"
                    "SYNOPSIS\n"
                    "  smcli Response_Recovery [-T] image_name [-f] failedRequestID\n\n"
                    "DESCRIPTION\n"
                    "  Use Response_Recovery to obtain response data from previous calls that may\n"
                    "  have failed.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -f    Previously failed requestId for which you wish to recover\n"
                    "          response data\n");
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

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
        }

    if (!image || !failedRequestID) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smResponse_Recovery(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, failedRequestID, &output);

    if (rc) {
        printAndLogSmapiCallReturnCode("Response_Recovery", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Response_Recovery", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("Response Data for %s: %s", image, output->responseData->vmapiString);
    }
    return rc;
}
