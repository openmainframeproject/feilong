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


from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk import utils
from zvmsdk.tests.unit.db_contract.fixture import ContractBase


T1 = 'tmpl0001'
T2 = 'tmpl0002'
USER = 'USER0001'
OTHER = 'USER0002'
PCHID_OF = {'1a': '02e4', '1b': '03fc', '1c': '05a0'}
PCHID_INFO = {'02E4': {'allocated': 0, 'max': 128},
              '03FC': {'allocated': 0, 'max': 128},
              '05A0': {'allocated': 0, 'max': 128}}
# path 0: 1a00-1a01 (PCHID 02e4), path 1: 1b00-1b01 (PCHID 03fc)
PATHS = {0: {'1a00', '1a01'}, 1: {'1b00', '1b01'}}


def zvm_fcp(fcp_id, state='free', owner='NONE', npiv=None):
    """(fcp_id, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner)"""
    pchid = PCHID_OF[fcp_id[:2].lower()]
    return (fcp_id, npiv or 'c05076de3300%s' % fcp_id,
            'c05076de3300%s' % pchid, '27', pchid, state, owner)


def fcp_row(fcp_id, assigner_id='', connections=0, reserved=0, tmpl_id='',
            state='free', owner='NONE'):
    """A row of get_all() as a dict."""
    _, npiv, phy, chpid, pchid, _, _ = zvm_fcp(fcp_id)
    return {'fcp_id': fcp_id, 'assigner_id': assigner_id,
            'connections': connections, 'reserved': reserved,
            'wwpn_npiv': npiv, 'wwpn_phy': phy, 'chpid': chpid,
            'pchid': pchid, 'state': state, 'owner': owner,
            'tmpl_id': tmpl_id}


