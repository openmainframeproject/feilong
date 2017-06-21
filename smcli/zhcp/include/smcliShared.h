/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLISHARED_H_
#define SMCLISHARED_H_

#include "wrapperutils.h"

int sharedMemoryAccessAddDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryAccessQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryAccessRemoveDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int sharedMemoryReplace(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLISHARED_H_ */
