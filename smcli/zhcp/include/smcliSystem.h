/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef SMCLISYSTEM_H_
#define SMCLISYSTEM_H_

#include "wrapperutils.h"

int systemConfigSyntaxCheck(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemDiskAccessibility(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemDiskAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemDiskIOQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemEQIDQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemFCPFreeQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPageUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceThresholdDisable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceThresholdEnable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemServiceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemShutdown(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSpoolUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemWWPNQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLISYSTEM_H_ */
