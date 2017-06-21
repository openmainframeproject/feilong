/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIEVENT_H_
#define SMCLIEVENT_H_

#include "wrapperutils.h"

int eventStreamAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int eventSubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int eventUnsubscribe(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIEVENT_H_ */
