/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIAUTHORIZATION_H_
#define SMCLIAUTHORIZATION_H_

#include "wrapperutils.h"

int authorizationListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIAUTHORIZATION_H_ */
