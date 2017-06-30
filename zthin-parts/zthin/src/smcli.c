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

#include "wrapperutils.h"

/**
 * Internal query for async operations
 */
int queryAsyncOperation(char* image, int operationId, char * apiName, struct _vmApiInternalContext *vmapiContextP, char * statusString) {
    
    vmApiQueryAsynchronousOperationDmOutput* output;
    int rc;
    int loopCount = SLEEP_ASYNCH_RETRIES;

    while (true){
        rc = smQuery_Asychronous_Operation_DM(vmapiContextP, "", 0, "",
            image, operationId, &output);

        // Handle return code and reason code if any are non zero
        if (rc || output->common.returnCode || output->common.reasonCode) {
            // if rc is bad, then this is an internal error. Log and return
            if (rc) {
                printAndLogProcessingErrors("Query_Asychronous_Operation_DM", rc, vmapiContextP, statusString, 0);
                return rc;
            }    
                
            // If Asychronous completed 0,0, just return Done and 0 rc
            // Reason code of 100 also means completed
            if (output->common.returnCode == 0 && 
                (output->common.reasonCode == 0 || output->common.reasonCode == 100) ) {
                rc = printAndLogSmapiReturnCodeReasonCodeDescription(apiName, 0, 0, 
                         vmapiContextP, statusString);
                return rc;
            }
           
            // If reason code is 104 (still in progress) then we can retry if more retries left
            // else we need to return with the original 592 and reason code so caller can retry 
            if (output->common.returnCode == 0 && output->common.reasonCode == 104) {
                loopCount = loopCount -1;
                if (loopCount) {
                    sleep(SLEEP_ASYNCH_DEFAULT);   
                    continue;
                }else {
                    // We ran out of retries so we must recreate the original 592 asynch return code
                    rc = printAndLogSmapiReturnCodeReasonCodeDescription(apiName, 592, operationId, 
                         vmapiContextP, statusString);
                    return rc;
                }
            }    
            
            // The following case is where the query asynchronous operation failed
            // Report back a failure with that API vs the original API
            
            rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_Asychronous_Operation_DM", 
                output->common.returnCode, output->common.reasonCode, vmapiContextP, statusString);
            return rc;
        }
        
        // Handle SMAPI return code and reason code if async query returned 0
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Query_Asychronous_Operation_DM",
                output->common.returnCode, output->common.reasonCode, vmapiContextP, statusString);
    } /* end loop retries */

    return rc;
}

/*
  Print out help information
*/

