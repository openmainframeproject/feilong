/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIPROFILE_H_
#define SMCLIPROFILE_H_

#include "wrapperutils.h"

int profileCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileLockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileLockQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileReplaceDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int profileUnlockDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIPROFILE_H_ */
