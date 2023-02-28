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
#ifndef _VMAPI_PARSER_ROUTINE_H
#define _VMAPI_PARSER_ROUTINE_H

#include <stddef.h>
#include <sys/types.h>
#include <netinet/in.h>
#include "smPublic.h"

#ifdef __cplusplus
extern "C" {
#endif

// Common information returned by SMAPI
typedef struct _commonOutputFields {
    int requestId;
    int returnCode;
    int reasonCode;
} commonOutputFields;

// Used to handle unknown number of zero terminated data returned by the SMAPI
typedef struct _vmApiCStringInfo {
    char * vmapiString;
} vmApiCStringInfo;

#define APITYPE_END_OF_TABLE 0
#define APITYPE_INT1         1
#define APITYPE_INT4         2
#define APITYPE_INT8         3
#define APITYPE_RC_INT4      4
#define APITYPE_RS_INT4      5

#define APITYPE_STRING_LEN          20
#define APITYPE_ARRAY_LEN           21
#define APITYPE_ARRAY_COUNT         22

// Some arrays have length fields as null term strings, so added the following
#define APITYPE_ARRAY_LEN_C_STR     23
#define APITYPE_ARRAY_STRUCT_COUNT  24
#define APITYPE_STRUCT_LEN          25
#define APITYPE_NOBUFFER_STRUCT_LEN 27
#define APITYPE_CHARBUF_LEN         28

// Added a CHARBUF_PTR with same value as LEN; since that is clearer in meaning
#define APITYPE_CHARBUF_PTR         28
#define APITYPE_CHARBUF_COUNT       29
#define APITYPE_C_STR_ARRAY_PTR     30
#define APITYPE_C_STR_ARRAY_COUNT   31
#define APITYPE_C_STR_STRUCT_LEN    32
#define APITYPE_C_STR_PTR           33
#define APITYPE_FIXED_STR_PTR       34
#define APITYPE_ARRAY_NULL_TERMINATED 35
#define APITYPE_ARRAY_NO_LENGTH     36

#define APITYPE_ERROR_BUFF_LEN      50
#define APITYPE_ERROR_BUFF_PTR      51

#define APITYPE_BASE_STRUCT_LEN     98

#define STRUCT_INDX_0    0
#define STRUCT_INDX_1    1
#define STRUCT_INDX_2    2
#define STRUCT_INDX_3    3
#define STRUCT_INDX_4    4
#define STRUCT_INDX_5    5
#define STRUCT_INDX_6    6
#define STRUCT_INDX_7    7
#define STRUCT_INDX_8    8
#define STRUCT_INDX_9    9
#define STRUCT_INDX_10   10

#define NEST_LEVEL_0  0
#define NEST_LEVEL_1  1
#define NEST_LEVEL_2  2
#define NEST_LEVEL_3  3
#define NEST_LEVEL_4  4
#define NEST_LEVEL_5  5
#define NEST_LEVEL_6  6
#define NEST_LEVEL_7  7
#define NEST_LEVEL_8  8
#define NEST_LEVEL_9  9
#define NEST_LEVEL_10 10


#define MAX_STRUCT_ARRAYS 10

#define COL_1_TYPE           0
#define COL_2_MINSIZE        1
#define COL_3_MAXSIZE        2
#define COL_4_STRUCT_INDEX   3
#define COL_5_NEST_LEVEL     4
#define COL_6_SIZE_OR_OFFSET 5

#define ERROR_OUTPUT_BUFFER_NOT_AVAILABLE 0
#define ERROR_OUTPUT_BUFFER_POSSIBLE_NO_LENGTH_FIELD 1
#define ERROR_OUTPUT_BUFFER_POSSIBLE_WITH_LENGTH_FIELD 2

enum tableParserModes {
    scan, populate
};

typedef int tableLayout[][6];

/* Input/output structure for use by smapiTableParser */
typedef struct _tableParserParms {
    char * smapiBufferCursor;
    char * smapiBufferEnd;
    int dataBufferSize;
    int byteCount;
    int outStringByteCount;
    int outStructCount[MAX_STRUCT_ARRAYS];
    int outStructSizes[MAX_STRUCT_ARRAYS];
    void * inStructAddrs[MAX_STRUCT_ARRAYS];
    char * inStringCursor;
} tableParserParms;

#define PARSER_ERROR_INVALID_TABLE       -4002
#define PARSER_ERROR_INVALID_STRING_SIZE -4003

#define swapEndianll(x) (((unsigned long long)(ntohl((int)((x << 32) >> 32))) << 32) | (unsigned int)ntohl(((int)(x >> 32))))

#define PUT_INT(_inInt_, _outBuf_)   \
    ({ int _int;                     \
        _int = htonl(_inInt_) ;      \
        memcpy(_outBuf_, &_int, 4);  \
        _outBuf_ += 4;               \
    } )

#define GET_INT(_outInt_, _inBuf_)   \
    ({ int _int;                     \
        memcpy(&_int, _inBuf_, 4);   \
        _outInt_ = ntohl(_int) ;     \
        _inBuf_ += 4;                \
    } )

#define PUT_64INT(_in64Int_, _outBuf_)       \
    ({ long long _64int;                     \
        int x;                               \
        x = ntohl(1);                        \
        if (x == 1) {                        \
            _64int = _in64Int_;              \
        } else {                             \
            _64int= swapEndianll(_in64Int_); \
        }                                    \
        memcpy(_outBuf_, &_64int, 8);        \
        _outBuf_ += 8;                       \
    } )

#define GET_64INT(_out64Int_, _inBuf_)       \
    ({ long long _64int;                     \
       int x;                                \
       memcpy(&_64int, _inBuf_, 8);          \
       x = ntohl(1);                         \
       if (x == 1) {                         \
          _out64Int_ = _64int;               \
       } else {                              \
          _out64Int_ = swapEndianll(_64int); \
       }                                     \
       _inBuf_ += 8;                         \
    })

int parseBufferWithTable(struct _vmApiInternalContext* vmapiContextP,
        enum tableParserModes mode, tableLayout table, tableParserParms *parms);

int getAndParseSmapiBuffer(struct _vmApiInternalContext* vmapiContextP,
        char * * inputBufferPointerPointer, int inputBufferSize,
        tableLayout parserTable, char * parserTableName, char * * outData);

#ifdef __cplusplus
}
#endif

#endif
