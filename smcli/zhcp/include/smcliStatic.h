/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */

#ifndef SMCLISTATIC_H_
#define SMCLISTATIC_H_

#include "wrapperutils.h"

int staticimageChangesActivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int staticimageChangesDeactivateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int staticimageChangesImmediateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLISTATIC_H_ */
