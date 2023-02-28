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
#include <stdio.h>
#include "smPublic.h"
#include "vmapiSystem.h"
#include "vmapiImage.h"
#include "vmapiVirtual.h"
#include "smPublic.h"
#include "vmapiAsynchronous.h"
#include "vmapiAuthorization.h"
#include "vmapiCheck.h"
#include "vmapiDirectory.h"
#include "vmapiName.h"
#include "vmapiProfile.h"
#include "vmapiPrototype.h"

/* Check if Smapi is up and running */
int checkSmapi(vmApiInternalContext vmapiContext);

/* Use Profile_Create_DM to create a profile directory entry to be included in
 * the definition of a virtual image in the directory */
int createProfile(vmApiInternalContext vmapiContext);

/* Use Prototype_Create_DM to create a new virtual image prototype */
int createProto(vmApiInternalContext vmapiContext);

/* Use Image_Create_DM to define a new virtual image in the directory */
int createImage(vmApiInternalContext vmapiContext, char * argV);

/* Use Prototype_Name_Query_DM to obtain a list of names of defined prototypes */
int queryProto(vmApiInternalContext vmapiContext, char * argV);

/* Use Profile_Query_DM to query a profile directory entry */
int queryProfile(vmApiInternalContext vmapiContext, char * argV);

/* Use Image_Query_DM to obtain a virtual images directory entry */
int queryImage(vmApiInternalContext vmapiContext, char * argV);

/* Use Profile_Delete_DM to delete a profile directory entry */
int deleteProfile(vmApiInternalContext vmapiContext, char * argV);

/* Use Prototype_Delete_DM to delete an image prototype */
int deleteProto(vmApiInternalContext vmapiContext, char * argV);

/* Use Image_Delete_DM to delete a virtual image's definition from the directory */
int deleteImage(vmApiInternalContext vmapiContext, char * argV);

/* Use Image_Disk_Create_DM to add a disk to a virtual images directory entry */
int addDisk(vmApiInternalContext vmapiContext, char * argV);

/* Use Image_Query_DM to obtain a virtual images directory entry */
void getImage(vmApiInternalContext vmapiContext, vmApiImageRecord imageRecord[], char * argV);

/* Internal function to display error text to console */
static void displayErrorText(int errorCode);

