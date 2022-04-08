# Copyright 2017, 2021 IBM Corp.
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
        self.db_op.new('1111', 0)
        self.db_op.new('2222', 1)
        try:
            fcp_list = self.db_op.get_all()
            self.assertEqual(2, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual(0, fcp[4])

            fcp = fcp_list[1]
            self.assertEqual('2222', fcp[0])
            self.assertEqual(1, fcp[4])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('2222')

    def test_assign(self):
        self.db_op.new('1111', 0)

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
        self.db_op.new('1111', 0)
        self.db_op.new('1112', 0)
        self.db_op.new('1113', 0)
        self.db_op.new('1114', 0)

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

    def test_get_reserved_fcps_from_assigner(self):
        self.db_op.new('1111', 0)
        self.db_op.new('1112', 1)

        try:
            # case1: connections == 0 and reserve == 0
            self.db_op.assign('1111', 'user1', update_connections=False)
            self.db_op.assign('1112', 'user2', update_connections=False)
            fcp_list = self.db_op.get_reserved_fcps_from_assigner('user2')
            self.assertEqual(0, len(fcp_list))
            # case2: reserve != 0 and connections == 0
            self.db_op.reserve('1112')
            fcp_list = self.db_op.get_reserved_fcps_from_assigner('user2')
            self.assertEqual(1, len(fcp_list))
            fcp = fcp_list[0]
            self.assertEqual('1112', fcp[0])
            self.assertEqual('user2', fcp[1])
            # case3: connections != 0 and reserve == 0
            self.db_op.unreserve('1112')
            self.db_op.assign('1111', 'user1')
            fcp_list = self.db_op.get_reserved_fcps_from_assigner('user1')
            self.assertEqual(0, len(fcp_list))
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')

    def test_get_allocated_fcps_from_assigner(self):
        self.db_op.new('1111', 0)
        self.db_op.new('1112', 1)

        try:
            # case1: connections == 0
            self.db_op.assign('1111', 'user1', update_connections=False)
            self.db_op.assign('1112', 'user1', update_connections=False)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner('user1')
            self.assertEqual(0, len(fcp_list))
            # case2: connections != 0
            self.db_op.assign('1111', 'user2', update_connections=True)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner('user2')
            self.assertEqual(1, len(fcp_list))
            # case3: reserve != 0
            self.db_op.assign('1112', 'user2', update_connections=False)
            self.db_op.reserve('1112')
            fcp_list = self.db_op.get_allocated_fcps_from_assigner('user2')
            self.assertEqual(2, len(fcp_list))

            fcp = fcp_list[0]
            self.assertEqual('1111', fcp[0])
            self.assertEqual('user2', fcp[1])
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('1112')

    def test_get_from_fcp(self):
        self.db_op.new('1111', 0)
        self.db_op.new('1112', 2)

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
        self.db_op.new('1111', 2)
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

    def test_get_fcp_pair_with_same_index(self):
        '''
        get_fcp_pair_with_same_index() only returns
        two possible values:
        case 1
            an empty list(i.e. [])
            if no fcp exist in DB
        case 2
           randomly choose a pair of below combinations:
           [1a00,1b00] ,[1a01,1b01] ,[1a02,1b02]...
           rather than below combinations:
           [1a00,1b02] ,[1a03,1b00]
           [1a02], [1b03]
        case 3
           an empty list(i.e. [])
           if no expected pair found
        '''
        try:
            # test case1
            fcp_list = self.db_op.get_fcp_pair_with_same_index()
            self.assertEqual([], fcp_list)
            # test case2
            self.db_op.new('1a00', 0)
            self.db_op.new('1a01', 0)
            self.db_op.new('1a02', 0)
            self.db_op.new('1a03', 0)
            self.db_op.new('1a04', 0)
            self.db_op.new('1a05', 0)
            self.db_op.new('1b00', 1)
            self.db_op.new('1b01', 1)
            self.db_op.new('1b02', 1)
            self.db_op.new('1b03', 1)
            self.db_op.new('1b04', 1)
            self.db_op.increase_usage('1a00')
            self.db_op.increase_usage('1a00')
            self.db_op.increase_usage('1a02')
            self.db_op.reserve('1a02')
            self.db_op.reserve('1b00')
            free_comment = {
                'state': 'free',
                'owner': 'NONE'
            }
            active_comment = {
                'state': 'active',
                'owner': 'JACK0004'
            }
            free_fcps = (
                '1a01', '1a03', '1a04',
                '1b01', '1b03'
            )
            active_fcps = (
                '1a00', '1b04'
            )
            for fcp in free_fcps:
                self.db_op.update_comment_of_fcp(fcp, free_comment)
            for fcp in active_fcps:
                self.db_op.update_comment_of_fcp(fcp, active_comment)
            # expected result
            expected_pairs_1 = {('1a01', '1b01'), ('1a03', '1b03')}
            result = set()
            for i in range(10):
                fcp_list = self.db_op.get_fcp_pair_with_same_index()
                result.add(tuple(fcp_list))
            self.assertEqual(result, expected_pairs_1)
            # test case3
            self.db_op.reserve('1a01')
            self.db_op.reserve('1b03')
            for i in range(10):
                fcp_list = self.db_op.get_fcp_pair_with_same_index()
                self.assertEqual(fcp_list, [])
        finally:
            self.db_op.delete('1a00')
            self.db_op.delete('1a01')
            self.db_op.delete('1a02')
            self.db_op.delete('1a03')
            self.db_op.delete('1a04')
            self.db_op.delete('1a05')
            self.db_op.delete('1b00')
            self.db_op.delete('1b01')
            self.db_op.delete('1b02')
            self.db_op.delete('1b03')
            self.db_op.delete('1b04')

    def test_get_fcp_pair(self):
        '''
        get_fcp_pair() only returns
        the following possible values:
        e.g. When FCP DB contains FCPs from 2 paths
        case 1
            randomly choose one available FCP per path:
            [1a03,1b00] ,[1a02,1b01], [1a02,1b02]...
            [1a00,1b01] ,[1a01,1b02], ...
        case 2
            if CONF.volume.min_fcp_paths_count is enabled,
            (such as, min_fcp_paths_count = 1)
            then it may also return a single FCP
            (such as, [1a02], [1b03], ...)
        case 3
           an empty list(i.e. [])
           if no expected pair found
        '''
        try:
            # test case1
            self.db_op.new('1a00', 0)
            self.db_op.new('1a01', 0)
            self.db_op.new('1a02', 0)
            self.db_op.new('1a03', 0)
            self.db_op.new('1a04', 0)
            self.db_op.new('1a05', 0)
            self.db_op.new('1b00', 1)
            self.db_op.new('1b01', 1)
            self.db_op.new('1b02', 1)
            self.db_op.new('1b03', 1)
            self.db_op.new('1b04', 1)
            self.db_op.increase_usage('1a00')
            self.db_op.increase_usage('1a00')
            self.db_op.increase_usage('1a02')
            self.db_op.reserve('1a02')
            self.db_op.reserve('1b00')
            free_comment = {
                'state': 'free',
                'owner': 'NONE'
            }
            active_comment = {
                'state': 'active',
                'owner': 'JACK0004'
            }
            free_fcps = (
                '1a01', '1a03', '1a04',
                '1b01', '1b03'
            )
            active_fcps = (
                '1a00', '1b04'
            )
            for fcp in free_fcps:
                self.db_op.update_comment_of_fcp(fcp, free_comment)
            for fcp in active_fcps:
                self.db_op.update_comment_of_fcp(fcp, active_comment)
            # expected result
            expected_pairs_1 = {
                ('1a01', '1b01'), ('1a01', '1b03'),
                ('1a03', '1b01'), ('1a03', '1b03'),
                ('1a04', '1b01'), ('1a04', '1b03')
            }
            result = set()
            for i in range(300):
                fcp_list = self.db_op.get_fcp_pair()
                result.add(tuple(fcp_list))
            self.assertEqual(result, expected_pairs_1)
            # test case2
            CONF.volume.min_fcp_paths_count = 1
            self.db_op.reserve('1a01')
            self.db_op.reserve('1a03')
            self.db_op.reserve('1a04')
            expected_pairs_2 = {('1b01',), ('1b03',)}
            result = set()
            for i in range(10):
                fcp_list = self.db_op.get_fcp_pair()
                result.add(tuple(fcp_list))
            self.assertEqual(result, expected_pairs_2)
            # test case3
            self.db_op.reserve('1b01')
            self.db_op.reserve('1b03')
            # expected result
            for i in range(10):
                fcp_list = self.db_op.get_fcp_pair()
                self.assertEqual(fcp_list, [])
        finally:
            self.db_op.delete('1a00')
            self.db_op.delete('1a01')
            self.db_op.delete('1a02')
            self.db_op.delete('1a03')
            self.db_op.delete('1a04')
            self.db_op.delete('1a05')
            self.db_op.delete('1b00')
            self.db_op.delete('1b01')
            self.db_op.delete('1b02')
            self.db_op.delete('1b03')
            self.db_op.delete('1b04')

    def test_find_and_reserve(self):
        self.db_op.new('1111', 1)
        self.db_op.new('1112', 2)

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
        self.db_op.new('1111', 0)

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

    def test_decrease_usage_of_not_exist_fcp(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.decrease_usage, 'xxxx')

    def test_increase_usage_of_not_exist_fcp(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.increase_usage, 'xxxx')

    def test_increase_usage_by_assigner(self):
        self.db_op.new('1111', 0)
        try:
            self.db_op.assign('1111', 'auser')
            self.db_op.increase_usage_by_assigner('1111', 'buser')
            fcp_list = self.db_op.get_all()
            fcp = fcp_list[0]
            self.assertEqual(u'buser', fcp[1])
        finally:
            self.db_op.delete('1111')

    def test_update_path_of_fcp(self):
        self.db_op.new('2222', 0)
        try:
            self.db_op.assign('2222', 'auser')
            self.db_op.update_path_of_fcp('2222', 1)
            res = self.db_op.get_from_fcp('2222')
            self.assertEqual(1, res[0][4])
        finally:
            self.db_op.delete('2222')

    def test_update_comment_of_fcp(self):
        self.db_op.new('2222', 0)
        try:
            new_comment = {'state': 'offline'}
            self.db_op.update_comment_of_fcp('2222', new_comment)
            self.assertDictEqual(self.db_op.get_comment_of_fcp('2222'),
                                 new_comment)
            new_comment = {'owner': 'fakeuser'}
            self.db_op.update_comment_of_fcp('2222', new_comment)
            self.assertDictEqual(self.db_op.get_comment_of_fcp('2222'),
                                 {'owner': 'fakeuser'})
        finally:
            self.db_op.delete('2222')

    def test_get_all_fcps_exception(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.get_all_fcps_of_assigner,
                          None)

    def test_get_all_fcps(self):
        """Test case when assigner_id specified or not.
        """
        self.db_op.new('1111', 0)
        self.db_op.new('2222', 1)
        try:
            # case 1, the assigner not specified
            res = self.db_op.get_all_fcps_of_assigner()
            # Format of return is like:
            # [(fcp_id, userid, connections, reserved, path, comment), (...)].
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 8)
            # connections == 0
            self.assertEqual(res[0][2], 0)
            # path of 1111 is 0
            self.assertEqual(res[0][4], 0)
            # path of 2222 is 1
            self.assertEqual(res[1][4], 1)
            # case 2, assigner_id
            self.db_op.assign('1111', 'fakeuser')
            res = self.db_op.get_all_fcps_of_assigner(assigner_id='fakeuser')
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 8)
            self.assertEqual(res[0][1], 'fakeuser')
        finally:
            self.db_op.delete('1111')
            self.db_op.delete('2222')


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
    def test_add_guest_registered(self, get_uuid):
        meta = 'fakemeta=1, fakemeta2=True'
        net = 1
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest_registered(self.userid, meta, net)
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

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_metadata_with_userid_exist(self, get_uuid):
        meta = 'os_version=rhel8.3'
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        # Delete
        guest = self.db_op.get_guest_metadata_with_userid(self.userid)
        self.assertListEqual([(u'os_version=rhel8.3',)], guest)
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')
        guests = self.db_op.get_guest_metadata_with_userid(self.userid)
        self.assertListEqual([], guests)

    @mock.patch.object(uuid, 'uuid4')
    def test_get_guest_metadata_with_userid_no_exist(self, get_uuid):
        meta = u''
        get_uuid.return_value = u'ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c'
        self.db_op.add_guest(self.userid, meta=meta)
        guest = self.db_op.get_guest_metadata_with_userid(self.userid)
        self.assertListEqual([(u'',)], guest)
        # Delete
        self.db_op.delete_guest_by_id('ad8f352e-4c9e-4335-aafa-4f4eb2fcc77c')

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


class CpupoolDbOperatorTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(CpupoolDbOperatorTestCase, cls).setUpClass()
        cls.db_op = database.CpupoolDbOperator()

    @classmethod
    def tearDownClass(cls):
        with database.get_cpupool_conn() as conn:
            conn.execute("DROP TABLE cpupools")
        super(CpupoolDbOperatorTestCase, cls).tearDownClass()

    def test_check_existence_by_name(self):
        self.assertRaises(exception.SDKObjectNotExistError,
            self.db_op._check_existence_by_name, 'NOTEXIST')

        p = self.db_op._check_existence_by_name('NOTEXIST',
                                                ignore=True)
        self.assertIsNone(p)

    def test_insert_duplicate(self):
        limittype = 'NOLIM'
        cputype = 'IFL'
        comments = 'no'
        self.db_op.add_cpupool('DUMMY', limittype, cputype, comments)

        self.assertRaises(exception.SDKObjectAlreadyExistError,
                          self.db_op.add_cpupool, 'DUMMY',
                          limittype, cputype, comments)
        self.db_op.delete_cpupool('DUMMY')

    def test_delete_not_exist(self):
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.delete_cpupool, 'NOTEXIST')

    def test_one_cpupool(self):
        limittype = 'NOLIM'
        cputype = 'IFL'
        comments = 'no'
        self.db_op.add_cpupool('DUMMY', limittype, cputype, comments)

        cpupools = self.db_op.get_cpupools()
        self.assertEqual(1, len(cpupools))
        exp = [('DUMMY', 'NOLIM', 'IFL', 'no')]
        self.assertListEqual(exp, cpupools)

        cpupools = self.db_op.get_cpupool('DUMMY')
        exp = ('DUMMY', 'NOLIM', 'IFL', 'no')
        self.assertEqual(exp, cpupools)

        self.db_op.delete_cpupool('DUMMY')
        cpupools = self.db_op.get_cpupools()
        self.assertEqual(0, len(cpupools))

    def test_multiple_cpupools(self):
        limittype = 'NOLIM'
        cputype = 'IFL'
        comments = 'no'
        self.db_op.add_cpupool('DUMMY1', limittype, cputype, comments)
        self.db_op.add_cpupool('DUMMY2', 'LIMIT', cputype, comments)
        self.db_op.add_cpupool('DUMMY3', limittype, 'CP', comments)

        cpupools = self.db_op.get_cpupools()
        self.assertEqual(3, len(cpupools))
        exp = [('DUMMY1', 'NOLIM', 'IFL', 'no'),
               ('DUMMY2', 'LIMIT', 'IFL', 'no'),
               ('DUMMY3', 'NOLIM', 'CP', 'no')]
        self.assertListEqual(exp, cpupools)

        self.db_op.delete_cpupool('DUMMY2')
        cpupools = self.db_op.get_cpupools()
        self.assertEqual(2, len(cpupools))
        exp = [('DUMMY1', 'NOLIM', 'IFL', 'no'),
               ('DUMMY3', 'NOLIM', 'CP', 'no')]
        self.assertListEqual(exp, cpupools)

        self.db_op.delete_cpupool('DUMMY1')
        self.db_op.delete_cpupool('DUMMY3')
