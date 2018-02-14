# Copyright 2017 IBM Corp.
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

from zvmsdk import vmops
from zvmsdk import volumeop
from zvmsdk.tests.unit import base


class TestFCP(base.SDKTestCase):

    def test_parse_normal(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Free',
                'opnstk1:   NPIV world wide port number: NONE',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertIsNone(fcp._npiv_port)
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())

    def test_parse_npiv(self):
        info = ['opnstk1: FCP device number: B83D',
                'opnstk1:   Status: Free',
                'opnstk1:   NPIV world wide port number: 20076D8500005182',
                'opnstk1:   Channel path ID: 59',
                'opnstk1:   Physical world wide port number: 20076D8500005181']
        fcp = volumeop.FCP(info)
        self.assertEqual('B83D', fcp._dev_no.upper())
        self.assertEqual('20076D8500005182', fcp._npiv_port.upper())
        self.assertEqual('59', fcp._chpid.upper())
        self.assertEqual('20076D8500005181', fcp._physical_port.upper())


class TestFCPManager(base.SDKTestCase):

    def setUp(self):
        self.fcpops = volumeop.FCPManager()   

    def test_expand_fcp_list_normal(self):
        fcp_list = "1f10;1f11;1f12;1f13;1f14"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f14'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_dash(self):
        fcp_list = "1f10-1f14"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f14'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_dash(self):
        fcp_list = "1f10;1f11-1f13;1f17"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f17'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    def test_expand_fcp_list_with_normal_plus_2dash(self):
        fcp_list = "1f10;1f11-1f13;1f17-1f1a;1f02"
        expected = set(['1f10', '1f11', '1f12', '1f13', '1f17', '1f18', '1f19', '1f1a', '1f02'])
        fcp_info = self.fcpops._expand_fcp_list(fcp_list)
        self.assertEqual(expected, fcp_info)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_all_fcp_info")
    def test_init_fcp_pool(self, mock_get):
        fcp_list = ['opnstk1: FCP device number: B83D',
                    'opnstk1:   Status: Free',
                    'opnstk1:   NPIV world wide port number: 20076D8500005182',
                    'opnstk1:   Channel path ID: 59',
                    'opnstk1:   Physical world wide port number: 20076D8500005181',
                    'opnstk1: FCP device number: B83E',
                    'opnstk1:   Status: Active',
                    'opnstk1:   NPIV world wide port number: 20076D8500005183',
                    'opnstk1:   Channel path ID: 50',
                    'opnstk1:   Physical world wide port number: 20076D8500005185',]

        mock_get.return_value = fcp_list

        self.fcpops._init_fcp_pool('b83d-b83e')
        self.assertEqual(2, len(self.fcpops._fcp_pool))
        self.assertTrue('b83d' in self.fcpops._fcp_pool)
        self.assertTrue('b83e' in self.fcpops._fcp_pool)
        self.assertFalse('b83f' in self.fcpops._fcp_pool)

        npiv = self.fcpops._fcp_pool['b83d']._npiv_port.upper()
        physical = self.fcpops._fcp_pool['b83d']._physical_port.upper()
        self.assertEqual('20076D8500005182', npiv)
        self.assertEqual('20076D8500005181', physical)
        self.assertEqual('59', self.fcpops._fcp_pool['b83d']._chpid.upper())

        npiv = self.fcpops._fcp_pool['b83e']._npiv_port.upper()
        physical = self.fcpops._fcp_pool['b83e']._physical_port.upper()
        self.assertEqual('20076D8500005183', npiv)
        self.assertEqual('20076D8500005185', physical)
        self.assertEqual('50', self.fcpops._fcp_pool['b83e']._chpid.upper())
