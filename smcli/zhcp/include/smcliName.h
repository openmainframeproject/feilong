/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLINAME_H_
#define SMCLINAME_H_

#include "wrapperutils.h"

int nameListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListDestroy(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int nameListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLINAME_H_ */