int displayHelpInfo(int smapiLevel) {

    printf("Command line interface to SMAPI socket APIs.\n\n"
           "Usage: smcli function_name\n"
           "The API function names:\n"
           "  Asynchronous_Notification_Disable_DM\n"
           "  Asynchronous_Notification_Enable_DM\n"
           "  Asynchronous_Notification_Query_DM\n"
           "  Authorization_List_Add\n"
           "  Authorization_List_Query\n"
           "  Authorization_List_Remove\n"
           "  Check_Authentication\n");
    if (smapiLevel >= 620) {
        printf("  Delete_ABEND_Dump\n");
    }
    printf("  Directory_Manager_Local_Tag_Define_DM\n"
           "  Directory_Manager_Local_Tag_Delete_DM\n"
           "  Directory_Manager_Local_Tag_Query_DM\n"
           "  Directory_Manager_Local_Tag_Set_DM\n"
           "  Directory_Manager_Search_DM\n"
           "  Directory_Manager_Task_Cancel_DM\n");
    if (smapiLevel >= 611) {
        printf("  Event_Stream_Add\n"
               /* "  Event_Subscribe\n" These two not implemented
               "  Event_Unsubscribe\n"*/ );
    }
    printf("  Image_Activate\n"
           "  Image_Active_Configuration_Query\n");

    if (smapiLevel >= 640) {
        printf("  Image_Console_Get\n");
    }

    printf("  Image_CPU_Define\n"
           "  Image_CPU_Define_DM\n"
           "  Image_CPU_Delete\n"
           "  Image_CPU_Delete_DM\n"
           "  Image_CPU_Query\n"
           "  Image_CPU_Query_DM\n"
           "  Image_CPU_Set_Maximum_DM\n"
           "  Image_Create_DM\n"
           "  Image_Deactivate\n");

    if (smapiLevel >= 620) {
        printf("  Image_Definition_Async_Updates\n"
               "  Image_Definition_Create_DM\n");
    }
    if (smapiLevel >= 611) {
        printf("  Image_Definition_Delete_DM\n"
               "  Image_Definition_Query_DM\n"
               "  Image_Definition_Update_DM\n");
    }
    printf("  Image_Delete_DM\n"
           "  Image_Device_Dedicate\n"
           "  Image_Device_Dedicate_DM\n"
           "  Image_Device_Reset\n"
           "  Image_Device_Undedicate\n"
           "  Image_Device_Undedicate_DM\n"
           "  Image_Disk_Copy\n"
           "  Image_Disk_Copy_DM\n"
           "  Image_Disk_Create\n"
           "  Image_Disk_Create_DM\n"
           "  Image_Disk_Delete\n"
           "  Image_Disk_Delete_DM\n"
           "  Image_Disk_Query\n"
           "  Image_Disk_Share\n"
           "  Image_Disk_Share_DM\n"
           "  Image_Disk_Unshare\n"
           "  Image_Disk_Unshare_DM\n"
           "  Image_IPL_Delete_DM\n"
           "  Image_IPL_Device_Query\n"
           "  Image_IPL_Query_DM\n"
           "  Image_IPL_Set_DM\n"
           "  Image_Lock_DM\n");
    if (smapiLevel >= 630) {
        printf("  Image_Lock_Query_DM\n"
               "  Image_MDISK_Link_Query\n");
    }
    printf(
           "  Image_Name_Query_DM\n"
           "  Image_Password_Set_DM\n");
    if (smapiLevel >= 630) {
        printf("  Image_Pause\n");
    }
    printf(
           "  Image_Performance_Query\n"
           "  Image_Query_Activate_Time\n"
           "  Image_Query_DM\n"
           "  Image_Recycle\n"
           "  Image_Replace_DM\n"
           "  Image_SCSI_Characteristics_Define_DM\n"
           "  Image_SCSI_Characteristics_Query_DM\n"
           "  Image_Status_Query\n"
           "  Image_Unlock_DM\n"
           "  Image_Volume_Add\n"
           "  Image_Volume_Delete\n");
    if (smapiLevel >= 620) {
        printf("  Image_Volume_Share\n");
    }
    printf(
           "  Image_Volume_Space_Define_DM\n");
    if (smapiLevel >= 620) {
        printf("  Image_Volume_Space_Define_Extended_DM\n");
    }
    printf("  Image_Volume_Space_Query_DM\n");
    if (smapiLevel >= 620) {
        printf("  Image_Volume_Space_Query_Extended_DM\n");
    }
    printf("  Image_Volume_Space_Remove_DM\n"
           "  IPaddr_Get\n");
    if (smapiLevel >= 620) {
        printf("  Metadata_Delete\n"
               "  Metadata_Get\n"
               "  Metadata_Set\n");
    }
    if (smapiLevel >= 640) {
        printf("  Metadata_Space_Query\n");
    }
    printf("  Name_List_Add\n"
           "  Name_List_Destroy\n"
           "  Name_List_Query\n"
           "  Name_List_Remove\n");
    if (smapiLevel >= 630) {
        printf("  Network_IP_Interface_Create\n"
               "  Network_IP_Interface_Modify\n"
               "  Network_IP_Interface_Query\n"
               "  Network_IP_Interface_Remove\n");
    }
    if (smapiLevel >= 620) {
        printf("  Page_or_Spool_Volume_Add\n"
               "  Process_ABEND_Dump\n");
    }
    printf("  Profile_Create_DM\n"
           "  Profile_Delete_DM\n"
           "  Profile_Lock_DM\n");
    if (smapiLevel >= 630) {
        printf("  Profile_Lock_Query_DM\n");
    }
    printf(
           "  Profile_Query_DM\n"
           "  Profile_Replace_DM\n"
           "  Profile_Unlock_DM\n"
           "  Prototype_Create_DM\n"
           "  Prototype_Delete_DM\n"
           "  Prototype_Name_Query_DM\n"
           "  Prototype_Query_DM\n"
           "  Prototype_Replace_DM\n");
    if (smapiLevel >= 620) {
        printf("  Query_ABEND_Dump\n"
               "  Query_All_DM\n");
    }
    printf("  Query_API_Functional_Level\n"
           "  Query_Asynchronous_Operation_DM\n"
           "  Query_Directory_Manager_Level_DM\n");
    if (smapiLevel >= 611) {
        printf("  Response_Recovery\n");
    }
    printf("  Shared_Memory_Access_Add_DM\n"
           "  Shared_Memory_Access_Query_DM\n"
           "  Shared_Memory_Access_Remove_DM\n"
           "  Shared_Memory_Create\n"
           "  Shared_Memory_Delete\n"
           "  Shared_Memory_Query\n"
           "  Shared_Memory_Replace\n");
    if (smapiLevel >= 630) {
        printf("  SMAPI_Status_Capture\n");
    }
    if (smapiLevel >= 620) {
        printf("  SSI_Query\n");
    }
    printf("  Static_Image_Changes_Activate_DM\n"
           "  Static_Image_Changes_Deactivate_DM\n"
           "  Static_Image_Changes_Immediate_DM\n");
    if (smapiLevel >= 611) {
        printf("  System_Config_Syntax_Check\n");
    }
    if (smapiLevel >= 620) {
        printf("  System_Disk_Accessibility\n");
    }
    if (smapiLevel >= 611) {
        printf("  System_Disk_Add\n");
    }
    if (smapiLevel >= 630) {
        printf("  System_Disk_IO_Query\n");
    }
    if (smapiLevel >= 611) {
        printf("  System_Disk_Query\n");
    }
    if (smapiLevel >= 630) {
        printf("  System_EQID_Query\n");
    }
    if (smapiLevel >= 620) {
        printf("  System_FCP_Free_Query\n");
    }
    printf("  System_Info_Query\n");
    if (smapiLevel >= 630) {
                printf("  System_Information_Query\n");
    }
    printf("  System_IO_Query\n");
    if (smapiLevel >= 630) {
        printf("  System_Page_Utilization_Query\n");
    }
    printf(
           "  System_Performance_Info_Query\n");
    if (smapiLevel >= 630) {
        printf("  System_Performance_Information_Query\n");
    }
    if (smapiLevel >= 620) {
        printf("  System_Performance_Threshold_Disable\n"
               "  System_Performance_Threshold_Enable\n");
    }
    if (smapiLevel >= 611) {
        printf("  System_SCSI_Disk_Add\n");
    }
    if (smapiLevel >= 620) {
                printf("  System_SCSI_Disk_Delete\n");
    }
    if (smapiLevel >= 611) {
        printf("  System_SCSI_Disk_Query\n");
    }
    if (smapiLevel >= 630) {
        printf("  System_Service_Query\n"
               "  System_Shutdown\n"
               "  System_Spool_Utilization_Query\n");
    }
    if (smapiLevel >= 611) {
        printf("  System_WWPN_Query\n");
    }
    printf("  Virtual_Channel_Connection_Create\n"
           "  Virtual_Channel_Connection_Create_DM\n"
           "  Virtual_Channel_Connection_Delete\n"
           "  Virtual_Channel_Connection_Delete_DM\n"
           "  Virtual_Network_Adapter_Connect_LAN\n"
           "  Virtual_Network_Adapter_Connect_LAN_DM\n"
           "  Virtual_Network_Adapter_Connect_Vswitch\n"
           "  Virtual_Network_Adapter_Connect_Vswitch_DM\n");
    if (smapiLevel >= 620) {
        printf("  Virtual_Network_Adapter_Connect_Vswitch_Extended\n");
    }
    printf("  Virtual_Network_Adapter_Create\n"
           "  Virtual_Network_Adapter_Create_DM\n");
    if (smapiLevel >= 611) {
        printf("  Virtual_Network_Adapter_Create_Extended\n"
               "  Virtual_Network_Adapter_Create_Extended_DM\n");
    }
    printf("  Virtual_Network_Adapter_Delete\n"
           "  Virtual_Network_Adapter_Delete_DM\n"
           "  Virtual_Network_Adapter_Disconnect\n"
           "  Virtual_Network_Adapter_Disconnect_DM\n"
           "  Virtual_Network_Adapter_Query\n");
    if (smapiLevel >= 630) {
        printf("  Virtual_Network_Adapter_Query_Extended\n");
    }
    printf("  Virtual_Network_LAN_Access\n"
           "  Virtual_Network_LAN_Access_Query\n"
           "  Virtual_Network_LAN_Create\n"
           "  Virtual_Network_LAN_Delete\n"
           "  Virtual_Network_LAN_Query\n");
    if (smapiLevel >= 611) {
        printf("  Virtual_Network_OSA_Query\n");
    }
    printf("  Virtual_Network_Query_LAN\n"
           "  Virtual_Network_Query_OSA\n");
    if (smapiLevel >= 620) {
        printf("  Virtual_Network_VLAN_Query_Stats\n");
    }
    printf("  Virtual_Network_Vswitch_Create\n");
    if (smapiLevel >= 611) {
        printf("  Virtual_Network_Vswitch_Create_Extended\n");
    }
    printf("  Virtual_Network_Vswitch_Delete\n");
    if (smapiLevel >= 611) {
        printf("  Virtual_Network_Vswitch_Delete_Extended\n");
    }
    printf("  Virtual_Network_Vswitch_Query\n");
    if (smapiLevel >= 620) {
        printf("  Virtual_Network_Vswitch_Query_Extended\n");
    }
    if (smapiLevel >= 630) {
        printf("  Virtual_Network_Vswitch_Query_IUO_Stats\n");
    }
    if (smapiLevel >= 620) {
        printf("  Virtual_Network_Vswitch_Query_Stats\n");
    }
    printf("  Virtual_Network_Vswitch_Set\n");
    if (smapiLevel >= 611) {
        printf("  Virtual_Network_Vswitch_Set_Extended\n");
    }
    if (smapiLevel >= 620) {
        printf("  VMRELOCATE\n"
               "  VMRELOCATE_Image_Attributes\n"
               "  VMRELOCATE_Modify\n"
               "  VMRELOCATE_Status\n");
    }
    printf(
           "  VMRM_Configuration_Query\n"
           "  VMRM_Configuration_Update\n"
           "  VMRM_Measurement_Query\n");
    if (smapiLevel >= 630) {
        printf("  xCAT_Commands_IUO\n");
    }
    printRCheaderHelp();
}

