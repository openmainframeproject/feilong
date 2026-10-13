#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0
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

from zvmsdk import config
from zvmsdk import database
from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk import fcp_ops
from zvmsdk import volumeop
from zvmsdk.tests.unit import base


CONF = config.CONF
TMPL = 'tmpl0001'
USER = 'USER0001'
PCHID_INFO = {'02E4': {'allocated': 0, 'max': 128}}


def _zvm_fcp(fcp_id, state='free', owner='NONE', npiv=None, phy='c05076de33002641'):
    """A zvm_fcps value, as a list the way it arrives over RPC."""
    return [fcp_id, npiv or 'c05076de3300%s' % fcp_id, phy, '27', '02E4',
            state, owner]


class FcpOpsTestCase(base.SDKTestCase):
    """TransactionalFcpOperations against the sqlite FCP DB."""

    def setUp(self):
        super(FcpOpsTestCase, self).setUp()
        self.ops = database.get_db_backend().fcp_ops()
        self.db = self.ops.db
        self._purge()
        self.addCleanup(self._purge)
        self.old_same_index = CONF.volume.get_fcp_pair_with_same_index
        CONF.volume.get_fcp_pair_with_same_index = 0
        self.addCleanup(setattr, CONF.volume, 'get_fcp_pair_with_same_index',
                        self.old_same_index)

    def _purge(self):
        with database.get_fcp_conn() as conn:
            for table in ('fcp', 'template', 'template_fcp_mapping',
                          'template_sp_mapping'):
                conn.execute("DELETE FROM %s" % table)

    def _add_template(self, fcp_paths, is_default=1):
        """fcp_paths: [[fcp_id, ...] per path]"""
        with database.get_fcp_conn() as conn:
            conn.execute("INSERT INTO template (id, name, description, "
                         "is_default) VALUES (?, ?, ?, ?)",
                         (TMPL, 'name', 'desc', is_default))
            conn.executemany("INSERT INTO template_fcp_mapping "
                             "(fcp_id, tmpl_id, path) VALUES (?, ?, ?)",
                             [(fcp, TMPL, path)
                              for path, fcps in enumerate(fcp_paths)
                              for fcp in fcps])

    def _add_fcps(self, rows):
        """rows: (fcp_id, assigner_id, connections, reserved, state)"""
        with database.get_fcp_conn() as conn:
            conn.executemany(
                "INSERT INTO fcp (fcp_id, assigner_id, connections, "
                "reserved, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner, "
                "tmpl_id) VALUES (?, ?, ?, ?, ?, ?, '27', '02E4', ?, 'NONE', ?)",
                [(f, a, c, r, 'c05076de3300%s' % f, 'c05076de33002641', s,
                  TMPL if r else '') for f, a, c, r, s in rows])

    def _fcp(self, fcp_id):
        return {r['fcp_id']: r for r in self.db.get_all()}.get(fcp_id)

    def test_implements_interface(self):
        self.assertIsInstance(self.ops, db_interface.FcpOperationsBase)
        self.assertIsInstance(self.ops, fcp_ops.TransactionalFcpOperations)

    def test_allocate_first_pass_needs_zvm_sync(self):
        self._add_template([['1a00'], ['1b00']])
        self._add_fcps([('1a00', '', 0, 0, 'free'), ('1b00', '', 0, 0, 'free')])
        result = self.ops.allocate(USER, TMPL, None, PCHID_INFO)
        self.assertEqual((db_interface.NEED_ZVM_SYNC, TMPL), result)
        self.assertEqual(0, self._fcp('1a00')['reserved'])
        self.assertEqual(0, self._fcp('1b00')['reserved'])

    def test_allocate_first_pass_resolves_default_template(self):
        self._add_template([['1a00']])
        result = self.ops.allocate(USER, None, None, PCHID_INFO)
        self.assertEqual((db_interface.NEED_ZVM_SYNC, TMPL), result)

    def test_allocate_template_not_exist(self):
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               r"FCP Multipath Template \(id: nope\) does "
                               "not exist",
                               self.ops.allocate, USER, 'nope', None,
                               PCHID_INFO)

    def test_allocate_second_pass_syncs_and_reserves(self):
        self._add_template([['1a00'], ['1b00']])
        # 1b00 is only known to z/VM so far
        self._add_fcps([('1a00', '', 0, 0, 'free')])
        zvm_fcps = {'1a00': _zvm_fcp('1a00'), '1b00': _zvm_fcp('1b00')}
        changed, fcp_list, tmpl, reason = self.ops.allocate(
            USER, TMPL, None, PCHID_INFO, zvm_fcps=zvm_fcps)
        self.assertTrue(changed)
        self.assertEqual(TMPL, tmpl)
        self.assertEqual('', reason)
        # get_fcp_devices returns uppercase FCP IDs
        self.assertEqual(['1A00', '1B00'],
                         sorted(f['fcp_id'] for f in fcp_list))
        for fcp in ('1a00', '1b00'):
            self.assertEqual(1, self._fcp(fcp)['reserved'])
            self.assertEqual(USER, self._fcp(fcp)['assigner_id'])

    def test_allocate_second_pass_reuses_concurrent_allocation(self):
        # another request allocated FCPs between the two passes
        self._add_template([['1a00'], ['1b00']])
        self._add_fcps([('1a00', USER, 0, 1, 'free'),
                        ('1b00', USER, 0, 1, 'free'),
                        ('1a01', '', 0, 0, 'free')])
        sync = mock.Mock()
        with mock.patch.object(self.ops, 'sync_with_zvm', sync):
            changed, fcp_list, tmpl, reason = self.ops.allocate(
                USER, TMPL, None, PCHID_INFO, zvm_fcps={})
        self.assertFalse(changed)
        self.assertEqual(['1a00', '1b00'],
                         sorted(f['fcp_id'] for f in fcp_list))
        sync.assert_not_called()

    def test_allocate_rolls_back_sync_on_failure(self):
        self._add_template([['1a00'], ['1b00']])
        zvm_fcps = {'1a00': _zvm_fcp('1a00'), '1b00': _zvm_fcp('1b00')}
        with mock.patch.object(self.db, 'reserve_fcps',
                               side_effect=exception.SDKInternalError('boom')):
            self.assertRaisesRegex(exception.SDKVolumeOperationError,
                                   'Failed to reserve FCP devices',
                                   self.ops.allocate, USER, TMPL, None,
                                   PCHID_INFO, zvm_fcps=zvm_fcps)
        # the FCPs inserted by the sync were rolled back with it
        self.assertEqual([], list(self.db.get_all()))

    def test_allocate_no_free_fcp(self):
        self._add_template([['1a00'], ['1b00']])
        zvm_fcps = {'1a00': _zvm_fcp('1a00', state='active', owner='X'),
                    '1b00': _zvm_fcp('1b00')}
        changed, fcp_list, tmpl, reason = self.ops.allocate(
            USER, TMPL, None, PCHID_INFO, zvm_fcps=zvm_fcps)
        self.assertEqual((False, [], TMPL), (changed, fcp_list, tmpl))
        self.assertTrue(reason)

    def test_sync_with_zvm(self):
        self._add_fcps([('1a00', USER, 1, 1, 'active'),   # in use, WWPN moved
                        ('1a01', '', 0, 0, 'free'),       # gone, free
                        ('1a02', USER, 1, 1, 'active'),   # gone, in use
                        ('1a03', '', 0, 0, 'free')])      # free, WWPN moved
        zvm_fcps = {
            '1a00': _zvm_fcp('1a00', state='offline', npiv='ffff00000000'),
            '1a03': _zvm_fcp('1a03', npiv='ffff00000003'),
            '1a04': _zvm_fcp('1a04')}
        original = {k: list(v) for k, v in zvm_fcps.items()}
        self.ops.sync_with_zvm(zvm_fcps)
        # in-use FCP keeps its DB WWPN but gets the new state
        self.assertEqual('c05076de33001a00', self._fcp('1a00')['wwpn_npiv'])
        self.assertEqual('offline', self._fcp('1a00')['state'])
        self.assertIsNone(self._fcp('1a01'))
        self.assertEqual('notfound', self._fcp('1a02')['state'])
        self.assertEqual('ffff00000003', self._fcp('1a03')['wwpn_npiv'])
        self.assertEqual('free', self._fcp('1a04')['state'])
        # the caller's dict is not changed
        self.assertEqual(original, zvm_fcps)

    def test_release(self):
        self._add_template([['1a00'], ['1b00']])
        self._add_fcps([('1a00', USER, 0, 1, 'active'),
                        ('1b00', USER, 1, 1, 'active')])
        changed, fcp_list, released = self.ops.release(USER, TMPL)
        self.assertTrue(changed)
        self.assertEqual(['1a00', '1b00'],
                         sorted(f['fcp_id'] for f in fcp_list))
        self.assertEqual(['1a00'], released)
        self.assertEqual(0, self._fcp('1a00')['reserved'])
        self.assertEqual(1, self._fcp('1b00')['reserved'])

    def test_release_nothing_reserved(self):
        self._add_template([['1a00']])
        self.assertEqual((False, [], []), self.ops.release(USER, TMPL))

    def test_increase_and_decrease_connections(self):
        self._add_fcps([('1a00', USER, 0, 1, 'active')])
        self.assertEqual({'1a00': 1},
                         self.ops.increase_connections(['1a00'], USER))
        self.assertEqual({'1a00': 0, 'ffff': 0},
                         self.ops.decrease_connections(['1a00', 'ffff']))

    def test_get_pchid_usage(self):
        self._add_template([['1a00'], ['1b00']])
        self._add_fcps([('1a00', USER, 1, 1, 'active')])
        all_pchids, inuse_pchids = self.ops.get_pchid_usage()
        self.assertEqual(['02E4'], [p.upper() for p in all_pchids])
        self.assertEqual(['02E4'], [p.upper() for p in inuse_pchids])


