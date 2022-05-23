# Copyright 2017, 2022 IBM Corp.
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


import contextlib
import random
import os
import six
import sqlite3
import threading
import uuid
import json

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


_DIR_MODE = 0o755
_VOLUME_CONN = None
_NETWORK_CONN = None
_IMAGE_CONN = None
_GUEST_CONN = None
_FCP_CONN = None
_DBLOCK_VOLUME = threading.RLock()
_DBLOCK_NETWORK = threading.RLock()
_DBLOCK_IMAGE = threading.RLock()
_DBLOCK_GUEST = threading.RLock()
_DBLOCK_FCP = threading.RLock()


@contextlib.contextmanager
def get_network_conn():
    global _NETWORK_CONN, _DBLOCK_NETWORK
    if not _NETWORK_CONN:
        _NETWORK_CONN = _init_db_conn(const.DATABASE_NETWORK)

    _DBLOCK_NETWORK.acquire()
    try:
        yield _NETWORK_CONN
    except Exception as err:
        msg = "Execute SQL statements error: %s" % six.text_type(err)
        LOG.error(msg)
        raise exception.SDKNetworkOperationError(rs=1, msg=msg)
    finally:
        _DBLOCK_NETWORK.release()


@contextlib.contextmanager
def get_image_conn():
    global _IMAGE_CONN, _DBLOCK_IMAGE
    if not _IMAGE_CONN:
        _IMAGE_CONN = _init_db_conn(const.DATABASE_IMAGE)

    _DBLOCK_IMAGE.acquire()
    try:
        yield _IMAGE_CONN
    except Exception as err:
        LOG.error("Execute SQL statements error: %s", six.text_type(err))
        raise exception.SDKDatabaseException(msg=err)
    finally:
        _DBLOCK_IMAGE.release()


@contextlib.contextmanager
def get_guest_conn():
    global _GUEST_CONN, _DBLOCK_GUEST
    if not _GUEST_CONN:
        _GUEST_CONN = _init_db_conn(const.DATABASE_GUEST)

    _DBLOCK_GUEST.acquire()
    try:
        yield _GUEST_CONN
    except Exception as err:
        msg = "Execute SQL statements error: %s" % six.text_type(err)
        LOG.error(msg)
        raise exception.SDKGuestOperationError(rs=1, msg=msg)
    finally:
        _DBLOCK_GUEST.release()


@contextlib.contextmanager
def get_fcp_conn():
    global _FCP_CONN, _DBLOCK_FCP
    if not _FCP_CONN:
        _FCP_CONN = _init_db_conn(const.DATABASE_FCP)

    _DBLOCK_FCP.acquire()
    try:
        yield _FCP_CONN
    except exception.SDKBaseException as err:
        msg = "Got SDK exception in FCP DB operation: %s" % six.text_type(err)
        LOG.error(msg)
        raise
    except Exception as err:
        msg = "Execute SQL statements error: %s" % six.text_type(err)
        LOG.error(msg)
        raise exception.SDKGuestOperationError(rs=1, msg=msg)
    finally:
        _DBLOCK_FCP.release()


def _init_db_conn(db_file):
    db_dir = CONF.database.dir
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, _DIR_MODE)
    database = os.path.join(db_dir, db_file)
    return sqlite3.connect(database,
                           check_same_thread=False,
                           isolation_level=None)


