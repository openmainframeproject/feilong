#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Virtual Machine Utilities for Systems Management Ultra Thin Layer
#
# Copyright 2022 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from datetime import datetime
from threading import Lock


CONTINUE_FAIL_THRESHOLD = 20


class SMAPIStatus():
    def __init__(self):
        # time stamp of last call, note the fail here doesn't mean
        # SMAPI API failed, it's SMAPI failed to execute the command

        self.lastSuccess = ''
        self.lastFail = ''

        # latest call status, 0 means success
        # >0 means continuous failure

        self.continueFail = 0

        self.totalSuccess = 0
        self.totalFail = 0

        # we have multiple threads for cloud connector, need lock for
        # operations for global data
        self.lock = Lock()

    def RecordSuccess(self):
        self.lock.acquire()
        self.lastSuccess = datetime.now()
        self.totalSuccess += 1

        # we think a success means there is no continue Fail
        self.continueFail = 0
        self.lock.release()

    def RecordFail(self):
        self.lock.acquire()
        self.lastFail = datetime.now()
        self.totalFail += 1

        self.continueFail += 1
        self.lock.release()

    def Get(self):
        status = {'totalSuccess': self.totalSuccess,
                  'totalFail': self.totalFail,
                  'lastSuccess': self.lastSuccess,
                  'lastFail': self.lastFail,
                  'continuousFail': self.continueFail,
                  'healthy': self.IsHealthy()
                 }
        return status

    def IsHealthy(self):
        return self.continueFail < CONTINUE_FAIL_THRESHOLD


_SMAPIStatus = None


def GetSMAPIStatus():
    global _SMAPIStatus
    if _SMAPIStatus is None:
        _GetSMAPIStatus = SMAPIStatus()
    return _GetSMAPIStatus
