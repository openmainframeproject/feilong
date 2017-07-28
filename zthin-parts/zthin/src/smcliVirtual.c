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

#include "smcliVirtual.h"
#include "wrapperutils.h"

int virtualChannelConnectionCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Channel_Connection_Create";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    char * coupledImage = NULL;
    char * coupledVirtualAddress = NULL;
    vmApiVirtualChannelConnectionCreateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvcd";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:c:d:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'c':
                coupledImage = optarg;
                break;

            case 'd':
                coupledVirtualAddress = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Channel_Connection_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Channel_Connection_Create [-T] image_name [-v] virtual_address\n"
                    "  [-c] coupled_image [-d] coupled_virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Channel_Connection_Create to establish a virtual network\n"
                    "  connection between two active virtual images. A virtual network\n"
                    "  connector (CTCA) is added to each virtual image's configuration if one\n"
                    "  is not already defined.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image obtaining a connection device\n"
                    "    -v    The virtual device number of the network device in the active\n"
                    "          virtual image\n"
                    "    -c    The virtual image name of the target virtual image that is to\n"
                    "          be connected\n"
                    "    -d    The virtual device number of the network device in another\n"
                    "          virtual image\n");
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

    if (!image || !virtualAddress || !coupledImage || !coupledVirtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Establishing a virtual network connection between %s and %s... ", image, coupledImage);

    rc = smVirtual_Channel_Connection_Create(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, coupledImage, coupledVirtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Channel_Connection_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Channel_Connection_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualChannelConnectionCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Channel_Connection_Create_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    char * coupledImage = NULL;
    vmApiVirtualChannelConnectionCreateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvc";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:c:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'c':
                coupledImage = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Channel_Connection_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Channel_Connection_Create_DM [-T] image_image [-v] device_number\n"
                    "    [-c] coupled_image\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Channel_Connection_Create_DM to add a virtual network connection\n"
                    "  between two virtual images to their directory entries. A virtual network\n"
                    "  connector (CTCA) is added to each virtual image's directory entry if one is\n"
                    "  not already defined.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image obtaining a connection device\n"
                    "    -v    The virtual device number of the network device in the active virtual\n"
                    "          image\n"
                    "    -c    The virtual image name of the target virtual image that is to be\n"
                    "          connected.\n");
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

    if (!image || !virtualAddress || !coupledImage) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding a virtual network connection between %s's and %s's directory entries... ", image, coupledImage);

    rc = smVirtual_Channel_Connection_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, coupledImage, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Channel_Connection_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Channel_Connection_Create_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualChannelConnectionDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Channel_Connection_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualChannelConnectionDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Channel_Connection_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Channel_Connection_Delete [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Channel_Connection_Delete to terminate a virtual network connection\n"
                    "  between two active virtual images and to remove the virtual network connector\n"
                    "  (CTCA) from the virtual image's configuration. \n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the connection device is being removed\n"
                    "    -v    The virtual device number of the device to be deleted\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Terminating virtual network connection for %s... ", image);

    rc = smVirtual_Channel_Connection_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Channel_Connection_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Channel_Connection_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualChannelConnectionDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Channel_Connection_Delete_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualChannelConnectionDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Channel_Connection_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Channel_Connection_Delete_DM [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Channel_Connection_Delete_DM to remove a virtual network\n"
                    "  connection from a virtual image's directory entry and to remove the virtual\n"
                    "  network connector (CTCA) from the virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the connection device is\n"
                    "          being removed\n"
                    "    -v    The virtual device number of the device to be deleted\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Terminating virtual network connection from %s's directory entry... ", image);

    rc = smVirtual_Channel_Connection_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Channel_Connection_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Channel_Connection_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterConnectLAN(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Connect_LAN";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    vmApiVirtualNetworkAdapterConnectLanOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvlo";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:l:o:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'l':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Connect_LAN\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Connect_LAN [-T] image_name [-v] virtual_address\n"
                    "    [-l] lan_name [-o] lan_owner\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Connect_LAN to connect an existing virtual\n"
                    "  network adapter on an active virtual image to an existing virtual network\n"
                    "  LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a LAN connection is being created\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -l    The name of the guest LAN segment to connect the virtual image\n"
                    "    -o    The virtual image owning the guest LAN segment to be connected\n");
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

    if (!image || !virtualAddress || !lanName || !lanOwner) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Connecting virtual network adapter at %s to %s... ", virtualAddress, lanName);

    rc = smVirtual_Network_Adapter_Connect_LAN(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, lanName, lanOwner, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Connect_LAN", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Connect_LAN", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterConnectLANDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Connect_LAN_DM";
    int rc;
    int option;
    char * image = NULL;
    char * deviceAddress = NULL;
    char * lanName = "";
    char * lanOwner = "";
    vmApiVirtualNetworkAdapterConnectLanDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvnocm";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:n:o:c:m:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                deviceAddress = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Connect_LAN_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Connect_LAN_DM [-T] image_name\n"
                    "    [-v] virtual_address [-n] lan_name [-o] lan_owner\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Connect_LAN_DM to define a virtual network LAN\n"
                    "  connection for an existing virtual network adapter in a virtual image's\n"
                    "  directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a LAN connection is being created\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -n    The name of the guest LAN segment to connect the virtual image\n"
                    "    -o    The virtual image owning the guest LAN segment to be connected\n");
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

    if (!image || !deviceAddress || !lanName || !lanOwner) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining virtual network LAN connection in %s's directory entry... ", image);

    rc = smVirtual_Network_Adapter_Connect_LAN_DM(vmapiContextP, "", 0, "",
            image, deviceAddress, lanName, lanOwner, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Connect_LAN_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Connect_LAN_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterConnectVswitch(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Connect_Vswitch";
    int rc;
    int option;
    char * image = NULL;
    char * deviceAddress = NULL;
    char * vswitchName = "";
    vmApiVirtualNetworkAdapterConnectVswitchOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvn";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:n:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                deviceAddress = optarg;
                break;

            case 'n':
                vswitchName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Connect_Vswitch\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Connect_Vswitch [-T] image_name\n"
                    "    [-v] virtual_address [-n] vswitch_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Connect_Vswitch to connect an existing virtual "
                    "  network adapter on an active virtual image to an existing virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the user or profile to which virtual network adapter\n"
                    "          virtual switch connection information will be added.\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -n    The name of the virtual switch segment to connect to the virtual\n"
                    "          image\n");
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

    if (!image || !deviceAddress || !vswitchName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Connecting virtual network adapter at %s to %s... ", deviceAddress, vswitchName);

    rc = smVirtual_Network_Adapter_Connect_Vswitch(vmapiContextP, "", 0, "",
            image, deviceAddress, vswitchName, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Connect_Vswitch", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Connect_Vswitch", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterConnectVswitchDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Connect_Vswitch_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    char * switchName = NULL;
    vmApiVirtualNetworkAdapterConnectVswitchDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvn";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:n:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 'n':
                switchName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Connect_Vswitch_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Connect_Vswitch_DM [-T] image_name\n"
                    "    [-v] virtual_address [-n] switch_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Connect_Vswitch_DM to define a virtual switch\n"
                    "  connection for an existing virtual network adapter in a virtual image's\n"
                    "  directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the user or profile to which virtual network adapter\n"
                    "          virtual switch connection information will be added\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -n    The name of the virtual switch segment to connect to the virtual\n"
                    "          image\n");
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

    if (!image || !virtualAddress || !switchName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Defining virtual switch connection in %s's directory entry... ", image);

    rc = smVirtual_Network_Adapter_Connect_Vswitch_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, switchName, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Connect_Vswitch_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Connect_Vswitch_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterConnectVswitchExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Connect_Vswitch_Extended";
    int rc;
    int i;
    int j;
    int entryCount = 0;
    int maxArrayCount = 3;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkAdapterConnectVswitchExtendedOutput * output;

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
                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Adapter_Connect_Vswitch_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Connect_Vswitch_Extended\n"
                    "    [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Connect_Vswitch_Extended to connect an existing\n"
                    "  virtual network adapter on an active virtual image to an existing virtual\n"
                    "  switch.\n\n"
                    "  The following options are required:\n"
                    "    -T   The name of the user to which virtual network adapter virtual switch\n"
                    "         connection information will be added.\n"
                    "    -k   A keyword=value item to be created in the directory.\n"
                    "         They may be specified in any order.\n\n"
                    "           image_device_number: The virtual device address for the new adapter.\n"
                    "                                This input parameter is required.\n\n"
                    "           switch_name: The name of the virtual switch segment. This input\n"
                    "                        parameter is required.\n\n"
                    "           port_selection: One of the following:\n"
                    "             AUTO - CP will choose the port.\n"
                    "             Range 0-65535 - The port number to be used.\n"
                    "             If unspecified, AUTO is the default.\n");
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

    if (!targetIdentifier ||  entryCount < 2)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Connecting virtual network adapter to an existing virtual switch... ");

    rc = smVirtual_Network_Adapter_Connect_Vswitch_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount,
            entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Connect_Vswitch_Extended", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Connect_Vswitch_Extended",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


int virtualNetworkAdapterCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Create";
    int rc;
    int option;
    int adapterType = 0;
    int virtualDevices = -1;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterCreateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvtd";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:t:d:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                virtualAddress = optarg;
                break;

            case 't':
                adapterType = atoi(optarg);
                break;

            case 'd':
                virtualDevices = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Create [-T] image_name [-v] virtualAddress\n"
                    "    [-t] adapterType [-d] virtualDevices\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Create to add a virtual network interface card\n"
                    "  (NIC) to an active virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a network adapter is being defined\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -t    The adapter type must be one of the following:\n"
                    "            1: Defines this adapter as a simulated HiperSockets NIC\n"
                    "            2: Defines this adapter as a simulated QDIO NIC\n"
                    "    -d    The number of virtual devices associated with this adapter\n");
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

    if (!image || !virtualAddress || !adapterType || (virtualDevices < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding virtual NIC to %s's active configuration... ", image);

    rc = smVirtual_Network_Adapter_Create(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, adapterType, virtualDevices, "", &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Create_DM";
    int rc;
    int option;
    int adapterType = 0;
    int adapterDevices = 0;
    char * image = NULL;
    char * deviceAddress = NULL;
    char * chpId = "";
    char * macId = "";
    vmApiVirtualNetworkAdapterCreateDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tvancm";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:a:n:c:m:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'v':
                deviceAddress = optarg;
                break;

            case 'a':
                adapterType = atoi(optarg);
                break;

            case 'n':
                adapterDevices = atoi(optarg);
                break;

            case 'c':
                chpId = optarg;
                break;

            case 'm':
                macId = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Adapter_Create_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Create_DM [-T] image_name [-v] virtual_address\n"
                    "    [-a] adapter_type [-n] devices_count [-c] channel_path_id [-m] mac_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Create_DM to add a virtual network interface\n"
                    "  card (NIC) to a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a network adapter is being defined.\n"
                    "    -v    The virtual device address for the new adapter\n"
                    "    -a    The adapter type:\n"
                    "            1: Defines this adapter as a simulated HiperSockets NIC\n"
                    "            2: Defines this adapter as a simulated QDIO NIC\n"
                    "    -n    The number of virtual devices associated with this adapter\n"
                    "  The following options are optional:\n"
                    "    -c    The hex CHPID numbers for the first- and second-level systems\n"
                    "    -m    The MAC identifier\n");
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

    if (!image || !deviceAddress || !adapterType || !adapterDevices) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding virtual NIC to %s's directory entry... ", image);

    rc = smVirtual_Network_Adapter_Create_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
        image, deviceAddress, adapterType, adapterDevices, chpId, macId, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Create_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Create_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterCreateExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Create_Extended";
    int rc;
    int entryCount = 0;
    int maxArrayCount = 4;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkAdapterCreateExtendedOutput * output;

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
                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Adapter_Create_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Create_Extended [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Create_Extended to add a virtual network\n"
                    "  interface card (NIC) to an active virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T   The name of the image for which a network adapter is being defined.\n"
                    "    -k   A keyword=value item to be created in the directory.\n"
                    "         They may be specified in any order.\n\n"
                    "         image_device_number: The virtual device address for the new adaptert\n\n"
                    "         adapter_type: One of the following:\n"
                    "           HIPERsockets - Defines this adapter as a simulated HiperSockets NIC. This\n"
                    "                          adapter will function like the HiperSockets internal\n"
                    "                          adapter (device model 1732-05). A HiperSockets NIC can\n"
                    "                          function without a guest LAN connection, or it can be\n"
                    "                          coupled to a HiperSockets guest LAN. This is the default\n"
                    "                          if adapter_type=value is not specified.\n"
                    "             Note: You will receive an error if you attempt to connect a\n"
                    "             simulated HiperSockets adapter to a virtual switch.\n"
                    "           QDIO - Defines this adapter as a simulated QDIO NIC. This adapter will\n"
                    "                  function like the OSA Direct Express (QDIO) adapter (device\n"
                    "                  model 1732-01). A QDIO NIC is functional when it is coupled\n"
                    "                  either to a QDIO guest LAN or to a QDIO, IEDN, or INMN virtual\n"
                    "                  switch. A QDIO adapter can couple to an IEDN or INMN virtual\n"
                    "                  switch only when the owning user ID is authorized (by the system\n"
                    "                  administrator), by specifying OSDSIM on the SET VSWITCH command.\n"
                    "           IEDN - Defines this adapter as a simulated Intraensemble Data Network NIC.\n"
                    "                  This adapter will function like an Intraensemble Data Network\n"
                    "                  (IEDN) adapter (device model 1732-02) that is connected to an IEDN\n"
                    "                  internal network managed by the Unified Resource Manager. An\n"
                    "                  IEDN NIC is is only functional when coupled to an IEDN virtual\n "
                    "                  switch.\n\n"
                    "           INMN - Defines this adapter as a simulated Intranode Management Network\n"
                    "                  NIC. This adapter will function like an Intranode Management\n"
                    "                  Network (INMN) adapter (device model 1732-03) that is connected to\n"
                    "                  internal network managed by the Unified Resource Manager. A\n"
                    "                  INMN NIC is only functional when coupled to an INMN virtual\n"
                    "                  switch.\n\n"
                    "         devices: (Range 3-3072) The number of virtual devices associated with this\n"
                    "                  adapter. For a simulated HiperSockets adapter, this must be a\n"
                    "                  decimal value between 3 and 3,072 (inclusive). For a simulated QDIO\n"
                    "                  adapter, this must be a decimal value between 3 and 240 (inclusive).\n"
                    "                  If omitted, the default is 3.\n\n"
                    "         channel_path_id: For use only when configuring a second-level z/OS system,\n"
                    "                          where it is used to specify the hex CHPID numbers for the\n"
                    "                          first- and second-level systems. Do not specify this\n"
                    "                          parameter for z/VM, which allocates available CHPIDs\n"
                    "                          by default.\n\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding virtual NIC to %s... ", targetIdentifier);

    rc = smVirtual_Network_Adapter_Create_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Create_Extended", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Create_Extended", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}


int virtualNetworkAdapterCreateExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Create_Extended_DM";
    int rc;
    int entryCount = 0;
    int maxArrayCount = 5;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkAdapterCreateExtendedDmOutput * output;

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
                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Adapter_Create_Extended_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Create_Extended_DM [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Create_Extended_DM to add a virtual network\n"
                    "  interface card (NIC) to an active virtual images directory entry\n\n"
                    "  The following options are required:\n"
                    "    -T   The name of the image for which a network adapter is being defined.\n"
                    "    -k   A keyword=value item to be created in the directory.\n"
                    "         They may be specified in any order.\n\n"
                    "           image_device_number: The virtual device address for the new adaptert\n\n"
                    "           adapter_type: One of the following:\n"
                    "             HIPERsockets - Defines this adapter as a simulated HiperSockets\n"
                    "                            NIC. This adapter will function like the\n"
                    "                            HiperSockets internal adapter(device model 1732-05)\n"
                    "                            . A HiperSockets NIC can function without a guest\n"
                    "                            LAN connection, or it can be coupled to a\n"
                    "                            HiperSockets guest LAN. This is the default if\n"
                    "                            adapter_type=value is not specified.\n"
                    "               Note: You will receive an error if you attempt to connect a\n"
                    "               simulated HiperSockets adapter to a virtual switch.\n"
                    "             QDIO - Defines this adapter as a simulated QDIO NIC. This adapter\n"
                    "                    will function like the OSA Direct Express (QDIO) adapter\n"
                    "                   (device model 1732-01). A QDIO NIC is functional when it is\n"
                    "                    coupled either to a QDIO guest LAN or to a QDIO, IEDN, or\n"
                    "                    INMN virtual switch.A QDIO adapter can couple to an IEDN or\n"
                    "                    INMN virtual switch only when the owning user ID is\n"
                    "                    authorized (by the system administrator), by specifying\n"
                    "                    OSDSIM on the SET VSWITCH command.\n"
                    "             IEDN - Defines this adapter as a simulated Intraensemble Data\n"
                    "                    Network NIC.This adapter will function like an \n"
                    "                    Intraensemble Data Network (IEDN) adapter (device model\n"
                    "                    1732-02) that is connected to an IEDN internal network\n"
                    "                    managed by the Unified Resource Manager.An IEDN NIC is only\n"
                    "                    functional when coupled to an IEDN virtual switch.\n\n"
                    "             INMN - Defines this adapter as a simulated Intranode Management\n"
                    "                    Network NIC.This adapter will function like an Intranode\n"
                    "                    Management Network (INMN) adapter (device model 1732-03)\n"
                    "                    that is connected to an INMN internal network managed by\n"
                    "                    the Unified Resource Manager. A INMN NIC is only functional\n"
                    "                    when coupled to an INMN virtual switch.\n\n"
                    "           devices: (Range 3-3072) The number of virtual devices associated\n"
                    "                    with this adapter.For a simulated HiperSockets adapter,this\n"
                    "                    must be a decimal value between 3 and 3,072 (inclusive).\n"
                    "                    For a simulated QDIO adapter,this must be a decimal value\n"
                    "                    between 3 and 240 (inclusive).If omitted, the default is 3.\n\n"
                    "           channel_path_id: For use only when configuring a second-level z/OS\n"
                    "                            system,where it is used to specify the hex CHPID\n"
                    "                            numbers for the first- and second-level systems.\n"
                    "                            Do not specify this parameter for z/VM, which\n"
                    "                            allocates available CHPIDs by default.\n\n"
                    "           mac_id: The MAC identifier.\n"
                    "             Note: This should only be specified for NIC adapter types of QDIO\n"
                    "             or Hipersockets. A user-defined MAC address is not allowed on\n"
                    "             types IEDN or INMN. Specifying a MAC ID for type IEDN or INMN\n"
                    "             prevents the adapter from being added to the virtual I/O\n"
                    "             configuration of the guest.\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Adding virtual NIC to %s's directory entry... ", targetIdentifier);

    rc = smVirtual_Network_Adapter_Create_Extended_DM(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Create_Extended_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Create_Extended_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Network_Adapter_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Delete [-T] image_name\n"
                    "    [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Delete to remove a virtual network interface\n"
                    "  card (NIC) from an active virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the network adapter is being\n"
                    "          removed\n"
                    "    -v    The virtual device number of the base address for the adapter\n"
                    "          to be deleted\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing virtual NIC from %s's active configuration... ", image);

    rc = smVirtual_Network_Adapter_Delete(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Delete_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterDeleteDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Image_Disk_Delete_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Image_Disk_Delete_DM [-T] image_name [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Delete_DM to remove a virtual\n"
                    "  network interface card (NIC) from a virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which the network adapter is being removed\n"
                    "    -v    The virtual device number of the base address for the adapter to be\n"
                    "          deleted.\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing virtual NIC from %s's directory entry... ", image);

    rc = smVirtual_Network_Adapter_Delete_DM(vmapiContextP, "", 0, "",  // Authorizing user, password length, password.
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Delete_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Delete_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterDisconnect(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Disconnect";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterDisconnectOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Network_Adapter_Disconnect\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Disconnect [-T] image_name\n"
                    "    [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Disconnect to disconnect a virtual network adapter\n"
                    "  on an active virtual image from a virtual network LAN or virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the user or profile from which virtual network adapter\n"
                    "          guest LAN connection information will be removed\n"
                    "    -v    Specifies the virtual device address of the connected adapter\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Disconnecting virtual network adapter... ");

    rc = smVirtual_Network_Adapter_Disconnect(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
            image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Disconnect", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Disconnect", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterDisconnectDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Disconnect_DM";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterDisconnectDmOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Network_Adapter_Disconnect_DM\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Disconnect_DM [-T] image_name\n"
                    "    [-v] virtual_address\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Disconnect_DM to remove a virtual network LAN or\n"
                    "  virtual switch connection from a virtual network adapter definition in a\n"
                    "  virtual image's directory entry.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the user or profile from which virtual network adapter\n"
                    "          guest LAN connection information will be removed\n"
                    "    -v    Specifies the virtual device address of the connected adapter\n");
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing virtual network LAN or virtual switch connection from %s's directory entry... ", image);

    rc = smVirtual_Network_Adapter_Disconnect_DM(vmapiContextP, "", 0, "", image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Disconnect_DM", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Disconnect_DM", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkAdapterQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Adapter_Query";
    int rc;
    int option;
    char * image = NULL;
    char * virtualAddress = NULL;
    vmApiVirtualNetworkAdapterQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tv";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:v:h?")) != -1)
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
                    "  Virtual_Network_Adapter_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Query to obtain information about the\n"
                    "  specified adapter for an active virtual image.\n\n"
                    "  The following options are required:\n"
                    "    -T    The virtual image name of the owner of the adapter\n"
                    "    -v    The virtual device address of the adapter\n"
                    "            '*': Request is made for information about all adapters owned\n"
                    "                 by the target userid\n");
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

    if (!image || !virtualAddress) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_Adapter_Query(vmapiContextP, "", 0, "",  // Authorizing user, password length, password
        image, virtualAddress, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Adapter_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Adapter_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int count = output->adapterArrayCount;
        if (count > 0) {
            int i;
            char * adapterType;
            char * adapterStatus;
            for (i = 0; i < count; i++) {
                if (output->adapterList[i].adapterType == 1) {
                    adapterType = "HiperSockets";
                } else if (output->adapterList[i].adapterType == 2) {
                    adapterType = "QDIO";
                } else if (output->adapterList[i].adapterType == 4) {
                    adapterType = "INMN";
                } else if (output->adapterList[i].adapterType == 5) {
                    adapterType = "IEDN";
                } else {
                    adapterType = "";
                }
                if (output->adapterList[i].adapterStatus == 0) {
                    adapterStatus = "Not coupled";
                } else if (output->adapterList[i].adapterType == 1) {
                    adapterStatus = "Coupled but not active";
                } else if (output->adapterList[i].adapterType == 2) {
                    adapterStatus = "Coupled and active";
                } else {
                    adapterStatus = "";
                }
                printf("Adapter:\n"
                    "  Address: %s\n"
                    "  Device count: %d\n"
                    "  Adapter type: %s\n"
                    "  Adapter status: %s\n"
                    "  LAN owner: %s\n"
                    "  LAN name: %s\n",
                    output->adapterList[i].imageDeviceNumber, output->adapterList[i].networkAdapterDevices, adapterType,
                    adapterStatus, output->adapterList[i].lanOwner, output->adapterList[i].lanName);
                }
        }
    }
    return rc;
}
int virtualNetworkAdapterQueryExtended( int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP ) {
    int rc;
    int i;
    int j;
    int k;
    int entryCount = 0;
    int maxArrayCount = 1;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];

    char * blank = " ";
    char *token;
    char * buffer;
    vmApiVirtualNetworkAdapterQueryExtendedOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while (( option = getopt( argC, argV, "T:k:h?") ) != -1 )
        switch ( option ) {
            case 'T':
                targetIdentifier = optarg;
                break;

            case 'k':
                if ( !optarg ) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    return INVALID_DATA;
                }

                if ( entryCount < maxArrayCount ) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                    printf( "ERROR: Too many -k values entered.\n" );
                    return INVALID_DATA;
                }
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf( "NAME\n"
                    "  Virtual_Network_Adapter_Query_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Adapter_Query_Extended [-T] targetIdentifier\n"
                    "    [-k] entry\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Adapter_Query_Extended to obtain information about the\n"
                    "   specified network adapter.\n\n"
                    "  The following options are required:\n"
                    "    -T    The virtual image name of the owner of the adapter.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            image_device_number= The virtual device address of the adapter, or\n"
                    "                         '*'  All virtual adapters\n");
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

    if ( !targetIdentifier ||  entryCount < 1 ) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf( "\nERROR: Missing required options\n" );
        return 1;
    }

    rc = smVirtual_Network_Adapter_Query_Extended( vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output );

    if ( rc ) {
        printAndLogProcessingErrors( "Virtual_Network_Adapter_Query_Extended", rc, vmapiContextP, "", 0);
    } else if ( output->common.returnCode || output->common.reasonCode ) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription( "Virtual_Network_Adapter_Query_Extended",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        // Print out the response
        int count = output->responseCnt;
        if ( count > 0 ) {
            for ( i = 0; i < count; i++ ) {
                printf( "%s\n", output->responseList[i].vmapiString );
            }
        }

    }
    return rc;
}