class NetworkDbOperator(object):

    def __init__(self):
        self._module_id = 'network'
        self._create_switch_table()

    def _create_switch_table(self):
        create_table_sql = ' '.join((
                'create table if not exists switch (',
                'userid       varchar(8)    COLLATE NOCASE,',
                'interface    varchar(4)    COLLATE NOCASE,',
                'switch       varchar(8)    COLLATE NOCASE,',
                'port         varchar(128)  COLLATE NOCASE,',
                'comments     varchar(128),',
                'primary key (userid, interface));'))
        with get_network_conn() as conn:
            conn.execute(create_table_sql)

    def _get_switch_by_user_interface(self, userid, interface):
        with get_network_conn() as conn:
            res = conn.execute("SELECT * FROM switch "
                               "WHERE userid=? and interface=?",
                               (userid, interface))
            switch_record = res.fetchall()

        if len(switch_record) == 1:
            return switch_record[0]
        elif len(switch_record) == 0:
            return None

    def switch_delete_record_for_userid(self, userid):
        """Remove userid switch record from switch table."""
        with get_network_conn() as conn:
            conn.execute("DELETE FROM switch WHERE userid=?",
                         (userid,))
            LOG.debug("Switch record for user %s is removed from "
                      "switch table" % userid)

    def switch_delete_record_for_nic(self, userid, interface):
        """Remove userid switch record from switch table."""
        with get_network_conn() as conn:
            conn.execute("DELETE FROM switch WHERE userid=? and interface=?",
                         (userid, interface))
            LOG.debug("Switch record for user %s with nic %s is removed from "
                      "switch table" % (userid, interface))

    def switch_add_record(self, userid, interface, port=None,
                          switch=None, comments=None):
        """Add userid and nic name address into switch table."""
        with get_network_conn() as conn:
            conn.execute("INSERT INTO switch VALUES (?, ?, ?, ?, ?)",
                         (userid, interface, switch, port, comments))
            LOG.debug("New record in the switch table: user %s, "
                      "nic %s, port %s" %
                      (userid, interface, port))

    def switch_add_record_migrated(self, userid, interface, switch,
                             port=None, comments=None):
        """Add userid and interfaces and switch into switch table."""
        with get_network_conn() as conn:
            conn.execute("INSERT INTO switch VALUES (?, ?, ?, ?, ?)",
                         (userid, interface, switch, port, comments))
            LOG.debug("New record in the switch table: user %s, "
                      "nic %s, switch %s" %
                      (userid, interface, switch))

    def switch_update_record_with_switch(self, userid, interface,
                                         switch=None):
        """Update information in switch table."""
        if not self._get_switch_by_user_interface(userid, interface):
            msg = "User %s with nic %s does not exist in DB" % (userid,
                                                                interface)
            LOG.error(msg)
            obj_desc = ('User %s with nic %s' % (userid, interface))
            raise exception.SDKObjectNotExistError(obj_desc,
                                                   modID=self._module_id)

        if switch is not None:
            with get_network_conn() as conn:
                conn.execute("UPDATE switch SET switch=? "
                             "WHERE userid=? and interface=?",
                             (switch, userid, interface))
                LOG.debug("Set switch to %s for user %s with nic %s "
                          "in switch table" %
                          (switch, userid, interface))
        else:
            with get_network_conn() as conn:
                conn.execute("UPDATE switch SET switch=NULL "
                             "WHERE userid=? and interface=?",
                             (userid, interface))
                LOG.debug("Set switch to None for user %s with nic %s "
                          "in switch table" %
                          (userid, interface))

    def _parse_switch_record(self, switch_list):
        # Map each switch record to be a dict, with the key is the field name
        # in switch DB
        switch_keys_list = ['userid', 'interface', 'switch',
                            'port', 'comments']

        switch_result = []
        for item in switch_list:
            switch_item = dict(zip(switch_keys_list, item))
            switch_result.append(switch_item)
        return switch_result

    def switch_select_table(self):
        with get_network_conn() as conn:
            result = conn.execute("SELECT * FROM switch")
            nic_settings = result.fetchall()
        return self._parse_switch_record(nic_settings)

    def switch_select_record_for_userid(self, userid):
        with get_network_conn() as conn:
            result = conn.execute("SELECT * FROM switch "
                                  "WHERE userid=?", (userid,))
            switch_info = result.fetchall()
        return self._parse_switch_record(switch_info)

    def switch_select_record(self, userid=None, nic_id=None, vswitch=None):
        if ((userid is None) and
            (nic_id is None) and
            (vswitch is None)):
            return self.switch_select_table()

        sql_cmd = "SELECT * FROM switch WHERE"
        sql_var = []
        if userid is not None:
            sql_cmd += " userid=? and"
            sql_var.append(userid)
        if nic_id is not None:
            sql_cmd += " port=? and"
            sql_var.append(nic_id)
        if vswitch is not None:
            sql_cmd += " switch=?"
            sql_var.append(vswitch)

        # remove the tailing ' and'
        sql_cmd = sql_cmd.strip(' and')

        with get_network_conn() as conn:
            result = conn.execute(sql_cmd, sql_var)
            switch_list = result.fetchall()

        return self._parse_switch_record(switch_list)


