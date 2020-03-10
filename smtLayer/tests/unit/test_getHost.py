# Copyright 2018 IBM Corp.
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

from smtLayer import getHost
from smtLayer.tests.unit import base


class SMTGetHostTestCase(base.SMTTestCase):
    """Test cases for getHost.py in smtLayer."""

    def test_getDiskPoolSpace9336(self):
        parts = ['v1', '9336-32', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390(self):
        parts = ['v1', '3390-09', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)

    def test_getDiskPoolSpace9336Unknown(self):
        parts = ['v1', '????', 1, 10000000]
        size = getHost._getDiskSize(parts)
        self.assertEqual(5120000000, size)

    def test_getDiskPoolSpace3390Unknown(self):
        parts = ['v1', '????', 1, 10016]
        size = getHost._getDiskSize(parts)
        self.assertEqual(7384596480, size)
