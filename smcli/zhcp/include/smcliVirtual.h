/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
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
int virtualNetworkVswitchQueryExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchQueryStats(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int virtualNetworkVswitchSetExtended(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIVIRTUAL_H_ */
