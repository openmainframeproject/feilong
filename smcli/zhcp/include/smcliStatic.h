/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */

#ifndef SMCLISTATIC_H_
#define SMCLISTATIC_H_

#include "wrapperutils.h"

int staticimageChangesActivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int staticimageChangesDeactivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int staticimageChangesImmediateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLISTATIC_H_ */
