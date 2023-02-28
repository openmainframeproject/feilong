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
 External Name: ckddecode

 Function: Decodes data CiKaDa encoded data coming in on the standard input
           stream and writes the keys and data to the ECKD disk in the
           correct format.

 Input Stream Format: See the cikada.h file.

 ECKD Disk Format: See the cikada.h file.

 @param $1: Linux device node representing the disk to be written
 @param $2: Size of the new disk so that additional space on
            the restored ECKD can be cleared.

 @return 0 Decode was successful
         1 Help data displayed, incorrect number of operands
         2 Unable to open the disk for writing
         3 Unable to allocate 64k of memory on a page buffer for use
           as a work buffer
         4 A negative return code was received on one of the functions calls.
         5 An error occurred reading data from STDIN.
         6 Unable to write a track buffer to the disk.
         7 Track buffer is not on a 4k boundary
*****************************************************************************/
#include "cikada.h"

// The first 16 bytes in each track are a label declaring the cylinder and
// track indices.
#define TRACK_BEGINNING_OVERHEAD 16

// Fixed data which appears in gap near the beginning of each track.
uint8_t  trackGap[12] = {0x00,0x00,0x00,0x08,
                         0x00,0x00,0x00,0x00,
                         0x00,0x00,0x00,0x00};

/****************************************************************************
  Name: readNBytesFromStdin()

  Function: Read a specified number of bytes from STDIN.

  @param $1: Pointer to the buffer to fill with data read from STDIN.
  @param $2: Number of bytes to read.

  @return 0 Read was successful
          -value Errno returned on the read
  ***************************************************************************/
static inline int readNBytesFromStdin(void* buffer, int bytes) {
  int retCode = 0;
  int bytesRead = 0;
  while (( bytesRead < bytes ) && ( retCode >= 0 )) {
    retCode = read(STDIN_FILENO, buffer + bytesRead, bytes - bytesRead);
    if ( retCode >= 0 ) {
      bytesRead += retCode;
    }
  }

  if ( retCode >= 0 ) {
    return 0;
  } else {
    return -errno;
  }
}

/****************************************************************************
  Function: Main section of the program.
  ***************************************************************************/
