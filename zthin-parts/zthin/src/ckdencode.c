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
/****************************************************************************
 External Name: ckdencode

 Function: Encodes the tracks from an ECKD disk into CiKaDa data and
           write it to STDOUT.  The expected use is to create an image file
           that represents the disk.

 @param $1: Linux device node representing the disk to be read

 @return 0 Encode was successful
         1 Incorrect number of operands
         2 Unable to open the disk for reading
         3 Unable to allocate 64k of memory on a page buffer for use
           as a work buffer
         4 Unexpected read error.
         5 Unable to write to STDOUT.
         6 Error encountered closing the disk.
*****************************************************************************/
#include "cikada.h"

// The first 16 bytes in each track are a label declaring the cylinder and
// track indices.
#define TRACK_BEGINNING_OVERHEAD 16

char    keyBuffer[512] = {0};
char    dataBuffer[65536] = {0};
uint8_t keyCountRunCount;
uint8_t keyCountRunLength[256];
uint8_t keyCountRunValue[256];
uint8_t dataCountRunCount;
uint8_t dataCountRunLength[256];
uint16_t dataCountRunValue[256];

//***************************************************************************
// Function: Main section of the program.
//***************************************************************************
int main (int argumentCount, char* argumentValues[]) {
  RecordMetadata recordMetadata;
  int     dasdDescriptor = -1;
  int      returnCode = 0;
  int      exitCode   = 0;
  uint8_t  recordsInTrack;
  //uint16_t cylinderIndex, trackIndex;
  uint32_t trackCount = 0;
  void*    trackBuffer = NULL;
  void*    trackBufferCursor;

  //**************************************************************************
  // Verify input and display help if parms are missing.
  //**************************************************************************
  if (argumentCount != 2) {
    fprintf( stderr, "Error: DEVICE_NODE operand is missing\n" );
    exitCode = 1;
    goto exit;
  }

  //**************************************************************************
  // Open the disk for reading and obtain a work buffer.
  //**************************************************************************
  dasdDescriptor = open(argumentValues[1], O_RDONLY | O_DIRECT);
  if (dasdDescriptor == -1) {
    fprintf(stderr, "Error: unable to open disk %s for reading\n", argumentValues[1]);
    exitCode = 2;
    goto exit;
  }

  returnCode = posix_memalign(&trackBuffer, 4096, 65536);
  if (returnCode) {
    fprintf(stderr, "Error allocating buffer\n");
    exitCode = 3;
    goto exit;
  }

  //**************************************************************************
  // Main Loop: Read and process each track in the disk.
  //**************************************************************************
  while (( returnCode = read( dasdDescriptor, trackBuffer, TRACK_SIZE ) ) > 0) {
    //cylinderIndex = ((uint16_t*)trackBuffer)[0];
    //trackIndex    = ((uint16_t*)trackBuffer)[1];
    trackCount++;

    // Re-initialize these values for each track read.
    keyCountRunCount  = 0;
    dataCountRunCount = 0;
    recordsInTrack    = 0;

    //************************************************************************
    // Loop thru each record in the track that was read and pull out the
    // key length and values along with the data lengths.  We will exit
    // when we encounter a recordIndex that is 'FF'.
    //************************************************************************
    trackBufferCursor = (trackBuffer + TRACK_BEGINNING_OVERHEAD);
    while (TRUE) {
      // Point to the meta data for the track
      recordMetadata = ((RecordMetadata*)trackBufferCursor)[0];
      trackBufferCursor = trackBufferCursor +
                          sizeof(recordMetadata) +
                          recordMetadata.keyCount +
                          recordMetadata.dataCount;

      // Leave the loop when we encounter a record index with a value of 'FF'.
      if (recordMetadata.recordIndex == 0xFF) break;
      recordsInTrack = recordMetadata.recordIndex;

      // Obtain the key count length and values for this record in the track.
      // If the key is the same as the previous key then just update the
      // previous key run count.  Otherwise, in the new row, set the
      // key run count to 1 and save the key count value.
      if (keyCountRunCount &&
          recordMetadata.keyCount ==
            keyCountRunValue[keyCountRunCount - 1]) {
        keyCountRunLength[keyCountRunCount - 1]++;
      } else {
        keyCountRunLength[keyCountRunCount] = 1;
        keyCountRunValue[keyCountRunCount] = recordMetadata.keyCount;
        keyCountRunCount++;
      }

      // Obtain the data count values for this record in the track.
      // If the key is the same as the previous key then just update
      // the previous data run count.  Otherwise, in the new row,
      // set the data run count to 1 and save the data length.
      if (dataCountRunCount &&
          recordMetadata.dataCount ==
            dataCountRunValue[dataCountRunCount - 1]) {
        dataCountRunLength[dataCountRunCount - 1]++;
      } else {
        dataCountRunLength[dataCountRunCount] = 1;
        dataCountRunValue[dataCountRunCount] = recordMetadata.dataCount;
        dataCountRunCount++;
      }
    }

    //************************************************************************
    // Write the information related to the track that has just been
    // processed.
    //************************************************************************
    // Write the number of records in the track to STDOUT.
    returnCode = write(STDOUT_FILENO, &recordsInTrack, 1);
    if ( returnCode < 0 ) {
      exitCode = 5;
      goto exit;
    }

    // Write the key information for the track to STDOUT.
    for (int i = 0; i < keyCountRunCount;  i++) {
      returnCode = write(STDOUT_FILENO, &keyCountRunLength[i], 1);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
      returnCode = write(STDOUT_FILENO, &keyCountRunValue[i],  1);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
    }

    // Write the data information for the track to STDOUT.
    for (int i = 0; i < dataCountRunCount; i++) {
      returnCode = write(STDOUT_FILENO, &dataCountRunLength[i], 1);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
      returnCode = write(STDOUT_FILENO, &dataCountRunValue[i],  2);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
    }

    // Write the keys and data for each record in the track to STDOUT.
    trackBufferCursor = (trackBuffer + TRACK_BEGINNING_OVERHEAD);
    while (TRUE) {
      // Point to the meta data for the record
      recordMetadata = ((RecordMetadata*)trackBufferCursor)[0];
      // Exit the loop when we find a record index of 'FF'.
      if (recordMetadata.recordIndex == 0xFF) break;
      trackBufferCursor += sizeof(recordMetadata);

      // Write the keys for this record to STDOUT.
      returnCode = write(STDOUT_FILENO, trackBufferCursor, recordMetadata.keyCount);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
      trackBufferCursor += recordMetadata.keyCount;

      // Write the data for this record to STDOUT.
      returnCode = write(STDOUT_FILENO, trackBufferCursor, recordMetadata.dataCount);
      if ( returnCode < 0 ) {
        exitCode = 5;
        goto exit;
      }
      trackBufferCursor += recordMetadata.dataCount;

    }
  }

  //*************************************************************************
  // Exit from main loop.  We have either read everything (rc=0) or
  // encountered an error (rc<0).
  //*************************************************************************
  if (returnCode < 0) {
    exitCode = 4;
    fprintf( stderr,
             "Error:  ckdencode encountered an unexpected read error, errno: %d\n",
             errno );
    goto exit;
  }

  //*************************************************************************
  // Normal main exit from this MAIN routine.
  // Note: All exits should exit from this location.
  //*************************************************************************
  exit:
  if ( exitCode == 5 ) {
    fprintf( stderr,
             "Error:  ckdencode encountered an unexpected error writing to STDOUT, errno: %d\n",
             errno );
  }
  if ( dasdDescriptor != -1 ) {
    returnCode = close(dasdDescriptor);
    if (returnCode < 0) {
      fprintf(stderr, "Error closing the disk\n");
      if ( exitCode == 0 ) {
        exitCode = 6;
      }
    }
  }
  if ( trackBuffer != NULL ) free(trackBuffer);
  return exitCode;
}
