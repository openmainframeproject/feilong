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
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#define TRUE                    1
#define PAGE_SIZE            4096
#define TRACK_SIZE          65536
#define TRACKS_PER_CYLINDER    15

// The first 16 bytes in each track are a label declaring the cylinder and
// track indices.
#define TRACK_BEGINNING_OVERHEAD 16

// Data structure at the beginning of each record in an ECKD track.
// Structure begins 16 bytes into the track.
typedef struct RecordMetadata {
  uint16_t cylinderIndex;     // Cylinder index, starts at 0
  uint16_t trackIndex;        // Track index within cylinder, starts at 0
  uint8_t  recordIndex;       // Record index within track, First valid
                              //   First record is 16 byte header.  Non-header
                              //   records begin at 1.
  uint8_t  keyCount;          // Count of keys in track. 0 = no keys,
                              // 'FF' = End of track
  uint16_t dataCount;         // Number of bytes of data in record
} RecordMetadata;

/*
  CiKaDa Stream Format:
        1 byte - Number of records in the next track
        Array  - Key counts.  2 dimension array which represents key
                 count information for each record in the track.
                 One row per unique key in a series of key counts.  If
                 the same key count is used multiple times consecutively
                 then only one row has the key count and the number of
                 times it was consecutively specified.
                 First element - (1 byte) Number of consecutive records
                 that have this key count.
                 Second element - (1 byte) key count (i.e. # of keys).
        Array  - Data counts.  2 dimension array of data information.
                 One row per unique data length in a series of data
                 lengths.  Each record has a data length but if
                 consecutive records have the same data length then we
                 only keep one row with the data length and count the
                 number of consecutive times this count is used.
                 First element - (1 byte) Number of consecutive records
                 that have this length data.
                 Second element - (2 bytes) Data length value.
        Array  - Key and data values for each record.  Unlike the
                 previous key and data count arrays we have one row
                 for each record.
                 First element - (x bytes) keys.  The number of keys
                 depends upon the related key count in the key count
                 array.
                 Second element - (x bytes) data.  The amount of data
                 depends upon the related data length in the data count
                 array.

  ECKD Cylinder Layout:
        16 byte header - Track header
                 2 bytes - Cylinder Index
                 2 bytes - Track Index
                12 bytes - Miscellaneous usage.
        For each record in the track, we have a record header as shown in
        the RecordMetadata structure followed by the keys and the
        data for the record.  The key length and data length is specified
        in the RecordMetadata structure.
*/

int main (int argumentCount, char* argumentValues[]);
