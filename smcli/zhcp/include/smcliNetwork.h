/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */

#ifndef SMCLINETWORK_H_
#define SMCLINETWORK_H_

#include "wrapperutils.h"

int networkIpInterfaceCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);


#endif /* SMCLINETWORK_H_ */
