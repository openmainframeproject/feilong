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
#ifndef _SM_TRACE_H
#define _SM_TRACE_H

#include <stdio.h>
#include <syslog.h>
#include "smPublic.h"

// Trace levels are to be powers of 2 to allow combinations of tracing
#define TRACE_LEVELS_FILE "tracing.conf"
#define TRACE_LEVELS_FILE_DIRECTORY "/var/opt/zthin/"

// Make sure the level information matches the index in the TRACE_LEVELS and
// TRACE_FLAG_VALUES array below. These values must be powers of 2 in order
// to address individual bits within the 4-byte flag value.
#define TRACELEVEL_OFF        0
#define TRACELEVEL_ERROR      2
#define TRACELEVEL_FLOW       4
#define TRACELEVEL_PARAMETERS 8
#define TRACELEVEL_DETAILS    16
#define TRACELEVEL_BUFFER_OUT    256  // Unit test socket layer
#define TRACELEVEL_BUFFER_IN     512  // Unit test socket layer
#define TRACELEVEL_ALL        0x8FFFFFFF

// Keywords for the trace file
#define TRACE_LEVELS_COUNT    8
static const char * const TRACE_LEVELS[TRACE_LEVELS_COUNT] = {"off", "error",
    "flow", "parms", "details", "buffout", "buffin", "all"};

static const unsigned int TRACE_FLAG_VALUES[TRACE_LEVELS_COUNT] = {0, TRACELEVEL_ERROR,
    TRACELEVEL_FLOW, TRACELEVEL_PARAMETERS, TRACELEVEL_DETAILS, TRACELEVEL_BUFFER_OUT,
    TRACELEVEL_BUFFER_IN, TRACELEVEL_ALL};

// Trace areas index into trace array, must match the indexes of trace_keywords[]
#define TRACEAREA_BACKGROUND_DIRECTORY_NOTIFICATION_THREAD 0
#define TRACEAREA_ZTHIN_GENERAL  1
#define TRACEAREA_SOCKET 2
#define TRACEAREA_PARSER 3
#define TRACEAREA_BACKGROUND_VMEVENT_NOTIFICATION_THREAD 4
#define TRACEAREA_NAME_VALUE_PARSER 5
#define TRACEAREA_CACHE 6
#define TRACEAREA_SMAPI_ONLY 7
#define TRACEAREA_SMCLI 8

// Keywords for the trace areas
#define TRACE_AREAS_COUNT  9
static const char * const TRACE_KEYWORDS[TRACE_AREAS_COUNT] = {"directorychanges",
    "resourcelayer", "socket", "parser", "vmeventchanges", "namevalueparser",
    "cache", "smapionly", "smcli"};

typedef struct _smTrace {
    unsigned int traceFlags[TRACE_AREAS_COUNT];  // A separate trace int for each area
    int traceLock;
    int traceFileRead;                  // 0 = Trace file needs to be checked with readTraceFile
    unsigned int  traceOutputLocation;  // 0 = Syslog
    FILE * traceFilePointer;            // 0 = No file open
} smTrace;

/* Trace functions and constants for a line of data or a block of storage */
// These severity constants get re-mapped to syslog constants in LogLine
#define LOGLINE_DEBUG     'D'
#define LOGLINE_ERR       'E'
#define LOGLINE_INFO      'I'
#define LOGLINE_NOTICE    'N'
#define LOGLINE_WARNING   'W'
#define LOGLINE_EXCEPTION 'X'

/* This macro can be used to test for a trace type */
#define TRACE_START(_context_ , _tracearea_, _tracelevel_) \
    if ((_context_)->smTraceDetails->traceFileRead != 1) readTraceFile(_context_ );\
    if (((_context_)->smTraceDetails->traceFlags[_tracearea_])&_tracelevel_ ) \
{
#define TRACE_END }

/* This can be used to trace start/end with just a string */
#define TRACE_IT(_context_ , _tracearea_, _tracelevel_, _pattern_) \
    if ((_context_)->smTraceDetails->traceFileRead != 1) readTraceFile(_context_ );\
    if (((_context_)->smTraceDetails->traceFlags[_tracearea_])&_tracelevel_ ) \
{\
    char _lineout_[LINESIZE];\
    sprintf(_lineout_, _pattern_);\
    logLine(_context_, LOGLINE_DEBUG, _lineout_); \
}

/* This can be used to trace start/end using sprintf with 1 substitution */
#define TRACE_1SUB(_context_ , _tracearea_, _tracelevel_, _pattern_, _subval_) \
    if ((_context_)->smTraceDetails->traceFileRead != 1) readTraceFile(_context_ );\
    if (((_context_)->smTraceDetails->traceFlags[_tracearea_])&_tracelevel_ ) \
{\
    char _lineout_[LINESIZE];\
    sprintf(_lineout_, _pattern_, _subval_);\
    logLine(_context_, LOGLINE_DEBUG, _lineout_); \
}

/* This can be used to trace start/end using sprintf with 2 substitutions */
#define TRACE_2SUBS(_context_ , _tracearea_, _tracelevel_, _pattern_, _subval_, _subval2_) \
    if ((_context_)->smTraceDetails->traceFileRead != 1) readTraceFile(_context_ );\
    if (((_context_)->smTraceDetails->traceFlags[_tracearea_])&_tracelevel_ ) \
{\
    char _lineout_[LINESIZE];\
    sprintf(_lineout_, _pattern_, _subval_, _subval2_);\
    logLine(_context_, LOGLINE_DEBUG, _lineout_); \
}

/* This can be used to trace start/end using sprintf with 3 substitutions */
#define TRACE_3SUBS(_context_ , _tracearea_, _tracelevel_, _pattern_, _subval_, _subval2_, _subval3_) \
    if ((_context_)->smTraceDetails->traceFileRead != 1) readTraceFile(_context_ );\
    if (((_context_)->smTraceDetails->traceFlags[_tracearea_])&_tracelevel_ ) \
{\
    char _lineout_[LINESIZE];\
    sprintf(_lineout_, _pattern_, _subval_, _subval2_, _subval3_);\
    logLine(_context_, LOGLINE_DEBUG, _lineout_); \
}

#define TRACE_END_DEBUG(_context_, _linedata_) \
    readTraceFile(_context_);\
    logLine(_context_, LOGLINE_DEBUG,  _linedata_); \
}

/* This macro can be used to trace entry into a function */
#define TRACE_ENTRY_FLOW(_context_ , _tracearea_) \
TRACE_START(_context_, _tracearea_, TRACELEVEL_FLOW); \
    char _line_[LINESIZE]; \
    sprintf(_line_,  \
        "%s function ENTRY (at line %d in %s) \n",   \
        __func__, __LINE__, __FILE__);  \
    logLine(_context_ , LOGLINE_DEBUG, _line_);  \
}

/* This macro can be used to trace exit from a function */
#define TRACE_EXIT_FLOW(_context_ , _tracearea_ , _rc_) \
TRACE_START(_context_, _tracearea_, TRACELEVEL_FLOW); \
    char _line_[LINESIZE]; \
    sprintf(_line_,  \
        "%s function EXIT. RC: %d (at line %d in %s) \n",   \
        __func__, \
        _rc_, __LINE__, __FILE__); \
    logLine(_context_ , LOGLINE_DEBUG, _line_);  \
}

#endif
