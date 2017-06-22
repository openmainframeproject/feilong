/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
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
