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


#include "smcliUnDocumented.h"
#include "wrapperutils.h"


int imageIPLDeviceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_IPL_Device_Query";
    int rc = 0;
    int option;
    char * userid = NULL;
    vmApiImageIplDeviceQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tc";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:h?")) != -1)
        switch (option) {
            case 'T':
                userid = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_IPL_Device_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_IPL_Device_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_IPL_Device_Query to what device the userid was IPL'ed on\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid to query\n");
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

    if (!userid) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_IPL_Device_Query(vmapiContextP, userid, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_IPL_Device_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_IPL_Device_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("UserId %s was IPL'ed from device %s\n", userid, output->iplDevice);
    }
    return rc;
}

int imagePerformanceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Status_Query";
    int rc;
    int option;
    int count = 0;
    int arrayOfVirtualServerIdsSize;
    int i = 0;
    int returnCode = 0;
    int reasonCode = 0;
    int ret0reas0 = 0;
    int ret4reas4 = 0;
    int ret900reas12 = 0;
    char * image = NULL;
    char *token = NULL;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    char * blank = " ";
    char tempUserId[9];
    char userid[9] = "";
    vmApiImageStatusQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tc";
    char tempStr[1];
    char strMsg[250];

    vmApiImagePerformanceQueryOutput* output2;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;
            case 'c':
                count = atoi(optarg);
                break;
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Performance_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Performance_Query [-T] virtualServerNameArray \n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Performance_Query to get performance data for a active virtual\n"
                    "  server.\n\n"
                    "  The following options are required:\n"
                    "    -T    An array of names of one or more virtual servers. Names must be\n"
                    "          separated by blanks.\n"
                    "          An '*' may be used to query all the active virtual Servers. You must\n"
                    "          enter it as '*'\n"
                    "    -c    The number of virtual servers in the array of names of virtual\n"
                    "          servers. This is a required input so if you enter '*' for the names\n"
                    "          you must enter in a number.\n");
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

    if (!image || count == 0) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    /**
     * Need to set the arrayOfVirtualServerIdsSize. Check the count. If there is
     * one, then parse the image to see if it contains the get all virtual
     * servers character (*). If it does, make the SMAPI call Image_Status_Query,
     * it gets all the active virtual servers. Set the arrayOfVirtualServerIdsSize
     * to the count of the active virtual servers. Otherwise, set the
     * arrayOfVirtualServerIdsSize to count.
     */
    if (count == 1) {
        // Obtain virtual server Id
        token = strtok_r(image, blank, &buffer);
        if (token != NULL) {
            strcpy(tempUserId, token);
            // Check for '*'
            if (strcmp(tempUserId, "*") == 0) {
                // Call Image_Status_Query with the "*" to get the array of active virtual servers
                rc = smImage_Status_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
                        "*", &output);

                if (rc) {
                    printAndLogProcessingErrors("Image_Status_Query", rc, vmapiContextP, "", 0);
                } else if (output->common.returnCode || output->common.reasonCode) {
                    // Handle SMAPI return code and reason code
                    rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Status_Query", output->common.returnCode,
                            output->common.reasonCode, vmapiContextP, "");
                } else {
                    if (output->imageNameCount == 0) {
                        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                        printf("There are no active Virtual Servers get performance data for\n");
                        return 1;
                    }
                }
                arrayOfVirtualServerIdsSize = output->imageNameCount;
            } else {
                arrayOfVirtualServerIdsSize = 1;
            }
        }
    } else if (count > 1) {
        arrayOfVirtualServerIdsSize = count;
    } else {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("The count of virtual servers must be greater then 0");
        return -1;
    }

    vmApiCStringInfo virtualServerIds[arrayOfVirtualServerIdsSize];
    char arrayOfuserids[arrayOfVirtualServerIdsSize][9];
    /**
     * Now fill the tempUserId array with all the active virtual servers
     * or the passed in virtual server Ids. This is used so that each Id
     * will be null terminated.
     */
    if ((count == 1) && (strcmp(tempUserId, "*") != 0)) {
        strcpy(arrayOfuserids[0], token);
    } else {
        // Obtain all the passed in virtualServerIds in image
        token = strtok_r(image, blank, &buffer);
        if (token != NULL) {
            strcpy(arrayOfuserids[0], token);
        }

        for (i = 1; i < arrayOfVirtualServerIdsSize; i ++) {
            // Obtain virtualServerId
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(arrayOfuserids[i], token);
            }
        }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Number of virtual server IDs: %d \n", arrayOfVirtualServerIdsSize);

    if ((count == 1) && (strcmp(tempUserId, "*") == 0)) {
        if (output->imageNameCount >0) {
            // Fill in the virtualServerIds with the array of active VirtualServerId
            for (i = 0; i < arrayOfVirtualServerIdsSize; i++) {
                virtualServerIds[i].vmapiString = output->imageNameList[i].imageName;
            }
        }
    } else {
        for (i = 0; i < arrayOfVirtualServerIdsSize; i++) {
            // Now fill the virtualServerIds with the arrayOfuserids
            virtualServerIds[i].vmapiString = arrayOfuserids[i];
        }
    }

    rc = smImage_Performance_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            "MAINT", arrayOfVirtualServerIdsSize, virtualServerIds, &output2);


    if (rc) {
        printAndLogProcessingErrors("Image_Performance_Query", rc, vmapiContextP, strMsg, 0);
    }
    returnCode = output2->common.returnCode;
    reasonCode = output2->common.reasonCode;
    ret0reas0 = (returnCode == 0) && (reasonCode == 0);
    ret4reas4 = (returnCode == 4) && (reasonCode == 4);
    ret900reas12 = (returnCode == 900) && (reasonCode == 12);

    if (ret900reas12) {
        printAndLogProcessingErrors("Profile_Create_DM", PROCESSING_ERROR, vmapiContextP, strMsg, 0);
        printf("Image_Performance_Query() is not supported for this level of zVM\n");
    } else if (!(ret0reas0 || ret4reas4)) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Performance_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);

    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        for (i =0; i < output2->performanceRecordCount; i++) {
            printf("Virtual server ID: %s\n", virtualServerIds[i].vmapiString);
            printf("Record version: \"%u\"\n", output2->performanceRecords[i].recordVersion);
            printf("Guest flags: \"%u\"\n", output2->performanceRecords[i].guestFlags);
            printf("Used CPU time: \"%llu uS\"\n", output2->performanceRecords[i].usedCPUTime);
            printf("Elapsed time: \"%llu uS\"\n", output2->performanceRecords[i].elapsedTime);
            printf("Minimum memory: \"%llu KB\"\n", output2->performanceRecords[i].minMemory);
            printf("Max memory: \"%llu KB\"\n", output2->performanceRecords[i].maxMemory);
            printf("Shared memory: \"%llu KB\"\n", output2->performanceRecords[i].sharedMemory);
            printf("Used memory: \"%llu KB\"\n", output2->performanceRecords[i].usedMemory);
            printf("Active CPUs in CEC: \"%u\"\n", output2->performanceRecords[i].activeCPUsInCEC);
            printf("Logical CPUs in VM: \"%u\"\n", output2->performanceRecords[i].logicalCPUsInVM);
            printf("Guest CPUs: \"%u\"\n", output2->performanceRecords[i].guestCPUs);
            printf("Minimum CPU count: \"%u\"\n", output2->performanceRecords[i].minCPUCount);
            printf("Max CPU limit: \"%u\"\n", output2->performanceRecords[i].maxCPULimit);
            printf("Processor share: \"%u\"\n", output2->performanceRecords[i].processorShare);
            printf("Samples CPU in use: \"%u\"\n,", output2->performanceRecords[i].samplesCPUInUse);
            printf("Samples CPU delay: \"%u\"\n", output2->performanceRecords[i].samplesCPUDelay);
            printf("Samples page wait: \"%u\"\n", output2->performanceRecords[i].samplesPageWait);
            printf("Samples idle: \"%u\"\n", output2->performanceRecords[i].samplesIdle);
            printf("Samples other: \"%u\"\n", output2->performanceRecords[i].samplesOther);
            printf("Samples total: \"%u\"\n", output2->performanceRecords[i].samplesTotal);
            // Convert the userid to asscii from it's EBCDIC
            convertEBCDICtoASCII(vmapiContextP, output2->performanceRecords[i].guestName, userid);
            printf("Guest name: \"%s\"\n", userid);
            printf("\n");
        }
    }
    return rc;
}

int ipAddrGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "IPaddr_Get";
    int rc;
    int option;
    vmApiIPaddrGetOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  IPaddr_Get\n\n"
                    "SYNOPSIS\n"
                    "  smcli IPaddr_Get\n\n"
                    "DESCRIPTION\n"
                    "  Use IPaddr_Get to obtain the TCP/IP address of the z/VM system that\n"
                    "  the zThin is running on.\n\n"
                    "  There are no options required.\n");
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

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Obtaining the TCP/IP address of the zVM system that the zThin is running on... ");

    rc = smIPaddr_Get(vmapiContextP, &output);

    if (rc) {
        printAndLogProcessingErrors("IPaddr_Get", rc, vmapiContextP, strMsg, 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("IPaddr_Get", output->common.returnCode, output->common.reasonCode,
                vmapiContextP, strMsg);
    } else {
        printf("IP count: %d\nIP Address = %s\n", output->ipCount, output->ipList->vmapiString);
    }
    return rc;
}

int systemInfoQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Info_Query";
    int rc = 0;
    int option;
    vmApiSystemInfoQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Info_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Info_Query\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Info_Query to obtain the z/VM info of the z/VM that the "
                    "  zThin is running on.\n\n"
                    "  There are no options required.\n");
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

    rc = smSystem_Info_Query(vmapiContextP, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Info_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Info_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("The z/VM timezone: %s\n", output->timezone);
        printf("The z/VM time: %s\n", output->time);
        printf("The z/VM version: %s\n", output->vmVersion);
        printf("The z/VM CP Gen time: %s\n", output->cpGenTime);
        printf("The z/VM CP IPL time: %s\n", output->cpIplTime);
        printf("The z/VM real storage size: %s\n", output->realStorageSize);
    }
    return rc;
}

int systemIOQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_IO_Query";
    int rc = 0;
    int i = 0;
    int option;
    char * rDev = NULL;
    vmApiSystemIoQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tc";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:h?")) != -1)
        switch (option) {
            case 'T':
                rDev = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_IO_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_IO_Query [-T] rDev\n\n"
                    "DESCRIPTION\n"
                    "  Use System_IO_Query to query system IO\n\n"
                    "  The following options are required:\n"
                    "    -T    The real device address\n");
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

    if (!rDev) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_IO_Query(vmapiContextP, rDev, &output);

    if (rc) {
        printAndLogProcessingErrors("System_IO_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_IO_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("Real device address %s. CHIPID count: %d \n", rDev, output->chipidCount);
        for (i = 0; i < output->chipidCount; i++) {
            printf("Real device address %s CHIPID list[%d]: %s\n", rDev, i, output->chipidList[i].vmapiString);
        }
    }
    return rc;
}

int systemPerformanceInfoQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Performance_Info_Query";
    int rc;
    int option;
    char * target = "MAINT";
    vmApiSystemPerformanceInfoQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Performance_Info_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Performance_Info_Query\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Performance_Info_Query to obtain the number of CPUs,"
                    "  CPUUtilization, MemoryPagingRate, and ConfiguredMemoryPages "
                    "  of a zVM system.\n\n"
                    "  There are no options required.\n");
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

    rc = smSystem_Performance_Info_Query(vmapiContextP, "", 0, "", target, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Performance_Info_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Performance_Info_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("Performance field count: %d\n", output->performanceFieldCount);
        printf("CPUs: %d\n", atoi(output->performanceInfo[0].vmapiString));
        printf("CPU utilization: %d\n", atoi(output->performanceInfo[1].vmapiString));
        printf("Memory paging rate: %d\n", atoi(output->performanceInfo[2].vmapiString));
        printf("Configured memory pages: %d\n", atoi(output->performanceInfo[3].vmapiString));
    }
    return rc;
}


int virtualNetworkQueryLAN(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Query_LAN";
    int rc;
    int i;
    int option;
    vmApiVirtualNetworkQueryLanOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Query_LAN\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Query_LAN\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Query_LAN to query the lan for the lan count and the\n"
                    "  lanList.\n\n"
                    "  There are no options required.\n");
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

    rc = smVirtual_Network_Query_LAN(vmapiContextP, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Query_LAN", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Query_LAN", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("LAN count: %d\n", output->lanCount);
        for (i = 0; i < output->lanCount; i++) {
            printf("LAN list: %s\n", output->lanList[i].vmapiString);
        }
    }
    return rc;
}

int virtualNetworkQueryOSA(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Query_OSA";
    int rc;
    int option;
    vmApiVirtualNetworkQueryOsaOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Query_OSA\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Query_OSA\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Query_OSA to query the OSA for the count and the list.\n\n"
                    "  There are no options required.\n");
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

    rc = smVirtual_Network_Query_OSA(vmapiContextP, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Query_OSA", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Query_OSA", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }  else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int i;
        printf("OSA count: %d\n", output->osaCount);
        for (i = 0; i < output->osaCount; i++) {
            printf("OSA list: %s\n", output->osaList[i].vmapiString);
        }
    }
    return rc;
}

