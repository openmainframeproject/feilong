/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
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
