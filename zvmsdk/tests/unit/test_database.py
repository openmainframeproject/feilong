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
        cls.userid = 'FAKEUSER'
        cls.rec_list = [('ID01', '1000', 'port_id01'),
                        ('ID01', '2000', 'port_id02'),
                        ('ID02', '1000', 'port_id02'),
                        ('ID03', '1000', 'port_id03')]

    @classmethod
    def tearDownClass(cls):
        with database.get_network_conn() as conn:
            conn.execute("DROP TABLE switch")
        super(NetworkDbOperatorTestCase, cls).tearDownClass()

    @mock.patch.object(database.NetworkDbOperator, '_create_switch_table')
    def test__init__(self, create_table):
        self.db_op.__init__()
        create_table.assert_called_once_with()

    def test_switch_add_record(self):
        interface = '1000'
        port = None

        # insert a record without port
        self.db_op.switch_add_record(self.userid, interface, port)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [{'userid': self.userid, 'interface': interface,
                     'switch': None, 'port': port, 'comments': None}]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(self.userid)

        port = 'testport'
        # insert a record with port
        self.db_op.switch_add_record(self.userid, interface, port)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [{'userid': self.userid, 'interface': interface,
                     'switch': None, 'port': port, 'comments': None}]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(self.userid)
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_add_record_migrated(self):
        interface = '1000'
        switch = 'XCATVSW1'
        self.db_op.switch_add_record_migrated(self.userid, interface, switch)
        # query
        switch_record = self.db_op.switch_select_table()
        expected = [{'userid': self.userid, 'interface': interface,
                     'switch': switch, 'port': None, 'comments': None}]
        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(self.userid)

    @mock.patch.object(database.NetworkDbOperator,
                       '_get_switch_by_user_interface')
    def test_switch_update_record_with_switch_fail(self, get_record):
        get_record.return_value = None
        interface = '1000'
        switch = 'testswitch'

        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.switch_update_record_with_switch,
                          self.userid, interface, switch)

    def test_switch_update_record_with_switch(self):
        interface = '1000'
        port = 'testport'
        switch = 'testswitch'

        # insert a record first
        self.db_op.switch_add_record(self.userid, interface, port)

        # update record with switch info
        self.db_op.switch_update_record_with_switch(self.userid, interface,
                                                    switch)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [{'userid': self.userid, 'interface': interface,
                     'switch': switch, 'port': port, 'comments': None}]
        self.assertEqual(expected, switch_record)

        switch = None
        # update record to remove switch info
        self.db_op.switch_update_record_with_switch(self.userid, interface,
                                                    switch)

        # query
        switch_record = self.db_op.switch_select_table()
        expected = [{'userid': self.userid, 'interface': interface,
                     'switch': switch, 'port': port, 'comments': None}]

        self.assertEqual(expected, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid(self.userid)
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_delete_record_for_userid(self):
        # insert multiple records
        for (userid, interface, port) in self.rec_list:
            self.db_op.switch_add_record(userid, interface, port)
            self.addCleanup(self.db_op.switch_delete_record_for_userid, userid)

        # delete specific records
        userid = 'ID01'
        self.db_op.switch_delete_record_for_userid(userid)

        # query: specific records removed
        switch_record = self.db_op.switch_select_record_for_userid(userid)
        expected = []
        self.assertEqual(expected, switch_record)

        # query: the other records still exist
        switch_record = self.db_op.switch_select_record_for_userid('ID02')
        expected = [{'userid': 'ID02', 'interface': '1000',
                     'switch': None, 'port': 'port_id02', 'comments': None}]

        self.assertEqual(expected, switch_record)
        switch_record = self.db_op.switch_select_record_for_userid('ID03')
        expected = [{'userid': 'ID03', 'interface': '1000',
                     'switch': None, 'port': 'port_id03', 'comments': None}]
        self.assertEqual(expected, switch_record)

    def test_switch_delete_record_for_nic(self):
        # insert multiple records
        for (userid, interface, port) in self.rec_list:
            self.db_op.switch_add_record(userid, interface, port)
            self.addCleanup(self.db_op.switch_delete_record_for_userid, userid)

        # query: specific record in the table
        record = {'userid': 'ID01', 'interface': '1000',
                  'switch': None, 'port': 'port_id01', 'comments': None}
        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record in switch_record, True)

        # delete one specific record
        userid = 'ID01'
        interface = '1000'
        self.db_op.switch_delete_record_for_nic(userid, interface)

        # query: specific record not in the table
        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record not in switch_record, True)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('ID01')
        self.db_op.switch_delete_record_for_userid('ID02')
        self.db_op.switch_delete_record_for_userid('ID03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_select_table(self):
        # empty table
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

        # insert multiple records
        for (userid, interface, port) in self.rec_list:
            self.db_op.switch_add_record(userid, interface, port)
            self.addCleanup(self.db_op.switch_delete_record_for_userid, userid)

        # query: specific record in the table
        record = [{'userid': 'ID01', 'interface': '1000',
                   'switch': None, 'port': 'port_id01', 'comments': None},
                  {'userid': 'ID01', 'interface': '2000',
                   'switch': None, 'port': 'port_id02', 'comments': None},
                  {'userid': 'ID02', 'interface': '1000',
                   'switch': None, 'port': 'port_id02', 'comments': None},
                  {'userid': 'ID03', 'interface': '1000',
                   'switch': None, 'port': 'port_id03', 'comments': None}]

        switch_record = self.db_op.switch_select_table()
        self.assertEqual(record, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('ID01')
        self.db_op.switch_delete_record_for_userid('ID02')
        self.db_op.switch_delete_record_for_userid('ID03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_select_record_for_userid(self):
        # insert multiple records
        for (userid, interface, port) in self.rec_list:
            self.db_op.switch_add_record(userid, interface, port)
            self.addCleanup(self.db_op.switch_delete_record_for_userid, userid)

        # query: specific record in the table
        record = [{'userid': 'ID01', 'interface': '1000',
                   'switch': None, 'port': 'port_id01', 'comments': None},
                  {'userid': 'ID01', 'interface': '2000',
                   'switch': None, 'port': 'port_id02', 'comments': None}]

        switch_record = self.db_op.switch_select_record_for_userid('ID01')
        self.assertEqual(record, switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('ID01')
        self.db_op.switch_delete_record_for_userid('ID02')
        self.db_op.switch_delete_record_for_userid('ID03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)

    def test_switch_select_record(self):
        # insert multiple records
        for (userid, interface, port) in self.rec_list:
            self.db_op.switch_add_record(userid, interface, port)
            self.addCleanup(self.db_op.switch_delete_record_for_userid, userid)

        # all record
        record = [{'userid': 'ID01', 'interface': '1000',
                   'switch': 'switch01', 'port': 'port_id01',
                   'comments': None},
                  {'userid': 'ID01', 'interface': '2000',
                   'switch': 'switch01', 'port': 'port_id02',
                   'comments': None},
                  {'userid': 'ID02', 'interface': '1000',
                   'switch': 'switch02', 'port': 'port_id02',
                   'comments': None},
                  {'userid': 'ID03', 'interface': '1000',
                   'switch': 'switch02', 'port': 'port_id03',
                   'comments': None}]

        # update record with switch info
        self.db_op.switch_update_record_with_switch('ID01', '1000', 'switch01')
        self.db_op.switch_update_record_with_switch('ID01', '2000', 'switch01')
        self.db_op.switch_update_record_with_switch('ID02', '1000', 'switch02')
        self.db_op.switch_update_record_with_switch('ID03', '1000', 'switch02')

        switch_record = self.db_op.switch_select_record()
        self.assertEqual(record, switch_record)

        switch_record = self.db_op.switch_select_record(userid='ID01')
        self.assertEqual([record[0], record[1]], switch_record)

        switch_record = self.db_op.switch_select_record(nic_id='port_id02')
        self.assertEqual([record[1], record[2]], switch_record)

        switch_record = self.db_op.switch_select_record(vswitch='switch02')
        self.assertEqual([record[2], record[3]], switch_record)

        switch_record = self.db_op.switch_select_record(nic_id='port_id02',
                                                        vswitch='switch02')
        self.assertEqual([record[2]], switch_record)

        # clean test switch
        self.db_op.switch_delete_record_for_userid('ID01')
        self.db_op.switch_delete_record_for_userid('ID02')
        self.db_op.switch_delete_record_for_userid('ID03')
        switch_record = self.db_op.switch_select_table()
        expected = []
        self.assertEqual(expected, switch_record)


class FCPDbOperatorTestCase(base.SDKTestCase):
    @classmethod
    def setUpClass(cls):
        super(FCPDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.FCPDbOperator()

    # tearDownClass deleted to work around bug of 'no such table:fcp'

    def test_new(self):
        self.db_op.new('1111')

        fcp_list = self.db_op.get_all()
        self.assertEqual(1, len(fcp_list))
        fcp = fcp_list[0]
        self.assertEqual('1111', fcp[0])

        self.db_op.delete('1111')

    def test_assign(self):
        self.db_op.new('1111')

        try:
            self.db_op.assign('1111', 'incuser')

            fcp_list = self.db_op.get_all()

            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.db_op.increase_usage('1111')

            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual(2, fcp[2])

        finally:
            self.db_op.delete('1111')

    def test_get_all_free(self):
        self.db_op.new('1111')
        self.db_op.new('1112')
        self.db_op.new('1113')
        self.db_op.new('1114')

        try:
            self.db_op.assign('1111', 'user1')
            self.db_op.assign('1112', 'user2')
            self.db_op.decrease_usage('1112')
            self.db_op.reserve('1114')

            fcp_list = self.db_op.get_all_free_unreserved()
            self.assertEqual(2, len(fcp_list))
            fcp_list.sort()
            fcp = fcp_list[0]
            self.assertEqual('1112', fcp[0])
            fcp = fcp_list[1]
            self.assertEqual('1113', fcp[0])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')
            self.db_op.delete('1113')
            self.db_op.delete('1114')

    def test_get_from_assigner(self):
        self.db_op.new('1111')
        self.db_op.new('1112')

        try:
            self.db_op.assign('1111', 'user1')
            self.db_op.assign('1112', 'user2')

            fcp_list = self.db_op.get_from_assigner('user2')
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1112', fcp[0])
            self.assertEqual('user2', fcp[1])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')

    def test_get_from_fcp(self):
        self.db_op.new('1111')
        self.db_op.new('1112')

        try:
            self.db_op.assign('1111', 'user1')
            self.db_op.assign('1112', 'user2')

            fcp_list = self.db_op.get_from_fcp('1111')
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual('user1', fcp[1])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')

    def test_reserve_unreserve(self):
        self.db_op.new('1111')
        try:
            self.db_op.reserve('1111')
            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])

            self.assertEqual(1, fcp[3])

            self.db_op.unreserve('1111')
            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])

            self.assertEqual(0, fcp[3])
        finally:
            self.db_op.delete('1111')

    def test_find_and_reserve(self):
        self.db_op.new('1111')
        self.db_op.new('1112')

        try:
            fcp = self.db_op.find_and_reserve()
            self.assertEqual('1111', fcp)

            fcp_list = self.db_op.get_from_fcp('1111')
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual(1, fcp[3])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')

    def test_decrease_usage(self):
        self.db_op.new('1111')

        try:
            self.db_op.assign('1111', 'decuser')
            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.db_op.increase_usage('1111')
            self.db_op.increase_usage('1111')

            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual(3, fcp[2])

            self.db_op.decrease_usage('1111')
            fcp_list = self.db_op.get_all()
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual(2, fcp[2])

        finally:
            self.db_op.delete('1111')


class GuestDbOperatorTestCase(base.SDKTestCase):
    @classmethod
    def setUpClass(cls):
        super(GuestDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.GuestDbOperator()
        cls.userid = 'FAKEUSER'

    @classmethod
    def tearDownClass(cls):
        with database.get_guest_conn() as conn:
            conn.execute("DROP TABLE guests")
        super(GuestDbOperatorTestCase, cls).tearDownClass()

    @mock.patch.object(uuid, 'uuid4')
    def test_add_guest(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Query, the guest should in table
        guests = self.db_op.get_guest_list()
        self.assertEqual(1, len(guests))
        self.assertListEqual([(u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                               u'FAKEUSER', u'fakemeta=1, fakemeta2=True', 0,
                               u'')], guests)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_add_guest_migrated(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        net = 1
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest_migrated(self.userid, meta, net)
        # Query, the guest should in table
        guests = self.db_op.get_guest_list()
        self.assertEqual(1, len(guests))
        self.assertListEqual([(u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                               u'FAKEUSER', u'fakemeta=1, fakemeta2=True', 1,
                               None)], guests)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_add_guest_twice_error(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Add same user the second time
        self.assertRaises(exception.SDKGuestOperationError,
                          self.db_op.add_guest, self.userid)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_delete_guest_by_id(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Delete
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        guests = self.db_op.get_guest_list()
        self.assertListEqual([], guests)

    def test_delete_guest_by_id_not_exist(self):
        self.db_op.delete_guest_by_id('Fakeid')

    @mock.patch.object(uuid, 'uuid4')
    def test_delete_guest_by_userid(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Delete
        self.db_op.delete_guest_by_userid(self.userid)
        guests = self.db_op.get_guest_list()
        self.assertListEqual([], guests)

    def test_delete_guest_by_userid_not_exist(self):
        self.db_op.delete_guest_by_id(self.userid)

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_by_userid(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # get guest
        guest = self.db_op.get_guest_by_userid(self.userid)
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'fakemeta=1, fakemeta2=True', 0,
                          u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_get_metadata_by_userid(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77d'
        self.db_op.add_guest(self.userid, meta=meta)
        # get metadata
        metadata = self.db_op.get_metadata_by_userid(self.userid)
        self.assertEqual(meta, metadata)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77d')

    def test_get_guest_by_userid_not_exist(self):
        guest = self.db_op.get_guest_by_userid(self.userid)
        self.assertEqual(None, guest)

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_by_id(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # get guest
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'fakemeta=1, fakemeta2=True', 0,
                          u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_get_guest_by_id_not_exist(self):
        guest = self.db_op.get_guest_by_id(
            'aa8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual(None, guest)

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_id(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Update
        self.db_op.update_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c', meta='newmeta',
            net_set='1', comments='newcomment')
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'newmeta', 1,
                          u'newcomment'), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_id_wrong_input(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
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
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Update
        self.db_op.update_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c', meta='',
            comments='')
        guest = self.db_op.get_guest_by_id(
            'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'', 0, u''), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Update
        self.db_op.update_guest_by_userid(
            self.userid, meta='newmetauserid', net_set='1',
            comments={'newcommentuserid': '1'})
        guest = self.db_op.get_guest_by_userid(self.userid)
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'newmetauserid', 1,
                          u'{"newcommentuserid": "1"}'), guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid_wrong_input(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Update
        self.assertRaises(exception.SDKInternalError,
                          self.db_op.update_guest_by_userid,
                          self.userid)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

    def test_update_guest_by_userid_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.update_guest_by_userid,
                          self.userid,
                          meta='newmeta')

    @mock.patch.object(uuid, 'uuid4')
    def test_update_guest_by_userid_null_value(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Update
        self.db_op.update_guest_by_userid(
            self.userid, meta='', comments='')
        guest = self.db_op.get_guest_by_userid(self.userid)
        self.assertEqual((u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c',
                          u'FAKEUSER', u'', 0, u'""'), guest)
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
            [{'imagename': u'test',
              'imageosdistro': u'rhel6.5',
              'md5sum': u'c73ce117eef8077c3420bfc8f473ac2f',
              'disk_size_units': u'3338:CYL',
              'image_size_in_bytes': u'5120000',
              'type': u'netboot',
              'comments': None}], image_record)

        # Delete it
        self.db_op.image_delete_record(imagename)
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.image_query_record,
                          imagename)

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
            [{'imagename': u'testimage1',
              'imageosdistro': u'rhel6.5',
              'md5sum': u'c73ce117eef8077c3420bfc8f473ac2f',
              'disk_size_units': u'3338:CYL',
              'image_size_in_bytes': u'5120000',
              'type': u'netboot',
              'comments': None},
             {'imagename': u'testimage2',
              'imageosdistro': u'rhel6.5',
              'md5sum': u'c73ce117eef8077c3420bfc8f473ac2f',
              'disk_size_units': u'3338:CYL',
              'image_size_in_bytes': u'5120000',
              'type': u'netboot',
              'comments': None}], image_records)
        # Clean up the images
        self.db_op.image_delete_record(imagename1)
        self.db_op.image_delete_record(imagename2)
