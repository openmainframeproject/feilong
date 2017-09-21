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
from zvmsdk.exception import SDKInvalidInputFormat as err
from zvmsdk.tests.unit import base

# instance parameters:
from zvmsdk.volumeop import NAME as NAME
from zvmsdk.volumeop import OS_TYPE as OS_TYPE
# volume parameters:
from zvmsdk.volumeop import SIZE as SIZE
from zvmsdk.volumeop import TYPE as TYPE
from zvmsdk.volumeop import LUN as LUN
# connection_info parameters:
from zvmsdk.volumeop import ALIAS as ALIAS
from zvmsdk.volumeop import PROTOCOL as PROTOCOL
from zvmsdk.volumeop import FCPS as FCPS
from zvmsdk.volumeop import WWPNS as WWPNS
from zvmsdk.volumeop import DEDICATE as DEDICATE


class _BaseConfiguratorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(_BaseConfiguratorTestCase, cls).setUpClass()
        cls._base_cnf = volumeop._BaseConfigurator()

    @mock.patch.object(volumeop._BaseConfigurator, 'config_attach_inactive')
    @mock.patch.object(volumeop._BaseConfigurator, 'config_attach_active')
    @mock.patch.object(vmops.VMOps, 'is_reachable')
    def test_config_attach(self, is_reachable,
                           config_attach_active,
                           config_attach_inactive):
        inst = {NAME: 'inst1'}
        (volume, conn_info) = ({}, {})

        is_reachable.return_value = True
        config_attach_active.return_value = None
        self._base_cnf.config_attach(inst, volume, conn_info)
        config_attach_active.assert_called_once_with(inst, volume, conn_info)

        is_reachable.return_value = False
        config_attach_inactive.return_value = None
        self._base_cnf.config_attach(inst, volume, conn_info)
        config_attach_inactive.assert_called_once_with(inst, volume, conn_info)


class VolumeOpTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(VolumeOpTestCase, cls).setUpClass()
        cls._vol_op = volumeop.VolumeOperator()

    @mock.patch.object(volumeop.VolumeOperator, '_get_configurator')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_connection_info')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_volume')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_instance')
    def test_attach_volume_to_instance_SLES12(self,
                                              _validate_instance,
                                              _validate_volume,
                                              _validate_connection_info,
                                              _get_configurator):
        inst = {NAME: 'inst1', OS_TYPE: 'sles12sp2'}
        volume = {TYPE: 'fc',
                  LUN: 'abCDEF0987654321'}
        fcps = ['1faa', '1fBB']
        wwpns = ['1234567890abcdea', '1234567890abCDEB',
                 '1234567890abcdec', '1234567890abCDED',
                 '1234567890abcdee', '1234567890abCDEF']
        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}

        configurator = volumeop._Configurator_SLES12()
        _get_configurator.return_value = configurator
        configurator.config_attach = mock.MagicMock()

        self._vol_op.attach_volume_to_instance(inst, volume, conn_info)
        _validate_instance.assert_called_once_with(inst)
        _validate_volume.assert_called_once_with(volume)
        _validate_connection_info.assert_called_once_with(conn_info)
        _get_configurator.assert_called_once_with(inst)
        configurator.config_attach.assert_called_once_with(inst,
                                                           volume,
                                                           conn_info)

    @mock.patch.object(volumeop.VolumeOperator, '_get_configurator')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_connection_info')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_volume')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_instance')
    def test_detach_volume_from_instance(self,
                                         _validate_instance,
                                         _validate_volume,
                                         _validate_connection_info,
                                         _get_configurator):
        inst = {NAME: 'inst1', OS_TYPE: 'sles12sp2'}
        volume = {TYPE: 'fc',
                  LUN: 'abCDEF0987654321'}
        fcps = ['1faa', '1fBB']
        wwpns = ['1234567890abcdea', '1234567890abCDEB',
                 '1234567890abcdec', '1234567890abCDED',
                 '1234567890abcdee', '1234567890abCDEF']
        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}

        configurator = volumeop._Configurator_SLES12()
        _get_configurator.return_value = configurator
        configurator.config_detach = mock.MagicMock()

        self._vol_op.detach_volume_from_instance(inst, volume, conn_info)
        _validate_instance.assert_called_once_with(inst)
        _validate_volume.assert_called_once_with(volume)
        _validate_connection_info.assert_called_once_with(conn_info)
        _get_configurator.assert_called_once_with(inst)
        configurator.config_detach.assert_called_once_with(inst,
                                                           volume,
                                                           conn_info)

    def test_validate_instance(self):
        inst = {NAME: 'inst1'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {OS_TYPE: 'sles12'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {NAME: 'inst1', OS_TYPE: 'centos'}
        self.assertRaises(err, self._vol_op._validate_instance, inst)

        inst = {NAME: 'inst1', OS_TYPE: 'rhel7.2'}
        self._vol_op._validate_instance(inst)

        inst = {NAME: 'inst1', OS_TYPE: 'sles12sp2'}
        self._vol_op._validate_instance(inst)

        inst = {NAME: 'inst1', OS_TYPE: 'ubuntu16.10'}
        self._vol_op._validate_instance(inst)

    @mock.patch.object(volumeop.VolumeOperator, '_validate_fc_volume')
    def test_validate_volume(self, _validate_fc_volume):
        volume = {LUN: 'abCDEF0987654321', SIZE: '1G'}
        self.assertRaises(err, self._vol_op._validate_volume, volume)

        volume = {TYPE: 'unknown',
                  LUN: 'abCDEF0987654321',
                  SIZE: '1G'}
        self.assertRaises(err, self._vol_op._validate_volume, volume)

        volume = {LUN: 'abCDEF0987654321', TYPE: 'fc'}
        self._vol_op._validate_volume(volume)
        _validate_fc_volume.assert_called_once_with(volume)
        _validate_fc_volume.reset_mock()

        volume = {TYPE: 'fc',
                  LUN: 'abCDEF0987654321',
                  SIZE: '1G'}
        self._vol_op._validate_volume(volume)
        _validate_fc_volume.assert_called_once_with(volume)

    def test_is_16bit_hex(self):
        self.assertFalse(self._vol_op._is_16bit_hex(None))
        self.assertFalse(self._vol_op._is_16bit_hex('1234'))
        self.assertFalse(self._vol_op._is_16bit_hex('1234567890abcdefg'))
        self.assertFalse(self._vol_op._is_16bit_hex('1234567890abcdeg'))
        self.assertTrue(self._vol_op._is_16bit_hex('1234567890abcdef'))

    def test_validate_fc_volume(self):
        volume = {TYPE: 'fc'}
        self.assertRaises(err, self._vol_op._validate_fc_volume, volume)

        volume = {TYPE: 'fc',
                  LUN: 'abcdef0987654321f'}
        self.assertRaises(err, self._vol_op._validate_fc_volume, volume)

        volume = {TYPE: 'fc',
                  LUN: 'abcdef0987654321'}
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

        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     WWPNS: wwpns}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'unknown',
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self._vol_op._validate_connection_info(conn_info)
        _validate_fc_connection_info.assert_called_once_with(conn_info)

    @mock.patch.object(volumeop.VolumeOperator, '_is_16bit_hex')
    @mock.patch.object(volumeop.VolumeOperator, '_validate_fcp')
    def test_validate_fc_connection_info(self, _validate_fcp, _is_16bit_hex):
        fcps = ['1faa', '1fBB']
        wwpns = ['1234567890abcdea', '1234567890abCDEB',
                 '1234567890abcdec', '1234567890abCDED',
                 '1234567890abcdee', '1234567890abCDEF']
        conn_info = {PROTOCOL: 'fc',
                     DEDICATE: '1faa, 1fBB',
                     FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     FCPS: '1faa, 1fBB',
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     FCPS: fcps,
                     WWPNS: '1234567890abcdea',
                     ALIAS: 'vda'}
        self.assertRaises(err,
                          self._vol_op._validate_fc_connection_info,
                          conn_info)

        conn_info = {PROTOCOL: 'fc',
                     DEDICATE: fcps,
                     FCPS: fcps,
                     WWPNS: wwpns,
                     ALIAS: 'vda'}
        self._vol_op._validate_fc_connection_info(conn_info)
        _validate_fcp.assert_called_with(conn_info[FCPS][-1])
        _is_16bit_hex.assert_called_with(conn_info[WWPNS][-1])

    def test_validate_fcp(self):
        self.assertRaises(err, self._vol_op._validate_fcp, None)
        self.assertRaises(err, self._vol_op._validate_fcp, 'absd')
        self.assertRaises(err, self._vol_op._validate_fcp, '12345')
        self._vol_op._validate_fcp('09af')

    def test_get_configurator(self):
        instance = {OS_TYPE: 'rhel7'}
        self.assertIsInstance(self._vol_op._get_configurator(instance),
                              volumeop._Configurator_RHEL7)
        instance = {OS_TYPE: 'sles12'}
        self.assertIsInstance(self._vol_op._get_configurator(instance),
                              volumeop._Configurator_SLES12)
        instance = {OS_TYPE: 'ubuntu16'}
        self.assertIsInstance(self._vol_op._get_configurator(instance),
                              volumeop._Configurator_Ubuntu16)
        instance = {OS_TYPE: 'centos'}
        self.assertRaises(err, self._vol_op._get_configurator, instance)
