/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIAUTHORIZATION_H_
#define SMCLIAUTHORIZATION_H_

#include "wrapperutils.h"

int authorizationListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIAUTHORIZATION_H_ */
