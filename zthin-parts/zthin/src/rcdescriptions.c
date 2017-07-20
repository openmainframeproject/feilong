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
 *
 * Use error codes from 5100 to 5999 for these errors
 * wrapperults.c will use values from 5000 to 5100.
 * Use SMC for zthin smcli errors as the module abbreviation.
 * example: ULGSMC5100E
 */
void printSmapiDescriptionAndLogError(const char * class, int rc, int rs, struct _vmApiInternalContext* vmapiContextP,
                                      int newHeader) {
    char errMsg[512];
    char line[1024];
    char syntaxErrorMessage[150];
    bool logMSG = true;
    // If the trace file has not been read yet, do it.
    if (!(vmapiContextP->smTraceDetails->traceFileRead)) {
        readTraceFile(vmapiContextP);
    }
    // Handle return code (rc) and reason code (rs) as defined
    if (rc == 0 && rs == 0) {
        sprintf(errMsg, "Request successful\n");
        logMSG = false;
    } else if (rc == 0 && rs == 4 && strcmp(class, "Image_CPU_Define") == 0) {
        sprintf(errMsg, "ULGSMC5100I CPU defined, but CPU affinity suppressed\n");
    } else if (rc == 0 && rs == 4) {
        sprintf(errMsg, "ULGSMC5101I Segment was created or replaced, but specified userid in memory_access_identifier could not be found to give RSTD access\n");
    } else if (rc == 0 && rs == 8) {
        sprintf(errMsg, "ULGSMC5102I Request successful; object directory offline\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(class, "Name_List_Add") == 0) {
        sprintf(errMsg, "ULGSMC5103I Request successful; new list created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(class, "Image_Status_Query") == 0) {
        sprintf(errMsg, "ULGSMC5104I Image not active\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12 && strcmp(class, "Image_Pause") == 0) {
        sprintf(errMsg, "ULGSMC5105I Image not active\n");
        logMSG = false;
    } else if (rc == 0 && rs == 12) {
        sprintf(errMsg, "ULGSMC5106I Request successful; NAMESAVE statement already exists in directory\n");
        logMSG = false;
    } else if (rc == 0 && rs == 16) {
        sprintf(errMsg, "ULGSMC5107I Request successful; no more entries, list destroyed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 20 && strcmp(class, "Virtual_Network_LAN_Create") == 0) {
        sprintf(errMsg, "ULGSMC5107I Request successful; new virtual network LAN created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 20) {
        sprintf(errMsg, "ULGSMC5109I No output; user(s) not authorized for specified segment\n");
    } else if (rc == 0 && rs == 24) {
        sprintf(errMsg, "ULGSMC5110I Request successful; virtual network LAN removed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(class, "Image_SCSI_Characteristics_Query_DM") == 0) {
        sprintf(errMsg, "ULGSMC5111I There are no SCSI characteristics for this image\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(class, "Shared_Memory_Query") == 0) {
        sprintf(errMsg, "ULGSMC5112I Query request successful, but segment not found\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28 && strcmp(class, "Asynchronous_Notification_Query_DM") == 0) {
        sprintf(errMsg, "ULGSMC5113I No matching entries found\n");
        logMSG = false;
    } else if (rc == 0 && rs == 28) {
        sprintf(errMsg, "ULGSMC5114I No matching entries found. Return buffer is empty\n");
        logMSG = false;
    } else if (rc == 0 && rs == 32) {
        sprintf(errMsg, "ULGSMC5115I Name is not in list\n");
        logMSG = false;
    } else if (rc == 0 && rs == 36) {
        sprintf(errMsg, "ULGSMC5116I Name is already in list\n");
        logMSG = false;
    } else if (rc == 0 && rs == 40) {
        sprintf(errMsg, "ULGSMC5117I Request successful; new virtual switch created\n");
        logMSG = false;
    } else if (rc == 0 && rs == 44) {
        sprintf(errMsg, "ULGSMC5118I Request successful; virtual switch removed\n");
        logMSG = false;
    } else if (rc == 0 && rs == 66) {
        sprintf(errMsg, "ULGSMC5119I Multiple DEFINE or MODIFY statements are erased in system config\n");
        logMSG = false;
    } else if (rc == 0 && rs == 100) {
        sprintf(errMsg, "ULGSMC5120I Asynchronous operation succeeded\n");
        logMSG = false;
    } else if (rc == 0 && rs == 104) {
        sprintf(errMsg, "ULGSMC5121I Asynchronous operation in progress\n");
        logMSG = false;
    } else if (rc == 0 && rs == 108) {
        sprintf(errMsg, "ULGSMC5122E Asynchronous operation failed\n");
    /* use the same message number for all the functional level output */
    } else if (rc == 0 && rs == 540) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is z/VM V5.4\n");
        logMSG = false;
    } else if (rc == 0 && rs == 610) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is z/VM V6.1\n");
        logMSG = false;
    } else if (rc == 0 && rs == 611) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is the updated z/VM V6.1 SPE release\n");
        logMSG = false;
    } else if (rc == 0 && rs == 620) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is z/VM V6.2\n");
        logMSG = false;
    } else if (rc == 0 && rs == 630) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is z/VM V6.3\n");
        logMSG = false;
    } else if (rc == 0 && rs == 640) {
        sprintf(errMsg, "ULGSMC5123I The API functional level is z/VM V6.4\n");
        logMSG = false;
    } else if (rc == 4 && rs == 4) {
        sprintf(errMsg, "ULGSMC5124W Request does not exist\n");
    } else if (rc == 4 && rs == 5) {
        sprintf(errMsg, "ULGSMC5125W Unrestricted LAN\n");
    } else if (rc == 4 && rs == 6) {
        sprintf(errMsg, "ULGSMC5126W No authorized users\n");
    } else if (rc == 4 && rs == 8) {
        sprintf(errMsg, "ULGSMC5127W Device does not exist\n");
    } else if (rc == 4 && rs == 28) {
        sprintf(errMsg, "ULGSMC5128W Return buffer is empty\n");
    } else if (rc == 4 && rs == 3000) {
        sprintf(errMsg, "ULGSMC5129W VMRELOCATE TEST error\n");
    } else if (rc == 4 && rs == 3001) {
        sprintf(errMsg, "ULGSMC5130W No active relocations found\n");
    } else if (rc == 4 && rs == 3008) {
        sprintf(errMsg, "ULGSMC5131W System is not a member of an SSI cluster\n");
    } else if (rc == 8 && rs == 2) {
        sprintf(errMsg, "ULGSMC5132E Invalid access user\n");
    } else if (rc == 8 && rs == 3) {
        sprintf(errMsg, "ULGSMC5133E Invalid op value\n");
    } else if (rc == 8 && rs == 4 && strcmp(class, "Virtual_Network_LAN_Access") == 0) {
        sprintf(errMsg, "ULGSMC5134E Invalid promiscuity value\n");
    } else if (rc == 8 && rs == 4 && strcmp(class, "Image_Definition_Delete_DM") == 0) {
        sprintf(errMsg, "ULGSMC5135E Directory entry to be deleted not found\n");
    } else if (rc == 8 && rs == 4 && strcmp(class, "System_Performance_Threshold_Enable") == 0) {
        sprintf(errMsg, "ULGSMC5136E Performance monitoring virtual server not found\n");
    } else if (rc == 8 && rs == 8 && strcmp(class, "Virtual_Network_Vswitch_Query_Stats") == 0) {
        sprintf(errMsg, "ULGSMC5137E This funcion is not available on this system\n");
    } else if (rc == 8 && rs == 8) {
        sprintf(errMsg, "ULGSMC5138E Device does not exist\n");
    } else if (rc == 8 && rs == 10) {
        sprintf(errMsg, "ULGSMC5139E Device not available for attachment\n");
    } else if (rc == 8 && rs == 12 && strcmp(class, "Image_MDISK_Link_Query") == 0) {
        sprintf(errMsg, "ULGSMC5140E target_identifier not logged on\n");
    } else if (rc == 8 && rs == 12 && strcmp(class, "Page_or_Spool_Volume_Add") == 0) {
        sprintf(errMsg, "ULGSMC5141E Device not a volume\n");
    } else if (rc == 8 && rs == 12 && strcmp(class, "VMRELOCATE_Image_Attributes") == 0) {
        sprintf(errMsg, "ULGSMC5142E target_identifier not logged on\n");
    } else if (rc == 8 && rs == 12 && strcmp(class, "Network_IP_Interface_Remove") == 0) {
        sprintf(errMsg, "ULGSMC5143E An error was encountered on IFCONFIG command\n");
    } else if (rc == 8 && rs == 13) {
        sprintf(errMsg, "ULGSMC5144E Match key length does not match the match key specified\n");
    } else if (rc == 8 && rs == 14) {
        sprintf(errMsg, "ULGSMC5145E Free modes not available\n");
    } else if (rc == 8 && rs == 18) {
        sprintf(errMsg, "ULGSMC5146E Volume does not exist\n");
    } else if (rc == 8 && rs == 19) {
        sprintf(errMsg, "ULGSMC5147E Volume is CP owned and cannot be used\n");
    } else if (rc == 8 && rs == 20 && strcmp(class, "Image_Volume_Share") == 0) {
        sprintf(errMsg, "ULGSMC5148E Volume is CP system and cannot be used\n");
    } else if (rc == 8 && rs == 20) {
        sprintf(errMsg, "ULGSMC5149E Volume label already CP_OWNED on this system or in this system's configuration\n");
    } else if (rc == 8 && rs == 24 && strcmp(class, "Image_Definition_Async_Updates") == 0) {
        sprintf(errMsg, "ULGSMC5150E Unable to write ASYNCH file\n");
    } else if (rc == 8 && rs == 24) {
        sprintf(errMsg, "ULGSMC5151E Error linking parm disk\n");
    } else if (rc == 8 && rs == 28) {
        sprintf(errMsg, "ULGSMC5152E Parm disk not RW\n");
    } else if (rc == 8 && rs == 32) {
        sprintf(errMsg, "ULGSMC5153E System configuration not found on parm disk\n");
    } else if (rc == 8 && rs == 34) {
        sprintf(errMsg, "ULGSMC5154E System configuration has bad data\n");
    } else if (rc == 8 && rs == 38) {
        sprintf(errMsg, "ULGSMC5155E CP disk modes not available\n");
    } else if (rc == 8 && rs == 40) {
        sprintf(errMsg, "ULGSMC5156E Parm disk is full\n");
    } else if (rc == 8 && rs == 42) {
        sprintf(errMsg, "ULGSMC5157E Parm disk access not allowed\n");
    } else if (rc == 8 && rs == 44) {
        sprintf(errMsg, "ULGSMC5158E No link password for parm disk was provided\n");
    } else if (rc == 8 && rs == 45) {
        sprintf(errMsg, "ULGSMC5159E Userid not logged on\n");
    } else if (rc == 8 && rs == 46) {
        sprintf(errMsg, "ULGSMC5160E Parm disk password is incorrect\n");
    } else if (rc == 8 && rs == 48) {
        sprintf(errMsg, "ULGSMC5161E Parm disk is not in server's user directory\n");
    } else if (rc == 8 && rs == 50) {
        sprintf(errMsg, "ULGSMC5162E Error with CPRELEASE of parm disk\n");
    } else if (rc == 8 && rs == 52) {
        sprintf(errMsg, "ULGSMC5163E Error in access of CPACCESS parm disk\n");
    } else if (rc == 8 && rs == 241) {
        sprintf(errMsg, "ULGSMC5164E Internal communication error\n");
    } else if (rc == 8 && rs == 1821) {
        sprintf(errMsg, "ULGSMC5165E Relocation domain domain_name does not exist\n");
    } else if (rc == 8 && rs == 1822) {
        sprintf(errMsg, "ULGSMC5166E User target_identifier cannot be set to a new relocation domain domain_name without the FORCE\n");
    } else if (rc == 8 && rs == 1823) {
        sprintf(errMsg, "ULGSMC5167E A multiconfiguration virtual machine cannot be relocated\n");
    } else if (rc == 8 && rs == 2783) {
        sprintf(errMsg, "ULGSMC5168E Invalid LAN ID\n");
    } else if (rc == 8 && rs == 2795) {
        sprintf(errMsg, "ULGSMC5169E Invalid LAN parameter\n");
    } else if (rc == 8 && rs == 3000) {
        sprintf(errMsg, "ULGSMC5170E VMRELOCATE MOVE error\n");
    } else if (rc == 8 && rs == 3002) {
        sprintf(errMsg, "ULGSMC5171E Invalid parameter name\n");
    } else if (rc == 8 && rs == 3003) {
        sprintf(errMsg, "ULGSMC5172E Invalid parameter operand\n");
    } else if (rc == 8 && rs == 3004) {
        sprintf(errMsg, "ULGSMC5173E Required Parameter is missing\n");
    } else if (rc == 8 && rs == 3006) {
        sprintf(errMsg, "ULGSMC5174E SSI is not in a STABLE state\n");
    } else if (rc == 8 && rs == 3007) {
        sprintf(errMsg, "ULGSMC5175E The volume ID or slot is not available on all systems in the SSI\n");
    } else if (rc == 8 && rs == 3008) {
        sprintf(errMsg, "ULGSMC5176E System is not a member of an SSI cluster\n");
    } else if (rc == 8 && rs == 3010) {
        sprintf(errMsg, "ULGSMC5177E VMRELOCATE modify error\n");
    } else if (rc == 8 && rs == 3011) {
        sprintf(errMsg, "ULGSMC5178E No unique CP_OWNED slot available on system and in System Config\n");
    } else if (rc == 8 && rs == 3012) {
        sprintf(errMsg, "ULGSMC5179E Volume does not exist\n");
    } else if (rc == 8 && rs == 3013) {
        sprintf(errMsg, "ULGSMC5180E Volume is offline\n");
    } else if (rc == 8 && rs == 3014) {
        sprintf(errMsg, "ULGSMC5181E Volume does not support sharing\n");
    } else if (rc == 8) {
        sprintf(errMsg, "ULGSMC5182E The RS %d represents the HCP/DMS %d message number\n", rs, rs);
    } else if (rc == 24 && rs == 13) {
        sprintf(errMsg, "ULGSMC5183E Metadata entry name value length exceeds allowable length (1024)\n");
    } else if (rc == 24) {
        fillSMAPIsyntaxReason(rs, syntaxErrorMessage);
        sprintf(errMsg, "ULGSMC5184E Syntax error in function parameter %d; %s\n", (rs/100), syntaxErrorMessage);
    } else if (rc == 28 && rs == 0) {
        sprintf(errMsg, "ULGSMC5185E Namelist file not found\n");
    } else if (rc == 36 && rs == 0) {
        sprintf(errMsg, "ULGSMC5186E Request is authorized\n");
    } else if (rc == 36 && rs == 4) {
        sprintf(errMsg, "ULGSMC5187E Authorization deferred to directory manager\n");
    } else if (rc == 100 && rs == 0) {
        sprintf(errMsg, "ULGSMC5188E Request not authorized by external security manager\n");
    } else if (rc == 100 && rs == 4) {
        sprintf(errMsg, "ULGSMC5189E Authorization deferred to directory manager\n");
    } else if (rc == 100 && rs == 8) {
        sprintf(errMsg, "ULGSMC5190E Request not authorized by external security manager\n");
    } else if (rc == 100 && rs == 12) {
        sprintf(errMsg, "ULGSMC5191E Request not authorized by directory manager\n");
    } else if (rc == 100 && rs == 16) {
        sprintf(errMsg, "ULGSMC5192E Request not authorized by server\n");
    } else if (rc == 104 && rs == 0) {
        sprintf(errMsg, "ULGSMC5193E Authorization file not found\n");
    } else if (rc == 106 && rs == 0) {
        sprintf(errMsg, "ULGSMC5194E Authorization file cannot be updated\n");
    } else if (rc == 108 && rs == 0) {
        sprintf(errMsg, "ULGSMC5195E Authorization file entry already exists\n");
    } else if (rc == 112 && rs == 0) {
        sprintf(errMsg, "ULGSMC5196E Authorization file entry does not exist\n");
    } else if (rc == 120 && rs == 0) {
        sprintf(errMsg, "ULGSMC5197E Authentication error; userid or password not valid\n");
    } else if (rc == 128 && rs == 0) {
        sprintf(errMsg, "ULGSMC5198E Authentication error; password expired\n");
    } else if (rc == 188) {
        sprintf(errMsg, "ULGSMC5199E Internal server error; ESM failure. - product-specific return code : %d\n", rs);
    } else if (rc == 192) {
        sprintf(errMsg, "ULGSMC5200E Internal server error; cannot authenticate user/password. - product-specific return code : %d\n", rs);
    } else if (rc == 200 && rs == 0) {
        sprintf(errMsg, "ULGSMC5201E Image operation error\n");
    } else if (rc == 200 && rs == 4) {
        sprintf(errMsg, "ULGSMC5202E Image not found\n");
    } else if (rc == 200 && rs == 8) {
        sprintf(errMsg, "ULGSMC5203E Image already active\n");
    } else if (rc == 200 && rs == 12) {
        sprintf(errMsg, "ULGSMC5204E Image not active\n");
    } else if (rc == 200 && rs == 16) {
        sprintf(errMsg, "ULGSMC5205E Image being deactivated\n");
    } else if (rc == 200 && rs == 24) {
        sprintf(errMsg, "ULGSMC5206E List not found\n");
    } else if (rc == 200 && rs == 28) {
        sprintf(errMsg, "ULGSMC5207E Some images in list not activated\n");
    } else if (rc == 200 && rs == 32) {
        sprintf(errMsg, "ULGSMC5208E Some images in list not deactivated\n");
    } else if (rc == 200 && rs == 36 && strcmp(class, "Image_Recycle") == 0) {
        sprintf(errMsg, "ULGSMC5209E Some images in list not recycled\n");
    } else if (rc == 200 && rs == 36 && strcmp(class, "Image_Deactivate") == 0) {
        sprintf(errMsg, "ULGSMC5210E Specified time results in interval greater than max allowed\n");
    } else if (rc == 204 && rs == 0) {
        sprintf(errMsg, "ULGSMC5211E Image device usage error\n");
    } else if (rc == 204 && rs == 2) {
        sprintf(errMsg, "ULGSMC5212E Input image device number not valid\n");
    } else if (rc == 204 && rs == 4) {
        sprintf(errMsg, "ULGSMC5213E Image device already exists\n");
    } else if (rc == 204 && rs == 8) {
        sprintf(errMsg, "ULGSMC5214E Image device does not exist\n");
    } else if (rc == 204 && rs == 12) {
        sprintf(errMsg, "ULGSMC5215E Image device is busy\n");
    } else if (rc == 204 && rs == 16) {
        sprintf(errMsg, "ULGSMC5216E Image device is not available\n");
    } else if (rc == 204 && rs == 20) {
        sprintf(errMsg, "ULGSMC5217E Image device already connected\n");
    } else if (rc == 204 && rs == 24) {
        sprintf(errMsg, "ULGSMC5218E Image device is not a tape drive, or cannot be assigned/reset\n");
    } else if (rc == 204 && rs == 28 && strcmp(class, "Image_Device_Reset") == 0) {
        sprintf(errMsg, "ULGSMC5219E Image device is not a shared DASD\n");
    } else if (rc == 204 && rs == 28) {
        sprintf(errMsg, "ULGSMC5220E Image device already defined as type other than network adapter\n");
    } else if (rc == 204 && rs == 32) {
        sprintf(errMsg, "ULGSMC5221E Image device is not a reserved DASD\n");
    } else if (rc == 204 && rs == 36) {
        sprintf(errMsg, "ULGSMC5222E I/O error on image device\n");
    } else if (rc == 204 && rs == 40) {
        sprintf(errMsg, "ULGSMC5223E Virtual Network Adapter not deleted\n");
    } else if (rc == 204 && rs == 44) {
        sprintf(errMsg, "ULGSMC5224E DASD volume cannot be deleted\n");
    } else if (rc == 204 && rs == 48) {
        sprintf(errMsg, "ULGSMC5225E Virtual network adapter is already disconnected\n");
    } else if (rc == 208 && rs == 0) {
        sprintf(errMsg, "ULGSMC5226E Image disk usage error\n");
    } else if (rc == 208 && rs == 4) {
        sprintf(errMsg, "ULGSMC5227E Image disk already in use\n");
    } else if (rc == 208 && rs == 8) {
        sprintf(errMsg, "ULGSMC5228E Image disk not in use\n");
    } else if (rc == 208 && rs == 12) {
        sprintf(errMsg, "ULGSMC5229E Image disk not available\n");
    } else if (rc == 208 && rs == 16) {
        sprintf(errMsg, "ULGSMC5230E Image disk cannot be shared as requested\n");
    } else if (rc == 208 && rs == 20) {
        sprintf(errMsg, "ULGSMC5231E Image disk shared in different mode\n");
    } else if (rc == 208 && rs == 28) {
        sprintf(errMsg, "ULGSMC5232E Image disk does not have required password\n");
    } else if (rc == 208 && rs == 32) {
        sprintf(errMsg, "ULGSMC5233E Incorrect password specified for image disk\n");
    } else if (rc == 208 && rs == 36) {
        sprintf(errMsg, "ULGSMC5234E Image disk does not exist\n");
    } else if (rc == 208 && rs == 1157) {
        sprintf(errMsg, "ULGSMC5235E MDISK DEVNO parameter requires the device to be a free volume\n");
    } else if (rc == 212 && rs == 0) {
        sprintf(errMsg, "ULGSMC5236E Active image connectivity error\n");
    } else if (rc == 212 && rs == 4) {
        sprintf(errMsg, "ULGSMC5237E Partner image not found\n");
    } else if (rc == 212 && rs == 8 && strcmp(class, "Virtual_Network_Adapter_Query") == 0) {
        sprintf(errMsg, "ULGSMC5238E Adapter does not exist\n");
    } else if (rc == 212 && rs == 8 && strcmp(class, "Virtual_Network_Adapter_Query_Extended") == 0) {
        sprintf(errMsg, "ULGSMC5239E Adapter does not exist\n");
    } else if (rc == 212 && rs == 8) {
        sprintf(errMsg, "ULGSMC5240E Image not authorized to connect\n");
    } else if (rc == 212 && rs == 12) {
        sprintf(errMsg, "ULGSMC5241E LAN does not exist\n");
    } else if (rc == 212 && rs == 16) {
        sprintf(errMsg, "ULGSMC5242E LAN owner LAN name does not exist\n");
    } else if (rc == 212 && rs == 20) {
        sprintf(errMsg, "ULGSMC5243E Requested LAN owner not active\n");
    } else if (rc == 212 && rs == 24) {
        sprintf(errMsg, "ULGSMC5244E LAN name already exists with different attributes\n");
    } else if (rc == 212 && rs == 28) {
        sprintf(errMsg, "ULGSMC5245E Image device not correct type for requested connection\n");
    } else if (rc == 212 && rs == 32) {
        sprintf(errMsg, "ULGSMC5246E Image device not connected to LAN\n");
    } else if (rc == 212 && rs == 36) {
        sprintf(errMsg, "ULGSMC5247E Virtual switch already exists\n");
    } else if (rc == 212 && rs == 40) {
        sprintf(errMsg, "ULGSMC5248E Virtual switch does not exist\n");
    } else if (rc == 212 && rs == 44) {
        sprintf(errMsg, "ULGSMC5249E Image already authorized\n");
    } else if (rc == 212 && rs == 48) {
        sprintf(errMsg, "ULGSMC5250E VLAN does not exist\n");
    } else if (rc == 212 && rs == 52) {
        sprintf(errMsg, "ULGSMC5251E Maximum number of connections reached\n");
    } else if (rc == 212 && rs == 96) {
        sprintf(errMsg, "ULGSMC5252E Unknown reason\n");
    } else if (rc == 216 && rs == 2) {
        sprintf(errMsg, "ULGSMC5253E Input virtual CPU value out of range\n");
    } else if (rc == 216 && rs == 4) {
        sprintf(errMsg, "ULGSMC5254E Virtual CPU not found\n");
    } else if (rc == 216 && rs == 12) {
        sprintf(errMsg, "ULGSMC5255E Image not active\n");
    } else if (rc == 216 && rs == 24) {
        sprintf(errMsg, "ULGSMC5256E Virtual CPU already exists\n");
    } else if (rc == 216 && rs == 28) {
        sprintf(errMsg, "ULGSMC5257E Virtual CPU address beyond allowable range defined in directory\n");
    } else if (rc == 216 && rs == 40) {
        sprintf(errMsg, "ULGSMC5258E Processor type not supported on your system\n");
    } else if (rc == 300 && rs == 0) {
        sprintf(errMsg, "ULGSMC5259E Image volume operation successful\n");
    } else if (rc == 300 && rs == 8) {
        sprintf(errMsg, "ULGSMC5260E Device not found\n");
    } else if (rc == 300 && rs == 10) {
        sprintf(errMsg, "ULGSMC5261E Device not available for attachment\n");
    } else if (rc == 300 && rs == 12) {
        sprintf(errMsg, "ULGSMC5262E Device not a volume\n");
    } else if (rc == 300 && rs == 14) {
        sprintf(errMsg, "ULGSMC5263E Free modes not available\n");
    } else if (rc == 300 && rs == 16) {
        sprintf(errMsg, "ULGSMC5264E Device vary online failed\n");
    } else if (rc == 300 && rs == 18) {
        sprintf(errMsg, "ULGSMC5265E Volume label not found in system configuration\n");
    } else if (rc == 300 && rs == 20) {
        sprintf(errMsg, "ULGSMC5266E Volume label already in system configuration\n");
    } else if (rc == 300 && rs == 22) {
        sprintf(errMsg, "ULGSMC5267E Parm disks 1 and 2 are same\n");
    } else if (rc == 300 && rs == 24) {
        sprintf(errMsg, "ULGSMC5268E Error linking parm disk (1 or 2)\n");
    } else if (rc == 300 && rs == 28) {
        sprintf(errMsg, "ULGSMC5269E Parm disk (1 or 2) not RW\n");
    } else if (rc == 300 && rs == 32) {
        sprintf(errMsg, "ULGSMC5270E System configuration not found on parm disk 1\n");
    } else if (rc == 300 && rs == 34) {
        sprintf(errMsg, "ULGSMC5271E System configuration has bad data\n");
    } else if (rc == 300 && rs == 36) {
        sprintf(errMsg, "ULGSMC5272E Syntax errors updating system configuration file\n");
    } else if (rc == 300 && rs == 38) {
        sprintf(errMsg, "ULGSMC5273E CP disk modes not available\n");
    } else if (rc == 300 && rs == 40) {
        sprintf(errMsg, "ULGSMC5274E Parm disk (1 or 2) is full\n");
    } else if (rc == 300 && rs == 42) {
        sprintf(errMsg, "ULGSMC5275E Parm disk (1 or 2) access not allowed\n");
    } else if (rc == 300 && rs == 44) {
        sprintf(errMsg, "ULGSMC5276E Parm disk (1 or 2) PW not supplied\n");
    } else if (rc == 300 && rs == 46) {
        sprintf(errMsg, "ULGSMC5277E Parm disk (1 or 2) PW is incorrect\n");
    } else if (rc == 300 && rs == 48) {
        sprintf(errMsg, "ULGSMC5278E Parm disk (1 or 2) is not in server's user directory\n");
    } else if (rc == 300 && rs == 50) {
        sprintf(errMsg, "ULGSMC5279E Error in release of CPRELEASE parm disk (1 or 2)\n");
    } else if (rc == 300 && rs == 52) {
        sprintf(errMsg, "ULGSMC5280E Error in access of CPACCESS parm disk (1 or 2)\n");
    } else if (rc == 396 && rs == 0) {
        sprintf(errMsg, "ULGSMC5281E Internal system error\n");
    } else if (rc == 396) {
        sprintf(errMsg, "ULGSMC5282E Internal error found. - product-specific return code : %d\n", rs);
    } else if (rc == 400 && rs == 0) {
        sprintf(errMsg, "ULGSMC5283E Image or profile definition error\n");
    } else if (rc == 400 && rs == 4) {
        sprintf(errMsg, "ULGSMC5284E Image or profile definition not found\n");
    } else if (rc == 400 && rs == 8) {
        sprintf(errMsg, "ULGSMC5285E Image or profile name already defined\n");
    } else if (rc == 400 && rs == 12) {
        sprintf(errMsg, "ULGSMC5286E Image or profile definition is locked \n");
    } else if (rc == 400 && rs == 16) {
        sprintf(errMsg, "ULGSMC5287E Image or profile definition cannot be deleted\n");
    } else if (rc == 400 && rs == 20) {
        sprintf(errMsg, "ULGSMC5288E Image prototype is not defined\n");
    } else if (rc == 400 && rs == 24) {
        sprintf(errMsg, "ULGSMC5289E Image or profile definition is not locked\n");
    } else if (rc == 400 && rs == 40) {
        sprintf(errMsg, "ULGSMC5290E Multiple user statements\n");
    } else if (rc == 404 && rs == 0) {
        sprintf(errMsg, "ULGSMC5291E Image device definition error\n");
    } else if (rc == 404 && rs == 4) {
        sprintf(errMsg, "ULGSMC5292E Image device already defined\n");
    } else if (rc == 404 && rs == 8) {
        sprintf(errMsg, "ULGSMC5293E Image device not defined\n");
    } else if (rc == 404 && rs == 12) {
        sprintf(errMsg, "ULGSMC5294E Image device is locked\n");
    } else if (rc == 404 && rs == 24 &&
    		((strcmp(class, "Image_Disk_Copy_DM") == 0) || strcmp(class, "Image_Disk_Create_DM") == 0)) {
        sprintf(errMsg, "ULGSMC5295E Image device type not same as source\n");
    } else if (rc == 404 && rs == 24) {
        sprintf(errMsg, "ULGSMC5296E Image device is not locked\n");
    } else if (rc == 404 && rs == 28) {
        sprintf(errMsg, "ULGSMC5297E Image device size not same as source\n");
    } else if (rc == 408 && rs == 0) {
        sprintf(errMsg, "ULGSMC5298E Image disk definition error\n");
    } else if (rc == 408 && rs == 4) {
        sprintf(errMsg, "ULGSMC5299E Image disk already defined\n");
    } else if (rc == 408 && rs == 8) {
        sprintf(errMsg, "ULGSMC5300E Image disk not defined\n");
    } else if (rc == 408 && rs == 12) {
        sprintf(errMsg, "ULGSMC5301E Image device is locked\n");
    } else if (rc == 408 && rs == 16) {
        sprintf(errMsg, "ULGSMC5302E Image disk sharing not allowed by target image definition\n");
    } else if (rc == 408 && rs == 24) {
        sprintf(errMsg, "ULGSMC5303E Requested image disk space not available\n");
    } else if (rc == 408 && rs == 28) {
        sprintf(errMsg, "ULGSMC5304E Image disk does not have required password\n");
    } else if (rc == 408 && rs == 32) {
        sprintf(errMsg, "ULGSMC5305E Incorrect password specified for image disk\n");
    } else if (rc == 412 && rs == 0) {
        sprintf(errMsg, "ULGSMC5306E Image connectivity definition error\n");
    } else if (rc == 412 && rs == 4) {
        sprintf(errMsg, "ULGSMC5307E Partner image not found\n");
    } else if (rc == 412 && rs == 16) {
        sprintf(errMsg, "ULGSMC5308E Parameters do not match existing directory statement\n");
    } else if (rc == 412 && rs == 28) {
        sprintf(errMsg, "ULGSMC5309E Image device not correct type for requested connection\n");
    } else if (rc == 416 && rs == 0) {
        sprintf(errMsg, "ULGSMC5310E Prototype definition error\n");
    } else if (rc == 416 && rs == 4) {
        sprintf(errMsg, "ULGSMC5311E Prototype definition not found\n");
    } else if (rc == 416 && rs == 8) {
        sprintf(errMsg, "ULGSMC5312E Prototype already exists\n");
    } else if (rc == 420 && rs == 4) {
        sprintf(errMsg, "ULGSMC5313E Group, region, or volume name is already defined\n");
    } else if (rc == 420 && rs == 8) {
        sprintf(errMsg, "ULGSMC5314E That group, region, or volume name is not defined\n");
    } else if (rc == 420 && rs == 12) {
        sprintf(errMsg, "ULGSMC5315E That region name is not included in the group\n");
    } else if (rc == 420 && rs == 36) {
        sprintf(errMsg, "ULGSMC5316E The requested volume is offline or is not a DASD device\n");
    } else if (rc == 424 && rs == 4) {
        sprintf(errMsg, "ULGSMC5317E Namesave statement already exists\n");
    } else if (rc == 424 && rs == 8) {
        sprintf(errMsg, "ULGSMC5318E Segment name not found\n");
    } else if (rc == 428 && rs == 4) {
        sprintf(errMsg, "ULGSMC5319E Duplicate subscription\n");
    } else if (rc == 428 && rs == 8) {
        sprintf(errMsg, "ULGSMC5320E No matching entries\n");
    } else if (rc == 432 && rs == 4) {
        sprintf(errMsg, "ULGSMC5321E Tag name is already defined\n");
    } else if (rc == 432 && rs == 8) {
        sprintf(errMsg, "ULGSMC5322E Tag name is not defined\n");
    } else if (rc == 432 && rs == 8) {
        sprintf(errMsg, "ULGSMC5323E Tag name is not defined\n");
    } else if (rc == 432 && rs == 12) {
        sprintf(errMsg, "ULGSMC5324E Tag ordinal is already defined\n");
    } else if (rc == 432 && rs == 16 && strcmp(class, "Directory_Manager_Local_Tag_Set_DM") == 0) {
        sprintf(errMsg, "ULGSMC5325E Tag too long\n");
    } else if (rc == 432 && rs == 16) {
        sprintf(errMsg, "ULGSMC5326E Tag is in use in one or more directory entries, can not be revoked\n");
    } else if (rc == 432 && rs == 20) {
        sprintf(errMsg, "ULGSMC5327E Use not allowed by exit routine\n");
    } else if (rc == 436 && rs == 4) {
        sprintf(errMsg, "ULGSMC5328E Profile included not found\n");
    } else if (rc == 436 && rs == 40) {
        sprintf(errMsg, "ULGSMC5329E Multiple profiles included\n");
    } else if (rc == 444 && rs == 0) {
        sprintf(errMsg, "ULGSMC5330E Password policy error\n");
    } else if (rc == 444 && rs == 4) {
        sprintf(errMsg, "ULGSMC5331E Password too long\n");
    } else if (rc == 444 && rs == 8) {
        sprintf(errMsg, "ULGSMC5332E Password too short\n");
    } else if (rc == 444 && rs == 12) {
        sprintf(errMsg, "ULGSMC5333E Password content does not match policy\n");
    } else if (rc == 448 && rs == 0) {
        sprintf(errMsg, "ULGSMC5334E Account policy error\n");
    } else if (rc == 448 && rs == 4) {
        sprintf(errMsg, "ULGSMC5335E Account number too long\n");
    } else if (rc == 448 && rs == 8) {
        sprintf(errMsg, "ULGSMC5336E Account number too short\n");
    } else if (rc == 448 && rs == 12) {
        sprintf(errMsg, "ULGSMC5337E Account number content does not match policy\n");
    } else if (rc == 452 && rs == 4) {
        sprintf(errMsg, "ULGSMC5337E Task not found\n");
    } else if (rc == 456 && rs == 4) {
        sprintf(errMsg, "ULGSMC5339E LOADDEV statement not found\n");
    } else if (rc == 460 && rs == 4) {
        sprintf(errMsg, "ULGSMC5340E Image does not have an IPL statement\n");
    } else if (rc == 500 && rs == 0) {
        sprintf(errMsg, "ULGSMC5341E Directory manager request could not be completed\n");
    } else if (rc == 500 && rs == 4) {
        sprintf(errMsg, "ULGSMC5342E Directory manager is not accepting updates\n");
    } else if (rc == 500 && rs == 8) {
        sprintf(errMsg, "ULGSMC5343E Directory manager is not available\n");
    } else if (rc == 500 && rs == 20) {
        sprintf(errMsg, "ULGSMC5344E Password format not supported\n");
    } else if (rc == 504) {
        sprintf(errMsg, "ULGSMC5345E Target ID not added - product-specific return code : %d\n", rs);
    } else if (rc == 520 && rs == 24) {
        sprintf(errMsg, "ULGSMC5346E Only one base CPU may be defined\n");
    } else if (rc == 520 && rs == 28) {
        sprintf(errMsg, "ULGSMC5347E Input virtual CPU value out of range\n");
    } else if (rc == 520 && rs == 30) {
        sprintf(errMsg, "ULGSMC5348E CPU not found\n");
    } else if (rc == 520 && rs == 32) {
        sprintf(errMsg, "ULGSMC5349E Maximum allowable number of virtual CPUs is exceeded\n");
    } else if (rc == 520 && rs == 45) {
        sprintf(errMsg, "ULGSMC5350E The Cryptographic Coprocessor Facility (CCF) is not installed on this system\n");
    } else if (rc == 520 && rs == 2826) {
        sprintf(errMsg, "ULGSMC5351E SCPDATA contains invalid UTF-8 data\n");
    } else if (rc == 592 && rs == 0) {
        sprintf(errMsg, "ULGSMC5352E Asynchronous operation started\n");
    } else if (rc == 592) {
        sprintf(errMsg, "ULGSMC5353E Asynchronous operation started - product-specific asynchronous operation ID : %d\n", rs);
    } else if (rc == 596) {
        sprintf(errMsg, "ULGSMC5354E Internal directory manager error - product-specific return code : %d\n", rs);
    } else if (rc == 600 && rs == 8) {
        sprintf(errMsg, "ULGSMC5355E Bad page range\n");
    } else if (rc == 600 && rs == 12) {
        sprintf(errMsg, "ULGSMC5356E User not logged on\n");
    } else if (rc == 600 && rs == 16) {
        sprintf(errMsg, "ULGSMC5357E Could not save segment\n");
    } else if (rc == 600 && rs == 20) {
        sprintf(errMsg, "ULGSMC5358E Not authorized to issue internal system command or is not authorized for RSTD segment\n");
    } else if (rc == 600 && rs == 24) {
        sprintf(errMsg, "ULGSMC5359E Conflicting parameters\n");
    } else if (rc == 600 && rs == 28) {
        sprintf(errMsg, "ULGSMC5360E Segment not found or does not exist\n");
    } else if (rc == 600 && rs == 299) {
        sprintf(errMsg, "ULGSMC5361E Class S (skeleton) segment file already exists\n");
    } else if (rc == 620 && rs == 14) {
        sprintf(errMsg, "ULGSMC5362E Free modes not available\n");
    } else if (rc == 620 && rs == 22) {
        sprintf(errMsg, "ULGSMC5363E System config parm disks 1 and 2 are same\n");
    } else if (rc == 620 && rs == 24) {
        sprintf(errMsg, "ULGSMC5364E Error linking parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 28) {
        sprintf(errMsg, "ULGSMC5365E Parm disk (1 or 2) not RW\n");
    } else if (rc == 620 && rs == 32) {
        sprintf(errMsg, "ULGSMC5366E System config not found on parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 34) {
        sprintf(errMsg, "ULGSMC5367E System config has bad data\n");
    } else if (rc == 620 && rs == 36) {
        sprintf(errMsg, "ULGSMC5368E Syntax errors updating system config\n");
    } else if (rc == 620 && rs == 38) {
        sprintf(errMsg, "ULGSMC5369E CP disk modes not available\n");
    } else if (rc == 620 && rs == 40) {
        sprintf(errMsg, "ULGSMC5370E Parm disk (1 or 2) is full\n");
    } else if (rc == 620 && rs == 42) {
        sprintf(errMsg, "ULGSMC5371E Parm disk (1 or 2) access not allowed\n");
    } else if (rc == 620 && rs == 44) {
        sprintf(errMsg, "ULGSMC5372E Parm disk (1 or 2) PW not supplied\n");
    } else if (rc == 620 && rs == 46) {
        sprintf(errMsg, "ULGSMC5373E Parm disk (1 or 2) PW is incorrect\n");
    } else if (rc == 620 && rs == 48) {
        sprintf(errMsg, "ULGSMC5374E Parm disk (1 or 2) is not in server's directory\n");
    } else if (rc == 620 && rs == 50) {
        sprintf(errMsg, "ULGSMC5375E Error in release of CPRELEASE parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 52) {
        sprintf(errMsg, "ULGSMC5376E Error in access of CPACCESS parm disk (1 or 2)\n");
    } else if (rc == 620 && rs == 54) {
        sprintf(errMsg, "ULGSMC5377E DEFINE VSWITCH statement already exists in system config\n");
    } else if (rc == 620 && rs == 58) {
        sprintf(errMsg, "ULGSMC5378E MODIFY VSWITCH statement to userid not found in system config\n");
    } else if (rc == 620 && rs == 60) {
        sprintf(errMsg, "ULGSMC5379E DEFINE VSWITCH statement does not exist in system config\n");
    } else if (rc == 620 && rs == 62) {
        sprintf(errMsg, "ULGSMC5380E DEFINE operands conflict, cannot be updated in the system config\n");
    } else if (rc == 620 && rs == 64) {
        sprintf(errMsg, "ULGSMC5381E Multiple DEFINE or MODIFY statements found in system config\n");
    } else if (rc == 800 && rs == 8) {
        sprintf(errMsg, "ULGSMC5382E No measurement data exists\n");
    } else if (rc == 800 && rs == 12) {
        sprintf(errMsg, "ULGSMC5383E Incorrect syntax in update data \n");
    } else if (rc == 800 && rs == 16) {
        sprintf(errMsg, "ULGSMC5384E Not authorized to access file\n");
    } else if (rc == 800 && rs == 24) {
        sprintf(errMsg, "ULGSMC5385E Error writing file(s) to directory\n");
    } else if (rc == 800 && rs == 28) {
        sprintf(errMsg, "ULGSMC5386E Specified configuration file not found\n");
    } else if (rc == 800 && rs == 32) {
        sprintf(errMsg, "ULGSMC5387E Internal error processing updates\n");
    } else if (rc == 900 && rs == 4) {
        sprintf(errMsg, "ULGSMC5388E Custom exec not found\n");
    } else if (rc == 900 && rs == 8) {
        sprintf(errMsg, "ULGSMC5389E Worker server was not found\n");
    } else if (rc == 900 && rs == 12) {
        sprintf(errMsg, "ULGSMC5390E Specified function does not exist\n");
    } else if (rc == 900 && rs == 16) {
        sprintf(errMsg, "ULGSMC5391E Internal server error - DMSSIPTS entry for function is invalid\n");
    } else if (rc == 900 && rs == 20) {
        sprintf(errMsg, "ULGSMC5392E Total length does not match the specified input data\n");
    } else if (rc == 900 && rs == 24) {
        sprintf(errMsg, "ULGSMC5393E Error accessing SFS directory\n");
    } else if (rc == 900 && rs == 28) {
        sprintf(errMsg, "ULGSMC5394E Internal server error - error with format of function output\n");
    } else if (rc == 900 && rs == 32) {
        sprintf(errMsg, "ULGSMC5395E Internal server error - response from worker server was not valid\n");
    } else if (rc == 900 && rs == 36) {
        sprintf(errMsg, "ULGSMC5396E Specified length was not valid, out of valid server data range\n");
    } else if (rc == 900 && rs == 40) {
        sprintf(errMsg, "ULGSMC5397E Internal server socket error\n");
    } else if (rc == 900 && rs == 68) {
        sprintf(errMsg, "ULGSMC5398E Unable to access LOHCOST server\n");
    } else if (rc == 900 && rs == 99) {
        sprintf(errMsg, "ULGSMC5399E A system change occurred during the API call - reissue the API call to obtain the data\n");
    } else {
        sprintf(errMsg, "ULGSMC5999E Unknown\n");
    }

    // If this call is only for the new header, just print that header out
    if (newHeader) {
        printf("8 %d %d (details) %s", rc, rs, errMsg);
    } else {
        printf("  Description: %s", errMsg);
        if (logMSG == true) {
            TRACE_START(vmapiContextP, TRACEAREA_SMCLI, TRACELEVEL_ERROR);
                sprintf(line, "SMAPI error. SMAPi API: %s RC = %d RS = %d Description: %s\n", class, rc, rs, errMsg);
            TRACE_END_DEBUG(vmapiContextP, line);
        }
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

