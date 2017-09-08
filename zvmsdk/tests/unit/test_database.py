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
import uuid

from zvmsdk import config
from zvmsdk import database
from zvmsdk.database import VolumeDBUtils
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.tests.unit import base


CONF = config.CONF
LOG = log.LOG


def _to_db_str(sequential_list):
    """Convert a list or tuple object to a string of database format."""
    entry_list = []
    for _entry in sequential_list:
        # I know only text type need to be converted by now. More types could
        # be added in the future when we know.
        if isinstance(_entry, str):
            entry_list.append("u'%s'" % _entry)
        else:
            entry_list.append(str(_entry))
    return "(%s)" % ", ".join(entry_list)


class VolumeDBUtilsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(VolumeDBUtilsTestCase, cls).setUpClass()
        cls._util = VolumeDBUtils()

    @classmethod
    def tearDownClass(cls):
        with database.get_db_conn() as conn:
            conn.execute("DROP TABLE volumes")
            conn.execute("DROP TABLE volume_attachments")
        super(VolumeDBUtilsTestCase, cls).tearDownClass()

    @mock.patch.object(VolumeDBUtils, '_initialize_table_volume_attachments')
    @mock.patch.object(VolumeDBUtils, '_initialize_table_volumes')
    def test__init__(self,
                     _initialize_table_volumes,
                     _initialize_table_volume_attachments):
        self._util.__init__()
        _initialize_table_volumes.assert_called_once_with()
        _initialize_table_volume_attachments.assert_called_once_with()

    def test_get_volume_by_id_errors(self):
        # error - Empty volume id
        volume_id_null = None
        self.assertRaises(exception.DatabaseException,
                          self._util.get_volume_by_id, volume_id_null)

        # not found
        volume_id = str(uuid.uuid4())
        self.assertIsNone(self._util.get_volume_by_id(volume_id))

    def test_get_volume_by_id(self):
        # setup test volume
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)

        # query
        volume = self._util.get_volume_by_id(volume_id)
        expected = [volume_id, 'fc', '3G']
        actual = [volume[0], volume[1], volume[2]]
        self.assertEqual(expected, actual)

        # clean test volume
        self._util.delete_volume(volume_id)

    def test_insert_volume_errors(self):
        # empty volume
        volume = None
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume, volume)

        # protocol_type absent
        volume = {'size': '3G'}
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume, volume)
        volume = {'protocol_type': 'fc'}
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume, volume)

    def test_insert_volume(self):
        # insert a simplest volume
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)

        # query
        volume = self._util.get_volume_by_id(volume_id)
        expected = [volume_id, 'fc', '3G', 'free', 0]
        actual = [volume[0], volume[1], volume[2], volume[3], volume[6]]
        self.assertEqual(expected, actual)

        # clean test volume
        self._util.delete_volume(volume_id)

        # insert a complicated volume
        image_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())
        volume = {'protocol_type': 'fc',
                  'size': '3G',
                  'image_id': image_id,
                  'snapshot_id': snapshot_id,
                  'comment': 'hello world'}
        volume_id = self._util.insert_volume(volume)

        # query
        volume = self._util.get_volume_by_id(volume_id)
        expected = _to_db_str((volume_id, 'fc', '3G', 'free', image_id,
                               snapshot_id, 0, None, 'hello world'))
        self.assertEqual(expected, str(volume))

    def test_update_volume_errors(self):
        # empty volume
        volume = None
        self.assertRaises(exception.DatabaseException,
                          self._util.update_volume, volume)
        volume = {}
        self.assertRaises(exception.DatabaseException,
                          self._util.update_volume, volume)

        # volume not found
        volume_id = str(uuid.uuid4())
        volume = {'id': volume_id}
        self.assertRaises(exception.DatabaseException,
                          self._util.update_volume, volume)

    def test_update_volume(self):
        # set up the test volume
        image_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())
        volume = {'protocol_type': 'fc',
                  'size': '3G',
                  'image_id': image_id,
                  'snapshot_id': snapshot_id,
                  'comment': 'hello world'}
        volume_id = self._util.insert_volume(volume)

        # make update
        image_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())
        volume = {'id': volume_id,
                  'size': '5G',
                  'status': 'in-use',
                  'image_id': image_id,
                  'snapshot_id': snapshot_id,
                  'comment': 'goodbye world'}
        self._util.update_volume(volume)

        # query the volume
        volume = self._util.get_volume_by_id(volume_id)
        expected = _to_db_str((volume_id, 'fc', '5G', 'in-use', image_id,
                               snapshot_id, 0, None, 'goodbye world'))
        self.assertEqual(expected, str(volume))

        # clean the volume
        self._util.delete_volume(volume_id)

    def test_delete_volume_errors(self):
        # empty volume
        volume_id = None
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume, volume_id)

        # not found
        volume_id = str(uuid.uuid4())
        self.assertIsNone(self._util.get_volume_by_id(volume_id))

    def test_delete_volume(self):
        # insert a simplest volume
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)
        # query it
        self.assertIsNotNone(self._util.get_volume_by_id(volume_id))
        # delete it
        self._util.delete_volume(volume_id)
        # query again
        self.assertIsNone(self._util.get_volume_by_id(volume_id))


class GuestDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(GuestDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.GuestDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_db_conn() as conn:
            conn.execute("DROP TABLE guests")
        super(GuestDbOperatorTestCase, cls).tearDownClass()

    @mock.patch.object(uuid, 'uuid4')
    def test_add_guest(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Query, the guest should in table
        guests = self.db_op.get_guest_list()
        self.assertEqual(1, len(guests))
        self.assertListEqual([(u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                               u'FAKEUSER', u'fakemeta=1, fakemeta2=True',
                               u'')], guests)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_add_guest_twice_error(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Add same user the second time
        self.assertRaises(exception.DatabaseException,
                          self.db_op.add_guest, 'fakeuser')
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_delete_guest_by_id(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Delete
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        guests = self.db_op.get_guest_list()
        self.assertListEqual([], guests)

    def test_delete_guest_by_id_not_exist(self):
        self.assertRaises(exception.DatabaseException,
                          self.db_op.delete_guest_by_id,
                          'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_delete_guest_by_userid(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Delete
        self.db_op.delete_guest_by_userid('FaKeuser')
        guests = self.db_op.get_guest_list()
        self.assertListEqual([], guests)

    def test_delete_guest_by_userid_not_exist(self):
        self.assertRaises(exception.DatabaseException,
                          self.db_op.delete_guest_by_userid,
                          'Fakeuser')

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_by_userid(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # get guest
        guest = self.db_op.get_guest_by_userid('FaKeuser')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'fakemeta=1, fakemeta2=True',
                          u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_get_guest_by_userid_not_exist(self):
        guest = self.db_op.get_guest_by_userid('FaKeuser')
        self.assertEqual(None, guest)

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_by_id(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # get guest
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'fakemeta=1, fakemeta2=True',
                          u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_get_guest_by_id_not_exist(self):
        guest = self.db_op.get_guest_by_id(
            'aa8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual(None, guest)

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_id(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.db_op.update_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c', meta='newmeta',
            comments='newcomment')
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'newmeta',
                          u'newcomment'), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_id_wrong_input(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.assertRaises(exception.DatabaseException,
                          self.db_op.update_guest_by_id,
                          'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_update_guest_by_id_not_exist(self):
        self.assertRaises(exception.DatabaseException,
                          self.db_op.update_guest_by_id,
                          'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          meta='newmeta')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_id_null_value(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.db_op.update_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c', meta='',
            comments='')
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'', u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.db_op.update_guest_by_userid(
            'Fakeuser', meta='newmetauserid', comments='newcommentuserid')
        guest = self.db_op.get_guest_by_userid('Fakeuser')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'newmetauserid',
                          u'newcommentuserid'), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid_wrong_input(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.assertRaises(exception.DatabaseException,
                          self.db_op.update_guest_by_userid,
                          'FakeUser')
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_update_guest_by_userid_not_exist(self):
        self.assertRaises(exception.DatabaseException,
                          self.db_op.update_guest_by_userid,
                          'FaKeUser',
                          meta='newmeta')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid_null_value(self, get_uuid):
        userid = 'fakeuser'
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(userid, meta=meta)
        # Update
        self.db_op.update_guest_by_userid(
            'FaKeUser', meta='', comments='')
        guest = self.db_op.get_guest_by_userid('fakeuser')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'', u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')


class ImageDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(ImageDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.ImageDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_db_conn() as conn:
            conn.execute("DROP TABLE image")
        super(ImageDbOperatorTestCase, cls).tearDownClass()

    def test_image_add_query_delete_record(self):
        imagename = 'test'
        imageosdistro = 'rhel6.5'
        md5sum = 'c73ce117eef8077c3420bfc8f473ac2f'
        disk_size_units = '3338:CYL'
        image_size_in_bytes = '5120000'
        type = 'netboot'
        # Add an record
        self.db_op.image_add_record(imagename, imageosdistro, md5sum,
            disk_size_units, image_size_in_bytes, type)
        # Query the record
        image_record = self.db_op.image_query_record(imagename)
        self.assertEqual(1, len(image_record))
        self.assertListEqual([(u'test', u'rhel6.5',
            u'c73ce117eef8077c3420bfc8f473ac2f',
            u'3338:CYL', u'5120000', u'netboot', None)], image_record)
        # Query the disk size units
        disk_size_units_query_result = self.db_op.query_disk_size_units(
                                                            imagename)
        self.assertEqual(disk_size_units, disk_size_units_query_result)
        # Delete it
        self.db_op.image_delete_record(imagename)
        image_record = self.db_op.image_query_record(imagename)
        self.assertEqual(0, len(image_record))
        self.assertListEqual([], image_record)

    def test_image_add_record_with_existing_imagename(self):
        imagename = 'test'
        imageosdistro = 'rhel6.5'
        md5sum = 'c73ce117eef8077c3420bfc8f473ac2f'
        disk_size_units = '3338:CYL'
        image_size_in_bytes = '5120000'
        type = 'netboot'

        # Add an record
        self.db_op.image_add_record(imagename, imageosdistro, md5sum,
            disk_size_units, image_size_in_bytes, type)
        self.assertRaises(exception.DatabaseException,
            self.db_op.image_add_record, imagename, imageosdistro, md5sum,
            disk_size_units, image_size_in_bytes, type)
        self.db_op.image_delete_record(imagename)

    def test_image_query_record_multiple_image(self):
        imagename1 = 'testimage1'
        imagename2 = 'testimage2'
        imageosdistro = 'rhel6.5'
        md5sum = 'c73ce117eef8077c3420bfc8f473ac2f'
        disk_size_units = '3338:CYL'
        image_size_in_bytes = '5120000'
        type = 'netboot'

        # Add two records
        self.db_op.image_add_record(imagename1, imageosdistro, md5sum,
            disk_size_units, image_size_in_bytes, type)
        self.db_op.image_add_record(imagename2, imageosdistro, md5sum,
            disk_size_units, image_size_in_bytes, type)

        image_records = self.db_op.image_query_record()
        self.assertEqual(2, len(image_records))
        self.assertListEqual([(u'testimage1', u'rhel6.5',
            u'c73ce117eef8077c3420bfc8f473ac2f',
            u'3338:CYL', u'5120000', u'netboot', None),
            (u'testimage2', u'rhel6.5',
            u'c73ce117eef8077c3420bfc8f473ac2f',
            u'3338:CYL', u'5120000', u'netboot', None)], image_records)
        # Clean up the images
        self.db_op.image_delete_record(imagename1)
        self.db_op.image_delete_record(imagename2)
