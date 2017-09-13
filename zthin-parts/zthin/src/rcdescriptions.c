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
#include <stdlib.h>
#include <string.h>
#include "wrapperutils.h"
#include "smPublic.h"

/* Internal routine to fill SMAPI syntax error details*/
void fillSMAPIsyntaxReason(int rs, char * outreasonMsg);

/**
 * print SMAPI returnCode reasonCode Description and log the SMAPI error
 *
 * Use error codes from 5000 to 5999 for these errors.
 * wrapperults.c will use values from 6000 to 6100.
 * Use SMC for zthin smcli errors as the module abbreviation.
 * example: ULGSMC5000E
 */
void printSmapiDescriptionAndLogError(const char * APIname, int rc, int rs, struct _vmApiInternalContext* vmapiContextP,
                                      int newHeader) {
    char errMsg[512];
    char errMsgPlusNum[540];
    char line[1024];
    char msgNum[20];
    char * severity;
    char syntaxErrorMessage[150];
    bool logMSG = true;
    // If the trace file has not been read yet, do it.
    if (!(vmapiContextP->smTraceDetails->traceFileRead)) {
        readTraceFile(vmapiContextP);
    }
    if (rc == 0) {
        severity = "I";
    } else if (rc == 4) {
        severity = "W";
    } else {
        severity = "E";
    }
    // Handle return code (rc) and reason code (rs) as defined
    if (rc == 0 && rs == 0) {
        sprintf(errMsg, "Request successful\n");
        logMSG = false;
    } else if (rc == 0 && rs == 4 && strcmp(APIname, "Image_CPU_Define") == 0) {
        sprintf(errMsg, "CPU defined, but CPU affinity suppressed\n");
    } else if (rc == 0 && rs == 4) {
        sprintf(errMsg, "Segment was created or replaced, but specified userid in memory_access_identifier could not be found to give RSTD access\n");
    } else if (rc == 0 && rs == 8) {
        sprintf(errMsg, "Request successful; object directory offline\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(APIname, "Name_List_Add") == 0) {
        sprintf(errMsg, "Request successful; new list created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(APIname, "Image_Status_Query") == 0) {
        sprintf(errMsg, "Image not active\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(APIname, "Image_Pause") == 0) {
        sprintf(errMsg, "Image not active\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12) {
        sprintf(errMsg, "Request successful; NAMESAVE statement already exists in directory\n");
        logMSG = false;
    } else if (rc == 0 && rs == 16) {
        sprintf(errMsg, "Request successful; no more entries, list destroyed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 20 && strcmp(APIname, "Virtual_Network_LAN_Create") == 0) {
        sprintf(errMsg, "Request successful; new virtual network LAN created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 20) {
        sprintf(errMsg, "No output; user(s) not authorized for specified segment\n");
    } else if (rc == 0 && rs == 24) {
        sprintf(errMsg, "Request successful; virtual network LAN removed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(APIname, "Image_SCSI_Characteristics_Query_DM") == 0) {
        sprintf(errMsg, "There are no SCSI characteristics for this image\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(APIname, "Shared_Memory_Query") == 0) {
        sprintf(errMsg, "Query request successful, but segment not found\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(APIname, "Asynchronous_Notification_Query_DM") == 0) {
        sprintf(errMsg, "No matching entries found\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28) {
        sprintf(errMsg, "No matching entries found. Return buffer is empty\n");
        logMSG = false;
    } else if (rc == 0 && rs == 32) {
        sprintf(errMsg, "Name is not in list\n");
        logMSG = false;
    } else if (rc == 0 && rs == 36) {
        sprintf(errMsg, "Name is already in list\n");
        logMSG = false;
    } else if (rc == 0 && rs == 40) {
        sprintf(errMsg, "Request successful; new virtual switch created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 44) {
        sprintf(errMsg, "Request successful; virtual switch removed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 66) {
        sprintf(errMsg, "Multiple DEFINE or MODIFY statements are erased in system config\n");
        logMSG = false;
    } else if (rc == 0 && rs == 100) {
        sprintf(errMsg, "Asynchronous operation succeeded\n");
        logMSG = false;
    } else if (rc == 0 && rs == 104) {
        sprintf(errMsg, "Asynchronous operation in progress\n");
        logMSG = false;
    } else if (rc == 0 && rs == 108) {
        sprintf(errMsg, "Asynchronous operation failed\n");
    /* use the same message number for all the functional level output */
    } else if (rc == 0 && rs == 540) {
        sprintf(errMsg, "The API functional level is z/VM V5.4\n");
        logMSG = false;
    } else if (rc == 0 && rs == 610) {
        sprintf(errMsg, "The API functional level is z/VM V6.1\n");
        logMSG = false;
    } else if (rc == 0 && rs == 611) {
        sprintf(errMsg, "The API functional level is the updated z/VM V6.1 SPE release\n");
        logMSG = false;
    } else if (rc == 0 && rs == 620) {
        sprintf(errMsg, "The API functional level is z/VM V6.2\n");
        logMSG = false;
    } else if (rc == 0 && rs == 630) {
        sprintf(errMsg, "The API functional level is z/VM V6.3\n");
        logMSG = false;
    } else if (rc == 0 && rs == 640) {
        sprintf(errMsg, "The API functional level is z/VM V6.4\n");
        logMSG = false;
    } else if (rc == 4 && rs == 4) {
        sprintf(errMsg, "Request does not exist\n");
    } else if (rc == 4 && rs == 5) {
        sprintf(errMsg, "Unrestricted LAN\n");
    } else if (rc == 4 && rs == 6) {
        sprintf(errMsg, "No authorized users\n");
    } else if (rc == 4 && rs == 8) {
        sprintf(errMsg, "Device does not exist\n");
    } else if (rc == 4 && rs == 28) {
        sprintf(errMsg, "Return buffer is empty\n");
    } else if (rc == 4 && rs == 3000) {
        sprintf(errMsg, "VMRELOCATE TEST error\n");
    } else if (rc == 4 && rs == 3001) {
        sprintf(errMsg, "No active relocations found\n");
    } else if (rc == 4 && rs == 3008) {
        sprintf(errMsg, "System is not a member of an SSI cluster\n");
    } else if (rc == 8 && rs == 2) {
        sprintf(errMsg, "Invalid access user\n");
    } else if (rc == 8 && rs == 3) {
        sprintf(errMsg, "Invalid op value\n");
    } else if (rc == 8 && rs == 4 && strcmp(APIname, "Virtual_Network_LAN_Access") == 0) {
        sprintf(errMsg, "Invalid promiscuity value\n");
    } else if (rc == 8 && rs == 4 && strcmp(APIname, "Image_Definition_Delete_DM") == 0) {
        sprintf(errMsg, "Directory entry to be deleted not found\n");
    } else if (rc == 8 && rs == 4 && strcmp(APIname, "System_Performance_Threshold_Enable") == 0) {
        sprintf(errMsg, "Performance monitoring virtual server not found\n");
    } else if (rc == 8 && rs == 8 && strcmp(APIname, "Virtual_Network_Vswitch_Query_Stats") == 0) {
        sprintf(errMsg, "This funcion is not available on this system\n");
    } else if (rc == 8 && rs == 8) {
        sprintf(errMsg, "Device does not exist\n");
    } else if (rc == 8 && rs == 10) {
        sprintf(errMsg, "Device not available for attachment\n");
    } else if (rc == 8 && rs == 12 && strcmp(APIname, "Image_MDISK_Link_Query") == 0) {
        sprintf(errMsg, "target_identifier not logged on\n");
    } else if (rc == 8 && rs == 12 && strcmp(APIname, "Page_or_Spool_Volume_Add") == 0) {
        sprintf(errMsg, "Device not a volume\n");
    } else if (rc == 8 && rs == 12 && strcmp(APIname, "VMRELOCATE_Image_Attributes") == 0) {
        sprintf(errMsg, "target_identifier not logged on\n");
    } else if (rc == 8 && rs == 12 && strcmp(APIname, "Network_IP_Interface_Remove") == 0) {
        sprintf(errMsg, "An error was encountered on IFCONFIG command\n");
    } else if (rc == 8 && rs == 13) {
        sprintf(errMsg, "Match key length does not match the match key specified\n");
    } else if (rc == 8 && rs == 14) {
        sprintf(errMsg, "Free modes not available\n");
    } else if (rc == 8 && rs == 18) {
        sprintf(errMsg, "Volume does not exist\n");
    } else if (rc == 8 && rs == 19) {
        sprintf(errMsg, "Volume is CP owned and cannot be used\n");
    } else if (rc == 8 && rs == 20 && strcmp(APIname, "Image_Volume_Share") == 0) {
        sprintf(errMsg, "Volume is CP system and cannot be used\n");
    } else if (rc == 8 && rs == 20) {
        sprintf(errMsg, "Volume label already CP_OWNED on this system or in this system's configuration\n");
    } else if (rc == 8 && rs == 24 && strcmp(APIname, "Image_Definition_Async_Updates") == 0) {
        sprintf(errMsg, "Unable to write ASYNCH file\n");
    } else if (rc == 8 && rs == 24) {
        sprintf(errMsg, "Error linking parm disk\n");
    } else if (rc == 8 && rs == 28) {
        sprintf(errMsg, "Parm disk not RW\n");
    } else if (rc == 8 && rs == 32) {
        sprintf(errMsg, "System configuration not found on parm disk\n");
    } else if (rc == 8 && rs == 34) {
        sprintf(errMsg, "System configuration has bad data\n");
    } else if (rc == 8 && rs == 38) {
        sprintf(errMsg, "CP disk modes not available\n");
    } else if (rc == 8 && rs == 40) {
        sprintf(errMsg, "Parm disk is full\n");
    } else if (rc == 8 && rs == 42) {
        sprintf(errMsg, "Parm disk access not allowed\n");
    } else if (rc == 8 && rs == 44) {
        sprintf(errMsg, "No link password for parm disk was provided\n");
    } else if (rc == 8 && rs == 45) {
        sprintf(errMsg, "Userid not logged on\n");
    } else if (rc == 8 && rs == 46) {
        sprintf(errMsg, "Parm disk password is incorrect\n");
    } else if (rc == 8 && rs == 48) {
        sprintf(errMsg, "Parm disk is not in server's user directory\n");
    } else if (rc == 8 && rs == 50) {
        sprintf(errMsg, "Error with CPRELEASE of parm disk\n");
    } else if (rc == 8 && rs == 52) {
        sprintf(errMsg, "Error in access of CPACCESS parm disk\n");
    } else if (rc == 8 && rs == 241) {
        sprintf(errMsg, "Internal communication error\n");
    } else if (rc == 8 && rs == 1821) {
        sprintf(errMsg, "Relocation domain domain_name does not exist\n");
    } else if (rc == 8 && rs == 1822) {
        sprintf(errMsg, "User target_identifier cannot be set to a new relocation domain domain_name without the FORCE\n");
    } else if (rc == 8 && rs == 1823) {
        sprintf(errMsg, "A multiconfiguration virtual machine cannot be relocated\n");
    } else if (rc == 8 && rs == 2783) {
        sprintf(errMsg, "Invalid LAN ID\n");
    } else if (rc == 8 && rs == 2795) {
        sprintf(errMsg, "Invalid LAN parameter\n");
    } else if (rc == 8 && rs == 3000) {
        sprintf(errMsg, "VMRELOCATE MOVE error\n");
    } else if (rc == 8 && rs == 3002) {
        sprintf(errMsg, "Invalid parameter name\n");
    } else if (rc == 8 && rs == 3003) {
        sprintf(errMsg, "Invalid parameter operand\n");
    } else if (rc == 8 && rs == 3004) {
        sprintf(errMsg, "Required Parameter is missing\n");
    } else if (rc == 8 && rs == 3006) {
        sprintf(errMsg, "SSI is not in a STABLE state\n");
    } else if (rc == 8 && rs == 3007) {
        sprintf(errMsg, "The volume ID or slot is not available on all systems in the SSI\n");
    } else if (rc == 8 && rs == 3008) {
        sprintf(errMsg, "System is not a member of an SSI cluster\n");
    } else if (rc == 8 && rs == 3010) {
        sprintf(errMsg, "VMRELOCATE modify error\n");
    } else if (rc == 8 && rs == 3011) {
        sprintf(errMsg, "No unique CP_OWNED slot available on system and in System Config\n");
    } else if (rc == 8 && rs == 3012) {
        sprintf(errMsg, "Volume does not exist\n");
    } else if (rc == 8 && rs == 3013) {
        sprintf(errMsg, "Volume is offline\n");
    } else if (rc == 8 && rs == 3014) {
        sprintf(errMsg, "Volume does not support sharing\n");
    } else if (rc == 8 && rs == 3015) {
        sprintf(errMsg, "File could not be saved\n");
    } else if (rc == 8 && rs == 3016) {
        sprintf(errMsg, "SMAPIOUT segment empty\n");
    } else if (rc == 8 && rs == 3017) {
        sprintf(errMsg, "SMAPIOUT segment does not contain valid data\n");
    } else if (rc == 8 && rs == 3018) {
        sprintf(errMsg, "SMAPIOUT segment not found\n");
    } else if (rc == 8 && rs == 3019) {
        sprintf(errMsg, "SMAPIOUT CPU data not found\n");
    } else if (rc == 8 && rs == 3020) {
        sprintf(errMsg, "Specified TCP/IP stack is not available\n");
    } else if (rc == 8 && rs == 3021) {
        sprintf(errMsg, "SMAPI worker server not in the obey list of specified TCP/IP stack\n");
    } else if (rc == 8) {
        sprintf(errMsg, "Check the SMAPI manual for this reason code %d. It may represent a HCP/DMS %d message number\n", rs, rs);
    } else if (rc == 24) {
        fillSMAPIsyntaxReason(rs, syntaxErrorMessage);
        sprintf(errMsg, "Syntax error in function parameter %d; %s\n", (rs/100), syntaxErrorMessage);
    } else if (rc == 28 && rs == 0) {
        sprintf(errMsg, "Namelist file not found\n");
    } else if (rc == 36 && rs == 0) {
        sprintf(errMsg, "Request is authorized\n");
    } else if (rc == 36 && rs == 4) {
        sprintf(errMsg, "Authorization deferred to directory manager\n");
    } else if (rc == 100 && rs == 0) {
        sprintf(errMsg, "Request not authorized by external security manager\n");
    } else if (rc == 100 && rs == 4) {
        sprintf(errMsg, "Authorization deferred to directory manager\n");
    } else if (rc == 100 && rs == 8) {
        sprintf(errMsg, "Request not authorized by external security manager\n");
    } else if (rc == 100 && rs == 12) {
        sprintf(errMsg, "Request not authorized by directory manager\n");
    } else if (rc == 100 && rs == 16) {
        sprintf(errMsg, "Request not authorized by server\n");
    } else if (rc == 104 && rs == 0) {
        sprintf(errMsg, "Authorization file not found\n");
    } else if (rc == 106 && rs == 0) {
        sprintf(errMsg, "Authorization file cannot be updated\n");
    } else if (rc == 108 && rs == 0) {
        sprintf(errMsg, "Authorization file entry already exists\n");
    } else if (rc == 112 && rs == 0) {
        sprintf(errMsg, "Authorization file entry does not exist\n");
    } else if (rc == 120 && rs == 0) {
        sprintf(errMsg, "Authentication error; userid or password not valid\n");
    } else if (rc == 128 && rs == 0) {
        sprintf(errMsg, "Authentication error; password expired\n");
    } else if (rc == 188) {
        sprintf(errMsg, "Internal server error; ESM failure. - product-specific return code : %d\n", rs);
    } else if (rc == 192) {
        sprintf(errMsg, "Internal server error; cannot authenticate user/password. - product-specific return code : %d\n", rs);
    } else if (rc == 200 && rs == 0) {
        sprintf(errMsg, "Image operation error\n");
    } else if (rc == 200 && rs == 4) {
        sprintf(errMsg, "Image not found\n");
    } else if (rc == 200 && rs == 8) {
        sprintf(errMsg, "Image already active\n");
    } else if (rc == 200 && rs == 12) {
        sprintf(errMsg, "Image not active\n");
    } else if (rc == 200 && rs == 16) {
        sprintf(errMsg, "Image being deactivated\n");
    } else if (rc == 200 && rs == 24) {
        sprintf(errMsg, "List not found\n");
    } else if (rc == 200 && rs == 28) {
        sprintf(errMsg, "Some images in list not activated\n");
    } else if (rc == 200 && rs == 32) {
        sprintf(errMsg, "Some images in list not deactivated\n");
    } else if (rc == 200 && rs == 36 && strcmp(APIname, "Image_Recycle") == 0) {
        sprintf(errMsg, "Some images in list not recycled\n");
    } else if (rc == 200 && rs == 36 && strcmp(APIname, "Image_Deactivate") == 0) {
        sprintf(errMsg, "Specified time results in interval greater than max allowed\n");
    } else if (rc == 204 && rs == 0) {
        sprintf(errMsg, "Image device usage error\n");
    } else if (rc == 204 && rs == 2) {
        sprintf(errMsg, "Input image device number not valid\n");
    } else if (rc == 204 && rs == 4) {
        sprintf(errMsg, "Image device already exists\n");
    } else if (rc == 204 && rs == 8) {
        sprintf(errMsg, "Image device does not exist\n");
    } else if (rc == 204 && rs == 12) {
        sprintf(errMsg, "Image device is busy\n");
    } else if (rc == 204 && rs == 16) {
        sprintf(errMsg, "Image device is not available\n");
    } else if (rc == 204 && rs == 20) {
        sprintf(errMsg, "Image device already connected\n");
    } else if (rc == 204 && rs == 24) {
        sprintf(errMsg, "Image device is not a tape drive, or cannot be assigned/reset\n");
    } else if (rc == 204 && rs == 28 && strcmp(APIname, "Image_Device_Reset") == 0) {
        sprintf(errMsg, "Image device is not a shared DASD\n");
    } else if (rc == 204 && rs == 28) {
        sprintf(errMsg, "Image device already defined as type other than network adapter\n");
    } else if (rc == 204 && rs == 32) {
        sprintf(errMsg, "Image device is not a reserved DASD\n");
    } else if (rc == 204 && rs == 36) {
        sprintf(errMsg, "I/O error on image device\n");
    } else if (rc == 204 && rs == 40) {
        sprintf(errMsg, "Virtual Network Adapter not deleted\n");
    } else if (rc == 204 && rs == 44) {
        sprintf(errMsg, "DASD volume cannot be deleted\n");
    } else if (rc == 204 && rs == 48) {
        sprintf(errMsg, "Virtual network adapter is already disconnected\n");
    } else if (rc == 208 && rs == 0) {
        sprintf(errMsg, "Image disk usage error\n");
    } else if (rc == 208 && rs == 4) {
        sprintf(errMsg, "Image disk already in use\n");
    } else if (rc == 208 && rs == 8) {
        sprintf(errMsg, "Image disk not in use\n");
    } else if (rc == 208 && rs == 12) {
        sprintf(errMsg, "Image disk not available\n");
    } else if (rc == 208 && rs == 16) {
        sprintf(errMsg, "Image disk cannot be shared as requested\n");
    } else if (rc == 208 && rs == 20) {
        sprintf(errMsg, "Image disk shared in different mode\n");
    } else if (rc == 208 && rs == 28) {
        sprintf(errMsg, "Image disk does not have required password\n");
    } else if (rc == 208 && rs == 32) {
        sprintf(errMsg, "Incorrect password specified for image disk\n");
    } else if (rc == 208 && rs == 36) {
        sprintf(errMsg, "Image disk does not exist\n");
    } else if (rc == 208 && rs == 1157) {
        sprintf(errMsg, "MDISK DEVNO parameter requires the device to be a free volume\n");
    } else if (rc == 212 && rs == 0) {
        sprintf(errMsg, "Active image connectivity error\n");
    } else if (rc == 212 && rs == 4) {
        sprintf(errMsg, "Partner image not found\n");
    } else if (rc == 212 && rs == 8 && strcmp(APIname, "Virtual_Network_Adapter_Query") == 0) {
        sprintf(errMsg, "Adapter does not exist\n");
    } else if (rc == 212 && rs == 8 && strcmp(APIname, "Virtual_Network_Adapter_Query_Extended") == 0) {
        sprintf(errMsg, "Adapter does not exist\n");
    } else if (rc == 212 && rs == 8) {
        sprintf(errMsg, "Image not authorized to connect\n");
    } else if (rc == 212 && rs == 12) {
        sprintf(errMsg, "LAN does not exist\n");
    } else if (rc == 212 && rs == 16) {
        sprintf(errMsg, "LAN owner LAN name does not exist\n");
    } else if (rc == 212 && rs == 20) {
        sprintf(errMsg, "Requested LAN owner not active\n");
    } else if (rc == 212 && rs == 24) {
        sprintf(errMsg, "LAN name already exists with different attributes\n");
    } else if (rc == 212 && rs == 28) {
        sprintf(errMsg, "Image device not correct type for requested connection\n");
    } else if (rc == 212 && rs == 32) {
        sprintf(errMsg, "Image device not connected to LAN\n");
    } else if (rc == 212 && rs == 36) {
        sprintf(errMsg, "Virtual switch already exists\n");
    } else if (rc == 212 && rs == 40) {
        sprintf(errMsg, "Virtual switch does not exist\n");
    } else if (rc == 212 && rs == 44) {
        sprintf(errMsg, "Image already authorized\n");
    } else if (rc == 212 && rs == 48) {
        sprintf(errMsg, "VLAN does not exist\n");
    } else if (rc == 212 && rs == 52) {
        sprintf(errMsg, "Maximum number of connections reached\n");
    } else if (rc == 212 && rs == 96) {
        sprintf(errMsg, "Unknown reason\n");
    } else if (rc == 216 && rs == 2) {
        sprintf(errMsg, "Input virtual CPU value out of range\n");
    } else if (rc == 216 && rs == 4) {
        sprintf(errMsg, "Virtual CPU not found\n");
    } else if (rc == 216 && rs == 12) {
        sprintf(errMsg, "Image not active\n");
    } else if (rc == 216 && rs == 24) {
        sprintf(errMsg, "Virtual CPU already exists\n");
    } else if (rc == 216 && rs == 28) {
        sprintf(errMsg, "Virtual CPU address beyond allowable range defined in directory\n");
    } else if (rc == 216 && rs == 40) {
        sprintf(errMsg, "Processor type not supported on your system\n");
    } else if (rc == 300 && rs == 0) {
        sprintf(errMsg, "Image volume operation successful\n");
    } else if (rc == 300 && rs == 8) {
        sprintf(errMsg, "Device not found\n");
    } else if (rc == 300 && rs == 10) {
        sprintf(errMsg, "Device not available for attachment\n");
    } else if (rc == 300 && rs == 12) {
        sprintf(errMsg, "Device not a volume\n");
    } else if (rc == 300 && rs == 14) {
        sprintf(errMsg, "Free modes not available\n");
    } else if (rc == 300 && rs == 16) {
        sprintf(errMsg, "Device vary online failed\n");
    } else if (rc == 300 && rs == 18) {
        sprintf(errMsg, "Volume label not found in system configuration\n");
    } else if (rc == 300 && rs == 20) {
        sprintf(errMsg, "Volume label already in system configuration\n");
    } else if (rc == 300 && rs == 22) {
        sprintf(errMsg, "Parm disks 1 and 2 are same\n");
    } else if (rc == 300 && rs == 24) {
        sprintf(errMsg, "Error linking parm disk (1 or 2)\n");
    } else if (rc == 300 && rs == 28) {
        sprintf(errMsg, "Parm disk (1 or 2) not RW\n");
    } else if (rc == 300 && rs == 32) {
        sprintf(errMsg, "System configuration not found on parm disk 1\n");
    } else if (rc == 300 && rs == 34) {
        sprintf(errMsg, "System configuration has bad data\n");
    } else if (rc == 300 && rs == 36) {
        sprintf(errMsg, "Syntax errors updating system configuration file\n");
    } else if (rc == 300 && rs == 38) {
        sprintf(errMsg, "CP disk modes not available\n");
    } else if (rc == 300 && rs == 40) {
        sprintf(errMsg, "Parm disk (1 or 2) is full\n");
    } else if (rc == 300 && rs == 42) {
        sprintf(errMsg, "Parm disk (1 or 2) access not allowed\n");
    } else if (rc == 300 && rs == 44) {
        sprintf(errMsg, "Parm disk (1 or 2) PW not supplied\n");
    } else if (rc == 300 && rs == 46) {
        sprintf(errMsg, "Parm disk (1 or 2) PW is incorrect\n");
    } else if (rc == 300 && rs == 48) {
        sprintf(errMsg, "Parm disk (1 or 2) is not in server's user directory\n");
    } else if (rc == 300 && rs == 50) {
        sprintf(errMsg, "Error in release of CPRELEASE parm disk (1 or 2)\n");
    } else if (rc == 300 && rs == 52) {
        sprintf(errMsg, "Error in access of CPACCESS parm disk (1 or 2)\n");
    } else if (rc == 396 && rs == 0) {
        sprintf(errMsg, "Internal system error\n");
    } else if (rc == 396) {
        sprintf(errMsg, "Internal error found. - product-specific return code : %d\n", rs);
    } else if (rc == 400 && rs == 0) {
        sprintf(errMsg, "Image or profile definition error\n");
    } else if (rc == 400 && rs == 4) {
        sprintf(errMsg, "Image or profile definition not found\n");
    } else if (rc == 400 && rs == 8) {
        sprintf(errMsg, "Image or profile name already defined\n");
    } else if (rc == 400 && rs == 12) {
        sprintf(errMsg, "Image or profile definition is locked \n");
    } else if (rc == 400 && rs == 16) {
        sprintf(errMsg, "Image or profile definition cannot be deleted\n");
    } else if (rc == 400 && rs == 20) {
        sprintf(errMsg, "Image prototype is not defined\n");
    } else if (rc == 400 && rs == 24) {
        sprintf(errMsg, "Image or profile definition is not locked\n");
    } else if (rc == 400 && rs == 40) {
        sprintf(errMsg, "Multiple user statements\n");
    } else if (rc == 404 && rs == 0) {
        sprintf(errMsg, "Image device definition error\n");
    } else if (rc == 404 && rs == 4) {
        sprintf(errMsg, "Image device already defined\n");
    } else if (rc == 404 && rs == 8) {
        sprintf(errMsg, "Image device not defined\n");
    } else if (rc == 404 && rs == 12) {
        sprintf(errMsg, "Image device is locked\n");
    } else if (rc == 404 && rs == 24 &&
            ((strcmp(APIname, "Image_Disk_Copy_DM") == 0) || strcmp(APIname, "Image_Disk_Create_DM") == 0)) {
        sprintf(errMsg, "Image device type not same as source\n");
    } else if (rc == 404 && rs == 24) {
        sprintf(errMsg, "Image device is not locked\n");
    } else if (rc == 404 && rs == 28) {
        sprintf(errMsg, "Image device size not same as source\n");
    } else if (rc == 408 && rs == 0) {
        sprintf(errMsg, "Image disk definition error\n");
    } else if (rc == 408 && rs == 4) {
        sprintf(errMsg, "Image disk already defined\n");
    } else if (rc == 408 && rs == 8) {
        sprintf(errMsg, "Image disk not defined\n");
    } else if (rc == 408 && rs == 12) {
        sprintf(errMsg, "Image device is locked\n");
    } else if (rc == 408 && rs == 16) {
        sprintf(errMsg, "Image disk sharing not allowed by target image definition\n");
    } else if (rc == 408 && rs == 24) {
        sprintf(errMsg, "Requested image disk space not available\n");
    } else if (rc == 408 && rs == 28) {
        sprintf(errMsg, "Image disk does not have required password\n");
    } else if (rc == 408 && rs == 32) {
        sprintf(errMsg, "Incorrect password specified for image disk\n");
    } else if (rc == 412 && rs == 0) {
        sprintf(errMsg, "Image connectivity definition error\n");
    } else if (rc == 412 && rs == 4) {
        sprintf(errMsg, "Partner image not found\n");
    } else if (rc == 412 && rs == 16) {
        sprintf(errMsg, "Parameters do not match existing directory statement\n");
    } else if (rc == 412 && rs == 28) {
        sprintf(errMsg, "Image device not correct type for requested connection\n");
    } else if (rc == 416 && rs == 0) {
        sprintf(errMsg, "Prototype definition error\n");
    } else if (rc == 416 && rs == 4) {
        sprintf(errMsg, "Prototype definition not found\n");
    } else if (rc == 416 && rs == 8) {
        sprintf(errMsg, "Prototype already exists\n");
    } else if (rc == 420 && rs == 4) {
        sprintf(errMsg, "Group, region, or volume name is already defined\n");
    } else if (rc == 420 && rs == 8) {
        sprintf(errMsg, "That group, region, or volume name is not defined\n");
    } else if (rc == 420 && rs == 12) {
        sprintf(errMsg, "That region name is not included in the group\n");
    } else if (rc == 420 && rs == 36) {
        sprintf(errMsg, "The requested volume is offline or is not a DASD device\n");
    } else if (rc == 424 && rs == 4) {
        sprintf(errMsg, "Namesave statement already exists\n");
    } else if (rc == 424 && rs == 8) {
        sprintf(errMsg, "Segment name not found\n");
    } else if (rc == 428 && rs == 4) {
        sprintf(errMsg, "Duplicate subscription\n");
    } else if (rc == 428 && rs == 8) {
        sprintf(errMsg, "No matching entries\n");
    } else if (rc == 432 && rs == 4) {
        sprintf(errMsg, "Tag name is already defined\n");
    } else if (rc == 432 && rs == 8) {
        sprintf(errMsg, "Tag name is not defined\n");
    } else if (rc == 432 && rs == 8) {
        sprintf(errMsg, "Tag name is not defined\n");
    } else if (rc == 432 && rs == 12) {
        sprintf(errMsg, "Tag ordinal is already defined\n");
    } else if (rc == 432 && rs == 16 && strcmp(APIname, "Directory_Manager_Local_Tag_Set_DM") == 0) {
        sprintf(errMsg, "Tag too long\n");
    } else if (rc == 432 && rs == 16) {
        sprintf(errMsg, "Tag is in use in one or more directory entries, can not be revoked\n");
    } else if (rc == 432 && rs == 20) {
        sprintf(errMsg, "Use not allowed by exit routine\n");
    } else if (rc == 436 && rs == 4) {
        sprintf(errMsg, "Profile included not found\n");
    } else if (rc == 436 && rs == 40) {
        sprintf(errMsg, "Multiple profiles included\n");
    } else if (rc == 444 && rs == 0) {
        sprintf(errMsg, "Password policy error\n");
    } else if (rc == 444 && rs == 4) {
        sprintf(errMsg, "Password too long\n");
    } else if (rc == 444 && rs == 8) {
        sprintf(errMsg, "Password too short\n");
    } else if (rc == 444 && rs == 12) {
        sprintf(errMsg, "Password content does not match policy\n");
    } else if (rc == 448 && rs == 0) {
        sprintf(errMsg, "Account policy error\n");
    } else if (rc == 448 && rs == 4) {
        sprintf(errMsg, "Account number too long\n");
    } else if (rc == 448 && rs == 8) {
        sprintf(errMsg, "Account number too short\n");
    } else if (rc == 448 && rs == 12) {
        sprintf(errMsg, "Account number content does not match policy\n");
    } else if (rc == 452 && rs == 4) {
        sprintf(errMsg, "Task not found\n");
    } else if (rc == 456 && rs == 4) {
        sprintf(errMsg, "LOADDEV statement not found\n");
    } else if (rc == 460 && rs == 4) {
        sprintf(errMsg, "Image does not have an IPL statement\n");
    } else if (rc == 500 && rs == 0) {
        sprintf(errMsg, "Directory manager request could not be completed\n");
    } else if (rc == 500 && rs == 4) {
        sprintf(errMsg, "Directory manager is not accepting updates\n");
    } else if (rc == 500 && rs == 8) {
        sprintf(errMsg, "Directory manager is not available\n");
    } else if (rc == 500 && rs == 20) {
        sprintf(errMsg, "Password format not supported\n");
    } else if (rc == 504) {
        sprintf(errMsg, "Target ID not added - product-specific return code : %d\n", rs);
    } else if (rc == 520 && rs == 24) {
        sprintf(errMsg, "Only one base CPU may be defined\n");
    } else if (rc == 520 && rs == 28) {
        sprintf(errMsg, "Input virtual CPU value out of range\n");
    } else if (rc == 520 && rs == 30) {
        sprintf(errMsg, "CPU not found\n");
    } else if (rc == 520 && rs == 32) {
        sprintf(errMsg, "Maximum allowable number of virtual CPUs is exceeded\n");
    } else if (rc == 520 && rs == 45) {
        sprintf(errMsg, "The Cryptographic Coprocessor Facility (CCF) is not installed on this system\n");
    } else if (rc == 520 && rs == 2826) {
        sprintf(errMsg, "SCPDATA contains invalid UTF-8 data\n");
    } else if (rc == 592 && rs == 0) {
        sprintf(errMsg, "Asynchronous operation started\n");
    } else if (rc == 592) {
        sprintf(errMsg, "Asynchronous operation started - product-specific asynchronous operation ID : %d\n", rs);
    } else if (rc == 596) {
        sprintf(errMsg, "Internal directory manager error - product-specific return code : %d\n", rs);
    } else if (rc == 600 && rs == 8) {
        sprintf(errMsg, "Bad page range\n");
    } else if (rc == 600 && rs == 12) {
        sprintf(errMsg, "User not logged on\n");
    } else if (rc == 600 && rs == 16) {
        sprintf(errMsg, "Could not save segment\n");
    } else if (rc == 600 && rs == 20) {
        sprintf(errMsg, "Not authorized to issue internal system command or is not authorized for RSTD segment\n");
    } else if (rc == 600 && rs == 24) {
        sprintf(errMsg, "Conflicting parameters\n");
    } else if (rc == 600 && rs == 28) {
        sprintf(errMsg, "Segment not found or does not exist\n");
    } else if (rc == 600 && rs == 299) {
        sprintf(errMsg, "Class S (skeleton) segment file already exists\n");
    } else if (rc == 620 && rs == 14) {
        sprintf(errMsg, "Free modes not available\n");
    } else if (rc == 620 && rs == 22) {
        sprintf(errMsg, "System config parm disks 1 and 2 are same\n");
    } else if (rc == 620 && rs == 24) {
        sprintf(errMsg, "Error linking parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 28) {
        sprintf(errMsg, "Parm disk (1 or 2) not RW\n");
    } else if (rc == 620 && rs == 32) {
        sprintf(errMsg, "System config not found on parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 34) {
        sprintf(errMsg, "System config has bad data\n");
    } else if (rc == 620 && rs == 36) {
        sprintf(errMsg, "Syntax errors updating system config\n");
    } else if (rc == 620 && rs == 38) {
        sprintf(errMsg, "CP disk modes not available\n");
    } else if (rc == 620 && rs == 40) {
        sprintf(errMsg, "Parm disk (1 or 2) is full\n");
    } else if (rc == 620 && rs == 42) {
        sprintf(errMsg, "Parm disk (1 or 2) access not allowed\n");
    } else if (rc == 620 && rs == 44) {
        sprintf(errMsg, "Parm disk (1 or 2) PW not supplied\n");
    } else if (rc == 620 && rs == 46) {
        sprintf(errMsg, "Parm disk (1 or 2) PW is incorrect\n");
    } else if (rc == 620 && rs == 48) {
        sprintf(errMsg, "Parm disk (1 or 2) is not in server's directory\n");
    } else if (rc == 620 && rs == 50) {
        sprintf(errMsg, "Error in release of CPRELEASE parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 52) {
        sprintf(errMsg, "Error in access of CPACCESS parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 54) {
        sprintf(errMsg, "DEFINE VSWITCH statement already exists in system config\n");
    } else if (rc == 620 && rs == 58) {
        sprintf(errMsg, "MODIFY VSWITCH statement to userid not found in system config\n");
    } else if (rc == 620 && rs == 60) {
        sprintf(errMsg, "DEFINE VSWITCH statement does not exist in system config\n");
    } else if (rc == 620 && rs == 62) {
        sprintf(errMsg, "DEFINE operands conflict, cannot be updated in the system config\n");
    } else if (rc == 620 && rs == 64) {
        sprintf(errMsg, "Multiple DEFINE or MODIFY statements found in system config\n");
    } else if (rc == 800 && rs == 8) {
        sprintf(errMsg, "No measurement data exists\n");
    } else if (rc == 800 && rs == 12) {
        sprintf(errMsg, "Incorrect syntax in update data \n");
    } else if (rc == 800 && rs == 16) {
        sprintf(errMsg, "Not authorized to access file\n");
    } else if (rc == 800 && rs == 24) {
        sprintf(errMsg, "Error writing file(s) to directory\n");
    } else if (rc == 800 && rs == 28) {
        sprintf(errMsg, "Specified configuration file not found\n");
    } else if (rc == 800 && rs == 32) {
        sprintf(errMsg, "Internal error processing updates\n");
    } else if (rc == 900 && rs == 4) {
        sprintf(errMsg, "Custom exec not found\n");
    } else if (rc == 900 && rs == 8) {
        sprintf(errMsg, "Worker server was not found\n");
    } else if (rc == 900 && rs == 12) {
        sprintf(errMsg, "Specified function does not exist\n");
    } else if (rc == 900 && rs == 16) {
        sprintf(errMsg, "Internal server error - DMSSIPTS entry for function is invalid\n");
    } else if (rc == 900 && rs == 20) {
        sprintf(errMsg, "Total length does not match the specified input data\n");
    } else if (rc == 900 && rs == 24) {
        sprintf(errMsg, "Error accessing SFS directory\n");
    } else if (rc == 900 && rs == 28) {
        sprintf(errMsg, "Internal server error - error with format of function output\n");
    } else if (rc == 900 && rs == 32) {
        sprintf(errMsg, "Internal server error - response from worker server was not valid\n");
    } else if (rc == 900 && rs == 36) {
        sprintf(errMsg, "Specified length was not valid, out of valid server data range\n");
    } else if (rc == 900 && rs == 40) {
        sprintf(errMsg, "Internal server socket error\n");
    } else if (rc == 900 && rs == 68) {
        sprintf(errMsg, "Unable to access LOHCOST server\n");
    } else if (rc == 900 && rs == 99) {
        sprintf(errMsg, "A system change occurred during the API call - reissue the API call to obtain the data\n");
    } else {
        sprintf(errMsg, "Unknown. Consult the SMAPI manual return and reason code summary\n");
    }

    TRACE_START(vmapiContextP, TRACEAREA_SMCLI, TRACELEVEL_ERROR);
        sprintf(line, "SMAPi error found (from %s); RC = %d, RS = %d, Description: %s\n", APIname, rc, rs, errMsg);
    TRACE_END_DEBUG(vmapiContextP, line);

    sprintf(errMsgPlusNum, "ULGSMC5%03d%s %s  API issued : %s\n", rc, severity, errMsg, APIname);

    // If this call is only for the new header, just print that header out
    if (newHeader) {
        printf("8 %d %d (details) %s", rc, rs, errMsgPlusNum);
    } else {
        printf("  Description: %s", errMsgPlusNum);
    }
}

/* SMAPI syntax errors (rc=24) have part of the reason code used to describe the problem found.
   This routine will display the text from the manual so the caller does not need to go to the manual.
*/
void fillSMAPIsyntaxReason(int rs, char * outreasonMsg){

    int synReason = rs%100;

    switch (synReason) {
        case 01:
            sprintf(outreasonMsg, "First character of listname is a colon \":\"");
            break;
        case 10:
            sprintf(outreasonMsg, "Characters not \"0123456789\"");
            break;
        case 11:
            sprintf(outreasonMsg, "Unsupported function");
            break;
        case 13:
            sprintf(outreasonMsg, "Length is greater than maximum or exceeds total length");
            break;
        case 14:
            sprintf(outreasonMsg, "Length is less than minimum");
            break;
        case 15:
            sprintf(outreasonMsg, "Numeric value less than minimum or null value encountered");
            break;
        case 16:
            sprintf(outreasonMsg, "Characters not \"0123456789ABCDEF\"");
            break;
        case 17:
            sprintf(outreasonMsg, "Characters not \"0123456789ABCDEF-\"");
            break;
        case 18:
            sprintf(outreasonMsg, "Numeric value greater than maximum");
            break;
        case 19:
            sprintf(outreasonMsg, "Unrecognized value");
            break;
        case 23:
            sprintf(outreasonMsg, "Conflicting parameter specified");
            break;
        case 24:
            sprintf(outreasonMsg, "Unspecified required parameter");
            break;
        case 25:
            sprintf(outreasonMsg, "Extraneous parameter specified");
            break;
        case 26:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ\"");
            break;
        case 36:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\"");
            break;
        case 37:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-\"");
            break;
        case 42:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$+-:\"");
            break;
        case 43:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$+-:_\"");
            break;
        case 44:
            sprintf(outreasonMsg, "Characters not \"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$+-:_=\"");
            break;
        case 45:
            sprintf(outreasonMsg, "Invalid SFS syntax");
            break;
        case 88:
            sprintf(outreasonMsg, "Unexpected end of data");
            break;
        case 99:
            sprintf(outreasonMsg, "Non-breaking characters: non-blank, non-null, non-delete, non-line-end, non-carriage return, non-line-feed");
            break;
        default:
            sprintf(outreasonMsg, "Unexpected new SMAPI syntax error number %d.", synReason);
        }
}

