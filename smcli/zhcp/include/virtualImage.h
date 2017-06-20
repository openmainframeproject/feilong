/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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

