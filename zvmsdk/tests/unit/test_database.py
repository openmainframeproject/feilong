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
import uuid

from zvmsdk import config
from zvmsdk import database
from zvmsdk.database import VolumeDbOperator
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.tests.unit import base


CONF = config.CONF
LOG = log.LOG


class NetworkDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(NetworkDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.NetworkDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_network_conn() as conn:
            conn.execute("DROP TABLE switch")
        super(NetworkDbOperatorTestCase, cls).tearDownClass()

    @mock.patch.object(database.NetworkDbOperator, '_create_switch_table')
    def test__init__(self, create_table):
        self.db_op.__init__()
        create_table.assert_called_once_with()

    def test_switch_add_record_for_nic(self):
        userid = 'testuser'
        interface = '1000'
        port = None

        # insert a record without port
        self.db_op.switch_add_record_for_nic(userid, interface, port)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [(userid.upper(), interface, None, port, None)]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(userid)

        port = 'testport'
        # insert a record with port
        self.db_op.switch_add_record_for_nic(userid, interface, port)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [(userid.upper(), interface, None, port, None)]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(userid)
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    @mock.patch.object(database.NetworkDbOperator,
                       '_get_switch_by_user_interface')
    def test_switch_updat_record_with_switch_fail(self, get_record):
        get_record.return_value = None
        userid = 'testuser'
        interface = '1000'
        switch = 'testswitch'

        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.switch_updat_record_with_switch,
                          userid, interface, switch)

    def test_switch_updat_record_with_switch(self):
        userid = 'testuser'
        interface = '1000'
        port = 'testport'
        switch = 'testswitch'

        # insert a record first
        self.db_op.switch_add_record_for_nic(userid, interface, port)

        # update record with switch info
        self.db_op.switch_updat_record_with_switch(userid, interface, switch)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [(userid.upper(), interface, switch, port, None)]
        self.assertEqual(expected, switch_record)

        switch = None
        # update record to remove switch info
        self.db_op.switch_updat_record_with_switch(userid, interface, switch)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [(userid.upper(), interface, switch, port, None)]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(userid)
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_delete_record_for_userid(self):
        list = [('id01', '1000', 'port_id01'),
                ('id01', '2000', 'port_id02'),
                ('id02', '1000', 'port_id02'),
                ('id03', '1000', 'port_id03')]
        # insert multiple records
        for (userid, interface, port) in list:
            self.db_op.switch_add_record_for_nic(userid, interface, port)

        # delete specific records
        userid = 'id01'
        self.db_op.switch_delete_record_for_userid(userid)

        # query: specific records removed
        switch_record = self.db_op.switch_select_record_for_userid(userid)
        expected = []
        self.assertEqual(expected, switch_record)

        # query: the other records still exist
        switch_record = self.db_op.switch_select_record_for_userid('id02')
        expected = [('ID02', '1000', None, 'port_id02', None)]
        self.assertEqual(expected, switch_record)
        switch_record = self.db_op.switch_select_record_for_userid('id03')
        expected = [('ID03', '1000', None, 'port_id03', None)]
        self.assertEqual(expected, switch_record)

        # clean test switch and check
        self.db_op.switch_delete_record_for_userid('id02')
        self.db_op.switch_delete_record_for_userid('id03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_delete_record_for_nic(self):
        list = [('id01', '1000', 'port_id01'),
                ('id01', '2000', 'port_id02'),
                ('id02', '1000', 'port_id02'),
                ('id03', '1000', 'port_id03')]
        # insert multiple records
        for (userid, interface, port) in list:
            self.db_op.switch_add_record_for_nic(userid, interface, port)

        # query: specific record in the table
        record = ('ID01', '1000', None, 'port_id01', None)
        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record in switch_record, True)

        # delete one specific record
        userid = 'id01'
        interface = '1000'
        self.db_op.switch_delete_record_for_nic(userid, interface)

        # query: specific record not in the table
        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record not in switch_record, True)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('id01')
        self.db_op.switch_delete_record_for_userid('id02')
        self.db_op.switch_delete_record_for_userid('id03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_select_table(self):
        # empty table
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

        list = [('id01', '1000', 'port_id01'),
                ('id01', '2000', 'port_id02'),
                ('id02', '1000', 'port_id02'),
                ('id03', '1000', 'port_id03')]
        # insert multiple records
        for (userid, interface, port) in list:
            self.db_op.switch_add_record_for_nic(userid, interface, port)

        # query: specific record in the table
        record = [('ID01', '1000', None, 'port_id01', None),
                  ('ID01', '2000', None, 'port_id02', None),
                  ('ID02', '1000', None, 'port_id02', None),
                  ('ID03', '1000', None, 'port_id03', None)]

        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('id01')
        self.db_op.switch_delete_record_for_userid('id02')
        self.db_op.switch_delete_record_for_userid('id03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_select_record_for_userid(self):
        list = [('id01', '1000', 'port_id01'),
                ('id01', '2000', 'port_id02'),
                ('id02', '1000', 'port_id02'),
                ('id03', '1000', 'port_id03')]
        # insert multiple records
        for (userid, interface, port) in list:
            self.db_op.switch_add_record_for_nic(userid, interface, port)

        # query: specific record in the table
        record = [('ID01', '1000', None, 'port_id01', None),
                  ('ID01', '2000', None, 'port_id02', None)]

        switch_record = self.db_op.switch_select_record_for_userid('id01')
        self.assertEqual(record, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('id01')
        self.db_op.switch_delete_record_for_userid('id02')
        self.db_op.switch_delete_record_for_userid('id03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)


class VolumeDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(VolumeDbOperatorTestCase, cls).setUpClass()
        cls._util = VolumeDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_volume_conn() as conn:
            conn.execute("DROP TABLE volumes")
            conn.execute("DROP TABLE volume_attachments")
        super(VolumeDbOperatorTestCase, cls).tearDownClass()

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
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.insert_volume, volume)

        # protocol_type absent
        volume = {'size': '3G'}
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.insert_volume, volume)
        volume = {'protocol_type': 'fc'}
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.update_volume, volume)
        volume = {}
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.insert_volume_attachment,
                          None)
        volume_id = str(uuid.uuid4())
        instance_id = str(uuid.uuid4())
        connection_info = {'wwpns': '0x5005500550055005;0x5005500550055006',
                           'lun': '0x1001100110011001'}
        attachment = {'instance_id': instance_id,
                      'connection_info': connection_info}
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.insert_volume_attachment,
                          attachment)
        attachment = {'volume_id': volume_id,
                      'connection_info': connection_info}
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.insert_volume_attachment,
                          attachment)
        attachment = {'volume_id': volume_id,
                      'instance_id': instance_id}
        self.assertRaises(exception.SDKDatabaseException,
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
        self.assertRaises(exception.SDKDatabaseException,
                          self._util.delete_volume_attachment,
                          None, instance_id)
        self.assertRaises(exception.SDKDatabaseException,
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


class GuestDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(GuestDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.GuestDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_guest_conn() as conn:
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
        self.assertRaises(exception.SDKGuestOperationError,
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
        self.db_op.delete_guest_by_id('Fakeid')

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
        self.db_op.delete_guest_by_id('Fakeuser')

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
        self.assertRaises(exception.SDKInternalError,
                          self.db_op.update_guest_by_id,
                          'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_update_guest_by_id_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
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
        self.assertRaises(exception.SDKInternalError,
                          self.db_op.update_guest_by_userid,
                          'FakeUser')
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_update_guest_by_userid_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
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
        with database.get_image_conn() as conn:
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
        self.db_op.image_add_record(
            imagename, imageosdistro, md5sum, disk_size_units,
            image_size_in_bytes, type)
        # Query the record
        image_record = self.db_op.image_query_record(imagename)
        self.assertEqual(1, len(image_record))
        self.assertListEqual(
            [(u'test', u'rhel6.5', u'c73ce117eef8077c3420bfc8f473ac2f',
              u'3338:CYL', u'5120000', u'netboot', None)],
            image_record)

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
        self.db_op.image_add_record(
            imagename, imageosdistro, md5sum, disk_size_units,
            image_size_in_bytes, type)
        self.assertRaises(
            exception.SDKDatabaseException,
            self.db_op.image_add_record,
            imagename, imageosdistro, md5sum, disk_size_units,
            image_size_in_bytes, type)
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
        self.db_op.image_add_record(
            imagename1, imageosdistro, md5sum, disk_size_units,
            image_size_in_bytes, type)
        self.db_op.image_add_record(
            imagename2, imageosdistro, md5sum, disk_size_units,
            image_size_in_bytes, type)

        image_records = self.db_op.image_query_record()
        self.assertEqual(2, len(image_records))
        self.assertListEqual(
            [(u'testimage1', u'rhel6.5', u'c73ce117eef8077c3420bfc8f473ac2f',
              u'3338:CYL', u'5120000', u'netboot', None),
             (u'testimage2', u'rhel6.5', u'c73ce117eef8077c3420bfc8f473ac2f',
              u'3338:CYL', u'5120000', u'netboot', None)],
            image_records)
        # Clean up the images
        self.db_op.image_delete_record(imagename1)
        self.db_op.image_delete_record(imagename2)
