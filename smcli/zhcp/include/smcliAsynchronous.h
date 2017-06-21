/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIASYNCHRONOUS_H_
#define SMCLIASYNCHRONOUS_H_

#include "wrapperutils.h"

int asynchronousNotificationDisableDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int asynchronousNotificationEnableDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int asynchronousNotificationQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIASYNCHRONOUS_H_ */
