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
#include "smcliVMRelocate.h"
#include "wrapperutils.h"


int vmRelocate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRELOCATE";
    int rc;
    int i;
    int entryCount = 0;
    int option;
    int destSpecified = 0;
    int cancelSpecified = 0;
    char * targetIdentifier = NULL;
    char * entryArray[6];
    vmApiVMRelocateOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[150] = "";

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
                if (entryCount < 6) {
                    entryArray[entryCount] = optarg;
                    if (( strlen(optarg) > 12) && (strncasecmp( "destination=", optarg, 12 ) == 0 )) {
                    	destSpecified = 1;
                    } else
                    if (( strlen(optarg) >= 13) && (strncasecmp( "action=cancel", optarg, 13 ) == 0 )) {
                        cancelSpecified = 1;
                    }
                    entryCount++;
                } else {
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }

                break;

            case 'h':
                printf("NAME\n"
                    "  VMRELOCATE\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRELOCATE [-T] targetIdentifier\n"
                    "  [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRELOCATE to relocate, test relocation eligibility, or cancel the \n"
                    "  relocation of the specified virtual machine, while it continues to run,\n"
                    "  to the specified system  within the z/VM SSI cluster.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine whose relocation to another system\n"
                    "          within the z/VM SSI cluster will be initiated, tested, or canceled.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords are:\n"
                    "              destination: The z/VM SSI cluster name of the destination system\n"
                    "                           to which the specified virtual machine will be\n"
                    "                           relocated.\n"
                    "                  * Note that this parameter is not used when canceling a\n"
                    "                    relocation. If it is specified with 'action=CANCEL', it\n"
                    "                    will be ignored.\n\n"
                    "              action: One of the following:\n"
                    "                MOVE - Initiate a VMRELOCATE MOVE of the virtual machine\n"
                    "                       specified in target_identifier.\n"
                    "                TEST - Test the specified virtual machine and determine if it\n"
                    "                       is eligible to be relocated to the specified system. If\n"
                    "                       TEST is specified, all other valid additional input\n"
                    "                       parameters except destination = are ignored.\n"
                    "                       If action = is not, specified TEST is the default.\n\n"
                    "                CANCEL - Stop the relocation of the specified virtual machine.\n"
                    "                         If CANCEL is specified, all other additional input\n"
                    "                         parameter are ignored.\n\n"
                    "              force: Any combination of the following may be specified,\n"
                    "                     in any order:\n"
                    "                ARCHITECTURE - Indicates that relocation is to be attempted\n"
                    "                               even though the virtual machine is currently\n"
                    "                               running on a system with hardware architecture\n"
                    "                               facilities or CP-supplied features not\n"
                    "                               available on the destination system\n"
                    "                               For example, when relocating to a system\n"
                    "                               running an earlier release of CP.\n"
                    "                DOMAIN - Indicates that relocation is to be attempted\n"
                    "                         even though the virtual machine would be moved\n"
                    "                         outside of its domain.\n"
                    "                STORAGE - Indicates that relocation should proceed even\n"
                    "                          if CP determines that there are insufficient\n"
                    "                          storage resources available on the destination,\n"
                    "                          following memory capacity assessment checks.\n"
                    "                  For example, to choose all three options,specify\n"
                    "                  'force=ARCHITECTURE DOMAIN STORAGE'.\n\n"
                    "              immediate:  One of the following:\n"
                    "                NO -  Specifies immediate processing. This is the default.\n"
                    "                YES - The VMRELOCATE command will do one early pass through\n"
                    "                      virtual machine storage and then go directly to the\n"
                    "                      quiesce stage. The defaults for both max_total and\n"
                    "                      max_quiesce are NOLIMIT when immediate=YES is specified\n\n"
                    "              max_total:  One of the following:\n"
                    "                NOLIMIT - Specifies that there is no limit on the total amount\n"
                    "                          of time the system should allow for this relocation.\n"
                    "                          The relocation will therefore not be canceled due to\n"
                    "                          time constraints. This is the default.\n"
                    "                value - The maximum total time (in seconds) that the command\n"
                    "                        issuer is willing to wait for the entire relocation\n\n"
                    "              max_quiesce: One of the following:\n"
                    "                NOLIMIT - Specifies that there is no limit on the total\n"
                    "                          quiesce time the system should allow for this\n"
                    "                          relocation.\n"
                    "                value - The maximum quiesce time(in seconds)a virtual machine\n"
                    "                        may be stopped during a relocation attempt. The range\n"
                    "                        for this  value is 1-99999999. The default is NOLIMIT\n"
                    "                        if immediate=YES is specified, or 10 seconds if not.\n\n");
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

    if ( !targetIdentifier || (!destSpecified && !cancelSpecified) )  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    for (i = 0; i < entryCount; i++) {
    	if ((strncmp(entryArray[i], "A", 1) == 0) || (strncmp(entryArray[i], "a", 1) == 0))  {
            // If they want special output header as first output, then we need to pass this
            // string on RC call so it is handled correctly for both cases.
            snprintf(strMsg, sizeof(strMsg), "Running VMRELOCATE %s against %s... ", entryArray[i], targetIdentifier);
            break;
    	}
    }
    rc = smVMRELOCATE(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRELOCATE", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("VMRELOCATE", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData,
                vmapiContextP, strMsg);
    }
    return rc;
}

