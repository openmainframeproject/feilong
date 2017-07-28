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
#include "smcliMetadata.h"
#include "wrapperutils.h"

int metadataDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "MetadataDelete";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "-T:k:h?";
    char * keywords = 0;
    vmApiMetadataDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

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
                    "  Metadata_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Metadata_Delete [-T] image_name\n"
                    "    [-k] 'metadata_name1 metadata_name2 ...'\n\n"
                    "DESCRIPTION\n"
                    "  Use Metadata_Delete to delete metadata values associated with\n"
                    "  a textual identifier (typically a directory entry name)..\n"
                    "  The following options are required:\n"
                    "    -T    A textual identifier (typically a directory entry name).\n"
                    "    -k    A blank-delimited list of metadata names. \n"
                    "          Note that these metadata names are case sensitive.\n");
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

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting metadata values associated with %s... ", image);

    rc = smMetadataDelete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, keywords, &output);

    if (rc) {
        printAndLogProcessingErrors("MetadataDelete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("MetadataDelete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int metadataGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "MetadataGet";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "-T:k:h?";
    char * keywords = NULL;
    vmApiMetadataGetOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

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
                    "  Metadata_Get\n\n"
                    "SYNOPSIS\n"
                    "  smcli Metadata_Get [-T] image_name\n"
                    "    [-k] 'metadata1 metadata2 ...'\n\n"
                    "DESCRIPTION\n"
                    "  Use Metadata_Get to obtain metadata values associated with a\n"
                    "  textual identifier (typically a directory entry name).\n"
                    "  The following options are required:\n"
                    "    -T    A textual identifier (typically a directory entry name).\n"
                    "    -k    A quoted blank-delimited list of metadata names.\n"
                    "          Note that these metadata names are case sensitive.\n");
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

    rc = smMetadataGet(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, keywords, &output);

    if (rc) {
        printAndLogProcessingErrors("MetadataGet", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("MetadataGet", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int i;
        int entryCount = output->metadataEntryCount;
        if (entryCount > 0) {
            // Loop through metadata entries and print out metadata entry
            for (i = 0; i < entryCount; i++) {
                if ((output->metadataEntryList[i].metadataEntryName != NULL) &&
                    (output->metadataEntryList[i].metadata != NULL)) {
                   printf("%s:%s\n", output->metadataEntryList[i].metadataEntryName,
                                     output->metadataEntryList[i].metadata);
                }
            }
        }
    }
    return rc;
}

int metadataSet(int argC, char* argV[],
        struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "MetadataSet";
    int rc;
    int i;
    int option;
    int entryCount = 0;
    int metadataStructureLength = 0;
    char * token;
    char * buffer;
    char * targetIdentifier = NULL;
    char ** entryArray;
    int argBytes = 0;

    vmApiMetadataSetOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    const char * optString = "-T:k:h?";

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }

    optind = 1;  // Reset optind so getopt can rescan arguments

    if (argBytes > 0) {
        if (0 == (entryArray = malloc(argBytes)))
            return MEMORY_ERROR;
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
            	targetIdentifier = optarg;
                break;

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Metadata_Set\n\n"
                    "SYNOPSIS\n"
                    "  smcli Metadata_Set [-T] image_name\n"
                    "    [-k] 'metadata1 metadata2 ...'\n\n"
                    "DESCRIPTION\n"
                    "  Use Metadata_Set to set metadata values associated with a\n"
                    "  textual identifier (typically a directory entry name).\n"
                    "  The following options are required:\n"
                    "    -T    A textual identifier (typically a directory entry name).\n"
                    "    -k     One or more quoted metadata_name=metadata item to be created\n"
                    "           The keyword is a unique value for this identifier\n"
                    "          Note that these metadata_names are case sensitive.\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
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

    if (!targetIdentifier || !entryCount) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    char *nameArray[entryCount];
    char *dataArray[entryCount];
    for (i = 0; i < entryCount; i ++) {
        token = strtok_r(entryArray[i], "=", &buffer);
        if (token != NULL) {
            nameArray[i] = token;
        } else {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: metadata_entry_name is NULL\n");
            FREE_MEMORY_CLEAR_POINTER(entryArray);
            return 1;
        }
        token = strtok_r(NULL, "\0", &buffer);
        if (token != NULL) {
            dataArray[i] = token;
        } else {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: metadata is NULL\n");
            FREE_MEMORY_CLEAR_POINTER(entryArray);
            return 1;
        }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Setting metadata values associated with %s... ", targetIdentifier);

    rc = smMetadataSet(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
    		targetIdentifier, entryCount, nameArray, dataArray, &output);
    FREE_MEMORY_CLEAR_POINTER(entryArray);

    if (rc) {
        printAndLogProcessingErrors("MetadataSet", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("MetadataSet", output->common.returnCode,
               output->common.reasonCode, vmapiContextP, strMsg);
    };
    return rc;
}

int metadataSpaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "MetadataSpaceQuery";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "-T:k:h?";
    char * keywords = NULL;
    vmApiMetadataSpaceQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

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
                    "  Metadata_Space_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Metadata_Space_Query [-T] image_name\n"
                    "    [-k] 'searchkey=<pattern>'\n\n"
                    "DESCRIPTION\n"
                    "  Use Metadata_Space_Qyery to obtain metadata values associated with a\n"
                    "  textual identifier (typically a directory entry name).\n"
                    "  The following options are required:\n"
                    "    -T    A textual identifier (typically a directory entry name).\n"
                    "    -k    One quoted searchkey=<pattern> search term to select the metadata items to be displayed\n"
                    "          The search pattern may include a trailing ""*"" to broaden the scope of the search   \n");
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

    rc = smMetadataSpaceQuery(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, keywords, &output);

    if (rc) {
        printAndLogProcessingErrors("MetadataSpaceQuery", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("MetadataSpaceQuery", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int i;
        int entryCount = output->metadataEntryCount;
        if (entryCount > 0) {
            // Loop through metadata entries and print out metadata entry
            for (i = 0; i < entryCount; i++) {
                printf("%s\n", output->metadataEntryList[i].vmapiString);
            }
        }
    }
    return rc;
}

