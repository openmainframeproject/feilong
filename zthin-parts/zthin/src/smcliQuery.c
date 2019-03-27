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
#include "smcliQuery.h"
#include "wrapperutils.h"

int queryABENDDump(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Query_ABEND_Dump";
    int rc;
    int i;
    int entryCount = 0;
    int option;
    char abend_dump_loc[75];
    char * targetIdentifier = NULL;
    char * entryArray[1];
    vmApiQueryAbendDumpOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:k:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'k':
                if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    return INVALID_DATA;
                }
                if (entryCount < 1) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Query_ABEND_Dump\n\n"
                    "SYNOPSIS\n"
                    "  smcli Query_ABEND_Dump [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Query_ABEND_Dump to display the current ABEND dumps that appear in the\n"
                    "  OPERATNS userid's reader or have already been processed to the dump processing\n"
                    "  location specified in the DMSSICNF COPY file.\n\n"
                    "  The following options are required:\n"
                    "    -T  This must match an entry in the authorization file\n"
                    "    -k  A keyword=value item location set to the where to query.\n"
                    "        It must be inside single quotes. For example -k 'key=value'\n. "
                    "        Possible keywords are:\n"
                    "          Location\n"
                    "          RDR: Query ABEND dumps in the reader (unprocessed).\n"
                    "          SFS: Query ABEND dumps in the VMSYSU:OPERATNS. SFS directory (processed).\n"
                    "          ALL: Query ABEND dumps both in the reader and the SFS directory.\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smQuery_ABEND_Dump(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Query_ABEND_Dump", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_ABEND_Dump", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        for (i = 0; i < output->dumpStrCount; i++) {
            if (output->abendDumpStructure[i].abend_dump_loc == 1) {
                strcpy(abend_dump_loc, "Reader (unprocessed)");
            } else if (output->abendDumpStructure[i].abend_dump_loc == 2) {
                strcpy(abend_dump_loc, "SFS directory (processed)");
            } else {
                strcpy(abend_dump_loc, "Error Invalid data received!! ");
                return 1;
            }
            printf("abend_dump_loc: %s\n",  abend_dump_loc);
            printf("abend_dump_id: %s\n",   output->abendDumpStructure[i].abend_dump_id);
            printf("abend_dump_date: %s\n", output->abendDumpStructure[i].abend_dump_date);
            printf("abend_dump_dist: %s\n", output->abendDumpStructure[i].abend_dump_dist);
        }
    }
    return rc;
}

int queryAllDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Query_All_DM";
    int rc;
    int i;
    int j;
    int k;
    int recCount;
    int recLen;
    int entryCount = 0;
    int option;
    int isLineNum;
    char format[10+1] = "";
    char line[80];
    char * targetIdentifier = NULL;
    char * entryArray[1];
    int bytesUsed;
    int entryLength;
    char * stringStart;
    vmApiQueryAllDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:k:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'k':
                if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    return INVALID_DATA;
                }
                if (entryCount < 1) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf("ERROR: Too many -k values entered\n");
                    return INVALID_DATA;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Query_All_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Query_All_DM [-T] targetIdentifier  [-k] entry\n\n"
                    "DESCRIPTION\n"
                    "  Use Query_All_DM to obtain the contents of the entire system directory.\n\n"
                    "  The following options are required:\n"
                    "    -T  This must match an entry in the authorization file\n"
                    "    -k  A keyword=value item location set to the where to query.\n"
                    "        It must be inside single quotes. For example -k 'key=value'.\n"
                    "         Possible settings are:\n"
                    "            FORMAT=YES  Output data formatted.\n"
                    "            FORMAT=NO   Output data unformatted..\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }
    // Fill the var format with the input for FORMAT
    // Convert the input to upper case for the strcmp test
    memset(format, 0, 11);
    for (i=0; i < strlen(entryArray[0]); i++) {
        format[i] = toupper(entryArray[0][i]);
    }

    if (strcmp(format, "FORMAT=YES") == 0) {
        // Format = YES
        rc = smQuery_All_DM_YES(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

        if (rc) {
            printAndLogProcessingErrors("Query_All_DM", rc, vmapiContextP, "", 0);
        } else if (output->common.returnCode || output->common.reasonCode) {
            // Handle SMAPI return code and reason code
            rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_All_DM", output->common.returnCode,
                    output->common.reasonCode, vmapiContextP, "");
        } else {
            DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
            for (i = 0; i < output->directoryEntriesArrayCount; i++) {
                printf("Directory Entry_type: %d\n", output->directoryEntryArray[i].directoryEntryType);
                printf("Directory Entry ID: %s\n", output->directoryEntryArray[i].directoryEntryId);
                // Print out directory entry strings
                bytesUsed = 0;
                stringStart = output->directoryEntryArray[i].directoryEntryData;
                entryLength = output->directoryEntryArray[i].directoryEntryDataLength;
                while (bytesUsed < entryLength) {
                    j = strlen(stringStart)+1;
                    printf("%s\n", stringStart);
                    stringStart += j;
                    bytesUsed += j;
                }
                printf("\n");
            }
        }
    } else {
        // Format = NO
        rc = smQuery_All_DM_NO(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

        if (rc) {
            printAndLogProcessingErrors("Query_All_DM", rc, vmapiContextP, "", 0);
        } else if (output->common.returnCode || output->common.reasonCode) {
            // Handle SMAPI return code and reason code
            rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_All_DM", output->common.returnCode,
                    output->common.reasonCode, vmapiContextP, "");
        } else {
            DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
            for (i = 0; i < output->directoryEntriesArrayCount; i++) {
                printf("Directory Entry_type: %d\n", output->directoryEntryArray[i].directoryEntryType);
                printf("Directory Entry ID: %s\n", output->directoryEntryArray[i].directoryEntryId);
                // Print out directory entry
                recCount = output->directoryEntryArray[i].directoryEntryArrayCount;
                for (j = 0; j < recCount; j++ ) {
                    recLen = output->directoryEntryArray[i].directoryEntryRecordArray[j].directoryEntryRecordLength;
                    // Remove line number if present
                    if (recLen == 80) {
                        isLineNum = 1;
                        for (k = 72; k < 80; k++) {
                            if (!isdigit(output->directoryEntryArray[i].directoryEntryRecordArray[j].directoryEntryRecord[k])) {
                                isLineNum = 0;
                                break;
                            }
                        }
                        if (isLineNum) {
                            recLen = 72;
                        }
                    }
                    memset(line, 0x20, 80);
                    strncpy(line, output->directoryEntryArray[i].directoryEntryRecordArray[j].directoryEntryRecord, recLen);
                    trim(line);
                    printf("%s\n", line);
                }
                printf("\n");
            }
        }
    }
    return rc;
}

