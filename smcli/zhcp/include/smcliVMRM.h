/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */
#ifndef SMCLIVMRM_H_
#define SMCLIVMRM_H_

#include "wrapperutils.h"

int vmrmConfigurationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmrmConfigurationUpdate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int vmrmMeasurementQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVMRM_H_ */
