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
#include "smcliName.h"
#include "wrapperutils.h"

int nameListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Name_List_Add";
    int rc;
    int option;
    char * nameList = NULL;
    char * name = NULL;
    vmApiNameListAddOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tn";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:h?")) != -1)
        switch (option) {
            case 'T':
                nameList = optarg;
                break;

            case 'n':
                name = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Name_List_Add\n\n"
                    "SYNOPSIS\n"
                    "  smcli Name_List_Add [-T] name_list [-n] name\n\n"
                    "DESCRIPTION\n"
                    "  Use Name_List_Add to add a name to a list in the name list file.\n"
                    "  If the list that is specified in target_identifier does not exist,\n"
                    "  a new list will be created.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the list that is being updated\n"
                    "    -n    The name to be added to the list specified\n");
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

    if (!nameList || !name) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding %s to %s... ", name, nameList);

    rc = smName_List_Add(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            nameList, name, &output);

    if (rc) {
        printAndLogProcessingErrors("Name_List_Add", rc, vmapiContextP, strMsg, 0);
    } else if ( (output->common.returnCode == 0) && (output->common.reasonCode == 12) ) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode);
        printf("%s", strMsg);
        // Handle the special case where the first Name is added and thus a new Name List is created
        printf("Done. New list created. \n");
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Name_List_Add", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int nameListDestroy(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Name_List_Destroy";
    int rc;
    int option;
    char * nameList = NULL;
    vmApiNameListDestroyOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                nameList = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Name_List_Destroy\n\n"
                    "SYNOPSIS\n"
                    "  smcli Name_List_Destroy [-T] name_list\n\n"
                    "DESCRIPTION\n"
                    "  Use Name_List_Destroy to destroy a list from the name list file.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the list being destroyed\n");
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

    if (!nameList) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Destroying %s... ", nameList);

    rc = smName_List_Destroy(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            nameList, &output);

    if (rc) {
        printAndLogProcessingErrors("Name_List_Destroy", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Name_List_Destroy", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int nameListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Name_List_Query";
    int rc;
    int option;
    int i;
    char * nameList = NULL;
    vmApiNameListQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                nameList = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Name_List_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Name_List_Query [-T] name_list\n\n"
                    "DESCRIPTION\n"
                    "  Use Name_List_Query to query the names that are in a list in the\n"
                    "  name list file.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the list being queried\n");
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

    if (!nameList) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smName_List_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            nameList, &output);

    if (rc) {
        printAndLogProcessingErrors("Name_List_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Name_List_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out the Names in the nameList
        for (i = 0; i < output->nameArrayCount; i++) {
            printf("%s\n", output->nameList[i]);
        }
    }
    return rc;
}

int nameListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Name_List_Remove";
    int rc;
    int option;
    char * nameList = NULL;
    char * name = NULL;
    vmApiNameListRemoveOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tn";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:h?")) != -1)
        switch (option) {
            case 'T':
                nameList = optarg;
                break;

            case 'n':
                name = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Name_List_Remove\n\n"
                    "SYNOPSIS\n"
                    "  smcli Name_List_Remove [-T] name_list [-n] name\n\n"
                    "DESCRIPTION\n"
                    "  Use Name_List_Remove to delete a name from a list in the name list\n"
                    "  file. If there are no names remaining in the list, the list is also\n"
                    "  deleted.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the list that is being updated\n"
                    "    -n    A userid or function name or list\n");
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

    if (!nameList || !name) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting %s from %s... ", name, nameList);

    rc = smName_List_Remove(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
             nameList, name, &output);

    if (rc) {
        printAndLogProcessingErrors("Name_List_Remove", rc, vmapiContextP, strMsg, 0);
    } else if ( (output->common.returnCode == 0) && (output->common.reasonCode == 16) ) {  
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode);
        printf("%s", strMsg);
        // Handle the special case where the last Name is removed and thus the Name List is destroyed
        printf("Done. No more entries, list destroyed. \n");
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Name_List_Remove", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


