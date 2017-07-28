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

#include "smcliVMRM.h"
#include "wrapperutils.h"

int vmrmConfigurationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRM_Configuration_Query";
    int rc;
    int option;
    int i;
    int charNALength;
    char * charNABuffer;
    char * image = NULL;
    char * configFileName = NULL;
    char * configFileType = NULL;
    char * configDirName = NULL;
    vmApiVmrmConfigurationQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tctd";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:t:d:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'c':
                configFileName = optarg;
                break;

            case 't':
                configFileType = optarg;
                break;

            case 'd':
                configDirName = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  VMRM_Configuration_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRM_Configuration_Query [-T] image_name [-c] config_file_name\n"
                    "  [-t] config_file_type [-d] config_dir_name\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRM_Configuration_Query to query the contents of the VMRM configuration\n"
                    "  file.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -c    The name of the configuration file\n"
                    "    -t    The file type of the configuration file\n"
                    "    -d    The fully-qualified Shared File System (SFS) directory name\n"
                    "          where the configuration file is located\n");
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

    if (!image || !configFileName || !configFileType || !configDirName) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVMRM_Configuration_Query(vmapiContextP, "", 0, "",
            image, configFileName, configFileType, configDirName, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRM_Configuration_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("VMRM_Configuration_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
    	charNABuffer = output->configurationFile;
        charNALength = output->configurationFileLength;

        // Print spaces through }, except for %, the rest print %xx values
        for (i = 0; i < charNALength; i++) {
            if ((charNABuffer[i] < 0x1F) ||
                    (charNABuffer[i] == 0x25) ||
                    (charNABuffer[i] > 0x7D)) {
                printf("%%%02.2x",charNABuffer[i]);
            } else {
                printf("%c",charNABuffer[i]);
            }
        }
        printf("\n");
    }
    return rc;
}

