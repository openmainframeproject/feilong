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
#include <unistd.h>
#include <errno.h>
#include "smapiTableParser.h"
#include "smPublic.h"
#include "smSocket.h"
#include "smcliResponse.h"

// Internal function to handle embedded arrays in SMAPI output
static int handleCountedArrays(struct _vmApiInternalContext* vmapiContextP, enum tableParserModes mode, int * tableStartingIndex, tableLayout table, tableParserParms * parms, void * previousStruct);

static int handleNullTerminatedArrays(struct _vmApiInternalContext* vmapiContextP, enum tableParserModes mode, int * tableStartingIndex, tableLayout table, tableParserParms * parms, void * previousStruct);

static int handleArrays(struct _vmApiInternalContext* vmapiContextP, enum tableParserModes mode, int * tableStartingIndex, tableLayout table, tableParserParms * parms, void * previousStruct);

int parseBufferWithTable(struct _vmApiInternalContext* vmapiContextP, enum tableParserModes mode, tableLayout table, tableParserParms *parms) {
    int temp, dataType, i, ii, rc, iSize, reachedByteCount;
    int cStringArrayPtrOffset, cStringArrayPtrIndex;
    int cStringCounterFieldOffset, cStringCounterFieldIndex;
    int cStringStructIndex, cStringStructSize;
    int cStringFieldIndex, cStringFieldOffset, cStringCurrentStructCount;
    char line[LINESIZE];
    void * firstStruct;

    reachedByteCount = 0;  // Set this if we are at the end of the data

    // If this is a SCAN mode, clear out the output fields
    if (mode == scan) {
        parms->outStringByteCount = 0;
        for (i = 0; i < MAX_STRUCT_ARRAYS; i++) {
            parms->outStructCount[i] = 0;
            parms->outStructSizes[i] = 0;
        }
    }

    parms->byteCount = 0;
    firstStruct = 0;

    // First entry in the table must be the base structure size
    if (table[0][COL_1_TYPE] != APITYPE_BASE_STRUCT_LEN) {
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                "Parser found a problem in the internal table\n");
        return PARSER_ERROR_INVALID_TABLE;
    }

    // If this is scan mode, fill in the output array size for top level structure
    if (mode == scan) {
        parms->outStructSizes[0] = table[0][COL_6_SIZE_OR_OFFSET];
        parms->outStructCount[0] = 1;
    } else {
        firstStruct = parms->inStructAddrs[0];
        TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Base structure used at address %p\n", firstStruct);
    }

    for (i = 1; (table[i][COL_1_TYPE] != APITYPE_END_OF_TABLE) && (parms->byteCount < parms->dataBufferSize); i++) {
        dataType = table[i][COL_1_TYPE];
        switch (dataType) {
        case APITYPE_INT1:
            if (mode == populate) {
                memcpy((parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET]), parms->smapiBufferCursor, 1);
                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 1 found. Stored at %p(+%d)\n",
                              parms->inStructAddrs[0], table[i][COL_6_SIZE_OR_OFFSET]);
            }

            parms->smapiBufferCursor += 1;
            parms->byteCount += 1;
            break;

        case APITYPE_INT4:
        case APITYPE_RC_INT4:
        case APITYPE_RS_INT4:
            if (mode == populate) {
                GET_INT(*((int *) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])), parms->smapiBufferCursor);

                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 4 found value %d stored at %p(+%d)\n",
                              *((int *) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])), parms->inStructAddrs[0], table[i][COL_6_SIZE_OR_OFFSET]);

            } else {
                parms->smapiBufferCursor += 4;
            }

            parms->byteCount += 4;

            // If this is the new reason code field, we need to see if the return code is non zero.
            // If in scan mode, check if a error buffer is there, update the string byte count.
            // If populate mode, copy error buffer into string area and put pointer in to error buff fields.
            if (dataType == APITYPE_RS_INT4) {
                // Check for non zero return code and if data can return error buffer.
                if ((vmapiContextP->smapiReturnCode != 0) &&
                    //(vmapiContextP->smapiReturnCode != 592) &&
                    (vmapiContextP->smapiErrorBufferPossible > ERROR_OUTPUT_BUFFER_NOT_AVAILABLE)) {
                    // Is there some error data?
                    TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Is there any error buffer data?\n");
                    if (parms->byteCount < parms->dataBufferSize) {
                        temp = parms->dataBufferSize - parms->byteCount;
                        if (mode == scan) {
                            parms->outStringByteCount += temp;
                        } else {  // Populate
                            // Find the error buff count and pointer to set values (if found)
                            if (vmapiContextP->smapiErrorBufferPossible == ERROR_OUTPUT_BUFFER_POSSIBLE_WITH_LENGTH_FIELD) {
                                temp = temp -4;  // Subtract length field size
                                parms->smapiBufferCursor += 4;
                                parms->byteCount += 4;
                            }

                            for (ii = i; (table[ii][COL_1_TYPE] != APITYPE_END_OF_TABLE) ; ii++) {
                                 dataType = table[ii][COL_1_TYPE];
                                 switch (dataType) {
                                 case APITYPE_ERROR_BUFF_LEN:
                                     *((int*) (parms->inStructAddrs[0] + table[ii][COL_6_SIZE_OR_OFFSET])) = temp;
                                     TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Error buffer byte count: %d\n", temp);
                                     break;
                                 case APITYPE_ERROR_BUFF_PTR:
                                     // Copy the error data into the string buffer
                                     memcpy(parms->inStringCursor, parms->smapiBufferCursor, temp);
                                     *((char **) ((parms->inStructAddrs[0] + table[ii][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;
                                     TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Error buffer data stored at address %p\n", parms->inStringCursor);
                                     parms->inStringCursor += temp;
                                     break;
                                 default:
                                     break;
                                }
                            }
                        }

                        parms->byteCount += temp;  // Skip processing any more table entries
                    }
                }
            }
            break;

        // Error buffer should be handled earlier in return/reason code processing, so skip them now
        case APITYPE_ERROR_BUFF_LEN:
        case APITYPE_ERROR_BUFF_PTR:
            break;
        case APITYPE_INT8:
            if (mode == populate) {
                GET_64INT(*((int64_t*) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])), parms->smapiBufferCursor);

                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 8 found value %lld stored at %p(+%d)\n",
                              *((int64_t*) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])), parms->inStructAddrs[0], table[i][COL_6_SIZE_OR_OFFSET]);
            } else {
                parms->smapiBufferCursor += 8;
            }

            parms->byteCount += 8;
            break;

        case APITYPE_FIXED_STR_PTR:
            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found. Length %d\n",
                       table[i][COL_3_MAXSIZE]);
            parms->byteCount += table[i][COL_3_MAXSIZE];
            if (mode == scan) {
                // If scan update the string byte count
                parms->outStringByteCount += (table[i][COL_3_MAXSIZE] + 1);
            } else {
                // If populate then set the char * in struct; copy the string/charbuf into the buffer
                *((char **) ((parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;

                // Copy the string/charbuf into the string buffer and add zero terminator if a string
                memcpy(parms->inStringCursor, parms->smapiBufferCursor, table[i][COL_3_MAXSIZE]);
                parms->inStringCursor += table[i][COL_3_MAXSIZE];
                *(parms->inStringCursor) = '\0';
                parms->inStringCursor++;
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found: %s\n",
                             (parms->inStringCursor - table[i][COL_3_MAXSIZE] - 1));
            }

            parms->smapiBufferCursor += (table[i][COL_3_MAXSIZE]);
            break;

        case APITYPE_STRING_LEN:
        case APITYPE_CHARBUF_LEN:
        case APITYPE_C_STR_PTR:
            if (APITYPE_C_STR_PTR == dataType) {
                temp = strlen(parms->smapiBufferCursor);
                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "C string found of length %d <%s>\n",
                            temp, parms->smapiBufferCursor);
                parms->byteCount += (temp + 1);
            } else {
                GET_INT(temp, parms->smapiBufferCursor);
                parms->byteCount += 4;
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string/charbuf length found: %d\n", temp);
                parms->byteCount += temp;
            }

            // If the string size is incorrect, display error and return
            if (temp < table[i][COL_2_MINSIZE]) {
                // Check for less than min first
                sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n", temp,
                        (parms->smapiBufferCursor - 4), table[i][COL_2_MINSIZE], table[i][COL_3_MAXSIZE]);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                printf("%s\n", line);
                return PARSER_ERROR_INVALID_STRING_SIZE;
            }

            // If max is not -1, then check for max
            if (-1 != table[i][COL_3_MAXSIZE] && temp > table[i][COL_3_MAXSIZE]) {
                sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n", temp,
                        (parms->smapiBufferCursor - 4), table[i][COL_2_MINSIZE], table[i][COL_3_MAXSIZE]);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                printf("%s\n", line);
                return PARSER_ERROR_INVALID_STRING_SIZE;
            }

            // If scan update the string byte count
            if (mode == scan) {
                if (temp > 0) {
                    parms->outStringByteCount += (temp + 1);
                }

                if (APITYPE_CHARBUF_LEN == dataType) {
                    // Skip past the buf count row in table
                    i++;
                    (parms->outStringByteCount)--;  // Don't need null terminator for char buffer
                }
            } else {
                // If populate then set the char * in struct, copy the string/charbuf into the buffer
                if (temp > 0) {
                    *((char **) ((parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;

                    // If this ia a null terminated string just just strcpy, else use memcpy
                    if (APITYPE_C_STR_PTR == dataType) {
                        strcpy(parms->inStringCursor, parms->smapiBufferCursor);
                        parms->inStringCursor += temp + 1;
                    } else {
                        // Copy the string/charbuf into the string buffer and add zero terminator if a string
                        memcpy(parms->inStringCursor, parms->smapiBufferCursor, temp);
                        TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Mem copying string data from %p into %p for length %d\n",
                                    parms->smapiBufferCursor, parms->inStringCursor, temp);
                        parms->inStringCursor += temp;
                        if (APITYPE_STRING_LEN == dataType) {
                            *(parms->inStringCursor) = '\0';
                            parms->inStringCursor++;
                        } else {
                            // Char buffer, so no need to add null terminator, but must update count field
                            i++;
                            *((int*) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])) = temp;
                        }
                    }
                } else {
                    *((char**) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])) = NULL;
                    if (APITYPE_CHARBUF_LEN == dataType) {
                        // Set char buf count to 0
                        i++;
                        *((int*) (parms->inStructAddrs[0] + table[i][COL_6_SIZE_OR_OFFSET])) = 0;
                    }
                }
            }

            if (APITYPE_C_STR_PTR == dataType) {
                temp++;  // Add on a byte for zero terminator
            }

            parms->smapiBufferCursor += temp;
            break;

        case APITYPE_ARRAY_LEN:
        case APITYPE_ARRAY_LEN_C_STR:
        case APITYPE_ARRAY_NO_LENGTH:
            // Call a subroutine to handle this
            if (0 != (rc = handleArrays(vmapiContextP, mode, &i, table, parms, firstStruct)))
                return rc;

            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Finished handling an array in parseBufferwithTable. Buffer pointer %p\n",
                       parms->smapiBufferCursor);
            break;

        case APITYPE_ARRAY_COUNT:
            // Call a subroutine to handle this
            if (0 != (rc = handleCountedArrays(vmapiContextP, mode, &i, table, parms, firstStruct)))
                return rc;

            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Finished handling a counted array in parseBufferwithTable. Buffer pointer %p\n",
                       parms->smapiBufferCursor);
            break;

        case APITYPE_ARRAY_NULL_TERMINATED:
            // Call a subroutine to handle this
            if (0!= (rc = handleNullTerminatedArrays(vmapiContextP, mode, &i, table, parms, firstStruct)))
                return rc;

            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Finished handling a null terminated array in parseBufferwithTable. Buffer pointer %p\n",
                       parms->smapiBufferCursor);
            break;

            // If null terminated strings are in the base structure, we need to
            // find them all until we use up the buffer. They must be the last
            // type of data in the stream.

            // For scan mode we need to add up all the string lengths
            // (adding in a byte for the null terminator) until the buffer is empty.
            // The static table will have the APITYPE_C_STR_ARRAY_PTR, then
            // APITYPE_C_STR_ARRAY_COUNT, APITYPE_C_STR_STRUCT_LEN,
            // APITYPE_C_STR_PTR in that order.
        case APITYPE_C_STR_ARRAY_PTR:
            cStringArrayPtrOffset = table[i][COL_6_SIZE_OR_OFFSET];  // Get the offset where the array ptr will be stored
            cStringArrayPtrIndex = table[i][COL_4_STRUCT_INDEX];  // Get the index of this field(should be 0 for this level)
            i++;  // Get next table value, which must be the counter info
            if (APITYPE_C_STR_ARRAY_COUNT != table[i][COL_1_TYPE]) {
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
            }

            cStringCounterFieldOffset = table[i][COL_6_SIZE_OR_OFFSET];
            cStringCounterFieldIndex = table[i][COL_4_STRUCT_INDEX];

            i++;  // Get next table value, which must be the C array structure size info
            if (APITYPE_C_STR_STRUCT_LEN != table[i][COL_1_TYPE]) {
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                        "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
            }

            cStringStructSize = table[i][COL_6_SIZE_OR_OFFSET];
            cStringStructIndex = table[i][COL_4_STRUCT_INDEX];

            i++;  // Get next table value; which must be the char * offset in the structure
            if (APITYPE_C_STR_PTR != table[i][COL_1_TYPE]) {
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                        "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
            }

            cStringFieldIndex = table[i][COL_4_STRUCT_INDEX];
            cStringFieldOffset = table[i][COL_6_SIZE_OR_OFFSET];
            cStringCurrentStructCount = 0;  // Used in populate

            // Look through the rest of the buffer
            while (parms->byteCount < parms->dataBufferSize) {
                iSize = strlen(parms->smapiBufferCursor) + 1;

                // If this is scan, then increment the c string structure count,
                // add the output size of the string + byte for zero terminator, and
                // move buffer pointer past the string. Increment our count of data bytes
                // processed also.
                if (mode == scan) {
                    parms->outStringByteCount += iSize;
                    parms->smapiBufferCursor += iSize;
                    parms->outStructCount[cStringStructIndex]++;  // Structures hold the char *

                    // If the size of the char * structure has not been filled in, do that now
                    if (0 == parms->outStructSizes[cStringStructIndex]) {
                        parms->outStructSizes[cStringStructIndex] = cStringStructSize;
                    }
                } else {
                    // If populate, copy the string to the storage area,
                    // store the pointer to the string in the correct array structure,
                    // then move to next string.
                    // If this is the first string/structure, then set the structure pointer to to the
                    // starting address. The array notation will handle the rest of the addresses.
                    if (0 == cStringCurrentStructCount) {
                        *(char **) (parms->inStructAddrs[cStringArrayPtrIndex] + cStringArrayPtrOffset) =
                                parms->inStructAddrs[cStringStructIndex];

                        // Copy the struct count from the scan (input to this populate) into the count field
                        *((int *) (parms->inStructAddrs[cStringCounterFieldIndex] + cStringCounterFieldOffset)) =
                                parms->outStructCount[cStringStructIndex];
                    }

                    // Copy the string into the string buffer
                    strcpy(parms->inStringCursor, parms->smapiBufferCursor);

                    // Set the char * pointer in the c structure of char *'s
                    memcpy((parms->inStructAddrs[cStringStructIndex] + (cStringCurrentStructCount * cStringStructSize)
                            + cStringFieldOffset), &(parms->inStringCursor), sizeof(char *));

                    // Advance to next string storage location and structure counter
                    parms->inStringCursor += iSize;
                    parms->smapiBufferCursor += iSize;
                    cStringCurrentStructCount++;
                }

                parms->byteCount += iSize;
            }  // End while buffer has data

            break;

        case APITYPE_ARRAY_STRUCT_COUNT:
            // Should not get here, subroutine should be handling this
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                    "Parser found a problem in the internal table\n");
            return PARSER_ERROR_INVALID_TABLE;
            break;

        default:  // Error
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                    "Parser found a problem in the internal table\n");
            return PARSER_ERROR_INVALID_TABLE;
            break;
        }  // End switch on table type

        if (parms->byteCount >= parms->dataBufferSize) {
            reachedByteCount = 1;
            break;
        }
    }  // For loop until end of table
    return 0;
}

