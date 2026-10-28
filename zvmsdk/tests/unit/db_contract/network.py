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
from zvmsdk.tests.unit.db_contract.fixture import ContractBase


def _switch(userid, interface, switch=None, port=None, comments=None):
    return {'userid': userid, 'interface': interface, 'switch': switch,
            'port': port, 'comments': comments}


def _sorted(records):
    return sorted(records, key=lambda r: (r['userid'], r['interface']))


class NetworkContract(ContractBase):

    def setUp(self):
        super(NetworkContract, self).setUp()
        self.db = self.backend.network()

    def _add_two_users(self):
        self.db.switch_add_record('USER1', '1000', port='p1', switch='VSW1')
        self.db.switch_add_record('USER1', '2000', port='p2', switch='VSW2')
        self.db.switch_add_record('USER2', '1000', port='p3', switch='VSW1')

    def test_implements_interface(self):
        self.assertIsInstance(self.db, db_interface.NetworkDbOperatorBase)

    def test_empty(self):
        self.assertEqual([], self.db.switch_select_table())
        self.assertEqual([], self.db.switch_select_record_for_userid('USER1'))

    def test_switch_add_record(self):
        self.db.switch_add_record('USER1', '1000', port='p1', switch='VSW1',
                                  comments='c')
        self.db.switch_add_record('USER2', '1000')
        self.assertEqual(
            [_switch('USER1', '1000', 'VSW1', 'p1', 'c'),
             _switch('USER2', '1000')],
            _sorted(self.db.switch_select_table()))

    def test_switch_add_record_migrated(self):
        self.db.switch_add_record_migrated('USER1', '1000', 'VSW1',
                                           port='p1', comments='c')
        self.assertEqual([_switch('USER1', '1000', 'VSW1', 'p1', 'c')],
                         self.db.switch_select_table())

    def test_switch_add_record_duplicate(self):
        self.db.switch_add_record('USER1', '1000')
        # userid and interface match case-insensitively
        self.assertRaises(exception.SDKNetworkOperationError,
                          self.db.switch_add_record, 'user1', '1000')

    def test_switch_update_record_with_switch(self):
        self.db.switch_add_record('USER1', '1000', port='p1')
        self.db.switch_update_record_with_switch('USER1', '1000', 'VSW9')
        self.assertEqual([_switch('USER1', '1000', 'VSW9', 'p1')],
                         self.db.switch_select_table())
        self.db.switch_update_record_with_switch('USER1', '1000', None)
        self.assertEqual([_switch('USER1', '1000', None, 'p1')],
                         self.db.switch_select_table())

    def test_switch_update_record_with_switch_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.switch_update_record_with_switch,
                          'USER1', '1000', 'VSW1')

    def test_switch_select_record_for_userid(self):
        self._add_two_users()
        self.assertEqual(
            [_switch('USER1', '1000', 'VSW1', 'p1'),
             _switch('USER1', '2000', 'VSW2', 'p2')],
            _sorted(self.db.switch_select_record_for_userid('user1')))

    def test_switch_select_record(self):
        self._add_two_users()
        self.assertEqual(3, len(self.db.switch_select_record()))
        self.assertEqual(
            ['USER1', 'USER1'],
            [r['userid'] for r in self.db.switch_select_record(
                userid='USER1')])
        self.assertEqual([_switch('USER1', '2000', 'VSW2', 'p2')],
                         self.db.switch_select_record(nic_id='p2'))
        self.assertEqual(
            [_switch('USER1', '1000', 'VSW1', 'p1'),
             _switch('USER2', '1000', 'VSW1', 'p3')],
            _sorted(self.db.switch_select_record(vswitch='VSW1')))
        self.assertEqual(
            [_switch('USER2', '1000', 'VSW1', 'p3')],
            self.db.switch_select_record(userid='USER2', nic_id='p3',
                                         vswitch='VSW1'))
        self.assertEqual([], self.db.switch_select_record(userid='USER2',
                                                          vswitch='VSW2'))

    def test_switch_delete_record_for_nic(self):
        self._add_two_users()
        self.db.switch_delete_record_for_nic('USER1', '1000')
        self.assertEqual(
            [_switch('USER1', '2000', 'VSW2', 'p2'),
             _switch('USER2', '1000', 'VSW1', 'p3')],
            _sorted(self.db.switch_select_table()))
        # deleting a missing record is not an error
        self.db.switch_delete_record_for_nic('USER1', '1000')

    def test_switch_delete_record_for_userid(self):
        self._add_two_users()
        self.db.switch_delete_record_for_userid('USER1')
        self.assertEqual([_switch('USER2', '1000', 'VSW1', 'p3')],
                         self.db.switch_select_table())
        self.db.switch_delete_record_for_userid('USER1')

    def test_switch_rename_userid(self):
        self._add_two_users()
        self.db.switch_rename_userid('user1', 'newuser')

        self.assertEqual([], self.db.switch_select_record_for_userid('USER1'))
        self.assertEqual(
            [_switch('NEWUSER', '1000', 'VSW1', 'p1'),
             _switch('NEWUSER', '2000', 'VSW2', 'p2')],
            _sorted(self.db.switch_select_record_for_userid('NEWUSER')))
        # other user unchanged
        self.assertEqual(
            [_switch('USER2', '1000', 'VSW1', 'p3')],
            self.db.switch_select_record_for_userid('USER2'))
