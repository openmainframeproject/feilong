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
import unittest

from zvmsdk import volumeop
from zvmsdk.exception import ZVMVolumeError as err


class VolumeOpTestCase(unittest.TestCase):

    def setUp(self):
        self._vol_op = volumeop.VolumeOperator()

    def test_attach_volume_to_instance(self):
        pass

    def test_detach_volume_from_instance(self):
        pass

    def test_validate_instance(self):
        self.assertRaises(err, self._vol_op._validate_instance, None)

        inst = ['inst1', 'sles12']
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {'name': 'inst1'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {'os_type': 'sles12'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {'name': 'inst1', 'os_type': 'centos'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {'name': 'inst1', 'os_type': 'sles12'}
        self._vol_op._validate_instance(inst)

    @mock.patch.object(volumeop.VolumeOperator, '_validate_fc_volume')
    def test_validate_volume(self, _validate_fc_volume):
        self.assertRaises(err, self._vol_op._validate_volume, None)

        volume = ['fcp', '0123456789abcdef', 'abcdef0987654321']
        self.assertRaises(err, self._vol_op._validate_volume, volume)

        volume = {'lun': 'abcdef0987654321'}
        self.assertRaises(err, self._vol_op._validate_volume, volume)

        volume = {'type': 'unknown',
                  'lun': 'abcdef0987654321'}
        self.assertRaises(err, self._vol_op._validate_volume, volume)

        volume = {'type': 'fc',
                  'lun': 'abcdef0987654321'}
        self._vol_op._validate_volume(volume)
        _validate_fc_volume.assert_called_once_with(volume)
        _validate_fc_volume.reset_mock()

        volume = {'type': 'fc',
                  'lun': 'abCDEF0987654321'}
        self._vol_op._validate_volume(volume)
        _validate_fc_volume.assert_called_once_with(volume)

    def test_is_16bit_hex(self):
        self.assertFalse(self._vol_op._is_16bit_hex(None))
        self.assertFalse(self._vol_op._is_16bit_hex('1234'))
        self.assertFalse(self._vol_op._is_16bit_hex('1234567890abcdefg'))
        self.assertFalse(self._vol_op._is_16bit_hex('1234567890abcdeg'))
        self.assertTrue(self._vol_op._is_16bit_hex('1234567890abcdef'))

    def test_validate_fc_volume(self):
        volume = {'type': 'fc'}
        self.assertRaises(err, self._vol_op._validate_fc_volume, volume)

        volume = {'type': 'fc',
                  'lun': 'abcdef0987654321f'}
        self.assertRaises(err, self._vol_op._validate_fc_volume, volume)

        volume = {'type': 'fc',
                  'lun': 'abcdef0987654321'}
        self._vol_op._validate_fc_volume(volume)

    @mock.patch.object(volumeop.VolumeOperator, '_validate_fc_connection_info')
    def _validate_connection_info(self, _validate_fc_connection_info):
        self.assertRaises(err, self._vol_op._validate_connection_info, None)

        fcps = ['1faa', '1fBB']
        wwpns = ['1234567890abcdea', '1234567890abCDEB',
                 '1234567890abcdec', '1234567890abCDED',
                 '1234567890abcdee', '1234567890abCDEF']
        conn_info = ['fc', fcps, wwpns, 'vda']
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {'fcps': fcps,
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {'protocol': 'unknown',
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {'protocol': 'fc',
                     'fcps': fcps,
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self._vol_op._validate_connection_info(conn_info)
        _validate_fc_connection_info.assert_called_once_with(conn_info)

    @mock.patch.object(volumeop.VolumeOperator, '_is_16bit_hex')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_fcp')
    def test_validate_fc_connection_info(self, _validate_fcp, _is_16bit_hex):
        fcps = ['1faa', '1fBB']
        wwpns = ['1234567890abcdea', '1234567890abCDEB',
                 '1234567890abcdec', '1234567890abCDED',
                 '1234567890abcdee', '1234567890abCDEF']

        conn_info = {'protocol': 'fc',
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {'protocol': 'fc',
                     'fcps': '1faa, 1fBB',
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {'protocol': 'fc',
                     'fcps': fcps,
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {'protocol': 'fc',
                     'fcps': fcps,
                     'wwpns': '1234567890abcdea',
                     'alias': 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {'protocol': 'fc',
                     'fcps': fcps,
                     'wwpns': wwpns,
                     'alias': 'vda'}
        self._vol_op._validate_fc_connection_info(conn_info)
        _validate_fcp.assert_called_with(conn_info['fcps'][-1])
        _is_16bit_hex.assert_called_with(conn_info['wwpns'][-1])

    def test_validate_fcp(self):
        self.assertRaises(err, self._vol_op._validate_fcp, None)
        self.assertRaises(err, self._vol_op._validate_fcp, 'absd')
        self.assertRaises(err, self._vol_op._validate_fcp, '12345')
        self._vol_op._validate_fcp('09af')

    def test_get_configurator(self):
        pass