/**
 * Routine for doing all processing when an array is found.
 * Can be recursively called if nested arrays
 */
static int handleArrays(struct _vmApiInternalContext* vmapiContextP, enum tableParserModes mode, int * tableStartingIndex, tableLayout table, tableParserParms * parms, void * previousStruct) {
    // At our calling the table index should be at the arrayLen field, and next field should be
    // struct len details. STRUCT_COUNT and STRUCT_LEN
    int arrayByteMax, arrayByteCount, arrayPointerOffset, arrayPointerIndex, dataType;
    int dataBuffStructSize, outStructSize, structIndex, structByteCount;
    int tableIndex, tableMaxIndex, temp, rc, arrayNestLevel;
    int structCounterField = 0;
    int noBufferStructLen;  // Set to 1 if SMAPI array doesn't have an inner structure length
    char line[LINESIZE];
    char * startData;
    void * thisStruct;

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Array found. Starting table index is %d buffer pointer %p\n",
                *tableStartingIndex, parms->smapiBufferCursor);

    arrayByteCount = 0;
    tableMaxIndex = 0;  // Used to find end of table entries for this structure
    thisStruct = 0;  // Used for populate of structure (base address)

    // If the array length is traditional 4 byte field, then get it,
    // else it will be a c String length or no length (just use rest of buffer)
    if (APITYPE_ARRAY_LEN == table[*tableStartingIndex][COL_1_TYPE]) {
        GET_INT(arrayByteMax, parms->smapiBufferCursor);
    } else {
        if (APITYPE_ARRAY_LEN_C_STR == table[*tableStartingIndex][COL_1_TYPE]) {
            // This is a C string, get it and convert to integer
            temp = strlen(parms->smapiBufferCursor)+1;
            arrayByteMax = atoi(parms->smapiBufferCursor);
            parms->smapiBufferCursor += temp;
        } else {  // Must have no length, use the rest of the buffer
            arrayByteMax = parms->dataBufferSize - parms->byteCount;
        }

    }

    arrayPointerOffset = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
    arrayPointerIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    arrayNestLevel = table[*tableStartingIndex][COL_5_NEST_LEVEL];
    (*tableStartingIndex)++;  // Position at the struct len in this table (or struct count)

    // If the struct count field was specified, then make a note of that for populate step
    if (APITYPE_ARRAY_STRUCT_COUNT == table[*tableStartingIndex][COL_1_TYPE]) {
        if (mode == populate) {
            structCounterField = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
        } else {
            structCounterField = 0;
        }

        (*tableStartingIndex)++;  // Position at the struct length APITYPE_STRUCT_LEN
    }

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "SMAPI buffer array found: %d bytes (x'%x')\n", arrayByteMax, arrayByteMax);

    structIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    outStructSize = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Output struct size is %d \n", outStructSize);

    // Figure out where is the ending index of the structure. This will be used in case the
    // array is empty or the size of the structure is larger than we expect. The actual
    // structure could be bigger if the next release of SMAPI adds more fields at the end.
    tableMaxIndex = *tableStartingIndex;
    while (arrayNestLevel < table[tableMaxIndex + 1][COL_5_NEST_LEVEL]
            && APITYPE_END_OF_TABLE != table[tableMaxIndex + 1][COL_1_TYPE]) {
        tableMaxIndex++;
    }

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Structure's table max index is %d \n  Calling structure address: %p\n",
                tableMaxIndex, previousStruct);

    // Find each structure until we reach array max
    while (arrayByteCount < arrayByteMax) {
        TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Loop to scan buffer for structure data. Starting at %p\n", parms->smapiBufferCursor);
        noBufferStructLen = 0;
        tableIndex = *tableStartingIndex;  // Start at the field past the array in the table

        // Next table field should be the array structure size or if no nested inner structure
        // the NOBUFFER keyword
        if ((APITYPE_STRUCT_LEN != table[tableIndex][COL_1_TYPE])
                && (APITYPE_NOBUFFER_STRUCT_LEN != table[tableIndex][COL_1_TYPE])) {
            printf("table index %d column1 type: %d \n", tableIndex, table[tableIndex][COL_1_TYPE]);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime,
                    RsUnexpected, "Parser found a problem in the internal table\n");
            return PARSER_ERROR_INVALID_TABLE;
        }

        structByteCount = 0;

        GET_INT(dataBuffStructSize, parms->smapiBufferCursor);

        // If the SMAPI buffer does not contain a nested structure size, then set
        // the data pointer back to make the "implied" structure.
        if (APITYPE_NOBUFFER_STRUCT_LEN == table[tableIndex][COL_1_TYPE]) {
            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "There is no inner structure length, so this length %d is first item, back up to re-read it later.\n", dataBuffStructSize);
            parms->smapiBufferCursor -= 4;
            noBufferStructLen = 1;  // Set flag so that correct count at bottom of loop is done
            dataBuffStructSize = 0;
        }

        if (dataBuffStructSize == 0 && !noBufferStructLen) {
            TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Skipping empty structure\n");
            continue;  // Probably rare, but skip empty structures
        }

        if (mode == scan) {
            parms->outStructCount[structIndex]++;
            // If the size of the structure has not been filled in, do that now
            if (0 == parms->outStructSizes[structIndex]) {
                parms->outStructSizes[structIndex] = table[tableIndex][COL_6_SIZE_OR_OFFSET];
            }
        } else {
            // If populate and structCounterField specified, then fill it in
            thisStruct = parms->inStructAddrs[structIndex];

            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Struct at table index %d size %d carved out from %p\n",
                        structIndex, outStructSize, thisStruct);

            // Move storage pointer to next available
            parms->inStructAddrs[structIndex] = parms->inStructAddrs[structIndex] + outStructSize;

            // If this pointer structure is 0 then this is the first struct, so save address
            if (0 == *(char **) (previousStruct + arrayPointerOffset)) {
                *(char **) (previousStruct + arrayPointerOffset) = thisStruct;
                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Saving first struct %p of this type at %p\n",
                            thisStruct, (char **) (previousStruct + arrayPointerOffset));
            }

            if (structCounterField) {
                *((int *) (previousStruct + structCounterField)) = 1
                        + *((int *) (previousStruct + structCounterField));
                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Increasing counter at %p + offset %d to %d\n",
                            previousStruct, structCounterField, *((int *) (previousStruct + structCounterField)));
            }
        }

        TRACE_START(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS);
        if (noBufferStructLen == 1) {
            sprintf(line, "Table index %d implied array struct index %d first data item starts with (x'%x')\n",
                tableIndex, structIndex, dataBuffStructSize);
        } else {
            sprintf(line, "Table index %d array struct index %d data size %d(x'%x')\n",
                tableIndex, structIndex, dataBuffStructSize,dataBuffStructSize);
        }
        TRACE_END_DEBUG(vmapiContextP, line);

        tableIndex++;

        // Loop until reaching the end of the table or if an embedded structure size,
        // when the data has been all read.
        while ((noBufferStructLen == 0 && (structByteCount < dataBuffStructSize))
                || (noBufferStructLen && (tableIndex <= tableMaxIndex))) {
            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "noBufferStructLen %d structByteCount %d table index %d\n",
                        noBufferStructLen, structByteCount, tableIndex);

            // If we are at the end of this table, then adjust the byte count and leave
            // this loop. This would happen if there is more data than we expect. A newer
            // version of SMAPI may of added more fields at the end.
            if (tableIndex > tableMaxIndex) {
                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Reached the end of the table. Restarting from %d. Current table index %d data pointer %p\n",
                            *tableStartingIndex, tableIndex, parms->smapiBufferCursor);
                structByteCount = dataBuffStructSize;
                break;
            }

            dataType = table[tableIndex][0];
            switch (dataType) {
            case APITYPE_INT1:
                if (mode == populate) {
                    memcpy((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]),
                            parms->smapiBufferCursor, 1);
                    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 1 found. Stored at %p(+%d)\n",
                                thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);
                }

                parms->smapiBufferCursor += 1;
                structByteCount += 1;
                break;

            case APITYPE_INT4:
                TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 4 found.\n");
                if (mode == populate) {
                    GET_INT(*((int*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])), parms->smapiBufferCursor);
                    TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 4 found Value %d stored at %p(+%d)\n",
                                *((int *) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])), thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);
                } else {
                    parms->smapiBufferCursor += 4;
                }

                structByteCount += 4;
                break;

            case APITYPE_INT8:
                TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, " Int8 found.\n");

                if (mode == populate) {
                    GET_64INT(*((int64_t*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])),
                        parms->smapiBufferCursor);
                    TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 8 found Value %lld stored at %p(+%d)\n",
                                 *((int64_t *) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])), thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);

                } else {
                    parms->smapiBufferCursor += 8;
                }

                structByteCount += 8;
                break;

            case APITYPE_FIXED_STR_PTR:
                parms->byteCount += table[tableIndex][COL_3_MAXSIZE];
                structByteCount += table[tableIndex][COL_3_MAXSIZE];
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found. Length %d\n",
                           table[tableIndex][COL_3_MAXSIZE]);


                if (mode == scan) {
                    // If scan update the string byte count
                    parms->outStringByteCount += (table[tableIndex][COL_3_MAXSIZE] + 1);
                } else {
                    // If populate then set the char * in struct, copy the string/charbuf into the buffer
                    *((char **) ((thisStruct
                            + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) =
                            parms->inStringCursor;
                    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Updating char * pointer at %p with %p\n",
                                ((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))), parms->inStringCursor);

                    // Copy the string/charbuf into the string buffer and add zero terminator if a string
                    memcpy(parms->inStringCursor, parms->smapiBufferCursor, table[tableIndex][COL_3_MAXSIZE]);
                    parms->inStringCursor += table[tableIndex][COL_3_MAXSIZE];
                    *(parms->inStringCursor) = '\0';
                    parms->inStringCursor++;
                    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found: %s\n", (parms->inStringCursor - table[tableIndex][COL_3_MAXSIZE] - 1));
                }

                parms->smapiBufferCursor += (table[tableIndex][COL_3_MAXSIZE]);
                break;

            case APITYPE_STRING_LEN:
            case APITYPE_CHARBUF_LEN:
            case APITYPE_C_STR_PTR:
                if (APITYPE_C_STR_PTR == dataType) {
                    temp = strlen(parms->smapiBufferCursor);

                    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "C string found. Length %d\n", temp);
                } else {
                    GET_INT(temp, parms->smapiBufferCursor);
                    structByteCount += 4;

                    TRACE_START(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS);
                    if (dataType == APITYPE_CHARBUF_LEN) {
                        sprintf(line, "Charbuf with length %d found.\n", temp);
                    } else {
                        sprintf(line, "String with length %d found.\n", temp);
                    }
                    TRACE_END_DEBUG(vmapiContextP, line);
                }

                // If the string size is incorrect, display error and return
                if (temp < table[tableIndex][COL_2_MINSIZE]) {  // Check for less than min first
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n",
                            temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                            table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                    printf("%s\n", line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If max is not -1, then check for max
                if (-1 != table[tableIndex][COL_3_MAXSIZE] && temp > table[tableIndex][COL_3_MAXSIZE]) {
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n",
                            temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                            table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                    printf("%s\n", line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If scan, update the string byte count
                if (mode == scan) {
                    if (temp > 0) {
                        parms->outStringByteCount += (temp + 1);
                    }

                    if (dataType == APITYPE_CHARBUF_LEN) {
                        tableIndex++;  // Position at the char buf count in the table
                    }
                } else {  // If populate, then set the char * in struct and copy the string into the buffer
                    if (temp > 0) {
                        *((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;
                        TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Updating char * pointer at %p with %p\n",
                                    ((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))), parms->inStringCursor);

                        // If this is a null terminated string, just use strcpy else use memcpy
                        if (APITYPE_C_STR_PTR == dataType) {
                            strcpy(parms->inStringCursor, parms->smapiBufferCursor);
                            parms->inStringCursor += temp + 1;
                        } else {
                            // Copy the string into the string buffer and add zero terminator
                            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Mem copying string data from %p into %p for length %d\n",
                                        parms->smapiBufferCursor, parms->inStringCursor, temp);

                            memcpy(parms->inStringCursor, parms->smapiBufferCursor, temp);
                            parms->inStringCursor += temp;

                            if (APITYPE_STRING_LEN == dataType) {
                                *parms->inStringCursor = '\0';
                                parms->inStringCursor++;
                                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "String found value '%s' next avail struct pointer %p\n",
                                            *((char**) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])), parms->inStringCursor);
                            } else {
                                // Char buffer, so no need to add null terminator, but must update count field
                                tableIndex++;  // Position at the char buf count in the table
                                *((int*) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = temp;

                                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Charbuf count at table index %d updated\n", tableIndex);
                            }
                        }
                    } else {
                        *((char**) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = NULL;
                    }
                }

                if (APITYPE_C_STR_PTR == dataType) {
                    temp++;  // Add on a byte for zero terminator
                }

                parms->smapiBufferCursor += temp;
                structByteCount += temp;
                break;

            case APITYPE_ARRAY_LEN:
            case APITYPE_ARRAY_LEN_C_STR:
                startData = parms->smapiBufferCursor;
                if (dataType == APITYPE_ARRAY_LEN) {
                    structByteCount += 4;
                    startData += 4;
                }
                // Call a subroutine to handle this
                if (0 != (rc = handleArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);


                break;

            case APITYPE_ARRAY_COUNT:
                startData = parms->smapiBufferCursor + 4;
                structByteCount += 4;

                // Call a subroutine to handle this
                if (0 != (rc = handleCountedArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);


                break;

            case APITYPE_ARRAY_STRUCT_COUNT:  // Should not get here, subroutine should be handling this
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                        RcRuntime, RsUnexpected, "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;

            default:  // Error
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                        RcRuntime, RsUnexpected, "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;
            }

            tableIndex++;
        }

        if (noBufferStructLen) {
            arrayByteCount += structByteCount;
        } else {
            arrayByteCount += structByteCount + 4;  // Add in struct length field also
        }

        TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Current arrayByteCount subtotal is %d\n", arrayByteCount);
    }

    *tableStartingIndex = tableMaxIndex;

    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Table starting index on return is %d\n", *tableStartingIndex);
    return 0;
}

