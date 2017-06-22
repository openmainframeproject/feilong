/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLINAME_H_
#define SMCLINAME_H_

#include "wrapperutils.h"

int nameListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListDestroy(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLINAME_H_ */
