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

from zvmsdk import dist
from zvmsdk import utils
from zvmsdk import vmops
from zvmsdk import volumeop
from zvmsdk.config import CONF
from zvmsdk.exception import ZVMVolumeError as err
from zvmsdk import xcatclient

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
from zvmsdk.exception import ZVMVolumeError


class _BaseConfiguratorTestCase(unittest.TestCase):

    def setUp(self):
        self._base_cnf = volumeop._BaseConfigurator()

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


class _xCATProxyTestCase(unittest.TestCase):

    def setUp(self):
        self._proxy = volumeop._xCATProxy()

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chvm')
    def test_dedicate_device(self, _xcat_chvm):
        inst = {NAME: 'inst1'}
        device = '1faa'
        _xcat_chvm.return_value = None
        body = ['--dedicatedevice 1faa 1faa 0']

        self._proxy.dedicate_device(inst, device)
        _xcat_chvm.assert_called_once_with(inst[NAME], body)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chvm')
    def test_undedicate_device(self, _xcat_chvm):
        inst = {NAME: 'inst1'}
        device = '1faa'
        _xcat_chvm.return_value = None
        body = ['--undedicatedevice 1faa']

        self._proxy.undedicate_device(inst, device)
        _xcat_chvm.assert_called_once_with(inst[NAME], body)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chhy')
    def test_add_zfcp_to_pool(self, _xcat_chhy):
        _xcat_chhy.return_value = None
        body = ['--addzfcp2pool zvmsdk free '
                '5005600670078008 0110022003300440 1G 1faa']

        self._proxy.add_zfcp_to_pool('1faa',
                                     '5005600670078008',
                                     '0110022003300440',
                                     '1G')
        _xcat_chhy.assert_called_once_with(body)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chhy')
    def test_remove_zfcp_from_pool(self, _xcat_chhy):
        _xcat_chhy.return_value = None
        body = ['--removezfcpfrompool zvmsdk '
                '0110022003300440 5005600670078008']

        self._proxy.remove_zfcp_from_pool('5005600670078008',
                                          '0110022003300440')
        _xcat_chhy.assert_called_once_with(body)

    @mock.patch.object(xcatclient, 'xcat_request')
    @mock.patch.object(utils.get_xcat_url(), 'chhv')
    def test_xcat_chhy(self, chhv, xcat_request):
        url = '/chhypervisor/' + CONF.zvm.host
        body = '[body]'
        chhv.return_value = url
        xcat_request.return_value = None

        self._proxy._xcat_chhy(body)
        chhv.assert_called_once_with('/' + CONF.zvm.host)
        xcat_request.assert_called_once_with('PUT', url, body)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chhy')
    def test_allocate_zfcp(self, _xcat_chhy):
        inst = {NAME: 'inst1'}
        _xcat_chhy.return_value = None
        body = ['--reservezfcp zvmsdk used inst1 '
                '1faa 1G 5005600670078008 0110022003300440']

        self._proxy.allocate_zfcp(inst,
                                  '1faa',
                                  '1G',
                                  '5005600670078008',
                                  '0110022003300440')
        _xcat_chhy.assert_called_once_with(body)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chvm')
    def test_remove_zfcp(self, _xcat_chvm):
        inst = {NAME: 'inst1'}
        body = ['--removezfcp 1faa 5005600670078008 0110022003300440 1']
        _xcat_chvm.return_value = None

        self._proxy.remove_zfcp(inst,
                                '1faa',
                                '5005600670078008',
                                '0110022003300440')
        _xcat_chvm.assert_called_once_with(inst[NAME], body)

    @mock.patch.object(volumeop._xCATProxy, '_get_mountpoint_parms')
    @mock.patch.object(volumeop._xCATProxy, '_send_notice')
    @mock.patch.object(volumeop._xCATProxy, '_get_volume_parms')
    def test_notice_attach(self, _get_volume_parms,
                           _send_notice,
                           _get_mountpoint_parms):
        inst = {NAME: 'inst1'}
        _get_volume_parms.return_value = 'fake_volume_parms'
        _send_notice.return_value = None
        _get_mountpoint_parms.return_value = 'fake_mp_parms'

        self._proxy.notice_attach(inst,
                                  '1faa',
                                  '5005600670078008',
                                  '0110022003300440',
                                  'vda',
                                  'rhel7')
        _get_volume_parms.assert_called_once_with('addScsiVolume',
                                                  '1faa',
                                                  '5005600670078008',
                                                  '0110022003300440')
        _get_mountpoint_parms.assert_called_once_with('createfilesysnode',
                                                      '1faa',
                                                      '5005600670078008',
                                                      '0110022003300440',
                                                      'vda',
                                                      'rhel7')
        calls = [mock.call(inst, 'fake_volume_parms'),
                 mock.call(inst, 'fake_mp_parms')]
        _send_notice.assert_has_calls(calls)

    @mock.patch.object(volumeop._xCATProxy, '_get_mountpoint_parms')
    @mock.patch.object(volumeop._xCATProxy, '_send_notice')
    @mock.patch.object(volumeop._xCATProxy, '_get_volume_parms')
    def test_notice_detach(self, _get_volume_parms,
                           _send_notice,
                           _get_mountpoint_parms):
        inst = {NAME: 'inst1'}
        _get_volume_parms.return_value = 'fake_volume_parms'
        _send_notice.return_value = None
        _get_mountpoint_parms.return_value = 'fake_mp_parms'

        self._proxy.notice_detach(inst,
                                  '1faa',
                                  '5005600670078008',
                                  '0110022003300440',
                                  'vda',
                                  'rhel7')
        _get_volume_parms.assert_called_once_with('removeScsiVolume',
                                                  '1faa',
                                                  '5005600670078008',
                                                  '0110022003300440')
        _get_mountpoint_parms.assert_called_once_with('removefilesysnode',
                                                      '1faa',
                                                      '5005600670078008',
                                                      '0110022003300440',
                                                      'vda',
                                                      'rhel7')
        calls = [mock.call(inst, 'fake_volume_parms'),
                 mock.call(inst, 'fake_mp_parms')]
        _send_notice.assert_has_calls(calls)

    def test_get_volume_parms(self):
        expected = ('action=test '
                    'fcpAddr=1faa,1fbb '
                    'wwpn=5005600670078008,5005600670079009 '
                    'lun=0110022003300440')
        self.assertEqual(self._proxy._get_volume_parms(
                                'test',
                                '1faa;1fbb',
                                '5005600670078008;5005600670079009',
                                '0110022003300440'),
                         expected)

    @mock.patch.object(volumeop._xCATProxy, '_xcat_chvm')
    def test_send_notice(self, _xcat_chvm):
        _xcat_chvm.return_value = None
        body = ['--aemod setupDisk parms']
        inst = {NAME: 'inst1'}
        self._proxy._send_notice(inst, 'parms')
        _xcat_chvm.assert_called_once_with(inst[NAME], body)

    @mock.patch.object(xcatclient, 'xcat_request')
    @mock.patch.object(utils.get_xcat_url(), 'chvm')
    def test_xcat_chvm(self, chvm, xcat_request):
        url = '/chvm/node'
        body = '[body]'
        chvm.return_value = url
        xcat_request.return_value = None

        self._proxy._xcat_chvm('node', body)
        chvm.assert_called_once_with('/node')
        xcat_request.assert_called_once_with('PUT', url, body)

    @mock.patch.object(dist.LinuxDistManager, 'get_linux_dist')
    def test_get_mountpoint_parms(self, get_linux_dist):
        distro = dist.rhel7
        get_linux_dist.return_value = distro
        distro.assemble_zfcp_srcdev = mock.MagicMock(return_value='zfcp_dev')

        expected = 'action=createfilesysnode tgtFile=vda srcFile=zfcp_dev'
        self.assertEqual(self._proxy._get_mountpoint_parms(
                                'createfilesysnode',
                                '1faa;1fbb',
                                '5005600670078008;5005600670079009',
                                '0110022003300440',
                                'vda',
                                'rhel7'),
                         expected)
        get_linux_dist.assert_called_once_with('rhel7')
        distro.assemble_zfcp_srcdev.assert_called_once_with(
                                        '1faa,1fbb',
                                        '5005600670078008,5005600670079009',
                                        '0110022003300440')
        get_linux_dist.reset_mock()
        distro.assemble_zfcp_srcdev.reset_mock()

        expected = 'action=removefilesysnode tgtFile=vda'
        self.assertEqual(self._proxy._get_mountpoint_parms(
                                'removefilesysnode',
                                '1faa;1fbb',
                                '5005600670078008;5005600670079009',
                                '0110022003300440',
                                'vda',
                                'rhel7'),
                         expected)
        get_linux_dist.assert_not_called()
        distro.assemble_zfcp_srcdev.assert_not_called()