/**
 * Routine for doing all processing when an array has an element count rather
 * than array size is found. Can be recursively called if nested arrays.
 */
static int handleCountedArrays(struct _vmApiInternalContext* vmapiContextP,
        enum tableParserModes mode, int * tableStartingIndex, tableLayout table,
        tableParserParms *parms, void * previousStruct) {
    // At our calling the table index should be at the arrayLen field, and next field should be
    // struct length details.
    int arrayElementCount, arrayCountMax, arrayPointerOffset, arrayPointerIndex, dataType;
    int dataBuffStructSize, outStructSize, structIndex, structByteCount;
    int tableIndex, tableMaxIndex, temp, rc, arrayNestLevel;
    int structCounterField = 0;
    int noBufferStructLen;  // Set to 1 if SMAPI array doesn't have an inner structure length
    char line[LINESIZE];
    char * startData;
    void * thisStruct;

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Array found. Starting table index is %d buffer pointer %p\n",
                *tableStartingIndex, parms->smapiBufferCursor);

    arrayElementCount = 0;
    tableMaxIndex = 0;  // Used to find end of table entries for this structure
    thisStruct = 0;  // Used for populate of structure (base address)

    GET_INT(arrayCountMax, parms->smapiBufferCursor);

    // Number of elements in SMAPI array data
    arrayPointerOffset = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
    arrayPointerIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    arrayNestLevel = table[*tableStartingIndex][COL_5_NEST_LEVEL];
    (*tableStartingIndex)++;  // Position at the struct len in this table (or struct count)

    // If the struct count field was specified, then make a note of that for populate step
    if (APITYPE_ARRAY_STRUCT_COUNT == table[*tableStartingIndex][COL_1_TYPE]) {
        if (mode == populate) {
            structCounterField =
                    table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
        } else {
            structCounterField = 0;
        }

        (*tableStartingIndex)++;  // Position at the struct length APITYPE_STRUCT_LEN
    }

    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "SMAPI buffer array found: %d elements\n", arrayCountMax);


    structIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    outStructSize = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Output struct size is %d \n", outStructSize);

    // Figure out where is the ending index of the structure. This will be used
    // in case the array is empty or the size of the structure is larger than
    // we expect. The actual structure could be bigger if the next release of
    // SMAPI adds more fields at the end.
    tableMaxIndex = *tableStartingIndex;
    while (arrayNestLevel < table[tableMaxIndex + 1][COL_5_NEST_LEVEL]
            && APITYPE_END_OF_TABLE != table[tableMaxIndex + 1][COL_1_TYPE]) {
        tableMaxIndex++;
    }

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Structure's table max index is %d\n  Calling structure address: %p\n", tableMaxIndex, previousStruct);

    // Find each structure until we reach array max
    while (arrayElementCount < arrayCountMax) {
        TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Loop to scan buffer for structure data. Starting at %p\n", parms->smapiBufferCursor);
        noBufferStructLen = 0;
        tableIndex = *tableStartingIndex;  // Start at the field past the array in the table

        // Next table field should be the array structure size or if no nested inner structure
        // the NOBUFFER keyword
        if ((APITYPE_STRUCT_LEN != table[tableIndex][COL_1_TYPE])
                && (APITYPE_NOBUFFER_STRUCT_LEN != table[tableIndex][COL_1_TYPE])) {
            printf("Table index %d column1 type: %d \n", tableIndex, table[tableIndex][COL_1_TYPE]);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime,
                    RsUnexpected, "Parser found a problem in the internal table\n");
            return PARSER_ERROR_INVALID_TABLE;
        }
        structByteCount = 0;

        GET_INT(dataBuffStructSize, parms->smapiBufferCursor);
        // If the SMAPI buffer does not contain a nested structure size, then set
        // the data pointer back to make the "implied" structure.
        if (APITYPE_NOBUFFER_STRUCT_LEN == table[tableIndex][COL_1_TYPE]) {
            TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "There is no inner structure length, so this length %d is first item, back up to re-read it later.\n",
                       dataBuffStructSize);
            parms->smapiBufferCursor -= 4;
            noBufferStructLen = 1;  // Set flag so that correct count at bottom of loop is done
        }

        if (dataBuffStructSize == 0) {
            TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Skipping empty structure\n");
            continue;  // Probably rare, but skip empty structures
        }

        if (mode == scan) {
            parms->outStructCount[structIndex]++;

            // If the size of the structure has not been filled in, do that now
            if (0 == parms->outStructSizes[structIndex]) {
                parms->outStructSizes[structIndex] = table[tableIndex][COL_6_SIZE_OR_OFFSET];
            }
        } else {
            // If populate and structCounterField specified, then fill it in
            thisStruct = parms->inStructAddrs[structIndex];

            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Struct at table index %d size %d carved out from %p\n",
                        structIndex, outStructSize, thisStruct);

            // Move storage pointer to next available
            parms->inStructAddrs[structIndex] = parms->inStructAddrs[structIndex] + outStructSize;

            // If this pointer structure is 0 then this is the first struct, so save address
            if (0 == *(char **) (previousStruct + arrayPointerOffset)) {
                *(char **) (previousStruct + arrayPointerOffset) = thisStruct;
                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Saving first struct %p of this type at %p\n", thisStruct,
                            (char **) (previousStruct + arrayPointerOffset));
            }

            if (structCounterField) {
                *((int *) (previousStruct + structCounterField)) = 1
                        + *((int *) (previousStruct + structCounterField));
                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Increasing counter at %p + offset %d to %d\n",
                            previousStruct, structCounterField, *((int *) (previousStruct + structCounterField)));
            }
        }

        TRACE_START(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS);
        if (noBufferStructLen == 1) {
            sprintf(line, "Table index %d implied array struct index %d first data item size %d(x'%x')\n",
                tableIndex, structIndex, dataBuffStructSize, dataBuffStructSize);
        } else {
            sprintf(line, "Table index %d array struct index %d data size %d(x' %x')\n",
                tableIndex, structIndex, dataBuffStructSize, dataBuffStructSize);
        }
        TRACE_END_DEBUG(vmapiContextP, line);

        tableIndex++;

        // Loop until reaching the end of the table or if an embedded structure
        // size, when the data has been all read.
        while ((noBufferStructLen == 0 && (structByteCount < dataBuffStructSize))
                || (noBufferStructLen && (tableIndex <= tableMaxIndex))) {
            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "noBufferStructLen %d structByteCount %d table index %d\n",
                        noBufferStructLen, structByteCount, tableIndex);

            // If we are at the end of this table, then adjust the byte count
            // and leave this loop. This would happen if there is more data than
            // we expect. (A newer version of SMAPI may of added more fields at
            // the end.
            if (tableIndex > tableMaxIndex) {
                TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Reached the end of the table. Restarting from %d. Current table index %d data pointer %p\n",
                            *tableStartingIndex, tableIndex, parms->smapiBufferCursor);
                structByteCount = dataBuffStructSize;
                break;
            }

            dataType = table[tableIndex][0];
            switch (dataType) {
            case APITYPE_INT1:
                if (mode == populate) {
                    memcpy((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]),
                            parms->smapiBufferCursor, 1);
                    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 1 found. Stored at %p(+%d)\n",
                                thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);
                }

                parms->smapiBufferCursor += 1;
                structByteCount += 1;
                break;

            case APITYPE_INT4:
                TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int4 found.\n");
                if (mode == populate) {
                    GET_INT(*((int*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])),
                            parms->smapiBufferCursor);
                    TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 4 found Value %d stored at %p(+%d)\n",
                                *((int *) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])), thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);
                } else {
                    parms->smapiBufferCursor += 4;
                }

                structByteCount += 4;
                break;

            case APITYPE_INT8:
                TRACE_IT(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int8 found.\n");
                if (mode == populate) {
                    GET_64INT(*((int64_t*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])), parms->smapiBufferCursor);
                    TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Int 8 found Value %lld stored at %p(+%d) \n",
                                *((int64_t *) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])), thisStruct, table[tableIndex][COL_6_SIZE_OR_OFFSET]);

                } else {
                    parms->smapiBufferCursor += 8;
                }

                structByteCount += 8;
                break;

            case APITYPE_FIXED_STR_PTR:
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found. Length %d\n",
                           table[tableIndex][COL_3_MAXSIZE]);
                parms->byteCount += (table[tableIndex][COL_3_MAXSIZE]);
                structByteCount += table[tableIndex][COL_3_MAXSIZE];
                if (mode == scan) {
                    // If scan update the string byte count
                    parms->outStringByteCount += (table[tableIndex][COL_3_MAXSIZE] + 1);
                } else {
                    // If populate then set the char * in struct; copy the string/charbuf into the buffer
                    *((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;
                    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Updating char * pointer at %p with %p\n",
                                ((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))), parms->inStringCursor);

                    // Copy the string/charbuf into the string buffer and add zero terminator if a string
                    memcpy(parms->inStringCursor, parms->smapiBufferCursor,
                            table[tableIndex][COL_3_MAXSIZE]);
                    parms->inStringCursor += table[tableIndex][COL_3_MAXSIZE];
                    *(parms->inStringCursor) = '\0';
                    parms->inStringCursor++;
                    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string found: %s\n", (parms->inStringCursor - table[tableIndex][COL_3_MAXSIZE] - 1));
                }

                parms->smapiBufferCursor += (table[tableIndex][COL_3_MAXSIZE]);
                break;

            case APITYPE_STRING_LEN:
            case APITYPE_CHARBUF_LEN:
            case APITYPE_C_STR_PTR:
                if (APITYPE_C_STR_PTR == dataType) {
                    temp = strlen(parms->smapiBufferCursor);
                    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "C string found. Length %d\n", temp);
                } else {
                    GET_INT(temp, parms->smapiBufferCursor);
                    structByteCount += 4;

                    TRACE_START(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS);
                    if (dataType == APITYPE_CHARBUF_LEN) {
                        sprintf(line, " Charbuf with length %d found.\n", temp);
                    } else {
                        sprintf(line, " String with length %d found.\n", temp);
                    }
                    TRACE_END_DEBUG(vmapiContextP, line);
                }

                // If the string size is incorrect, display error and return
                if (temp < table[tableIndex][COL_2_MINSIZE]) {  // Check for less than min first
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n",
                            temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                            table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                    printf("%s\n", line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If max is not -1, then check for max
                if (-1 != table[tableIndex][COL_3_MAXSIZE]
                        && temp > table[tableIndex][COL_3_MAXSIZE]) {
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d \n",
                            temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                            table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                    printf("%s\n", line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If scan update the string byte count
                if (mode == scan) {
                    if (temp > 0) {
                        parms->outStringByteCount += (temp + 1);
                    }

                    if (dataType == APITYPE_CHARBUF_LEN) {
                        tableIndex++;  // Position at the char buf count in the table
                    }
                } else {  // If populate then set the char * in struct, copy the string into the buffer
                    if (temp > 0) {
                        *((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;
                        TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "++ Updating char * pointer at %p with %p\n",
                                    ((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))), parms->inStringCursor);

                        // If this ia a null terminated string just just strcpy, else use memcpy
                        if (APITYPE_C_STR_PTR == dataType) {
                            strcpy(parms->inStringCursor, parms->smapiBufferCursor);
                            parms->inStringCursor += temp + 1;
                        } else {
                            // Copy the string into the string buffer and add zero terminator
                            TRACE_3SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Mem copying string data from %p into %p for length %d\n",
                                        parms->smapiBufferCursor, parms->inStringCursor, temp);
                            memcpy(parms->inStringCursor, parms->smapiBufferCursor, temp);
                            parms->inStringCursor += temp;

                            if (APITYPE_STRING_LEN == dataType) {
                                *parms->inStringCursor = '\0';
                                parms->inStringCursor++;

                                TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "String found Value '%s' next avail struct pointer %p\n",
                                            *((char**) (thisStruct + +table[tableIndex][COL_6_SIZE_OR_OFFSET])), parms->inStringCursor);
                            } else  {
                                // Char buffer, so no need to add null terminator, but must update count field
                                tableIndex++;  // Position at the char buf count in the table
                                *((int*) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = temp;
                                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Charbuf count at table index %d updated\n", tableIndex);
                            }
                        }
                    } else {
                        *((char**) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = NULL;
                    }
                }

                if (APITYPE_C_STR_PTR == dataType) {
                    temp++;  // Add on a byte for zero terminator
                }

                parms->smapiBufferCursor += temp;
                structByteCount += temp;
                break;

            case APITYPE_ARRAY_LEN:
                startData = parms->smapiBufferCursor + 4;
                structByteCount += 4;
                // Call a subroutine to handle this
                if (0 != (rc = handleArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);

                break;

            case APITYPE_ARRAY_COUNT:
                startData = parms->smapiBufferCursor + 4;
                structByteCount += 4;
                // Call a subroutine to handle this
                if (0 != (rc = handleCountedArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);

                break;

            case APITYPE_ARRAY_STRUCT_COUNT:  // Should not get here, subroutine should be handling this
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                        RcRuntime, RsUnexpected, "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;

            default:  // Error
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                        RcRuntime, RsUnexpected, "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;
            }
            tableIndex++;
        }

        arrayElementCount++;
        TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Current arrayElementCount subtotal is %d\n", arrayElementCount);
    }
    *tableStartingIndex = tableMaxIndex;

    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Table starting Index on return is %d\n", *tableStartingIndex);
    return 0;
}

/**
 * Routine for doing all processing for null terminated arrays (no length or count is specified).
 * That means this is the last output in SMAPI return buffer. Currently, no nested arrays are allowed 
 * for this, just simple fields.
 *
 * At our calling, the table index should be at the APITYPE_ARRAY_NULL_TERMINATED field.
 * This field has the location to store the array pointer.
 *
 * The table field after that should be APITYPE_ARRAY_STRUCT_COUNT, where we set the count
 * of output C structures.
 *
 * The next field should be APITYPE_STRUCT_LEN, which has the size of the output c structure.
 */
static int handleNullTerminatedArrays(struct _vmApiInternalContext* vmapiContextP,
        enum tableParserModes mode, int * tableStartingIndex, tableLayout table,
        tableParserParms *parms, void * previousStruct) {
    int arrayElementCount, arrayCountMax, arrayPointerOffset, arrayPointerIndex, dataType;
    int dataBuffStructSize, outStructSize, structIndex, structByteCount;
    int tableIndex, tableMaxIndex, temp, rc, arrayNestLevel;
    int structCounterField = 0;
    int i;
    int noBufferStructLen;  // Set to 1 if SMAPI array doesn't have an inner structure length
    char line[LINESIZE];
    void * thisStruct;
    char * startData;
    char * tempStr;

    TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "** Null terminated array found. Starting table index is %d buffer pointer %p\n",
                *tableStartingIndex, parms->smapiBufferCursor);

    arrayElementCount = 0;
    tableMaxIndex = 0;  // Used to find end of table entries for this structure
    thisStruct = 0;  // Used for populate of structure (base address)
    arrayCountMax = 0;

    // Scan to count how many null terminated arrays there are.
    tempStr = parms->smapiBufferCursor;
    temp = parms->byteCount;
    while (temp< parms->dataBufferSize) {
        i = strlen(tempStr);
        i += 1;  // Add in null terminator
        tempStr += i;
        arrayCountMax += 1;
        temp =+ i;
    }

    arrayPointerOffset = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
    arrayPointerIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    arrayNestLevel = table[*tableStartingIndex][COL_5_NEST_LEVEL];
    (*tableStartingIndex)++;  // Position at the struct count

    // Fill in the struct count
    if (APITYPE_ARRAY_STRUCT_COUNT == table[*tableStartingIndex][COL_1_TYPE]) {
        if (mode == populate) {
            structCounterField = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];
            *((int *) (previousStruct + structCounterField)) = arrayCountMax;
        } else {
            structCounterField = 0;
        }
        (*tableStartingIndex)++;  // Position at the struct length APITYPE_STRUCT_LEN
    }

    structIndex = table[*tableStartingIndex][COL_4_STRUCT_INDEX];
    outStructSize = table[*tableStartingIndex][COL_6_SIZE_OR_OFFSET];

    // Figure out where is the ending index of the structure. This will be used in case the
    // array is empty or the size of the structure is larger than we expect. The actual
    // structure could be bigger if the next release of SMAPI adds more fields at the end.
    tableMaxIndex = *tableStartingIndex;
    while (arrayNestLevel < table[tableMaxIndex + 1][COL_5_NEST_LEVEL]
            && APITYPE_END_OF_TABLE != table[tableMaxIndex + 1][COL_1_TYPE]) {
        tableMaxIndex++;
    }

    // Find each structure until we reach array max
    while (arrayElementCount < arrayCountMax) {
        noBufferStructLen = 0;
        tableIndex = *tableStartingIndex;  // Start at the field past the array in the table

        // Next table field should be the structure items
        structByteCount = 0;
        dataBuffStructSize = strlen(parms->smapiBufferCursor) + 1;  // Add in null term

        if (dataBuffStructSize == 0) {
            continue;  // Probably rare, but skip empty structures
        }

        if (mode == scan) {
            parms->outStructCount[structIndex]++;
            // If the size of the structure has not been filled in, do that now
            if (0 == parms->outStructSizes[structIndex]) {
                parms->outStructSizes[structIndex] =
                        table[tableIndex][COL_6_SIZE_OR_OFFSET];
            }
        } else {
            // If populate and structCounterField specified, then fill it in
            thisStruct = parms->inStructAddrs[structIndex];

            // Move storage pointer to next available
            parms->inStructAddrs[structIndex] =
                    parms->inStructAddrs[structIndex] + outStructSize;

            // If this pointer structure is 0 then this is the first struct, so save address
            if (0 == *(char **) (previousStruct + arrayPointerOffset)) {
                *(char **) (previousStruct + arrayPointerOffset) = thisStruct;
            }
        }

        tableIndex++;

        // Loop until reaching the end of the table or if an embedded structure size,
        // when the data has been all read.
        while ((noBufferStructLen == 0 && (structByteCount < dataBuffStructSize))
                || (noBufferStructLen && (tableIndex <= tableMaxIndex))) {
                // If we are at the end of this table, then adjust the byte count and leave
                // this loop. This would happen if there is more data than we expect. (A newer
                // version of SMAPI may of added more fields at the end.
            if (tableIndex > tableMaxIndex) {
                structByteCount = dataBuffStructSize;
                break;
            }

            dataType = table[tableIndex][0];
            switch (dataType) {
            case APITYPE_INT1:
                if (mode == populate) {
                    memcpy((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]),
                        parms->smapiBufferCursor, 1);
                }

                parms->smapiBufferCursor += 1;
                structByteCount += 1;
                break;

            case APITYPE_INT4:
                if (mode == populate) {
                    GET_INT(*((int*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])),
                            parms->smapiBufferCursor);
                } else {
                    parms->smapiBufferCursor += 4;
                }

                structByteCount += 4;
                break;

            case APITYPE_INT8:
                if (mode == populate) {
                    GET_64INT(*((int64_t*)(thisStruct+ table[tableIndex][COL_6_SIZE_OR_OFFSET])),
                            parms->smapiBufferCursor);

                } else {
                    parms->smapiBufferCursor += 8;
                }

                structByteCount += 8;
                break;

            case APITYPE_FIXED_STR_PTR:
                parms->byteCount += (table[tableIndex][COL_3_MAXSIZE]);
                structByteCount += table[tableIndex][COL_3_MAXSIZE];
                if (mode == scan) {
                    // If scan update the string byte count
                    parms->outStringByteCount +=
                            (table[tableIndex][COL_3_MAXSIZE] + 1);
                } else {
                    // If populate then set the char * in struct, copy the string/charbuf into the buffer
                    *((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) =
                            parms->inStringCursor;

                    // Copy the string/charbuf into the string buffer and add zero terminator if a string
                    memcpy(parms->inStringCursor, parms->smapiBufferCursor, table[tableIndex][COL_3_MAXSIZE]);
                    parms->inStringCursor += table[tableIndex][COL_3_MAXSIZE];
                    *(parms->inStringCursor) = '\0';
                    parms->inStringCursor++;
                }

                parms->smapiBufferCursor += (table[tableIndex][COL_3_MAXSIZE]);
                break;

            case APITYPE_STRING_LEN:
            case APITYPE_CHARBUF_LEN:
            case APITYPE_C_STR_PTR:
                if (APITYPE_C_STR_PTR == dataType) {
                    temp = strlen(parms->smapiBufferCursor);
                } else {
                    GET_INT(temp, parms->smapiBufferCursor);
                    structByteCount += 4;
                    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Fixed string/charbuf length found: %d\n", temp);
                }

                // If the string size is incorrect, display error and return.
                if (temp < table[tableIndex][COL_2_MINSIZE]) {  // Check for less than minimum first
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d\n",
                            temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                            table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__),
                            RcRuntime, RsUnexpected, line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If max is not -1, then check for max
                if (-1 != table[tableIndex][COL_3_MAXSIZE] && temp > table[tableIndex][COL_3_MAXSIZE]) {
                    sprintf(line, "String size found: %d (@ %p), not in correct range %d-%d\n",
                        temp, (parms->smapiBufferCursor - 4), table[tableIndex][COL_2_MINSIZE],
                        table[tableIndex][COL_3_MAXSIZE]);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                    printf("%s\n", line);
                    return PARSER_ERROR_INVALID_STRING_SIZE;
                }

                // If scan update the string byte count
                if (mode == scan) {
                    if (temp > 0) {
                        parms->outStringByteCount += (temp + 1);
                    }

                    if (dataType == APITYPE_CHARBUF_LEN) {
                        tableIndex++;  // Position at the char buf count in the table
                    }
                } else {  // If populate then set the char * in struct, copy the string into the buffer
                    if (temp > 0) {
                        *((char **) ((thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET]))) = parms->inStringCursor;

                        // If this is a null terminated string just just strcpy, else use memcpy
                        if (APITYPE_C_STR_PTR == dataType) {
                            strcpy(parms->inStringCursor, parms->smapiBufferCursor);
                            parms->inStringCursor += temp + 1;
                        } else {
                            // Copy the string into the string buffer and add zero terminator
                            memcpy(parms->inStringCursor, parms->smapiBufferCursor, temp);
                            parms->inStringCursor += temp;

                            if (APITYPE_STRING_LEN == dataType) {
                                *parms->inStringCursor = '\0';
                                parms->inStringCursor++;
                            } else {
                                // Char buffer, so no need to add null terminator, but must update count field
                                tableIndex++;  // Position at the char buf count in the table
                                *((int*) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = temp;
                            }
                        }
                    } else {
                        *((char**) (thisStruct + table[tableIndex][COL_6_SIZE_OR_OFFSET])) = NULL;
                    }
                }

                if (APITYPE_C_STR_PTR == dataType) {
                    temp++;  // Add on a byte for zero terminator
                }
                parms->smapiBufferCursor += temp;
                structByteCount += temp;
                break;

            case APITYPE_ARRAY_LEN:
                startData = parms->smapiBufferCursor + 4;
                structByteCount += 4;
                // Call a subroutine to handle this
                if (0 != (rc = handleArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);

                break;

            case APITYPE_ARRAY_COUNT:
                startData = parms->smapiBufferCursor + 4;
                structByteCount += 4;
                // Call a subroutine to handle this
                if (0 != (rc = handleCountedArrays(vmapiContextP, mode, &tableIndex, table, parms, thisStruct)))
                    return rc;
                structByteCount += (parms->smapiBufferCursor - startData);
                TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Handled array bytes: %d\n", structByteCount);

                break;

            case APITYPE_ARRAY_STRUCT_COUNT:  // Should not get here, subroutine should be handling this
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                        "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;

            default:  // Error
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected,
                        "Parser found a problem in the internal table\n");
                return PARSER_ERROR_INVALID_TABLE;
                break;
            }

            tableIndex++;
        }

        arrayElementCount++;
        parms->byteCount+= dataBuffStructSize;
    }

    *tableStartingIndex = tableMaxIndex;
    return 0;
}