int vmRelocateImageAttributes(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRELOCATE_Image_Attributes";
    int rc;
    int i;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[3];
    vmApiVMRelocateImageAttributesOutput * output;

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
                if (entryCount < 3) {
                    entryArray[entryCount] = optarg;
                    entryCount++;
                } else {
                    printf(" Error Too many -k values entered.\n");
                    return INVALID_DATA;
                }
                break;

            case 'h':
                printf("NAME\n"
                    "  VMRELOCATE_Image_Attributes\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRELOCATE_Image_Attributes [-T] targetIdentifier\n"
                    "  [-k] 'entry1' [-k] 'entry2' ...\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRELOCATE_Image_Attributes to modify the relocation setting for a\n"
                    "  the specified virtual machine, while it continues to run,\n"
                    "  to the specified system  within the z/VM SSI cluster.\n\n"
                    "  The following options are required:\n"
                    "    -T    The user ID whose relocation capability is being set. If * is\n"
                    "          specified, the target user is the command issuer.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. They must be inside\n"
                    "          single quotes. For example -k 'key=value'\n. Possible keywords are:\n"
                    "              relocation_setting - One of the following:\n"
                    "                  ON - Enables relocation for the specified user.\n"
                    "                  OFF - Disables relocation for the specified user.\n"
                    "              domain_name - The domain currently associated with a user.\n"
                    "                            If unspecified, the currently associated domain\n"
                    "                            is assumed\n"
                    "              archforce -  One of the following:\n"
                    "                  NO - The guest's virtual machine will not be set to a new\n"
                    "                       domain.\n"
                    "                 YES - Specifies the FORCE ARCHITECTURE option, in which the\n"
                    "                       virtual machine is assigned to the new domain even if\n"
                    "                       it means the guest's virtual architecture will be set to\n"
                    "                       a level with less capability than it had in its original\n"
                    "                       domain. If unspecified, the default is NO.\n\n");
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

    if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Modifying the relocation setting for %s... ", targetIdentifier);

    rc = smVMRELOCATE_Image_Attributes(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRELOCATE_Image_Attributes", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("VMRELOCATE_Image_Attributes", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    return rc;
}

int vmRelocateModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRELOCATE_Modify";
    int rc;
    int i;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[2];
    vmApiVMRelocateModifyOutput * output;

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
                if (entryCount < 2) {
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
                    "  VMRELOCATE_Modify\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRELOCATE_Modify [-T] targetIdentifier\n"
                    "  [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRELOCATE_Modify to modify the time limits associated with a relocation\n"
                    "  already in progress for the specified image\n"
                    "  The following options are required:\n"
                    "    -T    The name of the virtual machine whose relocation to another system\n"
                    "          within the z/VM SSI cluster is already in the process of relocation\n"
                    "          for which the time limits should be modified.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "          They may be specified in any order. Possible keywords:\n"
                    "            max_total: One of the following:\n"
                    "              NOLIMIT - Indicates that there is no limit on the total amount\n"
                    "                        of time the system should allow for this relocation.\n"
                    "                        The relocation will therefore not be canceled due to\n"
                    "                        time constraints. This is the default if unspecified.\n"
                    "              value - The maximum total time (in seconds) that the command\n"
                    "                      issuer is willing to wait for the entire relocation\n"
                    "                      to complete.\n"
                    "            max_quiesce: One of the following:\n"
                    "              NOLIMIT - Indicates that there is no limit on the total\n"
                    "                        quiesce time the system should allow for this\n"
                    "                        relocation.\n"
                    "              value - The maximum quiesce time in seconds a virtual machine\n"
                    "                      may be stopped during a relocation attempt.The default\n"
                    "                      if unspecified is 10 seconds.The range for this value\n"
                    "                      is 1-99999999.\n\n");
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

    if (!targetIdentifier)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Modifying the time limits associated with a relocation for %s... ", targetIdentifier);

    rc = smVMRELOCATE_Modify(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRELOCATE_Modify", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code and Error Buffer if it was sent
        rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("VMRELOCATE_Modify", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData,
                vmapiContextP, strMsg);
    }
    return rc;
}

