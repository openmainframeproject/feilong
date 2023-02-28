/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
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
#include "smSocket.h"
#include "vmapiProfile.h"
#include "smapiTableParser.h"
#include "smPublic.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <errno.h>
#include <ctype.h>

#define PARSER_TABLE_NAME     Profile_Query_DM_Layout
#define OUTPUT_STRUCTURE_NAME vmApiProfileQueryDmOutput

/**
 * Profile_Query_DM SMAPI interface
 */
int smProfile_Query_DM(struct _vmApiInternalContext* vmapiContextP,
        char * userid, int passwordLength, char * password,
        char * targetIdentifier, vmApiProfileQueryDmOutput ** outData) {
    const char * const functionName = "Profile_Query_DM";
    tableParserParms parserParms;
    int tempSize;
    char * cursor;
    char * stringCursor;  // Used for outData string area pointer
    int arrayCount;
    int totalStringSize;
    int rc;
    int sockDesc;
    int requestId;

    // Cache variables
    char path[BUFLEN + 1];
    char cachePath[BUFLEN + 1];
    char profileID[10];
    FILE* cacheFileP = 0;
    char resultLine[256];
    int resultLineL = 0;
    const char* cP = 0;
    char * tempTargetIdentifier;
    char traceLine[LINESIZE + 100];
    vmApiProfileRecord *recordList;
    char *profileRecord;
    int profileRecordLen;
    int recordCount = 0;
    int dataReadFromCache = 0;
    int cacheFileFD;
    struct flock fl;

    int inputSize = 4 + 4 + strlen(functionName) + 4 + strlen(userid) + 4
            + passwordLength + 4 + strlen(targetIdentifier);
    char * inputP = 0;
    char * smapiOutputP = 0;
    int i;
    rc = 0;

    // Check if any cache data for this profile
    memset(cachePath, 0, sizeof(cachePath));
    vmbkendGetCachePath(vmapiContextP, cachePath);
    memset(profileID, 0, sizeof(profileID));

    // Force profile id name to lowercase and save it in profileID
    tempTargetIdentifier = targetIdentifier;
    i = 0;
    for (; *tempTargetIdentifier != '\0'; tempTargetIdentifier++) {
        profileID[i++] = tolower(*tempTargetIdentifier);
    }
    profileID[i--] = '\0';
    strcat(cachePath, profileID);
    strcat(cachePath, ".direct");

    if (cacheFileValid(vmapiContextP, cachePath)) {
        cacheFileP = fopen(cachePath, "r");
        if (cacheFileP) {
            cacheFileFD = fileno(cacheFileP);

            if (cacheFileFD != -1) {
                // Lock the file while reading, so no one else is writing into it
                fl.l_type = F_RDLCK;
                fl.l_whence = SEEK_SET;
                fl.l_start = 0;
                fl.l_len = 0;

                // Try to get the lock, if the file is in use by some other process, fetch the information from directory
                if (fcntl(cacheFileFD, F_SETLK, &fl) != -1) {
                    recordList = smMemoryGroupAlloc(vmapiContextP,
                            sizeof(vmApiProfileRecord));
                    *outData = smMemoryGroupAlloc(vmapiContextP,
                            sizeof(vmApiProfileQueryDmOutput));
                    if (recordList == 0 || *outData == 0) {
                        sprintf(traceLine, "*** Error trying to obtain memory for cache records.\n");
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, traceLine);
                        return MEMORY_ERROR;
                    }
                    while (fgets(resultLine, sizeof(resultLine), cacheFileP)) {
                        resultLineL = strlen(resultLine);
                        recordCount++;
                        if (resultLineL > 0) {
                            if (resultLine[resultLineL - 1] == '\n') {
                                --resultLineL;
                                resultLine[resultLineL] = 0;
                            }
                        }
                        profileRecordLen = resultLineL;
                        profileRecord = smMemoryGroupAlloc(vmapiContextP,
                                profileRecordLen);
                        if (profileRecord == 0) {
                            sprintf(traceLine, "*** Error trying to obtain memory for cache records.\n");
                            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, traceLine);
                            return MEMORY_ERROR;
                        }
                        strcpy(profileRecord, resultLine);
                        dataReadFromCache = 1;

                        if (recordCount > 1) {
                            recordList = smMemoryGroupRealloc(vmapiContextP,
                                    (void *) recordList, recordCount * sizeof(vmApiProfileRecord));
                            if (recordList == 0) {
                                sprintf(traceLine, "*** Error trying to obtain memory for cache records.\n");
                                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, traceLine);
                                return MEMORY_ERROR;
                            }
                        }
                        recordList[recordCount - 1].recordData = profileRecord;
                        recordList[recordCount - 1].profileRecordLength = profileRecordLen;
                    }

                    (*outData) -> profileRecordList = recordList;
                    (*outData) -> profileRecordCount = recordCount;
                    (*outData) -> common.returnCode = (*outData) -> common.reasonCode = 0;

                    // Unlock the file
                    fl.l_type = F_UNLCK;
                    fl.l_whence = SEEK_SET;
                    fl.l_start = 0;
                    fl.l_len = 0;

                    if (-1 == fcntl(cacheFileFD, F_SETLK, &fl)) {
                        sprintf(traceLine, "*** Error trying to unlock cache file read lock.\n");
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                                RcFunction, RsUnexpected, traceLine);
                        return PROCESSING_ERROR;
                    }
                }
                // Else if not able to get lock, continue with call
            }

            if (0 != fclose(cacheFileP)) {
                sprintf(traceLine, "*** Error trying to close profile cache file.\n");
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                        RcFunction, RsUnexpected, traceLine);
                return PROCESSING_ERROR;
            }

            // If cache data used return to caller
            if (dataReadFromCache) {
                return rc;
            }
        }
    } else if (remove(cachePath)) {
        // Cache file is invalid/missing/(out of date) remove it
        if (ENOENT != errno)  {  // If the error is anything but the file is not found
            sprintf(traceLine, "*** Error removing out of date profile cache file <%.*s> errno %d\n", LINESIZE, cachePath, errno);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
            return PROCESSING_ERROR;
        }
    }

    // Build SMAPI input parameter buffer
    if (0 == (inputP = malloc(inputSize))) {
        return MEMORY_ERROR;
    }
    cursor = inputP;
    PUT_INT(inputSize - 4, cursor);

    tempSize = strlen(functionName);
    PUT_INT(tempSize, cursor);
    memcpy(cursor, functionName, tempSize);
    cursor += tempSize;

    tempSize = strlen(userid);  // Userid 1..8 or 0..8 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, userid, tempSize);
        cursor += tempSize;
    }

    tempSize = passwordLength;  // Password 1..200 or 0..200 chars
    PUT_INT(tempSize, cursor);
    if (tempSize > 0) {
        memcpy(cursor, password, tempSize);
        cursor += tempSize;
    }

    tempSize = strlen(targetIdentifier);  // Target identifier 1..8 image name
    PUT_INT(tempSize, cursor);
    memcpy(cursor, targetIdentifier, tempSize);
    cursor += tempSize;

    // This routine will send SMAPI the input, delete the input storage
    // and call the table parser to set the output in outData
    rc = getAndParseSmapiBuffer(vmapiContextP, &inputP, inputSize,
            PARSER_TABLE_NAME,  // Integer table
            TO_STRING(PARSER_TABLE_NAME),  // String name of the table
            (char * *) outData);

    // Do the caching of the image.
    if (0 == rc) {
        if ((0 == (*outData)->common.returnCode) && (0 == (*outData)->common.reasonCode)) {
            // Write the cache file
            {
                cacheFileP = 0;
                createDirectories(cachePath);
                cacheFileP = fopen(cachePath, "w");
                if (NULL == cacheFileP) {
                    sprintf(traceLine, "***Error trying to open profile cache file (%s) for write. errno %d\n", profileID, errno);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
                    return PROCESSING_ERROR;
                }

                // If the file opened for write then add cache information
                if (cacheFileP != NULL) {
                    cacheFileFD = fileno(cacheFileP);
                    if (cacheFileFD != -1) {
                        // Lock the file while writing, so no one else is using it
                        fl.l_type = F_WRLCK;
                        fl.l_whence = SEEK_SET;
                        fl.l_start = 0;
                        fl.l_len = 0;
                        if (fcntl(cacheFileFD, F_SETLK, &fl) != -1) {
                            tempSize = (*outData)->profileRecordCount;
                            if (tempSize > 0) {
                                for (i = 0; i < tempSize; i++) {
                                    memset(resultLine, 0, sizeof(resultLine));
                                    memcpy(resultLine, (*outData)->profileRecordList[i].recordData,
                                            (*outData)->profileRecordList[i].profileRecordLength);
                                    resultLineL = strlen(resultLine);
                                    if (resultLineL > 71) {
                                        resultLine[71] = 0;
                                        resultLineL = 71;
                                    }
                                    strip(resultLine, 'T', ' ');
                                    cP = &resultLine[0];
                                    while (cP && (*cP == ' '))
                                        ++cP;

                                    // Ignore DIRMAINT control lines
                                    strcat(resultLine, "\n");
                                    fprintf(cacheFileP, "%s", resultLine);
                                    rc = fflush(cacheFileP);
                                    if (EOF == rc) {
                                        // Can't write to file, try to remove file
                                        if (0 != fclose(cacheFileP)) {
                                            sprintf(traceLine, "*** Error trying to close profile cache file.\n");
                                            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
                                            return PROCESSING_ERROR;
                                        }
                                        cacheFileP = 0;
                                        if (remove(cachePath)) {
                                            sprintf(traceLine, "*** Error removing profil cache file after write error  <%.*s> errno %d\n", LINESIZE, cachePath, errno);
                                            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
                                            return PROCESSING_ERROR;
                                        }
                                        return rc;  // Continue processing even if cache file was removed
                                    }
                                }
                            }

                            // Unlock the file
                            fl.l_type = F_UNLCK;
                            fl.l_whence = SEEK_SET;
                            fl.l_start = 0;
                            fl.l_len = 0;
                            if (-1 == fcntl(cacheFileFD, F_SETLK, &fl)) {
                                sprintf(traceLine, "*** Error trying to unlock profile cache file WRITE lock.\n");
                                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
                                return PROCESSING_ERROR;
                            }
                        }
                    }

                    if (0 != fclose(cacheFileP)) {
                        sprintf(traceLine, "*** Error trying to close profile cache file.\n");
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcFunction, RsUnexpected, traceLine);
                        return PROCESSING_ERROR;
                    }
                }
            }
        }
    }
    return rc;
}
