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
#ifndef SMCLIMETADATA_H_
#define SMCLIMETADATA_H_

#include "wrapperutils.h"

int metadataDelete(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataGet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSet(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int metadataSpaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIMETADATA_H_ */
