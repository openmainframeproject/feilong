/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIIMAGEDEFINITION_H_
#define SMCLIIMAGEDEFINITION_H_

#include "wrapperutils.h"

int imageDefinitionAsyncUpdates(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDefinitionCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDefinitionDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDefinitionQueryDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imageDefinitionUpdateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIIMAGEDEFINITION_H_ */