int virtualNetworkLANAccess(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_LAN_Access";
    int rc;
    int option;
    char * image = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    char * accessOpt = NULL;
    char * accessGrantUser = NULL;
    char * promiscuity = NULL;
    vmApiVirtualNetworkLanAccessOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tnoaup";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:a:u:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'a':
                accessOpt = optarg;
                break;

            case 'u':
                accessGrantUser = optarg;
                break;

            case 'p':
                promiscuity = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Lan_Access\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Lan_Access [-T] image_name [-n] lan_name\n"
                    "    [-o] lan_owner [-a] access_op [-u] access_user [-p] promiscuity\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Lan_Access to grant users access to a restricted\n"
                    "  virtual network LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -n    The name of the LAN to which access is being granted or\n"
                    "          revoked\n"
                    "    -o    The virtual image owning the guest LAN segment to be created\n"
                    "    -a    Access operation:\n"
                    "            GRANT: Grant access\n"
                    "            REVOKE: Revoke access\n"
                    "    -u    Virtual image to be granted access to the LAN\n"
                    "    -p    Promiscuity:\n"
                    "            NONPROMISCUOUS: Nonpromiscuous access\n"
                    "            PROMISCUOUS: Promiscuous access\n");
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

    if (!image || !lanName || !lanOwner || !accessOpt || !accessGrantUser || !promiscuity) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Granting/revoking %s access to %s... ", accessGrantUser, lanName);

    rc = smVirtual_Network_LAN_Access(vmapiContextP, "", 0, "", image, lanName,
            lanOwner, accessOpt, accessGrantUser, promiscuity, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_LAN_Access", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_LAN_Access", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkLANAccessQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_LAN_Access_Query";
    int rc;
    int option;
    char * image = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    vmApiVirtualNetworkLanAccessQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tno";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_LAN_Access_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_LAN_Access_Query [-T] image_name"
                    "    [-n] lan_name [-o] lan_owner\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_LAN_Access_Query to query which users are\n"
                    "  authorized to access a specified restricted virtual network LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -n    The name of the LAN being queried\n"
                    "    -o    The owner of the LAN being queried\n");
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

    if (!image || !lanName || !lanOwner) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_LAN_Access_Query(vmapiContextP, "", 0, "", image, lanName, lanOwner, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_LAN_Access_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_LAN_Access_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int count = output->lanAccessCount;
        if (count > 0) {
            int i;
            for (i = 0; i < count; i++) {
                printf("%s\n", output->lanAccessList[i].vmapiString);
            }
        }
    }
    return rc;
}

int virtualNetworkLANCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_LAN_Create";
    int rc;
    int option;
    int lanType = 0;
    int transportType = -1;
    char * image = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    vmApiVirtualNetworkLanCreateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tnotp";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:t:p:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 't':
                lanType = atoi(optarg);
                break;

            case 'p':
                transportType = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_LAN_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_LAN_Create [-T] image_name [-n] lan_name\n"
                    "    [-o] lan_owner [-t] lan_type [-p] transport_type\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_LAN_Create to create a virtual network LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a LAN connection is being created\n"
                    "    -n    The name of the guest LAN segment to be created\n"
                    "    -o    The virtual image owning the guest LAN segment to be created\n"
                    "    -t    The type of guest LAN segment. This must be one of the following:\n"
                    "            1: Defines this adapter as an unrestricted simulated\n"
                    "               HiperSockets NIC\n"
                    "            2: Defines this adapter as an unrestricted simulated QDIO NIC\n"
                    "            3: Defines this adapter as a restricted simulated\n"
                    "               HiperSockets NIC\n"
                    "            4: Defines this adapter as a restricted simulated QDIO NIC\n"
                    "    -p    Specifies the transport mechanism to be used for guest LANs and\n"
                    "          virtual switches, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: IP ~ Reference all target nodes on LAN or switch using\n"
                    "               IP addresses\n"
                    "            2: Ethernet ~ Reference all target nodes on LAN or switch using\n"
                    "               MAC addresses\n");
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

    if (!image || !lanName || !lanOwner || !lanType || (transportType < 0)) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating virtual network LAN %s... ", lanName);

    rc = smVirtual_Network_LAN_Create(vmapiContextP, "", 0, "", image, lanName, lanOwner, lanType, transportType, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_LAN_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_LAN_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkLANDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_LAN_Delete";
    int rc;
    int option;
    char * image = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    vmApiVirtualNetworkLanDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tno";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_LAN_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_LAN_Delete [-T] image_name [-n] lan_name\n"
                    "    [-o] lan_owner\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_LAN_Delete to delete a virtual network LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the image for which a LAN connection is being deleted\n"
                    "    -n    The name of the guest LAN segment to be deleted\n"
                    "    -o    The virtual image owning the guest LAN segment to be deleted\n");
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

    if (!image || !lanName || !lanOwner) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting virtual network LAN %s... ", lanName);

    rc = smVirtual_Network_LAN_Delete(vmapiContextP, "", 0, "", image, lanName, lanOwner, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_LAN_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_LAN_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkLANQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_LAN_Query";
    int rc;
    int option;
    char * image = NULL;
    char * lanName = NULL;
    char * lanOwner = NULL;
    vmApiVirtualNetworkLanQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tno";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                lanName = optarg;
                break;

            case 'o':
                lanOwner = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_LAN_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_LAN_Query [-T] image_name [-n] lan_name\n"
                    "    [-o] lan_owner\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_LAN_Query to obtain information about a virtual\n"
                    "  network LAN.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -n    The name of the guest LAN segment to be queried\n"
                    "    -o    The name of the virtual image owning the guest LAN segment\n"
                    "            '*': A request is made for all qualified guest LAN segments\n");
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

    if (!image || !lanName || !lanOwner) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_LAN_Query(vmapiContextP, "", 0, "", image, lanName, lanOwner, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_LAN_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_LAN_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int count = output->lanCount;
        if (count > 0) {
            int i, j;
            char * lanType;
            for (i = 0; i < count; i++) {
                if (output->lanList[i].lanType == 1) {
                    lanType = "HiperSockets NIC";
                } else if (output->lanList[i].lanType == 2) {
                    lanType = "QDIO NIC";
                } else {
                    lanType = "";
                }
                printf("LAN:\n"
                    "  Name: %s\n"
                    "  Owner: %s\n"
                    "  LAN type: %s\n"
                    "  Connections:\n", output->lanList[i].lanName, output->lanList[i].lanOwner, lanType);
                for (j = 0; j < output->lanList[i].connectedAdapterCount; j++) {
                    printf("    Adapter owner: %s  Address: %s\n", output->lanList[i].connectedAdapterList[j].adapterOwner,
                           output->lanList[i].connectedAdapterList[j].imageDeviceNumber);
                }
            }
        }
    }
    return rc;
}

int virtualNetworkOSAQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_OSA_Query";
    int rc;
    int i;
    int option;
    char * image = NULL;
    char *token;
    char *buffer;  // char * whose value is preserved between successive related calls to strtok_r.
    char * blank = " ";
    char osa_address[4+1];
    char osa_status[17+1];
    char osa_type[7+1];
    char chpid_address[2+1];
    char agent_status[3+1];
    char userid[8+1];
    vmApiVirtualNetworkOsaQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tno";
    char tempStr[1];
    char strMsg[300];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:o:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_OSA_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_OSA_Query [-T] image_name\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_OSA_Query to query data about real OSA devices.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_OSA_Query(vmapiContextP, "", 0, "", image, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_OSA_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_OSA_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i =0; i < output->arrayCount; i ++) {
            token = strtok_r(output->osaInfoStructure[i].vmapiString, blank, &buffer);
            if (token != NULL) {
                strcpy(osa_address, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error osa_address is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                break;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(osa_status, token);
                if ( (strncmp(osa_status,"ATTACHED",8) == 0) || 
                     (strncmp(osa_status,"BOX/ATTC",8) == 0) ) {
                   memset(userid,'\0',sizeof(userid));
                   strncpy(userid,&osa_status[8],8);
                   osa_status[8]=' ';
                   strcpy(&osa_status[9],userid);
                }
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error osa_status is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                break;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(osa_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error osa_type is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                break;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(chpid_address, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error chpid_address is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                break;
            }

            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(agent_status, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error agent_status is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                rc = OUTPUT_ERRORS_FOUND;
                break;
            }
            snprintf(strMsg, sizeof(strMsg),
                   "  OSA Address: %s \n"
                   "  OSA Status: %s\n"
                   "  OSA Type: %s\n"
                   "  CHPID Address: %s\n"
                   "  Agent Status: %s\n",
                   osa_address, osa_status, osa_type, chpid_address, agent_status);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                break;
            }
        }
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


int virtualNetworkVLANQueryStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_VLAN_Query_Stats";
    int rc;
    int i;
    int j;
    int portNicValuesSize;
    int segmentDataSize;
    int entryCount = 0;
    int maxArrayCount = 4;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    char type[4 + 1];
    char port_name[8 + 1];
    char nic_addr[8 + 1];
    char port_num[10 + 1];
    char nic_num[10 + 1];
    char pseg_vlanid[10 + 1];
    char pseg_rx[10 + 1];
    char pseg_rx_disc[10 + 1];
    char pseg_tx[10 + 1];
    char pseg_tx_disc[10 + 1];
    char tempBuffPortNic[130];
    char tempBuffSegmentData[130];
    const char * blank = " ";
    char *token;
    char * buffer1;  // char * whose value is preserved between successive related calls to strtok_r.
    char * buffer2;  // char * whose value is preserved between successive related calls to strtok_r.
    vmApiVirtualNetworkVLANQueryStatsOutput * output;

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
                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_VLAN_Query_Stats\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_VLAN_Query_Stats [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_VLAN_Query_Stats to query a virtual switch's\n"
                    "  statistics.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization, i.e. the authenticated user must have\n"
                    "          authorization to perform this function for this target.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            fmt_version: The format version of this API, for calls to DIAGNOSE\n"
                    "                         X'26C'. For V6.2, the supported format version value\n"
                    "                         is 4. This is an optional parameter.\n"
                    "            userid: The name of the virtual machine. This input parameter is\n"
                    "                    required.\n"
                    "            VLAN_id: The VLAN ID for which you are querying information.\n"
                    "            device: Specifies whether information is requested for the ports,\n"
                    "                    the virtual NICs or both, as follows:\n"
                    "                      PORT\n"
                    "                      NIC\n"
                    "                      BOTH\n"
                    "              If not specified, BOTH is the default.\n");
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

    if (!targetIdentifier ||  entryCount < 2)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_VLAN_Query_Stats(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);
    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_VLAN_Query_Stats", rc, vmapiContextP, "", 0);
    } else  if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_VLAN_Query_Stats", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        //the smapi call worked print out the returned data
        printf("portNicArrayCount = %d\n", output->portNicArrayCount);
        snprintf(strMsg, sizeof(strMsg), "portNicArrayCount = %d\n\n", output->portNicArrayCount);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }

        // Get the type and the if it is PORT get the port_name and port_num
        // else get the nic_addr and nic_num
        for (i = 0; i < output->portNicArrayCount; i++) {
            memset(tempBuffPortNic, 0x00, 130);
            portNicValuesSize = strlen((char *)output->portNicList[i].portNicValues);
            strncpy(tempBuffPortNic, (char *)output->portNicList[i].portNicValues, portNicValuesSize);
            trim(tempBuffPortNic);
            tempBuffPortNic[portNicValuesSize + 1] = '\0';
            // Get type
            token = strtok_r(tempBuffPortNic, blank, &buffer1);
            if (token != NULL) {
                strcpy(type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error type is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            if (strcmp(token,"PORT") == 0) {
                // Get port_name
                token = strtok_r(NULL, blank, &buffer1);
                if (token != NULL) {
                    strcpy(port_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error port_name is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get port_num
                token = strtok_r(NULL, blank, &buffer1);
                if (token != NULL) {
                    strcpy(port_num, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error port_num is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
            } else if (strcmp(token,"NIC") == 0) {
                // Get nic_addr
                token = strtok_r(NULL, blank, &buffer1);
                if (token != NULL) {
                    strcpy(nic_addr, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error nic_addr is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get nic_num
                token = strtok_r(NULL, blank, &buffer1);
                if (token != NULL) {
                    strcpy(nic_num, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error nic_num is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error invalid type received!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            snprintf(strMsg, sizeof(strMsg), "type = %s\n", type);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            if (strcmp(type,"PORT") == 0) {
                snprintf(strMsg, sizeof(strMsg), "port_name = %s\n", port_name);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg), "port_num = %s\n", port_num);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            } else {
                snprintf(strMsg, sizeof(strMsg), "nic_addr = %s\n", nic_addr);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg), "nic_num = %s\n", nic_num);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            }
            snprintf(strMsg, sizeof(strMsg), "\n");
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            for (j = 0; j < output->portNicList[i].segmentCount; j++) {
                memset(tempBuffSegmentData, 0x00, 130);
                segmentDataSize = strlen((char *)output->portNicList[i].segmentArray[j].segmentStructure);
                strncpy(tempBuffSegmentData, (char *)output->portNicList[i].segmentArray[j].segmentStructure, segmentDataSize);
                trim(tempBuffSegmentData);
                tempBuffSegmentData[segmentDataSize + 1] = '\0';

                // Get the pseg_vlanid
                token = strtok_r(tempBuffSegmentData, " ", &buffer2);
                if (token != NULL) {
                    strcpy(pseg_vlanid, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error pseg_vlanid is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get pseg_rx
                token = strtok_r(NULL, " ", &buffer2);
                if (token != NULL) {
                    strcpy(pseg_rx, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error pseg_rx is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get pseg_rx_disc
                token = strtok_r(NULL, " ", &buffer2);
                if (token != NULL) {
                    strcpy(pseg_rx_disc, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error pseg_rx_disc is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get pseg_tx
                token = strtok_r(NULL, " ", &buffer2);
                if (token != NULL) {
                    strcpy(pseg_tx, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error pseg_tx is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                // Get pseg_tx_disc
                token = strtok_r(NULL, "\0", &buffer2);
                if (token != NULL) {
                    strcpy(pseg_tx_disc, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error pseg_tx_disc is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                         "pseg_vlanid = %s\n"
                         "pseg_rx = %s\n"
                         "pseg_rx_disc = %s\n"
                         "pseg_tx = %s\n"
                         "pseg_tx_disc = %s\n\n",
                         pseg_vlanid, pseg_rx, pseg_rx_disc, pseg_tx, pseg_tx_disc);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            } //end of for j
        } //end of for i
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
    } //end of else rc and return code and reason code equal 0

    return rc;
}

int virtualNetworkVswitchCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Create";
    int rc;
    int option;
    int connectionValue = 0;
    int queueMemoryLimit = -1;
    int routingValue = 0;
    int transportType = 0;
    int vlanId = 0;
    int portType = 0;
    int updateSystemConfigIndicator = 0;
    int gvrpValue = 0;
    int nativeVlanId = -1;
    char * image = NULL;
    char * switchName = "";
    char * realDeviceAddress = "";
    char * portName = "";
    char * controllerName = "";
    char * systemConfigName = "";
    char * systemConfigType = "";
    char * parmDiskOwner = "";
    char * parmDiskNumber = "";
    char * parmDiskPassword = "";
    char * altSystemConfigName = "";
    char * altSystemConfigType = "";
    char * altParmDiskOwner = "";
    char * altParmDiskNumber = "";
    char * altParmDiskPassword = "";
    vmApiVirtualNetworkVswitchCreateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TnraicqetvpuLFRCPNYOMDGV";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:r:a:i:c:q:e:t:v:p:u:L:F:R:C:P:N:Y:O:M:D:G:V:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                switchName = optarg;
                break;

            case 'r':
                realDeviceAddress = optarg;
                break;

            case 'a':
                portName = optarg;
                break;

            case 'i':
                controllerName = optarg;
                break;

            case 'c':
                connectionValue = atoi(optarg);
                break;

            case 'q':
                queueMemoryLimit = atoi(optarg);
                break;

            case 'e':
                routingValue = atoi(optarg);
                break;

            case 't':
                transportType = atoi(optarg);
                break;

            case 'v':
                vlanId = atoi(optarg);
                break;

            case 'p':
                portType = atoi(optarg);
                break;

            case 'u':
                updateSystemConfigIndicator = atoi(optarg);
                break;

            case 'L':
                systemConfigName = optarg;
                break;

            case 'F':
                systemConfigType = optarg;
                break;

            case 'R':
                parmDiskOwner = optarg;
                break;

            case 'C':
                parmDiskNumber = optarg;
                break;

            case 'P':
                parmDiskPassword = optarg;
                break;

            case 'N':
                altSystemConfigName = optarg;
                break;

            case 'Y':
                altSystemConfigType = optarg;
                break;

            case 'O':
                altParmDiskOwner = optarg;
                break;

            case 'M':
                altParmDiskNumber = optarg;
                break;

            case 'D':
                altParmDiskPassword = optarg;
                break;

            case 'G':
                gvrpValue = atoi(optarg);
                break;

            case 'V':
                nativeVlanId = atoi(optarg);
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Vswitch_Create\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Create [-T] image_name [-n] switch_name\n"
                    "    [-r] real_device_address [-a] port_name [-i] controller_name\n"
                    "    [-c] connection_value [-q] queue_memory_limit [-e] routing_value\n"
                    "    [-t] transport_type [-v] vlan_id [-p] port_type [-u] update_sys_config\n"
                    "    [-L] sys_config_name [-F] sys_config_type [-R] parm_disk_owner\n"
                    "    [-C] parm_disk_number [-P] parm_disk_passwd [-N] alt_sys_config_name\n"
                    "    [-Y] alt_sys_config_type [-O] alt_parm_disk_owner  [-M] alt_parm_disk_number\n"
                    "    [-D] alt_parm_disk_passwd [-G] gvrp [-V] native_vlan_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Create to create a virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    The virtual image name of the owner of the virtual switch\n"
                    "  The following options are optional:\n"
                    "    -n    The name of the virtual switch segment\n"
                    "    -r    The real device address of a real OSA-Express QDIO device\n"
                    "          used to create the switch to the virtual adapter\n"
                    "    -a    The name used to identify the OSA Expanded adapter\n"
                    "    -i    The user ID controlling the real device\n"
                    "    -c    Connection value. This can be any of the following values:\n"
                    "            0: Unspecified\n"
                    "            1: Activate the real device connection\n"
                    "            2: Do not activate the real device connection\n"
                    "    -q    Queue memory limit. A number between 1 and 8 specifying the QDIO\n"
                    "          buffer size in megabytes. If unspecified, the default is 8.\n"
                    "    -e    Specifies whether the OSA-Express QDIO device will act as a router\n"
                    "          to the virtual switch, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: NONROUTER ~ The OSA-Express device will not act as a router to\n"
                    "               the virtual switch\n"
                    "            2: PRIROUTER ~ The OSA-Express device identified will act as a\n"
                    "               primary router to the virtual switch\n"
                    "    -t    Specifies the transport mechanism to be used for the virtual\n"
                    "          switch, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: IP\n"
                    "            2: ETHERNET\n"
                    "    -v    The VLAN ID. This can be any of the following values:\n"
                    "           -1: The VLAN ID is not specified\n"
                    "            0: UNAWARE\n"
                    "            1-4094: Any number in this range is a valid VLAN ID\n"
                    "    -p    Specifies the port type, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: ACCESS\n"
                    "            2: TRUNK\n"
                    "    -u    Update system config indicator. This can be any of the following\n"
                    "          values:\n"
                    "            0: Unspecified\n"
                    "            1: Create a virtual switch on the active system\n"
                    "            2: Create a virtual switch on the active system and add the virtual\n"
                    "               switch definition to the system configuration file\n"
                    "            3: Add the virtual switch definition to the system configuration\n"
                    "               file\n"
                    "    -L    File name of the system configuration file. The default is 'SYSTEM'.\n"
                    "    -F    File type of the system configuration file. The default is 'CONFIG'.\n"
                    "    -R    Owner of the parm disk. The default is 'MAINT'.\n"
                    "    -C    Number of the parm disk, as defined in the server's directory.\n"
                    "          The default is 'CF1'.\n"
                    "    -P    Multiwrite password for the parm disk. The default is ','.\n"
                    "    -N    File name of the second (alternative) system configuration file.\n"
                    "          The default is 'SYSTEM'.\n"
                    "    -Y    File type of the second (alternative) system configuration file.\n"
                    "          The default is 'CONFIG'.\n"
                    "    -O    Owner of the second (alternative) parm disk. The default is 'MAINT'.\n"
                    "    -M    Number of the second (alternative) parm disk. The default is 'CF2'.\n"
                    "    -D    Multiwrite password for the second (alternative) parm disk.\n"
                    "          The default is ','.\n"
                    "    -G    GVRP value. This can be any of the following values:\n"
                    "            0: Unspecified\n"
                    "            1: GVRP\n"
                    "            2: NOGVRP\n"
                    "    -V    The native VLAN ID. This can be any of the following values:\n"
                    "            -1: The native VLAN ID is not specified\n"
                    "            1-4094: Any number in this range is a valid native VLAN ID\n");
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

    if (!image || !switchName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating virtual switch %s... ", switchName);

    rc = smVirtual_Network_Vswitch_Create(vmapiContextP, "", 0, "",
            image, switchName, realDeviceAddress, portName, controllerName, connectionValue,
            queueMemoryLimit, routingValue, transportType, vlanId, portType, updateSystemConfigIndicator,
            systemConfigName, systemConfigType, parmDiskOwner, parmDiskNumber, parmDiskPassword,
            altSystemConfigName, altSystemConfigType, altParmDiskOwner, altParmDiskNumber,
            altParmDiskPassword, gvrpValue, nativeVlanId, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Create", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Create", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkVswitchCreateExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Create_Extended";
    int rc;
    int entryCount = 0;
    int maxArrayCount = 16;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkVswitchCreateExtendedOutput * output;

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

                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Vswitch_Create_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Create_Extended [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Create_Extended to create a virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T   Used strictly for authorization, i.e. the authenticated user must have\n"
                    "         authorization to perform this function for this target.\n"
                    "    -k   A keyword=value item to be created in the directory.\n"
                    "         They may be specified in any order.\n\n"
                    "           switch_name: The name of the virtual switch segment\n\n"
                    "           real_device_address: The real device address or the real device address and\n"
                    "                                OSA Express port number of a QDIO OSA Express device to\n"
                    "                                be used to create the switch to the virtual adapter.\n"
                    "                                If using a real device and an OSA Express port number,\n"
                    "                                specify the real device number followed by a period(.),\n"
                    "                                the letter 'P' (or 'p'), followed by the port number as\n"
                    "                                a hexadecimal number.A maximum of three device addresses\n"
                    "                                all 1-7 characters in length, may be specified,delimited\n"
                    "                                by blanks. 'None' may also be specified.\n"
                    "                                (The default value is 'None'.)\n\n"
                    "           port_name: The name used to identify the OSA Expanded adapter. A maximum of\n"
                    "                      three port names, all 1-8 characters in length, may be specified,\n"
                    "                      delimited by blanks.\n\n"
                    "           controller_name: One of the following:\n"
                    "                            The userid controlling the real device or '*' that specifies\n"
                    "                            any available controller may be used.The default is '*'.\n\n"
                    "           connection_value: One of the following:\n"
                    "             CONnect - Activate the real device connection\n"
                    "             DISCONnect - Do not activate the real device connection\n"
                    "             NOUPLINK - The virtual switch will never have connectivity through the\n"
                    "                        UPLINK port. This option removes the UPLINK port from the\n"
                    "                        virtual switch. Once the UPLINK port is removed, it can never\n"
                    "                        be added back to the virtual switch.\n"
                    "             If not specified, the default is CONNECT.\n\n"
                    "           queue_memory_limit: A number between 1 and 8 specifying the QDIO buffer size\n"
                    "                               in megabytes. If unspecified, the default is 8.\n\n"
                    "           routing_value: Specifies whether the OSA-Express QDIO device will act as a\n"
                    "                          router to the virtual switch, as follows:\n"
                    "               NONrouter: The OSA-Express device identified in real_device_address=\n"
                    "                          will not act as a router to the virtual switch.\n"
                    "               PRIrouter: The OSA-Express device identified in real_device_address=\n"
                    "                          will act as a primary router to the virtual switch.\n"
                    "             If transport_type=ETHERNET is specified, this value must be unspecified.\n"
                    "             For other transport types, if this value is unspecified, the default is\n"
                    "             NONROUTER.\n\n"
                    "           transport_type: Specifies the transport mechanism to be used for the virtual\n"
                    "                           switch, as follows:\n"
                    "               IP\n"
                    "               ETHernet\n"
                    "             If vswitch_type=INMN is specified, the default for this value is ETHERNET\n"
                    "             (and it is the only allowed transport type for an INMN virtual switch).\n"
                    "             Otherwise,for all other vswitch types, the default of this value is IP.\n\n"
                    "           vlan_id: The VLAN ID. This can be any of the following values:\n"
                    "               UNAWARE\n"
                    "               AWARE\n"
                    "             1 - 4094 Any number in this range is a valid VLAN ID.\n"
                    "             If neither vlan_id= nor port_type= are specified, then vlan_id= defaults\n"
                    "             to UNAWARE.\n"
                    "             If vswitch_type=IEDN or INMN is specified, the default for this value is\n"
                    "             AWARE (and it is the only allowed value for either an IEDN or INMN virtual\n"
                    "             switch). Otherwise, for all other vswitch types, the default of this value\n"
                    "             is UNAWARE.\n\n"
                    "           port_type: Specifies the port type, as follows:\n"
                    "               ACCESS\n"
                    "               TRUNK\n"
                    "             If vlan_id= is specified but port_type= is not specified, then port_type= \n"
                    "             will default to ACCESS.\n"
                    "             If vlan_id==UNAWARE is specified, then you cannot specify port_type=,\n"
                    "             gvrp_value= or native_vlanid=.\n\n"
                    "           persist: This can be one of the following values:\n"
                    "             NO - The vswitch is updated on the active system, but is not updated in\n"
                    "                  the permanent configuration for the system.\n"
                    "             YES - The vswitch is updated on the active system and also in the permanent\n"
                    "                   configuration for the system.\n"
                    "             If not specified, the default is NO.\n\n"
                    "           gvrp_value: This can be one of the following values:\n"
                    "               GVRP\n"
                    "               NOGVRP\n"
                    "             If vlan_id=UNAWARE is not specified, then the default for this value is GVRP.\n"
                    "             If vlan_id=UNAWARE is specified, then you cannot specify port_type=,\n"
                    "             gvrp_value= or native_vlanid=.\n\n"
                    "           vswitch_type: The type of virtual switch to be created. This can be one of\n"
                    "                         the following values:\n"
                    "               QDIO\n"
                    "               IEDN\n"
                    "               INMN\n"
                    "             If not specified, the default is QDIO.\n\n"
                    "           iptimeout: A number between 1 and 240 specifying the length of time in\n"
                    "                      minutes that a remote IP address table entry remains in the IP\n"
                    "                      address table for the virtual switch.\n"
                    "             If not specified, the default is 5.\n\n"
                    "           port_selection: Indicates whether the vswitch is port-based or user-based,\n"
                    "                           as follows:\n"
                    "             PORTBASED: The virtual switch configuration and authorization will be on a\n"
                    "                        port basis. Each port must be configured using\n"
                    "                        VIRTUAL_NETWORK_VSWITCH_SET_EXTENDED.\n"
                    "             USERBASED: The virtual switch configuration and authorization will be on a\n"
                    "                        user ID basis. Port numbers for guests will be assigned by CP.\n"
                    "                        This is the default if not specified.\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating virtual switch... ");

    rc = smVirtual_Network_Vswitch_Create_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Create_Extended", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Create_Extended", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkVswitchDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Delete";
    int rc;
    int option;
    int updateSystemConfigIndicator = 0;
    char * image = NULL;
    char * switchName = "";
    char * systemConfigName = "";
    char * systemConfigType = "";
    char * parmDiskOwner = "";
    char * parmDiskNumber = "";
    char * parmDiskPassword = "";
    char * altSystemConfigName = "";
    char * altSystemConfigType = "";
    char * altParmDiskOwner = "";
    char * altParmDiskNumber = "";
    char * altParmDiskPassword = "";
    vmApiVirtualNetworkVswitchDeleteOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TnuLFRCPNYOMD";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:u:L:F:R:C:P:N:Y:O:M:D:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                switchName = optarg;
                break;

            case 'u':
                updateSystemConfigIndicator = atoi(optarg);
                break;

            case 'L':
                systemConfigName = optarg;
                break;

            case 'F':
                systemConfigType = optarg;
                break;

            case 'R':
                parmDiskOwner = optarg;
                break;

            case 'C':
                parmDiskNumber = optarg;
                break;

            case 'P':
                parmDiskPassword = optarg;
                break;

            case 'N':
                altSystemConfigName = optarg;
                break;

            case 'Y':
                altSystemConfigType = optarg;
                break;

            case 'O':
                altParmDiskOwner = optarg;
                break;

            case 'M':
                altParmDiskNumber = optarg;
                break;

            case 'D':
                altParmDiskPassword = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Vswitch_Delete\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Delete [-T] image_name [-n] switch_name\n"
                    "    [-u] update_indicator [-L] sys_config_name [-F] sys_config_type\n"
                    "    [-R] parm_disk_owner [-C] parm_disk_number [-P] parm_disk_passwd\n"
                    "    [-N] alt_sys_config_name [-Y] alt_sys_config_type [-O] alt_parm_disk_owner\n"
                    "    [-M] alt_parm_disk_number [-D] alt_parm_disk_passwd\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Delete to delete a virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T     The virtual image name of the owner of the virtual switch\n"
                    "    -n     The name of the virtual switch segment\n"
                    "  The following options are optional:\n"
                    "    -u  Update system config indicator. This can be any of the following values:\n"
                    "          0: Unspecified\n"
                    "          1: Delete the virtual switch from the active system\n"
                    "          2: Delete the virtual switch from the active system and delete the\n"
                    "             virtual switch definition from the system configuration file\n"
                    "          3: Delete the virtual switch definition from the system configuration\n"
                    "             file\n"
                    "    -L  File name of the system configuration file. The default is 'SYSTEM'.\n"
                    "    -F  File type of the system configuration file. The default is 'CONFIG'.\n"
                    "    -R  Owner of the parm disk. The default is 'MAINT'.\n"
                    "    -C  Number of the parm disk, as defined in the server's directory.\n"
                    "        The default is 'CF1'.\n"
                    "    -P  Multiwrite password for the parm disk. The default is ','.\n"
                    "    -N  File name of the second (alternative) system configuration file.\n"
                    "        The default is 'SYSTEM'.\n"
                    "    -Y  File type of the second (alternative) system configuration file.\n"
                    "        The default is 'CONFIG'.\n"
                    "    -O  Owner of the second (alternative) parm disk. The default is 'MAINT'.\n"
                    "    -M  Number of the second (alternative) parm disk. The default is 'CF2'.\n"
                    "    -D  Multiwrite password for the second (alternative) parm disk.\n"
                    "        The default is ','.\n");
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting virtual switch %s... ", switchName);

    rc = smVirtual_Network_Vswitch_Delete(vmapiContextP, "", 0, "",
            image, switchName, updateSystemConfigIndicator,
            systemConfigName, systemConfigType, parmDiskOwner, parmDiskNumber, parmDiskPassword,
            altSystemConfigName, altSystemConfigType, altParmDiskOwner, altParmDiskNumber,
            altParmDiskPassword, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Delete", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Delete", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkVswitchDeleteExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Delete_Extended";
    int rc;
    int entryCount = 0;
    int maxArrayCount = 2;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkVswitchDeleteExtendedOutput * output;

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

                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Vswitch_Delete_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Delete_Extended [-T] targetIdentifier\n"
                    "    [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Delete_Extended to delete a virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization, i.e. the authenticated user must have\n"
                    "          authorization to perform this function for this target.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            switch_name: The name of the virtual switch segment\n\n"
                    "            persist: This can be one of the following values:\n"
                    "              NO: The vswitch is deleted on the active system, but is not deleted\n"
                    "                  from the permanent configuration for the system.\n"
                    "              YES: The vswitch is deleted from the active system and also from the\n"
                    "                   permanent configuration for the system.\n"
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Deleting virtual switch... ");

    rc = smVirtual_Network_Vswitch_Delete_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Delete_Extended", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Delete_Extended",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkVswitchQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Query";
    int rc;
    int option;
    char * image = NULL;
    char * switchName = NULL;
    vmApiVirtualNetworkVswitchQueryOutput* output;

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
                switchName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Vswitch_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Query [-T] image_name [-s] switch_name\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Query to obtain information about the specified\n"
                    "  virtual switch or switches.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -s    The name of the virtual switch\n"
                    "          '*': All virtual switches\n");
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

    if (!image || !switchName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_Vswitch_Query(vmapiContextP, "", 0, "", image, switchName, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        int count = output->vswitchCount;
        if (count > 0) {
            int i, j, k, l, m;
            char * transportType;
            char * portType;
            char * routingValue;
            char * gvrpRequest;
            char * gvrpEnabled;
            char * switchStatus;
            char * deviceStatus;
            char * deviceErrorStatus;
            char * vlanIds;
            char * vlanId;
            for (i = 0; i < count; i++) {
                if (output->vswitchList[i].transportType == 1) {
                    transportType = "IP";
                } else if (output->vswitchList[i].transportType == 2) {
                    transportType = "Ethernet";
                } else {
                    transportType = "";
                }

                if (output->vswitchList[i].portType == 1) {
                    portType = "Access";
                } else if (output->vswitchList[i].portType == 2) {
                    portType = "Trunk";
                } else {
                    portType = "Unknown";
                }

                if (output->vswitchList[i].routingValue == 1) {
                    routingValue = "The device will not act as a router";
                } else if (output->vswitchList[i].routingValue == 2) {
                    routingValue = "The device will act as a router";
                } else {
                    routingValue = "";
                }

                if (output->vswitchList[i].grvpRequestAttribute == 1) {
                    gvrpRequest = "GVRP requested";
                } else if (output->vswitchList[i].grvpRequestAttribute == 2) {
                    gvrpRequest = "GVRP not requested";
                } else {
                    gvrpRequest = "";
                }

                if (output->vswitchList[i].grvpEnabledAttribute == 1) {
                    gvrpEnabled = "GVRP enabled";
                } else if (output->vswitchList[i].grvpEnabledAttribute == 2) {
                    gvrpEnabled = "GVRP not enabled";
                } else {
                    gvrpEnabled = "";
                }

                if (output->vswitchList[i].switchStatus == 1) {
                    switchStatus = "Virtual switch defined";
                } else if (output->vswitchList[i].switchStatus == 2) {
                    switchStatus = "Controller not available";
                } else if (output->vswitchList[i].switchStatus == 3) {
                    switchStatus = "Operator intervention required";
                } else if (output->vswitchList[i].switchStatus == 4) {
                    switchStatus = "Disconnected";
                } else if (output->vswitchList[i].switchStatus == 5) {
                    switchStatus = "Virtual devices attached to controller";
                } else if (output->vswitchList[i].switchStatus == 6) {
                    switchStatus = "OSA initialization in progress";
                } else if (output->vswitchList[i].switchStatus == 7) {
                    switchStatus = "OSA device not ready";
                } else if (output->vswitchList[i].switchStatus == 8) {
                    switchStatus = "OSA device ready";
                } else if (output->vswitchList[i].switchStatus == 9) {
                    switchStatus = "OSA devices being detached";
                } else if (output->vswitchList[i].switchStatus == 10) {
                    switchStatus = "Virtual switch delete pending";
                } else if (output->vswitchList[i].switchStatus == 11) {
                    switchStatus = "Virtual switch fail over recovering";
                } else if (output->vswitchList[i].switchStatus == 12) {
                    switchStatus = "Auto restart in progress";
                } else {
                    switchStatus = "";
                }

                printf("VSWITCH:"
                       "  Name: %s\n"
                       "  Transport type: %s\n"
                       "  Port type: %s\n"
                       "  Queue memory limit: %d\n"
                       "  Routing value: %s\n"
                       "  VLAN ID: %d\n"
                       "  Native VLAN ID: %d\n"
                       "  MAC ID: %012llX\n"
                       "  GVRP request attributes: %s\n"
                       "  GVRP enabled attributes: %s\n"
                       "  Switch status: %s\n", output->vswitchList[i].switchName, transportType, portType,
                       output->vswitchList[i].queueMemoryLimit, routingValue, output->vswitchList[i].vlanId,
                       output->vswitchList[i].nativeVlanId, output->vswitchList[i].macId, gvrpRequest,
                       gvrpEnabled, switchStatus);

                printf("  Devices:\n");
                for (j = 0; j < output->vswitchList[i].realDeviceCount; j++) {
                    if (output->vswitchList[i].realDeviceList[j].deviceStatus == 0) {
                        deviceStatus = "Device is not active";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceStatus == 1) {
                        deviceStatus = "Device is active";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceStatus == 2) {
                        deviceStatus = "Device is a backup device";
                    } else {
                        deviceStatus = "";
                    }

                    if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 0) {
                        deviceErrorStatus = "No error";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 1) {
                        deviceErrorStatus = "Port name conflict";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 2) {
                        deviceErrorStatus = "No layer 2 support";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 3) {
                        deviceErrorStatus = "Real device does not exist";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 4) {
                        deviceErrorStatus = "Real device is attached elsewhere";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 5) {
                        deviceErrorStatus = "Real device is not QDIO OSA-E";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 6) {
                        deviceErrorStatus = "Initialization error";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 7) {
                        deviceErrorStatus = "Stalled OSA";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 8) {
                        deviceErrorStatus = "Stalled controller";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 9) {
                        deviceErrorStatus = "Controller connection severed";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 10) {
                        deviceErrorStatus = "Primary or secondary routing conflict";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 11) {
                        deviceErrorStatus = "Device is offline";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 12) {
                        deviceErrorStatus = "Device was detached";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 13) {
                        deviceErrorStatus = "IP/Ethernet type mismatch";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 14) {
                        deviceErrorStatus = "Insufficient memory in controller virtual machine";
                    } else if (output->vswitchList[i].realDeviceList[j].deviceErrorStatus == 15) {
                        deviceErrorStatus = "TCP/IP configuration conflict";
                    } else {
                        deviceErrorStatus = "";
                    }
                    printf("    Real device: %04X\n"
                           "    Controller name: %s\n"
                           "    Port name: %s\n"
                           "    Device status: %s\n"
                           "    Device error status: %s\n\n", output->vswitchList[i].realDeviceList[j].realDeviceAddress,
                           output->vswitchList[i].realDeviceList[j].controllerName,
                           output->vswitchList[i].realDeviceList[j].portName, deviceStatus, deviceErrorStatus);
                }

                printf("  Authorized users:\n");
                for (k = 0; k < output->vswitchList[i].authorizedUserCount; k++) {
                    printf("    User: %s\n", output->vswitchList[i].authorizedUserList[k].grantUserid);
                }

                printf("  Connections:\n");
                for (m = 0; m < output->vswitchList[i].connectedAdapterCount; m++) {
                     printf("    Adapter owner: %s  Device number: %s\n",
                            output->vswitchList[i].connectedAdapterList[m].adapterOwner,
                            output->vswitchList[i].connectedAdapterList[m].imageDeviceNumber);
                }
            }
        }
    }
    return rc;
}

int virtualNetworkVswitchQueryExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Query_Extended";
    int rc;
    int i;
    int j;
    int k;
    int entryCount = 0;
    int maxArrayCount = 2;
    int option;
    int smapiLevel = 0;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    // vswitch_attr_info_structure
    char switch_name[8 + 1];
    char transport_type[8 + 1];
    char port_type[6 + 1];
    char queue_memory_limit[3 + 1];
    char routing_value[9 + 1];
    char vlan_awareness[7 + 1];
    char vlan_id[8 +1];
    char native_vlan_id[8 + 1];
    char mac_address[17 + 1];
    char gvrp_request_attribute[6 + 1];
    char gvrp_enabled_attribute[6 + 1];
    char switch_status[2 + 1];
    char link_ag[5 + 1];
    char lag_interval[3 + 1];
    char lag_group[8 + 1];
    char IP_timeout[3 + 1];
    char switch_type[4 + 1];
    char isolation_status[11 + 1];
    char MAC_protect[13 + 1];
    char user_port_based[9 + 1];
    char VLAN_counters[10 + 1];
    char vepa_status[3 + 1];   // zVM 6.3 var
    char spg_scope[7 + 1];   // zVM 6.3 var after apar for MVLAG

    // real_device_info_structure
    char real_device_address[4 + 1];
    char virtual_device_address[4 + 1];
    char controller_name[71 + 1];
    char port_name[8 + 1];
    char device_status[1 + 1];
    char device_error_status[2 + 1];

    // authorized_user_structure
    char port_num[16 + 1];
    char grant_userid[8 + 1];
    char promiscuous_mode[6 + 1];
    char osd_sim[8 + 1];
    char vlan_count[2 + 1];
    char user_vlan_id[8 + 1];
    int vlanCount = 0;

    // connected_adapter_structure
    char adapter_owner[8 + 1];
    char adapter_vdev[4 + 1];
    char adapter_macaddr[17 + 1];
    char adapter_type[12 + 1];

    // uplink_NIC_structure
    char uplink_NIC_userid[8 + 1];
    char uplink_NIC_vdev[4 + 1];
    char uplink_NIC_error_status[3 + 1];

    // global member array
    char global_member_name[8 + 1];
    char global_member_state[7 + 1];

    char * blank = " ";
    char *token;
    char * buffer;
    vmApiVirtualNetworkVswitchQueryExtendedOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[1200];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;


    rc = getSmapiLevel(vmapiContextP, " ", &smapiLevel);
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

                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Vswitch_Query_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Query_Extended [-T] targetIdentifier\n"
                    "    [-k] entry\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Query_Extended to obtain information about the\n"
                    "   specified virtual switch or switches.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization, i.e. the authenticated user must have\n"
                    "          authorization to perform this function for this target.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            switch_name= The name of the virtual switch segment\n"
                    "                         '*'  All virtual switches\n");
                if (smapiLevel >= 630) {
                   printf("            vepa_status= One of the following:\n"
                          "               YES: Indicates that the vepa_status output parameter\n"
                          "                    will be included in the vswitch_attr_info_structure.\n"
                          "               NO:  Indicates that the vepa_status output parameter will\n"
                          "                    not be included in the vswitch_attr_info_structure.\n"
                          "                    This is the default.");
                }
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


    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smVirtual_Network_Vswitch_Query_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Query_Extended", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Query_Extended",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i=0; i < output->vswitchArrayCountCalculated; i++ ) {
            // Get the vswitch_attr_info_structure
            token = strtok_r((char *)(output->vswitchList[i].vswitchAttributes), blank, &buffer);
            if (token != NULL) {
                strcpy(switch_name, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error switch_name is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(transport_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error transport_type is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(port_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error port_type is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(queue_memory_limit, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error queue_memory_limit is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(routing_value, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error routing_value is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vlan_awareness, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error vlan_awareness is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vlan_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error vlan_id is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(native_vlan_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error native_vlan_id is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(mac_address, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error mac_address is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(gvrp_request_attribute, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error gvrp_request_attribute is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(gvrp_enabled_attribute, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error gvrp_enabled_attribute is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(switch_status, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error switch_status is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(link_ag, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error link_ag is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(lag_interval, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error lag_interval  is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(lag_group, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error lag_group is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(IP_timeout, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error IP_timeout is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(switch_type, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error switch_type is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(isolation_status, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error isolation_status is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(MAC_protect, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error MAC_protect is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(user_port_based, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error user_port_based is NULL!!\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            if (smapiLevel < 630) {
                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(VLAN_counters, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error VLAN_counters is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
            } else {
                token = strtok_r(NULL, " \0", &buffer);
                if (token != NULL) {
                    strcpy(VLAN_counters, token);
                } else {
                    printf("Error VLAN_counters is NULL!!\n");
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error VLAN_counters is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                strcpy(spg_scope, "");

                // vepa status may not appear in output,
                token = strtok_r(NULL, " \0", &buffer);
                if (token != NULL) {
                    strcpy(vepa_status, token);
                    // spg scope will only appear if vespa does
                    token = strtok_r(NULL, " \0", &buffer);
                    if (token != NULL) {
                        strcpy(spg_scope, token);
                    }
                } else strcpy(vepa_status, "");

            }
            snprintf(strMsg, sizeof(strMsg),
                   " switch_name: %s\n"
                   " transport_type: %s\n"
                   " port_type: %s\n"
                   " queue_memory_limit: %s\n"
                   " routing_value: %s\n"
                   " vlan_awareness: %s\n"
                   " vlan_id: %s\n"
                   " native_vlan_id: %s\n"
                   " mac_address: %s\n"
                   " gvrp_request_attribute: %s\n"
                   " gvrp_enabled_attribute: %s\n"
                   " switch_status: %s\n"
                   " link_ag: %s\n"
                   " lag_interval: %s\n"
                   " lag_group: %s\n"
                   " IP_timeout: %s\n"
                   " switch_type: %s\n"
                   " isolation_status: %s\n"
                   " MAC_protect: %s\n"
                   " user_port_based: %s\n"
                   " VLAN_counters: %s\n",
                  switch_name, transport_type, port_type, queue_memory_limit, routing_value, vlan_awareness,
                  vlan_id, native_vlan_id, mac_address, gvrp_request_attribute, gvrp_enabled_attribute,
                  switch_status, link_ag, lag_interval, lag_group, IP_timeout, switch_type,
                  isolation_status, MAC_protect, user_port_based, VLAN_counters);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            if (smapiLevel >= 630 && strlen(vepa_status)) {
                snprintf(strMsg, sizeof(strMsg), " vepa_status: %s\n", vepa_status);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            }
            if (smapiLevel >= 630 && strlen(spg_scope)) {
                snprintf(strMsg, sizeof(strMsg), " spg_scope: %s\n", spg_scope);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            }

            for (j = 0; j < output->vswitchList[i].realDeviceCount; j++) {
                // Get real_device_info_structure
                token = strtok_r((char *)(output->vswitchList[i].realDeviceList[j].realDeviceFields), blank, &buffer);
                if (token != NULL) {
                    strcpy(real_device_address, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error real_device_address is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(virtual_device_address, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error virtual_device_address is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(controller_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error controller_name is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(port_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error port_name is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(device_status, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error device_status is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(device_error_status, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error device_error_status is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg),
                       "real_device_address: %s\n"
                       "virtual_device_address: %s\n"
                       "controller_name: %s\n"
                       "port_name: %s\n"
                       "device_status: %s\n"
                       "device_error_status %s\n",
                       real_device_address, virtual_device_address, controller_name, port_name,
                       device_status, device_error_status);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }

            } // end j < output->vswitchList[i].realDeviceCount

            for (j = 0; j < output->vswitchList[i].authUserCount; j++) {
                // Get authorized_user_structure
                token = strtok_r((char *)(output->vswitchList[i].authUserList[j].authUserFields), blank, &buffer);
                if (token != NULL) {
                    strcpy(port_num, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error port_num is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(grant_userid, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error grant_userid is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(promiscuous_mode, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error promiscuous_mode is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(osd_sim, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error osd_sim is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(vlan_count, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error vlan_count is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                vlanCount = atoi(vlan_count);
                char vlan_info[vlanCount * 9];
                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(vlan_info, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error vlan_info is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                       "port_num: %s\n"
                       "grant_userid: %s\n"
                       "promiscuous_mode: %s\n"
                       "osd_sim: %s\n"
                       "vlan_count: %s\n",
                       port_num, grant_userid, promiscuous_mode, osd_sim, vlan_count );
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }

                token = strtok_r(vlan_info, blank, &buffer);
                if (token != NULL) {
                    strcpy(user_vlan_id, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error user_vlan_id is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                printf("user_vlan_id: %s\n", user_vlan_id);
                for (k =1; k < vlanCount; k++) {
                    token = strtok_r(NULL, blank, &buffer);
                    if (token != NULL) {
                        strcpy(user_vlan_id, token);
                    } else {
                        if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error user_vlan_id is NULL!!\n"))) {
                            rc = OUTPUT_ERRORS_FOUND;
                        }
                        goto end;
                    }
                    snprintf(strMsg, sizeof(strMsg), "user_vlan_id: %s\n", user_vlan_id);
                    if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                        goto end;
                    }
                } // end of k < vlanCount

            } //end j < output->vswitchList[i].authUserCount

            for (j = 0; j < output->vswitchList[i].adapterCount; j++) {
                // Get connected_adapter_structure
                token = strtok_r((char *)(output->vswitchList[i].connAdapterList[j].connAdapterFields), blank, &buffer);
                if (token != NULL) {
                    strcpy(adapter_owner, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error adapter_owner is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(adapter_vdev, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error adapter_vdev is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(adapter_macaddr, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error adapter_macaddr is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(adapter_type, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error adapter_type is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                snprintf(strMsg, sizeof(strMsg),
                       "adapter_owner: %s\n"
                       "adapter_vdev: %s\n"
                       "adapter_macaddr: %s\n"
                       "adapter_type: %s\n",
                       adapter_owner, adapter_vdev, adapter_macaddr, adapter_type);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            } //end j < output->vswitchList[i].authUserCount

            for (j = 0; j < output->vswitchList[i].uplinkNicCount; j++) {
                // Get uplink_NIC_structure
                token = strtok_r((char *)(output->vswitchList[i].uplinkNicList[j].uplinkNICFields), blank, &buffer);
                if (token != NULL) {
                    strcpy(uplink_NIC_userid, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error uplink_NIC_userid is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(uplink_NIC_vdev, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error uplink_NIC_vdev is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, "\0", &buffer);

                if (token != NULL) {
                    strcpy(uplink_NIC_error_status, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error uplink_NIC_error_status is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                       "uplink_NIC_userid: %s\n"
                       "uplink_NIC_vdev: %s\n"
                       "uplink_NIC_error_status: %s\n",
                       uplink_NIC_userid, uplink_NIC_vdev, uplink_NIC_error_status);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            } //end j < output->vswitchList[i].uplinkNicCount

            for (j = 0; j < output->vswitchList[i].globalMemberCount; j++) {
                // Get global member structures
                token = strtok_r((char *)(output->vswitchList[i].globalMemberList[j].globalmemberFields), blank, &buffer);
                if (token != NULL) {
                    strcpy(global_member_name, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error global_member_name is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(global_member_state, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error global_member_state is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                       "global_member_name: %s\n"
                       "global_member_state: %s\n",
                       global_member_name, global_member_state);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            } //end j < output->vswitchList[i].globalMemberCount

        } // end i < output->vswitchArrayCountCalculated
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


int virtualNetworkVswitchQueryStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Query_Stats";
    int rc;
    int i;
    int j;
    int k;
    int segmentDataSize;
    int entryCount = 0;
    int maxArrayCount = 2;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    char seg_vlanid[10 + 1];
    char seg_rx[10 + 1];
    char seg_rx_disc[10 + 1];
    char seg_tx[10 + 1];
    char seg_tx_disc[10 + 1];
    char seg_activated_TOD[10 + 1];
    char seg_config_update_TOD[10 + 1];
    char seg_vlan_interfaces[10 + 1];
    char seg_vlan_deletes[10 + 1];
    char seg_device_type[4 +1];
    char seg_device_addr[4 + 1];
    char seg_device_status[1 + 1];
    char tempBuff[130];
    char *token;
    char *buffer;  // char * whose value is preserved between successive related calls to strtok_r.
    const char * blank = " ";
    vmApiVirtualNetworkVswitchQueryStatsOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[1200];

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

                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Vswitch_Query_Stats\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Query_Stats [-T] targetIdentifier\n"
                    "   [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Query_Stats to query a virtual switch's\n"
                    "  statistics.\n\n"
                    "  The following options are required:\n"
                    "    -T    Used strictly for authorization, i.e. the authenticated user must have\n"
                    "          authorization to perform this function for this target.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            switch_name: The name of the virtual switch segment\n\n"
                    "            fmt_version: The format version of this API, for calls to DIAGNOSE X'26C'.\n"
                    "              For V6.2, the supported format version value is 4. This is an\n"
                    "              optional parameter.\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }
    rc = smVirtual_Network_Vswitch_Query_Stats(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Query_Stats", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Query_Stats",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, "");
    } else {
        for (i = 0; i < output->vswitchArrayCount; i++) {
            snprintf(strMsg, sizeof(strMsg), "switch_name = %s\n", output->vswitchList[i].vswitchName);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg), "segmentCount = %d\n", output->vswitchList[i].segmentCount);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            for (j = 0; j < output->vswitchList[i].segmentCount; j++) {
                memset(tempBuff, 0x00, 130);
                segmentDataSize = strlen((char *)output->vswitchList[i].segmentArray[j].segmentData);
                strncpy(tempBuff, (char *)output->vswitchList[i].segmentArray[j].segmentData, segmentDataSize);
                trim(tempBuff);
                tempBuff[segmentDataSize + 1] = '\0';

                token = strtok_r(tempBuff, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_vlanid, token);
                } else {
                    printf("Error seg_vlanid is NULL!!\n");
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_vlanid is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }
                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_rx, token);
                } else {
                    printf("Error seg_rx is NULL!!\n");
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_rx is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_rx_disc, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_rx_disc is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_tx, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_tx is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_tx_disc, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_tx_disc is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_activated_TOD, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_activated_TOD is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_config_update_TOD, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, " Error seg_config_update_TOD is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_vlan_interfaces, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_vlan_interfaces is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_vlan_deletes, token);
                } else {
                   if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_vlan_deletes is NULL!!\n"))) {
                       rc = OUTPUT_ERRORS_FOUND;
                   }
                   goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_device_type, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_device_type is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, blank, &buffer);
                if (token != NULL) {
                    strcpy(seg_device_addr, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_device_addr is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                token = strtok_r(NULL, "\0", &buffer);
                if (token != NULL) {
                    strcpy(seg_device_status, token);
                } else {
                    if (0 == (rc = addMessageToBuffer(&saveMsgs, "Error seg_device_status is NULL!!\n"))) {
                        rc = OUTPUT_ERRORS_FOUND;
                    }
                    goto end;
                }

                snprintf(strMsg, sizeof(strMsg),
                         "seg_vlanid            = %s\n"
                         "seg_rx                = %s\n"
                         "seg_rx_disc           = %s\n"
                         "seg_tx                = %s\n"
                         "seg_tx_disc           = %s\n"
                         "seg_activated_TOD     = %s\n"
                         "seg_config_update_TOD = %s\n"
                         "seg_vlan_interfaces   = %s\n"
                         "seg_vlan_deletes      = %s\n"
                         "seg_device_type       = %s\n"
                         "seg_device_addr       = %s\n"
                         "seg_device_status     = %s\n\n",
                         j+1, seg_vlanid, seg_rx, seg_rx_disc, seg_tx, seg_tx_disc,
                         seg_activated_TOD, seg_config_update_TOD, seg_vlan_interfaces,
                         seg_vlan_deletes, seg_device_type, seg_device_addr, seg_device_status);
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

int virtualNetworkVswitchSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Set";
    int rc;
    int option;
    int connectionValue = 0;
    int queueMemoryLimit = -1;
    int routingValue = 0;
    int portType = 0;
    int updateSystemConfigIndicator = 0;
    int gvrpValue = 0;
    char * image = NULL;
    char * switchName = "";
    char * grantUserid = "";
    char * userVlanId = "";
    char * revokeUserid = "";
    char * realDeviceAddress = "";
    char * portName = "";
    char * controllerName = "";
    char * systemConfigName = "";
    char * systemConfigType = "";
    char * parmDiskOwner = "";
    char * parmDiskNumber = "";
    char * parmDiskPassword = "";
    char * altSystemConfigName = "";
    char * altSystemConfigType = "";
    char * altParmDiskOwner = "";
    char * altParmDiskNumber = "";
    char * altParmDiskPassword = "";
    char * macId = "";
    char vlanIDcopy[20];
    int tempLength;
    int i;
    int commaCount = 0;
    vmApiVirtualNetworkVswitchSetOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "TnIvUraicqepuLFRCPNYOMDGVm";
    char tempStr[1];
    char strMsg[250];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:n:I:v:U:r:a:i:c:q:e:p:u:L:F:R:C:P:N:Y:O:M:D:G:V:m:h?")) != -1)
         switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'n':
                switchName = optarg;
                break;

            case 'I':
                grantUserid = optarg;
                break;

            case 'v':
                userVlanId = optarg;
                break;

            case 'U':
                revokeUserid = optarg;
                break;

            case 'r':
                realDeviceAddress = optarg;
                break;

            case 'a':
                portName = optarg;
                break;

            case 'i':
                controllerName = optarg;
                break;

            case 'c':
                connectionValue = atoi(optarg);
                break;

            case 'q':
                queueMemoryLimit = atoi(optarg);
                break;

            case 'e':
                routingValue = atoi(optarg);
                break;

            case 'p':
                portType = atoi(optarg);
                break;

            case 'u':
                updateSystemConfigIndicator = atoi(optarg);
                break;

            case 'L':
                systemConfigName = optarg;
                break;

            case 'F':
                systemConfigType = optarg;
                break;

            case 'R':
                parmDiskOwner = optarg;
                break;

            case 'C':
                parmDiskNumber = optarg;
                break;

            case 'P':
                parmDiskPassword = optarg;
                break;

            case 'N':
                altSystemConfigName = optarg;
                break;

            case 'Y':
                altSystemConfigType = optarg;
                break;

            case 'O':
                altParmDiskOwner = optarg;
                break;

            case 'M':
                altParmDiskNumber = optarg;
                break;

            case 'D':
                altParmDiskPassword = optarg;
                break;

            case 'G':
                gvrpValue = atoi(optarg);
                break;

            case 'm':
                macId = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  Virtual_Network_Vswitch_Set\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Set [-T] image_name [-n] switch_name\n"
                    "    [-I] grant_userid [-r] real_device_address [-a] port_name [-i] controller_name\n"
                    "    [-c] connection_value [-q] queue_memory_limit [-e] routing_value\n"
                    "    [-t] transport_type [-v] vlan_id [-p] port_type [-u] update_sys_config\n"
                    "    [-L] sys_config_name [-F] sys_config_type [-R] parm_disk_owner\n"
                    "    [-C] parm_disk_number [-P] parm_disk_passwd [-N] alt_sys_config_name\n"
                    "    [-Y] alt_sys_config_type [-O] alt_parm_disk_owner [-M] alt_parm_disk_number\n"
                    "    [-D] alt_parm_disk_passwd [-G] gvrp [-m] mac_id\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Set to change the configuration of an existing\n"
                    "  virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    The virtual image name of the owner of the virtual switch\n"
                    "    -n    The name of the virtual switch segment\n"
                    "  The following options are optional:\n"
                    "    -I    A userid to be added to the access list for the specified virtual\n"
                    "          switch\n"
                    "    -v    The user VLAN ID, a range, or a comma separated list. Maximum of 19 chars\n"
                    "    -U    A userid to be removed from the access list for the specified\n"
                    "          virtual switch\n"
                    "    -r    The real device address of a real OSA-Express QDIO device used to\n"
                    "          create the switch to the virtual adapter\n"
                    "    -a    The name used to identify the OSA Expanded adapter\n"
                    "    -i    The userid controlling the real device\n"
                    "    -c    Connection value:\n"
                    "            0: Unspecified\n"
                    "            1: Activate the real device connection\n"
                    "            2: Do not activate the real device connection\n"
                    "    -q    Queue memory limit. A number between 1 and 8 specifying the QDIO\n"
                    "          buffer size in megabytes. If unspecified, the default is 8.\n"
                    "    -e    Specifies whether the OSA-Express QDIO device will act as a router\n"
                    "          to the virtual switch, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: NONROUTER ~ The OSA-Express device will not act as a router to\n"
                    "               the virtual switch\n"
                    "            2: PRIROUTER ~ The OSA-Express device identified will act as a\n"
                    "               primary router to the virtual switch\n"
                    "    -p    Specifies the port type, as follows:\n"
                    "            0: Unspecified\n"
                    "            1: ACCESS\n"
                    "            2: TRUNK\n"
                    "    -u    Update system config indicator.This can be any of the following\n"
                    "          values:\n"
                    "            0: Unspecified\n"
                    "            1: Update the virtual switch definition on the active system\n"
                    "            2: Update the virtual switch definition on the active system and in\n"
                    "               the system configuration file\n"
                    "            3: Update the virtual switch definition in the system configuration\n"
                    "               file\n"
                    "    -L    File name of the system configuration file. The default is 'SYSTEM'.\n"
                    "    -F    File type of the system configuration file. The default is 'CONFIG'.\n"
                    "    -R    Owner of the parm disk. The default is 'MAINT'.\n"
                    "    -C    Number of the parm disk, as defined in the server's directory.\n"
                    "          The default is 'CF1'.\n"
                    "    -P    Multiwrite password for the parm disk. The default is ','.\n"
                    "    -N    File name of the second (alternative) system configuration file.\n"
                    "          The default is 'SYSTEM'.\n"
                    "    -Y    File type of the second (alternative) system configuration file.\n"
                    "          The default is 'CONFIG'.\n"
                    "    -O    Owner of the second (alternative) parm disk. The default is 'MAINT'.\n"
                    "    -M    Number of the second (alternative) parm disk. The default is 'CF2'.\n"
                    "    -D    Multiwrite password for the second (alternative) parm disk.\n"
                    "          The default is ','.\n"
                    "    -G    GVRP value. This can be any of the following values:\n"
                    "            0: Unspecified\n"
                    "            1: GVRP\n"
                    "            2: NOGVRP\n"
                    "    -m    The MAC identifier\n");
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

    if (!image || !switchName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    tempLength = strlen(userVlanId);
    if (tempLength > 19) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: vlanId cannot be longer than 19 characters\n");
        return 1;
    }

    strcpy(vlanIDcopy, userVlanId);
    if (tempLength > 0) {
        // If any commas in the string change it to blanks for SMAPI
        for (i=0; i< tempLength; i++) {
            if (vlanIDcopy[i] == ',') {
                vlanIDcopy[i] = ' ';
                commaCount++;
            }
        }
        if (commaCount >= 0 && (tempLength==commaCount)) {
            DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
            printf("ERROR: vlanId has only commas, must contain vlan id numbers\n");
            return 1;
        }
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Changing configuration of virtual switch %s... ", switchName);

    rc = smVirtual_Network_Vswitch_Set(vmapiContextP, "", 0, "",
            image, switchName,  grantUserid, vlanIDcopy, revokeUserid, realDeviceAddress,
            portName, controllerName, connectionValue, queueMemoryLimit, routingValue, portType,
            updateSystemConfigIndicator, systemConfigName, systemConfigType, parmDiskOwner, parmDiskNumber,
            parmDiskPassword, altSystemConfigName, altSystemConfigType, altParmDiskOwner,
            altParmDiskNumber, altParmDiskPassword, gvrpValue, macId, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Set", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Set",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int virtualNetworkVswitchSetExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Virtual_Network_Vswitch_Set_Extended";
    int rc;
    int i;
    int entryCount = 0;
    int maxArrayCount = 33;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[maxArrayCount];
    vmApiVirtualNetworkVswitchSetExtendedOutput * output;

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

                if (entryCount < maxArrayCount) {
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
                    "  Virtual_Network_Vswitch_Set_Extended\n\n"
                    "SYNOPSIS\n"
                    "  smcli Virtual_Network_Vswitch_Set_Extended [-T] targetIdentifier\n"
                    "   [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use Virtual_Network_Vswitch_Set_Extended to change the configuration of an\n"
                    "  existing virtual switch.\n\n"
                    "  The following options are required:\n"
                    "    -T    The virtual image name of the owner of the virtual switch.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order.\n\n"
                    "            switch_name: The name of the virtual switch segment\n\n"
                    "            grant_userid: A userid to be added to the access list for the specified\n"
                    "                          virtual switch. This userid will be allowed to connect to the\n"
                    "                          switch through a QDIO device.:\n\n"
                    "            user_vlan_id: The user VLAN ID can be specified in the following ways:\n"
                    "                          As single values between 1 and 4094. A maximum of four values may be\n"
                    "                          specified, separated by blanks. Example: 1010 2020 3030 4040\n"
                    "                          As a range of two numbers, separated by a dash (-). A maximum of two\n"
                    "                          ranges may be specified. Example: 10-12 20-22\n\n"
                    "            revoke_userid: A userid to be removed from the access list for the specified\n"
                    "                           virtual switch. This userid will no longer be allowed to\n"
                    "                           connect to the switch but existing connections will not be\n"
                    "                           broken.\n\n"
                    "            real_device_address: The real device address or the real device address and\n"
                    "                                 OSA Express port number of a QDIO OSA Express device to\n"
                    "                                 be used to create the switch to the virtual adapter.\n"
                    "                                 If using a real device and an OSA Express port number,\n"
                    "                                 specify the real device number followed by a period\n"
                    "                                 (.), the letter 'P' (or 'p'), followed by the port\n"
                    "                                 number as a hexadecimal number. A maximum of three\n"
                    "                                 device addresses, all 1-7 characters in length, may be\n"
                    "                                 specified, delimited by blanks. 'None' may also be\n"
                    "                                 specified.\n\n"
                    "            port_name: The name used to identify the OSA Expanded adapter. A maximum of\n"
                    "                       three port names, all 1-8 characters in length, may be\n"
                    "                       specified, delimited by blanks.\n\n"
                    "            controller_name: One of the following:\n"
                    "                             The userid controlling the real device. A maximum of eight\n"
                    "                             userids, all 1-8 characters in length, may be specified,\n"
                    "                             delimited by blanks. (string,1,*) Specifies that any\n"
                    "                             available controller may be used.\n\n"
                    "            connection_value: This can be one of the following values:\n"
                    "              CONnect: Activate the real device connection.\n"
                    "              DISCONnect: Do not activate the real device connection.\n\n"
                    "            queue_memory_limit: A number between 1 and 8 specifying the QDIO buffer size\n"
                    "                                in megabytes.\n\n"
                    "            routing_value: Specifies whether the OSA-Express QDIO device will act as a\n"
                    "                           router to the virtual switch, as follows:\n"
                    "              NONrouter - The OSA-Express device identified in real_device_address= will\n"
                    "                          not act as a router to the virtual switch.\n"
                    "              PRIrouter - The OSA-Express device identified in real_device_address= will\n"
                    "                          act as a primary router to the virtual switch.\n\n"
                    "            port_type: Specifies the port type, as follows:\n"
                    "                ACCESS\n"
                    "                TRUNK\n\n"
                    "            persist: This can be one of the following values:\n"
                    "              NO - The vswitch is updated on the active system, but is not updated in\n"
                    "                   the permanent configuration for the system.\n"
                    "              YES - The vswitch is updated on the active system and also in the permanent\n"
                    "                    configuration for the system. If not specified, the default is NO.\n\n"
                    "            gvrp_value: This can be one of the following values:\n"
                    "                GVRP\n"
                    "                NOGVRP\n\n"
                    "            mac_id: The MAC identifier.\n"
                    "              Note: This value should only be specified for virtual switch type of QDIO.\n"
                    "              A user-defined MAC address is not allowed on types IEDN or INMN.\n\n"
                    "            uplink: One of the following:\n"
                    "              NO - The userid on the grant must use an IEDN or INMN type NIC adapter\n"
                    "                   when coupling to a IEDN or INMN type virtual switch (respectively).\n"
                    "              YES - A virtual NIC created by a DEFINE NIC TYPE QDIO CP command is allowed\n"
                    "                    to couple to an IEDN or INMN type virtual switch.\n\n"
                    "            nic_userid: One of the following:\n"
                    "              The userid of the port to/from which the UPLINK port will be\n"
                    "              connected or disconnected.\n"
                    "              Disconnect - The currently connected guest port to/from the special\n"
                    "                           virtual switch UPLINK port. (This is equivalent to specifying\n"
                    "                           NIC NONE on CP SET VSWITCH).\n"
                    "              Note: If a userid (not *) is specified, then nic_vdev= must also be specified.\n\n"
                    "            nic_vdev: The virtual device to/from which the the UPLINK port will be\n"
                    "                      connected/disconnected.\n"
                    "              Note: If this value is specified, nic_userid= must also be specified, with\n"
                    "              a userid\n\n"
                    "            lacp: One of the following values:\n"
                    "              ACTIVE - Indicates that the virtual switch will initiate negotiations with\n"
                    "                       the  physical switch via the link aggregation control protocol\n"
                    "                       (LACP) and will respond to LACP packets sent by the physical\n"
                    "                       switch.\n"
                    "              INACTIVE - Indicates that aggregation is to be performed, but without LACP.\n\n"
                    "            interval: The interval to be used by the control program (CP) when doing load\n"
                    "                      balancing of conversations across multiple links in the group. This\n"
                    "                      can be any of the following values:\n"
                    "              1-9990 - Indicates the number of seconds between load balancing\n"
                    "                       operations across the link aggregation group.\n"
                    "              OFF - Indicates that no load balancing is done.\n\n"
                    "            group_rdev: The real device address or the real device address and OSA Express\n"
                    "                        port number of a QDIO OSA Express device to be affected within the\n"
                    "                        link aggregation group associated with this vswitch. If using a\n"
                    "                        real device and an OSA Express port number, specify the real\n"
                    "                        device number followed by a period (.), the letter 'P' (or 'p'),\n"
                    "                        followed by the port number as a hexadecimal number. A maximum of\n"
                    "                        eight device addresses, all 1-7 characters in length, may be\n"
                    "                        specified, delimited by blanks.\n"
                    "              Note: If a real device address is specified, this device will be added to the\n"
                    "              link aggregation group associated with this vswitch. (The link aggregation\n"
                    "              group will be created if it does not already exist.)\n\n"
                    "            iptimeout: A number between 1 and 240 specifying the length of time in minutes\n"
                    "                       that a remote IP address table entry remains in the IP address\n"
                    "                       table for the virtual switch.\n\n"
                    "            port_isolation: One of the following:\n"
                    "                ON\n"
                    "                OFF\n\n"
                    "            promiscuous: One of the following:\n"
                    "              NO - The userid or port on the grant is not authorized to use the vswitch in\n"
                    "                   promiscuous mode\n"
                    "              YES - The userid or port on the grant is authorized to use the vswitch in\n"
                    "                    promiscuous mode.\n\n"
                    "            MAC_protect: One of the following:\n"
                    "                ON\n"
                    "                OFF\n"
                    "                UNSPECified\n\n"
                    "            VLAN_counters: One of the following:\n"
                    "                ON\n"
                    "                OFF\n\n"
                    "            nic_portselection: One of the following:\n"
                    "                AUTO - CP will assign the port number\n"
                    "                PORTNUM - The application specifies the port number.\n\n"
                    "              If not specified, AUTO is the default. If specified, nic_userid= must\n"
                    "              also be specified.\n\n"
                    "            portnum: Port number,followed by the userid. This parameter may be specified\n"
                    "                     with one or more of the following:\n"
                    "              port_type=value\n"
                    "              promiscuous=value\n"
                    "              osd_sim=value\n"
                    "              user_vlan_id=value\n\n"
                    "            portnum_modify: Port number to modify. This parameter must be specified\n"
                    "                            with one or more of the following:\n"
                    "              port_type=value\n"
                    "              promiscuous=value\n"
                    "              osd_sim=value\n\n"
                    "              user_vlan_id=value\n\n"
                    "            portnum_remove: Port number to remove.\n\n"
                    "            vlan_port_add: The VLAN ID, followed by a set of valid port numbers\n"
                    "                           (between 1 and 2048, inclusive). This set may contain ranges.\n\n"
                    "            vlan_port_remove: The VLAN ID, followed by a set of valid port numbers\n"
                    "                              (between 1 and 2048, inclusive). See examples above in\n"
                    "                               vlan_port_add=value.\n\n"
                    "            vlan_delete: The VLAN ID to be deleted.\n\n"
                    "            vepa: The operational mode of the virtual switch with regard to\n"
                    "                  forwarding guest-to-guest and guest-to-external destination\n"
                    "                  communications, as follows:"
                    "                    ON Prohibits guests from sending traffic to other guests on\n"
                    "                       the same virtual switch\n"
                    "                    OFF Allows guests to communicate with each other and with\n"
                    "                        any hosts");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Changing virtual switch configuration ... ");

    rc = smVirtual_Network_Vswitch_Set_Extended(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("Virtual_Network_Vswitch_Set_Extended", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Virtual_Network_Vswitch_Set_Extended",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}