class _Configurator_SLES12TestCases(unittest.TestCase):

    def setUp(self):
        self._conf = volumeop._Configurator_SLES12()

    @mock.patch.object(volumeop._Configurator_SLES12,
                       '_config_fc_attach_inactive_with_xCAT')
    def test_config_attach_inactive_with_xCAT(self, _config_fc):
        _config_fc.return_value = None
        volume = {LUN: 'abcdef0987654321', TYPE: 'fc'}
        conn_info = {PROTOCOL: 'fc'}
        self.assertRaises(ZVMVolumeError,
                          self._conf._config_attach_inactive_with_xCAT,
                          None,
                          volume,
                          conn_info)

        volume = {LUN: 'abcdef0987654321', TYPE: 'fc', SIZE: '1G'}
        self._conf._config_attach_inactive_with_xCAT(None, volume, conn_info)
        _config_fc.assert_called_once_with(None, volume, conn_info)

        conn_info = {PROTOCOL: 'iSCSI'}
        self.assertRaises(NotImplementedError,
                          self._conf._config_attach_inactive_with_xCAT,
                          None,
                          volume,
                          conn_info)

    @mock.patch.object(volumeop._xCATProxy, 'notice_attach')
    @mock.patch.object(volumeop._xCATProxy, 'allocate_zfcp')
    @mock.patch.object(volumeop._xCATProxy, 'add_zfcp_to_pool')
    @mock.patch.object(volumeop._xCATProxy, 'dedicate_device')
    def test_config_fc_attach_inactive_with_xCAT(self, dedicate_device,
                                                 add_zfcp_to_pool,
                                                 allocate_zfcp,
                                                 notice_attach):
        dedicate_device.return_value = None
        add_zfcp_to_pool.return_value = None
        allocate_zfcp.return_value = None
        notice_attach.return_value = None
        inst = {NAME: 'inst1', OS_TYPE: 'sles12'}
        conn_info = {DEDICATE: ['1faa', '1fbb'],
                     FCPS: ['1faa', '1fbb'],
                     WWPNS: ['1234567890abcdea', '1234567890abcdeb'],
                     ALIAS: 'sles12'}
        volume = {SIZE: '1G', LUN: 'abcdef0987654321'}
        formated_wwpns = '1234567890abcdea;1234567890abcdeb'

        calls = [mock.call(inst, '1faa'), mock.call(inst, '1fbb')]
        self._conf._config_fc_attach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        dedicate_device.assert_has_calls(calls)
        add_zfcp_to_pool.assert_called_once_with('1faa;1fbb',
                                                 formated_wwpns,
                                                 'abcdef0987654321',
                                                 '1G')
        allocate_zfcp.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              '1G',
                                              formated_wwpns,
                                              'abcdef0987654321')
        notice_attach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              'abcdef0987654321',
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])

        add_zfcp_to_pool.reset_mock()
        allocate_zfcp.reset_mock()
        notice_attach.reset_mock()
        conn_info.pop(DEDICATE)
        self._conf._config_fc_attach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        add_zfcp_to_pool.assert_called_once_with('1faa;1fbb',
                                                 formated_wwpns,
                                                 'abcdef0987654321',
                                                 '1G')
        allocate_zfcp.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              '1G',
                                              formated_wwpns,
                                              'abcdef0987654321')
        notice_attach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              'abcdef0987654321',
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])

    @mock.patch.object(volumeop._Configurator_SLES12,
                       '_config_fc_detach_inactive_with_xCAT')
    def test_config_detach_inactive_with_xCAT(self, _config_fc):
        _config_fc.return_value = None
        conn_info = {PROTOCOL: 'fc'}
        self._conf._config_detach_inactive_with_xCAT(None, None, conn_info)
        _config_fc.assert_called_once_with(None, None, conn_info)

        conn_info = {PROTOCOL: 'iSCSI'}
        self.assertRaises(NotImplementedError,
                          self._conf._config_detach_inactive_with_xCAT,
                          None,
                          None,
                          conn_info)

    @mock.patch.object(volumeop._xCATProxy, 'undedicate_device')
    @mock.patch.object(volumeop._xCATProxy, 'notice_detach')
    @mock.patch.object(volumeop._xCATProxy, 'remove_zfcp_from_pool')
    @mock.patch.object(volumeop._xCATProxy, 'remove_zfcp')
    def test_config_fc_detach_inactive_with_xCAT(self, remove_zfcp,
                                                 remove_zfcp_from_pool,
                                                 notice_detach,
                                                 undedicate_device):
        remove_zfcp.return_value = None
        remove_zfcp_from_pool.return_value = None
        notice_detach.return_value = None
        undedicate_device.return_value = None
        inst = {NAME: 'inst1', OS_TYPE: 'sles12'}
        conn_info = {DEDICATE: ['1faa', '1fbb'],
                     FCPS: ['1faa', '1fbb'],
                     WWPNS: ['1234567890abcdea', '1234567890abcdeb'],
                     ALIAS: 'sles12'}
        volume = {LUN: 'abcdef0987654321'}
        formated_wwpns = '1234567890abcdea;1234567890abcdeb'

        calls = [mock.call(inst, '1faa'), mock.call(inst, '1fbb')]
        self._conf._config_fc_detach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        remove_zfcp.assert_called_once_with(inst,
                                            '1faa;1fbb',
                                            formated_wwpns,
                                            volume[LUN])
        remove_zfcp_from_pool.assert_called_once_with(formated_wwpns,
                                                      volume[LUN])
        notice_detach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              volume[LUN],
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])
        undedicate_device.assert_has_calls(calls)

        remove_zfcp.reset_mock()
        remove_zfcp_from_pool.reset_mock()
        notice_detach.reset_mock()
        conn_info.pop(DEDICATE)
        self._conf._config_fc_detach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        remove_zfcp.assert_called_once_with(inst,
                                            '1faa;1fbb',
                                            formated_wwpns,
                                            volume[LUN])
        remove_zfcp_from_pool.assert_called_once_with(formated_wwpns,
                                                      volume[LUN])
        notice_detach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              volume[LUN],
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])


