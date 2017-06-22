/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIASYNCHRONOUS_H_
#define SMCLIASYNCHRONOUS_H_

#include "wrapperutils.h"

int asynchronousNotificationDisableDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int asynchronousNotificationEnableDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int asynchronousNotificationQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIASYNCHRONOUS_H_ */
