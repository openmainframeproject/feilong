/**
    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
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
#include "smcliSSI.h"
#include "wrapperutils.h"

int ssiQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "SSI_Query";
    int rc;
    int option;
    int i = 0;
    char *token;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    char * blank = " ";
    char member_slot[1 + 1];
    char member_system_id[8 + 1];
    char member_state[9 + 1];
    char member_pdr_heartbeat[19 + 1];
    char member_received_heartbeat[19 + 1];
    vmApiSSIQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "";
    char tempStr[1];
    char strMsg[250];

    // These variables hold output messages until the end
    smMessageCollector saveMsgs;
    char msgBuff[MESSAGE_BUFFER_SIZE];
    INIT_MESSAGE_BUFFER(&saveMsgs, MESSAGE_BUFFER_SIZE, msgBuff) ;

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "h?")) != -1)
        switch (option) {
            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  SSI_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli SSI_Query\n\n"
                    "DESCRIPTION\n"
                    "  Use SSI_Query to obtain the SSI and system status.\n\n");
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

    rc = smSSI_Query(vmapiContextP, &output);


    if (rc) {
        printAndLogProcessingErrors("SSI_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
    	rc = printAndLogSmapiReturnCodeReasonCodeDescription("SSI_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        snprintf(strMsg, sizeof(strMsg), "ssi_name = %s\n", output->ssi_name);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }
        snprintf(strMsg, sizeof(strMsg), "ssi_mode = %s\n", output->ssi_mode);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }
        snprintf(strMsg, sizeof(strMsg), "ssi_pdr = %s\n", output->ssi_pdr);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }
        snprintf(strMsg, sizeof(strMsg), "cross_system_timeouts = %s\n", output->cross_system_timeouts);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }
        snprintf(strMsg, sizeof(strMsg), "output.ssiInfoCount = %d\n\2n", output->ssiInfoCount);
        if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
            goto end;
        }

        // Obtain the 5 members of the ssi_info_structure that are in the output->ssiInfo[i].vmapiString
        for (i = 0; i < output->ssiInfoCount; i++) {
            // Obtain member_slot
            token = strtok_r(output->ssiInfo[i].vmapiString, blank, &buffer);
            if (token != NULL) {
                strcpy(member_slot, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: member_slot is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Obtain member_system_id
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(member_system_id, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: member_system_id is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Obtain member_state
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(member_state, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: member_state is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            //  Check member_state to see if it equals Available
            if (strcasecmp(member_state, "Available") == 0) {
                //  We are done there is no SSI data for this member_slot. This is not a error it just means
                //  this member_slot has no zVM in it. Continue to get the next member_slot if there is one.
                continue;
            } else if (strcasecmp(member_state, "Down") == 0) {
                //  There is no SSI data for this member_slot because this zVM is down
                snprintf(strMsg, sizeof(strMsg),
                         "member_slot = %s\n"
                         "member_system_id = %s\n"
                         "member_state = %s\n"
                         "member_pdr_heartbeat = N/A\n"
                         "member_received_heartbeat = N/A\n\n",
                         member_slot, member_system_id, member_state);
                if (0 != (rc = addMessageToBuffer(&saveMsgs, strMsg))) {
                    goto end;
                }
            }

            // Obtain member_pdr_heartbeat
            token = strtok_r(NULL, blank, &buffer);
            if (token != NULL) {
                strcpy(member_pdr_heartbeat, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: member_pdr_heartbeat is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            // Obtain member_received_heartbeat
            token = strtok_r(NULL, "\0", &buffer);
            if (token != NULL) {
                strcpy(member_received_heartbeat, token);
            } else {
                if (0 == (rc = addMessageToBuffer(&saveMsgs, "ERROR: member_received_heartbeat is NULL\n"))) {
                    rc = OUTPUT_ERRORS_FOUND;
                }
                goto end;
            }

            snprintf(strMsg, sizeof(strMsg),
                     "member_slot = %s\n"
                     "member_system_id = %s\n"
                     "member_state = %s\n"
                     "member_pdr_heartbeat = %s\n"
                     "member_received_heartbeat = %s\n\n",
                     member_slot, member_system_id, member_state, member_pdr_heartbeat, member_received_heartbeat);
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
