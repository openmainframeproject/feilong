/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017 IBM Corporation
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
#ifndef SMCLIUNDOCUMENTED_H_
#define SMCLIUNDOCUMENTED_H_

#include "wrapperutils.h"

int imageIPLDeviceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int imagePerformanceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int ipAddrGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int queryAsychronousOperationDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemInfoQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemIOQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int systemPerformanceInfoQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkQueryLAN(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkQueryOSA(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryIUOStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int xCATCommandsIUO(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIUNDOCUMENTED_H_ */