class FCPContract(ContractBase):

    def setUp(self):
        super(FCPContract, self).setUp()
        self.db = self.backend.fcp()

    # helpers using only the interface

    def _insert(self, *fcp_ids):
        self.db.bulk_insert_zvm_fcp_info_into_fcp_table(
            [zvm_fcp(f) for f in fcp_ids])

    def _create(self, tmpl=T1, paths=None, host_default=False, sp=None,
                min_count=None, name='name', desc='desc'):
        self.db.create_fcp_template(tmpl, name, desc,
                                    PATHS if paths is None else paths,
                                    host_default, sp or [], min_count)

    def _setup_template(self, **kwargs):
        self._insert('1a00', '1a01', '1b00', '1b01')
        self._create(**kwargs)

    def _all(self):
        return {r['fcp_id']: dict(r) for r in self.db.get_all()}

    def _usage(self, fcp_id):
        return tuple(self.db.get_usage_of_fcp(fcp_id))

    def _templates(self, rows):
        return sorted(tuple(r) for r in rows)

    def _mapping(self, tmpl=T1):
        return {r['fcp_id']: r['path']
                for r in self.db.get_fcp_templates_details([tmpl])[1]}

    # fcp table

    def test_implements_interface(self):
        self.assertIsInstance(self.db, db_interface.FCPDbOperatorBase)

    def test_empty(self):
        self.assertEqual([], list(self.db.get_all()))
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_all_fcps_of_assigner)
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_all_fcps_of_assigner, USER)

    def test_bulk_insert_and_get_all(self):
        self._insert('1a00', '1b00')
        self.assertEqual({'1a00': fcp_row('1a00'), '1b00': fcp_row('1b00')},
                         self._all())
        rows = self.db.get_all_fcps_of_assigner()
        self.assertEqual(sorted(self._all().values(),
                                key=lambda r: r['fcp_id']),
                         sorted((dict(r) for r in rows),
                                key=lambda r: r['fcp_id']))
        # positional access follows the documented column order
        row = [r for r in rows if r['fcp_id'] == '1a00'][0]
        self.assertEqual(tuple(fcp_row('1a00').values()), tuple(row))

    def test_bulk_insert_duplicate(self):
        self._insert('1a00')
        # fcp_id is unique case-insensitively
        self.assertRaises(exception.SDKBaseException, self._insert, '1A00')

    def test_bulk_update_zvm_fcp_info(self):
        self._insert('1a00', '1b00')
        self.db.bulk_update_zvm_fcp_info_in_fcp_table(
            [zvm_fcp('1a00', state='active', owner=USER, npiv='ffff')])
        expected = fcp_row('1a00', state='active', owner=USER)
        expected['wwpn_npiv'] = 'ffff'
        self.assertEqual({'1a00': expected, '1b00': fcp_row('1b00')},
                         self._all())

    def test_bulk_update_state(self):
        self._insert('1a00', '1a01', '1b00')
        self.db.bulk_update_state_in_fcp_table(['1a00', '1b00'], 'notfound')
        self.assertEqual({'1a00': 'notfound', '1a01': 'free',
                          '1b00': 'notfound'},
                         {k: v['state'] for k, v in self._all().items()})

    def test_bulk_delete(self):
        self._insert('1a00', '1a01', '1b00')
        self.db.bulk_delete_from_fcp_table(['1a00', '1b00', 'ffff'])
        self.assertEqual(['1a01'], list(self._all()))

    def test_reserve_and_unreserve(self):
        self._insert('1a00', '1b00')
        self.db.reserve_fcps(['1a00', '1b00'], USER, T1)
        self.assertEqual((USER, 1, 0, T1), self._usage('1a00'))
        self.assertEqual((USER, 1, 0, T1), self._usage('1B00'))
        self.db.unreserve_fcps(['1a00'])
        # unreserve keeps the assigner
        self.assertEqual((USER, 0, 0, ''), self._usage('1a00'))
        self.assertEqual((USER, 1, 0, T1), self._usage('1b00'))
        self.db.unreserve_fcps([])

    def test_get_usage_of_fcp_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_usage_of_fcp, '1a00')

    def test_update_usage_and_reset(self):
        self._insert('1a00', '1b00')
        self.db.update_usage_of_fcp('1a00', USER, 1, 2, T1)
        self.db.update_usage_of_fcp('1b00', OTHER, 1, 1, T1)
        self.assertEqual((USER, 1, 2, T1), self._usage('1a00'))
        self.assertEqual(2, self.db.get_connections_from_fcp('1a00'))
        self.db.reset_fcps_of_assigner(USER)
        self.assertEqual(('', 0, 0, ''), self._usage('1a00'))
        self.assertEqual((OTHER, 1, 1, T1), self._usage('1b00'))

    def test_get_all_fcps_of_assigner(self):
        self._insert('1a00', '1b00')
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.assertEqual(['1a00'], [r['fcp_id'] for r in
                                    self.db.get_all_fcps_of_assigner(USER)])
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_all_fcps_of_assigner, OTHER)

    def test_connections(self):
        self._insert('1a00')
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.assertEqual(1, self.db.increase_connections_by_assigner(
            '1a00', USER))
        self.assertEqual(2, self.db.increase_connections_by_assigner(
            '1a00', USER))
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.increase_connections_by_assigner,
                          '1a00', OTHER)
        self.assertEqual(1, self.db.decrease_connections('1a00'))
        self.assertEqual(0, self.db.decrease_connections('1a00'))
        self.assertEqual(0, self.db.get_connections_from_fcp('1a00'))
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.decrease_connections, '1a00')

    def test_connections_fcp_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.increase_connections_by_assigner,
                          '1a00', USER)
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.decrease_connections, '1a00')
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_connections_from_fcp, '1a00')

    def test_get_inuse_fcp_device_by_fcp_template(self):
        self._setup_template()
        self.assertEqual([], list(
            self.db.get_inuse_fcp_device_by_fcp_template(T1)))
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.assertEqual([('1a00',)], [tuple(r) for r in self.db.
                                       get_inuse_fcp_device_by_fcp_template(T1)])

    # template table and its mappings

    def test_create_fcp_template(self):
        self._create(host_default=True, sp=['sp1', 'sp2'])
        self.assertTrue(self.db.fcp_template_exist_in_db(T1))
        self.assertFalse(self.db.fcp_template_exist_in_db(T2))
        self.assertEqual(
            [(T1, 'name', 'desc', 1, -1, 'sp1'),
             (T1, 'name', 'desc', 1, -1, 'sp2')],
            self._templates(self.db.get_fcp_templates([T1])))
        self.assertEqual({'1a00': 0, '1a01': 0, '1b00': 1, '1b01': 1},
                         self._mapping())
        self.assertEqual(2, self.db.get_path_count(T1))
        self.assertEqual(-1, self.db.get_min_fcp_paths_count_from_db(T1))
        self.assertEqual(2, self.db.get_min_fcp_paths_count(T1))
        self.assertTrue(self.db.sp_name_exist_in_db('sp1'))
        self.assertFalse(self.db.sp_name_exist_in_db('sp3'))

    def test_create_fcp_template_duplicate(self):
        self._create()
        self.assertRaises(exception.SDKObjectAlreadyExistError, self._create)

    def test_create_fcp_template_with_min_count(self):
        self._create(min_count=1)
        self.assertEqual(1, self.db.get_min_fcp_paths_count_from_db(T1))
        self.assertEqual(1, self.db.get_min_fcp_paths_count(T1))

    def test_min_fcp_paths_count_template_not_exist(self):
        self.assertIsNone(self.db.get_min_fcp_paths_count_from_db(T1))
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.get_min_fcp_paths_count, T1)

    def test_create_moves_host_and_sp_default(self):
        self._create(T1, host_default=True, sp=['sp1'])
        self._create(T2, host_default=True, sp=['sp1'])
        self.assertEqual([(T2, 'name', 'desc', 1, -1, 'sp1')],
                         self._templates(
                             self.db.get_host_default_fcp_template()))
        self.assertEqual([(T1, 'name', 'desc', 0, -1, None)],
                         self._templates(
                             self.db.get_host_default_fcp_template(False)))

    def test_get_fcp_templates(self):
        self.assertEqual([], list(self.db.get_fcp_templates()))
        self._create(T1, sp=['sp1'])
        self._create(T2, paths={})
        self.assertEqual(
            [(T1, 'name', 'desc', 0, -1, 'sp1'),
             (T2, 'name', 'desc', 0, -1, None)],
            self._templates(self.db.get_fcp_templates()))
        self.assertEqual([(T2, 'name', 'desc', 0, -1, None)],
                         self._templates(self.db.get_fcp_templates([T2])))
        row = self.db.get_fcp_templates([T1])[0]
        self.assertEqual(
            ['id', 'name', 'description', 'is_default',
             'min_fcp_paths_count', 'sp_name'],
            [k.lower() for k in row.keys()])

    def test_get_sp_default_fcp_template(self):
        self._create(T1, sp=['sp1'])
        self._create(T2, sp=['sp2'])
        t1 = (T1, 'name', 'desc', 0, -1, 'sp1')
        t2 = (T2, 'name', 'desc', 0, -1, 'sp2')
        self.assertEqual([t1], self._templates(
            self.db.get_sp_default_fcp_template(['sp1'])))
        self.assertEqual([t1, t2], self._templates(
            self.db.get_sp_default_fcp_template(['sp1', 'sp2'])))
        self.assertEqual([t1, t2], self._templates(
            self.db.get_sp_default_fcp_template(['all'])))
        self.assertEqual([], list(
            self.db.get_sp_default_fcp_template(['sp9'])))

    def test_get_fcp_template_by_assigner_id(self):
        self._setup_template(sp=['sp1'])
        self.assertEqual([], list(
            self.db.get_fcp_template_by_assigner_id(USER)))
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.assertEqual(
            [(T1, 'name', 'desc', 0, -1, 'sp1')],
            self._templates(self.db.get_fcp_template_by_assigner_id(USER)))

    def test_update_basic_info_of_fcp_template(self):
        self._create(T1, host_default=True)
        self._create(T2)
        self.db.update_basic_info_of_fcp_template(('n2', 'd2', True, 1, T2))
        self.assertEqual(
            [(T1, 'name', 'desc', 0, -1, None), (T2, 'n2', 'd2', 1, 1, None)],
            self._templates(self.db.get_fcp_templates()))
        self.db.update_basic_info_of_fcp_template(('n3', 'd3', False, -1, T2))
        self.assertEqual(
            [(T1, 'name', 'desc', 0, -1, None),
             (T2, 'n3', 'd3', 0, -1, None)],
            self._templates(self.db.get_fcp_templates()))

    def test_bulk_set_sp_default_by_fcp_template(self):
        self._create(T1, sp=['sp1', 'sp2'])
        self._create(T2, sp=['sp3'])
        self.db.bulk_set_sp_default_by_fcp_template(T2, ['sp1'])
        self.assertEqual(
            [(T1, 'name', 'desc', 0, -1, 'sp2'),
             (T2, 'name', 'desc', 0, -1, 'sp1')],
            self._templates(self.db.get_fcp_templates()))
        self.assertFalse(self.db.sp_name_exist_in_db('sp3'))

    def test_template_fcp_mapping(self):
        self._create()
        self.db.bulk_insert_fcp_device_into_fcp_template([(T1, '1c00', 2)])
        self.assertEqual(3, self.db.get_path_count(T1))
        self.db.update_path_of_fcp_device((0, '1c00', T1))
        self.assertEqual(2, self.db.get_path_count(T1))
        self.db.bulk_delete_fcp_device_from_fcp_template(
            [(T1, '1a00'), (T1, '1b01')])
        self.assertEqual({'1a01': 0, '1c00': 0, '1b00': 1}, self._mapping())

    def test_get_fcp_templates_details(self):
        self._setup_template(sp=['sp1'])
        self._create(T2, paths={0: {'1a00'}})
        # 1c00 is in the template but not in the fcp table
        self.db.bulk_insert_fcp_device_into_fcp_template([(T1, '1c00', 2)])
        self.db.reserve_fcps(['1a00'], USER, T2)
        tmpl_rows, device_rows = self.db.get_fcp_templates_details([T1])
        self.assertEqual([(T1, 'name', 'desc', 0, -1, 'sp1')],
                         self._templates(tmpl_rows))
        devices = {r['fcp_id']: r for r in device_rows}
        self.assertEqual(['1a00', '1a01', '1b00', '1b01', '1c00'],
                         sorted(devices))
        self.assertEqual(
            ('1a00', T1, 0, USER, 0, 1) + zvm_fcp('1a00')[1:] + (T2,),
            tuple(devices['1a00']))
        self.assertEqual(('1c00', T1, 2) + (None,) * 10,
                         tuple(devices['1c00']))
        # tmpl_id appears twice; by name it is the mapping's template
        self.assertEqual(T1, devices['1a00']['tmpl_id'])
        tmpl_rows, device_rows = self.db.get_fcp_templates_details()
        self.assertEqual([T1, T2], sorted(r['id'] for r in tmpl_rows))
        self.assertEqual(6, len(device_rows))

    def test_bulk_delete_fcp_from_template_skips_inuse(self):
        self._setup_template()
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.db.update_usage_of_fcp('1b00', USER, 0, 1, T1)
        self.db.bulk_delete_fcp_from_template(['1a00', '1a01', '1b00', '1b01'],
                                              T1)
        self.assertEqual({'1a00': 0, '1b00': 1}, self._mapping())

    def test_delete_fcp_template(self):
        self._setup_template(sp=['sp1'])
        self._create(T2, paths={0: {'1a00'}}, sp=['sp2'])
        self.db.delete_fcp_template(T1)
        self.assertFalse(self.db.fcp_template_exist_in_db(T1))
        self.assertFalse(self.db.sp_name_exist_in_db('sp1'))
        self.assertEqual({}, self._mapping(T1))
        # other templates and the fcp table are untouched
        self.assertEqual({'1a00': 0}, self._mapping(T2))
        self.assertTrue(self.db.sp_name_exist_in_db('sp2'))
        self.assertEqual(4, len(self._all()))

    def test_delete_fcp_template_errors(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.delete_fcp_template, T1)
        self._setup_template()
        self.db.reserve_fcps(['1a00'], USER, T1)
        self.assertRaises(exception.SDKConflictError,
                          self.db.delete_fcp_template, T1)
        self.assertTrue(self.db.fcp_template_exist_in_db(T1))

    def test_edit_fcp_template_basic_info(self):
        self._setup_template(sp=['sp1'])
        result = self.db.edit_fcp_template(
            T1, name='n2', description='d2', host_default=True,
            default_sp_list=['sp2'], min_fcp_paths_count=1)['fcp_template']
        pchids = result.pop('pchids')
        self.assertEqual({'name': 'n2', 'id': T1, 'description': 'd2',
                          'host_default': True, 'storage_providers': ['sp2'],
                          'min_fcp_paths_count': 1}, result)
        self.assertEqual(['02E4', '03FC'], sorted(pchids['all']))
        self.assertEqual({'all': [], 'first_used_by_templates': []},
                         pchids['add'])
        self.assertEqual({'all': [], 'not_exist_in_any_template': []},
                         pchids['delete'])
        self.assertFalse(self.db.sp_name_exist_in_db('sp1'))

    def test_edit_fcp_template_devices(self):
        self._setup_template()
        self._insert('1c00')
        result = self.db.edit_fcp_template(
            T1, fcp_devices='1a00;1b00-1b01;1c00')['fcp_template']
        self.assertEqual({'1a00': 0, '1b00': 1, '1b01': 1, '1c00': 2},
                         self._mapping())
        self.assertEqual({'all': ['05A0'], 'first_used_by_templates': ['05A0']},
                         result['pchids']['add'])
        self.assertEqual(3, result['min_fcp_paths_count'])
        # moving a device to another path
        self.db.edit_fcp_template(T1, fcp_devices='1a00-1a01;1b00-1b01;1c00')
        self.db.edit_fcp_template(T1, fcp_devices='1a00;1b00-1b01;1a01')
        self.assertEqual({'1a00': 0, '1b00': 1, '1b01': 1, '1a01': 2},
                         self._mapping())
        result = self.db.edit_fcp_template(T1, fcp_devices='1a00;1b00-1b01')
        self.assertEqual({'all': [], 'not_exist_in_any_template': []},
                         result['fcp_template']['pchids']['delete'])

    def test_edit_fcp_template_errors(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.edit_fcp_template, T1, name='n2')
        self._setup_template()
        self.db.reserve_fcps(['1a01'], USER, T1)
        # removing an in-use FCP
        self.assertRaises(exception.SDKConflictError,
                          self.db.edit_fcp_template, T1,
                          fcp_devices='1a00;1b00-1b01')
        # changing the path count while an FCP is in use
        self.assertRaises(exception.SDKConflictError,
                          self.db.edit_fcp_template, T1,
                          fcp_devices='1a00-1a01')
        # min_fcp_paths_count larger than the path count
        self.assertRaises(exception.SDKConflictError,
                          self.db.edit_fcp_template, T1,
                          min_fcp_paths_count=3)
        self.assertEqual({'1a00': 0, '1a01': 0, '1b00': 1, '1b01': 1},
                         self._mapping())

    # queries over several tables

    def test_allocated_and_reserved_fcps_from_assigner(self):
        self._setup_template()
        self.db.reserve_fcps(['1b00', '1a00'], USER, T1)
        # connected but no longer reserved
        self.db.update_usage_of_fcp('1a01', USER, 0, 1, T1)
        allocated = self.db.get_allocated_fcps_from_assigner(USER, T1)
        self.assertEqual(['1a00', '1a01', '1b00'],
                         [r['fcp_id'] for r in allocated])
        _, npiv, phy, _, pchid, _, _ = zvm_fcp('1b00')
        self.assertEqual({'fcp_id': '1b00', 'wwpn_npiv': npiv,
                          'wwpn_phy': phy, 'path': 1, 'pchid': pchid},
                         dict(allocated[2]))
        reserved = self.db.get_reserved_fcps_from_assigner(USER, T1)
        self.assertEqual(['1a00', '1b00'], [r['fcp_id'] for r in reserved])
        self.assertEqual({'fcp_id': '1b00', 'wwpn_npiv': npiv,
                          'wwpn_phy': phy, 'connections': 0, 'path': 1,
                          'pchid': pchid},
                         dict(reserved[1]))
        self.assertEqual([], list(
            self.db.get_allocated_fcps_from_assigner(OTHER, T1)))
        self.assertEqual([], list(
            self.db.get_reserved_fcps_from_assigner(USER, T2)))

    def test_pchids(self):
        self.assertEqual([], self.db.get_pchids_from_all_fcp_templates())
        self.assertEqual({}, self.db.get_pchids_of_all_inuse_fcp_devices())
        self._setup_template()
        self.assertEqual(['02E4', '03FC'],
                         sorted(self.db.get_pchids_from_all_fcp_templates()))
        self.assertEqual(['02E4', '03FC'],
                         sorted(self.db.get_pchids_by_fcp_template(T1)))
        self.assertEqual([], self.db.get_pchids_by_fcp_template(T2))
        self.assertEqual({0: ['02E4'], 1: ['03FC']},
                         self.db.get_free_pchids_by_fcp_template(T1))
        self.db.reserve_fcps(['1a00', '1a01'], USER, T1)
        self.assertEqual({1: ['03FC']},
                         self.db.get_free_pchids_by_fcp_template(T1))
        self.assertEqual({'02E4': utils.shrink_fcp_list(['1a00', '1a01'])},
                         self.db.get_pchids_of_all_inuse_fcp_devices())
        self.assertEqual({'02E4': 'c05076de330002e4',
                          '03FC': 'c05076de330003fc'},
                         self.db.get_wwpn_phy_from_pchids(['02E4', '03FC']))

    def test_get_fcp_devices(self):
        self._setup_template()
        fcp_list, reason = self.db.get_fcp_devices(T1, PCHID_INFO)
        self.assertEqual('', reason)
        self.assertEqual([0, 1], sorted(f['path'] for f in fcp_list))
        for fcp in fcp_list:
            fcp_id = fcp['fcp_id']
            self.assertIn(fcp_id, {0: ['1A00', '1A01'],
                                   1: ['1B00', '1B01']}[fcp['path']])
            _, npiv, phy, _, pchid, _, _ = zvm_fcp(fcp_id.lower())
            self.assertEqual((npiv, phy, pchid.upper()),
                             (fcp['wwpn_npiv'], fcp['wwpn_phy'],
                              fcp['pchid']))
        # picking does not reserve
        self.assertEqual(2, len(self.db.get_fcp_devices(T1, PCHID_INFO)[0]))
        self.assertEqual({0}, {r['reserved'] for r in self._all().values()})

    def test_get_fcp_devices_min_paths(self):
        self._setup_template(min_count=1)
        self.db.reserve_fcps(['1b00', '1b01'], OTHER, T1)
        fcp_list, reason = self.db.get_fcp_devices(T1, PCHID_INFO)
        self.assertEqual('', reason)
        self.assertEqual([0], [f['path'] for f in fcp_list])

    def test_get_fcp_devices_not_enough_paths(self):
        self._setup_template()
        self.db.reserve_fcps(['1b00', '1b01'], OTHER, T1)
        fcp_list, reason = self.db.get_fcp_devices(T1, PCHID_INFO)
        self.assertEqual([], fcp_list)
        self.assertTrue(reason)

    def test_get_fcp_devices_no_free(self):
        self._setup_template()
        self.db.bulk_update_state_in_fcp_table(
            ['1a00', '1a01', '1b00', '1b01'], 'active')
        fcp_list, reason = self.db.get_fcp_devices(T1, PCHID_INFO)
        self.assertEqual([], fcp_list)
        self.assertTrue(reason)

    def test_get_fcp_devices_pchid_full(self):
        self._setup_template()
        pchid_info = dict(PCHID_INFO, **{'02E4': {'allocated': 128,
                                                  'max': 128}})
        fcp_list, reason = self.db.get_fcp_devices(T1, pchid_info)
        self.assertEqual([], fcp_list)
        self.assertIn('02E4', reason)

    def test_get_fcp_devices_with_same_index(self):
        self._setup_template()
        self.db.reserve_fcps(['1a00'], OTHER, T1)
        fcp_list, reason = self.db.get_fcp_devices_with_same_index(
            T1, PCHID_INFO)
        self.assertEqual('', reason)
        self.assertEqual([('1A01', 0, '02E4'), ('1B01', 1, '03FC')],
                         [(f['fcp_id'], f['path'], f['pchid'])
                          for f in fcp_list])
        self.db.reserve_fcps(['1b01'], OTHER, T1)
        self.assertEqual([], self.db.get_fcp_devices_with_same_index(
            T1, PCHID_INFO)[0])

    def test_get_fcp_devices_with_same_index_empty_template(self):
        self._create(paths={})
        fcp_list, reason = self.db.get_fcp_devices_with_same_index(
            T1, PCHID_INFO)
        self.assertEqual([], fcp_list)
        self.assertTrue(reason)