class FCPDbOperator(object):

    def __init__(self):
        self._module_id = 'volume'
        self._initialize_table()

    def _initialize_table(self):
        # fcp_info_tables:
        #   map the table name to the corresponding SQL to create it
        #   key is the name of table to be created
        #   value is the SQL to be executed to create the table
        fcp_info_tables = {}
        # table for basic info of FCP devices
        #   fcp_id: FCP device ID
        #   assigner_id: foreign key representing a VM
        #   connections: how many volumes connected to this FCP device,
        #                0 means no assigner
        #   reserved: 0 for not reserved by some operation
        #   wwpn_npiv: NPIV WWPN number
        #   wwpn_phy: Physical WWPN number
        #   chpid: CHPID of FCP device
        #   tmple_id: indecate which FCP template this FCP device was
        #             allocated from, not which FCP template this FCP
        #             device is in. because a FCP device may belong
        #             to multiple FCP templates.
        fcp_info_tables['fcp'] = (
            'CREATE TABLE IF NOT EXISTS fcp('
            'fcp_id         char(4)    PRIMARY KEY COLLATE NOCASE,'
            'assigner_id    varchar(8) COLLATE NOCASE,'
            'connections    integer,'
            'reserved       integer,'
            'comment        varchar(128),'
            'wwpn_npiv      varchar(16) COLLATE NOCASE,'
            'wwpn_phy       varchar(16) COLLATE NOCASE,'
            'chpid          char(2),'
            'tmpl_id        varchar(32))')

        # table for FCP templates:
        #   id: template uuid, the primary key
        #   name: the name of the template
        #   description: the description for this template
        #   is_default: is this template the default one on this host or not
        #            1 for yes, 0 for no
        fcp_info_tables['template'] = (
            'CREATE TABLE IF NOT EXISTS template('
            'id             varchar(32) PRIMARY KEY COLLATE NOCASE,'
            'name           varchar(128),'
            'description    varchar(255),'
            'is_default     integer)')

        # table for relationships between templates and storage providers:
        #   tmpl_id: template uuid, the primary key
        #   tmple_name: the name of the template
        #   default: is this template the default one for a storage provider?
        #            1 for yes, 0 for no
        #   composite primary key (tmpl_id, sp_name)
        fcp_info_tables['template_sp_mapping'] = (
            'CREATE TABLE IF NOT EXISTS template_sp_mapping('
            'sp_name        varchar(128) PRIMARY KEY COLLATE NOCASE,'
            'tmpl_id        varchar(32))')

        # table for relationships between templates and FCP devices:
        #   fcp_id: the fcp device ID
        #   tmpl_id: the template uuid
        #   path: the path number, 0 means the FCP device is in path0
        #         1 means the FCP devices is in path1, and so on.
        #   composite primary key (fcp_id, tmpl_id)
        fcp_info_tables['template_fcp_mapping'] = (
            'CREATE TABLE IF NOT EXISTS template_fcp_mapping('
            'fcp_id         char(4),'
            'tmpl_id        varchar(32),'
            'path           integer,'
            'PRIMARY KEY (fcp_id, tmpl_id))')

        # create all the tables
        with get_fcp_conn() as conn:
            for table_name in fcp_info_tables:
                LOG.info("Creating table {} in FCP "
                         "database.".format(table_name))
                create_table_sql = fcp_info_tables[table_name]
                conn.execute(create_table_sql)
                LOG.info("Table {} created in FCP "
                         "database.".format(table_name))

    def _update_reserve(self, fcp, reserved):
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET reserved=? "
                         "WHERE fcp_id=?",
                         (reserved, fcp))

    def unreserve(self, fcp):
        self._update_reserve(fcp, 0)

    def reserve(self, fcp):
        self._update_reserve(fcp, 1)

    def is_reserved(self, fcp):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT reserved FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            reserved_data = result.fetchall()
            if not reserved_data:
                return False
            reserved = reserved_data[0][0]
            return reserved == 1

    def insert_multiple_records_into_fcp_table(self, fcp_info_list):
        """Insert multiple FCP records into fcp table.
        The fcp_info_list must be a list of FCP info set, for example:
        the input fcp_info should be list of FCP info set, for example:
        [('1a06', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user1'),
         ('1a07', 'c05076de33000355', 'c05076de33002641', '27', 'free',
          'user1'),
         ('1a08', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user2')]
        """
        data_to_insert = list()
        for fcp in fcp_info_list:
            new_comment = str({'state': fcp[4], 'owner': fcp[5]})
            # compose a new list for update sql
            # it is like for example:
            # ['c05076de33000355', 'c05076de33002641', '27',
            #  "{'state': '', 'owner': 'user1'}", '1a08']
            new_record = list(fcp[0:4]) + [new_comment]
            data_to_insert.append(new_record)
        with get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp (fcp_id, wwpn_npiv, wwpn_phy, "
                             "chpid, comment) VALUES "
                             "(?, ?, ?, ?, ?)", data_to_insert)

    def insert_one_record_into_fcp_table(self, fcp_info):
        """Insert one FCP record into fcp Table"""
        with get_fcp_conn() as conn:
            conn.execute("INSERT INTO fcp (fcp_id, assigner_id, "
                         "connections, reserved, comment, "
                         "wwpn_npiv, wwpn_phy, chpid) VALUES "
                         "(?, ?, ?, ?, ?, ?, ?, ?)", fcp_info)

    def delete_multiple_records_from_fcp_table(self, fcp_id_list):
        """Delete multiple FCP records from fcp table
        The fcp_id_list is list of FCP IDs, for example:
        ['1a00', '1b01', '1c02']
        """
        with get_fcp_conn() as conn:
            conn.executemany("DELETE FROM fcp "
                             "WHERE fcp_id=?", fcp_id_list)

    def delete_one_record_from_fcp_table(self, fcp_id):
        """Delete one FCP record from fcp table"""
        with get_fcp_conn() as conn:
            conn.execute("DELETE FROM fcp "
                         "WHERE fcp_id=?", (fcp_id,))

    def update_multiple_records_in_fcp_table(self, fcp_info_list):
        """Update basic FCP info queried from zvm
        the input fcp_info should be list of FCP info set, for example:
        [('1a06', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user1'),
         ('1a07', 'c05076de33000355', 'c05076de33002641', '27', 'free',
          'user1'),
         ('1a08', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user2')]
         """
        # transfer state and owner to a comment dict
        # the key is the id of the FCP device, the value is a comment dict
        # for example:
        # {'1a07': {'state': 'free', 'owner': 'user1'},
        #  '1a08': {'state': 'active', 'owner': 'user2'}}
        data_to_update = list()
        for fcp in fcp_info_list:
            new_comment = str({'state': fcp[4], 'owner': fcp[5]})
            # compose a new list for update sql
            # it is like for example:
            # ['c05076de33000355', 'c05076de33002641', '27',
            #  "{'state': '', 'owner': 'user1'}", '1a08']
            new_record = list(fcp[1:4]) + [new_comment, fcp[0]]
            data_to_update.append(new_record)
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp SET wwpn_npiv=?, wwpn_phy=?, "
                             "chpid=?, comment=? WHERE "
                             "fcp_id=?", data_to_update)

    def mark_records_as_notfound(self, fcp_id_list):
        """Update multiple records' comments to update the state to nofound.
        """
        data_to_update = list()
        for id in fcp_id_list:
            new_comment = str({'state': 'notfound'})
            new_record = [new_comment, id]
            data_to_update.append(new_record)
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp set comment=? "
                             "WHERE fcp_id=?", data_to_update)

    def assign(self, fcp, assigner_id, update_connections=True):
        with get_fcp_conn() as conn:
            if update_connections:
                conn.execute("UPDATE fcp SET assigner_id=?, connections=? "
                             "WHERE fcp_id=?",
                             (assigner_id, 1, fcp))
            else:
                conn.execute("UPDATE fcp SET assigner_id=? "
                             "WHERE fcp_id=?",
                             (assigner_id, fcp))

    def get_all_fcps_of_assigner(self, assigner_id=None):
        """Get dict of all fcp records of specified assigner.
        If assigner is None, will get all fcp records.
        Format of return is like :
        [
          (fcp_id, userid, connections, reserved, comment,
           wwpn_npiv, wwpn_phy, chpid, tmpl_id),
          ('283c', 'user1', 2, 1, {'state': 'active', 'owner': 'user1'},
           'c05076ddf7000002', 'c05076ddf7001d81', 27, ''),
          ('483c', 'user2', 0, 0, {'state': 'free', 'owner': 'NONE'},
           'c05076ddf7000001', 'c05076ddf7001d82', 27, '')
        ]
        """
        with get_fcp_conn() as conn:
            if assigner_id:
                result = conn.execute("SELECT fcp_id, assigner_id, "
                                      "connections, reserved, comment, "
                                      "wwpn_npiv, wwpn_phy, chpid, "
                                      "tmpl_id FROM fcp WHERE "
                                      "assigner_id=?", (assigner_id,))
            else:
                result = conn.execute("SELECT fcp_id, assigner_id, "
                                      "connections, reserved, comment, "
                                      "wwpn_npiv, wwpn_phy, chpid, "
                                      "tmpl_id FROM fcp")
            results = result.fetchall()
            if not results:
                if assigner_id:
                    obj_desc = "FCP belongs to userid: %s" % assigner_id
                else:
                    obj_desc = "FCP records in database"
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            else:
                # transfer comment str to dict format
                fcp_info = []
                for item in results:
                    item = list(item)
                    comment = item[4]
                    # Expectedly, comment is a string, such as,
                    # "{'state': 'xxx', 'owner': 'yyy'}"
                    if (comment and
                            comment.startswith('{') and
                            comment.endswith('}')):
                        item[4] = eval(comment)
                    fcp_info.append(tuple(item))
        return fcp_info

    def get_usage_of_fcp(self, fcp):
        connections = 0
        reserved = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT assigner_id, reserved, connections "
                                  "FROM fcp WHERE fcp_id=?", (fcp,))
            fcp_info = result.fetchall()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            assigner_id = fcp_info[0][0]
            reserved = fcp_info[0][1]
            connections = fcp_info[0][2]

        return assigner_id, reserved, connections

    def update_usage_of_fcp(self, fcp, assigner_id, reserved, connections):
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET assigner_id=?, reserved=?, "
                         "connections=? WHERE fcp_id=?", (assigner_id,
                                                          reserved,
                                                          connections,
                                                          fcp))

    def get_comment_of_fcp(self, fcp):
        """Get the comment content, transfer into dict and return.
        """
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT comment "
                                  "FROM fcp WHERE fcp_id=?", (fcp,))
            current_comment = result.fetchall()
            # current_comment example
            # [("{'state': 'free', 'owner': 'NONE'}",)] or []
            if (len(current_comment) == 1 and
                    current_comment[0][0].startswith('{') and
                    current_comment[0][0].endswith('}')):
                # transfer from str to dict
                comment = eval(current_comment[0][0])
            else:
                comment = {}
        return comment

    def update_comment_of_fcp(self, fcp, comment_dict):
        """Update the cotent of comment.
        :param fcp: (str) the FCP ID string
        :param comment_dict: (dict) the dict to describe the FCP status
            this api will transfer this into string and store into db
        The comment in database should be a string like:
            "{'state': 'active', 'owner': 'iaas0001'}"
        """
        # the input parameter comment_dict must be a dict
        if not isinstance(comment_dict, dict):
            msg = ("Failed to update comment of FCP %s because input "
                   "comment %s is not a dict type." % (fcp, comment_dict))
            raise exception.SDKInternalError(msg=msg, modID=self._module_id)
        new_comment = str(comment_dict)
        # storage the new comment into database
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET comment=? "
                         "WHERE fcp_id=?", (new_comment, fcp))

    def update_path_of_fcp(self, fcp, path):
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET path=? WHERE "
                         "fcp_id=?", (path, fcp))

    def increase_usage(self, fcp):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            fcp_list = result.fetchall()
            if not fcp_list:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_list[0][2]
            connections += 1

            conn.execute("UPDATE fcp SET connections=? "
                         "WHERE fcp_id=?", (connections, fcp))
            return connections

    def increase_usage_by_assigner(self, fcp, assigner_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            fcp_list = result.fetchall()
            if not fcp_list:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_list[0][2]
            connections += 1

            conn.execute("UPDATE fcp SET assigner_id=?, connections=? "
                         "WHERE fcp_id=?", (assigner_id, connections, fcp))
            return connections

    def decrease_usage(self, fcp):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            fcp_list = result.fetchall()
            if not fcp_list:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_list[0][2]
            if connections == 0:
                msg = 'FCP with id: %s no connections in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            else:
                connections -= 1
            if connections < 0:
                connections = 0
                LOG.warning("Warning: connections of fcp is negative",
                            fcp)

            conn.execute("UPDATE fcp SET connections=? "
                         "WHERE fcp_id=?",
                         (connections, fcp))
            return connections

    def get_connections_from_assigner(self, assigner_id):
        connections = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "assigner_id=?", (assigner_id,))
            fcp_list = result.fetchall()
            if not fcp_list:
                connections = 0
            else:
                for fcp in fcp_list:
                    connections = connections + fcp[2]
        return connections

    def get_connections_from_fcp(self, fcp):
        connections = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT connections FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            fcp_info = result.fetchall()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_info[0][0]

        return connections

    def get_allocated_fcps_from_assigner(self, assigner_id, fcp_template_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM template_fcp_mapping "
                                  "INNER JOIN fcp "
                                  "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                                  "WHERE template_fcp_mapping.tmpl_id=? "
                                  "AND fcp.assigner_id=? "
                                  "AND (fcp.connections<>0 OR fcp.reserved<>0) "
                                  "ORDER BY template_fcp_mapping.fcp_id ASC", (fcp_template_id, assigner_id))
            fcp_list = result.fetchall()
        return fcp_list

    def get_reserved_fcps_from_assigner(self, assigner_id, fcp_template_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM template_fcp_mapping "
                                  "INNER JOIN fcp "
                                  "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                                  "WHERE template_fcp_mapping.tmpl_id=? "
                                  "AND fcp.assigner_id=? "
                                  "AND (fcp.connections<>0 OR fcp.reserved<>0) "
                                  "ORDER BY template_fcp_mapping.fcp_id ASC", (fcp_template_id, assigner_id))
            fcp_list = result.fetchall()

        return fcp_list

    def get_all(self):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp")
            fcp_list = result.fetchall()

        return fcp_list

    def get_from_fcp(self, fcp):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp where fcp_id=?", (fcp,))
            fcp_list = result.fetchall()

        return fcp_list

    def get_path_count(self):
        with get_fcp_conn() as conn:
            # Get distinct path list in DB
            result = conn.execute("SELECT DISTINCT path FROM template_fcp_mapping")
            path_list = result.fetchall()

        return len(path_list)

    def get_fcp_pair_with_same_index(self, fcp_template_id):
        """ Get a group of available FCPs with the same index,
            which also need satisfy the following conditions:
            a. connections = 0
            b. reserved = 0
            c. comment includes 'state': 'free'

        :return fcp_list: (list)
        case 1
            an empty list(i.e. [])
            if no fcp exist in DB
        case 2
           an empty list(i.e. [])
           if no expected pair found
        case 3
           randomly choose a pair of below combinations:
           [1a00,1b00] ,[1a01,1b01] ,[1a02,1b02]...
           rather than below combinations:
           [1a00,1b02] ,[1a03,1b00]
           [1a02], [1b03]
        """
        fcp_list = []
        fcp_pair_map = {}
        with get_fcp_conn() as conn:
            '''
            count_per_path examples:
            in normal cases, all path has same count, eg.
            4 paths: [7, 7, 7, 7]
            2 paths: [7, 7]
            we can also handle rare abnormal cases,
            where path count differs, eg.
            4 paths: [7, 4, 5, 6]
            2 paths: [7, 6]
            '''
            result = conn.execute("SELECT COUNT(path) FROM template_fcp_mapping "
                                  "GROUP BY path "
                                  "ORDER BY path ASC")
            count_per_path = [a[0] for a in result.fetchall()]
            # case1: return [] if no fcp found in FCP DB
            if not count_per_path:
                LOG.error("Not enough FCPs available, return empty list.")
                return fcp_list
            result = conn.execute("SELECT COUNT(template_fcp_mapping.path) FROM template_fcp_mapping "
                                  "INNER JOIN fcp "
                                  "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                                  "WHERE template_fcp_mapping.tmpl_id=? "
                                  "AND fcp.connections=0 "
                                  "AND fcp.reserved=0 "
                                  "AND fcp.comment LIKE \"%state': 'free%\" "
                                  "GROUP BY template_fcp_mapping.path "
                                  "ORDER BY template_fcp_mapping.path", (fcp_template_id, ))
            free_count_per_path = [a[0] for a in result.fetchall()]
            # case2: return [] if no free fcp found from at least one path
            if len(free_count_per_path) < len(count_per_path):
                # For get_fcp_pair_with_same_index, we will not check the
                # CONF.volume.min_fcp_paths_count, the returned fcp count
                # should always equal to the total paths count
                LOG.error("Available paths count: %s, total paths count: "
                          "%s." %
                          (len(free_count_per_path), len(count_per_path)))
                return fcp_list
            '''
            fcps 2 paths example:
               fcp  conn reserved
              ------------------
            [('1a00', 1, 1, "{'state': 'active', 'owner': 'user1'}"),
             ('1a01', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ('1a02', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ('1a03', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ('1a04', 0, 0, "{'state': 'offline', 'owner': 'user3'}"),
             ...
             ('1b00', 1, 0, "{'state': 'active', 'owner': 'user1'}"),
             ('1b01', 2, 1, "{'state': 'active', 'owner': 'user2'}"),
             ('1b02', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ('1b03', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ('1b04', 0, 0, "{'state': 'free', 'owner': 'NONE'}"),
             ...           ]
            '''
            result = conn.execute("SELECT fcp.fcp_id, fcp.connections, "
                                  "fcp.reserved, fcp.comment "
                                  "FROM fcp "
                                  "INNER JOIN template_fcp_mapping "
                                  "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                                  "WHERE template_fcp_mapping.tmpl_id=? "
                                  "ORDER BY template_fcp_mapping.path, template_fcp_mapping.fcp_id", (fcp_template_id,))
            fcps = result.fetchall()
        '''
        get all free fcps from 1st path
        fcp_pair_map example:
         idx    fcp_pair
         ----------------
        { 1 : ['1a01'],
          2 : ['1a02'],
          3 : ['1a03']}
        '''
        # The FCP count of 1st path
        for i in range(free_count_per_path[0]):
            fcp_no = fcps[i][0]
            connections = fcps[i][1]
            reserved = fcps[i][2]
            comment = fcps[i][3]
            # Expectedly, comment is a string, such as,
            # "{'state': 'xxx', 'owner': 'yyy'}"
            if comment.startswith('{') and comment.endswith('}'):
                state = eval(comment).get('state', '')
            else:
                state = ''
            if connections == reserved == 0 and state == 'free':
                fcp_pair_map[i] = [fcp_no]
        '''
        select out pairs if member count == path count
        fcp_pair_map example:
         idx    fcp_pair
         ----------------------
        { 2 : ['1a02', '1b02'],
          3 : ['1a03', '1b03']}
        '''
        for idx in fcp_pair_map.copy():
            s = 0
            for i, c in enumerate(free_count_per_path[:-1]):
                s += c
                # avoid index out of range for per path in fcps[]
                fcp_no = fcps[s + idx][0]
                connections = fcps[s + idx][1]
                reserved = fcps[s + idx][2]
                comment = fcps[s + idx][3]
                if comment.startswith('{') and comment.endswith('}'):
                    state = eval(comment).get('state', '')
                else:
                    state = ''
                if (idx < count_per_path[i + 1] and
                        connections == reserved == 0 and
                        state == 'free'):
                    fcp_pair_map[idx].append(fcp_no)
                else:
                    fcp_pair_map.pop(idx)
                    break
        '''
        case3: return one group randomly chosen from fcp_pair_map
        fcp_list example:
        ['1a03', '1b03']
        '''
        LOG.info("Print at most 5 available FCP groups: {}".format(
            list(fcp_pair_map.values())[:5]))
        if fcp_pair_map:
            fcp_list = random.choice(sorted(fcp_pair_map.values()))
        else:
            LOG.error("Not eligible FCP group found in FCP DB.")
        return fcp_list

    def get_fcp_pair(self, fcp_template_id):
        """ Get a group of available FCPs,
            which satisfy the following conditions:
            a. connections = 0
            b. reserved = 0
            c. comment includes 'state': 'free'
        """
        fcp_list = []
        with get_fcp_conn() as conn:
            # Get distinct path list in DB
            result = conn.execute("SELECT DISTINCT path FROM template_fcp_mapping")
            path_list = result.fetchall()
            # Get fcp_list of every path
            for no in path_list:
                result = conn.execute("SELECT * FROM template_fcp_mapping "
                                      "INNER JOIN fcp "
                                      "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                                      "WHERE template_fcp_mapping.tmpl_id=? "
                                      "AND fcp.connections=0 "
                                      "AND fcp.reserved=0 "
                                      "AND fcp.comment LIKE \"%state': 'free%\" "
                                      "AND template_fcp_mapping.path=? "
                                      "ORDER BY template_fcp_mapping.fcp_id", (fcp_template_id, no[0]))
                fcps = result.fetchall()
                if not fcps:
                    # continue to find whether other paths has available FCP
                    continue
                index = random.randint(0, len(fcps) - 1)
                fcp_list.append(fcps[index][0])
        # Start to check whether the available count >= min_fcp_paths_count
        allocated_paths = len(fcp_list)
        total_paths = len(path_list)
        if allocated_paths < total_paths:
            LOG.info("Not all paths have available FCP devices. "
                     "The count of paths having available FCP: %d is less "
                     "than total paths: %d. "
                     "The configured minimum FCP paths count is: %d." %
                     (allocated_paths, total_paths,
                      CONF.volume.min_fcp_paths_count))
            if allocated_paths >= CONF.volume.min_fcp_paths_count:
                LOG.warning("Return the FCPs from the available paths to "
                            "continue.")
                return fcp_list
            else:
                LOG.error("Not enough FCPs available, return empty list.")
                return []
        else:
            return fcp_list

    def get_default_fcp_template(self):
        """Get the default FCP template for this Host."""
        with get_fcp_conn() as conn:
            result = conn.execute("select id from template where is_default=1")
            fcp_tmpl_id = result.fetchall()
            if fcp_tmpl_id:
                return fcp_tmpl_id[0][0]
            else:
                LOG.warning("Can not find the default FCP template for this host.")
                return []

    def get_all_free_unreserved(self):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp where connections=0 "
                                  "and reserved=0")
            fcp_list = result.fetchall()

        return fcp_list

    def get_wwpns_of_fcp(self, fcp):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT wwpn_npiv, wwpn_phy FROM fcp "
                                  "WHERE fcp_id=?", (fcp,))
            wwpns_info = result.fetchall()
            if not wwpns_info:
                msg = 'WWPNs of fcp %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "WWPNs of FCP %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            wwpn_npiv = wwpns_info[0][0]
            wwpn_phy = wwpns_info[0][1]
        return wwpn_npiv, wwpn_phy

    def update_wwpns_of_fcp(self, fcp, wwpn_npiv, wwpn_phy):
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET wwpn_npiv=?, wwpn_phy=? "
                         "WHERE fcp_id=?",
                         (wwpn_npiv, wwpn_phy, fcp))

    def get_fcp_list_of_template(self, tmpl_id):
        """Get the FCP devices set index by path.
        For example:
        {
            0: {'1a00', '1a01', '1a02'},
            1: {'1b00', '1b01', '1b02'},
        }
        """
        fcp_list = {}
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT fcp_id, path FROM "
                                  "relationship_template_fcp "
                                  "WHERE tmpl_id=?", (tmpl_id,))
            fcp_by_path = result.fetchall()
            if not fcp_by_path:
                msg = ('FCP devices under template %s does not '
                       'exist in DB.' % tmpl_id)
                LOG.error(msg)
                obj_desc = "FCP devices under template %s" % tmpl_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            for fcp in fcp_by_path:
                if not fcp_list.get(fcp[1], None):
                    fcp_list[fcp[1]] = set()
                fcp_list[fcp[1]].add(fcp[0])
        return fcp_list


