/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017, 2022 IBM Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
int systemImagePerformanceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPageUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceInformationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceThresholdDisable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceThresholdEnable(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemProcessorQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemRDRFileManage(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSCSIDiskQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemServiceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemShutdown(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemSpoolUtilizationQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemWWPNQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLISYSTEM_H_ */