class _Configurator_RHEL7TestCases(unittest.TestCase):

    def setUp(self):
        self._conf = volumeop._Configurator_RHEL7()

    @mock.patch.object(volumeop._Configurator_RHEL7,
                       '_config_fc_attach_inactive_with_xCAT')
    def test_config_attach_inactive_with_xCAT(self, _config_fc):
        _config_fc.return_value = None
        volume = {LUN: 'abcdef0987654321', TYPE: 'fc'}
        conn_info = {PROTOCOL: 'fc'}
        self.assertRaises(ZVMVolumeError,
                          self._conf._config_attach_inactive_with_xCAT,
                          None,
                          volume,
                          conn_info)

        volume = {LUN: 'abcdef0987654321', TYPE: 'fc', SIZE: '1G'}
        self._conf._config_attach_inactive_with_xCAT(None, volume, conn_info)
        _config_fc.assert_called_once_with(None, volume, conn_info)

        conn_info = {PROTOCOL: 'iSCSI'}
        self.assertRaises(NotImplementedError,
                          self._conf._config_attach_inactive_with_xCAT,
                          None,
                          volume,
                          conn_info)

    @mock.patch.object(volumeop._xCATProxy, 'notice_attach')
    @mock.patch.object(volumeop._xCATProxy, 'allocate_zfcp')
    @mock.patch.object(volumeop._xCATProxy, 'add_zfcp_to_pool')
    @mock.patch.object(volumeop._xCATProxy, 'dedicate_device')
    def test_config_fc_attach_inactive_with_xCAT(self, dedicate_device,
                                                 add_zfcp_to_pool,
                                                 allocate_zfcp,
                                                 notice_attach):
        dedicate_device.return_value = None
        add_zfcp_to_pool.return_value = None
        allocate_zfcp.return_value = None
        notice_attach.return_value = None
        inst = {NAME: 'inst1', OS_TYPE: 'rhel7'}
        conn_info = {DEDICATE: ['1faa', '1fbb'],
                     FCPS: ['1faa', '1fbb'],
                     WWPNS: ['1234567890abcdea', '1234567890abcdeb'],
                     ALIAS: '/dev/vda'}
        volume = {SIZE: '1G', LUN: 'abcdef0987654321'}
        formated_wwpns = '1234567890abcdea;1234567890abcdeb'

        calls = [mock.call(inst, '1faa'), mock.call(inst, '1fbb')]
        self._conf._config_fc_attach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        dedicate_device.assert_has_calls(calls)
        add_zfcp_to_pool.assert_called_once_with('1faa;1fbb',
                                                 formated_wwpns,
                                                 'abcdef0987654321',
                                                 '1G')
        allocate_zfcp.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              '1G',
                                              formated_wwpns,
                                              'abcdef0987654321')
        notice_attach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              'abcdef0987654321',
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])

        add_zfcp_to_pool.reset_mock()
        allocate_zfcp.reset_mock()
        notice_attach.reset_mock()
        conn_info.pop(DEDICATE)
        self._conf._config_fc_attach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        add_zfcp_to_pool.assert_called_once_with('1faa;1fbb',
                                                 formated_wwpns,
                                                 'abcdef0987654321',
                                                 '1G')
        allocate_zfcp.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              '1G',
                                              formated_wwpns,
                                              'abcdef0987654321')
        notice_attach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              'abcdef0987654321',
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])

    @mock.patch.object(volumeop._Configurator_RHEL7,
                       '_config_fc_detach_inactive_with_xCAT')
    def test_config_detach_inactive_with_xCAT(self, _config_fc):
        _config_fc.return_value = None
        conn_info = {PROTOCOL: 'fc'}
        self._conf._config_detach_inactive_with_xCAT(None, None, conn_info)
        _config_fc.assert_called_once_with(None, None, conn_info)

        conn_info = {PROTOCOL: 'iSCSI'}
        self.assertRaises(NotImplementedError,
                          self._conf._config_detach_inactive_with_xCAT,
                          None,
                          None,
                          conn_info)

    @mock.patch.object(volumeop._xCATProxy, 'undedicate_device')
    @mock.patch.object(volumeop._xCATProxy, 'notice_detach')
    @mock.patch.object(volumeop._xCATProxy, 'remove_zfcp_from_pool')
    @mock.patch.object(volumeop._xCATProxy, 'remove_zfcp')
    def test_config_fc_detach_inactive_with_xCAT(self, remove_zfcp,
                                                 remove_zfcp_from_pool,
                                                 notice_detach,
                                                 undedicate_device):
        remove_zfcp.return_value = None
        remove_zfcp_from_pool.return_value = None
        notice_detach.return_value = None
        undedicate_device.return_value = None
        inst = {NAME: 'inst1', OS_TYPE: 'rhel7'}
        conn_info = {DEDICATE: ['1faa', '1fbb'],
                     FCPS: ['1faa', '1fbb'],
                     WWPNS: ['1234567890abcdea', '1234567890abcdeb'],
                     ALIAS: '/dev/vda'}
        volume = {LUN: 'abcdef0987654321'}
        formated_wwpns = '1234567890abcdea;1234567890abcdeb'

        calls = [mock.call(inst, '1faa'), mock.call(inst, '1fbb')]
        self._conf._config_fc_detach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        remove_zfcp.assert_called_once_with(inst,
                                            '1faa;1fbb',
                                            formated_wwpns,
                                            volume[LUN])
        remove_zfcp_from_pool.assert_called_once_with(formated_wwpns,
                                                      volume[LUN])
        notice_detach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              volume[LUN],
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])
        undedicate_device.assert_has_calls(calls)

        remove_zfcp.reset_mock()
        remove_zfcp_from_pool.reset_mock()
        notice_detach.reset_mock()
        conn_info.pop(DEDICATE)
        self._conf._config_fc_detach_inactive_with_xCAT(inst,
                                                        volume,
                                                        conn_info)
        remove_zfcp.assert_called_once_with(inst,
                                            '1faa;1fbb',
                                            formated_wwpns,
                                            volume[LUN])
        remove_zfcp_from_pool.assert_called_once_with(formated_wwpns,
                                                      volume[LUN])
        notice_detach.assert_called_once_with(inst,
                                              '1faa;1fbb',
                                              formated_wwpns,
                                              volume[LUN],
                                              conn_info[ALIAS],
                                              inst[OS_TYPE])


class VolumeOpTestCase(unittest.TestCase):

    def setUp(self):
        self._vol_op = volumeop.VolumeOperator()

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
        self.assertRaises(err, self._vol_op._validate_instance, None)

        inst = ['inst1', 'sles12']
        self.assertRaises(err, self._vol_op._validate_instance, inst)

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
        self.assertRaises(err, self._vol_op._validate_volume, None)

        volume = ['fc', 'abCDEF0987654321']
        self.assertRaises(err, self._vol_op._validate_volume, volume)

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
