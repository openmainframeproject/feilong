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
 External Name: ckdhex

 Function:

 @param $1: Linux device node representing the disk to be read
 @param $2: First track to display (optional)
 @param $3: Last track to display (optional)

 @return 0 Decode was successful
         1 Help data displayed, incorrect number of operands
         2 Unable to open the disk for reading
         3 Unable to allocate 64k of memory on a page buffer for use
           as a work buffer
         4 A negative return code was received on one of the functions calls.
*****************************************************************************/

#include "cikada.h"

char keyBuffer[512]    = {0};
char dataBuffer[65536] = {0};

//***************************************************************************
// Function: Main section of the program.
//***************************************************************************
int main (int argumentCount, char* argumentValues[]) {
  int firstLine = 1;                   // if 1, first line not shown yet
  int dasdDescriptor = 0;
  int returnCode, startTrack, endTrack;
  int exitCode = 0;
  void* trackBuffer = NULL;

  //**************************************************************************
  // Verify input and display help if parms are missing.
  //**************************************************************************
  if (argumentCount == 2) {
    startTrack = 0;
    endTrack   = INT_MAX;
  } else if (argumentCount == 4) {
    startTrack = atoi(argumentValues[2]);
    endTrack   = atoi(argumentValues[3]);
  } else {
    fprintf(stderr,
            "Usage: %s DEVICE_NODE\n       %s DEVICE_NODE START_TRK END_TRK\n",
            argumentValues[0],
            argumentValues[0]);
    fprintf( stderr, "Note: Disk must have raw track access enabled.\n" );
    exitCode = 1;
    goto exit;
  }

  //**************************************************************************
  // Open the disk for reading and obtain a work buffer.
  //**************************************************************************
  void* trackBufferCursor;
  uint16_t cylinderIndex, trackIndex;
  RecordMetadata recordMetadata;

  dasdDescriptor = open(argumentValues[1], O_RDONLY | O_DIRECT);
  if ( dasdDescriptor == -1 ) {
    fprintf (stderr, "Error opening file.\n");
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
  // Main Loop: Read and process each track.
  //            Loop begins with us reading the 64K of data.  We end the loop
  //            when we fail to read more data or exit early because we
  //            reached the end of tracks to process.
  //**************************************************************************
  while (( returnCode = read( dasdDescriptor, trackBuffer, TRACK_SIZE ) )
                      > 0 ) {
    cylinderIndex = ((uint16_t*)trackBuffer)[0];
    trackIndex    = ((uint16_t*)trackBuffer)[1];

    // Continue or break if we are at the beginning or end of a requested
    // range of tracks to process instead of the whole disk.
    int absTrack = (15 * cylinderIndex + trackIndex);
    if (absTrack < startTrack) continue;
    if (absTrack > endTrack) break;

    // Display the cylinder and track number
    if (( trackIndex == 0 ) || ( firstLine == 1 )) {
      printf("Cylinder: 0x%04x\n", cylinderIndex);
      firstLine = 0;
    }
    printf("  Track:  0x%04x\n", trackIndex);

    // Loop displaying each record in the current track.  Exit the loop
    // when a record index is 'FF'
    trackBufferCursor = (trackBuffer + TRACK_BEGINNING_OVERHEAD);
    while (TRUE) {
      // Point to the metadata, key values and data values.
      recordMetadata = ((RecordMetadata*)trackBufferCursor)[0];
      trackBufferCursor += sizeof(recordMetadata);
      memcpy(keyBuffer, trackBufferCursor, recordMetadata.keyCount);
      trackBufferCursor += recordMetadata.keyCount;
      memcpy(dataBuffer, trackBufferCursor, recordMetadata.dataCount);
      trackBufferCursor += recordMetadata.dataCount;

      // Display the output if we have a valid record. Otherwise, exit.
      if (recordMetadata.recordIndex == 0xFF) {
        break;
      } else {
        printf("    Record Index: 0x%02x   ", recordMetadata.recordIndex);
        printf(    "Key Count: 0x%02x   ",    recordMetadata.keyCount);
        printf(    "Data Count: 0x%02x\n",  recordMetadata.dataCount);

        if ( recordMetadata.keyCount == 0 ) {
          printf( "      KEY: NONE" );
        } else {
          printf( "      KEY: " );
          for (int i = 0; i < recordMetadata.keyCount; i++) {
            printf("%02x ", keyBuffer[i]);
          }
        }

        printf("\n      DATA: ");
        for (int i = 0; i < recordMetadata.dataCount; i++) {
          printf("%02x ", dataBuffer[i]);
        }

        printf("\n");
      }
    }
  }

  //**************************************************************************
  // We have exit from the main loop to read the track and format/display the
  // contents.
  // This can happen when we have read all of the information or we have a
  // read error.
  //
  // If we got an error on the read of the track then exit with an exit code
  // of 4.  Otherwise, everything is good and we can continue processing.
  //**************************************************************************
  if (returnCode < 0) {
    fprintf( stderr,
             "Error:  ckdhex encountered an unexpected read error, errno: %d\n",
             errno );
    exitCode = 4;
  }

  //*************************************************************************
  // Normal main exit from this MAIN routine.
  // Note: Error exits can also occur at earlier points in this routine.
  //*************************************************************************
  exit:
  if ( dasdDescriptor != -1 ) {
    returnCode = close( dasdDescriptor );
    if (returnCode < 0) {
      fprintf(stderr, "Error closing the disk\n");
      if ( exitCode == 0 ) {
        exitCode = 5;
      }
    }
  }
  if ( trackBuffer != NULL ) free(trackBuffer);
  return exitCode;
}
