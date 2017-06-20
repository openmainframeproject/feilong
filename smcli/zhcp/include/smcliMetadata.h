/**
 * IBM (C) Copyright 2013, 2016 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIMETADATA_H_
#define SMCLIMETADATA_H_

#include "wrapperutils.h"

int metadataDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSpaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIMETADATA_H_ */
