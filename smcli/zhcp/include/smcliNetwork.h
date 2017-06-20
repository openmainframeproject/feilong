/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */

#ifndef SMCLINETWORK_H_
#define SMCLINETWORK_H_

#include "wrapperutils.h"

int networkIpInterfaceCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int networkIpInterfaceRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);


#endif /* SMCLINETWORK_H_ */
