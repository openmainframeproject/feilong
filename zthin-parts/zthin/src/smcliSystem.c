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
#include "smcliSystem.h"
#include "wrapperutils.h"

int systemConfigSyntaxCheck(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Config_Syntax_Check";
    int rc;
    int maxEntryCount = 5;
    int minNeeded = 0;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemConfigSyntaxCheckOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

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
                if (entryCount < maxEntryCount) {
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
                    "  System_Config_Syntax_Check\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Config_Syntax_Check [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Config_Syntax_Check to check the syntax of a system configuration\n"
                    "  file located on a system parm disk.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name \n"
                    "          (System_Config_Syntax_Check).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            system_config_name: File name of the system configuration file.\n"
                    "                                The default is set by the\n"
                    "                                System_Config_File_Name = statement in the\n"
                    "                                DMSSICNF COPY file.\n\n"
                    "            system_config_type: File type of the system configuration file.\n"
                    "                                The default is set by the\n"
                    "                                System_Config_File_Type = statement in the\n"
                    "                                DMSSICNF COPY file.\n\n"
                    "            parm_disk_owner: Owner of the parm disk. The default is set by\n"
                    "                             the Parm_Disk_Owner = statement in the DMSSICNF\n"
                    "                             COPY file.\n"
                    "            parm_disk_number: Number of the parm disk as defined in the\n"
                    "                              VSMWORK1 directory.The default is set by the\n"
                    "                              Parm_Disk_Number = statement in the \n"
                    "                              DMSSICNF COPY file.\n\n"
                    "            parm_disk_password: Multiwrite password for the parm disk. The\n"
                    "                                default is set by the Parm_Disk_Password = \n"
                    "                                statement in the DMSSICNF COPY file.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Checking the syntax of system configuration... ");

    rc = smSystem_Config_Syntax_Check(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Config_Syntax_Check", rc, vmapiContextP, strMsg, 0);
    } else if ((output->common.returnCode == 8)  && (output->common.reasonCode == 34)) {
        // Handle SMAPI return code and reason code and Error Buffer if it was sent
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("System_Config_Syntax_Check", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Config_Syntax_Check", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int systemDiskAccessibility(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Disk_Accessibility";
    int rc;
    int maxEntryCount = 1;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemDiskAccessibilityOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

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
                if (entryCount < maxEntryCount) {
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
                    "  System_Disk_Accessibility\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Disk_Accessibility [-T] targetIdentifier [-k] 'dev_num=xxxx'\n\n"
                    "DESCRIPTION\n"
                    " Use System_Disk_Accessibility to verify that the specified device is available\n"
                    " to be attached. If RC=0/RS=0 is received, then the device is available.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name\n"
                    "          (System_Disk_Accessibility).\n"
                    "    -k    A keyword=value item to be created in the directory. Possible\n"
                    "          keywords are:\n"
                    "            dev_num: The disk device number. This is a required input\n"
                    "                     parameter. They may be specified in any order.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier || entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Verifying that %s is available to be attached... ", entryArray[0]);

    rc = smSystem_Disk_Accessibility(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Disk_Accessibility", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Disk_Accessibility", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


int systemDiskAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Disk_Add";
    int rc;
    int maxEntryCount = 1;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemDiskAddOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

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
                if (entryCount < maxEntryCount) {
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
                    "  System_Disk_Add\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Disk_Add [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Disk_Add to dynamically add an ECKD disk to a running z/VM system\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to which a disk is being added.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "              dev_num - The disk device number.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding ECKD disk to z/VM system... ");

    rc = smSystem_Disk_Add(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Disk_Add", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Disk_Add", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int systemDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Disk_Query";
    int rc;
    int i;
    int maxEntryCount = 4;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    char *token;
    char *buffer;  // char * whose value is preserved between successive related calls to strtok_r.
    char * blank = " ";
    char * delims = " \0";
    char dev_id[4+1];
    char dev_type[7+1];
    char dev_status[8+1];
    char dev_volser[6+1];
    char dev_size[8+1];
    vmApiSystemDiskQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    struct _smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff);

    int smapiLevel = 0;

    rc = getSmapiLevel(vmapiContextP, " ", &smapiLevel);
    if (rc != 0){
        printf("\nERROR: Unable to determine SMAPI level.\n");
        return 1;
    }

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
                if (entryCount < maxEntryCount +1) {
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
                    "  System_Disk_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Use System_Disk_Query [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2... \n\n"
                    "DESCRIPTION\n"
                    " Use System_Disk_Query to query a real ECKD disk or all real ECKD disks.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_Disk_Query).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            dev_num: The disk device number or ALL.\n");
                if (smapiLevel >= 630) {
                    printf("            disk_size: YES|NO Show the disk size. NO is the default.\n");
                }
                printf("\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_Disk_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Disk_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Disk_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {

        for (i =0; i < output->diskInfoArrayCount; i ++) {
            // Get dev_id
            token = strtok_r(output->diskIinfoStructure[i].vmapiString, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device ID is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_type
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device type is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_status
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_status, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device status is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_volser
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(dev_volser, token);
            } else {
                strcpy(dev_volser, "");
            }

            // Get dev_size if new enough SMAPI
            strcpy(dev_size, "");
            if (smapiLevel >= 630) {
                token = strtok_r(NULL, delims, &buffer);
                if (token != NULL) {
                    strcpy(dev_size, token);
                }
            }
            snprintf(strMsg, sizeof(strMsg),
                   "Device ID: %s\n"
                   "  Device type: %s\n"
                   "  Device status: %s\n"
                   "  Device volume serial number: %s\n", dev_id, dev_type, dev_status, dev_volser);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            if (strlen(dev_size) > 0){
                snprintf(strMsg, sizeof(strMsg), "  Device size: %s\n",dev_size);
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

int systemDiskIOQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Disk_IO_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "T:k:h?";
    char * entryArray[1];
    vmApiSystemDiskIOQueryOutput* output;

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
                if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    return INVALID_DATA;
                }
                if (entryCount > 0) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf("ERROR: Too many -k values entered.\n");
                    return INVALID_DATA;
                }
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Disk_IO_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Disk_IO_Query [-T] image_name\n"
                    "   [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Disk_IO_Query to obtain DASD read and write byte counts for SCSI\n"
                    "  EDEV and ECKD volumes owned by z/VM, and for which the control units have\n"
                    "  information. This information will be obtained from DCSS data that has been\n"
                    "  formatted from CP MONITOR records.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_Disk_IO_Query).\n"
                    "  The following option is optional:\n"
                    "    -k    A quoted string containing a blank-delimited \n"
                    "          'keyword=value'. Refer to the System Management Application\n"
                    "          Programming manual for additional details.\n"
                    "          'RDEV=rdev' - One of the following:\n"
                    "             RDEV=* - Return information for all RDEVs. (This is the default.)\n "
                    "             RDEV=rdev1 rdev2 .. - Return information for rdev1..\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_Disk_IO_Query(vmapiContextP, "", 0, "", // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Disk_IO_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Disk_IO_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int bytesUsed = 0;
        char * stringStart = output->dasdInformationData;
        while (bytesUsed < output->dasdInformationDataLength) {
            i = strlen(stringStart) + 1;
            printf("%s\n", stringStart);
            stringStart += i;
            bytesUsed += i;
        }
    }
    return rc;
}

int systemEQIDQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_EQID_Query";
    int rc;
    int i;
    int maxEntryCount = 2;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    int eqidForIsEQID = 0; // Needed for the parsing of the outPut
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    char *token;
    char *buffer;  // char * whose value is preserved between successive related calls to strtok_r.
    const char * blank = " ";
    char eqid_name[50+1];
    char eqid_rdev[4+1];
    vmApiSystemEQIDQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];

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
                if (entryCount < maxEntryCount +1) {
                    entryArray[entryCount] = optarg;
                    if (strcmp(optarg,"eqid_for=EQID") == 0) {
                       eqidForIsEQID = 1;
                    }
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
                    "  System_EQID_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Use System_EQID_Query [-T] targetIdentifier\n"
                    "   [-k] entry1 [-k] entry2\n\n"
                    "DESCRIPTION\n"
                    "  Use System_EQID_Query to obtain a list of system devices assigned a device\n"
                    "  equivalency ID.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_EQID_Query).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "              eqid_for=value - This is a required parameter.\n"
                    "                One of the following:\n"
                    "                EQID - Returns all RDEVs that have an EQID equal to the value\n"
                    "                       specified by eqid_target=.\n"
                    "                ALL - Returns all RDEVs that have been assigned a user-defined\n"
                    "                      EQID, along with the EQIDs for those RDEVs.\n"
                    "                RDEV - Returns the EQIDs for the RDEVs within the range\n"
                    "                       specified by eqid_target=.\n"
                    "              eqid_target=value - One of the following must be specified if\n"
                    "                                  eqid_for=EQID or eqid_for=RDEV:\n"
                    "                eqid_name - string of 1-8 alphanumeric characters for a\n"
                    "                            user-defined EQID, or a string of 50 alphanumeric\n"
                    "                            characters for a system-generated EQID. Multiple\n"
                    "                            EQID names may be specified, separated by blanks.\n"
                    "                eqid_rdev - A single RDEV, a range of RDEVs, or a series of\n"
                    "                            both. Only RDEVs that have an EQID (either\n"
                    "                            system-generated or user-defined) are returned.\n"
                    "                            RDEVs that do not exist or have no EQID are ignored.\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_EQID_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_EQID_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_EQID_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i = 0; i < output->eqidArrayCount; i ++) {
        	if (eqidForIsEQID == 1) {
        		// if eqid_for=EQID the the structure that comes back is the eqid_name a blank and a
        		// string of maxlength of eqid_rdev each one is blank-delimited, when u get a null
        		// it will be the end of the structure
        		// Get eqid_name
                token = strtok_r(output->eqidInfoStructureArray[i].vmapiString, blank, &buffer);
                if (token != NULL) {
                    strcpy(eqid_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: eqid_name is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Get the string of eqid_rdev
                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    snprintf(strMsg, sizeof(strMsg), "  Eqid Name: %s\n", eqid_name);
                    if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                        goto end;
                    }
                	if (strlen(token) < 5) {
                		// There is only one Rdev in the list
                        strcpy(eqid_rdev, token);
                        snprintf(strMsg, sizeof(strMsg), "  Eqid Rdev: %s\n", eqid_rdev);
                        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                            goto end;
                        }
                	} else {
                		// token contains a list of Rdevs
                        printf("  List of Eqid Rdevs: %s\n", token);
                        snprintf(strMsg, sizeof(strMsg), "  List of Eqid Rdevs: %s\n", token);
                        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                            goto end;
                        }
                	}
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: eqid_rdev is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
        	} else {
                // Get eqid_rdev
                token = strtok_r(output->eqidInfoStructureArray[i].vmapiString, blank, &buffer);
                if (token != NULL) {
                    strcpy(eqid_rdev, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: eqid_rdev is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get eqid_name
                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(eqid_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: eqid_name is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg), "  Eqid Name: %s\n  Eqid Rdev: %s\n", eqid_name, eqid_rdev);
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

int systemFCPFreeQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_FCP_Free_Query";
    int rc;
    int i;
    int maxEntryCount = 1;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    char *token;
    char *buffer;  // char * whose value is preserved between successive related calls to strtok_r.
    char semicolon[1] = ";";
    char fcp_dev[4+1];
    char wwpn[16+1];
    char lun[16+1];
    char uuid[64+1];
    char vendor[8+1];
    char prod[4+1];
    char model[4+1];
    char serial[8+1];
    char code[4+1];
    char blk_size[10+1];
    char diskblks[10+1];
    char lun_size[20+1];
    vmApiSystemFCPFreeQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[1000];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];

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
                if (entryCount < maxEntryCount) {
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
                    "  System_FCP_Free_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_FCP_Free_Query [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    " Use System_FCP_Query to query free FCP disk information.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also\n"
                    "          contains the authenticated_userid and the function_name\n"
                    "          (System_FCP_Free_Query).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            fcp_dev: The FCP device number. This is a required parameter.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_FCP_Free_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_FCP_Free_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_FCP_Free_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i =0; i < output->fcpArrayCount; i ++) {
            // Get fcp_dev
            token = strtok_r(output->fcpStructure[i].vmapiString, semicolon, &buffer);
            if (token != NULL) {
                strcpy(fcp_dev, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: FCP device number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get wwpn
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(wwpn, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: World wide port number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get lun
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(lun, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Logical unit number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get uuid
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(uuid, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Universally unique number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get vendor
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(vendor, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Vendor name is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get prod
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(prod, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Product number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get model
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(model, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Model number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get serial
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(serial, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Serial number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get code
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(code, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device code is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get blk_size
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(blk_size, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Block size is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get diskblks
            token = strtok_r(NULL, semicolon, &buffer);
            if (token != NULL) {
                strcpy(diskblks, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Number of blocks residing on the logical unit is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get lun_size
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(lun_size, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Number of bytes residing on the logical unit is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg),
                   "FCP device number: %s\n"
                   "  World wide port number: %s\n"
                   "  Logical unit number: %s\n"
                   "  Universally unique number in printed hex: %s\n"
                   "  Vendor name: %s\n"
                   "  Product number: %s\n"
                   "  Model number: %s\n"
                   "  Serial number: %s\n"
                   "  Device code: %s\n"
                   "  Block size, in bytes: %s\n"
                   "  Number of blocks residing on the logical unit: %s\n"
                   "  Number of bytes residing on the logical unit: %s\n",
                   fcp_dev, wwpn, lun, uuid, vendor, prod, model, serial, code, blk_size, diskblks, lun_size);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
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

int systemInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Information_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "-T:k:h?";
    vmApiSystemInformationQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    int bytesUsed = 0;
    int entryCount = 0;
    char * entryArray[1];
    char format[10+1] = "";

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
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
                    "  System_Information_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Information_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Information_Query to obtain information about a CP instance\n"
                    "  including time, storage, system level, IPL time, system generation\n"
                    "  time, language, CPU ID, and CPU capability information.\n"
                    "  (Note that some capability information may not be available due to\n"
                    "   hardware dependency. A zero will be returned in this case).\n"
                    "    -k  A keyword=value item location set to the where to query.\n"
                    "        It must be inside single quotes. For example -k 'key=value'.\n"
                    "          Possible settings are:\n"
                    "            FORMAT=YES  PrintOutput data formatted.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // Fill the var format with the input for FORMAT
    // Convert the input to upper case for the strcmp test
    memset(format, 0, 11);
    if (entryCount < 1) {
       strncpy(format,"FORMAT=NO",9);
    }
    else  {
       for (i=0; i < strlen(entryArray[0]); i++) {
           format[i] = toupper(entryArray[0][i]);
       }
    }

    rc = smSystem_Information_Query(vmapiContextP, "", 0, "", // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Information_Query", rc, vmapiContextP, "", 0);
    } else if (rc || output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Information_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        if (strcmp(format, "FORMAT=YES") == 0) {
            char * token;
            char * stringStart = output->systemInformationData;
            while (bytesUsed < output->systemInformationDataLength) {
                i = strlen(stringStart) + 1;
                token = strtok(stringStart, " ");
                while (token) {
                   printf("%s\n", token);
                   token = strtok(NULL, " ");
                }
                stringStart += i;
                bytesUsed += i;
            }
        }
        else
        {
            char * stringStart = output->systemInformationData;
            while (bytesUsed < output->systemInformationDataLength) {
                i = strlen(stringStart) + 1;
                printf("%s\n", stringStart);
                stringStart += i;
                bytesUsed += i;
            }
        }
    }

    return rc;
}

int systemPageUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Page_Utilization_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    const char * optString = "T:h?";
    vmApiSystemPageUtilizationQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    char total_page_pages[8+1] = {0};
    char total_page_pages_in_use[8+1] = {0};
    char total_page_percent_used[3+1] = {0};
    char volid[6+1] = {0};
    char rdev[4+1] = {0};
    char total_pages[8+1] = {0};
    char pages_in_use[8+1] = {0};
    char percent_used[3+1] = {0};
    char drained[10+1] = {0};
    char * blank = " ";
    char * buffer = NULL;
    char * token = NULL;
    char * pageinfo = NULL;
    char tempBuff[130];
    int bytesleft;
    int linesize; 

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Page_Utilization_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Page_Utilization_Query [-T] target_name\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Page_Utilization_Query to obtain information about the z/VM paging\n"
                    "  space defined on the system.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name\n"
                    "          (System_Page_Utilization_Query).\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }
    rc = smSystem_Page_Utilization_Query(vmapiContextP, "", 0, "", // Authorizing user, password length, password
            image, &output);
    if (rc) {
        printAndLogProcessingErrors("System_Page_Utilization_Query", rc, vmapiContextP, "", 0);
    } else if (rc || output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Page_Utilization_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        bytesleft = output->systemPageInfomationLength - 8;
        // Get total allocated pages
        token = strtok_r(output->systemPageInformation, blank, &buffer);
        if (token != NULL) {
            strcpy(total_page_pages, token);
            bytesleft = bytesleft - strlen(token);
        } else {
            if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages allocated for paging use on the system is NULL\n"))) {
                rc = OUTPUT_ERRORS_FOUND;
            }
            goto end;
        }

        // Get total uses pages
        token = strtok_r(NULL, blank, &buffer);
        if (token != NULL) {
            strcpy(total_page_pages_in_use, token);
            bytesleft = bytesleft - strlen(token);
        } else {
            if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages in use for paging on the system is NULL\n"))) {
                rc = OUTPUT_ERRORS_FOUND;
            }
            goto end;
        }

        // Get available percentage
        token = strtok_r(NULL, blank, &buffer);
        if (token != NULL) {
            strcpy(total_page_percent_used, token);
            bytesleft = bytesleft - strlen(token);
        } else {
            if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The percentage of the available paging space currently in use on the system is NULL\n"))) {
                rc = OUTPUT_ERRORS_FOUND;
            }
            goto end;
        }

        snprintf(strMsg, sizeof(strMsg),
               "Total allocated: %s\n"
               "Total used: %s\n"
               "Available percentage: %s\n" ,
               total_page_pages, total_page_pages_in_use, total_page_percent_used);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }

        pageinfo = strtok_r(NULL, "\0", &buffer);
        while ( bytesleft > 0 ) {
            memset(tempBuff, 0x00, 130);
            linesize = strlen((char *)pageinfo);
            strncpy(tempBuff, pageinfo, linesize);
            trim(tempBuff);
            tempBuff[linesize+1] = '\0';
            bytesleft = bytesleft - linesize;

            // Get volid
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(volid, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The volume ID of the paging volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get rdev
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(rdev, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The RDEV of the paging volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get total_pages
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(total_pages, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages on the volume available for paging use is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get pages_in_use
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(pages_in_use, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number pages in use on the volume for paging files is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get percent_used
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(percent_used, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The percentage of the available paging space on the volume in use is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get drained
            token = strtok_r(NULL, blank, &pageinfo);
            if (token != NULL) {
                strcpy(drained, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The drained information of the paging space on the volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            snprintf(strMsg, sizeof(strMsg),
                   "Volume ID: %s\n"
                   "RDEV: %s\n"
                   "Volume total pages: %s\n"
                   "Volume pages in use: %s\n"
                   "Available percentage: %s\n"
                   "Drain: %s\n" ,
                   volid, rdev, total_pages, pages_in_use, percent_used, drained);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            
            ++pageinfo;
        }
        if (rc) {
            DOES_CALLER_WANT_RC_HEADER_FOR_OUTPUT_ERRORS(vmapiContextP, MY_API_NAME);
        } else {
            DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
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

int systemPerformanceInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Performance_Information_Query";
    int rc;
    int i;
    int maxEntryCount = 1;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemPerformanceInformationQueryOutput * output;

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
                if (entryCount < maxEntryCount +1) {
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
                    "  System_Performance_Information_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Use System_Performance_Information_Query [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2... \n\n"
                    "DESCRIPTION\n"
                    "  Use System_Performance_Information_Query to gather hypervisor performance\n"
                    "  data, including available/used, processor number, total processor percentages,\n"
                    "  and optional detailed CPU information for all visible LPARs on the CEC.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_Disk_Query).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. \n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_Performance_Information_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Performance_Information_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Performance_Information_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int bytesUsed = 0;
        char * stringStart = output->systemPerformanceInformationData;
        while (bytesUsed < output->systemPerformanceInformationDataLength) {
            i = strlen(stringStart) + 1;
            printf("%s\n", stringStart);
            stringStart += i;
            bytesUsed += i;
        }
    }
    return rc;
}

int systemPerformanceThresholdDisable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Performance_Threshold_Disable";
    int rc;
    int option;
    char * targetIdentifier = NULL;
    char * eventType = NULL;
    vmApiSystemPerformanceThresholdDisableOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'v':
                eventType = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Performance_Threshold_Disable\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Performance_Threshold_Disable [-T] target_identifier [-v] dev_num\n\n"
                    "DESCRIPTION\n"
                    " Use System_Performance_Threshold_Disable to disable thresholds for asynchronous\n"
                    " event production.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization  i.e. the authenticated user must\n"
                    "          have authorization to perform this function for this target.\n"
                    "    -v    One of the following, followed by a null (ASCIIZ) terminator:\n"
                    "            System_CPU\n"
                    "            System_Virtual_IO\n"
                    "            System_Paging\n"
                    "            System_DASD_IO\n"
                    "            User_CPU userid\n"
                    "            User_IO userid\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier || !eventType) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Disabling thresholds for asynchronous event production for %s... ", eventType);

    rc = smSystem_Performance_Threshold_Disable(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            targetIdentifier, eventType, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Performance_Threshold_Disable", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Performance_Threshold_Disable", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


int systemPerformanceThresholdEnable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Performance_Threshold_Enable";
    int rc;
    int option;
    char * targetIdentifier = NULL;
    char * eventType = NULL;
    vmApiSystemPerformanceThresholdEnableOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'v':
                eventType = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Performance_Threshold_Enable\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Performance_Threshold_Enable [-T] targetIdentifier [-v] eventType\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Performance_Threshold_Enable to enable thresholds for asynchronous\n"
                    "  event production.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization  i.e. the authenticated user must\n"
                    "          have authorization to perform this function for this target.\n"
                    "    -v    One of the following, followed by a null (ASCIIZ) terminator:\n"
                    "            System_CPU = percentage\n"
                    "            System_Virtual_IO = rate/sec\n"
                    "            System_Paging = rate/sec\n"
                    "            System_DASD_IO = rate/sec\n"
                    "            User_CPU = userid percentage \n"
                    "            User_IO = userid rate/sec\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier || !eventType) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Enabling thresholds for asynchronous event production for %s... ", eventType);

    rc = smSystem_Performance_Threshold_Enable(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            targetIdentifier, eventType, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Performance_Threshold_Enable", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Performance_Threshold_Enable",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int systemSCSIDiskAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_SCSI_Disk_Add";
    int rc;
    int maxEntryCount = 4;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemSCSIDiskAddOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:k:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'k':
                if (!optarg) {
                    return INVALID_DATA;
                }
                if (entryCount < maxEntryCount) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }

                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_SCSI_Disk_Add\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_SCSI_Disk_Add [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_SCSI_Disk_Add to dynamically add a SCSI disk to a running z/VM\n"
                    "  system.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to which a disk is being added.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            dev_num: The SCSI disk device number.\n"
                    "            dev_path_array: An array of device path structures. Each\n"
                    "                            structure has the following fields\n"
                    "                            (each field is separated by a blank and the\n"
                    "                            structures are separated by semicolons)\n"
                    "              fcp_dev_num: The FCP device number\n"
                    "              fcp_wwpn:  The world wide port number\n"
                    "              fcp_lun: The logical unit number\n"
                    "    NOTE: The following are only used on ZVM 6.2 and above\n"
                    "            option: One of the following:\n"
                    "              1 - Add a new SCSI disk. This is the default if unspecified.\n"
                    "              2 - Add new paths to an existing SCSI disk.\n"
                    "              3 - Delete paths from an existing SCSI disk.\n\n"
                    "            persist: This can be one of the following values:\n"
                    "              NO - The SCSI device is updated on the active system, but is\n"
                    "                   not updated in the permanent configuration for the system.\n"
                    "              YES - The SCSI device is updated on the active system and also\n"
                    "                    in the permanent configuration for the system.\n"
                    "              If not specified, the default is NO.\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding a real SCSI disk to z/VM system... ");

    rc = smSystem_SCSI_Disk_Add(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_SCSI_Disk_Add", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_SCSI_Disk_Add", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int systemSCSIDiskDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_SCSI_Disk_Delete";
    int rc;
    int maxEntryCount = 2;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemSCSIDiskDeleteOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:k:h?")) != -1)
        switch (option) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'k':
                if (!optarg) {
                    return INVALID_DATA;
                }
                if (entryCount < maxEntryCount +1) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }

                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_SCSI_Disk_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_SCSI_Disk_Delete [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_SCSI_Disk_Delete to delete a real SCSI disk.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to which a disk is being added.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            dev_num: The SCSI disk device number.\n"
                    "            persist: This can be one of the following values:\n"
                    "              NO - The SCSI device is deleted on the active\n"
                    "                   system, but is not deleted in the permanent\n"
                    "                   configuration for the system.\n"
                    "              YES - The SCSI device is deleted from the active\n"
                    "                    system and also from the permanent\n"
                    "                    configuration for the system.\n"
                    "          If not specified, the default is NO.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting a real SCSI disk... ");

    rc = smSystem_SCSI_Disk_Delete(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);


    if (rc) {
        printAndLogProcessingErrors("System_SCSI_Disk_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_SCSI_Disk_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int systemSCSIDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_SCSI_Disk_Query";
    int rc;
    int i;
    int k;
    int offset;
    int maxEntryCount = 1;
    int minNeeded = 1;
    int entryCount = 0;
    int option;
    int fcpStructureSize;
    int numFcpStructures;
    int fcpDevIdIndex = 0;
    int fcpDevWwpnIndex = 0;
    int fcpDevLunIndex = 0;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    char * token;
    char * buffer;
    char * blank = " ";
    char dev_id[4+1];
    char dev_type[3+1];
    char dev_attr[4+1];
    char dev_size[8+1];
    char fcp_dev_id[4+1];
    char fcp_dev_wwpn[16+1];
    char fcp_dev_lun[16+1];
    char arrayFcpStructure[1024];
    vmApiSystemSCSIDiskQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

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
                if (entryCount < maxEntryCount) {
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
                    "  System_SCSI_Disk_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_SCSI_Disk_Query [-T] targetIdentifier [-k] entry.\n\n"
                    "DESCRIPTION\n"
                    " Use System_SCSI_Disk_Query to query a real SCSI disk or all real SCSI disks.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name\n"
                    "          (System_SCSI_Disk_Query).\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "            dev_num: The device number or 'ALL'\n\n");
                printRCheaderHelp();
                return 0;
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


    if (!targetIdentifier ||  entryCount < minNeeded)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_SCSI_Disk_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_SCSI_Disk_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_SCSI_Disk_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i =0; i < output->scsiInfoArrayCount; i ++) {
            // Get dev_id
            token = strtok_r(output->scsiInfoStructure[i].vmapiString, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device ID is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_type
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device type is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_attr
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_attr, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device attribute is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Get dev_size
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dev_size, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Device size is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            snprintf(strMsg, sizeof(strMsg),
                   "  Device ID: %s\n"
                   "  Device type: %s\n"
                   "  Device attribute: %s\n"
                   "  Device size, in blocks: %s\n",
                   dev_id, dev_type, dev_attr, dev_size);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }

            // Get fcp_structure
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(arrayFcpStructure, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: FCP structure is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            fcpStructureSize = strlen(arrayFcpStructure);
            numFcpStructures = fcpStructureSize / 36;
            offset =0;
        	memset(fcp_dev_id, 0x00, 4 + 1);
        	memset(fcp_dev_wwpn, 0x00, 16 + 1);
        	memset(fcp_dev_lun, 0x00, 16 + 1);
            for (k =0; k < numFcpStructures; k++) {
                strncpy(fcp_dev_id, arrayFcpStructure + (offset), 4);
                fcp_dev_id[4] = '\0';
                strncpy(fcp_dev_wwpn, arrayFcpStructure + (offset + 4), 16);
                fcp_dev_wwpn[16] = '\0';
                strncpy(fcp_dev_lun,  arrayFcpStructure +(offset + 20), 16);
                fcp_dev_lun[16] = '\0';
                snprintf(strMsg, sizeof(strMsg),
                       "  FCP device number: %s\n"
                       "  World wide port number: %s\n"
                       "  Logical unit number: %s\n",
                       fcp_dev_id, fcp_dev_wwpn, fcp_dev_lun);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
                offset = offset + 36;
            }
            if (0 != (rc = addMessageToBuffer(&saveMsgs, "\n"))) {
                goto end;
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

int systemServiceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Service_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiSystemServiceQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    int bytesUsed = 0;

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        argBytes = argBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (argBytes > 0) {
        entryArray = malloc(argBytes);
    }

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
        case 'T':
            image = optarg;
            break;

        case 'k':
            if (!optarg) {
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return INVALID_DATA;
            }
            entryArray[entryCount] = optarg;
            entryCount++;
            break;

        case 'h':
            DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
            printf(
                    "NAME\n"
                            "  System_Service_Query\n\n"
                            "SYNOPSIS\n"
                            "  smcli System_Service_Query [-T] image_name\n"
                            "   [-k] 'entry1' [-k] 'entry2' ...\n\n"
                            "DESCRIPTION\n"
                            "  Use System_Service_Query to query the status of an APAR, PTF,\n"
                            "  or RSU for a zVM component.\n"
                            "  (Note that the status is based on information returned from the\n"
                            "  SERVICE EXEC, not from querying the running components.)\n\n"
                            "  The following options are required:\n"
                            "    -T    The name of the virtual machine being created.\n"
                            "    -k    Quoted 'keyword=value' items to describe the type & number of\n"
                            "          APAR/PTF/RSU to be queried. Refer to the System Management\n"
                            "          Application Programming manual for additional details.\n"
                            "          COMPONENT=  followed by by a series of blank-delimited \n"
                            "          �subkeyword=value� pairs,\n"
                            "            NameComponent=compname Required\n"
                            "                Refer to the Service Guide for component names.\n"
                            "                Examples: VMSES, REXX, LE, CMS, CP, GCS, DV, TSAF, AVS,\n"
                            "                          RSCS, TCPIP, OSA, DIRM, RACF, PERFTK, VMHCD.\n"
                            "            Type=APAR|PTF|RSU  Required \n"
                            "            Number=APAR_number|PTF_number'\n"
                            "                Required for APAR or PTF, ignored for RSU.\n\n");
            FREE_MEMORY_CLEAR_POINTER(entryArray);
            printRCheaderHelp();
            return 0;
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

    if (!image || entryCount < 1) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0){
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    rc = smSystem_Service_Query(vmapiContextP, "", 0, "", // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_Service_Query", rc, vmapiContextP, "", 0);
    } else if (rc || output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Service_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char * stringStart = output->systemServiceQueryData;
        while (bytesUsed < output->systemServiceQueryDataLength) {
            i = strlen(stringStart) + 1;
            printf("%s\n", stringStart);
            stringStart += i;
            bytesUsed += i;
        }
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);

    return rc;
}

int systemShutdown(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Shutdown";
    int rc;
    int maxEntryCount = 5;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxEntryCount];
    vmApiSystemShutdownOutput * output;

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
                    return INVALID_DATA;
                }
                if (entryCount < maxEntryCount) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_Shutdown\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Shutdown [-T] targetIdentifier\n"
                    "   [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Shutdown to systematically end all system function.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_Shutdown).\n"
                    "  The following options are optional:\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "           They may be specified in any order. Possible keywords are:\n"
                    "              Within - Send a shutdown signal to enabled users and delay the shutdown\n"
                    "                       until either the specified interval (minus the amount of time\n"
                    "                       reserved for a CP shutdown) has elapsed, or until all signaled\n"
                    "                       user machines indicate that they have shut down, whichever occurs\n"
                    "                       first. The interval is specified as a number of seconds in the range\n"
                    "                       of 1-65535. The default is that no Within=value is submitted.\n"
                    "              By - Sends a shutdown signal to enabled users and delay the shutdown until\n"
                    "                   either the designated time of day (minus the amount of time reserved\n"
                    "                   for a CP shutdown) is reached, or until all signaled user machines\n"
                    "                   indicate that they have shut down, whichever occurs first. The time\n"
                    "                   can be specified as hh:mm or hh:mm:ss. The equivalent interval in\n"
                    "                   seconds must be in the range 1-65535. The default is that no By=value\n"
                    "                   is submitted."
                    "              Immediate - One of the following:\n"
                    "                  IMMEDIATE - Shut down the system immediately without sending shutdown\n"
                    "                              signals to enabled users, even if a previous SHUTDOWN command\n"
                    "                              is pending. If a previous SHUTDOWN command is pending, its\n"
                    "                              operands are not used and must be specified with IMMEDIATE on\n"
                    "                              the new command if they are required.\n"
                    "                  NOIMMEDIATE - Do not issue the SHUTDOWN with the IMMEDIATE option. This\n"
                    "                                is the default.\n"
                    "              Reipl - One of the following:\n"
                    "                  REIPL - Specifies that the system is to be restarted immediately after the\n"
                    "                          SHUTDOWN command completes. This is the default.\n"
                    "                  NOREIPL - Specifies that the system is not to be restarted immediately after\n"
                    "                            the SHUTDOWN command completes.\n"
                    "              Cancel - One of the following:\n"
                    "                  CANCEL - This causes a scheduled shutdown to be terminated. Any guests that\n"
                    "                           received termination signals when the original SHUTDOWN command was\n"
                    "                           issued continue to process those signals.\n"
                    "                  NOCANCEL - This does not cause a scheduled shutdown to be terminated.\n"
                    "                             This is the default.\n\n");
                printRCheaderHelp();
                return 0;
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

    if (!targetIdentifier)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smSystem_Shutdown(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    // Handle the rc that comes back from making the SMAPI API call. If rc then the call to SMAPI failed.
    if (rc) {
        printAndLogProcessingErrors("System_Shutdown", rc, vmapiContextP, "", 0);
    } else {
        // Handle SMAPI return code and reason code and Error Buffer if it was sent
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("System_Config_SySystem_Shutdownntax_Check", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, "");
    }

    return rc;
}

int systemSpoolUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_Spool_Utilization_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int i;
    int segmentDataSize;
    const char * optString = "T:h?";
    char total_spool_pages[8+1];
    char total_spool_pages_in_use[8+1];
    char total_spool_percent_used[3+1];
    char volid[6+1];
    char rdev[4+1];
    char total_pages[8+1];
    char pages_in_use[8+1];
    char percent_used[3+1];
    char dump[7+1];
    char drained[10+1];
    char * blank = " ";
    char * buffer = NULL;
    char * spoolinfo = NULL;
    char * token = NULL;
    char tempBuff[130];
    vmApiSystemSpoolUtilizationQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, optString)) != -1)
        switch (option) {
        case 'T':
            image = optarg;
            break;

        case 'h':
            DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
            printf(
                    "NAME\n"
                    "  System_Spool_Utilization_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_Spool_Utilization_Query [-T] target_name\n\n"
                    "DESCRIPTION\n"
                    "  Use System_Spool_Utilization_Query to obtain information about the z/VM spool\n"
                    "  space defined on the system.\n\n"
                    "  The following options are required:\n"
                    "    -T    This can be any value.\n\n");
            printRCheaderHelp();
            return 0;
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }
    rc = smSystem_Spool_Utilization_Query(vmapiContextP, "", 0, "", // Authorizing user, password length, password
            image, &output);
    if (rc) {
        printAndLogProcessingErrors("System_Spool_Utilization_Query", rc, vmapiContextP, "", 0);
    } else if (rc || output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_Spool_Utilization_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i = 0; i < output->systemSpoolInformationCount; i++) {
        	memset(tempBuff, 0x00, 130);
            segmentDataSize = strlen((char *)output->systemSpoolInformation[i].vmapiString);
            strncpy(tempBuff, (char *)output->systemSpoolInformation[i].vmapiString, segmentDataSize);
            trim(tempBuff);
            tempBuff[segmentDataSize + 1] = '\0';
            token = strtok_r(tempBuff, blank, &buffer);

     	    if (i == 0) {
     	    	// Only get these 3 vars on the 1st loop
                // Get total allocated pages
                if (token != NULL) {
                    strcpy(total_spool_pages, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages allocated for spool use on the system is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Get total uses pages
                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(total_spool_pages_in_use, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages in use for spool on the system is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Get available percentage
                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(total_spool_percent_used, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The percentage of the available spool space currently in use on the system is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg), "\n"
                       "Total allocated: %s\n"
                       "Total used: %s\n"
                       "Available percentage: %s\n" ,
                       total_spool_pages, total_spool_pages_in_use, total_spool_percent_used);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
     	    }

     	    // Get volid
     	    if ( i == 0 ) {
     	    	// Only do the strtok_r on the 1st one after that it is handled
     	    	// on the main one under the for loop
                token = strtok_r(NULL, blank, &buffer);
     	    }
            if (token != NULL) {
                strcpy(volid, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The volume ID of the spool volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get rdev
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(rdev, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The RDEV of the spool volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get total_pages
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(total_pages, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number of pages on the volume available for spool use is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get pages_in_use
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(pages_in_use, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The total number pages in use on the volume for spool files is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get percent_used
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(percent_used, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The percentage of the available spool space on the volume in use is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get dump
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(dump, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The DUMP space information of the spool space on the volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get drained
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(drained, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: The drained information of the spool space on the volume is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            snprintf(strMsg, sizeof(strMsg),
                   "  Volume ID: %s\n"
                   "  RDEV: %s\n"
                   "  Volume total pages: %s\n"
                   "  Volume pages in use: %s\n"
                   "  Available percentage: %s\n"
                   "  Dump: %s\n"
                   "  Drain: %s\n" ,
                   volid, rdev, total_pages, pages_in_use, percent_used, dump, drained);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
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

int systemWWPNQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "System_WWPN_Query";
    int rc;
    int i;
    int option;
    int devStatus;
    char * targetIdentifier = NULL;
    char * token;
    char * buffer;
    char * delims = " \0";
    char fcp_dev_id[4+1];
    char npiv_wwpn[16+1];
    char chpid[2+1];
    char perm_wwpn[16+1];
    char dev_status[1+1];
    char owner[8+1];
    char * status;
    int entryCount = 0;
    int argBytes = 0;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    int smapiLevel = 0;
    vmApiSystemWWPNQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;


    rc = getSmapiLevel(vmapiContextP, " ", &smapiLevel);
    if (rc != 0){
        printf("\nERROR: Unable to determine SMAPI level.\n");
        return 1;
    }

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
                targetIdentifier = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  System_WWPN_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli System_WWPN_Query [-T] targetIdentifier\n\n"
                    "DESCRIPTION\n"
                    " Use System_WWPN_Query to query all FCPs on a z/VM system and return a list of\n"
                    " WWPNs.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file that also contains\n"
                    "          the authenticated_userid and the function_name (System_WWPN_Query).\n");
                if (smapiLevel >= 630) {
                    printf("  The following options are optional:\n"
                    "    -k    A quoted keyword=value OWNER=YES|NO default is NO.\n");
                }
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                printRCheaderHelp();
                return 0;
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

            case 'k':
                entryArray[entryCount] = optarg;
                entryCount++;
                break;

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                printf("\nERROR: Unknown option\n");
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
                break;
        }


    if (!targetIdentifier) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0){
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    rc = smSystem_WWPN_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("System_WWPN_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("System_WWPN_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i =0; i < output->wwpnArrayCount; i ++) {
            // Get fcp_dev_id
            token = strtok_r(output->wwpnStructure[i].vmapiString, delims, &buffer);
            if (token != NULL) {
                strcpy(fcp_dev_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: FCP device number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get npiv_wwpn
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(npiv_wwpn, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: NPIV world wide port number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get chpid
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(chpid, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Channel path ID is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get perm_wwpn
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(perm_wwpn, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: Physical world wide port number is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Get dev_status
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(dev_status, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: FCP device status is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            devStatus = atoi(dev_status);
            switch (devStatus) {
                case 1:
                    status = "Active";
                    break;
                case 2:
                    status = "Free";
                    break;
                case 3:
                    status = "Offline";
                    break;
                default:
                	status = "Unknown";
                    break;
            }

            // Get owner if specified
            token = strtok_r(NULL, delims, &buffer);
            if (token != NULL) {
                strcpy(owner, token);
            } else {
                strcpy(owner, "");
            }
            snprintf(strMsg, sizeof(strMsg),
                   "FCP device number: %s\n"
                   "  Status: %s\n"
                   "  NPIV world wide port number: %s\n"
                   "  Channel path ID: %s\n"
                   "  Physical world wide port number: %s\n",
                   fcp_dev_id, status, npiv_wwpn, chpid, perm_wwpn);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            if (smapiLevel >= 630) {
                if (strlen(owner) > 0) {
                    snprintf(strMsg, sizeof(strMsg),"  Owner: %s\n",owner);
                    if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                        goto end;
                    }
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
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}
