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
from zvmsdk.database import VolumeDbOperator
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


class VolumeDbOperatorTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = CONF.database.path
        CONF.database.path = '/tmp/test_volume.db'
        cls._util = VolumeDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_db_conn() as conn:
            conn.execute("DROP TABLE volumes")
            conn.execute("DROP TABLE volume_attachments")
        CONF.database.path = cls.db_path

    @mock.patch.object(VolumeDbOperator,
                       '_initialize_table_volume_attachments')
    @mock.patch.object(VolumeDbOperator, '_initialize_table_volumes')
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
        volume_db = self._util.get_volume_by_id(volume_id)
        expected = [volume_id, 'fc', '3G']
        actual = [volume_db[0], volume_db[1], volume_db[2]]
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
        expected = (volume_id, 'fc', '3G', 'free', image_id, snapshot_id, 0,
                    None, 'hello world')
        actual = (volume[0], volume[1], volume[2], volume[3], volume[4],
                  volume[5], volume[6], volume[7], volume[8])
        self.assertEqual(expected, volume)
        self.assertEqual(expected, actual)

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
        self.assertRaises(exception.ZVMVolumeError,
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
        expected = (volume_id, 'fc', '5G', 'in-use', image_id, snapshot_id, 0,
                    None, 'goodbye world')
        self.assertEqual(expected, volume)

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

    def test_get_attachment_by_volume_id_errors(self):
        # error - Empty volume id
        volume_id_null = None
        self.assertRaises(exception.DatabaseException,
                          self._util.get_attachment_by_volume_id,
                          volume_id_null)

        # not found
        volume_id = str(uuid.uuid4())
        self.assertIsNone(self._util.get_attachment_by_volume_id(volume_id))

    def test_get_attachment_by_volume_id(self):
        # setup test volume
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)
        # FIXME  need insert_instance() by Dong Yan
        instance_id = str(uuid.uuid4())
        connection_info = {'wwpns': '0x5005500550055005',
                           'lun': '0x1001100110011001'}
        mountpoint = '/dev/vda'
        volume_attachment = {'volume_id': volume_id,
                             'instance_id': instance_id,
                             'connection_info': connection_info,
                             'mountpoint': mountpoint,
                             'comment': 'my comment'}
        self._util.insert_volume_attachment(volume_attachment)

        # query
        attachment = self._util.get_attachment_by_volume_id(volume_id)
        expected = (volume_id, instance_id, str(connection_info),
                    mountpoint, 'my comment')
        actual = (attachment[1], attachment[2], attachment[3], attachment[4],
                  attachment[7])
        self.assertEqual(expected, actual)

        # clean test volume
        self._util.delete_volume_attachment(volume_id, instance_id)
        self._util.delete_volume(volume_id)
        # FIXME  delete instance

    def test_get_attachments_by_instance_id_errors(self):
        # error - Empty volume id
        instance_id_null = None
        self.assertRaises(exception.DatabaseException,
                          self._util.get_attachment_by_volume_id,
                          instance_id_null)

        # not found
        instance_id = str(uuid.uuid4())
        self.assertIsNone(self._util.get_attachment_by_volume_id(instance_id))

    def test_get_attachments_by_instance_id(self):
        # setup test volume_1
        volume_1 = {'protocol_type': 'fc', 'size': '3G'}
        volume_id_1 = self._util.insert_volume(volume_1)
        volume_2 = {'protocol_type': 'iscsi', 'size': '2G'}
        volume_id_2 = self._util.insert_volume(volume_2)
        # FIXME  need insert_instance() by Dong Yan
        instance_id = str(uuid.uuid4())
        connection_info_1 = {'wwpns': '0x5005500550055005',
                             'lun': '0x1001100110011001'}
        mountpoint_1 = '/dev/vda'
        volume_attachment_1 = {'volume_id': volume_id_1,
                               'instance_id': instance_id,
                               'connection_info': connection_info_1,
                               'mountpoint': mountpoint_1,
                               'comment': 'my comment 1'}
        self._util.insert_volume_attachment(volume_attachment_1)
        connection_info_2 = {'wwpns': '0x5005500550055005',
                             'lun': '0x1001100110011002'}
        mountpoint_2 = '/dev/vdb'
        volume_attachment_2 = {'volume_id': volume_id_2,
                               'instance_id': instance_id,
                               'connection_info': connection_info_2,
                               'mountpoint': mountpoint_2,
                               'comment': 'my comment 2'}
        self._util.insert_volume_attachment(volume_attachment_2)

        # query
        attachments = self._util.get_attachments_by_instance_id(instance_id)
        expected_1 = (volume_id_1, instance_id, str(connection_info_1),
                      mountpoint_1, 'my comment 1')
        actual_1 = (attachments[0][1], attachments[0][2], attachments[0][3],
                    attachments[0][4], attachments[0][7])
        self.assertEqual(expected_1, actual_1)
        expected_2 = (volume_id_2, instance_id, str(connection_info_2),
                      mountpoint_2, 'my comment 2')
        actual_2 = (attachments[1][1], attachments[1][2], attachments[1][3],
                    attachments[1][4], attachments[1][7])
        self.assertEqual(expected_2, actual_2)

    def test_insert_volume_attachment_error(self):
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume_attachment,
                          None)
        volume_id = str(uuid.uuid4())
        instance_id = str(uuid.uuid4())
        connection_info = {'wwpns': '0x5005500550055005;0x5005500550055006',
                           'lun': '0x1001100110011001'}
        attachment = {'instance_id': instance_id,
                      'connection_info': connection_info}
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume_attachment,
                          attachment)
        attachment = {'volume_id': volume_id,
                      'connection_info': connection_info}
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume_attachment,
                          attachment)
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id}
        self.assertRaises(exception.DatabaseException,
                          self._util.insert_volume_attachment,
                          attachment)

        # volume does not exist
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id,
                      'connection_info': connection_info}
        self.assertRaises(exception.ZVMVolumeError,
                          self._util.insert_volume_attachment,
                          attachment)
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)
        # FIXME  instance does not exist
        # volume has already been attached on the instance
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id,
                      'connection_info': connection_info}
        self._util.insert_volume_attachment(attachment)
        self.assertRaises(exception.ZVMVolumeError,
                          self._util.insert_volume_attachment,
                          attachment)

        self._util.delete_volume_attachment(volume_id, instance_id)
        self._util.delete_volume(volume_id)
        # FIXME  delete instance

    def test_insert_volume_attachment(self):
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)
        # FIXME insert an instance
        instance_id = str(uuid.uuid4())
        connection_info = {'wwpns': '0x5005500550055005;0x5005500550055006',
                           'lun': '0x1001100110011001'}
        mountpoint = '/dev/vda'
        comment = 'my comment'
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id,
                      'connection_info': connection_info,
                      'mountpoint': mountpoint,
                      'comment': comment}
        self._util.insert_volume_attachment(attachment)

        attachment = self._util.get_attachment_by_volume_id(volume_id)
        expected = (volume_id, instance_id, str(connection_info),
                    mountpoint, 'my comment')
        actual = (attachment[1], attachment[2], attachment[3], attachment[4],
                  attachment[7])
        self.assertEqual(expected, actual)

        # clean test volume
        self._util.delete_volume_attachment(volume_id, instance_id)
        self._util.delete_volume(volume_id)
        # FIXME  delete instance

    def test_delete_volume_attachment_error(self):
        volume_id = str(uuid.uuid4())
        instance_id = str(uuid.uuid4())
        self.assertRaises(exception.DatabaseException,
                          self._util.delete_volume_attachment,
                          None, instance_id)
        self.assertRaises(exception.DatabaseException,
                          self._util.delete_volume_attachment,
                          volume_id, None)
        # volume is not attached on the instance
        self.assertRaises(exception.ZVMVolumeError,
                          self._util.delete_volume_attachment,
                          volume_id, instance_id)

    def test_delete_volume_attachment(self):
        volume = {'protocol_type': 'fc', 'size': '3G'}
        volume_id = self._util.insert_volume(volume)
        # FIXME insert an instance
        instance_id = str(uuid.uuid4())
        connection_info = {'wwpns': '0x5005500550055005;0x5005500550055006',
                           'lun': '0x1001100110011001'}
        mountpoint = '/dev/vda'
        comment = 'my comment'
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id,
                      'connection_info': connection_info,
                      'mountpoint': mountpoint,
                      'comment': comment}
        self._util.insert_volume_attachment(attachment)

        attachment = self._util.get_attachment_by_volume_id(volume_id)
        self.assertIsNotNone(attachment)

        self._util.delete_volume_attachment(volume_id, instance_id)
        attachment = self._util.get_attachment_by_volume_id(volume_id)
        self.assertIsNone(attachment)

        self._util.delete_volume(volume_id)
        # FIXME  delete instance
