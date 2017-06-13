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
        self.assertEqual(self._vol_op._validate_instance(inst), None)

    def test_validate_volume(self):
        self.assertRaises(err, self._vol_op._validate_volume, None)
        volume = ['fcp', '0123456789abcdef', 'abcdef0987654321']
        self.assertRaises(err, self._vol_op._validate_volume, volume)
        volume = {'type': 'unknown',
                  'lun': 'abcdef0987654321'}
        self.assertRaises(err, self._vol_op._validate_volume, volume)
        volume = {'type': 'fc',
                  'lun': 'abcdef0987654321'}
        self.assertEqual(self._vol_op._validate_volume(volume), None)

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
                  'lun': 'abcdef0987654321'}
        self.assertEqual(self._vol_op._validate_fc_volume(volume), None)

    def test_get_configurator(self):
        pass
