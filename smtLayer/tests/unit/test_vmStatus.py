#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8

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

from smtLayer import vmStatus
from smtLayer.tests.unit import base


class SMTvmStatusTestCase(base.SMTTestCase):
    """Test cases for vmStatus.py in smtLayer."""

    def test_get_success(self):
        s = vmStatus.SMAPIStatus()
        s.RecordSuccess()
        s.RecordSuccess()

        ret = s.Get()
        d = ret.pop('lastSuccess', None)
        self.assertIsNotNone(d)
        exp = {'continuousFail': 0,
               'totalFail': 0,
               'healthy': True,
               'lastFail': '',
               'totalSuccess': 2}
        self.assertDictEqual(exp, ret)

    def test_get_fail(self):
        s = vmStatus.SMAPIStatus()
        s.RecordFail()
        s.RecordFail()

        ret = s.Get()
        d = ret.pop('lastFail', None)
        self.assertIsNotNone(d)
        exp = {'continuousFail': 2,
               'totalFail': 2,
               'healthy': True,
               'lastSuccess': '',
               'totalSuccess': 0}
        self.assertDictEqual(exp, ret)

    def test_get_multiplefail(self):
        s = vmStatus.SMAPIStatus()
        s.RecordSuccess()
        for i in range(40):
            s.RecordFail()

        ret = s.Get()
        d = ret.pop('lastFail', None)
        self.assertIsNotNone(d)
        m = ret.pop('lastSuccess', None)
        self.assertIsNotNone(m)
        exp = {'continuousFail': 40,
               'totalFail': 40,
               'healthy': False,
               'totalSuccess': 1}
        self.assertDictEqual(exp, ret)
