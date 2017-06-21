/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
