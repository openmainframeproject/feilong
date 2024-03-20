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
#ifndef SMCLIAUTHORIZATION_H_
#define SMCLIAUTHORIZATION_H_

#include "wrapperutils.h"

int authorizationListAdd(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);
int authorizationListRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP);

#endif /* SMCLIAUTHORIZATION_H_ */
