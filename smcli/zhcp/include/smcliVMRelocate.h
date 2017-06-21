/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIVMRELOCATE_H_
#define SMCLIVMRELOCATE_H_

#include "wrapperutils.h"

int vmRelocate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateImageAttributes(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmRelocateStatus(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVMRELOCATE_H_ */
