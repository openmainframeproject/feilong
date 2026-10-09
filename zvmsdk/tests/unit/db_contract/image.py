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


def _image(name, comments=None):
    return {'imagename': name, 'imageosdistro': 'rhel9.4',
            'checksum': 'c' * 128, 'disk_size_units': '3338:CYL',
            'image_size_in_bytes': '1012', 'type': 'rootonly',
            'comments': comments}


class ImageContract(ContractBase):

    def setUp(self):
        super(ImageContract, self).setUp()
        self.db = self.backend.image()

    def _add(self, name, comments=None):
        img = _image(name)
        self.db.image_add_record(name, img['imageosdistro'], img['checksum'],
                                 img['disk_size_units'],
                                 img['image_size_in_bytes'], img['type'],
                                 comments=comments)

    def test_implements_interface(self):
        self.assertIsInstance(self.db, db_interface.ImageDbOperatorBase)

    def test_add_query_delete(self):
        self.assertEqual([], self.db.image_query_record())
        self._add('img1')
        self._add('img2', comments='{"a": 1}')
        self.assertEqual([_image('img1')], self.db.image_query_record('img1'))
        self.assertEqual(
            [_image('img1'), _image('img2', '{"a": 1}')],
            sorted(self.db.image_query_record(), key=lambda i: i['imagename']))
        self.db.image_delete_record('img1')
        self.assertEqual([_image('img2', '{"a": 1}')],
                         self.db.image_query_record())
        # deleting a missing record is not an error
        self.db.image_delete_record('img1')

    def test_query_is_case_insensitive(self):
        self._add('Img1')
        self.assertEqual([_image('Img1')], self.db.image_query_record('IMG1'))

    def test_query_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db.image_query_record, 'nope')

    def test_add_duplicate(self):
        self._add('img1')
        self.assertRaises(exception.SDKDatabaseException, self._add, 'IMG1')