int virtualNetworkVswitchQueryIUOStats(int argC, char* argV[],
        struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Query_IUO_Stats";
    int rc;
    int i;
    int j;
    int k;

    int entryCount = 0;
    int maxKeyValueArrayCount = 1;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxKeyValueArrayCount];
    vmApiVirtualNetworkVswitchQueryIUOStatsOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    int vswitchCount;
    int uplinkCount;
    int nicCount;
    int vlanCount;

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

                if (entryCount < maxKeyValueArrayCount) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf("ERROR: Too many -k values entered.\n");
                    return INVALID_DATA;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Vswitch_Query_IUO_Stats\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Query_IUO_Stats [-T] targetIdentifier [-k] entry\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Query_IUO_Stats to query a virtual switch's\n"
                    "  byte information statistics.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization, i.e. the authenticated user must have\n"
                    "          authorization to perform this function for this target.\n"
                    "    -k    A keyword=value item to be created in the directory.\n\n"
                    "            switch_name: The name of the virtual switch segment\n\n");
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
    rc = smVirtual_Network_Vswitch_Query_IUO_Stats(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Query_IUO_Stats", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Query_IUO_Stats",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        i = 0;
        // deal with vswitch array
        vswitchCount = atoi(output->stringList[i++].vmapiString);
        printf("vswitch count: %d\n\n", vswitchCount);
        for (j = 0; j < vswitchCount; j++) {
            printf("vswitch number: %d\n", j + 1);
            printf("vswitch name: %s\n", output->stringList[i++].vmapiString);

            // deal with uplink array
            uplinkCount = atoi(output->stringList[i++].vmapiString);
            printf("uplink count: %d\n", uplinkCount);
            for (k = 0; k < uplinkCount; k++) {
                printf("uplink_conn: %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_rx:     %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_rx_dsc: %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_rx_err: %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_tx:     %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_tx_dsc: %s\n", output->stringList[i++].vmapiString);
                printf("uplink_fr_tx_err: %s\n", output->stringList[i++].vmapiString);
                printf("uplink_rx:        %s\n", output->stringList[i++].vmapiString);
                printf("uplink_tx:        %s\n", output->stringList[i++].vmapiString);
            }

            printf("bridge_fr_rx:     %s\n", output->stringList[i++].vmapiString);
            printf("bridge_fr_rx_dsc: %s\n", output->stringList[i++].vmapiString);
            printf("bridge_fr_rx_err: %s\n", output->stringList[i++].vmapiString);
            printf("bridge_fr_tx:     %s\n", output->stringList[i++].vmapiString);
            printf("bridge_fr_tx_dsc: %s\n", output->stringList[i++].vmapiString);
            printf("bridge_fr_tx_err: %s\n", output->stringList[i++].vmapiString);
            printf("bridge_rx:        %s\n", output->stringList[i++].vmapiString);
            printf("bridge_tx:        %s\n", output->stringList[i++].vmapiString);

            // deal with nic array
            nicCount = atoi(output->stringList[i++].vmapiString);
            printf("nic count: %d\n", nicCount);
            for (k = 0; k < nicCount; k++) {
                printf("nic_id: %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_rx:        %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_rx_dsc:    %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_rx_err:    %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_tx:        %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_tx_dsc:    %s\n", output->stringList[i++].vmapiString);
                printf("nic_fr_tx_err:    %s\n", output->stringList[i++].vmapiString);
                printf("nic_rx:           %s\n", output->stringList[i++].vmapiString);
                printf("nic_tx:           %s\n", output->stringList[i++].vmapiString);
            }

            // deal with vlan array
            vlanCount = atoi(output->stringList[i++].vmapiString);
            printf("vlan count: %d\n", vlanCount);
            for (k = 0; k < vlanCount; k++) {
                printf("vlan_id: %s\n", output->stringList[i++].vmapiString);
                printf("vlan_rx:          %s\n", output->stringList[i++].vmapiString);
                printf("vlan_tx:          %s\n", output->stringList[i++].vmapiString);
            }
            printf("\n");
        }

    }
    return rc;
}

int xCATCommandsIUO(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "XCAT_Commands_IUO";
    int rc;
    int option;
    int i=0;
    char * image = NULL;
    char * command = NULL;
    int bytesUsed = 0;
    vmApiXCATCommandsIUOOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tc";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'c':
                command = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  xCAT_Commands_IUO\n\n"
                    "SYNOPSIS\n"
                    "  smcli xCAT_Commands_IUO [-T] image_name [-c] command\n\n"
                    "DESCRIPTION\n"
                    "  Use xCAT_Commands_IUO to execute PURGE, FLASHCOPY, SEND, or \n"
                    "QUERY NIC ALL MACID\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual image\n"
                    "    -c    The quoted string cmd=command with all parameters\n");
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

    if (!image || !command) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Executing PURGE, FLASHCOPY, SEND, etc CP command... ");

    rc = smXCAT_Commands_IUO(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, command, &output);

    if (rc) {
        printAndLogProcessingErrors("XCAT_Commands_IUO", rc, vmapiContextP, strMsg, 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("XCAT_Commands_IUO", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char * stringStart = output->XCATCommandsIUOData;
        // If there is no output then print done
        if (!(output->XCATCommandsIUODataLength)){
        	printf("Done\n");
        	return 0;
        }
        while (bytesUsed < output->XCATCommandsIUODataLength) {
            i = strlen(stringStart) + 1;
            printf("%s\n", stringStart);
            stringStart += i;
            bytesUsed += i;
        }
    }
    return rc;
}
