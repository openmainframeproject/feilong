/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIQUERY_H_
#define SMCLIQUERY_H_

#include "wrapperutils.h"

int queryABENDDump(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int queryAllDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int queryAPIFunctionalLevel(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int queryAsynchronousOperationDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int queryDirectoryManagerLevelDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIQUERY_H_ */
