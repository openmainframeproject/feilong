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
#include "smcliDirectory.h"
#include "wrapperutils.h"

int directoryManagerLocalTagDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Local_Tag_Define_DM";
    int rc;
    int option;
    int tagOrdinal = 0;
    int action = 0;
    char * image = NULL;
    char * tagName = NULL;
    vmApiDirectoryManagerLocalTagDefineDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tnoa";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:a:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                tagName = optarg;
                break;

            case 'o':
                tagOrdinal = atoi(optarg);
                break;

            case 'a':
                action = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Local_Tag_Define_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Local_Tag_Define_DM [-T] image_name\n"
                    "  [-t] tag_name [-o] tag_ordinal [-a] action\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Local_Tag_Define_DM to define a local tag or named\n"
                    "  comment record to contain installation-specific information about a virtual\n"
                    "  image.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -n    The name of the local tag or named comment to be defined\n"
                    "    -o    The value of the tag sort ordinal, relative to other defined\n"
                    "          local tags\n"
                    "    -a    Specifies creation of a new tag or change of a tag ordinal value:\n"
                    "            1: Create a new tag\n"
                    "            2: Change an existing tag's ordinal value\n");
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


    if (!image || !tagName || !tagOrdinal || !action) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining a local tag or named comment record %s... ", tagName);

    rc = smDirectory_Manager_Local_Tag_Define_DM(vmapiContextP, "", 0, strMsg,  // Authorizing user, password length, password.
             image, tagName, tagOrdinal, action, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Local_Tag_Define_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Local_Tag_Define_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    }
    return rc;
}

int directoryManagerLocalTagDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Local_Tag_Delete_DM";
    int rc;
    int option;
    char * image = NULL;
    char * tagName = NULL;
    vmApiDirectoryManagerLocalTagDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tn";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                tagName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Local_Tag_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Local_Tag_Delete_DM [-T] image_name [-n] tag_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Local_Tag_Delete_DM to remove a local tag or\n"
                    "  named comment record from the directory manager's internal tables.\n"
                    "  Users will no longer be able to set or query the tag.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that\n"
                    "          also contains the authenticated_userid and the function_name\n"
                    "    -n    Specifies the name of the tag to be deleted\n");
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

    if (!image || !tagName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing a local tag or named comment record %s... ", tagName);

    rc = smDirectory_Manager_Local_Tag_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
             image, tagName, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Local_Tag_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Local_Tag_Delete_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int directoryManagerLocalTagQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Local_Tag_Query_DM";
    int rc;
    int option;
    char * image = NULL;
    char * tagName = NULL;
    vmApiDirectoryManagerLocalTagQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tn";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                tagName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Local_Tag_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Local_Tag_Query_DM [-T] image_name [n] tag_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Local_Tag_Query_DM to obtain the value of a\n"
                    "  virtual image's local tag or named comment record.\n\n"
                    "  The following options are required:\n"
                    "    -T    The target userid whose tag is being queried\n"
                    "    -n    The name of the local tag or named comment to be queried\n");
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

    if (!image || !tagName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smDirectory_Manager_Local_Tag_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
             image, tagName, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Local_Tag_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Local_Tag_Query_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    }  else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print value of the associated tag
        printf("%s\n", output->tagValue);
    }
    return rc;
}

int directoryManagerLocalTagSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Local_Tag_Set_DM";
    int rc;
    int option;
    char * image = NULL;
    char * tagName = NULL;
    char * tagValue = NULL;
    vmApiDirectoryManagerLocalTagSetDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tnv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                tagName = optarg;
                break;

            case 'v':
                tagValue = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Local_Tag_Set_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Local_Tag_Set_DM [-T] image_name\n"
                    "  [-n] tag_name [-v] tag_value\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Local_Tag_Set_DM to set the value of a virtual\n"
                    "  image's local tag or named comment record.\n\n"
                    "  The following options are required:\n"
                    "    -T    The target userid whose tag is being set\n"
                    "    -n    The name of the local tag or named comment to be set\n"
                    "    -v    The value of a virtual image's local tag or named comment\n"
                    "          to be set\n");
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


    if (!image || !tagName || !tagValue) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Setting the value of a virtual image's local tag or named comment record %s... ", tagName);

    rc = smDirectory_Manager_Local_Tag_Set_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
             image, tagName, strlen(tagValue), tagValue, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Local_Tag_Set_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Local_Tag_Set_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int directoryManagerSearchDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Search_DM";
    int rc;
    int option;
    int i;
    int j;
    int recCount;
    int statementLength;
    char targetId[8 + 1];
    char statement[72 + 1];
    char * image = NULL;
    char * searchPattern = NULL;
    vmApiDirectoryManagerSearchDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ts";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                searchPattern = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Search_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Search_DM [-T] image_name [-s] search_pattern\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Search_DM to search the directory for records that\n"
                    "  match the specified pattern.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -s    The records to be searched for. Tokens must be separated by blanks\n");
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

    if (!image || !searchPattern) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smDirectory_Manager_Search_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
             image, strlen(searchPattern), searchPattern, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Search_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Search_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out image names
        recCount = output->statementCount;
        if (recCount > 0) {
            // Loop through the records and print it out
            for (i = 0; i < recCount; i++) {
                printf("%s: ", output->statementList[i].targetId);
                for (j = 0; j < output->statementList[i].statementLength; j++){
                    encode_print(output->statementList[i].statement[j]);
                }
                printf("\n");
            }
        }
    }
    return rc;
}

int directoryManagerTaskCancelDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Directory_Manager_Task_Cancel_DM";
    int rc;
    int option;
    int opId = 0;
    char * image = NULL;
    vmApiDirectoryManagerTaskCancelDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ti";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:i:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'i':
               opId = atoi(optarg);
               break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Directory_Manager_Task_Cancel_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Directory_Manager_Task_Cancel_DM [-T] image_name\n"
                    "  [-i] operation_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Directory_Manager_Task_Cancel_DM to cancel a specific asynchronous\n"
                    "  task being performed by the directory manager.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -i    The identifier of the task\n");
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


    if (!image || !opId) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Canceling asynchronous task %d... ", opId);

    rc = smDirectory_Manager_Task_Cancel_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, opId, &output);

    if (rc) {
        printAndLogProcessingErrors("Directory_Manager_Task_Cancel_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Directory_Manager_Task_Cancel_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}
