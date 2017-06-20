/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLIVMRM_H_
#define SMCLIVMRM_H_

#include "wrapperutils.h"

int vmrmConfigurationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmrmConfigurationUpdate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmrmMeasurementQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVMRM_H_ */
