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


import uuid

from zvmsdk import db_interface
from zvmsdk import exception
from zvmsdk.tests.unit.db_contract.fixture import ContractBase


MIGRATED = '{"migrated": 1}'


class GuestContract(ContractBase):
    """Guest rows are positional: (id, userid, metadata, net_set, comments).
    """

    def setUp(self):
        super(GuestContract, self).setUp()
        self.db = self.backend.guest()

    def _guest(self, userid):
        return tuple(self.db.get_guest_by_userid(userid))

    def test_implements_interface(self):
        self.assertIsInstance(self.db, db_interface.GuestDbOperatorBase)

    def test_add_guest(self):
        self.db.add_guest('USER1', meta='os_version=rhel9.4')
        guest_id, userid, meta, net_set, comments = self._guest('USER1')
        self.assertEqual(str(uuid.UUID(guest_id)), guest_id)
        self.assertEqual(('USER1', 'os_version=rhel9.4', 0, ''),
                         (userid, meta, net_set, comments))
        self.assertEqual(self._guest('USER1'),
                         tuple(self.db.get_guest_by_id(guest_id)))

    def test_add_guest_duplicate(self):
        self.db.add_guest('USER1')
        # userid is unique case-insensitively
        self.assertRaises(exception.SDKGuestOperationError,
                          self.db.add_guest, 'user1')

    def test_add_guest_registered(self):
        self.db.add_guest_registered('USER1', 'a=1', 1, MIGRATED)
        self.assertEqual(('USER1', 'a=1', 1, MIGRATED),
                         self._guest('USER1')[1:])
        self.db.add_guest_registered('USER2', 'a=2', 0)
        self.assertEqual(('USER2', 'a=2', 0, None), self._guest('USER2')[1:])

    def test_get_guest_not_exist(self):
        self.assertIsNone(self.db.get_guest_by_userid('USER1'))
        self.assertIsNone(self.db.get_guest_by_id(str(uuid.uuid4())))

    def test_get_guest_by_userid_is_case_insensitive(self):
        self.db.add_guest('USER1')
        self.assertEqual('USER1', self.db.get_guest_by_userid('user1')[1])

    def test_get_guest_list(self):
        self.assertEqual([], list(self.db.get_guest_list()))
        self.db.add_guest('USER1')
        self.db.add_guest('USER2')
        self.assertEqual(['USER1', 'USER2'],
                         sorted(g[1] for g in self.db.get_guest_list()))

    def test_migrated_guest_lists(self):
        self.db.add_guest('USER1')
        self.db.add_guest_registered('USER2', 'a=2', 1, MIGRATED)
        self.db.add_guest_registered('USER3', 'a=3', 1, '{"migrated": 0}')
        self.assertEqual([('USER2',)],
                         [tuple(g) for g in self.db.get_migrated_guest_list()])
        self.assertEqual([self._guest('USER2')],
                         [tuple(g) for g in
                          self.db.get_migrated_guest_info_list()])

    def test_metadata(self):
        self.db.add_guest('USER1', meta='a=1,b=2')
        self.assertEqual([('a=1,b=2',)],
                         [tuple(r) for r in
                          self.db.get_guest_metadata_with_userid('USER1')])
        self.assertEqual([], list(
            self.db.get_guest_metadata_with_userid('USER2')))
        self.assertEqual('a=1,b=2', self.db.get_metadata_by_userid('USER1'))
        self.assertEqual('', self.db.get_metadata_by_userid('USER2'))
        self.assertEqual({'a': '1', 'b': '2'},
                         self.db.transfer_metadata_to_dict('a=1, b=2,'))

    def test_comments(self):
        self.db.add_guest('USER1')
        self.assertEqual({}, self.db.get_comments_by_userid('USER1'))
        self.db.update_guest_by_userid('USER1', comments={'migrated': 1})
        self.assertEqual({'migrated': 1},
                         self.db.get_comments_by_userid('USER1'))
        self.assertEqual([('USER1',)],
                         [tuple(g) for g in self.db.get_migrated_guest_list()])

    def test_update_guest_by_id(self):
        self.db.add_guest('USER1', meta='a=1')
        guest_id = self._guest('USER1')[0]
        self.db.update_guest_by_id(guest_id, userid='USER9', meta='a=2',
                                   net_set=1, comments='raw')
        self.assertEqual((guest_id, 'USER9', 'a=2', 1, 'raw'),
                         tuple(self.db.get_guest_by_id(guest_id)))
        # fields not given are kept
        self.db.update_guest_by_id(guest_id, meta='a=3')
        self.assertEqual((guest_id, 'USER9', 'a=3', 1, 'raw'),
                         tuple(self.db.get_guest_by_id(guest_id)))

    def test_update_guest_by_id_errors(self):
        self.db.add_guest('USER1')
        guest_id = self._guest('USER1')[0]
        self.assertRaises(exception.SDKInternalError,
                          self.db.update_guest_by_id, guest_id)
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.update_guest_by_id, str(uuid.uuid4()),
                          meta='a=1')

    def test_update_guest_by_userid(self):
        self.db.add_guest('USER1', meta='a=1')
        self.db.update_guest_by_userid('USER1', meta='a=2', net_set=1)
        self.assertEqual(('USER1', 'a=2', 1, ''), self._guest('USER1')[1:])

    def test_update_guest_by_userid_errors(self):
        self.db.add_guest('USER1')
        self.assertRaises(exception.SDKInternalError,
                          self.db.update_guest_by_userid, 'USER1')
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.update_guest_by_userid, 'USER2',
                          meta='a=1')

    def test_delete_guest_by_id(self):
        self.db.add_guest('USER1')
        self.db.add_guest('USER2')
        self.db.delete_guest_by_id(self._guest('USER1')[0])
        self.assertIsNone(self.db.get_guest_by_userid('USER1'))
        self.assertIsNotNone(self.db.get_guest_by_userid('USER2'))
        # deleting a missing guest is not an error
        self.db.delete_guest_by_id(str(uuid.uuid4()))

    def test_delete_guest_by_userid(self):
        self.db.add_guest('USER1')
        self.db.add_guest('USER2')
        self.db.delete_guest_by_userid('USER1')
        self.assertIsNone(self.db.get_guest_by_userid('USER1'))
        self.assertIsNotNone(self.db.get_guest_by_userid('USER2'))
        self.db.delete_guest_by_userid('USER1')

    def test_guest_rename_userid(self):
        self.db.add_guest('USER1', meta='a=1,b=2', comments='raw')
        guest_id = self._guest('USER1')[0]
        self.db.update_guest_by_id(guest_id, net_set=1)

        self.db.guest_rename_userid('user1', 'newuser')

        self.assertIsNone(self.db.get_guest_by_userid('USER1'))
        expected = (guest_id, 'NEWUSER', 'a=1,b=2', 1, 'raw')
        self.assertEqual(expected, self._guest('NEWUSER'))
        self.assertEqual(expected, tuple(self.db.get_guest_by_id(guest_id)))

    def test_guest_rename_userid_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.guest_rename_userid, 'NOTEXIST', 'NEWUSER')
