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

    def _insert_data_into_fcp_table(self, fcp_info_list):
        # insert data into all columns of fcp table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp "
                             "(fcp_id, assigner_id, connections, "
                             "reserved, wwpn_npiv, wwpn_phy, chpid, "
                             "state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)

    def _insert_data_into_template_table(self, templates_info):
        # insert data into all columns of template table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template "
                             "(id, name, description, is_default) "
                             "VALUES (?, ?, ?, ?)", templates_info)

    def _insert_data_into_template_fcp_mapping_table(self,
                                                     template_fcp_mapping):
        # insert data into all columns of template_fcp_mapping table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template_fcp_mapping "
                             "(fcp_id, tmpl_id, path) "
                             "VALUES (?, ?, ?)", template_fcp_mapping)

    def _insert_data_into_template_sp_mapping_table(self,
                                                    template_sp_mapping):
        # insert data into all columns of template_sp_mapping table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template_sp_mapping "
                             "(sp_name, tmpl_id) "
                             "VALUES (?, ?)", template_sp_mapping)

    #########################################################
    #             Test cases for Table fcp                  #
    #########################################################
    def test_default_values_of_fcp_table(self):
        """Test the default values of columns in fcp table"""
        pass

    def test_unreserve_fcps(self):
        """Test API unreserve_fcps"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id),
                         ('2222', '', 0, 1, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id),
                         ('3333', '', 0, 1, 'c05076de33000333',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # test API function
        try:
            self.db_op.unreserve_fcps(fcp_id_list)
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            # check default values of (assigner_id, connections) are correct
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            # check reserved value
            self.assertEqual(0, reserved)
            userid, reserved, conn = self.db_op.get_usage_of_fcp('2222')
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            self.assertEqual(0, reserved)
            userid, reserved, conn = self.db_op.get_usage_of_fcp('3333')
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            self.assertEqual(0, reserved)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_reserve_fcps(self):
        """Test API reserve_fcps"""
        pass

    def test_bulk_insert(self):
        """Test API bulk_insert_zvm_fcp_info_into_fcp_table"""
        pass

    def test_bulk_delete(self):
        """Test API bulk_delete_from_fcp_table"""
        pass

    def test_bulk_update_fcp_info(self):
        """Test API bulk_update_zvm_fcp_info_in_fcp_table"""
        pass

    def test_bulk_update_fcp_state(self):
        """Test API bulk_update_state_in_fcp_table"""
        pass

    def test_assign(self):
        """Test API assign"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        """
        format of item in fcp_info_list:
        (fcp_id, assigner_id, connections, reserved, wwpn_npiv, wwpn_phy,
         chpid, state, owner, tmpl_id)
        """
        fcp_info_list = [('1111', '', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', '',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # test API function
        try:
            # case1: update_connections == False
            self.db_op.assign('1111', 'user1', update_connections=False)
            fcp_list = self.db_op.get_all()
            # only one record exists
            self.assertEqual(1, len(fcp_list))
            # check values(fcp_id, assigner_id, connections)
            self.assertEqual('1111', fcp_list[0][0])
            self.assertEqual('user1', fcp_list[0][1])
            self.assertEqual(0, fcp_list[0][2])
            # case2: default update_connections == True
            self.db_op.assign('1111', 'user2')
            fcp_list = self.db_op.get_all()
            self.assertEqual('1111', fcp_list[0][0])
            self.assertEqual('user2', fcp_list[0][1])
            self.assertEqual(1, fcp_list[0][2])
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_all_fcps_of_assigner(self):
        """Test API get_all_fcps_of_assigner with assigner_id parameter"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        """
        format of item in fcp_info_list:
        (fcp_id, assigner_id, connections, reserved, wwpn_npiv, wwpn_phy,
         chpid, state, owner, tmpl_id)
        """
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('2222', 'user2', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'owner2',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # test API function
        try:
            # case 1, the assigner not specified
            res = self.db_op.get_all_fcps_of_assigner()
            # Format of return is like:
            # [(fcp_id, userid, connections, reserved, wwpn_npiv, wwpn_phy,
            #   chpid, state, owner, tmpl_id), (...)].
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 10)
            # connections == 0
            self.assertEqual(res[0][2], 0)
            # case 2, specify an assigner_id
            res = self.db_op.get_all_fcps_of_assigner(assigner_id='user2')
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 10)
            self.assertEqual(res[0][1], 'user2')
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_all_fcps_exception(self):
        """Test API get_all_fcps_of_assigner when no data in DB"""
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.get_all_fcps_of_assigner,
                          None)

    def test_get_usage_of_fcp(self):
        """Test API get_usage_of_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('', userid)
            self.assertEqual(2, conn)
            self.assertEqual(1, reserved)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_update_usage_of_fcp(self):
        """Test API update_usage_of_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user2', 1, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            # update reserved to 1, connection to 2, assigner_id to user2
            self.db_op.update_usage_of_fcp('1111', 'user2', 1, 2)
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('user2', userid)
            self.assertEqual(1, reserved)
            self.assertEqual(2, conn)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_increase_usage(self):
        """Test API increase_usage"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            self.db_op.increase_usage('1111')
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('', userid)
            self.assertEqual(3, conn)
            self.assertEqual(1, reserved)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_increase_usage_of_not_exist_fcp(self):
        """Test API increase_usage when fcp id not exist"""
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.increase_usage, 'xxxx')

    def test_increase_usage_by_assigner(self):
        """Test API increase_usage_by_assigner"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user1', 1, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            self.db_op.increase_usage_by_assigner('1111', 'user1')
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('user1', userid)
            self.assertEqual(2, conn)
            self.assertEqual(1, reserved)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_increase_usage_by_not_exist_assigner(self):
        """Test API increase_usage_by_assigner when assigner_id not exist"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 1, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # record belonging to user2 does not exist
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.increase_usage_by_assigner,
                          '1111', 'fakeuser')
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_decrease_usage_of_not_exist_fcp(self):
        """Test API decrease_usage when fcp_id not exist"""
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.decrease_usage, 'xxxx')

    def test_decrease_usage_no_connections(self):
        """Test API decrease_usage when connections is 0"""
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 0, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # decrease when connections == 0
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.decrease_usage, '1111')
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_decrease_usage(self):
        """Test API decrease_usage"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            self.db_op.decrease_usage('1111')
            userid, reserved, conn = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('', userid)
            self.assertEqual(1, conn)
            self.assertEqual(1, reserved)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_connections_from_assigner(self):
        """Test API get_connections_from_assigner"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user1', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 3, 1, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'owner2',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            conn = self.db_op.get_connections_from_assigner('user1')
            self.assertEqual(5, conn)
            conn = self.db_op.get_connections_from_assigner('user2')
            self.assertEqual(0, conn)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_connections_from_fcp(self):
        """Test API get_connections_from_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id),
                         ('2222', '', 3, 1, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'user1',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            conn = self.db_op.get_connections_from_fcp('1111')
            self.assertEqual(2, conn)
            conn = self.db_op.get_connections_from_fcp('2222')
            self.assertEqual(3, conn)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_all(self):
        pass

    def test_get_from_fcp(self):
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'user1',
                          template_id),
                         ('2222', '', 3, 1, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'user1',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            fcp_list = self.db_op.get_from_fcp('1111')
            self.assertEqual(1, len(fcp_list))
            self.assertEqual('1111', fcp_list[0][0])
            self.assertEqual(2, fcp_list[0][2])
            self.assertEqual(1, fcp_list[0][3])
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_wwpns_of_fcp(self):
        pass

    def test_update_wwpns_of_fcp(self):
        pass

    #########################################################
    #       Test cases for Table template_fcp_mapping       #
    #########################################################
    def test_update_path_of_fcp(self):
        """Test API update_usage_of_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 1),
                        ('2222', template_id, 2)]
        fcp_id_list = [fcp_info[0] for fcp_info in template_fcp]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        try:
            self.db_op.update_path_of_fcp('1111', 3, template_id)
            path = self.db_op.get_path_of_fcp('1111', template_id)
            self.assertEqual(3, path)
        finally:
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_bulk_delete_fcp_from_template(self):
        """Test API delete_fcp_from_path"""
        pass

    def test_get_path_count(self):
        pass

    def test_get_fcp_list_of_template(self):
        pass

    #########################################################
    #            Test cases for Table template              #
    #########################################################
    def test_default_values_of_template_table(self):
        """Test the default values of columns in fcp table"""
        pass

    def test_get_default_fcp_template(self):
        pass

    def test_fcp_template_exist_in_db(self):
        pass

    #########################################################
    #       Test cases for Table template_sp_mapping        #
    #########################################################
    def test_default_values_of_template_sp_mapping_table(self):
        """Test the default values of columns in fcp table"""
        pass

    def test_sp_name_exist_in_db(self):
        pass

    def test_fcp_template_sp_mapping_exist_in_db(self):
        template_sp_mapping = [('0001', 'v7k60'), ('0002', 'ds8k')]
        # insert test data into table template_sp_mapping
        self._insert_data_into_template_sp_mapping_table(template_sp_mapping)
        try:
            res1 = self.db_op.fcp_template_sp_mapping_exist_in_db('0001', 'v7k60')
            self.assertTrue(res1)
            res2 = self.db_op.fcp_template_sp_mapping_exist_in_db('0002', 'v7k60')
            self.assertFalse(res2)
        finally:
            self.db_op.delete_fcp_template('0001')
            self.db_op.delete_fcp_template('0002')

    #########################################################
    #        Test cases related to multiple tables          #
    #########################################################
    def test_get_allocated_fcps_from_assigner(self):
        """Test API get_allocated_fcps_from_assigner"""
        # prepare data for fcp template "1111;2222"
        # insert test data into table template_fcp_mapping
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 0),
                        ('2222', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert test data into table fcp
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            # case1: reserved and connections == 0
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user1', template_id)
            self.assertEqual(0, len(fcp_list))
            # case2: reserved == 0 and connections != 0
            #   increase connections to 1
            self.db_op.increase_usage('1111')
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user1', template_id)
            self.assertEqual(1, len(fcp_list))
            # case3: reserved != 0 and connections == 0
            self.db_op.reserve_fcps(['2222'], 'user2', template_id)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(1, len(fcp_list))
            # case4: reserve !=0 and connections != 0
            self.db_op.assign('1111', 'user2', update_connections=True)
            self.db_op.assign('2222', 'user2', update_connections=True)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(2, len(fcp_list))
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_get_reserved_fcps_from_assigner(self):
        # prepare data for fcp template "1111;2222"
        # insert test data into table fcp
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', 'active', 'owner1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert test data into table template_fcp_mapping
        template_fcp = [('1111', template_id, 0),
                        ('2222', template_id, 1)]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        try:
            # case1: reserved and connections == 0
            fcp_list = self.db_op.get_reserved_fcps_from_assigner(
                'user1', template_id)
            self.assertEqual(0, len(fcp_list))
            # case2: reserved == 0 and connections != 0
            #   increase connections to 1
            self.db_op.increase_usage('1111')
            fcp_list = self.db_op.get_reserved_fcps_from_assigner(
                'user1', template_id)
            self.assertEqual(0, len(fcp_list))
            # case3: reserved !=0 and connection == 0
            #   set reserved to 1
            self.db_op.reserve_fcps(['2222'], 'user2', template_id)
            fcp_list = self.db_op.get_reserved_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(1, len(fcp_list))
            # case4: reserve !=0 and connections != 0
            #   set reserved to 1
            self.db_op.reserve_fcps(fcp_id_list, 'user2', template_id)
            #   set connections to 1
            self.db_op.assign('1111', 'user2', update_connections=True)
            self.db_op.assign('2222', 'user2', update_connections=True)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(2, len(fcp_list))
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_get_fcp_devices_with_same_index(self):
        '''Test get_fcp_devices_with_same_index

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
        # prepare data for fcp template "1111;2222"
        template_id = 'fakehost-1111-1111-1111-111111111111'
        # insert test data into table fcp
        # Usage in test data:
        #   1a00 usage is connections == 2, reserved == 0
        #   1a02 usage is connections == 1, reserved == 1
        #   1b00 usage is connections == 0, reserved == 1
        #   others are connections ==0, reserved == 0
        # State in test data:
        #   1a01, 1a03, 1a04, 1b01, 1b03 are free
        #   1a00, 1b04 are active
        #   others are ''
        # WWPNs in test data:
        #   1b02 wwpns are empty, others are normal
        fcp_info_list = [('1a00', '', 2, 0, 'c05076de33000a00',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('1a01', '', 0, 0, 'c05076de33000a01',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1a02', '', 1, 1, 'c05076de33000a02',
                          'c05076de33002641', '27', '', 'owner1',
                          ''),
                         ('1a03', '', 0, 0, 'c05076de33000a03',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1a04', '', 0, 0, 'c05076de33000a04',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1b00', '', 0, 1, 'c05076de33000b00',
                          'c05076de33002642', '30', '', 'owner1',
                          ''),
                         ('1b01', '', 0, 0, 'c05076de33000b01',
                          'c05076de33002642', '30', 'free', 'owner1',
                          ''),
                         ('1b02', '', 0, 0, '',
                          '', '30', 'notfound', 'owner1',
                          ''),
                         ('1b03', '', 0, 0, 'c05076de33000b03',
                          'c05076de33002642', '30', 'free', 'owner1',
                          ''),
                         ('1b04', '', 0, 0, 'c05076de33000b04',
                          'c05076de33002642', '30', 'active', 'owner1',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert test data into table template_fcp_mapping
        template_fcp = [('1a00', template_id, 0),
                        ('1a01', template_id, 0),
                        ('1a02', template_id, 0),
                        ('1a03', template_id, 0),
                        ('1a04', template_id, 0),
                        ('1b00', template_id, 1),
                        ('1b01', template_id, 1),
                        ('1b02', template_id, 1),
                        ('1b03', template_id, 1),
                        ('1b04', template_id, 1)]
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        try:
            # test case1
            fcp_list = self.db_op.get_fcp_devices_with_same_index('fakeid')
            self.assertEqual([], fcp_list)
            # test case2
            # expected result
            #   can not return 1a04 because it does not have 1bxx with same ndex
            expected_results = {('1a01', '1b01'), ('1a03', '1b03')}
            result = set()
            for i in range(10):
                fcp_list = self.db_op.get_fcp_devices_with_same_index(
                    template_id)
                result.add(tuple([fcp[0] for fcp in fcp_list]))
            self.assertEqual(result, expected_results)
            # test case3:
            self.db_op.reserve_fcps(['1a01', '1b03'], '', template_id)
            # after reserve_fcps, no available pair records with same index
            fcp_list = self.db_op.get_fcp_devices_with_same_index(
                template_id)
            self.assertEqual(fcp_list, [])
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_get_fcp_devices(self):
        '''Test API get_fcp_devices

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
        # prepare data for fcp template "1a00-1a04;1b00-1b04"
        template_id = 'fakehost-1111-1111-1111-111111111111'
        # insert test data into table fcp
        # Usage in test data:
        #   1a00 usage is connections == 2, reserved == 0
        #   1a02 usage is connections == 1, reserved == 1
        #   1b00 usage is connections == 0, reserved == 1
        #   others are connections ==0, reserved == 0
        # State in test data:
        #   1a01, 1a03, 1a04, 1b01, 1b03 are free
        #   1a00, 1b04 are active
        #   others are ''
        # WWPNs in test data:
        #   1b02 wwpns are empty, others are normal
        fcp_info_list = [('1a00', '', 2, 0, 'c05076de33000a00',
                          'c05076de33002641', '27', 'active', 'owner1',
                          ''),
                         ('1a01', '', 0, 0, 'c05076de33000a01',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1a02', '', 1, 1, 'c05076de33000a02',
                          'c05076de33002641', '27', '', 'owner1',
                          ''),
                         ('1a03', '', 0, 0, 'c05076de33000a03',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1a04', '', 0, 0, 'c05076de33000a04',
                          'c05076de33002641', '27', 'free', 'owner1',
                          ''),
                         ('1b00', '', 0, 1, 'c05076de33000b00',
                          'c05076de33002642', '30', '', 'owner1',
                          ''),
                         ('1b01', '', 0, 0, 'c05076de33000b01',
                          'c05076de33002642', '30', 'free', 'owner1',
                          ''),
                         ('1b02', '', 0, 0, '',
                          '', '30', 'notfound', 'owner1',
                          ''),
                         ('1b03', '', 0, 0, 'c05076de33000b03',
                          'c05076de33002642', '30', 'free', 'owner1',
                          ''),
                         ('1b04', '', 0, 0, 'c05076de33000b04',
                          'c05076de33002642', '30', 'active', 'owner1',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert test data into table template_fcp_mapping
        template_fcp = [('1a00', template_id, 0),
                        ('1a01', template_id, 0),
                        ('1a02', template_id, 0),
                        ('1a03', template_id, 0),
                        ('1a04', template_id, 0),
                        ('1b00', template_id, 1),
                        ('1b01', template_id, 1),
                        ('1b02', template_id, 1),
                        ('1b03', template_id, 1),
                        ('1b04', template_id, 1)]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        # insert new test data
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        try:
            # expected result
            all_possible_pairs = {
                ('1a01', '1b01'), ('1a01', '1b03'),
                ('1a03', '1b01'), ('1a03', '1b03'),
                ('1a04', '1b01'), ('1a04', '1b03')
            }
            # exhaustion to get all possible pairs
            result = set()
            for i in range(300):
                fcp_list = self.db_op.get_fcp_devices(template_id)
                # fcp_list include fcp_id, wwpn_npiv, wwpn_phy
                # we test fcp_id only
                result.add(tuple([fcp[0] for fcp in fcp_list]))
            self.assertEqual(result, all_possible_pairs)
            # test case2: no available fcp device in one path
            #   reserve all fcp devices in path 0
            self.db_op.reserve_fcps(['1a01', '1a03', '1a04'], '', template_id)
            # expected result
            for i in range(10):
                fcp_list = self.db_op.get_fcp_devices(template_id)
                self.assertEqual(fcp_list, [])
            # test case3: min_fcp_paths_count was set to 1
            CONF.volume.min_fcp_paths_count = 1
            all_possible_pairs = {('1b01',), ('1b03',)}
            result = set()
            for i in range(10):
                fcp_list = self.db_op.get_fcp_devices(template_id)
                result.add(tuple([fcp[0] for fcp in fcp_list]))
            self.assertEqual(result, all_possible_pairs)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_create_fcp_template(self):
        pass

    def test_get_fcp_templates(self):
        pass

    def test_get_host_default_fcp_template(self):
        pass

    def test_get_sp_default_fcp_template(self):
        pass

    def test_get_fcp_template_by_assigner_id(self):
        pass

    def test_get_fcp_templates_details(self):
        pass


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
