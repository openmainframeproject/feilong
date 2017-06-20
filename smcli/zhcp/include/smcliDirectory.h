/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIDIRECTORY_H_
#define SMCLIDIRECTORY_H_

#include "wrapperutils.h"

int directoryManagerLocalTagDefineDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int directoryManagerLocalTagDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int directoryManagerLocalTagQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int directoryManagerLocalTagSetDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int directoryManagerSearchDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int directoryManagerTaskCancelDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIDIRECTORY_H_ */