/**
 * This helper function will handle connecting and reading of the SMAPI buffer data.
 */
int getAndParseSmapiBuffer(struct _vmApiInternalContext* vmapiContextP, char * * inputPp,
        int inputSize, tableLayout parserTable, char * parserTableName, char * * outData) {
    int sockDesc;
    tableParserParms parserParms;
    int requestId;
    int tempSize;
    int * pReturnCode;
    int * pReasonCode;
    int rc, i, j, k, jk;
    int saverc;
    char line[BUFLEN];
    char * smapiOutputP = 0;
    rc = 0;
    const int SLEEP_TIMES[SEND_RETRY_LIMIT] = { 0, 8, 16, 16, 15, 15, 15, 15 };

    readTraceFile(vmapiContextP);
    TRACE_ENTRY_FLOW(vmapiContextP, TRACEAREA_ZTHIN_GENERAL);

    TRACE_1SUB(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Table being parsed: <%s>\n", parserTableName);

    // Create a retry in case the socket loses connection
    // Cover creating the socket, sending SMAPI the API, and also getting the requestID
    for (k = 0;; k++) {
        if (k > SEND_RETRY_LIMIT) {
            sprintf(line, "Socket create/send/receive requestId failed after %d retries\n", SEND_RETRY_LIMIT);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
            FREE_MEMORY(*inputPp);
            return saverc;
        } else
        {
            // clean up old socket on retry
            if (k > 0) {
                rc = close(sockDesc);
                if (0 != rc) {
                    sprintf(line, "Close of old socket create/send/receive requestId got errno: %d Continuing anyway.\n", errno);
                    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                }
            }
        }
        if (SLEEP_TIMES[k] > 0) {
            sleep(SLEEP_TIMES[k]);
        }
        if (k > 0) {
            // Display the api buffer table name in message
            sprintf(line, "Retry %n of sending SMAPI API for table %s\n", k, parserTableName);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
        }

        // Initialize our socket, no need to retry this, usually not a problem
        if (0 != (rc = smSocketInitialize(vmapiContextP, &sockDesc))) {
            FREE_MEMORY(*inputPp);
            return rc;
        }

        TRACE_1SUB(vmapiContextP, TRACEAREA_SMAPI_ONLY, TRACELEVEL_DETAILS, "Socket write starting for <%s>\n", parserTableName);

        saverc = 0;

        // Retry the send if the error detected is ok to retry
        for (j = 0;; j++) {
            if (0 != (rc = smSocketWrite(vmapiContextP, sockDesc, *inputPp, inputSize))) {
                if (rc == SOCKET_TIMEOUT_ERROR || rc == SOCKET_NOT_CONNECTED_ERROR || rc == SOCKET_CONNECT_REFUSED_ERROR) {
                    if (j < SEND_RETRY_LIMIT) {
                        // Delay for a while to give SMAPI some time to restart
                        if (SLEEP_TIMES[j] > 0) {
                            sleep(SLEEP_TIMES[j]);
                        }
                        continue;
                    }
                    // Change the internal return code to general write one
                    rc = SOCKET_WRITE_ERROR;
                }

                FREE_MEMORY(*inputPp);
                TRACE_2SUBS(vmapiContextP, TRACEAREA_SMAPI_ONLY, TRACELEVEL_DETAILS, "Socket write for <%s> did not complete after %d retries\n",
                            parserTableName, SEND_RETRY_LIMIT);
                return rc;
            }
            break;
        }


        // Get the request Id
        if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char*) &requestId, 4))) {
            if (rc == SOCKET_TIMEOUT_ERROR || rc == SOCKET_NOT_CONNECTED_ERROR || rc == SOCKET_CONNECT_REFUSED_ERROR) {
                // redrive entire request
                saverc = rc;
                continue;
            }
            sprintf(line, "Socket %d receive of the requestId failed after %n retries\n", sockDesc, SEND_RETRY_LIMIT);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
            FREE_MEMORY(*inputPp);
            return rc;
        }

        // Read in the output length and retry if an error. Retry a few times if needed
        for (jk=0;; jk++) {
            if (jk > SEND_RETRY_LIMIT) {
                sprintf(line, "SMAPI response_recovery retry limit of %d exceeded\n", SEND_RETRY_LIMIT);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                FREE_MEMORY(*inputPp);
                return saverc;
            } else {
                if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, (char *)&tempSize, 4))) {
                    saverc = rc;
                    // Try SMAPI recovery for SOCKET_TIMEOUT_ERROR; SOCKET_NOT_CONNECTED_ERROR;
                    if (rc == SOCKET_TIMEOUT_ERROR || rc == SOCKET_NOT_CONNECTED_ERROR  || rc == SOCKET_CONNECT_REFUSED_ERROR) {

                        // clean up old socket on retry
                        rc = close(sockDesc);
                        if (0 != rc) {
                            sprintf(line, "Close of old socket got errno: %d Continuing anyway.\n", errno);
                            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        }

                        // Sleep to give SMAPI a chance to recover
                        sleep(ResponseRecoveryDelay);

                        // Initialize our socket
                        if (0 != (rc = smSocketInitialize(vmapiContextP, &sockDesc))) {
                            return rc;
                        }

                        sprintf(line, "Calling SMAPI response_recovery for requestId %d attempt %d\n", requestId,jk+1);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        rc =  tryRecoveryUsingRequestId(vmapiContextP, sockDesc, requestId, &tempSize);
                        saverc = rc;
                        if (rc == SOCKET_TIMEOUT_ERROR || rc == SOCKET_NOT_CONNECTED_ERROR  || rc == SOCKET_CONNECT_REFUSED_ERROR ||
                            rc == SOCKET_RETRY_SMAPI_POSSIBLE) {
                            if (rc == SOCKET_RETRY_SMAPI_POSSIBLE) {
                                break; // break to outer loop to retry
                            }
                            // retry response recovery
                            continue;
                        }
                        if (0 != saverc) {
                            sprintf(line, "Failed on call to SMAPI response_recovery for requestId %d Error rc:%d\n", requestId, saverc);
                            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                            FREE_MEMORY(*inputPp);
                            return saverc;
                        } else {
                            // all good, lets see if any data
                            goto allgood;
                        }

                    } else {
                        sprintf(line, "Socket %d receive of the buffer length for requestId %d failed. Error rc:%d\n", sockDesc, requestId, saverc);
                        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcIucv, RsUnexpected, line);
                        FREE_MEMORY(*inputPp);
                        return saverc;
                    }
                } else {
                    // All good
                    goto allgood;
                }
            }
        } // response recovery retry loop
    } // main retry loop
    allgood:
    FREE_MEMORY(*inputPp);
    tempSize = ntohl(tempSize);

    // Read in the rest of the output buffer
    if (tempSize >= (3 * 4)) {  // Must have at least  3 more ints
        if (0 == (smapiOutputP = malloc(tempSize))) {
            sprintf(line, "Insufficiant memory (request=%d bytes)\n", tempSize);
            errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, line);
            return MEMORY_ERROR;
        }

        if (0 != (rc = smSocketRead(vmapiContextP, sockDesc, smapiOutputP, tempSize))) {
            FREE_MEMORY(smapiOutputP);
            return rc;
        }

        if (0 != (rc = smSocketTerminate(vmapiContextP, sockDesc))) {
            FREE_MEMORY(smapiOutputP);
            return rc;
        }

        pReturnCode = (int *) (smapiOutputP + 4);
        pReasonCode = (int *) (smapiOutputP + 8);
        vmapiContextP->smapiReturnCode = *pReturnCode;
        vmapiContextP->smapiReasonCode = *pReasonCode;

        TRACE_2SUBS(vmapiContextP, TRACEAREA_SMAPI_ONLY, TRACELEVEL_DETAILS, "SMAPI return code %d reason code %d\n", *pReturnCode, *pReasonCode);

        // Scan the SMAPI output data to get sizes of structures and strings.
        // A non zero return code indicates errors.
        parserParms.smapiBufferCursor = smapiOutputP;
        parserParms.dataBufferSize = tempSize;
        parserParms.smapiBufferEnd = smapiOutputP + tempSize;

        rc = parseBufferWithTable(vmapiContextP, scan, parserTable, &parserParms);
        if (rc != 0) {
            // If we have an error because of invalid string size, dump out the
            // buffer to help with diagnosis. Limit the dump to 5000 characters
            if (rc == PARSER_ERROR_INVALID_STRING_SIZE) {
                if (tempSize > 5000) {
                    dumpArea(vmapiContextP, smapiOutputP, 5000);
                } else {
                    dumpArea(vmapiContextP, smapiOutputP, tempSize);
                }
            }

            FREE_MEMORY(smapiOutputP);
            return rc;
        }

        // We can add up all the storage or get each structure independently, do independent for now
        for (i = 0; i < MAX_STRUCT_ARRAYS; i++) {
            if (parserParms.outStructSizes[i] == 0 || parserParms.outStructCount[i] == 0)
                continue;

            parserParms.inStructAddrs[i] = smMemoryGroupAlloc(vmapiContextP,
                    parserParms.outStructSizes[i] * parserParms.outStructCount[i]);
            TRACE_START(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS);
            sprintf(line, "Obtaining struct storage[%d] size %d count %d starting at %p\n",
                    i, parserParms.outStructSizes[i], parserParms.outStructCount[i], parserParms.inStructAddrs[i]);
            TRACE_END_DEBUG(vmapiContextP, line);

            if (parserParms.inStructAddrs[i] == 0) {
                FREE_MEMORY(smapiOutputP);
                sprintf(line, "Insufficiant memory (request=%d bytes)\n",
                        parserParms.outStructSizes[i] * parserParms.outStructCount[i]);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, line);
                return MEMORY_ERROR;
            }
        }

        // If any string data, just get one chunk of storage for that
        if (parserParms.outStringByteCount > 0) {
            parserParms.inStringCursor = smMemoryGroupAlloc(vmapiContextP, parserParms.outStringByteCount);
            TRACE_2SUBS(vmapiContextP, TRACEAREA_PARSER, TRACELEVEL_DETAILS, "Obtaining string storage size %d starting at %p\n",
                        parserParms.outStringByteCount, parserParms.inStringCursor);

            if (parserParms.inStringCursor == 0) {
                FREE_MEMORY(smapiOutputP);
                sprintf(line, "Insufficiant memory (request=%d bytes)\n", parserParms.outStringByteCount);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsNoMemory, line);
                return MEMORY_ERROR;
            }
        }

        // Set the output pointer to the level 0 structure's storage
        *outData = parserParms.inStructAddrs[0];
        parserParms.smapiBufferCursor = smapiOutputP;  // Reset the output cursor pointer

        rc = parseBufferWithTable(vmapiContextP, populate, parserTable, &parserParms);
        if (rc != 0) {
            FREE_MEMORY(smapiOutputP);
            return rc;
        }
    } else {
        sprintf(line, "SMAPI response data too small. Bytes returned:%d\n", tempSize);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        return INVALID_DATA;  // Not enough data returned
    }

    FREE_MEMORY(smapiOutputP);

    return 0;
}
/**
 * This helper function will try to call SMAPI recovery to get
 * the buffer data using the requestId. It will just read first
 * 16 bytes to see if any output length, requestid, retcode,
 * reasoncode for the recovery is returned.
 */
