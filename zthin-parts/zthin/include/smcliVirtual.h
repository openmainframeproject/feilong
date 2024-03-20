/**
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Copyright 2017,2018 IBM Corporation
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
#ifndef SMCLIVIRTUAL_H_
#define SMCLIVIRTUAL_H_

#include "wrapperutils.h"

int virtualChannelConnectionCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualChannelConnectionCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualChannelConnectionDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualChannelConnectionDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterConnectLAN(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterConnectLANDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterConnectVswitch(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterConnectVswitchDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterConnectVswitchExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterCreateDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterCreateExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterCreateExtendedDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterDeleteDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterDisconnect(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterDisconnectDM(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkAdapterQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryExtended( int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP );
int virtualNetworkLANAccess(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkLANAccessQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkLANCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkLANDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkLANQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkOSAQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVLANQueryStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchCreateExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchDeleteExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryByteStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchSetExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVIRTUAL_H_ */
