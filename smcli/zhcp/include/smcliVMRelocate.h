/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIVMRELOCATE_H_
#define SMCLIVMRELOCATE_H_

#include "wrapperutils.h"

int vmRelocate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateImageAttributes(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateStatus(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVMRELOCATE_H_ */