class ImageDbOperator(object):

    def __init__(self):
        self._create_image_table()
        self._module_id = 'image'

    def _create_image_table(self):
        create_image_table_sql = ' '.join((
                'CREATE TABLE IF NOT EXISTS image (',
                'imagename         varchar(128) PRIMARY KEY COLLATE NOCASE,',
                'imageosdistro            varchar(16),',
                'md5sum                   varchar(512),',
                'disk_size_units          varchar(512),',
                'image_size_in_bytes      varchar(512),',
                'type                     varchar(16),',
                'comments                 varchar(128))'))
        with get_image_conn() as conn:
            conn.execute(create_image_table_sql)

    def image_add_record(self, imagename, imageosdistro, md5sum,
                         disk_size_units, image_size_in_bytes,
                         type, comments=None):
        if comments is not None:
            with get_image_conn() as conn:
                conn.execute("INSERT INTO image (imagename, imageosdistro,"
                             "md5sum, disk_size_units, image_size_in_bytes,"
                             " type, comments) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (imagename, imageosdistro, md5sum,
                              disk_size_units, image_size_in_bytes, type,
                              comments))
        else:
            with get_image_conn() as conn:
                conn.execute("INSERT INTO image (imagename, imageosdistro,"
                             "md5sum, disk_size_units, image_size_in_bytes,"
                             " type) VALUES (?, ?, ?, ?, ?, ?)",
                             (imagename, imageosdistro, md5sum,
                              disk_size_units, image_size_in_bytes, type))

    def image_query_record(self, imagename=None):
        """Query the image record from database, if imagename is None, all
        of the image records will be returned, otherwise only the specified
        image record will be returned."""

        if imagename:
            with get_image_conn() as conn:
                result = conn.execute("SELECT * FROM image WHERE "
                                      "imagename=?", (imagename,))
                image_list = result.fetchall()
            if not image_list:
                obj_desc = "Image with name: %s" % imagename
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID=self._module_id)
        else:
            with get_image_conn() as conn:
                result = conn.execute("SELECT * FROM image")
                image_list = result.fetchall()

        # Map each image record to be a dict, with the key is the field name in
        # image DB
        image_keys_list = ['imagename', 'imageosdistro', 'md5sum',
                      'disk_size_units', 'image_size_in_bytes', 'type',
                      'comments']

        image_result = []
        for item in image_list:
            image_item = dict(zip(image_keys_list, item))
            image_result.append(image_item)
        return image_result

    def image_delete_record(self, imagename):
        """Delete the record of specified imagename from image table"""
        with get_image_conn() as conn:
            conn.execute("DELETE FROM image WHERE imagename=?", (imagename,))


