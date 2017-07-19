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
#include "smcliPrototype.h"
#include "wrapperutils.h"


int prototypeCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Prototype_Create_DM";
    int rc;
    int recordCount = 0;
    int c;
    int option;
    char * prototype = NULL;
    char * file = NULL;
    FILE * fp = NULL;
    vmApiPrototypeCreateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:f:h?")) != -1)
        switch (option) {
            case 'T':
                prototype = optarg;
                break;

            case 'f':
                file = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Prototype_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Prototype_Create_DM [-T] prototype_name [-f] prototype_file\n\n"
                    "DESCRIPTION\n"
                    "  Use Prototype_Create_DM to create a new virtual image prototype.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being activated\n"
                    "    -f    The new virtual image prototype");
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

    if (!prototype || !file) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Open the user entry file
    fp = fopen(file, "r");
    if (fp != NULL) {
        // Count the number of lines and set the record count to it
        while ((c = fgetc(fp)) != EOF) {
            if (c == '\n') {
                recordCount++;
            }
        }
    } else {
        printAndLogProcessingErrors("Prototype_Create_DM", PROCESSING_ERROR, vmapiContextP, "", 0);
        printf("\nERROR: Failed to open file %s\n", file);
        return 1;
    }
    // Reset position to start of file
    rewind(fp);

    // Create prototype record
    vmApiPrototypeRecordList record[recordCount];
    int i = 0, LINE_SIZE = 72;
    char line[recordCount][LINE_SIZE];
    char * ptr;
    while (fgets(line[i], LINE_SIZE, fp) != NULL) {
        // Replace newline with null terminator
        ptr = strstr(line[i], "\n");
        if (ptr != NULL) {
            strncpy(ptr, "\0", 1);
        }
        record[i].recordNameLength = strlen(line[i]);
        record[i].recordName = line[i];
        i++;
    }

    // Close file
    fclose(fp);

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating new image prototype %s... ", prototype);

    rc = smPrototype_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            prototype, recordCount, (vmApiPrototypeRecordList *) record, &output);

    if (rc) {
        printAndLogProcessingErrors("Prototype_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Prototype_Create_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int prototypeDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Prototype_Delete_DM";
    int rc;
    int option;
    char * prototype = NULL;
    vmApiPrototypeDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                prototype = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Prototype_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Prototype_Delete_DM [-T] prototype_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Prototype_Delete_DM to delete an image prototype.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the prototype to be deleted\n");
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

    if (!prototype) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting image prototype %s... ", prototype);

    rc = smPrototype_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            prototype, &output);

    if (rc) {
        printAndLogProcessingErrors("Prototype_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Prototype_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int prototypeNameQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Prototype_Name_Query_DM";
    int rc;
    int option;
    char * prototype = NULL;
    vmApiPrototypeNameQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                prototype = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Prototype_Name_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Prototype_Name_Query_DM [-T] prototype_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Prototype_Name_Query_DM to obtain a list of names of defined prototypes.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

    if (!prototype) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smPrototype_Name_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            prototype,  // Does not matter what image name is used
            &output);

    if (rc) {
        printAndLogProcessingErrors("Prototype_Name_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Prototype_Name_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out image names
        int i;
        int n = output->nameArrayCount;
        for (i = 0; i < n; i++) {
            printf("%s\n", output->nameList[i]);
        }
    }
    return rc;
}

int prototypeQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Prototype_Query_DM";
    int rc;
    int i;
    int option;
    int recLen;
    int recCount;
    char line[72];
    char * prototype = NULL;
    vmApiPrototypeQueryDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                prototype = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Prototype_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Prototype_Query_DM [-T] prototype_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Prototype_Query_DM to query the characteristics of an image prototype.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the prototype to be queried\n");
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

    if (!prototype) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smPrototype_Query_DM(vmapiContextP, "", 0, "", prototype, &output);

    if (rc) {
        printAndLogProcessingErrors("Prototype_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Prototype_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out directory entry
        recCount = output->recordArrayCount;
        if (recCount > 0) {
            for (i = 0; i < recCount; i++) {
                recLen = output->recordList[i].recordNameLength;
                memset(line, 0, recLen);
                memcpy(line, output->recordList[i].recordName, recLen);
                line[recLen] = '\0';
                printf("%s\n", line);
            }
        }
    }
    return rc;
}

int prototypeReplaceDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Prototype_Replace_DM";
    int rc;
    int option;
    int recordCount = 0;
    int c;
    char * prototype = NULL;
    char * file = NULL;
    FILE * fp = NULL;
    vmApiPrototypeReplaceDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:f:h?")) != -1)
        switch (option) {
            case 'T':
                prototype = optarg;
                break;

            case 'f':
                file = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Prototype_Replace_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Prototype_Replace_DM [-T] prototype_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Prototype_Replace_DM to replace an existing prototype.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being activated\n"
                    "    -f    The new virtual image prototype\n");
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

    if (!prototype || !file) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Open the user entry file
    fp = fopen(file, "r");
    if (fp != NULL) {
        // Count the number of lines and set the record count to it
        while ((c = fgetc(fp)) != EOF) {
            if (c == '\n') {
                recordCount++;
            }
        }
    } else {
        printAndLogProcessingErrors("Prototype_Replace_DM", PROCESSING_ERROR, vmapiContextP, "", 0);
        printf("\nERROR: Failed to open file %s\n", file);
        return 1;
    }
    // Reset position to start of file
    rewind(fp);

    // Create prototype record
    vmApiPrototypeRecordList record[recordCount];
    int i = 0, LINE_SIZE = 72;
    char line[recordCount][LINE_SIZE];
    char * ptr;
    while (fgets(line[i], LINE_SIZE, fp) != NULL) {
        // Replace newline with null terminator
        ptr = strstr(line[i], "\n");
        if (ptr != NULL) {
            strncpy(ptr, "\0", 1);
        }
        record[i].recordNameLength = strlen(line[i]);
        record[i].recordName = line[i];
        i++;
    }

    // Close file
    fclose(fp);

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Replacing image prototype %s... ", prototype);

    rc = smPrototype_Replace_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            prototype, recordCount, (vmApiPrototypeRecordList *) record, &output);

    if (rc) {
        printAndLogProcessingErrors("Prototype_Replace_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Prototype_Replace_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}
