/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
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