int vmrmConfigurationUpdate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRM_Configuration_Update";
    int rc;
    int option;
    int syncheck = -1;
    char * image = NULL;
    char * configFileName = NULL;
    char * configFileType = NULL;
    char * configDirName = NULL;
    char * updateFile = NULL;
    vmApiVmrmConfigurationUpdateOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tctdsu";
    char tempStr[1];
    char strMsg[250];

    FILE * fp;
    int recordCount = 0;
    int recordWidth, maxRecordWidth;
    int c;
    char * ptr;


    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:c:t:d:s:u:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'c':
                configFileName = optarg;
                break;

            case 't':
                configFileType = optarg;
                break;

            case 'd':
                configDirName = optarg;
                break;

            case 's':
                syncheck = atoi(optarg);
                break;

            case 'u':
                updateFile = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  VMRM_Configuration_Update\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRM_Configuration_Update [-T] image_name [-c] config_file_name\n"
                    "  [-t] config_file_type [-d] config_dir_name\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRM_Configuration_Update to add, delete, and change VMRM configuration\n"
                    "  file statements.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n"
                    "    -c    The name of the configuration file\n"
                    "    -t    The file type of the configuration file\n"
                    "    -d    The fully-qualified Shared File System (SFS) directory name\n"
                    "          where the configuration file is located\n"
                    "    -s    Specify a 1 to choose the SYNCHECK option, meaning that only a syntax\n"
                    "          check of the configuration is done, without processing a configuration\n"
                    "          file update. Otherwise, specify a 0 to indicate that both a syntax\n"
                    "          check and a configuration file update should occur.\n"
                    "    -u    A new, complete VMRM configuration file to syntax-check or to replace\n"
                    "          the old file.\n");
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

    if (!image || !configFileName || !configFileType || !configDirName || (syncheck < 0) || !updateFile) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    // Open the user entry file
    fp = fopen(updateFile, "r");
    if (NULL == fp) {
        printAndLogProcessingErrors("VMRM_Configuration_Update", PROCESSING_ERROR, vmapiContextP, "", 0);
       printf("\nERROR: Failed to open file %s\n", updateFile);
       return 2;
    }

    // Count the number of lines and width of widest line
    recordWidth = 0;
    maxRecordWidth = 0;
    while ((c = fgetc(fp)) != EOF) {
        ++recordWidth;
        if (c == '\n') {
            recordCount++;
            if (recordWidth > maxRecordWidth)
               maxRecordWidth = recordWidth;
            recordWidth = 0;
        }
    }

    // Reset position to start of file
    rewind(fp);

    // Create update record array 
    vmApiUpdateRecord *record;
    if (recordCount > 0) {
        if (0 == (record = malloc(recordCount * sizeof(vmApiUpdateRecord)))){
            printAndLogProcessingErrors("VMRM_Configuration_Update", PROCESSING_ERROR, vmapiContextP, "", 0);
            return MEMORY_ERROR;
        }
    }

    // Create input buffer
    char *line[recordCount+1];
    if (maxRecordWidth > 0) {
        for (c = 0; c < recordCount+1; c++) {
           if (0 == (line[c] = malloc(maxRecordWidth+1))) {
              int i;
              for (i = 0; i < c; c++) 
                 free(line[i]);
              free(record);
              printAndLogProcessingErrors("VMRM_Configuration_Update", PROCESSING_ERROR, vmapiContextP, "", 0);
              return MEMORY_ERROR;
           }
        }
    }

    // Read in user entry from file
    c = 0;
    while (fgets(line[c], maxRecordWidth+1, fp) != NULL) {
       // Replace newline with null terminator
       ptr = strstr(line[c], "\n");
       if (ptr != NULL) 
          strncpy(ptr, "\0", 1);
       // If blank line, leave one blank charascter
       if (strlen(line[c]) == 0)
          strncpy(line[c]," \0",2);
       record[c].updateRecordLength = strlen(line[c])+1;
       record[c].updateRecord = line[c];
       c++;
    }

    // Close file
    fclose(fp);

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Updating VMRM configuration... ");

    rc = smVMRM_Configuration_Update(vmapiContextP, "", 0, "", image, configFileName, configFileType, configDirName,
            syncheck, recordCount, (vmApiUpdateRecord *) record, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRM_Configuration_Update", rc, vmapiContextP, strMsg, 0);
    } else {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("VMRM_Configuration_Update", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, strMsg);
    }
    // Print syntax error log if there is any
    if (output->logRecordCount > 0) {
        printf("Error log:\n");
        for(c = 0; c < output->logRecordCount; c++) {
           printf("  %.*s\n", output->logRecordInfoList[c].logRecordLength ,output->logRecordInfoList[c].logRecord);
        }
    }

    for(c = 0; c < recordCount; c++) 
       free(line[c]);
    free(record);

    return rc;
}

int vmrmMeasurementQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "VMRM_Measurement_Query";
    int rc;
    int option;
    char * image = NULL;
    vmApiVmrmMeasurementQueryOutput* output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "T";
    char tempStr[1];

    // Options that have arguments are followed by a : character
    while ((option = getopt(argC, argV, "T:h?")) != -1)
        switch (option) {
            case 'T':
                image = optarg;
                break;

            case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
                    "  VMRM_Measurement_Query\n\n"
                    "SYNOPSIS\n"
                    "  smcli VMRM_Measurement_Query [-T] image_name\n\n"
                    "DESCRIPTION\n"
                    "  Use VMRM_Measurement_Query to obtain current VMRM measurement values.\n\n"
                    "  The following options are required:\n"
                    "    -T    This must match an entry in the authorization file\n");
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

    if (!image) {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
        printf("ERROR: Missing required options\n");
        return 1;
    }

    rc = smVMRM_Measurement_Query(vmapiContextP, "", 0, "", image, &output);

    if (rc) {
        printAndLogProcessingErrors("VMRM_Measurement_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("VMRM_Measurement_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
        printf("File name: %s\n"
               "File time stamp: %s\n"
               "Query time stamp: %s\n", output->fileName, output->fileTimestamp, output->queryTimestamp);

        int i;
        printf("Workload:\n");
        for (i = 0; i < output->workloadCount; i++) {
            printf("  %s\n", output->workloadInfoList[i].workloadRecord);
        }
    }
    return rc;
}