/**
 * Command line interface to SMAPI socket API
 */
int main(int argC, char* argV[]) {
    int rc = 0;  // Return code
    int j;
    int saveCount;
    int k;
    vmApiInternalContext vmapiContext;
    smMemoryGroupContext memContext;
    extern struct _smTrace externSmapiTraceFlags;
    int smapiLevel = 0;


    /* Initialize context and memory structure */
    INIT_CONTEXT_AND_MEMORY(&vmapiContext, &memContext, &externSmapiTraceFlags, rc);
    if (rc)  {
        // Out of memory
        return rc;
    }
    readTraceFile(&vmapiContext);
    TRACE_ENTRY_FLOW(&vmapiContext, TRACEAREA_ZTHIN_GENERAL);

    rc = getSmapiLevel(&vmapiContext, " ", &smapiLevel);
    if (rc != 0){
        printf("\nERROR: Unable to determine SMAPI level.\n");
        return 1;
    }

    if (argC < 2 || !strcmp(argV[1], "--help") || !strcmp(argV[1], "-h")) {
        displayHelpInfo(smapiLevel);
        rc =1;
        TRACE_EXIT_FLOW(&vmapiContext, TRACEAREA_ZTHIN_GENERAL, rc);
        /* Clean up for memory context */
        FREE_CONTEXT_MEMORY(&vmapiContext);
        return rc;
    }



#define APIS_611_COUNT 17
static const char * APIS_611[APIS_611_COUNT] = {
    "Event_Stream_Add",
    "Event_Subscribe",
    "Event_Unsubscribe",
    "Image_Definition_Delete_DM",
    "Image_Definition_Query_DM",
    "Image_Definition_Update_DM",
    "Image_Disk_Query",
    "Response_Recovery",
    "System_Config_Syntax_Check",
    "System_Disk_Add",
    "System_Disk_Query",
    "System_SCSI_Disk_Add",
    "System_SCSI_Disk_Query",
    "System_WWPN_Query",
    "Virtual_Network_Adapter_Create_Extended",
    "Virtual_Network_Adapter_Create_Extended_DM",
    "Virtual_Network_OSA_Query",
};

#define APIS_620_COUNT 27
static const char * APIS_620[APIS_620_COUNT] = {
    "Delete_ABEND_Dump",
    "Image_Definition_Async_Updates",
    "Image_Definition_Create_DM",
    "Image_Volume_Share",
    "Image_Volume_Space_Define_Extended_DM",
    "Image_Volume_Space_Query_Extended_DM",
    "Metadata_Delete",
    "Metadata_Get",
    "Metadata_Set",
    "Page_or_Spool_Volume_Add",
    "Process_ABEND_Dump",
    "Query_ABEND_Dump",
    "Query_All_DM",
    "SSI_Query",
    "System_Disk_Accessibility",
    "System_FCP_Free_Query",
    "System_SCSI_Disk_Delete",
    "System_Performance_Threshold_Disable",
    "System_Performance_Threshold_Enable",
    "Virtual_Network_Adapter_Connect_Vswitch_Extended",
    "Virtual_Network_VLAN_Query_Stats",
    "Virtual_Network_Vswitch_Query_Extended",
    "Virtual_Network_Vswitch_Query_Stats",
    "VMRELOCATE",
    "VMRELOCATE_Image_Attributes",
    "VMRELOCATE_Modify",
    "VMRELOCATE_Status",
};

#define APIS_630_COUNT 19
static const char * APIS_630[APIS_630_COUNT] = {
    "Image_Lock_Query_DM",
    "Image_MDISK_Link_Query",
    "Image_Pause",
    "Network_IP_Interface_Create",
    "Network_IP_Interface_Modify",
    "Network_IP_Interface_Query",
    "Network_IP_Interface_Remove",
    "Profile_Lock_Query_DM",
    "SMAPI_Status_Capture",
    "System_Disk_IO_Query",
    "System_EQID_Query",
    "System_Information_Query",
    "System_Page_Utilization_Query",
    "System_Performance_Information_Query",
    "System_Service_Query",
    "System_Shutdown",
    "System_Spool_Utilization_Query",
    "Virtual_Network_Adapter_Query_Extended",
    "xCAT_Commands_IUO",
};


//TODO(jichenjc) need ignore this function call before zvm6.4
#define APIS_640_COUNT 1
static const char * APIS_640[APIS_640_COUNT] = {
    "Image_Console_Get",
};

    // Check for older releases and being passed an API that does not fit current release
    // API mismatch name is checked in if then else if following
    if (smapiLevel < 640){
        int foundit = 0;
        if (smapiLevel < 611) {
            for (j = 0; j < APIS_611_COUNT; j++ ){
                if (!strcmp(argV[1], APIS_611[j])) {
                    foundit = 1;
                    break;
                }
            }
        }
        if (smapiLevel < 620 && foundit ==0){
            for (j = 0; j < APIS_620_COUNT; j++ ){
                if (!strcmp(argV[1], APIS_620[j])) {
                    foundit = 1;
                    break;
                }
            }
        }
        if (smapiLevel < 630 && foundit ==0){
            for (j = 0; j < APIS_630_COUNT; j++ ){
                if (!strcmp(argV[1], APIS_630[j])) {
                    foundit = 1;
                    break;
                }
            }
        }
        if (foundit == 1){
            printf("ERROR: Unsupported API function name\n");
            rc = 1;
            TRACE_EXIT_FLOW(&vmapiContext, TRACEAREA_ZTHIN_GENERAL, rc);
            /* Clean up for memory context */
            FREE_CONTEXT_MEMORY(&vmapiContext);
            return rc;
        }
    }

    /*  Does the caller want a return code header line? If so set a global flag */
    for (j = 0; j < argC; j++) {
        if (!strcmp(argV[j], RETURN_CODE_HEADER_KEYWORD)) {
            vmapiContext.addRcHeader = 1;
            // Now we need to adjust the arguments to not have this special one
            saveCount = argC;
            argC--;
            if (saveCount == (j+1)) {
                // nothing to do, this was last argument.
            } else {
                for (k = j+1; k < saveCount; k++) {
                    argV[k-1] = argV[k];
                }
            }
            if (argC < 2) {
                displayHelpInfo(smapiLevel);
                rc =1;
                TRACE_EXIT_FLOW(&vmapiContext, TRACEAREA_ZTHIN_GENERAL, rc);
                /* Clean up for memory context */
                FREE_CONTEXT_MEMORY(&vmapiContext);
                return rc;
            }
        }
    }

    if (!strcmp(argV[1], "Asynchronous_Notification_Disable_DM")) {
        rc = asynchronousNotificationDisableDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Asynchronous_Notification_Enable_DM")) {
        rc = asynchronousNotificationEnableDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Asynchronous_Notification_Query_DM")) {
        rc = asynchronousNotificationQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Authorization_List_Add")) {
        rc = authorizationListAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Authorization_List_Query")) {
        rc = authorizationListQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Authorization_List_Remove")) {
        rc = authorizationListRemove(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Check_Authentication")) {
        rc = checkAuthentication(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Delete_ABEND_Dump")) {
        rc = deleteABENDDump(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Local_Tag_Define_DM")) {
        rc = directoryManagerLocalTagDefineDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Local_Tag_Delete_DM")) {
        rc = directoryManagerLocalTagDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Local_Tag_Query_DM")) {
        rc = directoryManagerLocalTagQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Local_Tag_Set_DM")) {
        rc = directoryManagerLocalTagSetDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Search_DM")) {
        rc = directoryManagerSearchDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Directory_Manager_Task_Cancel_DM")) {
        rc = directoryManagerTaskCancelDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Event_Stream_Add")) {
        rc = eventStreamAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Event_Subscribe")) {
        rc = eventSubscribe(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Event_Unsubscribe")) {
        rc = eventUnsubscribe(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Activate")) {
        rc = imageActivate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Active_Configuration_Query")) {
        rc = imageActiveConfigurationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Define")) {
        rc = imageCPUDefine(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Define_DM")) {
        rc = imageCPUDefineDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Delete")) {
        rc = imageCPUDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Delete_DM")) {
        rc = imageCPUDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Query")) {
        rc = imageCPUQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Query_DM")) {
        rc = imageCPUQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_CPU_Set_Maximum_DM")) {
        rc = imageCPUSetMaximumDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Console_Get")) {
        rc = imageConsoleGet(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Create_DM")) {
        rc = imageCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Deactivate")) {
        rc = imageDeactivate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Definition_Async_Updates")) {
        rc = imageDefinitionAsyncUpdates(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Definition_Create_DM")) {
        rc = imageDefinitionCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Definition_Delete_DM")) {
        rc = imageDefinitionDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Definition_Query_DM")) {
        rc = imageDefinitionQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Definition_Update_DM")) {
        rc = imageDefinitionUpdateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Delete_DM")) {
        rc = imageDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Device_Dedicate")) {
        rc = imageDeviceDedicate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Device_Dedicate_DM")) {
        rc = imageDeviceDedicateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Device_Reset")) {
        rc = imageDeviceReset(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Device_Undedicate")) {
        rc = imageDeviceUndedicate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Device_Undedicate_DM")) {
        rc = imageDeviceUndedicateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Copy")) {
        rc = imageDiskCopy(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Copy_DM")) {
        rc = imageDiskCopyDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Create")) {
        rc = imageDiskCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Create_DM")) {
        rc = imageDiskCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Delete")) {
        rc = imageDiskDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Delete_DM")) {
        rc = imageDiskDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Query")) {
        rc = imageDiskQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Share")) {
        rc = imageDiskShare(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Share_DM")) {
        rc = imageDiskShareDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Unshare")) {
        rc = imageDiskUnshare(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Disk_Unshare_DM")) {
        rc = imageDiskUnshareDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_IPL_Delete_DM")) {
        rc = imageIPLDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_IPL_Device_Query")) {
        rc = imageIPLDeviceQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_IPL_Query_DM")) {
        rc = imageIPLQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_IPL_Set_DM")) {
        rc = imageIPLSetDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Lock_DM")) {
        rc = imageLockDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Lock_Query_DM")) {
        rc = imageLockQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_MDISK_Link_Query")) {
        rc = imageMDISKLinkQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Name_Query_DM")) {
        rc = imageNameQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Password_Set_DM")) {
        rc = imagePasswordSetDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Pause")) {
        rc = imagePause(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Performance_Query")) {
        rc = imagePerformanceQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Query_Activate_Time")) {
        rc = imageQueryActivateTime(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Query_DM")) {
        rc = imageQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Recycle")) {
        rc = imageRecycle(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Replace_DM")) {
        rc = imageReplaceDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_SCSI_Characteristics_Define_DM")) {
        rc = imageSCSICharacteristicsDefineDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_SCSI_Characteristics_Query_DM")) {
        rc = imageSCSICharacteristicsQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Status_Query")) {
        rc = imageStatusQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Unlock_DM")) {
        rc = imageUnlockDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Add")) {
        rc = imageVolumeAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Delete")) {
        rc = imageVolumeDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Share")) {
        rc = imageVolumeShare(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Space_Define_DM")) {
        rc = imageVolumeSpaceDefineDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Space_Define_Extended_DM")) {
        rc = imageVolumeSpaceDefineExtendedDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Space_Query_DM")) {
        rc = imageVolumeSpaceQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Space_Query_Extended_DM")) {
        rc = imageVolumeSpaceQueryExtendedDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Image_Volume_Space_Remove_DM")) {
        rc = imageVolumeSpaceRemoveDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "IPaddr_Get")) {
        rc = ipAddrGet(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Metadata_Delete")) {
        rc = metadataDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Metadata_Get")) {
        rc = metadataGet(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Metadata_Set")) {
        rc = metadataSet(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Metadata_Space_Query")) {
        rc = metadataSpaceQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Name_List_Add")) {
        rc = nameListAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Name_List_Destroy")) {
        rc = nameListDestroy(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Name_List_Query")) {
        rc = nameListQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Name_List_Remove")) {
        rc = nameListRemove(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Network_IP_Interface_Create")) {
        rc = networkIpInterfaceCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Network_IP_Interface_Modify")) {
        rc = networkIpInterfaceModify(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Network_IP_Interface_Query")) {
        rc = networkIpInterfaceQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Network_IP_Interface_Remove")) {
        rc = networkIpInterfaceRemove(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Page_or_Spool_Volume_Add")) {
        rc = pageorSpoolVolumeAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Process_ABEND_Dump")) {
        rc = processABENDDump(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Create_DM")) {
        rc = profileCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Delete_DM")) {
        rc = profileDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Lock_DM")) {
        rc = profileLockDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Lock_Query_DM")) {
        rc = profileLockQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Query_DM")) {
        rc = profileQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Replace_DM")) {
        rc = profileReplaceDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Profile_Unlock_DM")) {
        rc = profileUnlockDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Prototype_Create_DM")) {
        rc = prototypeCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Prototype_Delete_DM")) {
        rc = prototypeDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Prototype_Name_Query_DM")) {
        rc = prototypeNameQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Prototype_Query_DM")) {
        rc = prototypeQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Prototype_Replace_DM")) {
        rc = prototypeReplaceDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Query_ABEND_Dump")) {
        rc = queryABENDDump(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Query_All_DM")) {
        rc = queryAllDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Query_API_Functional_Level")) {
        rc = queryAPIFunctionalLevel(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Query_Asynchronous_Operation_DM")) {
        rc = queryAsynchronousOperationDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Query_Directory_Manager_Level_DM")) {
        rc = queryDirectoryManagerLevelDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Response_Recovery")) {
        rc = responseRecovery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Access_Add_DM")) {
        rc = sharedMemoryAccessAddDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Access_Query_DM")) {
        rc = sharedMemoryAccessQueryDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Access_Remove_DM")) {
        rc = sharedMemoryAccessRemoveDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Create")) {
        rc = sharedMemoryCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Delete")) {
        rc = sharedMemoryDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Query")) {
        rc = sharedMemoryQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Shared_Memory_Replace")) {
        rc = sharedMemoryReplace(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "SMAPI_Status_Capture")) {
        rc = smapiStatusCapture(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "SSI_Query")) {
        rc = ssiQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Static_Image_Changes_Activate_DM")) {
        rc = staticImageChangesActivateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Static_Image_Changes_Deactivate_DM")) {
        rc = staticImageChangesDeactivateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Static_Image_Changes_Immediate_DM")) {
        rc = staticImageChangesImmediateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Config_Syntax_Check")) {
        rc = systemConfigSyntaxCheck(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Disk_Accessibility")) {
        rc = systemDiskAccessibility(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Disk_Add")) {
        rc = systemDiskAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Disk_IO_Query")) {
        rc = systemDiskIOQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Disk_Query")) {
        rc = systemDiskQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_EQID_Query")) {
        rc = systemEQIDQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_FCP_Free_Query")) {
        rc = systemFCPFreeQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Info_Query")) {
        rc = systemInfoQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Information_Query")) {
        rc = systemInformationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_IO_Query")) {
        rc = systemIOQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Page_Utilization_Query")) {
        rc = systemPageUtilizationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Performance_Info_Query")) {
        rc = systemPerformanceInfoQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Performance_Information_Query")) {
        rc = systemPerformanceInformationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Performance_Threshold_Disable")) {
        rc = systemPerformanceThresholdDisable(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Performance_Threshold_Enable")) {
        rc = systemPerformanceThresholdEnable(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_SCSI_Disk_Add")) {
        rc = systemSCSIDiskAdd(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_SCSI_Disk_Delete")) {
        rc = systemSCSIDiskDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_SCSI_Disk_Query")) {
        rc = systemSCSIDiskQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Service_Query")) {
        rc = systemServiceQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Shutdown")) {
        rc = systemShutdown(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_Spool_Utilization_Query")) {
        rc = systemSpoolUtilizationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "System_WWPN_Query")) {
        rc = systemWWPNQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Channel_Connection_Create")) {
        rc = virtualChannelConnectionCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Channel_Connection_Create_DM")) {
        rc = virtualChannelConnectionCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Channel_Connection_Delete")) {
        rc = virtualChannelConnectionDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Channel_Connection_Delete_DM")) {
        rc = virtualChannelConnectionDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Connect_LAN")) {
        rc = virtualNetworkAdapterConnectLAN(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Connect_LAN_DM")) {
        rc = virtualNetworkAdapterConnectLANDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Connect_Vswitch")) {
        rc = virtualNetworkAdapterConnectVswitch(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Connect_Vswitch_DM")) {
        rc = virtualNetworkAdapterConnectVswitchDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Connect_Vswitch_Extended")) {
        rc = virtualNetworkAdapterConnectVswitchExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Create")) {
        rc = virtualNetworkAdapterCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Create_DM")) {
        rc = virtualNetworkAdapterCreateDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Create_Extended")) {
        rc = virtualNetworkAdapterCreateExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Create_Extended_DM")) {
        rc = virtualNetworkAdapterCreateExtendedDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Delete")) {
        rc = virtualNetworkAdapterDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Delete_DM")) {
        rc = virtualNetworkAdapterDeleteDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Disconnect")) {
        rc = virtualNetworkAdapterDisconnect(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Disconnect_DM")) {
        rc = virtualNetworkAdapterDisconnectDM(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Query")) {
        rc = virtualNetworkAdapterQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Adapter_Query_Extended")) {
        rc = virtualNetworkAdapterQueryExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_LAN_Access")) {
        rc = virtualNetworkLANAccess(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_LAN_Access_Query")) {
        rc = virtualNetworkLANAccessQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_LAN_Create")) {
        rc = virtualNetworkLANCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_LAN_Delete")) {
        rc = virtualNetworkLANDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_LAN_Query")) {
        rc = virtualNetworkLANQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_OSA_Query")) {
        rc = virtualNetworkOSAQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Query_LAN")) {
        rc = virtualNetworkQueryLAN(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Query_OSA")) {
        rc = virtualNetworkQueryOSA(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_VLAN_Query_Stats")) {
        rc = virtualNetworkVLANQueryStats(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Create")) {
        rc = virtualNetworkVswitchCreate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Create_Extended")) {
        rc = virtualNetworkVswitchCreateExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Delete")) {
        rc = virtualNetworkVswitchDelete(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Delete_Extended")) {
        rc = virtualNetworkVswitchDeleteExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Query")) {
        rc = virtualNetworkVswitchQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Query_Extended")) {
        rc = virtualNetworkVswitchQueryExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Query_IUO_Stats")) {
        rc = virtualNetworkVswitchQueryIUOStats(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Query_Stats")) {
        rc = virtualNetworkVswitchQueryStats(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Set")) {
        rc = virtualNetworkVswitchSet(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "Virtual_Network_Vswitch_Set_Extended")) {
        rc = virtualNetworkVswitchSetExtended(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRELOCATE")) {
        rc = vmRelocate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRELOCATE_Image_Attributes")) {
        rc = vmRelocateImageAttributes(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRELOCATE_Modify")) {
        rc = vmRelocateModify(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRELOCATE_Status")) {
        rc = vmRelocateStatus(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRM_Configuration_Query")) {
        rc = vmrmConfigurationQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRM_Configuration_Update")) {
        rc = vmrmConfigurationUpdate(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "VMRM_Measurement_Query")) {
        rc = vmrmMeasurementQuery(argC, argV, &vmapiContext);
    } else if (!strcmp(argV[1], "xCAT_Commands_IUO")) {
        rc = xCATCommandsIUO(argC, argV, &vmapiContext);
    } else {
        printf("ERROR: Unsupported API function name\n");
        rc = 1;
    }

    TRACE_EXIT_FLOW(&vmapiContext, TRACEAREA_ZTHIN_GENERAL, rc);
    /* Clean up for memory context */
    FREE_CONTEXT_MEMORY(&vmapiContext);
    return rc;
}

