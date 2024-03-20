#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017, 2023 IBM Corp.
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
import random
from mock import Mock, patch

from zvmsdk import utils
from zvmsdk import config
from zvmsdk import database
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.tests.unit import base


CONF = config.CONF
LOG = log.LOG


def mock_reset(*args):
    """Reset mock objects in args"""
    for m in args:
        if isinstance(m, Mock):
            m.reset_mock(return_value=True, side_effect=True)


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

    #################################################
    #            Helper Methods                     #
    #################################################
    def get_path_of_fcp(self, fcp_id, fcp_template_id):
        with database.get_fcp_conn() as conn:
            result = conn.execute("SELECT path FROM template_fcp_mapping "
                                  "WHERE fcp_id=? and tmpl_id=?",
                                  (fcp_id, fcp_template_id))
            path_info = result.fetchone()
            return path_info['path']

    def _insert_data_into_fcp_table(self, fcp_info_list):
        # insert data into all columns of fcp table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp "
                             "(fcp_id, assigner_id, connections, "
                             "reserved, wwpn_npiv, wwpn_phy, chpid, pchid,"
                             "state, owner, tmpl_id) VALUES "
                             "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcp_info_list)

    def _insert_data_into_template_table(self, templates_info):
        # insert data into all columns of template table
        with database.get_fcp_conn() as conn:
            conn.executemany("INSERT INTO template "
                             "(id, name, description, is_default, min_fcp_paths_count) "
                             "VALUES (?, ?, ?, ?, ?)", templates_info)

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

    def _prepare_fcp_info_for_a_test_fcp_template(self):
        """ Prepare FCP device info for test
        1. create a FCP Multipath Template with fcp_devices
        2. set some of the fcp_devices as inuse

        Note: Remember to do cleanup after using the func
        Example code-block:
          try:
              tid = self._prepare_fcp_info_for_a_test_fcp_template()
              # do some thing with tid
              test_my_function()
          finally:
              # clean up by call _purge_fcp_db()
              _purge_fcp_db()
        """
        #   a. create_fcp_template
        #   b. bulk_insert_zvm_fcp_info_into_fcp_table
        #       insert '1A00-1A03;1B00-1B03'
        #   c. reserve_fcps
        #       set assigner_id and tmpl_id
        #       ('1a01', '1b03')
        #   d. increase_connections
        #       set connections
        #       ('1a01', '1b03')
        tmpl_id = 'fake_id_' + str(random.randint(100000, 999999))
        kwargs = {
            'name': 'new_name',
            'description': 'new_desc',
            'fcp_devices': '1A00-1A03;1B00-1B03',
            'host_default': False,
            'default_sp_list': []}
        self.db_op.create_fcp_template(
            tmpl_id, kwargs['name'], kwargs['description'],
            utils.expand_fcp_list(kwargs['fcp_devices']),
            host_default=kwargs['host_default'],
            default_sp_list=kwargs['default_sp_list'],
            min_fcp_paths_count=2)
        fcp_info = [
            ('1a01', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1'),
            ('1b03', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1')]
        # set FCP ('1a01', '1b03') as inuse
        try:
            self.db_op.bulk_insert_zvm_fcp_info_into_fcp_table(fcp_info)
        except exception.SDKGuestOperationError as ex:
            if 'UNIQUE constraint failed' in str(ex):
                pass
            else:
                raise
        reserve_info = (('1a01', '1b03'), 'user1', tmpl_id)
        self.db_op.reserve_fcps(*reserve_info)
        self.increase_connections('1a01')
        self.increase_connections('1b03')
        return tmpl_id

    @staticmethod
    def increase_connections(fcp_id):
        """Increase the connections by 1 of a given FCP device"""
        with database.get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "fcp_id=?", (fcp_id,))
            fcp_info = result.fetchone()
            if not fcp_info:
                msg = 'FCP device %s does not exist in FCP DB.' % fcp_id
                LOG.error(msg)
                obj_desc = "FCP device %s" % fcp_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID='volume')
            connections = fcp_info['connections'] + 1

            conn.execute("UPDATE fcp SET connections=? "
                         "WHERE fcp_id=?", (connections, fcp_id))
            # check the result
            result = conn.execute("SELECT connections FROM fcp "
                                  "WHERE fcp_id=?", (fcp_id,))
            connections = result.fetchone()['connections']
            return connections

    @staticmethod
    def _purge_fcp_db():
        """ Delete all records in the fcp related tables """
        with database.get_fcp_conn() as conn:
            conn.execute("DELETE FROM fcp")
            conn.execute("DELETE FROM template")
            conn.execute("DELETE FROM template_fcp_mapping")
            conn.execute("DELETE FROM template_sp_mapping")

    #########################################################
    #             Test cases for Table fcp                  #
    #########################################################
    def test_unreserve_fcps(self):
        """Test API unreserve_fcps"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id),
                         ('2222', '', 0, 1, 'c05076de33000222',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id),
                         ('3333', '', 0, 1, 'c05076de33000333',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        self._insert_data_into_fcp_table(fcp_info_list)
        # test API function
        try:
            self.db_op.unreserve_fcps(fcp_id_list)
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('1111')
            # check default values of (assigner_id, connections) are correct
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            # check reserved value
            self.assertEqual(0, reserved)
            # tmpl_id set to ''
            self.assertEqual('', tmpl_id)
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('2222')
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            self.assertEqual(0, reserved)
            self.assertEqual('', tmpl_id)
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('3333')
            self.assertEqual('', userid)
            self.assertEqual(0, conn)
            self.assertEqual(0, reserved)
            self.assertEqual('', tmpl_id)
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

    def test_get_all_fcps_of_assigner(self):
        """Test API get_all_fcps_of_assigner with assigner_id parameter"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        """
        format of item in fcp_info_list:
        (fcp_id, assigner_id, connections, reserved, wwpn_npiv, wwpn_phy,
         chpid, pchid, state, owner, tmpl_id)
        """
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                          template_id),
                         ('2222', 'user2', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', '02e4', 'active', 'owner2',
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
            #   chpid, pchid, state, owner, tmpl_id), (...)].
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 11)
            # connections == 0
            self.assertEqual(res[0][2], 0)
            # case 2, specify an assigner_id
            res = self.db_op.get_all_fcps_of_assigner(assigner_id='user2')
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 11)
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
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('', userid)
            self.assertEqual(2, conn)
            self.assertEqual(1, reserved)
            self.assertEqual(template_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_update_usage_of_fcp(self):
        """Test API update_usage_of_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user2', 1, 1, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            # update reserved to 1, connection to 2, assigner_id to user2
            new_tmpl_id = 'newhost-1111-1111-1111-111111111111'
            self.db_op.update_usage_of_fcp('1111', 'user2', 1, 2, new_tmpl_id)
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('user2', userid)
            self.assertEqual(1, reserved)
            self.assertEqual(2, conn)
            self.assertEqual(new_tmpl_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_decrease_connections_of_not_exist_fcp(self):
        """Test API decrease_connections when fcp_id not exist"""
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.decrease_connections, 'xxxx')

    def test_decrease_connections_no_connections(self):
        """Test API decrease_connections when connections is 0"""
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 0, 1, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        # decrease when connections == 0
        self.assertRaises(exception.SDKObjectNotExistError,
                          self.db_op.decrease_connections, '1111')
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_decrease_connections(self):
        """Test API decrease_connections"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                          template_id)]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            self.db_op.decrease_connections('1111')
            userid, reserved, conn, tmpl_id = self.db_op.get_usage_of_fcp('1111')
            self.assertEqual('', userid)
            self.assertEqual(1, conn)
            self.assertEqual(1, reserved)
            self.assertEqual(template_id, tmpl_id)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)

    def test_get_connections_from_fcp(self):
        """Test API get_connections_from_fcp"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', '', 2, 1, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
                          template_id),
                         ('2222', '', 3, 1, 'c05076de33000222',
                          'c05076de33002641', '27', '02e4', 'active', 'user1',
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

    def test_get_inuse_fcp_device_by_fcp_template(self):
        """ Test get_inuse_fcp_device_by_fcp_template """
        try:
            # prepare test data by set inuse FCP ('1a01', '1b03')
            tmpl_id = self._prepare_fcp_info_for_a_test_fcp_template()
            expected = {'1a01', '1b03'}
            fcps = self.db_op.get_inuse_fcp_device_by_fcp_template(tmpl_id)
            result = {f['fcp_id'] for f in fcps}
            self.assertEqual(expected, result)
        finally:
            self._purge_fcp_db()

    #########################################################
    #       Test cases for Table template_fcp_mapping       #
    #########################################################
    def test_update_path_of_fcp_device(self):
        """Test API update_usage_of_fcp_device"""
        # pre create data in FCP DB for test
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 1),
                        ('2222', template_id, 2)]
        fcp_id_list = [fcp_info[0] for fcp_info in template_fcp]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        try:
            self.db_op.update_path_of_fcp_device((3, '1111', template_id))
            path = self.get_path_of_fcp('1111', template_id)
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

    def test_bulk_delete_fcp_device_from_fcp_template(self):
        """ Test bulk_delete_fcp_device_from_fcp_template """
        try:
            # prepare test data by create a template
            # with FCP devices as 1A00-1A03;1B00-1B03
            tmpl_id = self._prepare_fcp_info_for_a_test_fcp_template()
            expected = {'1a00', '1a01', '1a03', '1b00', '1b01', '1b03'}
            rec = ((tmpl_id, '1a02'), (tmpl_id, '1b02'))
            self.db_op.bulk_delete_fcp_device_from_fcp_template(rec)
            # verify
            _, fcp_detail = self.db_op.get_fcp_templates_details([tmpl_id])
            fcp_in_db = {f['fcp_id'] for f in fcp_detail}
            self.assertEqual(expected, fcp_in_db)
        finally:
            self._purge_fcp_db()

    def test_bulk_insert_fcp_device_into_fcp_template(self):
        """ Test bulk_insert_fcp_device_into_fcp_template """
        try:
            # prepare test data by create a template
            # with FCP devices as 1A00-1A03;1B00-1B03
            tmpl_id = self._prepare_fcp_info_for_a_test_fcp_template()
            expected = {
                '1a00', '1a01', '1a02', '1a03', '1a04',
                '1b00', '1b01', '1b02', '1b03', '1b04'}
            # bulk insert FCPs 1a04,1b04
            rec = ((tmpl_id, '1a04', 0), (tmpl_id, '1b04', 1))
            self.db_op.bulk_insert_fcp_device_into_fcp_template(rec)
            # verify
            _, fcp_detail = self.db_op.get_fcp_templates_details([tmpl_id])
            fcp_in_db = {f['fcp_id'] for f in fcp_detail}
            self.assertEqual(expected, fcp_in_db)
        finally:
            self._purge_fcp_db()

    #########################################################
    #            Test cases for Table template              #
    #########################################################
    def test_fcp_template_exist_in_db(self):
        pass

    def test_update_basic_info_of_fcp_template(self):
        """ Test update_basic_info_of_fcp_template """
        try:
            # prepare test data by create 2 templates
            # with is_default as False
            tmpl_id_1 = self._prepare_fcp_info_for_a_test_fcp_template()
            tmpl_id_2 = self._prepare_fcp_info_for_a_test_fcp_template()
            # case1:
            # set tmpl_id_1 is_default as True
            expected_1 = ('name1', 'desc1', True, 2, tmpl_id_1)
            self.db_op.update_basic_info_of_fcp_template(expected_1)
            # verify
            info_1 = self.db_op.get_fcp_templates_details([tmpl_id_1])[0][0]
            result_1 = (
                info_1['name'], info_1['description'],
                bool(info_1['is_default']), info_1['min_fcp_paths_count'], tmpl_id_1)
            self.assertEqual(expected_1, result_1)
            info_2 = self.db_op.get_fcp_templates_details([tmpl_id_2])[0][0]
            self.assertEqual(False, bool(info_2['is_default']))

            # case2:
            # set tmpl_id_2 is_default as True
            expected_2 = ('name2', 'desc2', True, 2, tmpl_id_2)
            self.db_op.update_basic_info_of_fcp_template(expected_2)
            # verify
            info_2 = self.db_op.get_fcp_templates_details([tmpl_id_2])[0][0]
            result_2 = (
                info_2['name'], info_2['description'],
                bool(info_2['is_default']), info_2['min_fcp_paths_count'], tmpl_id_2)
            self.assertEqual(expected_2, result_2)
            info_1 = self.db_op.get_fcp_templates_details([tmpl_id_1])[0][0]
            self.assertEqual(False, bool(info_1['is_default']))

            # case3:
            # set both tmpl_id_1 and tmpl_id_2 as False for is_default
            expected_1 = ('name1', 'desc1', False, 2, tmpl_id_1)
            expected_2 = ('name2', 'desc2', False, 4, tmpl_id_2)
            self.db_op.update_basic_info_of_fcp_template(expected_1)
            self.db_op.update_basic_info_of_fcp_template(expected_2)
            info_1 = self.db_op.get_fcp_templates_details([tmpl_id_1])[0][0]
            self.assertEqual(False, bool(info_1['is_default']))
            info_2 = self.db_op.get_fcp_templates_details([tmpl_id_2])[0][0]
            self.assertEqual(False, bool(info_2['is_default']))
        finally:
            self._purge_fcp_db()

    #########################################################
    #       Test cases for Table template_sp_mapping        #
    #########################################################
    def test_sp_name_exist_in_db(self):
        pass

    def test_bulk_set_sp_default_by_fcp_template(self):
        """ Test bulk_set_sp_default_by_fcp_template """
        try:
            # create 1st template(tmpl_id_1)
            # with default_sp_list=['SP1', 'SP2']
            tmpl_id_1 = self._prepare_fcp_info_for_a_test_fcp_template()
            self.db_op.edit_fcp_template(tmpl_id_1,
                                         default_sp_list=['SP1', 'SP2'])
            # create 2nd template(tmpl_id_2)
            # with default_sp_list=['SP3', 'SP4']
            tmpl_id_2 = self._prepare_fcp_info_for_a_test_fcp_template()
            self.db_op.edit_fcp_template(tmpl_id_2,
                                         default_sp_list=['SP3', 'SP4'])
            # set tmpl_id_1 with ['SP3', 'SP4']
            self.db_op.bulk_set_sp_default_by_fcp_template(
                tmpl_id_1, ['SP3', 'SP4'])
            info = self.db_op.get_fcp_templates_details([tmpl_id_1])[0]
            result = {r['sp_name'].upper() for r in info}
            expected = {'SP3', 'SP4'}
            self.assertEqual(expected, result)
        finally:
            self._purge_fcp_db()

    #########################################################
    #        Test cases related to multiple tables          #
    #########################################################
    def test_get_allocated_fcps_from_assigner(self):
        """Test API get_allocated_fcps_from_assigner"""
        # prepare data for FCP Multipath Template "1111;2222"
        # insert test data into table template_fcp_mapping
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 0),
                        ('2222', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert test data into table fcp
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
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
            self.increase_connections('1111')
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user1', template_id)
            self.assertEqual(1, len(fcp_list))
            # case3: reserved != 0 and connections == 0
            self.db_op.reserve_fcps(['2222'], 'user2', template_id)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(1, len(fcp_list))
            # case4: reserve !=0 and connections != 0
            self.db_op.update_usage_of_fcp('1111', 'user2', 1, 1, template_id)
            self.db_op.update_usage_of_fcp('2222', 'user2', 1, 1, template_id)
            fcp_list = self.db_op.get_allocated_fcps_from_assigner(
                'user2', template_id)
            self.assertEqual(2, len(fcp_list))
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_get_reserved_fcps_from_assigner(self):
        # prepare data for FCP Multipath Template "1111;2222"
        # insert test data into table fcp
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
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
            self.increase_connections('1111')
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
            self.db_op.update_usage_of_fcp('1111', 'user2', 1, 1, template_id)
            self.db_op.update_usage_of_fcp('2222', 'user2', 1, 1, template_id)
            fcp_list = self.db_op.get_reserved_fcps_from_assigner(
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

        # delete dirty data from other test cases
        self._purge_fcp_db()
        # prepare data for FCP Multipath Template "1111;2222"
        template_id = 'fakehost-1111-1111-1111-111111111111'
        # insert test data into table fcp
        # Usage in test data:
        #   1a00 usage is connections == 2, reserved == 0
        #   1b00 usage is connections == 0, reserved == 1
        #   others are connections ==0, reserved == 0
        # State in test data:
        #   free:
        #       1a01/1b01/1c01 ~ 1a03/1b03/1c03
        #       1a04 1c00 1c04
        #   active:
        #       1a00 1b04
        #   others are ''
        fcp_info_list = [
            # fcp_id, assigner_id, connections, reserved, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner, tmpl_id
            ('1a00', '', 2, 0, 'wwpn_npiv', 'wwpn_phy', '27', '1111', 'active', 'owner1', ''),
            ('1a01', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', 'aaaa', 'free', 'none', ''),
            ('1a02', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', 'aaaa', 'free', 'none', ''),
            ('1a03', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', 'aaaa', 'free', 'none', ''),
            ('1a04', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', '1111', 'free', 'none', ''),

            ('1b00', '', 0, 1, 'wwpn_npiv', 'wwpn_phy', '30', '2222', '', '', ''),
            ('1b01', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', 'aaaa', 'free', 'none', ''),
            ('1b02', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', 'bbbb', 'free', 'none', ''),
            ('1b03', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', 'dddd', 'free', 'none', ''),
            ('1b04', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', '2222', 'active', 'owner1', ''),

            ('1c00', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '31', '3333', 'free', 'none', ''),
            ('1c01', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '31', 'cccc', 'free', 'none', ''),
            ('1c02', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '31', 'cccc', 'free', 'none', ''),
            ('1c03', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '31', 'dddd', 'free', 'none', ''),
            ('1c04', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '31', '3333', 'free', 'none', '')]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert test data into table template_fcp_mapping with 3 paths
        template_fcp = [  # path 0
                        ('1a00', template_id, 0),
                        ('1a01', template_id, 0),
                        ('1a02', template_id, 0),
                        ('1a03', template_id, 0),
                        ('1a04', template_id, 0),
                          # path 1
                        ('1b00', template_id, 1),
                        ('1b01', template_id, 1),
                        ('1b02', template_id, 1),
                        ('1b03', template_id, 1),
                        ('1b04', template_id, 1),
                          # path 2
                        ('1c00', template_id, 2),
                        ('1c01', template_id, 2),
                        ('1c02', template_id, 2),
                        ('1c03', template_id, 2),
                        ('1c04', template_id, 2)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # The following pchid_info results in
        # free_count_in_pchid_info =
        # {'AAAA': 1, 'BBBB': 3, 'CCCC': 2, 'DDDD': 2, 'EEEE': -9}
        pchid_info = {
            'AAAA': {'allocated': 127, 'max': 128},
            'BBBB': {'allocated': 107, 'max': 110},
            'CCCC': {'allocated': 126, 'max': 128},
            'DDDD': {'allocated': 108, 'max': 110},
            # EEEE is not used
            'EEEE': {'allocated': 99, 'max': 90}}
        try:
            # case1: non-existing template id
            LOG.info('--------- case1 ---------')
            fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index('fakeid', pchid_info)
            self.assertEqual([], fcp_list)
            self.assertTrue('No FCP device exists in FCP multipath template (id={})'
                            .format('fakeid') in empty_reason)

            # case2:
            # path0/path1/path2     AAAA BBBB CCCC DDDD     weight  valid
            # 1a01/1b01/1c01    min(0.5       2        )    0.5     No
            # 1a02/1b02/1c02    min(1    3    2        )    1       Yes
            # 1a03/1b03/1c03    min(1              1   )    1       Yes
            LOG.info('--------- case2 ---------')
            expected_set = {('1A02', '1B02', '1C02'), ('1A03', '1B03', '1C03')}
            result_set = set()
            for i in range(8):
                fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index(template_id, pchid_info)
                result_set.add(tuple(fcp['fcp_id'] for fcp in fcp_list))
            self.assertEqual(result_set, expected_set)
            self.assertEqual(empty_reason, '')

            # test case3: No eligible FCP device combination with the same index
            # after the following reserve_fcps, no available pair records with same index
            LOG.info('--------- case3 ---------')
            self.db_op.reserve_fcps(['1a02', '1b03'], '', template_id)
            fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index(template_id, pchid_info)
            self.assertEqual(fcp_list, [])
            self.assertTrue('Not enough free capacity of the following PCHIDs left. '
                            'Their free capacity is {}.'
                            .format(sorted(dict(AAAA=1).items()))
                            in empty_reason)

            # test case4: No FCP device combination matches the same index policy
            # after the following reserve_fcps,
            # only 1a04 is free in path 0, however, 1b04 & 1c04 are not free
            LOG.info('--------- case4 ---------')
            self.db_op.reserve_fcps(['1a00', '1a01', '1a02', '1a03'], '', template_id)
            fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index(template_id, pchid_info)
            self.assertEqual(fcp_list, [])
            self.assertTrue('No FCP device combination of FCP multipath template (id={}) '
                            'matches the same index policy.'
                            .format(template_id) in empty_reason)

            # test case5: free path count < total path count
            # after the following reserve_fcps, no free FCP left in path 0
            LOG.info('--------- case5 ---------')
            self.db_op.reserve_fcps(['1a00', '1a01', '1a02', '1a03', '1a04'], '', template_id)
            fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index(template_id, pchid_info)
            self.assertEqual(fcp_list, [])
            self.assertTrue('{} path(s) of template (id={}) does not have free FCP devices'
                            .format(1, template_id) in empty_reason)
        finally:
            self._purge_fcp_db()

    def test_get_fcp_devices_with_same_index_FCP_count_different(self):
        '''Test get_fcp_devices_with_same_index

        get_fcp_pair_with_same_index() only returns
        1 possible value since the fcp template has 2 paths, but the first path has 2 fcp and the second has 1:
        '''

        # delete dirty data from other test cases
        self._purge_fcp_db()
        # prepare data for FCP Multipath Template "1111;2222"
        template_id = 'fakehost-1111-1111-1111-111111111111'
        fcp_info_list = [
            # fcp_id, assigner_id, connections, reserved, wwpn_npiv, wwpn_phy, chpid, pchid, state, owner, tmpl_id
            ('1a00', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', 'AAAA', 'free', 'none', ''),
            ('1a01', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '27', 'AAAA', 'free', 'none', ''),

            ('1b00', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', 'BBBB', 'free', '', ''),
            ('1b01', '', 0, 0, 'wwpn_npiv', 'wwpn_phy', '30', 'BBBB', 'free', 'none', '')
           ]
        self._insert_data_into_fcp_table(fcp_info_list)
        # insert test data into table template_fcp_mapping with 2 paths
        template_fcp = [  # path 0
                        ('1a00', template_id, 0),
                        ('1a01', template_id, 0),

                          # path 1
                        ('1b00', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        pchid_info = {
            'AAAA': {'allocated': 120, 'max': 128},
            'BBBB': {'allocated': 107, 'max': 110}
        }

        try:
            fcp_list, empty_reason = self.db_op.get_fcp_devices_with_same_index(template_id, pchid_info)
            fcp_device_list = [fcp['fcp_id'] for fcp in fcp_list]
            self.assertEqual(['1A00', '1B00'], fcp_device_list)
        finally:
            self._purge_fcp_db()

    @patch('zvmsdk.database.FCPDbOperator.get_path_count')
    @patch('zvmsdk.database._FCP_CONN')
    @patch("zvmsdk.database.FCPDbOperator.get_free_pchids_by_fcp_template")
    @patch("zvmsdk.database.FCPDbOperator.get_min_fcp_paths_count")
    def test_get_fcp_devices(self, mock_min_path_count,
                             mock_free_pchids_per_path, mock_conn,
                             mock_total_path_count):
        '''Test get_fcp_devices'''
        fcp_template_id = 'fake_id'
        sql_string = (
            "SELECT fcp.fcp_id, fcp.wwpn_npiv, fcp.wwpn_phy, tf.path, fcp.pchid "
            "FROM template_fcp_mapping as tf "
            "INNER JOIN fcp "
            "ON tf.fcp_id=fcp.fcp_id "
            "WHERE tf.tmpl_id='{}' "
            "AND fcp.connections=0 "
            "AND fcp.reserved=0 "
            "AND fcp.state='free' "
            "AND fcp.wwpn_npiv IS NOT '' "
            "AND fcp.wwpn_phy IS NOT '' "
            "AND ({}) "
            "ORDER BY tf.path, fcp.pchid, fcp.fcp_id")
        # case1: total_path_count > min_path_count > free_path_count
        LOG.info('----- case1 ------')
        mock_min_path_count.return_value = 2
        mock_free_pchids_per_path.return_value = {1: ['AAAA', 'BBBB']}
        mock_total_path_count.return_value = 3
        pchid_info = {}
        expect = []
        # call
        result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
        # verify
        self.assertEqual(expect, result)
        self.assertTrue('However, free path count of template (id={}) is {}, '
                        'which is less than its minimum path count {}.'
                        .format(fcp_template_id, 1, 2) in empty_reason)
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

        # case2: min_path_count(2) < free_path_count(4) < total_path_count(6)
        #        and final_pchid_per_path is on 3 paths
        #        and only 1 combination has the largest weight
        #        and some PCHIDs are shared across some paths
        # >>> pp(pchids_per_path_combinations)
        # [{1: 'AAAA', 3: 'CCCC', 4: 'CCCC', 'weight': 0.0},
        # {1: 'AAAA', 3: 'CCCC', 4: 'DDDD', 'weight': -3.0},
        # {1: 'BBBB', 3: 'CCCC', 4: 'CCCC', 'weight': 0.0},
        # {1: 'BBBB', 3: 'CCCC', 4: 'DDDD', 'weight': -3.0},
        # {1: 'AAAA', 3: 'CCCC', 5: 'EEEE', 'weight': 0.0},
        # {1: 'BBBB', 3: 'CCCC', 5: 'EEEE', 'weight': 0.0},
        # {1: 'AAAA', 4: 'CCCC', 5: 'EEEE', 'weight': 0.0},
        # {1: 'AAAA', 4: 'DDDD', 5: 'EEEE', 'weight': -3.0},
        # {1: 'BBBB', 4: 'CCCC', 5: 'EEEE', 'weight': 0.0},
        # {1: 'BBBB', 4: 'DDDD', 5: 'EEEE', 'weight': -3.0},
        # {3: 'CCCC', 4: 'CCCC', 5: 'EEEE', 'weight': 8.5}, <----
        # {3: 'CCCC', 4: 'DDDD', 5: 'EEEE', 'weight': -3.0}]
        LOG.info('----- case2 ------')
        mock_min_path_count.return_value = 2
        mock_free_pchids_per_path.return_value = {
            1: ['AAAA', 'BBBB'],
            3: ['CCCC'],
            4: ['CCCC', 'DDDD'],
            5: ['EEEE']}
        mock_total_path_count.return_value = 6
        # mock execute(sql).fetchall in _get_one_random_fcp_combinations
        all_fcps = [
            {'fcp_id': '1c01', 'path': 3, 'pchid': 'cccc', 'wwpn_npiv': 'c1', 'wwpn_phy': 'x1'},
            {'fcp_id': '1c02', 'path': 3, 'pchid': 'cccc', 'wwpn_npiv': 'c2', 'wwpn_phy': 'x2'},
            {'fcp_id': '1c03', 'path': 4, 'pchid': 'cccc', 'wwpn_npiv': 'c3', 'wwpn_phy': 'x3'},
            {'fcp_id': '1c04', 'path': 4, 'pchid': 'cccc', 'wwpn_npiv': 'c4', 'wwpn_phy': 'x4'},
            {'fcp_id': '1e04', 'path': 5, 'pchid': 'eeee', 'wwpn_npiv': 'e1', 'wwpn_phy': 'y1'},
            {'fcp_id': '1e05', 'path': 5, 'pchid': 'eeee', 'wwpn_npiv': 'e2', 'wwpn_phy': 'y2'}]
        mock_conn.execute().fetchall.return_value = all_fcps
        # all_fcps_with_uppercase for later verify
        all_fcps_with_uppercase = all_fcps.copy()
        for fcp in all_fcps_with_uppercase:
            for k in fcp:
                if k in ('fcp_id', 'pchid'):
                    fcp[k] = fcp[k].upper()
        # free_count_in_pchid_info =
        # {'AAAA': 0, 'BBBB': 0, 'CCCC': 17, 'DDDD': -3, 'EEEE': 20}
        pchid_info = {
            'AAAA': {'allocated': 128, 'max': 128},
            'BBBB': {'allocated': 110, 'max': 110},
            'CCCC': {'allocated': 111, 'max': 128},
            'DDDD': {'allocated': 113, 'max': 110},
            'EEEE': {'allocated': 70, 'max': 90}}
        # prepare sql
        pchid_path_filter = ("(tf.path=3 AND fcp.pchid='CCCC') OR "
                             "(tf.path=4 AND fcp.pchid='CCCC') OR "
                             "(tf.path=5 AND fcp.pchid='EEEE')")
        sql = sql_string[:].format(
            fcp_template_id, pchid_path_filter)
        for i in range(8):
            # call
            result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
            # verify final_pchid_per_path by sql
            mock_conn.execute.assert_called_with(sql)
            # verify result
            final_pchid_per_path = {3: 'CCCC', 4: 'CCCC', 5: 'EEEE'}
            for fcp in result:
                final_pchid_per_path.pop(fcp['path'])
                self.assertIn(fcp, all_fcps_with_uppercase)
            self.assertEqual(final_pchid_per_path, {})
            self.assertEqual(empty_reason, '')
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

        # case3: min_path_count(4) = free_path_count(4) = total_path_count(4)
        #        and final_pchid_per_path is on 4 paths
        #        and multiple combinations has the largest weight
        #        and some PCHIDs are shared across some paths
        # >>> pp(pchids_per_path_combinations)
        # [{0: 'AAAA', 1: 'CCCC', 2: 'CCCC', 3: 'EEEE', 'weight': 10.0},
        #  {0: 'AAAA', 1: 'CCCC', 2: 'DDDD', 3: 'EEEE', 'weight': 10.0},
        #  {0: 'BBBB', 1: 'CCCC', 2: 'CCCC', 3: 'EEEE', 'weight': 20.0},
        #  {0: 'BBBB', 1: 'CCCC', 2: 'DDDD', 3: 'EEEE', 'weight': 20.0}]
        LOG.info('----- case3 ------')
        mock_min_path_count.return_value = 4
        mock_free_pchids_per_path.return_value = {
            0: ['AAAA', 'BBBB'],
            1: ['CCCC'],
            2: ['CCCC', 'DDDD'],
            3: ['EEEE']}
        mock_total_path_count.return_value = 4
        # mock execute(sql).fetchall in _get_one_random_fcp_combinations
        all_fcps = [
            {'fcp_id': '1b01', 'path': 0, 'pchid': 'bbbb', 'wwpn_npiv': 'c1', 'wwpn_phy': 'x1'},
            {'fcp_id': '1b02', 'path': 0, 'pchid': 'bbbb', 'wwpn_npiv': 'c2', 'wwpn_phy': 'x2'},
            {'fcp_id': '1c03', 'path': 1, 'pchid': 'cccc', 'wwpn_npiv': 'c3', 'wwpn_phy': 'x3'},
            {'fcp_id': '1c04', 'path': 1, 'pchid': 'cccc', 'wwpn_npiv': 'c4', 'wwpn_phy': 'x4'},
            {'fcp_id': '1d03', 'path': 2, 'pchid': 'dddd', 'wwpn_npiv': 'c5', 'wwpn_phy': 'x5'},
            {'fcp_id': '1d04', 'path': 2, 'pchid': 'dddd', 'wwpn_npiv': 'c6', 'wwpn_phy': 'x6'},
            {'fcp_id': '1e04', 'path': 3, 'pchid': 'eeee', 'wwpn_npiv': 'c7', 'wwpn_phy': 'x7'},
            {'fcp_id': '1e05', 'path': 3, 'pchid': 'eeee', 'wwpn_npiv': 'c8', 'wwpn_phy': 'x8'}]
        mock_conn.execute().fetchall.return_value = all_fcps
        # all_fcps_with_uppercase for later verify
        all_fcps_with_uppercase = all_fcps.copy()
        for fcp in all_fcps_with_uppercase:
            for k in fcp:
                if k in ('fcp_id', 'pchid'):
                    fcp[k] = fcp[k].upper()
        # free_count_in_pchid_info =
        # {'AAAA': 10, 'BBBB': 41, 'CCCC': 43, 'DDDD': 50, 'EEEE': 31, 'FFFF': -2, 'GGGG': 80}
        pchid_info = {
            'AAAA': {'allocated': 118, 'max': 128},
            'BBBB': {'allocated': 87, 'max': 128},
            'CCCC': {'allocated': 85, 'max': 128},
            'DDDD': {'allocated': 78, 'max': 128},
            'EEEE': {'allocated': 108, 'max': 128},
            'FFFF': {'allocated': 130, 'max': 128},
            'GGGG': {'allocated': 48, 'max': 128}
        }
        # prepare sql
        pchid_path_filter = ("(tf.path=0 AND fcp.pchid='BBBB') OR "
                             "(tf.path=1 AND fcp.pchid='CCCC') OR "
                             "(tf.path=2 AND fcp.pchid='DDDD') OR "
                             "(tf.path=3 AND fcp.pchid='EEEE')")
        sql = sql_string[:].format(
            fcp_template_id, pchid_path_filter)
        for i in range(5):
            # call
            result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
            # verify final_pchid_per_path by sql
            mock_conn.execute.assert_called_with(sql)
            # verify result
            final_pchid_per_path = {0: 'BBBB', 1: 'CCCC',
                                    2: 'DDDD', 3: 'EEEE'}
            for fcp in result:
                final_pchid_per_path.pop(fcp['path'])
                self.assertIn(fcp, all_fcps_with_uppercase)
            self.assertEqual(final_pchid_per_path, {})
            self.assertEqual(empty_reason, '')
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

        # case4: min_path_count(4) = free_path_count(4) = total_path_count(4)
        #        and final_pchid_per_path is on 4 paths
        #        and multiple combinations has the largest weight
        #        and no PCHIDs are shared across more than 1 path
        # >>> pp(pchids_per_path_combinations)
        # [{0: 'AAAA', 1: 'CCCC', 2: 'EEEE', 3: 'GGGG', 'weight': 10.0},
        # {0: 'AAAA', 1: 'CCCC', 2: 'FFFF', 3: 'GGGG', 'weight': -2.0},
        # {0: 'AAAA', 1: 'DDDD', 2: 'EEEE', 3: 'GGGG', 'weight': 10.0},
        # {0: 'AAAA', 1: 'DDDD', 2: 'FFFF', 3: 'GGGG', 'weight': -2.0},
        # {0: 'BBBB', 1: 'CCCC', 2: 'EEEE', 3: 'GGGG', 'weight': 43.0},
        # {0: 'BBBB', 1: 'CCCC', 2: 'FFFF', 3: 'GGGG', 'weight': -2.0},
        # {0: 'BBBB', 1: 'DDDD', 2: 'EEEE', 3: 'GGGG', 'weight': 51.0},
        # {0: 'BBBB', 1: 'DDDD', 2: 'FFFF', 3: 'GGGG', 'weight': -2.0}]
        LOG.info('----- case4 ------')
        mock_min_path_count.return_value = 4
        mock_free_pchids_per_path.return_value = {
            0: ['AAAA', 'BBBB'],
            1: ['CCCC', 'DDDD'],
            2: ['EEEE', 'FFFF'],
            3: ['GGGG']}
        mock_total_path_count.return_value = 4
        # mock execute(sql).fetchall in _get_one_random_fcp_combinations
        all_fcps = [
            {'fcp_id': '1b01', 'path': 0, 'pchid': 'bbbb', 'wwpn_npiv': 'c1', 'wwpn_phy': 'x1'},
            {'fcp_id': '1b02', 'path': 0, 'pchid': 'bbbb', 'wwpn_npiv': 'c2', 'wwpn_phy': 'x2'},
            {'fcp_id': '1d03', 'path': 1, 'pchid': 'dddd', 'wwpn_npiv': 'c3', 'wwpn_phy': 'x3'},
            {'fcp_id': '1d04', 'path': 1, 'pchid': 'dddd', 'wwpn_npiv': 'c4', 'wwpn_phy': 'x4'},
            {'fcp_id': '1e03', 'path': 2, 'pchid': 'eeee', 'wwpn_npiv': 'c5', 'wwpn_phy': 'x5'},
            {'fcp_id': '1e04', 'path': 2, 'pchid': 'eeee', 'wwpn_npiv': 'c6', 'wwpn_phy': 'x6'},
            {'fcp_id': '1g04', 'path': 3, 'pchid': 'gggg', 'wwpn_npiv': 'c7', 'wwpn_phy': 'x7'},
            {'fcp_id': '1g05', 'path': 3, 'pchid': 'gggg', 'wwpn_npiv': 'c8', 'wwpn_phy': 'x8'}]
        mock_conn.execute().fetchall.return_value = all_fcps
        # all_fcps_with_uppercase for later verify
        all_fcps_with_uppercase = all_fcps.copy()
        for fcp in all_fcps_with_uppercase:
            for k in fcp:
                if k in ('fcp_id', 'pchid'):
                    fcp[k] = fcp[k].upper()
        # free_count_in_pchid_info =
        # {'AAAA': 10, 'BBBB': 61, 'CCCC': 43, 'DDDD': 51, 'EEEE': 61, 'FFFF': -2, 'GGGG': 80}
        pchid_info = {
            'AAAA': {'allocated': 118, 'max': 128},
            'BBBB': {'allocated': 67, 'max': 128},
            'CCCC': {'allocated': 85, 'max': 128},
            'DDDD': {'allocated': 77, 'max': 128},
            'EEEE': {'allocated': 67, 'max': 128},
            'FFFF': {'allocated': 130, 'max': 128},
            'GGGG': {'allocated': 48, 'max': 128}
        }
        # prepare sql
        pchid_path_filter = ("(tf.path=0 AND fcp.pchid='BBBB') OR "
                             "(tf.path=1 AND fcp.pchid='DDDD') OR "
                             "(tf.path=2 AND fcp.pchid='EEEE') OR "
                             "(tf.path=3 AND fcp.pchid='GGGG')")
        sql = sql_string[:].format(
            fcp_template_id, pchid_path_filter)
        for i in range(5):
            # call
            result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
            # verify final_pchid_per_path by sql
            mock_conn.execute.assert_called_with(sql)
            # verify result
            final_pchid_per_path = {0: 'BBBB', 1: 'DDDD',
                                    2: 'EEEE', 3: 'GGGG'}
            for fcp in result:
                final_pchid_per_path.pop(fcp['path'])
                self.assertIn(fcp, all_fcps_with_uppercase)
            self.assertEqual(final_pchid_per_path, {})
            self.assertEqual(empty_reason, '')
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

        # case5: No free FCP device left in FCP multipath template
        LOG.info('----- case5 ------')
        mock_min_path_count.return_value = 3
        mock_free_pchids_per_path.return_value = {}
        mock_total_path_count.return_value = 3
        # free_count_in_pchid_info =
        # {'AAAA': 10, 'BBBB': 0, 'CCCC': 1}
        pchid_info = {
            'AAAA': {'allocated': 118, 'max': 128},
            'BBBB': {'allocated': 128, 'max': 128},
            'CCCC': {'allocated': 127, 'max': 128}
        }
        # call
        result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
        # verify
        self.assertEqual([], result)
        self.assertTrue('No free FCP device left in FCP multipath template' in empty_reason)
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

        # case6: min_path_count(3) = free_path_count(3) = total_path_count(3)
        #        and final_pchid_per_path is on 3 paths
        #        and all combinations are invalid       <-----
        #        and no PCHIDs are shared across more than 1 path
        # >>> pp(pchids_per_path_combinations)
        # [{0: 'AAAA', 1: 'CCCC', 2: 'CCCC', 'weight': 0.5},
        #  {0: 'BBBB', 1: 'CCCC', 2: 'CCCC', 'weight': 0}]
        LOG.info('----- case6 ------')
        mock_min_path_count.return_value = 3
        mock_free_pchids_per_path.return_value = {
            0: ['AAAA', 'BBBB'],
            1: ['CCCC'],
            2: ['CCCC']}
        mock_total_path_count.return_value = 3
        # free_count_in_pchid_info =
        # {'AAAA': 10, 'BBBB': 0, 'CCCC': 1}
        pchid_info = {
            'AAAA': {'allocated': 118, 'max': 128},
            'BBBB': {'allocated': 128, 'max': 128},
            'CCCC': {'allocated': 127, 'max': 128}
        }
        # call
        result, empty_reason = self.db_op.get_fcp_devices(fcp_template_id, pchid_info)
        # verify
        self.assertEqual([], result)
        self.assertTrue('Not enough free capacity of the following PCHIDs left. '
                        'Their free capacity is {}.'
                        .format(sorted(dict(BBBB=0, CCCC=1).items()))
                        in empty_reason)
        mock_reset(mock_min_path_count, mock_free_pchids_per_path,
                   mock_total_path_count)

    def test_create_fcp_template_with_name_and_desc(self):
        """Create a FCP Multipath Template only with name and description, other parameters are all default values"""
        fcp_template_id = 'fake_tmpl_id'
        name = 'tmpl_1'
        description = 'this is the description.'
        fcp_devices_by_path = []
        host_default = False
        default_sp_list = None
        self.db_op.create_fcp_template(fcp_template_id, name, description,
                                       fcp_devices_by_path, host_default,
                                       default_sp_list)
        actual_tmpl = self.db_op.get_fcp_templates([fcp_template_id])
        self.assertEqual(actual_tmpl[0]['id'], fcp_template_id)
        self.db_op.delete_fcp_template(fcp_template_id)

    def test_validate_min_fcp_paths_count_with_fcp_and_minCount_no_err(self):
        fcp_devices = '1a10;1b10;1c10;1d10'
        min_fcp_paths_count = 4
        fcp_template_id = 'fcp_tmpl_1'
        self.db_op._validate_min_fcp_paths_count(fcp_devices, min_fcp_paths_count, fcp_template_id)

    @patch("zvmsdk.database.FCPDbOperator.get_min_fcp_paths_count_from_db")
    def test_validate_min_fcp_paths_count_only_with_fcp_error(self, get_min_fcp_paths_count_from_db):
        fcp_devices = '1a10;1b10'
        fcp_template_id = 'fcc_tmpl_1'
        get_min_fcp_paths_count_from_db.return_value = 4
        self.assertRaisesRegex(exception.SDKConflictError,
                               'min_fcp_paths_count 4 is larger than fcp device path count 2',
                               self.db_op._validate_min_fcp_paths_count,
                               fcp_devices, None, fcp_template_id)

    @patch("zvmsdk.database.FCPDbOperator.get_path_count")
    def test_validate_min_fcp_paths_count_only_with_minCount_error(self, get_path_count):
        fcp_devices = None
        min_fcp_paths_count = 4
        fcp_template_id = 'fcc_tmpl_1'
        get_path_count.return_value = 2
        self.assertRaisesRegex(exception.SDKConflictError,
                               'min_fcp_paths_count 4 is larger than fcp device path count 2',
                               self.db_op._validate_min_fcp_paths_count,
                               fcp_devices, min_fcp_paths_count, fcp_template_id)

    @patch("zvmsdk.database.FCPDbOperator.get_path_count")
    @patch("zvmsdk.database.FCPDbOperator.get_min_fcp_paths_count_from_db")
    def test_get_min_fcp_paths_count_not_set_minCount(self, get_min_fcp_paths_count_from_db, get_path_count):
        get_path_count.return_value = 2
        get_min_fcp_paths_count_from_db.return_value = -1
        ret = self.db_op.get_min_fcp_paths_count('template_id')
        self.assertEqual(2, ret)

    @patch("zvmsdk.database.FCPDbOperator.get_path_count")
    @patch("zvmsdk.database.FCPDbOperator.get_min_fcp_paths_count_from_db")
    def test_get_min_fcp_paths_count_with_minCount(self, get_min_fcp_paths_count_from_db, get_path_count):
        get_path_count.return_value = 2
        get_min_fcp_paths_count_from_db.return_value = 4
        ret = self.db_op.get_min_fcp_paths_count('template_id')
        self.assertEqual(4, ret)

    def test_get_min_fcp_paths_count_with_non_template(self):
        self.assertRaisesRegex(exception.SDKObjectNotExistError,
                               'min_fcp_paths_count from fcp_template_id',
                               self.db_op.get_min_fcp_paths_count, None)

    @patch("zvmsdk.database.FCPDbOperator.get_min_fcp_paths_count_from_db")
    def test_get_min_fcp_paths_count_with_none_mincount(self, get_min_fcp_paths_count_from_db):
        get_min_fcp_paths_count_from_db.return_value = None
        self.assertRaisesRegex(exception.SDKObjectNotExistError,
                               'min_fcp_paths_count from fcp_template_id',
                               self.db_op.get_min_fcp_paths_count, 'fake_fcp_template_id')

    def test_edit_fcp_template(self):
        """Test edit_fcp_template"""
        tmpl_id = 'fake_id_0000'
        kwargs = {
            'name': 'new_name',
            'description': 'new_desc',
            'fcp_devices': '1A00-1A03;1B00-1B03',
            'host_default': False,
            'default_sp_list': []
        }
        try:
            # case1:
            # validate: FCP Multipath Template
            obj_desc = ("FCP Multipath Template {}".format(tmpl_id))
            with self.assertRaises(exception.SDKObjectNotExistError) as cm:
                self.db_op.edit_fcp_template(tmpl_id, **kwargs)
            # The following 3 assertions are the same
            # (Pdb) pp str(cm.exception)
            # 'FCP Multipath Template fake_id_0000 does not exist.'
            self.assertIn(obj_desc, cm.exception.message)
            self.assertIn(obj_desc, str(cm.exception))
            self.assertRaisesRegex(exception.SDKObjectNotExistError,
                                   obj_desc,
                                   self.db_op.edit_fcp_template,
                                   tmpl_id, **kwargs)

            # case2:
            # validate: add or delete path from FCP Multipath Template
            # preparation:
            #   a. create_fcp_template
            #   b. bulk_insert_zvm_fcp_info_into_fcp_table
            #       insert '1A00-1A03;1B00-1B03'
            #   c. reserve_fcps
            #       set assigner_id and tmpl_id
            #       ('1a01', '1b03')
            #   d. increase_connections
            #       set connections
            #       ('1a01', '1b03')
            kwargs['fcp_devices'] = '1A00-1A03;1B00-1B03'
            self.db_op.create_fcp_template(
                tmpl_id, kwargs['name'], kwargs['description'],
                utils.expand_fcp_list(kwargs['fcp_devices']),
                host_default=kwargs['host_default'],
                default_sp_list=kwargs['default_sp_list'])
            fcp_info = [
                ('1a01', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1'),
                ('1b03', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1')]
            # set FCP ('1a01', '1b03') as inuse
            self.db_op.bulk_insert_zvm_fcp_info_into_fcp_table(fcp_info)
            reserve_info = (('1a01', '1b03'), 'user1', tmpl_id)
            self.db_op.reserve_fcps(*reserve_info)
            self.increase_connections('1a01')
            self.increase_connections('1b03')
            # add path
            kwargs['fcp_devices'] = '1A00-1A03;1B00-1B03;1c00'
            detail = "Adding or deleting a FCP device path"
            self.assertRaisesRegex(exception.SDKConflictError,
                                   detail,
                                   self.db_op.edit_fcp_template,
                                   tmpl_id, **kwargs)
            # delete path
            kwargs['fcp_devices'] = '1A00-1A03'
            self.assertRaisesRegex(exception.SDKConflictError,
                                   detail,
                                   self.db_op.edit_fcp_template,
                                   tmpl_id, **kwargs)

            # case3
            # validate: not allowed to remove inuse FCP

            # Prepare 2 templates with the same FCP devices
            # 1a01, 1b03 are allocated from template 'fake_id_0000'
            # 1a02, 1b02 are allocated from template 'fake_id_1111'
            self.db_op.create_fcp_template(
                'fake_id_1111', "fake_name", 'fake_desc',
                utils.expand_fcp_list('1A00-1A03;1B00-1B03'),
                host_default=False,
                default_sp_list=[])
            fcp_info = [
                ('1a02', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1'),
                ('1b02', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active', 'user1'),
                ('1c03', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e3', 'active', 'user1'),
                ('1d04', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e1', 'active', 'user1')]
            self.db_op.bulk_insert_zvm_fcp_info_into_fcp_table(fcp_info)
            reserve_info = (('1a02', '1b02'), 'user1', 'fake_id_1111')
            self.db_op.reserve_fcps(*reserve_info)
            self.increase_connections('1a02')
            self.increase_connections('1b02')
            # case-3.1:
            # delete (1a01,1b03) from 'fake_id_0000' must fail
            fcp_device_list = '1A00,1A02-1A03;1B00-1B02, 1C03, 1D04'
            not_allow_for_del = {'1a01', '1b03'}
            detail = ("The FCP devices ({}) are missing from the FCP device list."
                      .format(utils.shrink_fcp_list(list(not_allow_for_del))))
            with self.assertRaises(exception.SDKConflictError) as cm:
                self.db_op.edit_fcp_template('fake_id_0000', fcp_devices=fcp_device_list)
            self.assertIn(detail, str(cm.exception))
            # case-3.2:
            # delete (1a01,1b03) from 'fake_id_1111' must success
            ret_val = self.db_op.edit_fcp_template('fake_id_1111', fcp_devices=fcp_device_list)
            pchids_add = ret_val.get('fcp_template').get('pchids').get('add')
            pchids_all = ret_val.get('fcp_template').get('pchids').get('all')
            pchids_del = ret_val.get('fcp_template').get('pchids').get('delete')
            expect_add = {'all': ['02E1', '02E3'], 'first_used_by_templates': ['02E1', '02E3']}
            expect_add['all'].sort()
            pchids_add['all'].sort()
            expect_add['first_used_by_templates'].sort()
            pchids_add['first_used_by_templates'].sort()
            pchids_all.sort()
            self.assertListEqual(expect_add['all'], pchids_add['all'])
            self.assertListEqual(expect_add['first_used_by_templates'], pchids_add['first_used_by_templates'])
            self.assertEqual({'all': [], 'not_exist_in_any_template': []}, pchids_del)
            self.assertEqual(['02E1', '02E3', '02E4'], pchids_all)
            # case4
            # DML: table template_fcp_mapping
            # (based on the preparation done in case2)
            # a. insert fcp device : 1a05-1a07, 1b05-1b07
            # b. remove fcp device : 1a02, 1b02
            # c. update fcp path   :
            #      change 1a01,1a03 from path0 to path1
            #      change 1b01,1b03 from path1 to path0
            kwargs['fcp_devices'] = '1A00,1B01,1B03;1B00,1A01,1A03, 1C03'
            ret_val = self.db_op.edit_fcp_template(tmpl_id, fcp_devices=kwargs['fcp_devices'])
            pchids_add = ret_val.get('fcp_template').get('pchids').get('add')
            pchids_all = ret_val.get('fcp_template').get('pchids').get('all')
            pchids_del = ret_val.get('fcp_template').get('pchids').get('delete')
            expect_add = {'all': ['02E3'], 'first_used_by_templates': []}
            self.assertListEqual(expect_add['all'], pchids_add['all'])
            self.assertListEqual(expect_add['first_used_by_templates'], pchids_add['first_used_by_templates'])
            self.assertEqual({'all': [], 'not_exist_in_any_template': []}, pchids_del)
            self.assertListEqual(['02E4', '02E3'], pchids_all)
            expected = utils.expand_fcp_list(kwargs['fcp_devices'])
            _, fcp_detail = self.db_op.get_fcp_templates_details([tmpl_id])
            fcp_in_db = {0: set(), 1: set()}
            for row in fcp_detail:
                fcp_in_db[row['path']].add(row['fcp_id'])
            self.assertEqual(expected, fcp_in_db)

            # case5
            # DML: table(template and template_sp_mapping)
            # (based on the preparation done in case2)
            kwargs['name'] = 'test_name'
            kwargs['description'] = 'test_desc'
            kwargs['host_default'] = True
            kwargs['default_sp_list'] = ['SP1', 'SP2']
            tmpl_basic = self.db_op.edit_fcp_template(tmpl_id, **kwargs)
            all_add_pchids = []
            first_used_by_templates = []
            del_pchids = []
            not_used_in_any_template = []
            add_pchids = dict(all=list(all_add_pchids),
                              first_used_by_templates=first_used_by_templates)
            delete_dict = dict(all=del_pchids,
                               not_exist_in_any_template=not_used_in_any_template)
            expected = {'fcp_template': {
                'id': tmpl_id,
                'name': kwargs['name'],
                'description': kwargs['description'],
                'host_default': kwargs['host_default'],
                'storage_providers': kwargs['default_sp_list'],
                'min_fcp_paths_count': 2,
                'pchids': {
                        'add': add_pchids,
                        'delete': delete_dict,
                        'all': ['02E4', '02E3']
                }
            }}
            self.assertEqual(expected, tmpl_basic)
        finally:
            # clean up
            self._purge_fcp_db()

    @patch("zvmsdk.database.FCPDbOperator.get_fcp_templates", Mock())
    @patch("zvmsdk.database.FCPDbOperator.get_pchids_by_fcp_template", Mock())
    def test_get_pchids_from_all_fcp_templates(self):
        """test_get_pchids_from_all_fcp_templates"""
        """Test function get_pchids_by_fcp_template"""
        # insert test data into table template_fcp_mapping
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 0),
                        ('2222', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert test data into table fcp
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                           template_id),
                           ('2222', 'user1', 0, 0, 'c05076de33000222',
                            'c05076de33002641', '30', '02ec', 'active', 'owner1',
                            '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            # case1: fcp_template doesn't have related pchid info
            pchids = self.db_op.get_pchids_from_all_fcp_templates()
            self.assertEqual(["02E4", "02EC"], pchids)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    def test_get_fcp_templates(self):
        """test get_fcp_templates"""
        self._purge_fcp_db()
        try:
            # prepare test data
            tmpl_id_1 = 'fake_id_0001'
            kwargs1 = {
                'name': 'new_name1',
                'description': 'new_desc1',
                'fcp_devices': '1A00-1A03;1B00-1B03',
                'host_default': False,
                'default_sp_list': []
            }
            tmpl_id_2 = 'fake_id_0002'
            kwargs2 = {
                'name': 'new_name2',
                'description': 'new_desc2',
                'fcp_devices': '1C00-1C03;1D00-1D03',
                'host_default': True,
                'default_sp_list': ['fake_sp']
            }
            self.db_op.create_fcp_template(
                tmpl_id_1, kwargs1['name'], kwargs1['description'],
                utils.expand_fcp_list(kwargs1['fcp_devices']),
                host_default=kwargs1['host_default'],
                default_sp_list=kwargs1['default_sp_list'])
            self.db_op.create_fcp_template(
                tmpl_id_2, kwargs2['name'], kwargs2['description'],
                utils.expand_fcp_list(kwargs2['fcp_devices']),
                host_default=kwargs2['host_default'],
                default_sp_list=kwargs2['default_sp_list'])

            # case1: get_fcp_templates by template_id_list
            expected_1 = (tmpl_id_1, 'new_name1', 'new_desc1', False, None)
            info_1 = self.db_op.get_fcp_templates([tmpl_id_1])[0]
            result_1 = (
                info_1[0], info_1[1], info_1[2], bool(info_1[3]), info_1[5])
            self.assertEqual(expected_1, result_1)

            # case2: get_fcp_templates without parameter, will get all
            # templates info
            expected_2 = (tmpl_id_2, 'new_name2', 'new_desc2', True, 'fake_sp')
            info_all = self.db_op.get_fcp_templates()
            self.assertEqual(2, len(info_all))
            result_1 = (
                info_all[0][0], info_all[0][1], info_all[0][2],
                bool(info_all[0][3]), info_all[0][5])
            result_2 = (
                info_all[1][0], info_all[1][1], info_all[1][2],
                bool(info_all[1][3]), info_all[1][5])
            self.assertEqual(expected_1, result_1)
            self.assertEqual(expected_2, result_2)
        finally:
            self._purge_fcp_db()

    def test_get_host_default_fcp_template(self):
        """test get_host_default_fcp_template"""
        try:
            # prepare test data
            tmpl_id_1 = 'fake_id_0001'
            kwargs1 = {
                'name': 'new_name1',
                'description': 'new_desc1',
                'fcp_devices': '1A00-1A03;1B00-1B03',
                'host_default': True,
                'default_sp_list': []
            }
            tmpl_id_2 = 'fake_id_0002'
            kwargs2 = {
                'name': 'new_name2',
                'description': 'new_desc2',
                'fcp_devices': '1C00-1C03;1D00-1D03',
                'host_default': False,
                'default_sp_list': ['fake_sp']
            }
            self.db_op.create_fcp_template(
                tmpl_id_1, kwargs1['name'], kwargs1['description'],
                utils.expand_fcp_list(kwargs1['fcp_devices']),
                host_default=kwargs1['host_default'],
                default_sp_list=kwargs1['default_sp_list'])
            self.db_op.create_fcp_template(
                tmpl_id_2, kwargs2['name'], kwargs2['description'],
                utils.expand_fcp_list(kwargs2['fcp_devices']),
                host_default=kwargs2['host_default'],
                default_sp_list=kwargs2['default_sp_list'])

            # get by host_default=True
            info_1 = self.db_op.get_host_default_fcp_template()[0]
            expected_1 = (tmpl_id_1, 'new_name1', 'new_desc1', True, -1, None)
            result_1 = (
                info_1[0], info_1[1], info_1[2], bool(info_1[3]), info_1[4], info_1[5])
            self.assertEqual(expected_1, result_1)
            # get by host_default=False
            info_2 = self.db_op.get_host_default_fcp_template(False)[0]
            expected_2 = (tmpl_id_2, 'new_name2', 'new_desc2', False, 'fake_sp')
            result_2 = (
                info_2[0], info_2[1], info_2[2], bool(info_2[3]), info_2[5])
            self.assertEqual(expected_2, result_2)
        finally:
            self._purge_fcp_db()

    def test_get_sp_default_fcp_template(self):
        """test get_sp_default_fcp_template"""
        try:
            # prepare test data
            tmpl_id_1 = 'fake_id_0001'
            kwargs1 = {
                'name': 'new_name1',
                'description': 'new_desc1',
                'fcp_devices': '1A00-1A03;1B00-1B03',
                'host_default': False,
                'default_sp_list': ['v7k60']
            }
            tmpl_id_2 = 'fake_id_0002'
            kwargs2 = {
                'name': 'new_name2',
                'description': 'new_desc2',
                'fcp_devices': '1C00-1C03;1D00-1D03',
                'host_default': True,
                'default_sp_list': ['ds8k']
            }
            self.db_op.create_fcp_template(
                tmpl_id_1, kwargs1['name'], kwargs1['description'],
                utils.expand_fcp_list(kwargs1['fcp_devices']),
                host_default=kwargs1['host_default'],
                default_sp_list=kwargs1['default_sp_list'],
                min_fcp_paths_count=2)
            self.db_op.create_fcp_template(
                tmpl_id_2, kwargs2['name'], kwargs2['description'],
                utils.expand_fcp_list(kwargs2['fcp_devices']),
                host_default=kwargs2['host_default'],
                default_sp_list=kwargs2['default_sp_list'],
                min_fcp_paths_count=2)
            # case1: get by one sp
            info_1 = self.db_op.get_sp_default_fcp_template(['v7k60'])[0]
            expected_1 = (tmpl_id_1, 'new_name1', 'new_desc1', False, 'v7k60')
            result_1 = (
                info_1[0], info_1[1], info_1[2], bool(info_1[3]), info_1[5])
            self.assertEqual(expected_1, result_1)

            # case2: get by 'all' sp
            expected_2 = (tmpl_id_2, 'new_name2', 'new_desc2', True, 'ds8k')
            info_all = self.db_op.get_sp_default_fcp_template(['all'])
            self.assertEqual(2, len(info_all))
            result_1 = (
                info_all[0][0], info_all[0][1], info_all[0][2],
                bool(info_all[0][3]), info_all[0][5])
            result_2 = (
                info_all[1][0], info_all[1][1], info_all[1][2],
                bool(info_all[1][3]), info_all[1][5])
            self.assertEqual(expected_1, result_1)
            self.assertEqual(expected_2, result_2)
        finally:
            self._purge_fcp_db()

    def test_get_fcp_template_by_assigner_id(self):
        """test get_fcp_template_by_assigner_id"""
        try:
            # prepare test data, template_1 has assigner_id='user1'
            tmpl_id_1 = self._prepare_fcp_info_for_a_test_fcp_template()
            # template_2 does not have assigner_id
            tmpl_id_2 = 'fake_id_0002'
            kwargs2 = {
                'name': 'new_name2',
                'description': 'new_desc2',
                'fcp_devices': '1C00-1C03;1D00-1D03',
                'host_default': True,
                'default_sp_list': ['fake_sp']
            }
            self.db_op.create_fcp_template(
                tmpl_id_2, kwargs2['name'], kwargs2['description'],
                utils.expand_fcp_list(kwargs2['fcp_devices']),
                host_default=kwargs2['host_default'],
                default_sp_list=kwargs2['default_sp_list'])

            info_1 = self.db_op.get_fcp_template_by_assigner_id('user1')[0]
            expected_1 = (tmpl_id_1, 'new_name', 'new_desc', False, 2, None)
            result_1 = (
                info_1[0], info_1[1], info_1[2], bool(info_1[3]), info_1[4], info_1[5])
            self.assertEqual(expected_1, result_1)
        finally:
            self._purge_fcp_db()

    def test_get_fcp_templates_details(self):
        """test get_fcp_templates_details"""
        try:
            # prepare test data, template_1 has assigner_id='user1'
            tmpl_id_1 = 'fake_id_' + str(random.randint(100000, 999999))
            kwargs1 = {
                'name': 'new_name1',
                'description': 'new_desc1',
                'fcp_devices': '1A00',
                'host_default': False,
                'default_sp_list': []
            }
            # template_2 does not have assigner_id
            tmpl_id_2 = 'fake_id_' + str(random.randint(100000, 999999))
            kwargs2 = {
                'name': 'new_name2',
                'description': 'new_desc2',
                'fcp_devices': '1C00-1C01;1D00-1D01',
                'host_default': True,
                'default_sp_list': ['fake_sp']
            }
            self.db_op.create_fcp_template(
                tmpl_id_1, kwargs1['name'], kwargs1['description'],
                utils.expand_fcp_list(kwargs1['fcp_devices']),
                host_default=kwargs1['host_default'],
                default_sp_list=kwargs1['default_sp_list'])
            self.db_op.create_fcp_template(
                tmpl_id_2, kwargs2['name'], kwargs2['description'],
                utils.expand_fcp_list(kwargs2['fcp_devices']),
                host_default=kwargs2['host_default'],
                default_sp_list=kwargs2['default_sp_list'])
            fcp_info = [
                ('1a00', 'wwpn_npiv_1', 'wwpn_phy_1', '27', '02e4', 'active',
                'user1')]
            try:
                self.db_op.bulk_insert_zvm_fcp_info_into_fcp_table(fcp_info)
            except exception.SDKGuestOperationError as ex:
                if 'UNIQUE constraint failed' in str(ex):
                    pass
                else:
                    raise
            reserve_info = (('1a00'), 'user1', tmpl_id_1)
            self.db_op.reserve_fcps(*reserve_info)

            # case1: get all templates detail
            result = self.db_op.get_fcp_templates_details()
            tmpl_result = result[0]
            fcp_result = result[1]

            # should include 2 templates info
            self.assertEqual(2, len(tmpl_result))

            expected_template_info_1 = (tmpl_id_1, 'new_name1', 'new_desc1',
                                        False, -1)
            template_info_1 = (tmpl_result[0][0], tmpl_result[0][1],
                               tmpl_result[0][2], bool(tmpl_result[0][3]),
                               tmpl_result[0][4])
            self.assertEqual(template_info_1, expected_template_info_1)

            expected_template_info_2 = (tmpl_id_2, 'new_name2', 'new_desc2',
                                        True, -1)
            template_info_2 = (tmpl_result[1][0], tmpl_result[1][1],
                               tmpl_result[1][2], bool(tmpl_result[1][3]),
                               tmpl_result[1][4])
            self.assertEqual(template_info_2, expected_template_info_2)

            # should include 5 fcps info of the two templates
            self.assertEqual(5, len(fcp_result))

            # case2: get by template_id_list
            result = self.db_op.get_fcp_templates_details([tmpl_id_1])
            # should include 1 template info
            self.assertEqual(1, len(result[0]))
            expected_template_info_1 = (tmpl_id_1, 'new_name1', 'new_desc1',
                                        False, -1, None)
            template_info_1 = (tmpl_result[0][0], tmpl_result[0][1],
                               tmpl_result[0][2], bool(tmpl_result[0][3]),
                               tmpl_result[0][4], tmpl_result[0][5])
            self.assertEqual(template_info_1, expected_template_info_1)
            # should include 1 fcp info of the template
            self.assertEqual(1, len(result[1]))
            fcp_in_db = result[1]
            expected = ('1a00', tmpl_id_1, 0, '', 0, 1, 'wwpn_npiv_1',
                                 'wwpn_phy_1', 27, '02e4', 'active', 'user1', tmpl_id_1)
            i = 0
            for fcp in fcp_in_db:
                self.assertEqual(fcp[i], expected[i])
                i += 1
        finally:
            self._purge_fcp_db()

    def test_delete_fcp_template(self):
        try:
            # case1: delete a in-use template
            tmpl_id_1 = self._prepare_fcp_info_for_a_test_fcp_template()
            self.assertRaises(exception.SDKConflictError,
                              self.db_op.delete_fcp_template,
                              tmpl_id_1)

            # case2: normal case
            self.db_op.unreserve_fcps(['1A01', '1B03'])
            self.db_op.delete_fcp_template(tmpl_id_1)

            # case3: delete a non-exist template
            obj_desc = ("FCP Multipath Template {}".format(tmpl_id_1))
            with self.assertRaises(exception.SDKObjectNotExistError) as cm:
                self.db_op.delete_fcp_template(tmpl_id_1)
            # The following 3 assertions are the same
            # 'FCP Multipath Template fake_id_0000 does not exist.'
            self.assertIn(obj_desc, cm.exception.message)
            self.assertIn(obj_desc, str(cm.exception))
            self.assertRaisesRegex(exception.SDKObjectNotExistError,
                                   obj_desc,
                                   self.db_op.delete_fcp_template,
                                   tmpl_id_1)
        finally:
            self._purge_fcp_db()

    def test_get_pchids_by_fcp_template(self):
        """Test function get_pchids_by_fcp_template"""
        # insert test data into table template_fcp_mapping
        template_id = 'fakehost-1111-1111-1111-111111111111'
        template_fcp = [('1111', template_id, 0),
                        ('2222', template_id, 1)]
        self._insert_data_into_template_fcp_mapping_table(template_fcp)
        # insert test data into table fcp
        fcp_info_list = [('1111', 'user1', 0, 0, 'c05076de33000111',
                          'c05076de33002641', '27', '02e4', 'active', 'owner1',
                          template_id),
                         ('2222', 'user1', 0, 0, 'c05076de33000222',
                          'c05076de33002641', '30', '02ec', 'active', 'owner1',
                          '')]
        fcp_id_list = [fcp_info[0] for fcp_info in fcp_info_list]
        # delete dirty data from other test cases
        self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
        # insert new test data
        self._insert_data_into_fcp_table(fcp_info_list)
        try:
            # case1: fcp_template doesn't have related pchid info
            template_id_not_exist = 'fakehost-1111-1111-1111-111111111122'
            pchids_blank = self.db_op.get_pchids_by_fcp_template(template_id_not_exist)
            self.assertEqual([], pchids_blank)
            # case2: fcp_template has related pchid info
            template_id = 'fakehost-1111-1111-1111-111111111111'
            pchids = self.db_op.get_pchids_by_fcp_template(template_id)
            pchids.sort(reverse=False)
            self.assertEqual(["02E4", "02EC"], pchids)
        finally:
            self.db_op.bulk_delete_from_fcp_table(fcp_id_list)
            self.db_op.bulk_delete_fcp_from_template(fcp_id_list, template_id)

    @patch('zvmsdk.database._FCP_CONN')
    def test_get_pchids_of_all_inuse_fcp_devices(self, mock_conn):
        """test get_pchids_of_all_inuse_fcp_devices"""
        mock_conn.execute().fetchall.side_effect = [
            [],
            [   # all the keys and values must be in lower case,
                # because sqlite DB query always returns in lower case
                # pchid: 02E0
                {'pchid': '02e0', 'fcp_id': '1a0a'},
                {'pchid': '02e0', 'fcp_id': '1a09'},
                {'pchid': '02e0', 'fcp_id': '1a0b'},
                {'pchid': '02e0', 'fcp_id': '1a02'},
                {'pchid': '02e0', 'fcp_id': '1a11'},
                # pchid: 03FC
                {'pchid': '03fc', 'fcp_id': '1c03'},
                {'pchid': '03fc', 'fcp_id': '1c04'},
                {'pchid': '03fc', 'fcp_id': '1b1f'},
                {'pchid': '03fc', 'fcp_id': '1b20'},
                {'pchid': '03fc', 'fcp_id': '1b21'}]
        ]
        # case1: no inuse fcp
        expected = {}
        result = self.db_op.get_pchids_of_all_inuse_fcp_devices()
        self.assertEqual(expected, result)
        # case2: has inuse fcp
        expected = {'02E0': '1A02, 1A09 - 1A0B, 1A11',
                    '03FC': '1B1F - 1B21, 1C03 - 1C04'}
        result = self.db_op.get_pchids_of_all_inuse_fcp_devices()
        self.assertDictEqual(expected, result)

    @patch('zvmsdk.database._FCP_CONN')
    def test_get_free_pchids_by_fcp_template(self, mock_conn):
        """test get_free_pchids_by_fcp_template"""
        mock_conn.execute().fetchall.side_effect = [
            [],
            [{'pchid': '01e0', 'path': '1'},
             {'pchid': '02A0', 'path': '1'},
             {'pchid': '02a0', 'path': '3'},
             {'pchid': '03fc', 'path': '3'}]
        ]
        # case1: no free fcp
        expected = {}
        result = self.db_op.get_free_pchids_by_fcp_template('fake_id')
        self.assertEqual(expected, result)
        # case2: has free fcp
        expected = {'1': ['01E0', '02A0'],
                    '3': ['02A0', '03FC']}
        result = self.db_op.get_free_pchids_by_fcp_template('fake_id')
        self.assertDictEqual(expected, result)


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
