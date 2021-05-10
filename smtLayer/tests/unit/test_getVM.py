# Copyright 2021 IBM Corp.
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

import mock

from smtLayer import getVM
from smtLayer.tests.unit import base


class SMTGetVMTestCase(base.SMTTestCase):
    """Test cases for getHost.py in smtLayer."""
    def test_extract_fcp_data(self):
        rh = mock.Mock()
        fake_response = ['FCP device number: 1B0E',
                         'Status: Free',
                         'NPIV world wide port number: C05076DE330005EA',
                         'Channel path ID: 27',
                         'Physical world wide port number: C05076DE33002E41',
                         'FCP device number: 1B0F',
                         'Status: Free',
                         'NPIV world wide port number: C05076DE330005EB',
                         'Channel path ID: 27',
                         'Physical world wide port number:',
                         'Owner: turns', '']
        raw_data = '\n'.join(fake_response)
        ret = getVM.extract_fcp_data(rh, raw_data, 'free')
        self.assertEqual(ret, '\n'.join(fake_response[0:10]))