int vmRelocateStatus(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRELOCATE_Status";
    int rc;
    int i;
    int entryCount = 0;
    int option;
    char * targetIdentifier = NULL;
    char * entryArray[1];
    char *token;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    char * blank = " ";
    char vmRelocate_image[8 + 1];
    char vmRelocate_source_system[8 + 1];
    char vmRelocate_destination_system[8 + 1];
    char vmRelocate_by[8 + 1];
    char vmRelocate_elapsed[8 + 1];
    char vmRelocate_status[15 + 1];
    vmApiVMRelocateStatusOutput * output;

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
                    "  VMRELOCATE_Status\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRELOCATE_Status [-T] targetIdentifier\n"
                    "  [-k] entry1 [-k] entry2 ...\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRELOCATE_Status to obtain information about relocations currently in\n"
                    "  progress.\n\n"
                    "  The following options are required:\n"
                    "    -T    The name of a virtual machine whose relocation to another system\n"
                    "          within the z/VM SSI cluster that we want the status of.\n"
                    "    -k    A keyword=value item to be created in the directory.\n"
                    "           They may be specified in any order. Possible keywords are:\n"
                    "              status_target - One of the following:\n"
                    "                  ALL - Specifies that the status of all relocations currently\n"
                    "                        in progress on this system are displayed.\n"
                    "                  USER userid - Display relocation status of the virtual\n"
                    "                                machine with name userid.\n"
                    "                  INCOMING - Display status of all incoming relocations.\n"
                    "                  OUTGOING - Display status of all outgoing relocations.\n"
                    "              If unspecified, ALL is the default.\n\n");
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

    if (!targetIdentifier)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("\nERROR: Missing required options\n");
        return 1;
    }

    rc = smVMRELOCATE_Status(vmapiContextP, "", 0, "",  targetIdentifier, entryCount, entryArray, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRELOCATE_Status", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("VMRELOCATE_Status", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        // Obtain the 6 members of the VMRELOCATE_status_structure
        for (i = 0; i < output->statusArrayCount; i++) {
            // Obtain VMRELOCATE_image
            token = strtok_r(output->statusArray[i].vmapiString, blank, &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_image, token);
            } else  {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: VMRELOCATE_image is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Obtain VMRELOCATE_source_system
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_source_system, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: VMRELOCATE_source_system is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Obtain VMRELOCATE_destination_system
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_destination_system, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: VMRELOCATE_destination_system is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Obtain VMRELOCATE_by
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_by, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: VMRELOCATE_by is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Obtain VMRELOCATE_elapsed
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_elapsed, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: VMRELOCATE_elapsed is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }
            // Obtain VMRELOCATE_status
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(vmRelocate_status, token);
            } else {
                strcpy(vmRelocate_status, "");  // vmRelocate_status can be null so set it to empty string
            }
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE image: %s\n", vmRelocate_image);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE source system: %s\n", vmRelocate_source_system);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE destination system: %s\n", vmRelocate_destination_system);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE by: %s\n", vmRelocate_by);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE elapsed: %s\n", vmRelocate_elapsed);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
            // Add extra newline after status for spacing.
            snprintf(strMsg, sizeof(strMsg),"VMRELOCATE status: %s\n\n", vmRelocate_status);
            if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                goto end;
            }
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