int queryAPIFunctionalLevel(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Query_API_Functional_Level";
    int rc;
    int option;
    char * image = NULL;
    vmApiQueryApiFunctionalLevelOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Query_API_Functional_Level\n\n"
                    "SYNOPSIS\n"
                    "  smcli Query_API_Functional_Level [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Query_API_Functional_Level to obtain the support level of the server\n"
                    "  and functions, as follows:\n"
                    "    For z/VM V5.3, this API will provide a return and reason code of 0/0\n"
                    "    For z/VM V5.4, this API will provide a return and reason code of 0/540\n"
                    "    For z/VM V6.1, this API will provide a return and reason code of 0/610\n"
                    "    For the updated z/VM V6.1 SPE release, this API will provide a return\n"
                    "    and reason code of 0/611.\n"
                    "    For z/VM V6.2, this API will provide a return and reason code of 0/620.\n"
                    "    For z/VM V6.3, this API will provide a return and reason code of 0/630.\n"
                    "    For z/VM V6.4, this API will provide a return and reason code of 0/640.\n\n"
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

    rc = smQuery_API_Functional_Level(vmapiContextP, "", 0, "", image, &output);

    if (rc) {
        printAndLogProcessingErrors("Query_API_Functional_Level", rc, vmapiContextP, "", 0);
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 0)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V5.3\n");
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 540)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V5.4\n");
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 610)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V6.1\n");
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 611 || output->common.reasonCode == 612)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is the updated z/VM V6.1 SPE release\n");
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 620 || output->common.reasonCode == 621)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V6.2\n");
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 630 || output->common.reasonCode == 631 || output->common.reasonCode == 632)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V6.3\n");
    } else if ((output->common.returnCode == 0) && ((output->common.reasonCode >= 640 || output->common.reasonCode < 650))) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode) \
        printf("The API functional level is z/VM V6.4\n");
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_API_Functional_Level", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }
    return rc;
}

int queryAsynchronousOperationDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_SCSI_Disk_Query";
    int rc;
    int option;
    int operationId = -1;
    char * image = NULL;
    vmApiQueryAsynchronousOperationDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ti";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:i:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'i':
                operationId = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Query_Asynchronous_Operation_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Query_Asynchronous_Operation_DM [-T] image_name [-i] operation_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Query_Asynchronous_Operation_DM to query the status of an asynchronous\n"
                    "  directory manager operation.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -i    The identifier of the operation to be queried\n");
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

    if (!image || (operationId < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smQuery_Asychronous_Operation_DM(vmapiContextP, "", 0, "", image, operationId, &output);

    if (rc) {
        printAndLogProcessingErrors("System_SCSI_Disk_Query", rc, vmapiContextP, "", 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_Asychronous_Operation_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }
    return rc;
}

int queryDirectoryManagerLevelDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Query_Directory_Manager_Level_DM";
    int rc;
    int option;
    char * image = NULL;
    vmApiQueryDirectoryManagerLevelDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Query_Directory_Manager_Level_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Query_Directory_Manager_Level_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Query_Directory_Manager_Level_DM to query the directory manager\n"
                    "  that is being used and its functional level.\n\n"
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

    rc = smQuery_Directory_Manager_Level_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Query_Directory_Manager_Level_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_Directory_Manager_Level_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("%s\n", output->directoryManagerLevel);
    }
    return rc;
}