class GuestDbOperator(object):

    def __init__(self):
        self._create_guests_table()
        self._module_id = 'guest'

    def _create_guests_table(self):
        """
        net_set: it is used to describe network interface status, the initial
                 value is 0, no network interface. It will be updated to be
                 1 after the network interface is configured
        """
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS guests(',
            'id             char(36)     PRIMARY KEY COLLATE NOCASE,',
            'userid         varchar(8)   NOT NULL UNIQUE  COLLATE NOCASE,',
            'metadata       varchar(255),',
            'net_set        smallint      DEFAULT 0,',
            'comments       text)'))
        with get_guest_conn() as conn:
            conn.execute(sql)

    def _check_existence_by_id(self, guest_id, ignore=False):
        guest = self.get_guest_by_id(guest_id)
        if guest is None:
            msg = 'Guest with id: %s does not exist in DB.' % guest_id
            if ignore:
                # Just print a warning message
                LOG.info(msg)
            else:
                LOG.error(msg)
                obj_desc = "Guest with id: %s" % guest_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
        return guest

    def _check_existence_by_userid(self, userid, ignore=False):
        guest = self.get_guest_by_userid(userid)
        if guest is None:
            msg = 'Guest with userid: %s does not exist in DB.' % userid
            if ignore:
                # Just print a warning message
                LOG.info(msg)
            else:
                LOG.error(msg)
                obj_desc = "Guest with userid: %s" % userid
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
        return guest

    def add_guest_registered(self, userid, meta, net_set,
                             comments=None):
        # Add guest which is migrated from other host or onboarded.
        guest_id = str(uuid.uuid4())
        with get_guest_conn() as conn:
            conn.execute(
                "INSERT INTO guests VALUES (?, ?, ?, ?, ?)",
                (guest_id, userid, meta, net_set, comments))

    def add_guest(self, userid, meta='', comments=''):
        # Generate uuid automatically
        guest_id = str(uuid.uuid4())
        net_set = '0'
        with get_guest_conn() as conn:
            conn.execute(
                "INSERT INTO guests VALUES (?, ?, ?, ?, ?)",
                (guest_id, userid, meta, net_set, comments))

    def delete_guest_by_id(self, guest_id):
        # First check whether the guest exist in db table
        guest = self._check_existence_by_id(guest_id, ignore=True)
        if guest is None:
            return
        # Update guest if exist
        with get_guest_conn() as conn:
            conn.execute(
                "DELETE FROM guests WHERE id=?", (guest_id,))

    def delete_guest_by_userid(self, userid):
        # First check whether the guest exist in db table
        guest = self._check_existence_by_userid(userid, ignore=True)
        if guest is None:
            return
        with get_guest_conn() as conn:
            conn.execute(
                "DELETE FROM guests WHERE userid=?", (userid,))

    def get_guest_metadata_with_userid(self, userid):
        with get_guest_conn() as conn:
            res = conn.execute("SELECT metadata FROM guests "
                               "WHERE userid=?", (userid,))
            guests = res.fetchall()
        return guests

    def update_guest_by_id(self, uuid, userid=None, meta=None, net_set=None,
                           comments=None):
        if ((userid is None) and (meta is None) and
            (net_set is None) and (comments is None)):
            msg = ("Update guest with id: %s failed, no field "
                   "specified to be updated." % uuid)
            LOG.error(msg)
            raise exception.SDKInternalError(msg=msg, modID=self._module_id)

        # First check whether the guest exist in db table
        self._check_existence_by_id(uuid)
        # Start update
        sql_cmd = "UPDATE guests SET"
        sql_var = []
        if userid is not None:
            sql_cmd += " userid=?,"
            sql_var.append(userid)
        if meta is not None:
            sql_cmd += " metadata=?,"
            sql_var.append(meta)
        if net_set is not None:
            sql_cmd += " net_set=?,"
            sql_var.append(net_set)
        if comments is not None:
            sql_cmd += " comments=?,"
            sql_var.append(comments)

        # remove the tailing comma
        sql_cmd = sql_cmd.strip(',')
        # Add the id filter
        sql_cmd += " WHERE id=?"
        sql_var.append(uuid)

        with get_guest_conn() as conn:
            conn.execute(sql_cmd, sql_var)

    def update_guest_by_userid(self, userid, meta=None, net_set=None,
                               comments=None):
        userid = userid
        if (meta is None) and (net_set is None) and (comments is None):
            msg = ("Update guest with userid: %s failed, no field "
                   "specified to be updated." % userid)
            LOG.error(msg)
            raise exception.SDKInternalError(msg=msg, modID=self._module_id)

        # First check whether the guest exist in db table
        self._check_existence_by_userid(userid)
        # Start update
        sql_cmd = "UPDATE guests SET"
        sql_var = []
        if meta is not None:
            sql_cmd += " metadata=?,"
            sql_var.append(meta)
        if net_set is not None:
            sql_cmd += " net_set=?,"
            sql_var.append(net_set)
        if comments is not None:
            new_comments = json.dumps(comments)
            sql_cmd += " comments=?,"
            sql_var.append(new_comments)

        # remove the tailing comma
        sql_cmd = sql_cmd.strip(',')
        # Add the id filter
        sql_cmd += " WHERE userid=?"
        sql_var.append(userid)

        with get_guest_conn() as conn:
            conn.execute(sql_cmd, sql_var)

    def get_guest_list(self):
        with get_guest_conn() as conn:
            res = conn.execute("SELECT * FROM guests")
            guests = res.fetchall()
        return guests

    def get_migrated_guest_list(self):
        with get_guest_conn() as conn:
            res = conn.execute("SELECT userid FROM guests "
                               "WHERE comments LIKE '%\"migrated\": 1%'")
            guests = res.fetchall()
        return guests

    def get_migrated_guest_info_list(self):
        with get_guest_conn() as conn:
            res = conn.execute("SELECT * FROM guests "
                               "WHERE comments LIKE '%\"migrated\": 1%'")
            guests = res.fetchall()
        return guests

    def get_comments_by_userid(self, userid):
        """ Get comments record.
        output should be like: {'k1': 'v1', 'k2': 'v2'}'
        """
        userid = userid
        with get_guest_conn() as conn:
            res = conn.execute("SELECT comments FROM guests "
                               "WHERE userid=?", (userid,))

        result = res.fetchall()
        comments = {}
        if result[0][0]:
            comments = json.loads(result[0][0])
        return comments

    def get_metadata_by_userid(self, userid):
        """get metadata record.
        output should be like: "a=1,b=2,c=3"
        """
        userid = userid
        with get_guest_conn() as conn:
            res = conn.execute("SELECT * FROM guests "
                               "WHERE userid=?", (userid,))
            guest = res.fetchall()

        if len(guest) == 1:
            return guest[0][2]
        elif len(guest) == 0:
            LOG.debug("Guest with userid: %s not found from DB!" % userid)
            return ''
        else:
            msg = "Guest with userid: %s have multiple records!" % userid
            LOG.error(msg)
            raise exception.SDKInternalError(msg=msg, modID=self._module_id)

    def transfer_metadata_to_dict(self, meta):
        """transfer str to dict.
        output should be like: {'a':1, 'b':2, 'c':3}
        """
        dic = {}
        arr = meta.strip(' ,').split(',')
        for i in arr:
            temp = i.split('=')
            key = temp[0].strip()
            value = temp[1].strip()
            dic[key] = value
        return dic

    def get_guest_by_id(self, guest_id):
        with get_guest_conn() as conn:
            res = conn.execute("SELECT * FROM guests "
                               "WHERE id=?", (guest_id,))
            guest = res.fetchall()
        # As id is the primary key, the filtered entry number should be 0 or 1
        if len(guest) == 1:
            return guest[0]
        elif len(guest) == 0:
            LOG.debug("Guest with id: %s not found from DB!" % guest_id)
            return None
        # Code shouldn't come here, just in case
        return None

    def get_guest_by_userid(self, userid):
        userid = userid
        with get_guest_conn() as conn:
            res = conn.execute("SELECT * FROM guests "
                               "WHERE userid=?", (userid,))
            guest = res.fetchall()
        # As id is the primary key, the filtered entry number should be 0 or 1
        if len(guest) == 1:
            return guest[0]
        elif len(guest) == 0:
            LOG.debug("Guest with userid: %s not found from DB!" % userid)
            return None
        # Code shouldn't come here, just in case
        return None
