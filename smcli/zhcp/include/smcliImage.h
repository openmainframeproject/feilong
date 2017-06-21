/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIIMAGE_H_
#define SMCLIIMAGE_H_

#include "wrapperutils.h"

int imageActivate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageActiveConfigurationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUDefine(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCPUSetMaximumDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeactivate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeviceDedicate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeviceDedicateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeviceReset(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeviceUndedicate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDeviceUndedicateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskCopy(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskCopyDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskShare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskShareDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskUnshare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDiskUnshareDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageIPLDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageIPLQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageIPLSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageLockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageLockQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageMDISKLinkQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageNameQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imagePasswordSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageQueryActivateTime(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageRecycle(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageReplaceDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageSCSICharacteristicsDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageSCSICharacteristicsQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageStatusQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageUnlockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeShare(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeSpaceDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeSpaceDefineExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeSpaceQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeSpaceQueryExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageVolumeSpaceRemoveDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIIMAGE_H_ */
