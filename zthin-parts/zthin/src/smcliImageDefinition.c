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
#include "smcliImageDefinition.h"
#include "wrapperutils.h"

int imageDefinitionAsyncUpdates(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Definition_Async_Updates";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    char ** entryArray;
    const char * optString = "-T:k:h?";
    vmApiImageDefinitionAsyncUpdatesOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Count the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (argBytes > 0) {
        if (0 == (entryArray = malloc(argBytes)))return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Definition_Async_Updates\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Definition_Async_Updates [-T] image_name\n"
                    "    [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Definition_Async_Updates to change the completion notification for\n"
                    "  the following APIs: Image_Definition_Update_DM, Image_Definition_Delete_DM \n"
                    "  Image_Defintion_Create_DM to a particular system.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine you want notifications from.\n"
                    "    -k    A quoted keyword=value 'ENABLED=YES' or 'ENABLED=NO'\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
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
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;
        }

    if (!image || !entryCount) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Changing the completion notification for %s... ", image);

    rc = smImage_Definition_Async_Updates(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Definition_Async_Updates", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Definition_Async_Updates",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}


int imageDefinitionCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Definition_Create_DM";
    //  Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiImageDefinitionCreateDMOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (argBytes > 0) {
        if (0 == (entryArray = malloc(argBytes)))return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Definition_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Definition_Create_DM [-T] image_name\n"
                    "    [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Definition_Create_DM to create a new virtual machine directory entry\n"
                    "  for a particular system. Example: CPU_MAXIMUM=COUNT=3 TYPE=ESA\n"
                    "  Refer to the System Management Application Programming manual for additional\n"
                    "  details.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine being created.\n"
                    "    -k    A quoted keyword=value item to be created in the directory.\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
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
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;
        }

    if (!image || !entryCount) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating a new virtual machine directory entry for %s... ", image);

    rc = smImage_Definition_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Definition_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Image_Definition_Create_DM", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
        if (output->asynchIdLength) {
            printf("Asnych ids:\n%s\n", output->asynchIds);
        }
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}

int imageDefinitionDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Definition_Delete_DM";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiImageDefinitionDeleteDMOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (argBytes > 0) {
        if (0 == (entryArray = malloc(argBytes)))return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Definition_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Definition_Delete_DM [-T] image_name\n"
                    "    [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Definition_Delete_DM to delete a virtual machine directory entry\n"
                    "  for a particular system. Example: CPU_MAXIMUM=COUNT=3 TYPE=ESA\n"
                    "  Refer to the System Management Application Programming manual for additional\n"
                    "  details.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine being modified.\n"
                    "    -k    A quoted keyword=value item to be deleted in the directory.\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
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
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;
        }

    if (!image || !entryCount) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting a new virtual machine directory entry for %s... ", image);

    rc = smImage_Definition_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Definition_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Image_Definition_Delete_DM", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData,  vmapiContextP, strMsg);
        if (output->asynchIdLength) {
            printf("Asnych ids:\n%s\n", output->asynchIds);
        }
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}

int imageDefinitionQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Definition_Query_DM";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "-T:k:h?";
    char * keywords = 0;
    int smapiLevel = 0;
    vmApiImageDefinitionQueryDMOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    rc = getSmapiLevel(vmapiContextP, " ", &smapiLevel);
    if (rc != 0){
        printf("\nERROR: Unable to determine SMAPI level.\n");
        return 1;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                keywords = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Definition_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Definition_Query_DM [-T] image_name\n"
                    "    [-k] 'keyword1 keyword2 ...'\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Definition_Query_DM to extract directory records and parse them\n"
                    "  into keyword=value strings.\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine being queried.\n"
                    "    -k    The quoted blank delimited keyword(s) to be queried.\n"
                    "          definition_query_keyword_parameter_list:\n"
                    "              COMMAND_DEFINE_CPU\n"
                    "              COMMAND_SET_CPUAFFINITY\n"
                    "              COMMAND_SET_SHARE\n");
                if (smapiLevel >= 620){
                    printf("              COMMAND_SET_VCONFIG\n");
                }
                printf("              CONSOLE\n"
                    "              CPU\n"
                    "              CPU_MAXIMUM\n"
                    "              DEDICATE\n"
                    "              INCLUDE\n"
                    "              IPL\n"
                    "              LINK\n"
                    "              MDISK\n"
                    "              NICDEF\n"
                    "              OPTION\n"
                    "              PASSWORD\n"
                    "              PRIVILEGE_CLASSES\n"
                    "              SHARE\n");
                if (smapiLevel >= 620){
                    printf("              SPOOL\n");
                }
                printf("              STORAGE_INITIAL\n"
                    "              STORAGE_MAXIMUM\n");
                if (smapiLevel >= 620){
                    printf("              VMRELOCATE\n");
                }
                printf("              * asterisk, meaning all of the above\n");
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

    if (!image || !keywords) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Definition_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, keywords, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Definition_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Image_Definition_Query_DM", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int bytesUsed = 0;
        char * stringStart = output->directoryInfo;
        while (bytesUsed < output->directoryDataLength) {
            i = strlen(stringStart)+1;
            printf("%s\n", stringStart);
            stringStart += i;
            bytesUsed += i;
        }
    }
    return rc;
}

int imageDefinitionUpdateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Definition_Update_DM";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiImageDefinitionUpdateDMOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (argBytes > 0) {
        if (0 == (entryArray = malloc(argBytes)))return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Definition_Update_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Definition_Update_DM [-T] image_name\n"
                    "    [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Definition_Update_DM to update a virtual machine directory entry\n"
                    "  for a particular system. Example: CPU_MAXIMUM=COUNT=3 TYPE=ESA\n"
                    "  refer to the System Management Application Programming manual for\n"
                    "  additional details.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine being updated.\n"
                    "    -k    A quoted keyword=value item to be updated in the directory.\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                printRCheaderHelp();
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
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
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;
        }

    if (!image || !entryCount) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Updating %s virtual machine directory entry... ", image);

    rc = smImage_Definition_Update_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Definition_Update_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Image_Definition_Update_DM", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
        if (output->asynchIdLength) {
            printf("Asnych ids:\n%s\n", output->asynchIds);
        }
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}
