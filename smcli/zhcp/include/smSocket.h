/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef _SMSOCKET_H
#define _SMSOCKET_H
#include "smPublic.h"

/* smSocket read modifications */
#define SOCKET_ERROR_OK 1  // It is ok to have the socket closed or other error

int smSocketInitialize(struct _vmApiInternalContext* vmapiContextP, int * sockId);
int smSocketWrite(struct _vmApiInternalContext* vmapiContextP, int sockId, char * data, int dataLen);
int smSocketRead(struct _vmApiInternalContext* vmapiContextP, int sockId, char * buff, int len);
int smSocketReadLoop(struct _vmApiInternalContext* vmapiContextP, int sockId, char * buff, int len, int readMod);
int smSocketTerminate(struct _vmApiInternalContext* vmapiContextP, int sockId);
#endif
