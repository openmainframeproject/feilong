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


from zvmsdk import config
from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk.tests.unit.db_contract.fcp import FCPContract
from zvmsdk.tests.unit.db_contract.fcp import OTHER
from zvmsdk.tests.unit.db_contract.fcp import PCHID_INFO
from zvmsdk.tests.unit.db_contract.fcp import T1
from zvmsdk.tests.unit.db_contract.fcp import T2
from zvmsdk.tests.unit.db_contract.fcp import USER
from zvmsdk.tests.unit.db_contract.fcp import fcp_row
from zvmsdk.tests.unit.db_contract.fcp import zvm_fcp
from zvmsdk.tests.unit.db_contract.fixture import ContractBase


CONF = config.CONF
ALL_FCPS = ('1a00', '1a01', '1b00', '1b01')


def zvm_fcps(*fcp_ids, **kwargs):
    """A zvm_fcps argument, values as lists the way they arrive over RPC."""
    return {f: list(zvm_fcp(f, **kwargs)) for f in fcp_ids}


class FcpOperationsContract(ContractBase):

    # reuse the FCP data helpers
    _insert = FCPContract._insert
    _create = FCPContract._create
    _setup_template = FCPContract._setup_template
    _all = FCPContract._all
    _usage = FCPContract._usage

    def setUp(self):
        super(FcpOperationsContract, self).setUp()
        self.db = self.backend.fcp()
        self.ops = self.backend.fcp_ops()
        old = CONF.volume.get_fcp_pair_with_same_index
        CONF.volume.get_fcp_pair_with_same_index = 0
        self.addCleanup(setattr, CONF.volume, 'get_fcp_pair_with_same_index',
                        old)

    def _allocate(self, tmpl=T1, assigner=USER, sp_name=None, fcps=ALL_FCPS):
        return self.ops.allocate(assigner, tmpl, sp_name, PCHID_INFO,
                                 zvm_fcps=zvm_fcps(*fcps))

    def test_implements_interface(self):
        self.assertIsInstance(self.ops, db_interface.FcpOperationsBase)

    def test_increase_and_decrease_connections(self):
        self._setup_template()
        self.db.reserve_fcps(['1a00', '1b00'], USER, T1)
        self.assertEqual({'1a00': 1, '1b00': 1},
                         self.ops.increase_connections(['1a00', '1b00'], USER))
        self.assertEqual({'1a00': 2},
                         self.ops.increase_connections(['1a00'], USER))
        self.assertEqual({'1a00': 1, '1b00': 0, '1b01': 0, 'ffff': 0},
                         self.ops.decrease_connections(
                             ['1a00', '1b00', '1b01', 'ffff']))
        self.assertEqual((USER, 1, 1, T1), self._usage('1a00'))

    def test_increase_connections_is_atomic(self):
        self._setup_template()
        self.db.reserve_fcps(['1a00'], USER, T1)
        # 1b00 is not assigned to USER, so nothing changes
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.ops.increase_connections, ['1a00', '1b00'],
                          USER)
        self.assertEqual(0, self.db.get_connections_from_fcp('1a00'))

    def test_allocate_template_not_exist(self):
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.ops.allocate, USER, T1, None, PCHID_INFO)

    def test_allocate_no_default_template(self):
        self._create(T1)
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.ops.allocate, USER, None, 'sp1', PCHID_INFO)

    def test_allocate_missing_pchid_info(self):
        self._setup_template()
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.ops.allocate, USER, T1, None,
                          {'02E4': {'allocated': 0, 'max': 128}})

    def test_allocate_first_pass(self):
        self._setup_template()
        self.assertEqual((db_interface.NEED_ZVM_SYNC, T1),
                         self.ops.allocate(USER, T1, None, PCHID_INFO))
        # nothing changed
        self.assertEqual({0}, {r['reserved'] for r in self._all().values()})

    def test_allocate_first_pass_resolves_default_template(self):
        self._setup_template(tmpl=T1, host_default=True)
        self._create(T2, sp=['sp1'])
        self.assertEqual((db_interface.NEED_ZVM_SYNC, T2),
                         self.ops.allocate(USER, None, 'sp1', PCHID_INFO))
        self.assertEqual((db_interface.NEED_ZVM_SYNC, T1),
                         self.ops.allocate(USER, None, 'sp9', PCHID_INFO))
        self.assertEqual((db_interface.NEED_ZVM_SYNC, T1),
                         self.ops.allocate(USER, None, None, PCHID_INFO))

    def test_allocate_second_pass(self):
        # 1b00 and 1b01 are only known to z/VM so far
        self._insert('1a00', '1a01')
        self._create()
        changed, fcp_list, tmpl, reason = self._allocate()
        self.assertEqual((True, T1, ''), (changed, tmpl, reason))
        self.assertEqual([0, 1], sorted(f['path'] for f in fcp_list))
        fcp_ids = sorted(f['fcp_id'].lower() for f in fcp_list)
        rows = self._all()
        self.assertEqual(sorted(ALL_FCPS), sorted(rows))
        for fcp_id in fcp_ids:
            self.assertEqual((USER, 1, 0, T1), self._usage(fcp_id))
        self.assertEqual(2, sum(r['reserved'] for r in rows.values()))

    def test_allocate_returns_existing_allocation(self):
        self._setup_template()
        first = self._allocate()[1]
        # a second request, or a second pass after a concurrent
        # allocation, gets the same FCPs without re-syncing
        changed, fcp_list, tmpl, reason = self.ops.allocate(
            USER, T1, None, PCHID_INFO, zvm_fcps={})
        self.assertEqual((False, T1, ''), (changed, tmpl, reason))
        self.assertEqual(sorted(f['fcp_id'].lower() for f in first),
                         sorted(f['fcp_id'].lower() for f in fcp_list))
        self.assertEqual(sorted(ALL_FCPS), sorted(self._all()))
        # the first pass returns them too
        self.assertFalse(self.ops.allocate(USER, T1, None, PCHID_INFO)[0])

    def test_allocate_no_free_fcp(self):
        self._setup_template()
        changed, fcp_list, tmpl, reason = self.ops.allocate(
            USER, T1, None, PCHID_INFO,
            zvm_fcps=zvm_fcps(*ALL_FCPS, state='active', owner=OTHER))
        self.assertEqual((False, [], T1), (changed, fcp_list, tmpl))
        self.assertTrue(reason)
        # the sync is kept
        self.assertEqual({'active'}, {r['state'] for r in
                                      self._all().values()})

    def test_release(self):
        self._setup_template()
        self.db.reserve_fcps(['1a00', '1b00'], USER, T1)
        self.ops.increase_connections(['1b00'], USER)
        changed, fcp_list, released = self.ops.release(USER, T1)
        self.assertTrue(changed)
        self.assertEqual(['1a00', '1b00'],
                         sorted(f['fcp_id'] for f in fcp_list))
        self.assertEqual(['1a00'], released)
        self.assertEqual((USER, 0, 0, ''), self._usage('1a00'))
        self.assertEqual((USER, 1, 1, T1), self._usage('1b00'))

    def test_release_nothing_reserved(self):
        self._setup_template()
        self.assertEqual((False, [], []), self.ops.release(USER, T1))

    def test_release_errors(self):
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.ops.release, USER, T1)
        self.assertRaises(exception.SDKVolumeOperationError,
                          self.ops.release, USER, None)

    def test_sync_with_zvm(self):
        self._insert('1a00', '1a01', '1b00', '1b01')
        self.db.reserve_fcps(['1a00', '1b00'], USER, T1)
        self.ops.increase_connections(['1a00', '1b00'], USER)
        fcps = zvm_fcps('1a00', state='offline', npiv='ffff00000000')
        fcps.update(zvm_fcps('1b01', npiv='ffff00000003'))
        fcps.update(zvm_fcps('1c00'))
        original = {k: list(v) for k, v in fcps.items()}
        self.ops.sync_with_zvm(fcps)
        rows = self._all()
        # in use: keeps its DB WWPN, takes the z/VM state
        self.assertEqual(fcp_row('1a00', USER, 1, 1, T1, state='offline'),
                         rows['1a00'])
        # gone from z/VM: deleted if free, marked notfound if in use
        self.assertNotIn('1a01', rows)
        self.assertEqual(fcp_row('1b00', USER, 1, 1, T1, state='notfound'),
                         rows['1b00'])
        # free: takes the z/VM WWPN
        self.assertEqual('ffff00000003', rows['1b01']['wwpn_npiv'])
        # new on z/VM: inserted
        self.assertEqual(fcp_row('1c00'), rows['1c00'])
        # the caller's dict is not changed
        self.assertEqual(original, fcps)

    def test_get_pchid_usage(self):
        self.assertEqual(([], {}), self.ops.get_pchid_usage())
        self._setup_template()
        self.db.reserve_fcps(['1a00'], USER, T1)
        all_pchids, inuse_pchids = self.ops.get_pchid_usage()
        self.assertEqual(['02E4', '03FC'], sorted(all_pchids))
        self.assertEqual(['02E4'], list(inuse_pchids))
