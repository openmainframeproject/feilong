/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIMETADATA_H_
#define SMCLIMETADATA_H_

#include "wrapperutils.h"

int metadataDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSpaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIMETADATA_H_ */
