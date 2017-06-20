/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIPROTOTYPE_H_
#define SMCLIPROTOTYPE_H_

#include "wrapperutils.h"

int prototypeCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int prototypeDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int prototypeNameQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int prototypeQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int prototypeReplaceDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIPROTOTYPE_H_ */
