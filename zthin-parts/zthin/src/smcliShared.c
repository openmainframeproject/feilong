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

#include "smcliShared.h"
#include "wrapperutils.h"

int sharedMemoryAccessAddDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Access_Add_DM";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    vmApiSharedMemoryAccessAddDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ts";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Access_Add_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Access_Add_DM [-T] image_name [-s] segment_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Access_Add_DM to add restricted (RSTD) access to a\n"
                    "  shared memory segment.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or list of userids being granted access to the\n"
                    "          memory segment\n"
                    "    -s    The name of the memory segment to which access is being\n"
                    "          granted\n");
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

    if (!image || !segmentName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding restricted access to %s... ", segmentName);

    rc = smShared_Memory_Access_Add_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Access_Add_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Access_Add_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int sharedMemoryAccessQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Access_Query_DM";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    vmApiSharedMemoryAccessQueryDmOutput* output;

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
                segmentName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Access_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Access_Query_DM [-T] image_name [-s] segment_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Access_Query_DM to query the restricted (RSTD) access\n"
                    "  to a shared memory segment.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or list of userids being queried for restricted\n"
                    "          access to the specified segment\n"
                    "    -s    The name of the memory segment being queried\n");
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

    if (!image || !segmentName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smShared_Memory_Access_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Access_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Access_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int i;
        for (i = 0; i < output->memorySegmentNameCount; i++) {
            printf("%s\n", output->memorySegmentNameList[i].memorySegmentName);
        }
    }
    return rc;
}

int sharedMemoryAccessRemoveDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Access_Remove_DM";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    vmApiSharedMemoryAccessRemoveDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ts";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Access_Remove_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Access_Remove_DM [-T] image_name [-s] segment_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Access_Remove_DM to remove restricted (RSTD) access\n"
                    "  from a shared memory segment.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or list of IDs for which access is being removed\n"
                    "    -s    The name of the memory segment to which access is being removed\n");
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

    if (!image || !segmentName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing restricted access from %s... ", segmentName);

    rc = smShared_Memory_Access_Remove_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, &output);


    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Access_Remove_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Access_Remove_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int sharedMemoryCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Create";
    int rc;
    int option;
    int pageAccessType = 0;
    int memoryAttributes = -1;
    long beginPage = 0;
    long endPage = 0;
    char * image = NULL;
    char * segmentName = NULL;
    char * memoryAccessId = "";
    vmApiSharedMemoryCreateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tsbetmi";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:b:e:t:m:i:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'b':
                beginPage = atol(optarg);
                break;

            case 'e':
                endPage = atol(optarg);
                break;

            case 't':
                pageAccessType = atoi(optarg);
                break;

            case 'm':
                memoryAttributes = atoi(optarg);
                break;

            case 'i':
                memoryAccessId = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Create [-T] image_name [-s] segment_name\n"
                    "    [-b] begin_page [-e] end_page [-t] page_type [-m] memory_attributes\n"
                    "    [-i] memory_access_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Create to create a memory segment that can be shared\n"
                    "  among virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid for which memory is being saved in the segment\n"
                    "    -s    The name of the memory segment being created\n"
                    "    -b    The beginning page to be saved\n"
                    "    -e    The ending page to be saved\n"
                    "    -t    The type of page access. Valid values are:\n"
                    "            1: SW ~ Shared read/write access\n"
                    "            2: EW ~ Exclusive read/write access\n"
                    "            3: SR ~ Shared read-only access\n"
                    "            4: ER ~ Exclusive read-only access\n"
                    "            5: SN ~ Shared read/write access, no data saved\n"
                    "            6: EN ~ Exclusive read/write access, no data saved\n"
                    "            7: SC ~ Shared read-only access, no data saved, CP writeable pages\n"
                    "    -m    Memory attributes, valid values are:\n"
                    "            0: Unspecified\n"
                    "            1: RSTD ~ Restricted saved memory\n"
                    "            2: UNRSTD ~ Unrestricted saved memory. This is the default.\n"
                    "  The following options are optional:\n"
                    "    -i    The name of the image or list of images authorized to access the\n"
                    "          RSTD segment.  If specified, it is used only when RSTD is specified\n"
                    "          in the memory_attributes parameter.\n");
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

    if (!image || !segmentName || !beginPage || !endPage || !pageAccessType || (memoryAttributes < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating memory segment %s... ", segmentName);

    rc = smShared_Memory_Create(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, beginPage, endPage, pageAccessType, memoryAttributes, memoryAccessId, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int sharedMemoryDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    vmApiSharedMemoryDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ts";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Delete [-T] image_name [-s] segment_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Delete to delete a shared memory segment\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -s    The name of the memory segment being deleted\n");
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

    if (!image || !segmentName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting memory segment %s... ", segmentName);

    rc = smShared_Memory_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int sharedMemoryQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Query";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    vmApiSharedMemoryQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Ts";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Query [-T] image_name [-s] segment_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Query to query information about system data files that\n"
                    "  are contained in the saved memory segment.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -s    The name of the memory segment being queried\n"
                    "            '*': Specifies all defined memory segments for query\n");
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

    if (!image || !segmentName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smShared_Memory_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
         char * status;
         char * shareAccess;
         int i, j;
         for (i = 0; i < output->memorySegmentCount; i++) {
            if (output->memorySegmentInfoList[i].memorySegmentStatus == 1) {
                status = "Skeleton";
            } else if (output->memorySegmentInfoList[i].memorySegmentStatus == 2) {
                status = "Available and nonrestricted";
            } else if (output->memorySegmentInfoList[i].memorySegmentStatus == 3) {
                status = "Available and restricted";
            } else if (output->memorySegmentInfoList[i].memorySegmentStatus == 4) {
                status = "Pending purge";
            } else {
                status = "Invalid Shared Status received!!";
                rc = 1;
            }
            snprintf(strMsg, sizeof(strMsg),
                     "Memory segment: %s\n"
                     "Status:         %s\n",
                     output->memorySegmentInfoList[i].memorySegmentName, status);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }

            for (j = 0; j < output->memorySegmentInfoList[i].pageRangeCount; j++) {
                if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 1) {
                	shareAccess = "Shared read/write access";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 2) {
                	shareAccess = "Exclusive read/write access";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 3) {
                	shareAccess = "Shared read-only access";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 4) {
                	shareAccess = "Exclusive read-only access";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 5) {
                	shareAccess = "Shared read/write access, no data saved";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 6) {
                	shareAccess = "Exclusive read/write access, no data saved";
                } else if (output->memorySegmentInfoList[i].pageRangeList[j].pageAccessDescriptor == 7) {
                	shareAccess = "Shared read-only access, no data saved, CP writeable pages";
                } else {
                    shareAccess = "Invalid Shared Access received !!";
                    rc = 1;
                }
                snprintf(strMsg, sizeof(strMsg),
                         "Beginning page: %ullX\n"
                         "Ending page:    %ullX\n"
                         "Page access:    %s\n",
                         output->memorySegmentInfoList[i].pageRangeList[j].beginPage,
                         output->memorySegmentInfoList[i].pageRangeList[j].endPage, shareAccess);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            }
        }
         end:
         if (rc) {
             if (rc == OUTPUT_ERRORS_FOUND) {
                 DOES_CALLER_WANT_RC_HEADER_FOR_OUTPUT_ERRORS(vmapiContextP, MY_API_NAME);
             } else {
                 printAndLogProcessingErrors(MY_API_NAME, rc, vmapiContextP, "", 0);
             }
         } else {
             DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
         }
         printMessageBuffersAndRelease(&saveMsgs);
    }
    return rc;
}

int sharedMemoryReplace(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Shared_Memory_Replace";
    int rc;
    int option;
    char * image = NULL;
    char * segmentName = NULL;
    char * memoryAccessId = NULL;
    vmApiSharedMemoryReplaceOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tsi";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:s:i:h?")) != -1)
        switch (option) {
           case 'T':
                image = optarg;
                break;

            case 's':
                segmentName = optarg;
                break;

            case 'i':
                memoryAccessId = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Shared_Memory_Replace\n\n"
                    "SYNOPSIS\n"
                    "  smcli Shared_Memory_Replace [-T] image_name [-s] segment_name\n"
                    "  [-i] memory_access_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Shared_Memory_Replace to replace a shared memory segment\n"
                    "  previously defined by Shared_Memory_Create.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid for whom the memory is being replaced\n"
                    "    -s    The name of the memory segment being replaced\n"
                    "    -i    The image name or the name of a list of new users who\n"
                    "          have access to the RSTD memory segment\n");
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

    if (!image || !segmentName || !memoryAccessId) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Replacing memory segment %s... ", segmentName);

    rc = smShared_Memory_Replace(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, segmentName, memoryAccessId, &output);

    if (rc) {
        printAndLogProcessingErrors("Shared_Memory_Replace", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Shared_Memory_Replace_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


