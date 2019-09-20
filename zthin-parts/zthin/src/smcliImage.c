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
#include <stdio.h>
#include <stdlib.h>
#include "smcliImage.h"
#include "wrapperutils.h"

int imageActivate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Activate";
    int rc;
    int option;
    char * image = NULL;
    int retries = 6;
    int sleepTimeSeconds = 15;
    int i;
    char strMsg[250];
    vmApiImageActivateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Activate\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Activate [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Activate to activate a virtual image or list of virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being activated\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Activating %s... ", image);

    // Loop a few times if image is still being shutdown
    for (i=0; i < retries; i++) {
        rc = smImage_Activate(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
                image, &output);

        if (rc) {
            printAndLogProcessingErrors("Image_Activate", rc, vmapiContextP, strMsg, 0);
            break; // Stop loop if severe error
        } else {
            // Handle SMAPI return code and reason code
            // If this is a rc 200 reason 16, the image is still shutting down, so sleep and retry a few times
            // Note: The &output data will be reobtained and the old memory freed later
            if ((output->common.returnCode == 200) && (output->common.reasonCode == 16)) {
                // If this is not the last attempt, sleep and retry
                if (i < (retries -1)) {
                    sleep(sleepTimeSeconds);
                    continue;
                }
            }
            rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Activate", output->common.returnCode,
                    output->common.reasonCode, vmapiContextP, strMsg);
            break; // all done
        }
    }
    return rc;
}

int imageActiveConfigurationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Active_Configuration_Query";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageActiveConfigurationQueryOutput * output;
    vmApiImageCpuInfo* cpuList;
    vmApiImageDeviceInfo* deviceList;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Active_Configuration_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Active_Configuration_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Active_Configuration_Query to obtain current configuration\n"
                    "  information for an active virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid being queried\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Handle return code and reason code
    rc = smImage_Active_Configuration_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Active_Configuration_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Active_Configuration_Query",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out active configuration
        int cpuInfoCount = output->cpuInfoCount;
        int deviceCount = output->deviceCount;
        int memorySize = output->memorySize;
        int numberOfCpus = output->numberOfCpus;
        char* shareType = "";
        if (output->shareType == 1) {
            shareType = "Relative";
        } else if (output->shareType == 2) {
            shareType = "Absolute";
        }

        char* shareValue = output->shareValue;
        char* memoryUnit = "";
        if (output->memoryUnit == 1) {
            memoryUnit = "KB";
        } else if (output->memoryUnit == 2) {
            memoryUnit = "MB";
        } else if (output->memoryUnit == 3) {
            memoryUnit = "GB";
        }

        printf("Memory: %i %s\n"
            "Share type: %s\n"
            "Share value: %s\n"
            "CPU count: %i\n", memorySize, memoryUnit, shareType, shareValue, numberOfCpus);

        cpuList = output->cpuList;
        int i;
        char* cpuType;
        char* cpuStatus;
        printf("CPUs\n");
        for (i = 0; i < numberOfCpus; i++) {
            if (cpuList[i].cpuStatus == 1) {
                cpuStatus = "Base";
            } else if (cpuList[i].cpuStatus == 2) {
                cpuStatus = "Stopped";
            } else if (cpuList[i].cpuStatus == 3) {
                cpuStatus = "Check-stopped";
            } else if (cpuList[i].cpuStatus == 4) {
                cpuStatus = "Non-base, active";
            }
            printf("  Address: %i\n"
                "  ID: %s (%s)\n", cpuList[i].cpuNumber, cpuList[i].cpuId, cpuStatus);
        }

        deviceList = output->deviceList;
        char* deviceType;
        printf("Devices\n");
        for (i = 0; i < deviceCount; i++) {
            if (deviceList[i].deviceType == 1) {
                deviceType = "CONS";
            } else if (deviceList[i].deviceType == 2) {
                deviceType = "RDR";
            } else if (deviceList[i].deviceType == 3) {
                deviceType = "PUN";
            } else if (deviceList[i].deviceType == 4) {
                deviceType = "PRT";
            } else if (deviceList[i].deviceType == 5) {
                deviceType = "DASD";
            }
            printf("  Address: %s (%s)\n", deviceList[i].deviceAddress, deviceType);
        }
    }
    return rc;
}

int imageCPUDefine(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Define";
    int rc;
    int option;
    int cpuType = -1;
    char * image = NULL;
    char * cpuAddress = NULL;
    vmApiImageCpuDefineOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvt";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:t:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                cpuAddress = optarg;
                break;

            case 't':
                cpuType = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Define\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Define [-T] image_name [-v] virtual_address\n"
                    "    [-t] cpu_type\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Define to add a virtual processor to an active virtual\n"
                    "  image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual image for which to define a virtual CPU\n"
                    "    -v    The virtual CPU address to add to the virtual image\n"
                    "    -t    The type of processor to add:\n"
                    "            0: Unspecified\n"
                    "            1: CP\n"
                    "            2: IFL\n"
                    "            3: ZAAP\n"
                    "            4: ZIIP\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !cpuAddress || (cpuType < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding a virtual processor to %s's configuration...", image);

    rc = smImage_CPU_Define(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, cpuAddress, cpuType, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Define", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Define", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageCPUDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Define_DM";
    int rc;
    int option;
    int baseCpu = -1;
    int dedicateCpu = -1;
    int cryto = 0;  // ZVM 6.1 this is no longer supported but must be accounted for in input list
    char * image = NULL;
    char * cpuAddress = NULL;
    char * cpuId = "";
    int smapiLevel = 0;
    vmApiImageCpuDefineDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvbcdy";
    char tempStr[1];
    char strMsg[250];


    rc = getSmapiLevel(vmapiContextP, "", &smapiLevel);
    if (rc != 0){
        printAndLogProcessingErrors("Image_CPU_Define_DM", rc, vmapiContextP, "", 0);
        printf("\nERROR: Unable to determine SMAPI level.\n");
        return 1;
    }
    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:b:c:d:y:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                cpuAddress = optarg;
                break;

            case 'b':
                baseCpu = atoi(optarg);
                break;

            case 'c':
                cpuId = optarg;
                break;

            case 'd':
                dedicateCpu = atoi(optarg);
                break;

            case 'y':
                cryto = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf( "NAME\n"
                    "  Image_CPU_Define_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Define_DM -h\n\n"
                    "  smcli Image_CPU_Define_DM -T image_name -v virtual_address -b base_cpu\n"
                    "    -d dedicate_cpu [-c cpu_id]\n" );
                if ( smapiLevel < 610 ) {
                    printf( "    [-y cryto_cpu]\n" );
                }
                printf( "\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Define_DM to add a virtual processor to a virtual image's\n"
                    "  directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T image_name\n"
                    "          The name of the virtual image for which to statically define a\n"
                    "          virtual CPU.\n"
                    "    -v virtual_address\n"
                    "          The virtual CPU address to add to the static definition of the\n"
                    "          virtual image (in the hexadecimal range of 0-3F)\n"
                    "    -b base_cpu\n"
                    "          Specifies whether this CPU defines the base virtual processor:\n"
                    "            0: Unspecified\n"
                    "            1: BASE\n"
                    "    -d dedicate_cpu\n"
                    "          Specifies whether the virtual processor is to be dedicated at LOGON\n"
                    "          time to a real processor:\n"
                    "            0: Unspecified\n"
                    "            1: NODEDICATE\n"
                    "            2: DEDICATE\n");
                printf(
                    "  The following options are optional:\n"
                    "    -c cpu_id\n"
                    "          The processor identification number to be stored in bits 8 through 31\n"
                    "          of the CPU ID, returned in response to the store processor ID (STIDP)\n"
                    "          instruction\n");
                if ( smapiLevel < 610 ) {
                    printf(
                    "    -y cryto_cpu\n"
                    "          Specifies whether the virtual Cryptographic Coprocessor Facility (CCF)\n"
                    "          should be defined automatically for the virtual CPU at LOGON time:\n"
                    "            0: Unspecified (no CRYPTO)\n"
                    "            1: CRYPTO\n" );
                }
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (!image || !cpuAddress || (baseCpu < 0) || (dedicateCpu < 0) ) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding a virtual processor to %s's directory entry...", image);

    rc = smImage_CPU_Define_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, cpuAddress, baseCpu, cpuId, dedicateCpu, cryto, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Define", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Define", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageCPUDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * cpuAddress = NULL;
    vmApiImageCpuDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                cpuAddress = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Delete [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Delete to delete a virtual processor from an active\n"
                    "  virtual image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of a virtual image for which a virtual CPU will\n"
                    "          be deleted.\n"
                    "    -v    The virtual CPU address to delete from the virtual image\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (!image || !cpuAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting a virtual processor from %s's active configuration... ", image);

    rc = smImage_CPU_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, cpuAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageCPUDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Delete_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiImageCpuDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Delete_DM [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Delete_DM to delete a virtual processor from a\n"
                    "  virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual image from which to statically\n"
                    "          delete a virtual CPU.\n"
                    "    -v    The virtual CPU address to delete from the static\n"
                    "          definition of the virtual image (in the hexadecimal\n"
                    "          range of 0-3F).\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting a virtual processor from %s's directory entry... ", image);

    rc = smImage_CPU_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageCPUQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Query";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageCpuQueryOutput* output;
    vmApiImageCpuInfo* cpuList;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Query to query the virtual processors in an active\n"
                    "  virtual image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual image whose virtual CPUs are\n"
                    "          being queried\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_CPU_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out active configuration
        int cpuInfoCount = output->cpuInfoCount;
        int numberOfCpus = output->numberOfCpus;

        printf("CPU count: %i\n", numberOfCpus);

        cpuList = output->cpuList;
        int i;
        char* cpuType;
        char* cpuStatus;
        printf("CPUs\n");
        for (i = 0; i < numberOfCpus; i++) {
            if (cpuList[i].cpuStatus == 1) {
                cpuStatus = "Base";
            } else if (cpuList[i].cpuStatus == 2) {
                cpuStatus = "Stopped";
            } else if (cpuList[i].cpuStatus == 3) {
                cpuStatus = "Check-stopped";
            } else if (cpuList[i].cpuStatus == 4) {
                cpuStatus = "Non-base, active";
            }

            if (cpuList[i].cpuType == 1) {
                cpuType = "CP";
            } else if (cpuList[i].cpuType == 2) {
                cpuType = "IFL";
            } else if (cpuList[i].cpuType == 3) {
                cpuType = "ZAAP";
            } else if (cpuList[i].cpuType == 4) {
                cpuType = "ZIIP";
            }
            printf("  Address: %i\n"
                "    Type: %s\n"
                "    ID: %s (%s)\n", cpuList[i].cpuNumber, cpuType, cpuList[i].cpuId, cpuStatus);
        }
    }
    return rc;
}

int imageCPUQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Query_DM";
    int rc;
    int option;
    char * image = NULL;
    char * cpuAddress = NULL;
    vmApiImageCpuQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                cpuAddress = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Query_DM [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Query_DM to query a virtual processor in a virtual\n"
                    "  image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual image from which to query a\n"
                    "          virtual CPU\n"
                    "    -v    The virtual CPU address to query from the static definition\n"
                    "          of the virtual image\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !cpuAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_CPU_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, cpuAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char* cpuAddress = output->cpuAddress;

        char* baseCpu = "Unspecified";
        if (output->baseCpu == 0) {
            baseCpu = "Unspecified";
        } else if (output->baseCpu == 1) {
            baseCpu = "BASE";
        }

        char* cpuId = output->cpuId;

        char* dedicateCpu = "Unspecified";
        if (output->cpuDedicate == 0) {
            dedicateCpu = "Unspecified";
        } else if (output->cpuDedicate == 1) {
            dedicateCpu = "NODEDICATE";
        } else if (output->cpuDedicate == 2) {
            dedicateCpu = "DEDICATE";
        }

        char* crypto = "Unspecified";
        if (output->cpuCrypto == 0) {
            crypto = "Unspecified";
        } else if (output->cpuCrypto == 1) {
            crypto = "CRYPTO";
        }

        printf("Address: %s (%s)\n"
            "ID: %s\n"
            "Dedicated: %s\n"
            "CCF: %s\n", cpuAddress, baseCpu, cpuId, dedicateCpu, crypto);
    }
    return rc;
}

int imageCPUSetMaximumDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_CPU_Set_Maximum_DM";
    int rc;
    int option;
    int maxCpu = 0;
    char * image = NULL;
    vmApiImageCpuSetMaximumDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tm";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:m:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'm':
                maxCpu = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_CPU_Set_Maximum_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_CPU_Set_Maximum_DM [-T] image_name [-m] max_cpu\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_CPU_Set_Maximum_DM to set the maximum number of virtual\n"
                    "  processors that can be defined in a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T     The name of the virtual image for which to set the maximum\n"
                    "           number of virtual processors\n"
                    "    -m     The maximum number of virtual processors the user can define\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !maxCpu) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Setting the maximum number of virtual processors to %d for %s directory entry... ", maxCpu, image);

    rc = smImage_CPU_Set_Maximum_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, maxCpu, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_CPU_Set_Maximum_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_CPU_Set_Maximum_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Create_DM";
    int rc;
    int option;
    char * image = NULL;
    char * userEntryFile = NULL;
    int userEntryStdin = 0;
    char * prototype = "";
    char * password = "";
    char * accountNumber = "";

    FILE * fp;
    int recordCount = 0;
    int c;
    char * ptr;

    int i;
    int j;
    int LINE_SIZE = 72;
    char buffer[100][LINE_SIZE];

    vmApiImageCreateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tfpwa";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:p:w:a:sh?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;
            case 'f':
                userEntryFile = optarg;
                break;
            case 's':
                userEntryStdin = 1;
                break;
            case 'p':
                prototype = optarg;
                break;
            case 'w':
                password = optarg;
                break;
            case 'a':
                accountNumber = optarg;
                break;
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Create_DM [-T] image_name [-f] user_entry_file\n"
                    "    [-p] prototype [-w] password [-a] account_number\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Create_DM to define a new virtual image in the directory.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be created\n"
                    "   Only one of the following options can be used\n\n"
                    "    -f    The directory entry file. Not required if a directory entry\n"
                    "          is provided from stdin.\n"
                    "    -s    Read the directory entry from stdin. Not required if a directory entry\n"
                    "          file is provided.\n"
                    "    -p    The prototype to use for creating the image\n\n"
                    "  The following options are optional:\n"
                    "    -w    The logon password to be assigned initially to the virtual image\n"
                    "          being created\n"
                    "    -a    The account number to be assigned initially to the virtual image\n"
                    "          being created\n\n"
                    "     Notes:\n"
                    "         1. If both the prototype and directory entry parameters are specified,\n"
                    "            then the prototype will be used and the directory entry parameter\n"
                    "            will be ignored.\n"
                    "         2. Neither the logon password nor the account number input parameters\n"
                    "            may be specified if directory entry is specified.\n");
                printRCheaderHelp();
                return 0;

            case 1:  // API name type data(other non option element key data)
            	break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (image == NULL || (userEntryFile == NULL && userEntryStdin == 0 && strlen(prototype) == 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    if (userEntryFile != NULL) {
        // Open the user entry file
        fp = fopen(userEntryFile, "r");
        if (NULL == fp) {
            printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
            printf("\nERROR: Failed to open file %s\n", userEntryFile);
            return 2;
        }

        // Count the number of lines and check that the line length is less then 72.
        // If it is set the record count to it else return an error
        j = 0;
        while ((c = fgetc(fp)) != EOF) {
            if (c == '\n') {
                j++;
                if (j <= 72) {
                    recordCount++;
                    j = 0;
                } else {
                    printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
                    printf("\nERROR: Input file %s line %d contains %d chars of input and the max is 72\n",
                           userEntryFile, recordCount + 1, j);
                    return 3;
                }
            } else {
                j++;
            }
        }

        // Reset position to start of file
        rewind(fp);
    } else if (userEntryStdin == 1) {
    	i=0;
        // Read in user entry from stdin
        while (fgets(buffer[i], LINE_SIZE, stdin) != NULL) {
            // Replace newline with null terminator
            ptr = strstr(buffer[i], "\n");
            if (ptr != NULL) {
                strncpy(ptr, "\0", 1);
                // Count the number of lines and set the record count to it
                recordCount++;
            }
            i++;
            if ((i == 100) && (stdin != NULL)) {
                printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
                printf("\nERROR: stdin contains more then 100 lines of input\n");
                return 4;
            }
        }
    }

    // Create image record
    vmApiImageRecord record[recordCount];
    char line[recordCount][LINE_SIZE];
	i=0;
    if (userEntryFile != NULL) {
        // Read in user entry from file
        while (fgets(line[i], LINE_SIZE, fp) != NULL) {
            // Replace newline with null terminator
            ptr = strstr(line[i], "\n");
            if (ptr != NULL) {
                strncpy(ptr, "\0", 1);
            }
            if (i == recordCount) {
            	// This should never happen but checking anyway
                printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
                printf("\nERROR: file contains more then %d lines of input\n", i);
                return 5;
            } else {
                record[i].imageRecordLength = strlen(line[i]);
                record[i].imageRecord = line[i];
                i++;
            }
        }

        // Close file
        fclose(fp);
    } else {
        // Read in user entry from stdin buffer
        for (i = 0; i < recordCount; i++) {
            record[i].imageRecordLength = strlen(buffer[i]);
            record[i].imageRecord = buffer[i];
        }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining %s in the directory... ", image);

    rc = smImage_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, prototype, strlen(password), password,  // Initial password length, initial password
            accountNumber, recordCount,  // Initial account number, image record array length
            (vmApiImageRecord *) record,  // Image record
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Create_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageDeactivate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Deactivate";
    int rc;
    int option;
    char * image = NULL;
    char * forceTime = "";
    vmApiImageDeactivateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'f':
                forceTime = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Deactivate\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Deactivate [-T] image_name [-f] force_time\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Deactivate to stop a virtual image or list of virtual images.\n"
                    "  The virtual image(s) will no longer be active on the system.\n\n"
                    "  The following option is required:\n"
                    "    -T    The name of the image being deactivated\n"
                        "  The following option is optional:\n"
                    "    -f    Specifies when the Image_Deactivate function is to take place. This \n"
                    "          must be inside double quotes because of spaces.\n"
                    "            IMMED: Immediate image deactivation\n"
                    "            WITHIN interval: Where interval is a number of seconds in the\n"
                    "                             the range 1-65535\n"
                    "            BY time: Where time is specified as hh:mm or hh:mm:ss\n"
                    "      Note: If unspecified, deactivation takes place according to the default\n"
                    "            signal timeout value set for the system\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Stopping %s... ", image);

    rc = smImage_Deactivate(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, forceTime, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Deactivate", rc, vmapiContextP, strMsg, 0);
    } else {
    	if (output->common.returnCode == 0) {
    		// Request successful; Image Deactivated Within output->common.reasonCode Seconds
    		// set the output->common.reasonCode to 0
    		output->common.reasonCode = 0;
    	}
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Deactivate", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Delete_DM";
    int rc;
    int option;
    int erase = -1;
    char * image = NULL;
    vmApiImageDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Te";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:e:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'e':
                erase = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Delete_DM [-T] image_name [-e] erase\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Delete_DM to delete a virtual image's definition from the directory.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be deleted\n"
                    "    -e    Indicates whether to erase data from the disk(s) being released:\n"
                    "            0: Unspecified (use installation default)\n"
                    "            1: Do not erase (override installation default)\n"
                    "            2: Erase (override installation default)\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || (erase < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting %s from the directory... ", image);

    rc = smImage_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, erase, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Delete_DM", rc, vmapiContextP, strMsg, 0);
    }  else if (output->common.returnCode == 592 && output->operationId) {
        // Asynchronous operation started. Messages/header handled in this routine
        rc = queryAsyncOperation(image, output->operationId, "Image_Delete_DM", vmapiContextP, strMsg);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeviceDedicate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Device_Dedicate";
    int rc;
    int option;
    int readOnly = 0;
    char * image = NULL;
    char * virtualAddress = NULL;
    char * realDevice = NULL;
    vmApiImageDeviceDedicateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TvrR";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:r:R:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'r':
                realDevice = optarg;
                break;

            case 'R':
                readOnly = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Device_Dedicate\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Device_Dedicate [-T] image_name [-v] virtual_address\n"
                    "    [-r] real_device_number [-o] readonly\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Device_Dedicate to add a dedicated device to an active virtual\n"
                    "  image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image obtaining a dedicated device\n"
                    "    -v    The virtual device number of the device\n"
                    "    -r    A real device number to be dedicated or attached to the\n"
                    "          specified virtual image\n"
                    "    -R    Specify a 1 if the virtual device is to be in read-only\n"
                    "          mode. Otherwise, specify a 0\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualAddress || !realDevice || (readOnly < 0) || (readOnly > 1)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Dedicating device %s to %s's active configuration... ", realDevice, image);

    rc = smImage_Device_Dedicate(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualAddress, realDevice, readOnly, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Device_Dedicate", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Device_Dedicate", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeviceDedicateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Device_Dedicate_DM";
    int rc;
    int option;
    int readOnly = 0;
    char * image = NULL;
    char * virtualDevice = NULL;
    char * realDevice = NULL;
    vmApiImageDeviceDedicateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TvrR";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:r:R:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualDevice = optarg;
                break;

            case 'r':
                realDevice = optarg;
                break;

            case 'R':
                readOnly = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Device_Dedicate_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Device_Dedicate_DM [-T] image_name [-v] virtual_device_number\n"
                    "    [-r] real_device_number [-R] read_only\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Device_Dedicate_DM to add a dedicated device to a virtual\n"
                    "  image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image obtaining a dedicated device\n"
                    "    -v    The virtual device number of the device\n"
                    "    -r    A real device number to be dedicated or attached to the\n"
                    "          specified virtual image\n"
                    "    -R    Specify a 1 if the virtual device is to be in read-only mode.\n"
                    "          Otherwise, specify a 0.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualDevice || !realDevice || (readOnly < 0) || (readOnly > 1)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Dedicating device %s to %s's directory entry... ", realDevice, image);

    rc = smImage_Device_Dedicate_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualDevice, realDevice, readOnly, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Device_Dedicate_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Device_Dedicate_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeviceReset(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Device_Reset";
    int rc;
    int option;
    char * image = NULL;
    char * virtualDevice = NULL;
    vmApiImageDeviceResetOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualDevice = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Device_Reset\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Device_Reset [-T] image_name [-v] virtual_device\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Device_Reset to clear all pending interrupts from the specified\n"
                    "  virtual device.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or image name for which the device is being reset\n"
                    "    -v    The virtual device number of the device to reset\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualDevice) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Clearing all pending interrupts from %s... ", virtualDevice);

    rc = smImage_Device_Reset(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualDevice, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Device_Reset", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Device_Reset", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeviceUndedicate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Device_Undedicate";
    int rc;
    int option;
    char * image = NULL;
    char * virtualDevice = NULL;
    vmApiImageDeviceUndedicateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualDevice = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Device_Undedicate\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Device_Undedicate [-T] image_name [-v] virtual_device\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Device_Undedicate to delete a dedicated device from an active\n"
                    "  virtual image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image from which a dedicated device is being\n"
                    "          removed\n"
                    "    -v    The virtual device number of the device to be deleted\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualDevice) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting dedicated device from %s's active configuration... ", image);

    rc = smImage_Device_Undedicate(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualDevice, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Device_Undedicate", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Device_Undedicate", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDeviceUndedicateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Device_Undedicate_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualDevice = NULL;
    vmApiImageDeviceUndedicateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualDevice = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Device_Undedicate_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Device_Undedicate_DM [-T] image_name [-v] virtual_device\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Device_Undedicate_DM to delete a dedicated device from a virtual\n"
                    "  image's directory entry\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image from which a dedicated device is being removed\n"
                    "    -v    The virtual device number of the device to be deleted\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualDevice) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting dedicated device from %s's directory entry... ", image);

    rc = smImage_Device_Undedicate_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualDevice, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Device_Undedicate_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Device_Undedicate_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskCopy(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Copy";
    int rc;
    int option;
    char * image = NULL;
    char * virtualDevice = NULL;
    vmApiImageDiskCopyOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualDevice = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Copy\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Copy [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Copy to clone a disk in an active virtual image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or image name of the single image for which the disk is\n"
                    "          being copied\n"
                    "    -v    The virtual device address of the target disk for the copy\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !virtualDevice) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Cloning disk in %s's active configuration... ", image);

    rc = smImage_Disk_Copy(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualDevice, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Copy", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Copy", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskCopyDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Copy_DM";
    int rc;
    int option;
    char * srcImage = NULL;
    char * srcDiskAddress = NULL;
    char * tgtDiskAddress = NULL;
    char * tgtImage = NULL;
    char * allocType = "";
    char * areaOrVolser = "";
    char * accessMode = "";
    char * readPass = "";
    char * writePass = "";
    char * multiPass = "";
    vmApiImageDiskCopyDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TtSsanmrwx";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:t:S:s:a:n:m:r:w:x:h?")) != -1)
        switch (option) {
            case 'S':
                srcImage = optarg;
                break;

            case 's':
                srcDiskAddress = optarg;
                break;

            case 'T':
                tgtImage = optarg;
                break;

            case 't':
                tgtDiskAddress = optarg;
                break;

            case 'a':
                allocType = optarg;
                break;

            case 'n':
                areaOrVolser = optarg;
                break;

            case 'm':
                accessMode = optarg;
                break;

            case 'r':
                readPass = optarg;
                break;

            case 'w':
                writePass = optarg;
                break;

            case 'x':
                multiPass = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Copy_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Copy_DM [-T] image_name [-s] src_disk_address\n"
                    "    [-t] target_image [-u] target_disk_address [-a] alloc_type\n"
                    "    [-n] area_or_volser [-m] access_mode [-r] read_password\n"
                    "    [-w] write_password [-x] multi_password\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Copy_DM to clone a disk in a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or image name of the single image for which the disk is\n"
                    "          being copied\n"
                    "    -t    The virtual device address of the target disk for the copy\n"
                    "    -S    The name of the virtual image that owns the image disk being copied\n"
                    "    -s    The image disk number of the virtual image that owns the disk\n"
                    "          being copied\n"
                    "  The following options are optional if the vdev exists on target machine:\n"
                    "    -a    Disk allocation type:\n"
                    "            The starting location\n"
                    "            AUTOG: Automatic_Group_Allocation\n"
                    "            AUTOR: Automatic_Region_Allocation\n"
                    "            AUTOV: Automatic_Volume_Allocation\n"
                    "            DEVNO: Full Volume Minidisk\n"
                    "    -n    Allocation area name or volser\n"
                    "    -m    The access mode requested for the disk:\n"
                    "            R: Read-only (R/O) access\n"
                    "            RR: Read-only (R/O) access\n"
                    "            W: Write access\n"
                    "            WR: Write access\n"
                    "            M: Multiple access\n"
                    "            MR: Write or any exclusive access\n"
                    "            MW: Write access is allowed to the disk unconditionally\n"
                    "  The following options are optional:\n"
                    "    -r    Defines the read password that will be used for accessing the disk\n"
                    "    -w    Defines the write password that will be used for accessing the disk\n"
                    "    -x    Defines the multi password that will be used for accessing the disk\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!srcImage || !srcDiskAddress || !tgtDiskAddress || !tgtImage) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Cloning disk in %s's directory entry... ", srcImage);

    rc = smImage_Disk_Copy_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            tgtImage, tgtDiskAddress, srcImage, srcDiskAddress, allocType, areaOrVolser, accessMode,
            readPass, writePass, multiPass, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Copy_DM", rc, vmapiContextP, strMsg, 0);
    } else if (output->common.returnCode == 592 && output->operationId) {
        rc = queryAsyncOperation(srcImage, output->operationId, "Image_Disk_Copy_DM", vmapiContextP, strMsg);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Copy_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Create";
    int rc;
    int option;
    char* image = NULL;
    char* deviceAddr = NULL;
    char* accessMode = NULL;
    vmApiImageDiskCreateOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvm";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:m:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                deviceAddr = optarg;
                break;

            case 'm':
                accessMode = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Create [-T] image_name [-v] virtual_address [-m] access_mode\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Create to add a disk that is defined in a virtual image's\n"
                    "  directory entry to that virtual image's active configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or image name of the single image for which the disk\n"
                    "          is being created.\n"
                    "    -v    The virtual device address of the disk to be added\n"
                    "    -m    The access mode requested for the disk\n"
                    "            R: Read-only (R/O) access\n"
                    "            RR: Read-only (R/O) access\n"
                    "            W: Write access\n"
                    "            WR: Write access\n"
                    "            M: Multiple access\n"
                    "            MR: Write or any exclusive access\n"
                    "            MW: Write access is allowed to the disk unconditionally\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !deviceAddr || !accessMode) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding disk to %s's active configuration... ", image);

    rc = smImage_Disk_Create(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, deviceAddr, accessMode, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Create_DM";
    int rc;
    int option;
    char* image = NULL;
    char* deviceAddr = "";
    char* deviceType = "";
    char* allocType = "";
    char* allocName = "";
    int allocSize = 0;
    int diskSize = 0;
    char* accessMode = "";
    int diskFormat = 0;
    char* diskLabel = "";
    char* readPass = "";
    char* writePass = "";
    char* multiPass = "";
    vmApiImageDiskCreateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TvtaruzmflRWM";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:t:a:r:u:z:m:f:l:R:W:M:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;
            case 'v':
                deviceAddr = optarg;
                break;
            case 't':
                deviceType = optarg;
                break;
            case 'a':
                allocType = optarg;
                break;
            case 'r':
                allocName = optarg;
                break;
            case 'u':
                allocSize = atoi(optarg);
                break;
            case 'z':
                diskSize = atoi(optarg);
                break;
            case 'm':
                accessMode = optarg;
                break;
            case 'f':
                diskFormat = atoi(optarg);
                break;
            case 'l':
                diskLabel = optarg;
                break;
            case 'R':
                readPass = optarg;
                break;
            case 'W':
                writePass = optarg;
                break;
            case 'M':
                multiPass = optarg;
                break;
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Create_DM [-T] image_name [-v] virtual_address\n"
                    "    [-t] device_type [-a] allocation_type [-r] area_name_or_volser\n"
                    "    [-u] unit_size [-z] disk_size [-m] access_mode\n"
                    "    [-f] disk_format [-l] disk_label [-R] read_password\n"
                    "    [-W] write_password [-M] multi_password\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Create_DM to add a disk to a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The userid or image name of the single image for which the disk\n"
                    "          is being created\n"
                    "    -v    The virtual device address of the disk to be added\n"
                    "    -t    The device type of the volume to which the disk is assigned\n"
                    "    -a    Allocation type:\n"
                    "            AUTOG: Automatic_Group_Allocation\n"
                    "            AUTOR: Automatic_Region_Allocation\n"
                    "            AUTOV: Automatic_Volume_Allocation\n"
                    "            DEVNO: Full Volume Minidisk\n"
                    "            T-DISK: Automatic Temporary Disk\n"
                    "            V-DISK: Automatic Virtual Disk\n"
                    "              In this case, image_disk_device_type must have value = FB-512\n"
                    "    -r    Allocation area name or volser:\n"
                    "            - The group or region where the new image disk is to be created.\n"
                    "              This is specified when allocationtype is AUTOG or AUTOR.\n"
                    "            - The label of the DASD volume where the new image disk is to\n"
                    "              be created. This is specified when allocation type is the\n"
                    "              starting location or AUTOV.\n"
                    "            - The device address of the full volume minidisk where the new\n"
                    "              image disk is to be created. This is specified when allocation\n"
                    "              type is DEVNO.\n"
                    "    -u    Unit size:\n"
                    "            1: CYLINDERS\n"
                    "            2: BLK0512\n"
                    "            3: BLK1024\n"
                    "            4: BLK2048\n"
                    "            5: BLK4096\n"
                    "    -z    The size of the disk to be created:\n"
                    "            - Cylinders, if the allocation_unit_size is CYLINDERS\n"
                    "            - Logical disk blocks of size nnnn if allocation_unit_size is\n"
                    "              BLKnnnn. nnnn is either 512 (or 0512), 1024, 2048, or 4096.\n"
                    "    -m    The access mode requested for the disk:\n"
                    "            R: Read-only (R/O) access\n"
                    "            RR: Read-only (R/O) access\n"
                    "            W: Write access\n"
                    "            WR: Write access\n"
                    "            M: Multiple access\n"
                    "            MR: Write or any exclusive access\n"
                    "            MW: Write access is allowed to the disk unconditionally\n"
                    "    -f    Disk format:\n"
                    "            0: Unspecified\n"
                    "            1: Unformatted\n"
                    "            2: CMS formatted with 512 bytes per block\n"
                    "            3: CMS formatted with 1024 bytes per block\n"
                    "            4: CMS formatted with 2048 bytes per block\n"
                    "            5: CMS formatted with 4096 bytes per block\n"
                    "            6: CMS formatted with the default block size for the allocated\n"
                    "               device type\n"
                    "  The following options are optional:\n"
                    "    -l    The disk label to use when formatting the new extent\n"
                    "    -R    Read password\n"
                    "    -W    Write password\n"
                    "    -M    Multi password\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !deviceAddr || !deviceType || !allocType || !allocName || !allocSize || !diskSize || !accessMode) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding a disk to %s's directory entry... ", image);

    rc = smImage_Disk_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, deviceAddr, deviceType, allocType, allocName, allocSize,
            diskSize, accessMode, diskFormat, diskLabel,
            readPass, writePass, multiPass,  // Read, write, and multi passwords
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else if (output->common.returnCode == 592 && output->operationId) {
        rc = queryAsyncOperation(image, output->operationId, "Image_Disk_Create_DM", vmapiContextP, strMsg);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Create_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * address = NULL;
    vmApiImageDiskDeleteOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Delete [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Delete to delete a disk from an active virtual image's\n"
                    "  configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the disk is being deleted\n"
                    "    -v    The virtual device address of the disk to be deleted\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting disk from %s's configuration... ", image);

    rc = smImage_Disk_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, address, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Delete_DM";
    int rc;
    int option;
    int securityErase = -1;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiImageDiskDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tve";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:e:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'e':
                securityErase = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Delete_DM [-T] image_name [-v] virtual_address\n"
                    "    [-e] security_erase\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Delete_DM to delete a disk from a virtual image's directory\n"
                    "  entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name\n"
                    "    -v    The virtual device address of the disk to be deleted.\n"
                    "    -e    Indicates whether to erase data from the disk(s) being released:\n"
                    "            0: Unspecified (use installation default)\n"
                    "            1: Do not erase (override installation default)\n"
                    "            2: Erase (override installation default)\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }


    if (!image || !virtualAddress || (securityErase < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting a disk from %s's directory entry... ", image);

    rc = smImage_Disk_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualAddress, securityErase, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else if (output->common.returnCode == 592 && output->operationId) {
        rc = queryAsyncOperation(image, output->operationId, "Image_Disk_Delete_DM", vmapiContextP, strMsg);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Query";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    int arrayBytes = 0;
    char ** entryArray;
    const char * optString = "-T:k:h?";
    vmApiImageDiskQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        arrayBytes = arrayBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (arrayBytes > 0) {
        entryArray = malloc(arrayBytes);
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
                printf("NAME\n"
                    "  Image_Disk_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Query [-T] image_name\n"
                    "    [-k] 'vdasd_id=value' \n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Query to display the status of all DASDs \n"
                    "    accessible to a virtual image, including temporary disks and virtual disks\n"
                    "    in storage.\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine whose disks are being queried.\n"
                    "    -k    A quoted 'vdasd_id=value'\n"
                    "          The value is a virtual device number, or ALL \n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
     }
     if (!image || !entryCount) {
         DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
       printf("\nERROR: Missing required options\n");
       if (arrayBytes > 0){
           FREE_MEMORY_CLEAR_POINTER(entryArray);
       }
       return 1;
    }

    rc = smImage_Disk_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
         image, entryCount, entryArray, &output);
    FREE_MEMORY_CLEAR_POINTER(entryArray);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char * accessType;
        char * dasdUnit;

        for (i = 0; i < output->dasdCount; i++) {
            if (output->dasdList[i].accessType == 1) {
                accessType = "R/O";
            } else {
                accessType = "R/W";
            }
            if (output->dasdList[i].cylOrBlocks == 1) {
                dasdUnit = "Cylinders";
            } else {
                dasdUnit = "Blocks";
            }
            printf("DASD VDEV: %s\n"
                    "  RDEV: %s\n"
                    "  Access type: %s\n"
                    "  Device type: %s\n"
                    "  Device size: %lld\n"
                    "  Device units: %s\n"
                    "  Device volume label: %s\n\n",
                    output->dasdList[i].vdev, output->dasdList[i].rdev, accessType, output->dasdList[i].devtype,
                    output->dasdList[i].size, dasdUnit, output->dasdList[i].volid);
        }
    }
    return rc;
}

int imageDiskShare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Share";
    int rc;
    int option;
    char * image = NULL;
    char * address = NULL;
    char * tgtImage = NULL;
    char * tgtAddress = NULL;
    char * accessMode = NULL;
    char * password = "";
    vmApiImageDiskShareOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvtrap";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:t:r:a:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 't':
                tgtImage = optarg;
                break;

            case 'r':
                tgtAddress = optarg;
                break;

            case 'a':
                accessMode = optarg;
                break;

            case 'p':
                password = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Share\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Share [-T] image_name [-v] virtual_address [-t] target_image\n"
                    "    [-r] target_address [-a] access_mode [-p] password\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Share to add a disk that is defined in a virtual\n"
                    "  image's directory entry to a different active virtual image's\n"
                    "  configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the single image attempting to share the disk\n"
                    "    -v    The virtual device address of the disk to be shared\n"
                    "    -t    The name of the virtual image that owns the image disk\n"
                    "          being shared\n"
                    "    -r    The virtual device number to assign to the shared disk\n"
                    "    -a    The access mode requested for the disk:\n"
                    "            R: Read-only (R/O) access\n"
                    "            RR: Read-only (R/O) access\n"
                    "            W: Write access\n"
                    "            WR: Write access\n"
                    "            M: Multiple access\n"
                    "            MR: Write or any exclusive access\n"
                    "            MW: Write access is allowed to the disk unconditionally\n"
                    "  The following options are optional:\n"
                    "    -p    The password that MAY BE REQUIRED to share the disk\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address || !tgtImage || !tgtAddress || !accessMode) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding disk in %s's directory entry to %s's active configuration... ", tgtImage, image);

    rc = smImage_Disk_Share(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, address, tgtImage, tgtAddress, accessMode, password, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Share", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Share", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskShareDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Share_DM";
    int rc;
    int option;
    char * image = NULL;
    char * address = NULL;
    char * tgtImage = NULL;
    char * tgtAddress = NULL;
    char * accessMode = NULL;
    char * password = "";
    vmApiImageDiskShareDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvtrap";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:t:r:a:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 't':
                tgtImage = optarg;
                break;

            case 'r':
                tgtAddress = optarg;
                break;

            case 'a':
                accessMode = optarg;
                break;

            case 'p':
                password = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Share_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Share_DM [-T] image_name [-v] target_address \n"
                    "    [-t] target_image [-r] virtual_address [-a] access_mode\n"
                    "    [-p] password\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Share_DM to add a disk that is defined in a virtual\n"
                    "  image's directory entry to a different virtual image's directory entry\n\n"
                    "    -T    The name of the single image attempting to share the disk\n"
                    "    -v    The virtual device address of the disk to be shared\n"
                    "    -t    The name of the virtual image that owns the image disk\n"
                    "          being shared\n"
                    "    -r    The virtual device number to assign to the shared disk\n"
                    "    -a    The access mode requested for the disk:\n"
                    "            R: Read-only (R/O) access\n"
                    "            RR: Read-only (R/O) access\n"
                    "            W: Write access\n"
                    "            WR: Write access\n"
                    "            M: Multiple access\n"
                    "            MR: Write or any exclusive access\n"
                    "            MW: Write access is allowed to the disk unconditionally\n"
                    "      The following options are optional:\n"
                    "    -p    The password that MAY BE REQUIRED to share the disk\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address || !tgtImage || !tgtAddress || !accessMode) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding disk in %s's directory entry to %s's directory entry... ", tgtImage, image);

    rc = smImage_Disk_Share_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, tgtAddress, tgtImage, address, accessMode, password, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Share_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Share_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskUnshare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Unshare";
    int rc;
    int option;
    char * image = NULL;
    char * address = NULL;
    vmApiImageDiskUnshareOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Unshare\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Unshare [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Unshare to delete a shared disk from an active\n"
                    "  virtual image's configuration.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image from which the previously-shared\n"
                    "          disk is to be removed from the configuration\n"
                    "    -v    The virtual device address of the previously-shared\n"
                    "          disk to be removed from the configuration\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting shared disk from %s's configuration... ", image);

    rc = smImage_Disk_Unshare(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, address, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Unshare", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Unshare", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageDiskUnshareDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Disk_Unshare_DM";
    int rc;
    int option;
    char * image = NULL;
    char * address = NULL;
    char * tgtImage = NULL;
    char * tgtAddress = NULL;
    vmApiImageDiskUnshareDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvtr";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:t:r:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 't':
                tgtImage = optarg;
                break;

            case 'r':
                tgtAddress = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Disk_Unshare_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Unshare_DM [-T] image_name [-v] virtual_address\n"
                    "    [-t] target_image [-r] target_virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Disk_Unshare_DM to delete a shared disk from a virtual\n"
                    "  image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image from which the previously-shared\n"
                    "          disk is to be removed from the configuration\n"
                    "    -v    The virtual device address of the previously-shared\n"
                    "          disk to be removed from the configuration\n"
                    "    -t    The name of the virtual image that owns the previously-shared\n"
                    "          disk to be removed from the configuration\n"
                    "    -r    The virtual device number previously assigned to the shared\n"
                    "          disk\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address || !tgtImage || !tgtAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting shared disk from %s's directory entry... ", image);

    rc = smImage_Disk_Unshare_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, address, tgtImage, tgtAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Disk_Unshare_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Disk_Unshare_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageIPLDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_IPL_Delete_DM";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageIplDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_IPL_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_IPL_Delete_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_IPL_Delete_DM to delete the IPL statement from a virtual\n"
                    "  image's directory entry or a profile directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    Specifies the name of the user or profile for which the IPL\n"
                    "          statement is to be deleted\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting IPL statement from %s's directory entry... ", image);

    rc = smImage_IPL_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_IPL_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_IPL_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageIPLQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_IPL_Query_DM";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageIplQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_IPL_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_IPL_Query_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_IPL_Query_DM to query the information about the operating\n"
                    "  system, or device containing the operating system, that is specified\n"
                    "  on the IPL statement in a virtual image's directory entry or a\n"
                    "  profile directory entry. This operating system is automatically\n"
                    "  loaded and started when the virtual image is activated.\n\n"
                    "  The following options are required:\n"
                    "    -T    Specifies the name of the user or profile for which the IPL\n"
                    "          statement is to be queried\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_IPL_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_IPL_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_IPL_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("IPL: %s\n"
            "Load parameter: %s\n"
            "Parameters: %s\n", output->savedSystem, output->loadParameter,
                output->parameters);
    }
    return rc;
}

int imageIPLSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_IPL_Set_DM";
    int rc;
    int option;
    char * image = NULL;
    char * savedSystem = "";
    char * loadParameter = "";
    char * parameter = "";
    vmApiImageIplSetDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tslp";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:s:l:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 's':
                savedSystem = optarg;
                break;

            case 'l':
                loadParameter = optarg;
                break;

            case 'p':
                parameter = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_IPL_Set_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_IPL_Set_DM [-T] image_name [-s] saved_system\n"
                    "    [-l] load_parameter [-p] parameter\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_IPL_Set_DM to add an IPL statement to a virtual image's\n"
                    "  directory entry or a profile directory entry. The IPL statement\n"
                    "  identifies an operating system, or a device containing an operating\n"
                    "  system, which is automatically loaded and started when the virtual\n"
                    "  image is activated.\n\n"
                    "  The following options are required:\n"
                    "    -T    Specifies the name of the user or profile for which the\n"
                    "          IPL statement is to be set.\n"
                    "    -s    Specifies the name of the saved system or virtual device\n"
                    "          address of the device containing the system to be loaded.\n"
                    "    -l    Specifies the load parameter (up to 8 characters) that is\n"
                    "          used by the IPL'd system. It may be necessary to enclose\n"
                    "          the load parameter in single quotes.\n"
                    "    -p    Specifies the parameters to be passed to the IPL'd operating\n"
                    "          system. Although the IPL command allows for 64 bytes of\n"
                    "          parameters, the string on the directory statement is limited\n"
                    "          to the number of characters that can be specified in the first\n"
                    "          72 positions of the statement.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding IPL statement to %s's directory entry... ", image);

    rc = smImage_IPL_Set_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, savedSystem, loadParameter, parameter, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_IPL_Set_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_IPL_Set_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageLockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Lock_DM";
    int rc;
    int option;
    char * image = NULL;
    char * address = "";
    vmApiImageLockDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Lock_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Lock_DM [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Lock_DM to lock a virtual image's directory entry or a specific\n"
                    "  device in a virtual image's directory entry so that it cannot be changed.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be locked.\n"
                    "  The following options are optional:\n"
                    "    -v    The virtual address of the device being locked.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    if (strlen(address) == 0) {
        // If they want special output header as first output, then we need to pass this
        // string on RC call so it is handled correctly for both cases.
        snprintf(strMsg, sizeof(strMsg), "Locking virtual image's directory entry %s... ", image);
    } else {
       snprintf(strMsg, sizeof(strMsg), "Locking virtual image's device %s... ", address);
    }
    rc = smImage_Lock_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, address,  // Image name, device virtual address
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Lock_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Lock_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageLockQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Lock_Query_DM";
    int rc;
    int option;
    int i;
    int devAddressDevLockedBySize;
    char * image = NULL;
    char *token;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    char * blank = " ";
    char lockedType[7 + 1];
    char imageLockedBy[8 + 1];
    char devAddress[4 + 1];
    char devLockedBy[8 + 1];
    char tempBuff[14];
    vmApiImageLockQueryDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Lock_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Lock_Query_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Lock_Query_DM to query the status of directory manager\n"
                    "  locks in effect for a specific virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the directory lock status is being\n"
                    "          queried.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Lock_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image,  // Image name
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Lock_Query_DM", rc, vmapiContextP, "", 0);
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 12)) {

        // Obtain lockedType
        token = strtok_r(output->lockedTypeImageLockedBy, blank, &buffer);
        if (token != NULL) {
            strcpy(lockedType, token);
        } else {
            if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: lockedType is NULL\n"))) {
                rc = OUTPUT_ERRORS_FOUND;
            }
            goto endRS12;
        }
        if (strcmp(lockedType, "IMAGE") == 0) {
            // Obtain imageLockedBy
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(imageLockedBy, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: imageLockedBy is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto endRS12;
            }
            snprintf(strMsg, sizeof(strMsg),
                     "Locked type: %s\n"
                     "Image locked by: %s\n",
                     lockedType, imageLockedBy);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto endRS12;
            }
        } else {
            snprintf(strMsg, sizeof(strMsg), "Locked type: %s\n", lockedType);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto endRS12;
            }
        }

        for (i = 0; i < output->imageDevLockInfoRecordCount; i++) {
            memset(tempBuff, 0x00, 14);
            devAddressDevLockedBySize = strlen((char *)output->lockDevList[i].devAddressDevLockedBy);
            strncpy(tempBuff, (char *)output->lockDevList[i].devAddressDevLockedBy, devAddressDevLockedBySize);
            trim(tempBuff);
            tempBuff[devAddressDevLockedBySize + 1] = '\0';
            // Get devAddress
            token = strtok_r(tempBuff, blank, &buffer);
            if (token != NULL) {
                strcpy(devAddress, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error devAddress is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto endRS12;
            }

            // Obtain devLockedBy
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(devLockedBy, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: devLockedBy is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto endRS12;
            }

            snprintf(strMsg, sizeof(strMsg),
                     "Device address: %s\n"
                     "Device locked by: %s\n\n",
                     devAddress, devLockedBy);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto endRS12;
            }
        }
        endRS12:
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
    } else if ((output->common.returnCode == 0) && (output->common.reasonCode == 24)) {
        DOES_CALLER_WANT_RC_HEADER_SMAPI_RC0_RS(vmapiContextP, output->common.returnCode, output->common.reasonCode);

        printf("%s is Unlocked...\n", image);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Lock_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }

    return rc;
}

int imageMDISKLinkQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_MDISK_Link_Query";
    int rc;
    int i;
    int imageCount;
    int option;
    char *token;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    char * blank = " ";
    char systemName[8 + 1];
    char user[8 + 1];
    char vaddr[4 + 1];
    char accessMode[5 + 1];
    char * image = NULL;
    char * vdev = NULL;
    vmApiImageMDISKLinkQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:k:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                vdev  = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_MDISK_Link_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_MDISK_Link_Query [-T] image_name -k vdev\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_MDISK_Link_Query to query the links to an image's MDISK.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a virtual dasd link is being\n"
                    "          queried.\n"
                    "    -k    A quoted strings 'VDEV=' followed by the VDEV address of the virtual\n"
                    "          DASD which is being queried for links. This is a required parameter.\n");

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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !vdev) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_MDISK_Link_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, vdev, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_MDISK_Link_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_MDISK_Link_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        // Print out directory entry
    	imageCount = output->mdiskLinkCount;
        if (imageCount > 0) {
            // Have the images now parse them
            for (i = 0; i < imageCount; i++) {
            	// Obtain systemName
                token = strtok_r(output->mdiskLinkList[i].vmapiString, blank, &buffer);
                if (token != NULL) {
                    strcpy(systemName, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: systemName is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Obtain user
                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(user, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: user is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Obtain vaddr
                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(vaddr, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: vaddr is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                // Obtain accessMode
                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(accessMode, token);
                } else {
                    printf("ERROR: accessMode is NULL\n");
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: accessMode is NULL\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                         "System name: %s\n"
                         "User: %s\n"
                         "Vaddr: %s\n"
                         "Access Mode: %s\n",
                          systemName, user, vaddr, accessMode);
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

int imageNameQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Name_Query_DM";
    int rc;
    int option;
    vmApiImageNameQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Name_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Name_Query_DM\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Name_Query_DM to obtain a list of defined virtual images.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    rc = smImage_Name_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            "FOOBAR",  // Does not matter what image name is used
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Name_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Name_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out image names
        int i;
        int n = output->nameCount;
        for (i = 0; i < n; i++) {
            printf("%s\n", output->nameList[i]);
        }
    }
    return rc;
}

int imagePasswordSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Password_Set_DM";
    int rc;
    int option;
    char * image = NULL;
    char * password = "";
    vmApiImagePasswordSetDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tp";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'p':
                password = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Password_Set_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Password_Set_DM [-T] image_name [-p] password\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Password_Set_DM to set or change a virtual image's password.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the password is being set\n"
                    "    -p    The password or passphrase to set for the image\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !password) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Setting %s's password... ", image);

    rc = smImage_Password_Set_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, strlen(password), password, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Password_Set_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Password_Set_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imagePause(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Pause";
    int rc;
    int option;
    char * image = NULL;
    char * pauseOrBegin = "";
    char queryData[80];
    char * myUserid = NULL;
    char * saveptr;
    FILE *fp;
    vmApiImagePauseOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:k:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'k':
                pauseOrBegin = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Pause\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Pause [-T] image_name [-k] 'PAUSE=YES|NO'\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Pause to halt processing in a virtual image or continue\n"
                    "  processing that was paused.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the password is being set\n"
                    "    -k    The quoted string PAUSE=YES to halt processing or PAUSE=NO to start.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !pauseOrBegin) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Check that the image being paused is not this Linux image
    fp = popen("sudo /sbin/vmcp q userid", "r");
    if (fp == NULL) {
        printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
        printf("ERROR: Failed to identify the user");
        return 1;
    }
    fgets(queryData, sizeof(queryData)-1, fp);
    pclose(fp);

    myUserid = strtok_r(queryData, " ", &saveptr);
    if (strcasecmp(myUserid, image) == 0) {
        printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
        printf("ERROR: Cannot specify image %s for this command\n", image);
        return 1;
    }

    if (strcmp(pauseOrBegin, "PAUSE=YES") == 0) {
        // If they want special output header as first output, then we need to pass this
        // string on RC call so it is handled correctly for both cases.
        snprintf(strMsg, sizeof(strMsg), "Halting processing on %s... ", image);
    } else  if (strcmp(pauseOrBegin, "PAUSE=NO") == 0) {
        snprintf(strMsg, sizeof(strMsg), "Resuming processing on %s... ", image);
    } else {
        printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, strMsg, 0);
        printf("Invalid Image_Pause action\n");
        return 1;
    }
    rc = smImage_Pause(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, pauseOrBegin, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Pause", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Pause", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageQueryActivateTime(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Query_Activate_Time";
    int rc;
    int option;
    int format = 0;
    char * image = NULL;
    vmApiImageQueryActivateTimeOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'f':
                format = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Query_Activate_Time\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Query_Activate_Time [-T] image_name [-f] format\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Query_Activate_Time to obtain the date and time when a virtual\n"
                    "  image was activated.\n\n"
                    "  The following options are required:\n"
                    "    -T    To specify which virtual image's activation date and time is\n"
                    "          being queried\n"
                    "    -f    The format of the date stamp that is returned:\n"
                    "            1: mm/dd/yy\n"
                    "            2: mm/dd/yyyy\n"
                    "            3: yy-mm-dd\n"
                    "            4: yyyy-mm-dd\n"
                    "            5: dd/mm/yy\n"
                    "            6: dd/mm/yyyy\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !format) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Query_Activate_Time(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, format, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Query_Activate_Time", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Query_Activate_Time", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char * image = output->imageName;
        char * actDate = output->activationDate;
        char * actTime = output->activationTime;
        printf("%s was activated on %s at %s\n", image, actDate, actTime);
    }
    return rc;
}

/**
 * Use Image_Query_DM to obtain a virtual image's directory entry
 */
int imageQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Query_DM";
    int rc;
    int i;
    int option;
    char * image = NULL;
    vmApiImageQueryDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Query_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Query_DM to obtain a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being queried\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Query_DM(vmapiContextP, "", 0, "", image, &output, false);

    if (rc) {
        printAndLogProcessingErrors("Image_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out directory entry
        int recCount = output->imageRecordCount;
        int recLen = output->imageRecordList[0].imageRecordLength - 8;
        char line[recLen], chs[4];
        if (recCount > 0) {
            for (i = 0; i < recCount; i++) {
                memset(line, 0, recLen);
                memcpy(line, output->imageRecordList[i].imageRecord, recLen);
                trim(line);
                printf("%s\n", line);
            }
        }
    }
    return rc;
}

int imageRecycle(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Recycle";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageRecycleOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Recycle\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Recycle [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Recycle to deactivate and then reactivate a virtual image or\n"
                    "  list of virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being recycled\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Recycling %s... ", image);

    rc = smImage_Recycle(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Recycle", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Recycle", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageReplaceDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Replace_DM";
    // IMPORTANT: Image must be locked before it can be replaced
    int rc;
    int option;
    char * image = NULL;
    char * userEntryFile = NULL;
    int userEntryStdin = 0;

    FILE * fp;
    int recordCount = 0;
    int c;
    char * ptr;

    int i = 0, LINE_SIZE = 72;
    char buffer[100][LINE_SIZE];

    vmApiImageReplaceDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tf";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:sh?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;
            case 'f':
                userEntryFile = optarg;
                break;
            case 's':
                userEntryStdin = 1;
                break;
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Replace_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Replace_DM [-T] image_name [-f] user_entry_file\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Replace_DM to replace a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be replaced\n"
                    "    -f    The file containing the updated directory entry. Not required\n"
                    "          if a directory entry is provided from stdin.\n"
                    "    -s    Read the updated directory entry from stdin. Not required if a\n"
                    "          directory entry file is provided.\n");
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
            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || (!userEntryFile && !userEntryStdin)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    if (!userEntryStdin) {
        // Open the user entry file
        fp = fopen(userEntryFile, "r");
        if (NULL == fp) {
            printAndLogProcessingErrors(MY_API_NAME, PROCESSING_ERROR, vmapiContextP, "", 0);
            printf("\nERROR: Failed to open file %s\n", userEntryFile);
            return 2;
        }

        // Count the number of lines and set the record count to it
        while ((c = fgetc(fp)) != EOF) {
            if (c == '\n') {
                recordCount++;
            }
        }

        // Reset position to start of file
        rewind(fp);
    } else {
        // Read in user entry from stdin
        while (fgets(buffer[i], LINE_SIZE, stdin) != NULL) {
            // Replace newline with null terminator
            ptr = strstr(buffer[i], "\n");
            if (ptr != NULL) {
                strncpy(ptr, "\0", 1);
                // Count the number of lines and set the record count to it
                recordCount++;
            }
            i++;
        }
    }

    // Create image record
    vmApiImageRecord record[recordCount];
    char line[recordCount][LINE_SIZE];
    if (!userEntryStdin) {
        // Read in user entry from file
        while (fgets(line[i], LINE_SIZE, fp) != NULL) {
            // Replace newline with null terminator
            ptr = strstr(line[i], "\n");
            if (ptr != NULL) {
                strncpy(ptr, "\0", 1);
            }
            record[i].imageRecordLength = strlen(line[i]);
            record[i].imageRecord = line[i];
            i++;
        }

        // Close file
        fclose(fp);
    } else {
        // Read in user entry from stdin buffer
        for (i = 0; i < recordCount; i++) {
            record[i].imageRecordLength = strlen(buffer[i]);
            record[i].imageRecord = buffer[i];
        }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Replacing %s's directory entry... ", image);

    rc = smImage_Replace_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, recordCount,    (vmApiImageRecord *) record,  // Image record
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Replace_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Replace_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageSCSICharacteristicsDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_SCSI_Characteristics_Define_DM";
    int rc;
    int option;
    char * image = NULL;
    char * bootProgram = NULL;
    char * logicalBlock = NULL;
    char * lun = NULL;
    char * portName = NULL;
    int scpType = -1;
    char * scpData = NULL;
    vmApiImageScsiCharacteristicsDefineDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tbklpsd";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:b:k:l:p:s:d:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'b':
                bootProgram = optarg;
                break;

            case 'k':
                logicalBlock = optarg;
                break;

            case 'l':
                lun = optarg;
                break;

            case 'p':
                portName = optarg;
                break;

            case 's':
                scpType = atoi(optarg);
                break;

            case 'd':
                scpData = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_SCSI_Characteristics_Define_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_SCSI_Characteristics_Define_DM [-T] image_name\n"
                    "    [-b] boot_program [-k] logical_block [-l] lun [-p] port_name\n"
                    "    [-s] scp_data_type [-d] scp_data\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_SCSI_Characteristics_Define_DM to define or change the\n"
                    "  location of a program to be loaded as a result of an FCP\n"
                    "  list-directed IPL, and the data to be passed to the loaded program,\n"
                    "  in a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The target image name whose LOADDEV is being set\n"
                    "    -b    The boot program number (which must be a value in the range\n"
                    "          0 to 30), or the keyword 'DELETE' to delete the existing\n"
                    "          boot program number. If null, the boot program number will\n"
                    "          be unchanged\n"
                    "    -k    The logical-block address of the boot record, or the keyword\n"
                    "          'DELETE' to delete the existing logical-block address. If\n"
                    "          null, the logical-block address will be unchanged\n"
                    "    -l    The logical unit number, or the keyword 'DELETE' to delete\n"
                    "          the existing logical unit number. If null, the logical unit\n"
                    "          number will be unchanged\n"
                    "    -p    The port name, or the keyword 'DELETE' to delete the existing\n"
                    "          port name. If null, the port name will be unchanged\n"
                    "    -s    The type of data specified in the SCP_data parameter, as\n"
                    "          follows:\n"
                    "            0: Unspecified ~ No data\n"
                    "            1: DELETE ~ Delete the SCP_data for the image\n"
                    "            2: EBCDIC ~ EBCDIC (codepage 924) data\n"
                    "            3: HEX ~ UTF-8 encoded hex data\n"
                    "    -d    The SCP data\n"
                    "            If the -s parameter is 0 or 1 then do not use this parameter\n"
                    "            If the -s parameter is 2 or 3 then you must use this parameter\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !bootProgram || !logicalBlock || !lun || !portName || (scpType < 0) ) {      
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    if ( (scpType == 2) || (scpType == 3) ) {
        if ( !scpData ) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
        char ebcdicString[strlen(scpData)];
        convertASCIItoEBCDIC(vmapiContextP, scpData, ebcdicString);
        memmove(scpData, ebcdicString, strlen(scpData));
    }
    else {
         if ( !scpData ) {
            scpData = "";
         }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining location of program to be loaded... ");

    rc = smImage_SCSI_Characteristics_Define_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, bootProgram, logicalBlock, lun, portName, scpType, strlen(scpData), scpData, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_SCSI_Characteristics_Define_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_SCSI_Characteristics_Define_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageSCSICharacteristicsQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_SCSI_Characteristics_Query_DM";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageScsiCharacteristicsQueryDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_SCSI_Characteristics_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_SCSI_Characteristics_Query_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_SCSI_Characteristics_Query_DM to obtain the location of a program\n"
                    "  to be loaded as a result of an FCP list-directed IPL, and the data to be\n"
                    "  passed to the loaded program, from a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The target userid whose LOADDEV is being queried\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_SCSI_Characteristics_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_SCSI_Characteristics_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_SCSI_Characteristics_Query_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        char * bootProgram = output->bootProgramNumber;
        char * logicalBlock = output->br_LBA;
        char * lun = output->lun;
        char * portName = output->port;
        char * scpData = output->scpData;
        

        char* scpDataType = "Unspecified                 "; 
        if ((int)output->scpDataType == 0) 
           scpDataType = "Unspecified                 ";
        else if ((int)output->scpDataType == 2)
           scpDataType = "EBCDIC (codepage 924) data  ";
        else if ((int)output->scpDataType == 3)
           scpDataType = "HEX (UTF-8) encoded hex data";

        printf("Boot program number: %s\n"
            "Logical-block address of the boot record: %s\n"
            "Logical unit number: %s\n"
            "Port name: %s\n"
            "Type of data: %s\n", bootProgram, logicalBlock, lun, portName, scpDataType);

        if (((int)output->scpDataType == 2) || ((int)output->scpDataType == 3)) { 
           int  scpDataLength = strlen(scpData);
           char ebcdicString[scpDataLength];
           convertEBCDICtoASCII(vmapiContextP, scpData, ebcdicString);
           printf("SCP Data: %s\n",ebcdicString);
        }
        else {
           printf("SCP Data: (null)\n");
        }

    }
    return rc;
}

int imageStatusQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Status_Query";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageStatusQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Status_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Status_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Status_Query to determine whether virtual images are\n"
                    "  active (logged on or logged on disconnected) or inactive.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being queried\n"
                    "          You may enter '*' to get the list of all active servers\n ");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Status_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Status_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Status_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out directory entry
        int imageCount = output->imageNameCount;
        if (imageCount > 0) {
            int i;
            for (i = 0; i < imageCount; i++) {
                printf("%s\n", output->imageNameList[i].imageName);
            }
        }
    }

    return rc;
}

int imageUnlockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Unlock_DM";
    int rc;
    int option;
    char * image = NULL;
    char * address = "";
    vmApiImageUnlockDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Unlock_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Unlock_DM [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Unlock_DM to unlock a virtual image's directory entry\n"
                    "  or a specific device in a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be unlocked\n"
                    "  The following options are optional:\n"
                    "    -v    The virtual address of the device being unlocked\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    if (strlen(address) == 0) {
        // If they want special output header as first output, then we need to pass this
        // string on RC call so it is handled correctly for both cases.
        snprintf(strMsg, sizeof(strMsg), "Unlocking %s's directory entry... ", image);
    } else {
        snprintf(strMsg, sizeof(strMsg), "Unlocking %s's device %s... ", image, address);
    }
    rc = smImage_Unlock_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, address,  // Image name, device virtual address
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Unlock_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Unlock_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int imageVolumeAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Add";
    int rc;
    int option;
    char * image = NULL;
    char * address = "";
    char * volId = "";
    char * sysConfName = "";
    char * sysConfType = "";
    char * parmDiskOwner = "";
    char * parmDiskNumber = "";
    char * parmDiskPass = "";
    char * altSysConfName = "";
    char * altSysConfType = "";
    char * altParmDiskNumber = "";
    char * altParmDiskOwner = "";
    char * altParmDiskPass = "";
    vmApiImageVolumeAddOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvlstopwcynmx";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:l:s:t:o:p:w:c:y:n:m:x:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'l':
                volId = optarg;
                break;

            case 's':
                sysConfName = optarg;
                break;

            case 't':
                sysConfType = optarg;
                break;

            case 'o':
                parmDiskOwner = optarg;
                break;

            case 'p':
                parmDiskNumber = optarg;
                break;

            case 'w':
                parmDiskPass = optarg;
                break;

            case 'c':
                altSysConfName = optarg;
                break;

            case 'y':
                altSysConfType = optarg;
                break;

            case 'n':
                altParmDiskOwner = optarg;
                break;

            case 'm':
                altParmDiskNumber = optarg;
                break;

            case 'x':
                altParmDiskPass = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Add\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Add [-T] image_name [-v] virtual_address\n"
                    "    [-l] volid [-s] sys_conf_name [-t] sys_conf_type [-o] parm_disk_owner\n"
                    "    [-p] parm_disk_number [-w] parm_disk_password [-c] alt_sys_conf_name\n"
                    "    [-y] alt_sys_conf_type [-n] alt_parm_disk_owner [-m] alt_parm_disk_number\n"
                    "    [-x] alt_parm_disk_password\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Add to add a DASD volume to be used by virtual images\n"
                    "  to the z/VM system configuration file.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to which a volume is being added\n"
                    "    -v    The virtual device number of the device\n"
                    "    -l    The DASD volume label\n"
                    "    -s    File name of system configuration file. The default is 'SYSTEM'.\n"
                    "    -t    File type of system configuration file. The default is 'CONFIG'.\n"
                    "    -o    Owner of the parm disk. The default is 'MAINT''."
                    "    -p    Number of the parm disk as defined in the VSMWORK1 directory\n"
                    "    -w    Multiwrite password for the parm disk. The default is ','.\n"
                    "    -c    File name of the second, or alternative, system configuration file\n"
                    "    -y    File type of the second, or alternative, system configuration file.\n"
                    "          The default is 'CONFIG'.\n"
                    "    -n    Owner of the second, or alternative, parm disk.\n"
                    "          The default is 'MAINT'.\n"
                    "    -m    Number of the second, or alternative, parm disk.\n"
                    "          The default is 'CF2'.\n"
                    "    -x    Multiwrite password for the alternate parm disk.\n"
                    "          The default is ','.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address || !volId || !sysConfName || !sysConfType || !parmDiskOwner || !parmDiskNumber
            || !parmDiskPass || !altSysConfName || !altSysConfType || !altParmDiskOwner || !altParmDiskNumber
            || !altParmDiskPass) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding DASD volume to the z/VM system configuration... ");

    rc = smImage_Volume_Add(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, address, volId, sysConfName, sysConfType, parmDiskOwner, parmDiskNumber, parmDiskPass,
            altSysConfName, altSysConfType, altParmDiskOwner, altParmDiskNumber, altParmDiskPass, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Add", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Add", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageVolumeDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * address = "";
    char * volId = "";
    char * sysConfName = "";
    char * sysConfType = "";
    char * parmDiskOwner = "";
    char * parmDiskNumber = "";
    char * parmDiskPass = "";
    char * altSysConfName = "";
    char * altSysConfType = "";
    char * altParmDiskNumber = "";
    char * altParmDiskOwner = "";
    char * altParmDiskPass = "";
    vmApiImageVolumeDeleteOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvlstopwcynmx";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:v:l:s:t:o:p:w:c:y:n:m:x:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                address = optarg;
                break;

            case 'l':
                volId = optarg;
                break;

            case 's':
                sysConfName = optarg;
                break;

            case 't':
                sysConfType = optarg;
                break;

            case 'o':
                parmDiskOwner = optarg;
                break;

            case 'p':
                parmDiskNumber = optarg;
                break;

            case 'w':
                parmDiskPass = optarg;
                break;

            case 'c':
                altSysConfName = optarg;
                break;

            case 'y':
                altSysConfType = optarg;
                break;

            case 'n':
                altParmDiskOwner = optarg;
                break;

            case 'm':
                altParmDiskNumber = optarg;
                break;

            case 'x':
                altParmDiskPass = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Delete [-T] image_name [-v] virtual_address\n"
                    "    [-l] volid [-s] sys_conf_name [-t] sys_conf_type [-o] parm_disk_owner\n"
                    "    [-p] parm_disk_number [-w] parm_disk_password [-c] alt_sys_conf_name\n"
                    "    [-y] alt_sys_conf_type [-n] alt_parm_disk_owner [-m] alt_parm_disk_number\n"
                    "    [-x] alt_parm_disk_password\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Delete to delete a DASD volume definition from the z/VM\n"
                    "  system configuration file.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image being activated\n"
                    "    -v    The virtual device number of the device\n"
                    "    -l    The DASD volume label\n"
                    "    -s    File name of system configuration file. The default is 'SYSTEM'.\n"
                    "    -t    File type of system configuration file. The default is 'CONFIG'.\n"
                    "    -o    Owner of the parm disk. The default is 'MAINT''."
                    "    -p    Number of the parm disk as defined in the VSMWORK1 directory\n"
                    "    -w    Multiwrite password for the parm disk. The default is ','.\n"
                    "    -c    File name of the second, or alternative, system configuration file\n"
                    "    -y    File type of the second, or alternative, system configuration file.\n"
                    "          The default is 'CONFIG'.\n"
                    "    -n    Owner of the second, or alternative, parm disk.\n"
                    "          The default is 'MAINT'.\n"
                    "    -m    Number of the second, or alternative, parm disk.\n"
                    "          The default is 'CF2'.\n"
                    "    -x    Multiwrite password for the alternate parm disk.\n"
                    "          The default is ','.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !address || !volId || !sysConfName || !sysConfType || !parmDiskOwner || !parmDiskNumber
            || !parmDiskPass || !altSysConfName || !altSysConfType || !altParmDiskOwner || !altParmDiskNumber
            || !altParmDiskPass) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting DASD volume definition from the z/VM system configuration... ");

    rc = smImage_Volume_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, address, volId, sysConfName, sysConfType, parmDiskOwner, parmDiskNumber, parmDiskPass,
            altSysConfName, altSysConfType, altParmDiskOwner, altParmDiskNumber, altParmDiskPass, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageVolumeShare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Share";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    int arrayBytes = 0;
    int foundRequiredParm = 0;
    char ** entryArray;
    const char * optString = "-T:k:h?";
    vmApiImageVolumeShareOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

    // Count up the max number of arguments to create the array
    while ((option = getopt(argC, argV, optString)) != -1) {
        arrayBytes = arrayBytes + sizeof(*entryArray);
    }
    optind = 1;  // Reset optind so getopt can rescan arguments
    if (arrayBytes > 0) {
        entryArray = malloc(arrayBytes);
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
                if (strstr(optarg, "img_vol_addr"))foundRequiredParm=1;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Share\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Share [-T] image_name\n"
                    "   [-k] 'img_vol_addr=value' \n"
                    "   [-k] 'share_enable=value' \n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Share to to indicate a full-pack minidisk is to be shared by\n"
                    "  the users of many real and virtual systems.\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine whose volumes are being shared.\n"
                    "    -k    A quoted  'img_vol_addr=value' \n"
                    "          The real device number of the volume to be shared.\n"
                    "  The following options are optional:\n"
                    "    -k    A quoted  'share_enable=value' \n"
                    "          value: ON Turns on sharing of the specified full-pack minidisk.\n"
                    "          value: OFF Turns off sharing of the specified full-pack minidisk.\n"
                    "          If unspecified, the default is ON.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
        }

    if (!image || !entryCount || !foundRequiredParm) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (arrayBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }

        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Indicating a full-pack minidisk is to be shared... ");

    rc = smImage_Volume_Share(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);
    FREE_MEMORY_CLEAR_POINTER(entryArray);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Share", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Share", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageVolumeSpaceDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Space_Define_DM";
    int rc;
    int option;
    int function = 0;
    int startCylinder = -1;
    int regionSize = -1;
    int deviceType = 0;
    char * image = NULL;
    char * regionName = NULL;
    char * volumeId = NULL;
    char * groupName = NULL;
    vmApiImageVolumeSpaceDefineDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tfgvszpy";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:g:v:s:z:p:y:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'f':
                function = atoi(optarg);
                break;

            case 'g':
                regionName = optarg;
                break;

            case 'v':
                volumeId = optarg;
                break;

            case 's':
                startCylinder = atoi(optarg);
                break;

            case 'z':
                regionSize = atoi(optarg);
                break;

            case 'p':
                groupName = optarg;
                break;

            case 'y':
                deviceType = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Space_Define_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Space_Define_DM [-T] image_name [-f] function_type\n"
                    "    [-g] region_name [-v] vol_id [-s] start_cylinder [-z] size"
                    "    [-p] group_name [-y] device_type\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Space_Define_DM to define space on a DASD\n"
                    "  volume to be allocated by the directory manager for use by\n"
                    "  virtual images.\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name\n"
                    "    -f    Function type:\n"
                    "            1: Define region as specified. image_volid,\n"
                    "               region_name, start_cylinder, and size are\n"
                    "               required for this function\n"
                    "            2: Define region as specified and add to group.\n "
                    "               image_vol_id, region_name, start_cylinder, size,\n"
                    "               and group_name are required for this function\n"
                    "            3: Define region as full volume. vol_id and\n"
                    "               region_name are required for this function\n"
                    "            4: Define region as full volume and add to group.\n"
                    "               vol_id, region_name, and group_name are\n"
                    "               required for this function\n"
                    "            5: Add existing region to group. (This function also\n"
                    "               defines the group if it does not already exist.)\n"
                    "               region_name and Group are required for this function.\n"
                    "    -g    The region to be defined\n"
                    "    -v    The DASD volume label\n"
                    "    -s    The starting point of the region\n"
                    "    -z    The number of cylinders to be used by region\n"
                    "    -p    The name of the group to which the region is assigned\n"
                    "    -y    The device type designation:\n"
                    "            0: Unspecified\n"
                    "            1: 3390\n"
                    "            2: 9336\n"
                    "            3: 3380\n"
                    "            4: FB-512\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !function || !regionName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Check function value to determining which parameters are required
    if (function == 1) {
        if (!volumeId || startCylinder == -1 || regionSize == -1) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
    } else if (function == 2) {
        if (!volumeId || startCylinder == -1 || regionSize == -1 || !groupName) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
    } else if (function == 3) {
        if (!volumeId) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
    } else if (function == 4) {
        if (!volumeId || !groupName) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
    } else if (function == 5) {
        if (!groupName) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: Missing required options\n");
            return 1;
        }
    } else {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: function value is invalid\n");
        return 1;
    }

    // make sure that no NULL values are sent
    if (image == NULL) {
        image = "";
    }
    if (regionName == NULL) {
        regionName = "";
    }
    if (volumeId == NULL) {
        volumeId = "";
    }
    if (groupName == NULL) {
        groupName = "";
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining space on DASD volume to be allocated by directory manager... ");

    rc = smImage_Volume_Space_Define_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, function, regionName, volumeId, startCylinder, regionSize,
            groupName, deviceType, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Space_Define_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Space_Define_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    return rc;
}

int imageVolumeSpaceDefineExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Space_Define_Extended_DM";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiImageVolumeSpaceDefineExtendedDmOutput* output;

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
                printf("NAME\n"
                    "  Image_Volume_Space_Define_Extended_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Space_Define_Extended_DM [-T] image_name\n"
                    "    [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Space_Define_Extended_DM to define space on a DASD volume to\n"
                    "  be allocated by the directory manager for use by virtual images\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name.\n"
                    "    -k    Quoted 'keyword=value' items to describe the type of space to be added.\n"
                    "          refer to the System Management Application Programming manual for\n"
                    "          additional details.\n"
                    "          'function_type=1|2|3|4|5'\n"
                    "             1: Define region as specified. Additional parameters required for\n"
                    "                this function:\n"
                    "                image_vol_id=value, region_name=value, start_cylinder=value,\n"
                    "                v_size=value\n"
                    "             2: Define region as specified and add to group. Additional\n"
                    "                parameters required for this function:\n"
                    "                image_vol_id=value, region_name=value, start_cylinder=value,\n"
                    "                v_size=value, group_name=value\n"
                    "             3: Define region as full volume. Additional parameters required for\n"
                    "                this function:\n"
                    "                image_vol_id=value, region_name=value\n"
                    "             4: Define region as full volume and add to group. Additional\n"
                    "                parameters required for this function:\n"
                    "                image_vol_id=value, region_name=value, group_name=value\n"
                    "             5: Add existing region to group. (This function also defines the\n"
                    "                group if it does not already exist.) Additional parameters\n"
                    "                required for this function:\n"
                    "                region_name=value, group_name=value\n\n"
                    "          'region_name=value': (string,0-8,char42) The region to be defined.\n"
                    "          'image_vol_id=value': (string,0-6,char42) The DASD volume label.'\n"
                    "          'start_cylinder=value': (string,0-10,char10) The starting point of the\n"
                    "             region. If the device is not mounted and attached to the system,\n"
                    "             then this parameter is required along with the size=value and \n"
                    "             device_type=value parameters.\n"
                    "          'size=value': (string,0-10,char10) The number of cylinders to be used\n"
                    "             by region. If the device is not mounted and attached to the system,\n"
                    "             then this parameter is required along with the start_cylinder=value\n"
                    "             and device_type=value parameters.\n"
                    "          'group_name=value': (string,0-8,char42) The name of the group to which\n"
                    "             the region is assigned.\n"
                    "          'device_type=value': (string,0-1,char10) The device type designation.\n"
                    "             Valid values are:\n"
                    "               0: Unspecified\n "
                    "               1: 3390\n"
                    "               2: 9336\n"
                    "               3: 3380\n"
                    "               4: FB-512\n"
                    "          'alloc_method=value': (string,0-1,char10) The allocation method.\n"
                    "             Valid values are:\n"
                    "               0: Unspecified\n"
                    "               1: Specifies the linear scanning method, in which the first region\n"
                    "                  within a group is scanned for allocation until full, then the\n"
                    "                  second region, and so on until the last region is reached.\n"
                    "               2: Specifies the rotating scanning method, in which the first\n"
                    "                  region within a group is scanned for the first allocation, then\n"
                    "                  the second region for the second allocation, and so on with each\n"
                    "                  new allocation starting at the next region.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
        }

    if (!image || entryCount < 3) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining space on DASD volume to be allocated by directory manager... ");

    rc = smImage_Volume_Space_Define_Extended_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Space_Define_Extended_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Space_Define_Extended_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }

    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}

int imageVolumeSpaceQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Space_Query_DM";
    int rc;
    int option;
    int query = 0;
    int entry = 0;
    char * image = NULL;
    char * entryName = "";
    vmApiImageVolumeSpaceQueryDmOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tqen";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:q:e:n:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'q':
                query = atoi(optarg);
                break;

            case 'e':
                entry = atoi(optarg);
                break;

            case 'n':
                entryName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Space_Query_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Space_Query_DM [-T] image_name [-q] query_type \n"
                    "    [-e] entry_type [-n] entry_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Space_Query_DM to query how space on a DASD volume\n"
                    "  is allocated by the directory manager.\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name\n"
                    "    -q    Query type:\n"
                    "            1: Query volume definition\n"
                    "            2: Query amount of free space available\n"
                    "            3: Query amount of space used\n"
                    "    -e    Entry type:\n"
                    "            1: Query specified volume\n"
                    "            2: Query specified region\n"
                    "            3: Query specified group\n"
                    "  The following options are optional:\n"
                    "    -n    Entry name\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !query || !entry) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Handle return code and reason code
    rc = smImage_Volume_Space_Query_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, query, entry, entryName, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Space_Query_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Space_Query_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out image volumes
        int i, length;
        int recCount = output->recordCount;
        int p = 0;
        for (i = 0; i < recCount; i++) {
            length = output->recordList[i].imageRecordLength;
            printf("%.*s\n", length, output->recordList[0].imageRecord + p);
            p = p + length;
        }
    }

    return rc;
}

int imageVolumeSpaceQueryExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Space_Query_Extended_DM";
    // Parse the command-line arguments
    int option;
    int rc;
    char * image = NULL;
    int entryCount = 0;
    int argBytes = 0;
    int i;
    const char * optString = "-T:k:h?";
    char ** entryArray;
    vmApiVolumeSpaceQueryExtendedDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

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
                printf("NAME\n"
                    "  Image_Volume_Space_Query_Extended_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Space_Query_Extended_DM [-T] image_name\n"
                    "    [-k] 'query_type=n1' [-k] 'entry_type=n2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Space_Query_Extended_DM to query how space on a DASD volume\n"
                    "  is allocated by the directory manager.\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name.\n"
                    "    -k    Quoted 'keyword=value' items to describe the type of space to be added.\n"
                    "          Two of these items are required and one is optional:\n"
                    "      'query_type=1|2|3':\n"
                    "        1: DEFINITION Query volume definition for the specified image\n"
                    "           device.\n"
                    "        2: FREE Query amount of free space available on the specified\n"
                    "           image device.\n"
                    "        3: USED Query amount of space used on the specified image device\n"
                    "           image_vol_id=value, region_name=value\n"
                    "      'entry_type=1|2|3':\n"
                    "        1: VOLUME - Query specified volume.\n"
                    "        2: REGION - Query specified region.\n"
                    "        3: GROUP - Query specified group.\n"
                    "  The following options are optional:\n"
                    "    'entry_names=value': string,0-255,char42 plus blank) Names of groups,\n"
                    "      regions or volumes to be queried, separated by blanks. An asterisk (*)\n"
                    "      specifies all areas of the requested type. If unspecified, * is the\n"
                    "      default.\n"
                    "  Refer to the System Management Application Programming manual for additional\n"
                    "  details.\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                FREE_MEMORY_CLEAR_POINTER(entryArray);
                return 1;
        }

    if (!image || entryCount < 2) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        if (argBytes > 0) {
            FREE_MEMORY_CLEAR_POINTER(entryArray);
        }
        return 1;
    }

    rc = smImage_Volume_Space_Query_Extended_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Space_Query_Extended_DM", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Space_Query_Extended_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out image volume information
        entryCount = output->volumeSpaceCount;
        for (i = 0; i < entryCount; i++) {
            printf("%s\n", output->volumeSpaceList[i].vmapiString);
        }
    }
    FREE_MEMORY_CLEAR_POINTER(entryArray);
    return rc;
}


int imageVolumeSpaceRemoveDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Volume_Space_Remove_DM";
    int rc;
    int option;
    int functionType = 0;
    char * image = NULL;
    char * regionName = "";
    char * volId = "";
    char * groupName = "";
    vmApiImageVolumeSpaceRemoveDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tfrvg";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:f:r:v:g:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'f':
                functionType = atoi(optarg);
                break;

            case 'r':
                regionName = optarg;
                break;

            case 'v':
                volId = optarg;
                break;

            case 'g':
                groupName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Volume_Space_Remove_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Volume_Space_Remove_DM [-T] image_name [-f] function_type\n"
                    "    [-r] region_name [-v] image_volid [-g] group_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Volume_Space_Remove_DM to remove the directory manager's\n"
                    "  space allocations from a DASD volume.\n\n"
                    "  The following options are required:\n"
                    "    -T    Target image or authorization entry name\n"
                    "    -f    Function type:\n"
                    "            1: Remove named region. RegionName is required for this function.\n"
                    "            2: Remove named region from group. region_name and group_name are\n"
                    "               required for this function.\n"
                    "            3: Remove named region from all groups. region_name is required\n"
                    "               for this function.\n"
                    "            4: Remove all regions from specific volume. image_volid is required\n"
                    "               for this function.\n"
                    "            5: Remove all regions from specific volume and group. image_volid\n"
                    "               and group_name are required for this function.\n"
                    "            6: Remove all regions from specific volume and all groups.\n"
                    "               image_volid is required for this function.\n"
                    "            7: Remove entire group. group_name is required for this function.\n"
                    "    -r    The region to be defined\n"
                    "    -v    The DASD volume label\n"
                    "    -g    The name of the group to which the region is assigned\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image || !functionType) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Volume_Space_Remove_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, functionType, regionName, volId, groupName, &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Volume_Space_Remove_DM", rc, vmapiContextP, "", 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Volume_Space_Remove_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }

    return rc;
}


int imageConsoleGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Image_Console_Get";
    int rc;
    int option;
    char * image = NULL;
    vmApiImageConsoleGetOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "-T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Image_Console_Get\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Console_Get [-T] image_name \n\n"
                    "DESCRIPTION\n"
                    "  Use Image_Console_Get to get a virtual image's console log\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image to be get console from\n");
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

            case 1:  // API name type data(other non option element key data)
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
        }

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smImage_Console_Get(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, // Image name
            &output);

    if (rc) {
        printAndLogProcessingErrors("Image_Console_Get", rc, vmapiContextP, "", 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Image_Console_Get", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    }
    return rc;
}