class FcpManagerTwoPassTestCase(base.SDKTestCase):
    """FCPManager.allocate_fcp_devices drives the two-pass allocate."""

    @mock.patch("zvmsdk.utils.print_all_pchids", mock.Mock())
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUp(self):
        super(FcpManagerTwoPassTestCase, self).setUp()
        self.mgr = volumeop.FCPManager()
        self.mgr.fcp_ops = mock.Mock()

    @mock.patch("zvmsdk.volumeop.FCPManager._get_zvm_fcp_tuples")
    def test_no_zvm_query_when_already_allocated(self, get_zvm):
        expected = (False, ['row'], TMPL, '')
        self.mgr.fcp_ops.allocate.return_value = expected
        self.assertEqual(expected, self.mgr.allocate_fcp_devices(
            USER, TMPL, 'sp', PCHID_INFO))
        get_zvm.assert_not_called()
        self.mgr.fcp_ops.allocate.assert_called_once_with(
            USER, TMPL, 'sp', PCHID_INFO)

    @mock.patch("zvmsdk.volumeop.FCPManager._get_zvm_fcp_tuples")
    def test_zvm_query_then_second_pass(self, get_zvm):
        get_zvm.return_value = {'1a00': ('1a00',)}
        expected = (True, ['row'], 'resolved', '')
        self.mgr.fcp_ops.allocate.side_effect = [
            (db_interface.NEED_ZVM_SYNC, 'resolved'), expected]
        self.assertEqual(expected, self.mgr.allocate_fcp_devices(
            USER, None, 'sp', PCHID_INFO))
        get_zvm.assert_called_once_with()
        self.mgr.fcp_ops.allocate.assert_called_with(
            USER, 'resolved', 'sp', PCHID_INFO,
            zvm_fcps={'1a00': ('1a00',)})

    @mock.patch("zvmsdk.volumeop.FCPManager._get_zvm_fcp_tuples")
    def test_zvm_query_failure(self, get_zvm):
        get_zvm.side_effect = exception.SDKInternalError('smapi down')
        self.mgr.fcp_ops.allocate.return_value = (
            db_interface.NEED_ZVM_SYNC, TMPL)
        self.assertRaisesRegex(exception.SDKVolumeOperationError,
                               'Failed to reserve FCP devices.*smapi down',
                               self.mgr.allocate_fcp_devices,
                               USER, TMPL, 'sp', PCHID_INFO)
        self.assertEqual(1, self.mgr.fcp_ops.allocate.call_count)

    @mock.patch("zvmsdk.volumeop.FCPManager._sync_db_with_zvm")
    def test_release_syncs_only_when_released(self, sync):
        self.mgr.fcp_ops.release.return_value = (False, ['row'], [])
        self.assertEqual((False, ['row']),
                         self.mgr.release_fcp_devices(USER, TMPL))
        sync.assert_not_called()
        self.mgr.fcp_ops.release.return_value = (True, ['row'], ['1a00'])
        self.assertEqual((True, ['row']),
                         self.mgr.release_fcp_devices(USER, TMPL))
        sync.assert_called_once_with()

    def test_sync_fcp_table_with_zvm_passes_tuples(self):
        fcp = mock.Mock()
        fcp.to_tuple.return_value = ('1a00', 'n', 'p', '27', '02E4', 'free',
                                     'NONE')
        self.mgr.sync_fcp_table_with_zvm({'1a00': fcp})
        self.mgr.fcp_ops.sync_with_zvm.assert_called_once_with(
            {'1a00': ('1a00', 'n', 'p', '27', '02E4', 'free', 'NONE')})


class VolumeConnectorTestCase(base.SDKTestCase):

    @mock.patch("zvmsdk.utils.print_all_pchids", mock.Mock())
    @mock.patch("zvmsdk.volumeop.FCPManager.sync_db", mock.Mock())
    def setUp(self):
        super(VolumeConnectorTestCase, self).setUp()
        self.volumeops = volumeop.FCPVolumeManager()

    @mock.patch("zvmsdk.volumeop.FCPManager.allocate_fcp_devices")
    @mock.patch("zvmsdk.utils.get_zhypinfo")
    @mock.patch("zvmsdk.utils.get_zvm_name", mock.Mock(return_value='zvm'))
    def test_zhypinfo_failure_leaves_db_unchanged(self, get_zhypinfo,
                                                  allocate):
        get_zhypinfo.side_effect = exception.SDKInternalError('no qclib')
        self.assertRaises(exception.SDKInternalError,
                          self.volumeops.get_volume_connector,
                          USER, True, TMPL, 'sp', PCHID_INFO)
        allocate.assert_not_called()