int tryRecoveryUsingRequestId(struct _vmApiInternalContext* vmapiContextP, int sockId, int requestId, int * inputSize) {
    char smapiAPI[46];
    int rc, saverc;
    int j, tempSize;
    char * cursor;
    char * inputP = 0;
    char recoveryCodes[12]; // this api has req id, rc, rs
    char * rCodesP;
    int recoveryRQid = 0;
    int recoveryRC = 0;
    int recoveryRS = 0;
    int recoverySize = 0;
    char line[LINESIZE];

    // Start at top of smapi API buffer to send
    inputP = smapiAPI;
    cursor = inputP;
    rCodesP = recoveryCodes;

    tempSize = 42;  //Buffer length after this field
    PUT_INT(tempSize, cursor);

    tempSize = 17; // Length of API
    PUT_INT(tempSize, cursor);

    memcpy(cursor, "Response_Recovery", 17);
    cursor += 17;

    tempSize = 0;
    PUT_INT(tempSize, cursor); // userid length 0
    PUT_INT(tempSize, cursor); // password length 0

    tempSize = 5; // Length of MAINT
    PUT_INT(tempSize, cursor); // Maint length 5
    memcpy(cursor, "MAINT", 5);
    cursor += 5;

    PUT_INT(requestId, cursor);

    rc = 0;

    if (0 != (rc = smSocketWrite(vmapiContextP, sockId, smapiAPI, 46))) {
        saverc = rc;
        sprintf(line, "tryRecoveryUsingRequestId failed in socket write call. Return code: %d \n", saverc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        return saverc;
    }

    // Read in the request ID for response recovery
    if (0 != (rc = smSocketRead(vmapiContextP, sockId, (char *) &recoveryRQid, 4))) {
        saverc = rc;
        sprintf(line, "tryRecoveryUsingRequestId failed in socket read call for requestID. Return code: %d \n", saverc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        return saverc;
    }

    // Read in the total output length
    if (0 != (rc = smSocketRead(vmapiContextP, sockId, (char *) &recoverySize, 4))) {
        saverc = rc;
        sprintf(line, "tryRecoveryUsingRequestId failed in socket read call for recovery response length. Return code: %d \n", saverc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        return saverc;
    }
    // Read in the reqid, rc, and rs for this API
    if (0 != (rc = smSocketRead(vmapiContextP, sockId, (char *) rCodesP, 12))) {
        saverc = rc;
        sprintf(line, "tryRecoveryUsingRequestId failed in socket read call for request ID, rc, rs. Return code: %d \n", saverc);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        return saverc;
    }
    recoveryRC = *((int *) (rCodesP + 4));
    recoveryRS = *((int *) (rCodesP + 8));
    if (0 != recoveryRC) {
        sprintf(line, "tryRecoveryUsingRequestId error from SMAPI Response_Recovery. Error rc:%d rs:%d\n", recoveryRC, recoveryRS);
        errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
        if (4 == recoveryRC) {
            if (recoveryRS == 4) {
                sprintf(line, "SMAPI Response_Recovery says retry possible, lets retry. rc:%d rs:%d\n", recoveryRC, recoveryRS);
                errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);
                return SOCKET_RETRY_SMAPI_POSSIBLE;
            }
            return SOCKET_RETRY_NO_DATA;
        }
        return recoveryRC;
    }
    // Adjust the buffer size to be 12 bytes less because of previous read for return codes, etc
    *inputSize = recoverySize - 12;
    sprintf(line, "tryRecoveryUsingRequestId data buffer size from previous API is bytes:%d\n", *inputSize);
    errorLog(vmapiContextP, __func__, TO_STRING(__LINE__), RcRuntime, RsUnexpected, line);

    return 0;
}
