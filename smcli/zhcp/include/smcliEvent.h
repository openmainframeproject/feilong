/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIEVENT_H_
#define SMCLIEVENT_H_

#include "wrapperutils.h"

int eventStreamAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int eventSubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int eventUnsubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIEVENT_H_ */