int main (int argumentCount, char* argumentValues[]) {
  int returnCode, exitCode = 0;
  int dasdDescriptor = -1;          // DASD device descriptor
  int cylCount = 0;                 // Cylinder count
  int totalTracks = 0;              // Total number of tracks in new disk
  uint8_t  keyCountRunCount;        // Number of key count runs.
  uint8_t  keyCountRunTotal;        // Sum of key count run lengths.
  uint8_t  keyCountRunLength[256];  // List of key count run lengths.
  uint8_t  keyCountRunValue[256];   // List of key count run values.
  uint8_t  keyCountRunIndex;        // Key run being processed.
  uint8_t  keyCountRunRemaining;    // Keys left in run being processed.
  uint8_t  dataCountRunCount;       // Number of data count runs.
  uint8_t  dataCountRunTotal;       // Sum of data count run lengths.
  uint8_t  dataCountRunLength[256]; // List of data count run lengths.
  uint16_t dataCountRunValue[256];  // List of data count run values.
  uint8_t  dataCountRunIndex;       // Data run being processed.
  uint8_t  dataCountRunRemaining;   // Data blocks left in run being processed.
  uint8_t  recordsInTrack;          // Count of records in track being written.
  uint8_t  keyCount;                // Size of key being processed.
  uint16_t dataCount;               // Size of data block being processed.
  uint32_t trackIndex;              // Index of track being processed.
  void*    trackBuffer = NULL;      // Buffer for assembling track data before
                                    // writing it to disk.
  void*    trackBufferCursor;       // Pointer to place within track buffer
                                    // to which the next write should be
                                    // performed.

  //**************************************************************************
  // Verify input and display help if parms are missing.
  //**************************************************************************
  if (argumentCount != 3) {
    fprintf( stderr, "Usage: %s DEVICE_NODE DEVICE_SIZE\n", argumentValues[0] );
    exitCode = 1;
    goto exit;
  }

  cylCount = atoi( argumentValues[2] );    // Begin with number of cylinders
  if ( cylCount > 0 ) {
    totalTracks = cylCount * TRACKS_PER_CYLINDER;
  } else {
    fprintf( stderr, "Error: Cylinder count is not valid: %s\n",
        argumentValues[2]);
    exitCode = 1;
    goto exit;
  }

  //**************************************************************************
  // Open the disk for writing and obtain a work buffer.
  //**************************************************************************
  dasdDescriptor = open( argumentValues[1], O_WRONLY | O_DIRECT | O_SYNC );
  if (dasdDescriptor == -1) {
    fprintf(stderr, "Error opening disk for writing\n");
    exitCode = 2;
    goto exit;
  }

  // Obtain a 64k work buffer aligned on a page boundary.
  returnCode = posix_memalign(&trackBuffer, 4096, 65536);

  if (returnCode) {
    if ( returnCode == ENOMEM ) {
      fprintf( stderr, "Error: insufficient space for track work buffer\n" );
    } else {
      fprintf( stderr, "Error allocating buffer, rc: %d\n", returnCode );
    }
    exitCode = 3;
    goto exit;
  }

  if ( ((uintptr_t) trackBuffer) % 4096 != 0 ) {
    fprintf( stderr, "Track buffer is not on a 4k boundary: 0x%lx\n", (uintptr_t) trackBuffer );
    exitCode = 7;
    goto exit;
  }

  //**************************************************************************
  // Main Loop: Read and process a track's worth of data at a time from STDIN.
  //            Loop begins with us reading the number of records in the
  //            current track.  We end the loop when we fail to read a value
  //            for the records in the track.
  //**************************************************************************
  trackIndex = 0;
  while (( returnCode = read(STDIN_FILENO,
                            &recordsInTrack,
                            sizeof(recordsInTrack)) )
                      > 0) {

    keyCountRunCount  = 0;
    keyCountRunTotal  = 0;
    dataCountRunCount = 0;
    dataCountRunTotal = 0;

    // Read the key count length and values for each record in the track.
    while (keyCountRunTotal < recordsInTrack) {
      returnCode = readNBytesFromStdin(&keyCountRunLength[keyCountRunCount], 1);
      if (returnCode < 0) {
        fprintf(stderr, "Error reading the key count length\n");
        fprintf(stderr, "Errno: %s\n", strerror(-returnCode));
        exitCode = 5;
        goto exit;
      }
      returnCode = readNBytesFromStdin(&keyCountRunValue[keyCountRunCount],  1);
      if (returnCode < 0) {
        fprintf(stderr, "Error reading record key count value\n");
        fprintf(stderr, "Errno: %s\n", strerror(-returnCode));
        exitCode = 5;
        goto exit;
      }
      keyCountRunTotal+=keyCountRunLength[keyCountRunCount];
      keyCountRunCount++;
    }

    // Read the data count length and value for each record in the track.
    while (dataCountRunTotal < recordsInTrack) {
      returnCode = readNBytesFromStdin(&dataCountRunLength[dataCountRunCount], 1);
      if (returnCode < 0) {
        fprintf(stderr, "Error reading record data count\n");
        fprintf(stderr, "Errno: %s\n", strerror(-returnCode));
        exitCode = 5;
        goto exit;;
      }

      returnCode = readNBytesFromStdin(&dataCountRunValue[dataCountRunCount], 2);
      if (returnCode < 0) {
        fprintf(stderr, "Error reading record data count\n");
        fprintf(stderr, "Errno: %s\n", strerror(-returnCode));
        exitCode = 5;
        goto exit;
      }

      dataCountRunTotal+=dataCountRunLength[dataCountRunCount];
      dataCountRunCount++;
    }

    // Set up count variables for the next part where we create/format
    // the track buffer with the keys and data.
    keyCountRunIndex      = 0;
    keyCountRunRemaining  = keyCountRunLength[0] - 1;
    dataCountRunIndex     = 0;
    dataCountRunRemaining = dataCountRunLength[0] - 1;

    // Add the cylinder, track, and gap to beginning of track buffer:
    trackBufferCursor = trackBuffer;
    ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex / 15);
    trackBufferCursor += 2;
    ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex % 15);
    trackBufferCursor += 2;
    memcpy(trackBufferCursor, trackGap, sizeof(trackGap));
    trackBufferCursor += sizeof(trackGap);

    //*************************************************************************
    // Add the records in this track to the track buffer:
    //*************************************************************************
    for (uint8_t i = 0; i < recordsInTrack; i++) {
      keyCount = keyCountRunValue[keyCountRunIndex];
      dataCount = dataCountRunValue[dataCountRunIndex];

      // Add record metadata:
      ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex / 15);
      trackBufferCursor += 2;
      ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex % 15);
      trackBufferCursor += 2;

      // Record numbers are for some reason indexed off of 1 in the raw CKD
      // encoding, despite indexing off of 0 for cylinders and tracks.
      ((uint8_t*)trackBufferCursor)[0] = (i + 1);
      trackBufferCursor += 1;
      ((uint8_t*)trackBufferCursor)[0] = keyCount;
      trackBufferCursor += 1;
      ((uint16_t*)trackBufferCursor)[0] = dataCount;
      trackBufferCursor += 2;

      //**********************************************************************
      // For each record key expected, read it from STDIN into the
      // track work buffer.
      //**********************************************************************
      while (keyCount > 0) {
        returnCode = read(STDIN_FILENO, trackBufferCursor, keyCount);
        if (returnCode < 0) {
          fprintf(stderr, "Error reading record key\n");
          fprintf(stderr, "0x%02x bytes read\n", returnCode);
          exitCode = 5;
          goto exit;
        } else {
          trackBufferCursor += returnCode;
          keyCount -= returnCode;
        }
      }

      //**********************************************************************
      // For count of data expected, read it from STDIN into the
      // track work buffer.
      //**********************************************************************
      while (dataCount > 0) {
        returnCode = read(STDIN_FILENO, trackBufferCursor, dataCount);
        if (returnCode < 0) {
          fprintf(stderr, "Error reading record data\n");
          fprintf(stderr, "0x%04x bytes read\n", returnCode);
          exitCode = 5;
          goto exit;
        } else {
          trackBufferCursor += returnCode;
          dataCount -= returnCode;
        }
      }

      //**********************************************************************
      //
      //**********************************************************************
      if (keyCountRunRemaining) {
        keyCountRunRemaining--;
      } else {
        keyCountRunRemaining = keyCountRunLength[++keyCountRunIndex] - 1;
      }
      if (dataCountRunRemaining) {
        dataCountRunRemaining--;
      } else {
        dataCountRunRemaining = dataCountRunLength[++dataCountRunIndex] - 1;
      }
    }

    //************************************************************************
    // Set a "fence" at the end of the track buffer to foxes for the control
    // portion and zero out any remaining data space.
    //************************************************************************
    memset(trackBufferCursor, 0xFF, 12);
    trackBufferCursor += 12;
    memset(trackBufferCursor,
           0x00,
           TRACK_SIZE - (trackBufferCursor - trackBuffer));

    //************************************************************************
    // Write the track buffer work area to the disk.
    //************************************************************************
    returnCode = write(dasdDescriptor, trackBuffer, TRACK_SIZE);
    if (returnCode < TRACK_SIZE) {
        fprintf( stderr, "Error: A problem was encountered writing track %d" \
                 "to the target disk, rc: %d, errno: %d\n",
                 trackIndex, returnCode, errno );
      exitCode = 6;
      goto exit;
    }

    trackIndex++;
  }

  //**************************************************************************
  // We have exit from the main read image information and write track loop.
  // This can happen when we have read all of the information or we have a
  // read error when trying to obtain the number of records in the new track.
  //
  // If we got an error on the read of the number of records in the track
  // (rc = -1) then exit with an exit code of 5.
  // Otherwise (rc = 0), everything is good and we can continue processing.
  //**************************************************************************
  if (returnCode < 0) {
    exitCode = 5;
    fprintf( stderr,
             "Error:  ckddecode encountered an unexpected read error, errno: %d\n",
             errno );
    goto exit;
  }

  //**************************************************************************
  // Clear out the rest of the rest of this disk if this disk is larger than
  // the original disk from which the image was created.
  //**************************************************************************
  if ( trackIndex < totalTracks ) {

    dataCount = 4096;           // all dummy records will have same data count

    //*************************************************************************
    // Build the track header portion of the track buffer
    //*************************************************************************
    trackBufferCursor = trackBuffer;
    trackBufferCursor += 4;               // Bump past track header's cyl/track info
                                          // which we will fill in later.
    memcpy( trackBufferCursor, trackGap, sizeof(trackGap) );  // Set the trackGap
    trackBufferCursor += sizeof(trackGap);

    //****************************************************************************
    // Build the fixed record portion of the track buffer, 15 records each having:
    //     rec # (1-15), key count (0), data count (4096)
    //****************************************************************************
    for (uint8_t i = 1; i <= 12; i++) {
      trackBufferCursor += 4  ;    // Bump past the record header's cylinder/track
                                   // info area which we fill in later.
      ((uint8_t*)trackBufferCursor)[0] = i;           // Set the record number
      trackBufferCursor += 1;

      ((uint8_t*)trackBufferCursor)[0] = 0;           // zero key count
      trackBufferCursor += sizeof(keyCount);

      ((uint16_t*)trackBufferCursor)[0] = dataCount;
      trackBufferCursor += sizeof(dataCount);
      memset( trackBufferCursor, 0x00, (size_t) dataCount );          // clear data area
      trackBufferCursor += dataCount;
    }

    // Set a "fence" at the end of the track buffer to foxes for the control
    // portion and zero out any remaining space.
    memset( trackBufferCursor, 0xFF, 12 );                // Add the control portion
    trackBufferCursor += 12;
    memset(trackBufferCursor,
           0x00,
           TRACK_SIZE - (trackBufferCursor - trackBuffer));

    //*************************************************************************
    // For each track configure the variable header information which is the
    //   cylinder and track index in record 0 and for the beginning of each
    //   record.  After variable portion is updated then write the cylinder
    //   to the DASD.
    //*************************************************************************
    while ( trackIndex < totalTracks ) {
      trackBufferCursor = trackBuffer;        // Start each track at beginning of buffer

      // Modify the track's cylinder and track info
      ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex / TRACKS_PER_CYLINDER );
      ((uint16_t*)trackBufferCursor)[1] = (uint16_t)(trackIndex % TRACKS_PER_CYLINDER );
      trackBufferCursor += 4 + sizeof(trackGap);

      // Modify the track record's cylinder and track info
      for (uint8_t i = 1; i <= 12; i++) {
        ((uint16_t*)trackBufferCursor)[0] = (uint16_t)(trackIndex / TRACKS_PER_CYLINDER);
        ((uint16_t*)trackBufferCursor)[1] = (uint16_t)(trackIndex % TRACKS_PER_CYLINDER);
        trackBufferCursor += 4 + 1 + 1 + sizeof(dataCount) + dataCount;
      }

      // Write the track buffer work area to the disk.
      returnCode = write( dasdDescriptor, trackBuffer, TRACK_SIZE );
      if ( returnCode < TRACK_SIZE ) {
        fprintf( stderr, "Error: A problem was encountered writing track %d" \
                 "to the target disk, rc: %d, errno: %d\n",
                 trackIndex, returnCode, errno );
        exitCode = 6;
        goto exit;
      }

      trackIndex++;
    }
  }

  //*************************************************************************
  // Normal main exit from this MAIN routine.
  // Note: Error exits can also occur at earlier points in this routine.
  //*************************************************************************
  exit:
  if ( dasdDescriptor != -1 ) {
    fsync( dasdDescriptor );
    close( dasdDescriptor );
  }
  if ( trackBuffer != NULL ) free( trackBuffer );
  return exitCode;
}
