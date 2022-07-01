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
from zvmsdk import utils


CONF = config.CONF
LOG = log.LOG


_DIR_MODE = 0o755
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
        # enable access columns by name
        _FCP_CONN.row_factory = sqlite3.Row
    _DBLOCK_FCP.acquire()
    try:
        # sqlite DB not allow to start a transaction within a transaction,
        # so, only begin a transaction when no other alive transaction
        if not _FCP_CONN.in_transaction:
            _FCP_CONN.execute("BEGIN")
            skip_commit = False
        else:
            skip_commit = True
        yield _FCP_CONN
    except exception.SDKBaseException as err:
        # rollback only if _FCP_CONN.execute("BEGIN")
        # is invoked when entering the contextmanager
        if not skip_commit:
            _FCP_CONN.execute("ROLLBACK")
        msg = "Got SDK exception in FCP DB operation: %s" % six.text_type(err)
        LOG.error(msg)
        raise
    except Exception as err:
        # rollback only if _FCP_CONN.execute("BEGIN")
        # is invoked when entering the contextmanager
        if not skip_commit:
            _FCP_CONN.execute("ROLLBACK")
        msg = "Execute SQL statements error: %s" % six.text_type(err)
        LOG.error(msg)
        raise exception.SDKGuestOperationError(rs=1, msg=msg)
    else:
        # commit only if _FCP_CONN.execute("BEGIN")
        # is invoked when entering the contextmanager
        if not skip_commit:
            _FCP_CONN.execute("COMMIT")
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
        #   fcp_id: FCP device ID, the primary key
        #   assigner_id: VM userid representing an unique VM,
        #                it is allocated by zvmsdk and may differ with owner
        #   connections: how many volumes connected to this FCP device,
        #                0 means no assigner
        #   reserved: 0 for not reserved by some operation
        #   wwpn_npiv: NPIV WWPN
        #   wwpn_phy: Physical WWPN
        #   chpid: channel ID of FCP device
        #   state: FCP device status
        #   owner: VM userid representing an unique VM,
        #          it is read from z/VM hypervisor and
        #          may differ with assigner_id
        #   tmpl_id: indicate from which FCP template this FCP device was
        #             allocated, not to which FCP template this FCP
        #             device belong. because a FCP device may belong
        #             to multiple FCP templates.
        fcp_info_tables['fcp'] = (
            "CREATE TABLE IF NOT EXISTS fcp("
            "fcp_id         char(4)     NOT NULL COLLATE NOCASE,"
            "assigner_id    varchar(8)  NOT NULL DEFAULT '' COLLATE NOCASE,"
            "connections    integer     NOT NULL DEFAULT 0,"
            "reserved       integer     NOT NULL DEFAULT 0,"
            "wwpn_npiv      varchar(16) NOT NULL DEFAULT '' COLLATE NOCASE,"
            "wwpn_phy       varchar(16) NOT NULL DEFAULT '' COLLATE NOCASE,"
            "chpid          char(2)     NOT NULL DEFAULT '' COLLATE NOCASE,"
            "state          varchar(8)  NOT NULL DEFAULT '' COLLATE NOCASE,"
            "owner          varchar(8)  NOT NULL DEFAULT '' COLLATE NOCASE,"
            "tmpl_id        varchar(32) NOT NULL DEFAULT '' COLLATE NOCASE,"
            "PRIMARY KEY (fcp_id))")

        # table for FCP templates:
        #   id: template id, the primary key
        #   name: the name of the template
        #   description: the description for this template
        #   is_default: is this template the default one on this host or not
        #       1/True for yes, 0/False for no
        #       note: SQLite recognizes the keywords "TRUE" and "FALSE",
        #       those keywords are saved in SQLite
        #       as integer 1 and 0 respectively
        fcp_info_tables['template'] = (
            "CREATE TABLE IF NOT EXISTS template("
            "id             varchar(32)  NOT NULL COLLATE NOCASE,"
            "name           varchar(128) NOT NULL COLLATE NOCASE,"
            "description    varchar(255) NOT NULL DEFAULT '' COLLATE NOCASE,"
            "is_default     integer      NOT NULL DEFAULT 0,"
            "PRIMARY KEY (id))")

        # table for relationships between templates and storage providers:
        #   sp_name: name of storage provider, the primary key
        #   tmpl_id: template id
        fcp_info_tables['template_sp_mapping'] = (
            'CREATE TABLE IF NOT EXISTS template_sp_mapping('
            'sp_name        varchar(128) NOT NULL COLLATE NOCASE,'
            'tmpl_id        varchar(32)  NOT NULL COLLATE NOCASE,'
            'PRIMARY KEY (sp_name))')

        # table for relationships between templates and FCP devices:
        #   fcp_id: the fcp device ID
        #   tmpl_id: the template id
        #   path: the path number, 0 means the FCP device is in path0
        #         1 means the FCP devices is in path1, and so on.
        #   composite primary key (fcp_id, tmpl_id)
        fcp_info_tables['template_fcp_mapping'] = (
            'CREATE TABLE IF NOT EXISTS template_fcp_mapping('
            'fcp_id         char(4)     NOT NULL COLLATE NOCASE,'
            'tmpl_id        varchar(32) NOT NULL COLLATE NOCASE,'
            'path           integer     NOT NULL,'
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

    #########################################################
    #                DML for Table fcp                      #
    #########################################################
    def unreserve_fcps(self, fcp_ids):
        if not fcp_ids:
            return
        fcp_update_info = []
        for fcp_id in fcp_ids:
            fcp_update_info.append((fcp_id,))
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp SET reserved=0, tmpl_id='' "
                             "WHERE fcp_id=?", fcp_update_info)

    def reserve_fcps(self, fcp_ids, assigner_id, fcp_template_id):
        fcp_update_info = []
        for fcp_id in fcp_ids:
            fcp_update_info.append(
                (assigner_id, fcp_template_id, fcp_id))
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp "
                             "SET reserved=1, assigner_id=?, tmpl_id=? "
                             "WHERE fcp_id=?", fcp_update_info)

    def bulk_insert_zvm_fcp_info_into_fcp_table(self, fcp_info_list: list):
        """Insert multiple records into fcp table witch fcp info queried
        from z/VM.

        The input fcp_info_list should be list of FCP info, for example:
        [(fcp_id, wwpn_npiv, wwpn_phy, chpid, state, owner),
         ('1a06', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user1'),
         ('1a07', 'c05076de33000355', 'c05076de33002641', '27', 'free',
          'user1'),
         ('1a08', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user2')]
        """
        with get_fcp_conn() as conn:
            conn.executemany("INSERT INTO fcp (fcp_id, wwpn_npiv, wwpn_phy, "
                             "chpid, state, owner) "
                             "VALUES (?, ?, ?, ?, ?, ?)", fcp_info_list)

    def bulk_delete_from_fcp_table(self, fcp_id_list: list):
        """Delete multiple FCP records from fcp table
        The fcp_id_list is list of FCP IDs, for example:
        ['1a00', '1b01', '1c02']
        """
        fcp_id_list = [(fcp_id,) for fcp_id in fcp_id_list]
        with get_fcp_conn() as conn:
            conn.executemany("DELETE FROM fcp "
                             "WHERE fcp_id=?", fcp_id_list)

    def bulk_update_zvm_fcp_info_in_fcp_table(self, fcp_info_list: list):
        """Update multiple records with FCP info queried from z/VM.

        The input fcp_info_list should be list of FCP info set, for example:
        [(fcp_id, wwpn_npiv, wwpn_phy, chpid, state, owner),
         ('1a06', 'c05076de33000355', 'c05076de33002641', '27', 'active',
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
            # change order of update data
            # the new order is like:
            #   (wwpn_npiv, wwpn_phy, chpid, state, owner, fcp_id)
            new_record = list(fcp[1:]) + [fcp[0]]
            data_to_update.append(new_record)
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp SET wwpn_npiv=?, wwpn_phy=?, "
                             "chpid=?, state=?, owner=? WHERE "
                             "fcp_id=?", data_to_update)

    def bulk_update_state_in_fcp_table(self, fcp_id_list: list,
                                       new_state: str):
        """Update multiple records' comments to update the state to nofound.
        """
        data_to_update = list()
        for id in fcp_id_list:
            new_record = [new_state, id]
            data_to_update.append(new_record)
        with get_fcp_conn() as conn:
            conn.executemany("UPDATE fcp set state=? "
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
          (fcp_id, userid, connections, reserved, wwpn_npiv, wwpn_phy,
           chpid, state, owner, tmpl_id),
          ('283c', 'user1', 2, 1, 'c05076ddf7000002', 'c05076ddf7001d81',
           27,'active', 'user1', ''),
          ('483c', 'user2', 0, 0, 'c05076ddf7000001', 'c05076ddf7001d82',
           27, 'free', 'NONE', '')
        ]
        """
        with get_fcp_conn() as conn:
            if assigner_id:
                result = conn.execute("SELECT fcp_id, assigner_id, "
                                      "connections, reserved, wwpn_npiv, "
                                      "wwpn_phy, chpid, state, owner, "
                                      "tmpl_id FROM fcp WHERE "
                                      "assigner_id=?", (assigner_id,))
            else:
                result = conn.execute("SELECT fcp_id, assigner_id, "
                                     "connections, reserved, wwpn_npiv, "
                                      "wwpn_phy, chpid, state, owner, "
                                      "tmpl_id FROM fcp")
            fcp_info = result.fetchall()
            if not fcp_info:
                if assigner_id:
                    obj_desc = ("FCP record in fcp table belongs to "
                                "userid: %s" % assigner_id)
                else:
                    obj_desc = "FCP records in fcp table"
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
        return fcp_info

    def get_usage_of_fcp(self, fcp_id):
        connections = 0
        reserved = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp "
                                  "WHERE fcp_id=?", (fcp_id,))
            fcp_info = result.fetchone()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp_id
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            assigner_id = fcp_info['assigner_id']
            reserved = fcp_info['reserved']
            connections = fcp_info['connections']

        return assigner_id, reserved, connections

    def update_usage_of_fcp(self, fcp, assigner_id, reserved, connections):
        with get_fcp_conn() as conn:
            conn.execute("UPDATE fcp SET assigner_id=?, reserved=?, "
                         "connections=? WHERE fcp_id=?", (assigner_id,
                                                          reserved,
                                                          connections,
                                                          fcp))

    def increase_usage(self, fcp_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "fcp_id=?", (fcp_id,))
            fcp_info = result.fetchone()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp_id
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_info['connections'] + 1

            conn.execute("UPDATE fcp SET connections=? "
                         "WHERE fcp_id=?", (connections, fcp_id))
            return connections

    def increase_usage_by_assigner(self, fcp, assigner_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE fcp_id=? "
                                  "AND assigner_id=?", (fcp, assigner_id))
            fcp_info = result.fetchone()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_info['connections'] + 1

            conn.execute("UPDATE fcp SET connections=? WHERE fcp_id=? "
                         "AND assigner_id=?", (connections, fcp, assigner_id))
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
        """Get sum connections count belongs to assigner_id"""
        connections = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT * FROM fcp WHERE "
                                  "assigner_id=?", (assigner_id,))
            fcp_list = result.fetchall()
            if not fcp_list:
                connections = 0
            else:
                for fcp in fcp_list:
                    connections = connections + fcp['connections']
        return connections

    def get_connections_from_fcp(self, fcp):
        connections = 0
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT connections FROM fcp WHERE "
                                  "fcp_id=?", (fcp,))
            fcp_info = result.fetchone()
            if not fcp_info:
                msg = 'FCP with id: %s does not exist in DB.' % fcp
                LOG.error(msg)
                obj_desc = "FCP with id: %s" % fcp
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            connections = fcp_info['connections']

        return connections

    def get_all(self):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp")
            fcp_list = result.fetchall()

        return fcp_list

    def get_from_fcp(self, fcp):
        with get_fcp_conn() as conn:

            result = conn.execute("SELECT * FROM fcp WHERE fcp_id=?", (fcp,))
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

    @staticmethod
    def get_inuse_fcp_device_by_fcp_template(fcp_template_id):
        """ Get the FCP devices allocated from the template """
        with get_fcp_conn() as conn:
            query_sql = conn.execute("SELECT * FROM fcp "
                                     "WHERE tmpl_id=?",
                                     (fcp_template_id,))
            result = query_sql.fetchall()
        # result example
        # [<sqlite3.Row object at 0x3ff8d1d64d0>,
        #  <sqlite3.Row object at 0x3ff8d1d6570>,
        #  <sqlite3.Row object at 0x3ff8d1d6590>]
        return result

    #########################################################
    #          DML for Table template_fcp_mapping           #
    #########################################################
    def get_path_of_fcp(self, fcp_id, fcp_template_id):
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT path FROM template_fcp_mapping "
                                  "WHERE fcp_id=? and tmpl_id=?",
                                  (fcp_id, fcp_template_id))
            path_info = result.fetchone()
            if not path_info:
                msg = ("path of fcp %s in template %s does not exist in "
                       "table template_fcp_mapping." % (fcp_id,
                                                        fcp_template_id))
                LOG.error(msg)
                obj_desc = "path of FCP %s" % fcp_id
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                       modID=self._module_id)
            return path_info['path']

    @staticmethod
    def update_path_of_fcp_device(record):
        """ update path of single fcp device
            from table template_fcp_mapping

            :param record (tuple)
                example:
                (path, fcp_id, fcp_template_id)

            :return NULL
        """
        with get_fcp_conn() as conn:
            conn.execute("UPDATE template_fcp_mapping "
                         "SET path=? "
                         "WHERE fcp_id=? and tmpl_id=?",
                         record)

    def get_path_count(self, fcp_template_id):
        with get_fcp_conn() as conn:
            # Get distinct path list in DB
            result = conn.execute(
                "SELECT DISTINCT path FROM template_fcp_mapping "
                "WHERE tmpl_id=?", (fcp_template_id,))
            path_list = result.fetchall()

        return len(path_list)

    @staticmethod
    def bulk_delete_fcp_device_from_fcp_template(records):
        """ Delete multiple fcp device
            from table template_fcp_mapping

            :param records (iter)
                example:
                [(fcp_template_id, fcp_id), ...]

            :return NULL
        """
        with get_fcp_conn() as conn:
            conn.executemany(
                "DELETE FROM template_fcp_mapping "
                "WHERE tmpl_id=? AND fcp_id=?",
                records)

    @staticmethod
    def bulk_insert_fcp_device_into_fcp_template(records):
        """ Insert multiple fcp device
            from table template_fcp_mapping

            :param records (iter)
                example:
                [
                    (fcp_template_id, fcp_id, path),
                    ...
                ]

            :return NULL
        """
        with get_fcp_conn() as conn:
            conn.executemany(
                "INSERT INTO template_fcp_mapping "
                "(tmpl_id, fcp_id, path) VALUES (?, ?, ?)",
                records)

    #########################################################
    #               DML for Table template                  #
    #########################################################
    def get_default_fcp_template(self):
        """Get the default FCP template for this Host."""
        with get_fcp_conn() as conn:
            result = conn.execute("SELECT id FROM template WHERE is_default=1")
            fcp_tmpl_id = result.fetchall()
            if fcp_tmpl_id:
                return fcp_tmpl_id[0][0]
            else:
                LOG.warning(
                    "Can not find the default FCP template for this host.")
                return ''

    def fcp_template_exist_in_db(self, fcp_template_id: str):
        with get_fcp_conn() as conn:
            query_sql = conn.execute("SELECT id FROM template "
                                     "WHERE id=?", (fcp_template_id,))
            query_ids = query_sql.fetchall()
        if query_ids:
            return True
        else:
            return False

    def fcp_template_allocated_in_db(self, tmpl_id: str):
        with get_fcp_conn() as conn:
            query_sql = conn.execute("SELECT tmpl_id FROM fcp "
                                     "WHERE tmpl_id=?", (tmpl_id,))
            query_ids = query_sql.fetchall()
        if query_ids:
            return True
        else:
            return False

    @staticmethod
    def update_basic_info_of_fcp_template(record):
        """ update basic info of a fcp template
            in table template

            :param record (tuple)
                example:
                (name, description, host_default, fcp_template_id)

            :return NULL
        """
        name, description, host_default, fcp_template_id = record
        with get_fcp_conn() as conn:
            # 1. change the is_default of existing templates to False,
            #    if the is_default of the being-created template is True,
            #    because only one default template per host is allowed
            if host_default is True:
                conn.execute("UPDATE template SET is_default=?", (False,))
            # 2. update current template
            conn.execute("UPDATE template "
                         "SET name=?, description=?, is_default=? "
                         "WHERE id=?",
                         record)

    #########################################################
    #          DML for Table template_sp_mapping            #
    #########################################################
    def sp_name_exist_in_db(self, sp_name: str):
        with get_fcp_conn() as conn:
            query_sp = conn.execute("SELECT sp_name FROM template_sp_mapping "
                                    "WHERE sp_name=?", (sp_name,))
            query_sp_names = query_sp.fetchall()

        if query_sp_names:
            return True
        else:
            return False

    def fcp_template_sp_mapping_exist_in_db(self, sp_name: str,
                                            fcp_template_id: str):
        with get_fcp_conn() as conn:
            query_mapping = conn.execute("SELECT sp_name "
                                         "FROM template_sp_mapping "
                                         "WHERE sp_name=? and tmpl_id=?",
                                         (sp_name, fcp_template_id))
            mapping = query_mapping.fetchall()

        if mapping:
            return True
        else:
            return False

    @staticmethod
    def bulk_set_sp_default_by_fcp_template(template_id,
                                            sp_name_list):
        """ Set a default FCP template
            for multiple storage providers

            The function only manipulate table(template_fcp_mapping)

            :param template_id: the FCP device template id
            :param sp_name_list: a list of storage provider hostname

            :return NULL
        """
        # Example:
        # if
        #  a.the existing-in-db storage providers for template_id:
        #      ['sp1', 'sp2']
        #  b.the sp_name_list is ['sp3', 'sp4']
        # then
        #  c.remove records of ['sp1', 'sp2'] from db
        #  d.remove records of ['sp3', 'sp4'] if any from db
        #  e.insert ['sp3', 'sp4'] with template_id as default
        with get_fcp_conn() as conn:
            # delete all records related to the template_id
            conn.execute("DELETE FROM template_sp_mapping "
                         "WHERE tmpl_id=?", (template_id,))
            # delete all records related to the
            # storage providers in sp_name_list
            records = ((sp, ) for sp in sp_name_list)
            conn.executemany("DELETE FROM template_sp_mapping "
                             "WHERE sp_name=?", records)
            # insert new record for each
            # storage provider in sp_name_list
            records = ((template_id, sp) for sp in sp_name_list)
            conn.executemany("INSERT INTO template_sp_mapping "
                             "(tmpl_id, sp_name) VALUES (?, ?)",
                             records)

    #########################################################
    #           DML related to multiple tables              #
    #########################################################
    def get_allocated_fcps_from_assigner(self,
                                         assigner_id, fcp_template_id):
        with get_fcp_conn() as conn:
            result = conn.execute(
                "SELECT "
                "fcp.fcp_id, fcp.wwpn_npiv, fcp.wwpn_phy "
                "FROM template_fcp_mapping "
                "INNER JOIN fcp "
                "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                "WHERE template_fcp_mapping.tmpl_id=? "
                "AND fcp.assigner_id=? "
                "AND (fcp.connections<>0 OR fcp.reserved<>0) "
                "AND fcp.tmpl_id=? "
                "ORDER BY template_fcp_mapping.fcp_id ASC",
                (fcp_template_id, assigner_id, fcp_template_id))
            fcp_list = result.fetchall()

        return fcp_list

    def get_reserved_fcps_from_assigner(self, assigner_id, fcp_template_id):
        with get_fcp_conn() as conn:
            result = conn.execute(
                "SELECT fcp.fcp_id, fcp.wwpn_npiv, "
                "fcp.wwpn_phy, fcp.connections "
                "FROM template_fcp_mapping "
                "INNER JOIN fcp "
                "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                "WHERE template_fcp_mapping.tmpl_id=? "
                "AND fcp.assigner_id=? "
                "AND fcp.reserved<>0 "
                "AND fcp.tmpl_id=? "
                "ORDER BY template_fcp_mapping.fcp_id ASC",
                (fcp_template_id, assigner_id, fcp_template_id))
            fcp_list = result.fetchall()

        return fcp_list

    def get_fcp_devices_with_same_index(self, fcp_template_id):
        """ Get a group of available FCPs with the same index,
            which also need satisfy the following conditions:
            a. connections = 0
            b. reserved = 0
            c. state = 'free'

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
            result = conn.execute("SELECT COUNT(path) "
                                  "FROM template_fcp_mapping "
                                  "WHERE tmpl_id=? "
                                  "GROUP BY path "
                                  "ORDER BY path ASC", (fcp_template_id,))
            count_per_path = [a[0] for a in result.fetchall()]
            # case1: return [] if no fcp found in FCP DB
            if not count_per_path:
                LOG.error("Not enough FCPs available, return empty list.")
                return fcp_list
            result = conn.execute(
                "SELECT COUNT(template_fcp_mapping.path) "
                "FROM template_fcp_mapping "
                "INNER JOIN fcp "
                "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                "WHERE template_fcp_mapping.tmpl_id=? "
                "AND fcp.connections=0 "
                "AND fcp.reserved=0 "
                "AND fcp.state='free' "
                "AND fcp.wwpn_npiv IS NOT '' "
                "AND fcp.wwpn_phy IS NOT '' "
                "GROUP BY template_fcp_mapping.path "
                "ORDER BY template_fcp_mapping.path", (fcp_template_id,))
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
            [('1a00', 1, 1, 'active'),
             ('1a01', 0, 0, 'free'),
             ('1a02', 0, 0, 'free'),
             ('1a03', 0, 0, 'free'),
             ('1a04', 0, 0, 'offline'"),
             ...
             ('1b00', 1, 0, 'active'),
             ('1b01', 2, 1, 'active'),
             ('1b02', 0, 0, 'free'),
             ('1b03', 0, 0, 'free'),
             ('1b04', 0, 0, 'free'),
             ...           ]
            '''
            result = conn.execute(
                "SELECT fcp.fcp_id, fcp.connections, "
                "fcp.reserved, fcp.state, fcp.wwpn_npiv, fcp.wwpn_phy "
                "FROM fcp "
                "INNER JOIN template_fcp_mapping "
                "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                "WHERE template_fcp_mapping.tmpl_id=? "
                "ORDER BY template_fcp_mapping.path, "
                "template_fcp_mapping.fcp_id", (fcp_template_id,))
            fcps = result.fetchall()
        '''
        get all free fcps from 1st path
        fcp_pair_map example:
         idx    fcp_pair
         ----------------
        { 1 : [('1a01', 'c05076de330003a3', '', 1)],
          2 : ['1a02'],
          3 : ['1a03']}
        '''
        # The FCP count of 1st path
        for i in range(count_per_path[0]):
            (fcp_no, connections, reserved,
             state, wwpn_npiv, wwpn_phy) = fcps[i]
            if connections == reserved == 0 and state == 'free':
                fcp_pair_map[i] = [(fcp_no, wwpn_npiv, wwpn_phy)]
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
            for i, c in enumerate(count_per_path[:-1]):
                s += c
                # avoid index out of range for per path in fcps[]
                (fcp_no, connections, reserved,
                 state, wwpn_npiv, wwpn_phy) = fcps[s + idx]
                if (idx < count_per_path[i + 1] and
                        connections == reserved == 0 and
                        state == 'free'):
                    fcp_pair_map[idx].append(
                        (fcp_no, wwpn_npiv, wwpn_phy))
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

    def get_fcp_devices(self, fcp_template_id):
        """ Get a group of available FCPs,
            which satisfy the following conditions:
            a. connections = 0
            b. reserved = 0
            c. state = free
        """
        fcp_list = []
        with get_fcp_conn() as conn:
            # Get distinct path list in DB
            result = conn.execute("SELECT DISTINCT path "
                                  "FROM template_fcp_mapping "
                                  "WHERE tmpl_id=?", (fcp_template_id,))
            path_list = result.fetchall()
            # Get fcp_list of every path
            for no in path_list:
                result = conn.execute(
                    "SELECT fcp.fcp_id, fcp.wwpn_npiv, fcp.wwpn_phy "
                    "FROM template_fcp_mapping "
                    "INNER JOIN fcp "
                    "ON template_fcp_mapping.fcp_id=fcp.fcp_id "
                    "WHERE template_fcp_mapping.tmpl_id=? "
                    "AND fcp.connections=0 "
                    "AND fcp.reserved=0 "
                    "AND fcp.state='free' "
                    "AND template_fcp_mapping.path=? "
                    "AND fcp.wwpn_npiv IS NOT '' "
                    "AND fcp.wwpn_phy IS NOT '' "
                    "ORDER BY template_fcp_mapping.path",
                    (fcp_template_id, no[0]))
                fcps = result.fetchall()
                if not fcps:
                    # continue to find whether
                    # other paths has available FCP
                    continue
                index = random.randint(0, len(fcps) - 1)
                fcp_list.append(fcps[index])
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

    def create_fcp_template(self, fcp_template_id, name, description,
                            fcp_devices_by_path, host_default,
                            default_sp_list):
        """ Insert records of new fcp template in fcp DB

        :param fcp_template_id: fcp template id
        :param name: fcp template name
        :param description: description
        :param fcp_devices_by_path:
            Example:
            if fcp_list is "0011-0013;0015;0017-0018",
            then fcp_devices_by_path should be passed like:
            {
              0: {'0011' ,'0012', '0013'}
              1: {'0015'}
              2: {'0017', '0018'}
            }
        :param host_default: (bool)
        :param default_sp_list: (list)
        :return: NULL
        """
        # first check the template exist or not
        # if already exist, raise exception
        if self.fcp_template_exist_in_db(fcp_template_id):
            raise exception.SDKObjectAlreadyExistError(
                    obj_desc=("FCP template '%s' already "
                              "exist" % fcp_template_id),
                    modID=self._module_id)
        # then check the SP records exist in template_sp_mapping or not
        # if already exist, will update the tmpl_id
        # if not exist, will insert new records
        sp_mapping_to_add = list()
        sp_mapping_to_update = list()
        for sp_name in default_sp_list:
            record = (fcp_template_id, sp_name)
            if self.sp_name_exist_in_db(sp_name):
                sp_mapping_to_update.append(record)
            else:
                sp_mapping_to_add.append(record)
        # Prepare records include (fcp_id, tmpl_id, path)
        # to be inserted into table template_fcp_mapping
        fcp_mapping = list()
        for path in fcp_devices_by_path:
            for fcp_id in fcp_devices_by_path[path]:
                new_record = [fcp_id, fcp_template_id, path]
                fcp_mapping.append(new_record)
        with get_fcp_conn() as conn:
            # 1. change the is_default of existing templates to False,
            #    if the is_default of the being-created template is True,
            #    because only one default template per host is allowed
            if host_default is True:
                conn.execute("UPDATE template SET is_default=?", (False,))
            # 2. insert a new record in template table
            tmpl_basics = (fcp_template_id, name, description, host_default)
            conn.execute("INSERT INTO template (id, name, description, "
                         "is_default) VALUES (?, ?, ?, ?)", tmpl_basics)
            # 3. insert new records in template_fcp_mapping
            conn.executemany("INSERT INTO template_fcp_mapping (fcp_id, "
                             "tmpl_id, path) VALUES (?, ?, ?)", fcp_mapping)
            # 4. insert a new record in template_sp_mapping
            if default_sp_list:
                if sp_mapping_to_add:
                    conn.executemany("INSERT INTO template_sp_mapping "
                                     "(tmpl_id, sp_name) VALUES "
                                     "(?, ?)", sp_mapping_to_add)
                if sp_mapping_to_update:
                    conn.executemany("UPDATE template_sp_mapping SET "
                                     "tmpl_id=? WHERE sp_name=?",
                                     sp_mapping_to_update)

    def edit_fcp_template(self, fcp_template_id, name=None, description=None,
                          fcp_devices=None, host_default=None,
                          default_sp_list=None):
        """ Edit a FCP device template

        The kwargs values are pre-validated in two places:
          validate kwargs types
            in zvmsdk/sdkwsgi/schemas/volume.py
          set a kwarg as None if not passed by user
            in zvmsdk/sdkwsgi/handlers/volume.py

        If any kwarg is None, the kwarg will not be updated.

        :param fcp_template_id: template id
        :param name:            template name
        :param description:     template desc
        :param fcp_devices:     FCP devices divided into
                                different paths by semicolon
          Format:
            "fcp-devices-from-path0;fcp-devices-from-path1;..."
          Example:
            "0011-0013;0015;0017-0018",
        :param host_default: (bool)
        :param default_sp_list: (list)
          Example:
            ["SP1", "SP2"]
        :return:
          Example
            {
              'fcp_template': {
                'name': 'bjcb-test-template',
                'id': '36439338-db14-11ec-bb41-0201018b1dd2',
                'description': 'This is Default template',
                'is_default': True,
                'sp_name': ['sp4', 'v7k60']
              }
            }
        """
        with get_fcp_conn():
            # The following multiple DQLs(Database query)
            # are put into the with-block with DMLs
            # because the consequent DMLs(Database modification)
            # depend on the result of the DQLs.
            # So that, other threads can NOT begin a sqlite transacation
            # util current thread exits the with-block.
            # Refer to 'def get_fcp_conn' for thread lock

            # DQL: validate: FCP device template
            if not self.fcp_template_exist_in_db(fcp_template_id):
                obj_desc = ("FCP device template {}".format(fcp_template_id))
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc)

            # DQL: validate: add or delete path from FCP template.
            # If fcp_devices is None, it means user do not want to
            # modify fcp_devices, so skip the validation;
            # otherwise, perform the validation.
            if fcp_devices is not None:
                fcp_path_count_from_input = len(
                    [i for i in fcp_devices.split(';') if i])
                fcp_path_count_in_db = self.get_path_count(fcp_template_id)
                if fcp_path_count_from_input != fcp_path_count_in_db:
                    inuse_fcp = self.get_inuse_fcp_device_by_fcp_template(
                        fcp_template_id)
                    if inuse_fcp:
                        inuse_fcp = utils.shrink_fcp_list(
                            [fcp['fcp_id'] for fcp in inuse_fcp])
                        detail = ("Adding or deleting path from a FCP "
                                  "device template is not allowed if "
                                  "there is any FCP device allocated "
                                  "from the template. The FCP devices "
                                  "({}) are allocated from template {}."
                                  .format(inuse_fcp, fcp_template_id))
                        raise exception.ValidationError(detail=detail)

            tmpl_basic, fcp_detail = self.get_fcp_templates_details(
                [fcp_template_id])

            # DML: table template_fcp_mapping
            if fcp_devices is not None:
                # fcp_from_input:
                # fcp devices from user input
                # example:
                # {'0011': 0, '0013': 0,  <<< path 0
                #  '0015': 1,             <<< path 1
                #  '0018': 2, '0017': 2}  <<< path 2
                fcp_from_input = dict()
                # fcp_devices_by_path:
                # example:
                # if fcp_devices is "0011-0013;0015;0017-0018",
                # then fcp_devices_by_path is :
                # {
                #   0: {'0011', '0013'}
                #   1: {'0015'}
                #   2: {'0017', '0018'}
                # }
                fcp_devices_by_path = utils.expand_fcp_list(fcp_devices)
                for path in fcp_devices_by_path:
                    for fcp_id in fcp_devices_by_path[path]:
                        fcp_from_input[fcp_id] = path
                # fcp_in_db:
                # FCP devices belonging to fcp_template_id
                # queried from database including the FCP devices
                # that are not found in z/VM
                # example:
                # {'0011': <sqlite3.Row object at 0x3ff85>,
                #  '0013': <sqlite3.Row object at 0x3f3da>}
                fcp_in_db = dict()
                for row in fcp_detail:
                    fcp_in_db[row['fcp_id']] = row
                # Divide the FCP devices into three sets
                add_set = set(fcp_from_input) - set(fcp_in_db)
                inter_set = set(fcp_from_input) & set(fcp_in_db)
                del_set = set(fcp_in_db) - set(fcp_from_input)
                # only unused FCP devices can be
                # deleted from a FCP device template.
                # Note:
                #  connections == None:
                #   the fcp only exists in table(template_fcp_mapping),
                #   rather than table(fcp)
                #  connections == 0:
                #   the fcp exists in both tables
                #   and it is not allocated from FCP DB
                not_allow_for_del = set()
                for fcp in del_set:
                    if (fcp_in_db[fcp]['connections'] not in (None, 0) or
                            fcp_in_db[fcp]['reserved'] not in (None, 0)):
                        not_allow_for_del.add(fcp)
                # validate: not allowed to remove inuse FCP devices
                if not_allow_for_del:
                    not_allow_for_del = utils.shrink_fcp_list(
                        list(not_allow_for_del))
                    detail = ("The FCP devices ({}) are missing "
                              "from the input. These FCP devices "
                              "are allocated to virtual machines, "
                              "ensure they are included in the "
                              "FCP device list."
                              .format(not_allow_for_del))
                    raise exception.ValidationError(detail=detail)

                # DML: table template_fcp_mapping
                LOG.info("DML: table template_fcp_mapping")
                # 1. delete from table template_fcp_mapping
                records_to_delete = [
                    (fcp_template_id, fcp_id)
                    for fcp_id in del_set]
                self.bulk_delete_fcp_device_from_fcp_template(
                    records_to_delete)
                LOG.info("FCP devices ({}) removed from FCP template {}."
                         .format(utils.shrink_fcp_list(list(del_set)),
                                 fcp_template_id))
                # 2. insert into table template_fcp_mapping
                records_to_insert = [
                    (fcp_template_id, fcp_id, fcp_from_input[fcp_id])
                    for fcp_id in add_set]
                self.bulk_insert_fcp_device_into_fcp_template(
                    records_to_insert)
                LOG.info("FCP devices ({}) added into FCP template {}."
                         .format(utils.shrink_fcp_list(list(add_set)),
                                 fcp_template_id))
                # 3. update table template_fcp_mapping
                #    update path of fcp devices if changed
                for fcp in inter_set:
                    path_from_input = fcp_from_input[fcp]
                    path_in_db = fcp_in_db[fcp]['path']
                    if path_from_input != path_in_db:
                        record_to_update = (
                            fcp_from_input[fcp], fcp, fcp_template_id)
                        self.update_path_of_fcp_device(record_to_update)
                        LOG.info("FCP device ({}) updated into "
                                 "FCP template {} from path {} to path {}."
                                 .format(fcp, fcp_template_id,
                                         fcp_in_db[fcp]['path'],
                                         fcp_from_input[fcp]))

            # DML: table template
            if (name, description, host_default) != (None, None, None):
                LOG.info("DML: table template")
                record_to_update = (
                    name if name is not None
                    else tmpl_basic[0]['name'],
                    description if description is not None
                    else tmpl_basic[0]['description'],
                    host_default if host_default is not None
                    else tmpl_basic[0]['is_default'],
                    fcp_template_id)
                self.update_basic_info_of_fcp_template(record_to_update)
                LOG.info("FCP template basic info updated.")

            # DML: table template_sp_mapping
            if default_sp_list is not None:
                LOG.info("DML: table template_sp_mapping")
                self.bulk_set_sp_default_by_fcp_template(fcp_template_id,
                                                         default_sp_list)
                LOG.info("Default template of storage providers ({}) "
                         "updated.".format(default_sp_list))

            # Return template basic info queried from DB
            # tmpl_basic is a list containing one or more sqlite.Row objects
            # Example:
            #  if a template is the SP-level default for 2 SPs (SP1 and SP2)
            #  (i.e. the template has 2 entries in table template_sp_mapping
            #  then tmpl_basic is a list containing 2 Row objects,
            #  the only different value between the 2 Row objects is 'sp_name'
            #  (i.e. tmpl_basic[0]['sp_name'] is 'SP1',
            #  while tmpl_basic[1]['sp_name'] is 'SP2'.
            tmpl_basic = self.get_fcp_templates_details([fcp_template_id])[0]
            return {'fcp_template': {
                'name': tmpl_basic[0]['name'],
                'id': tmpl_basic[0]['id'],
                'description': tmpl_basic[0]['description'],
                'is_default': bool(tmpl_basic[0]['is_default']),
                'sp_name':
                    [] if tmpl_basic[0]['sp_name'] is None
                    else [r['sp_name'] for r in tmpl_basic]}}

    def get_fcp_templates(self, template_id_list=None):
        """Get fcp templates base info by template_id_list.
        If template_id_list is None, will get all the fcp templates in db.

        return format:
        [(id|name|description|is_default|sp_name)]
        """
        cmd = ("SELECT template.id, template.name, template.description, "
               "template.is_default, template_sp_mapping.sp_name "
               "FROM template "
               "LEFT OUTER JOIN template_sp_mapping "
               "ON template.id=template_sp_mapping.tmpl_id")

        with get_fcp_conn() as conn:
            if template_id_list:
                result = conn.execute(
                    cmd + " WHERE template.id "
                    "IN (%s)" %
                    ','.join('?' * len(template_id_list)),
                    template_id_list)
            else:
                result = conn.execute(cmd)

            raw = result.fetchall()
        return raw

    def get_host_default_fcp_template(self):
        """Get the host default fcp template base info.
        return format: (id|name|description|is_default|sp_name)

        when the  template is more than one SP's default,
        then it will show up several times in the result.
        """
        with get_fcp_conn() as conn:
            result = conn.execute(
                "SELECT t.id, t.name, t.description, t.is_default, "
                "ts.sp_name "
                "FROM template AS t "
                "LEFT OUTER JOIN template_sp_mapping AS ts "
                "ON t.id=ts.tmpl_id "
                "WHERE t.is_default=1")
            raw = result.fetchall()
        return raw

    def get_sp_default_fcp_template(self, sp_host_list):
        """Get the sp_host_list default fcp template.
        """
        cmd = ("SELECT t.id, t.name, t.description, t.is_default, "
               "ts.sp_name "
               "FROM template_sp_mapping AS ts "
               "INNER JOIN template AS t "
               "ON ts.tmpl_id=t.id")
        raw = []
        with get_fcp_conn() as conn:
            if (len(sp_host_list) == 1 and
                    sp_host_list[0].lower() == 'all'):
                result = conn.execute(cmd)
                raw = result.fetchall()
            else:
                for sp_host in sp_host_list:
                    result = conn.execute(
                        cmd + " WHERE ts.sp_name=?", (sp_host,))
                    raw.extend(result.fetchall())
        return raw

    def get_fcp_template_by_assigner_id(self, assigner_id):
        """Get a templates list of specified assigner.
        """
        with get_fcp_conn() as conn:
            result = conn.execute(
                "SELECT t.id, t.name, t.description, t.is_default, "
                "ts.sp_name "
                "FROM fcp "
                "INNER JOIN template AS t "
                "ON fcp.tmpl_id=t.id "
                "LEFT OUTER JOIN template_sp_mapping AS ts "
                "ON fcp.tmpl_id=ts.tmpl_id "
                "WHERE fcp.assigner_id=?", (assigner_id,))
            raw = result.fetchall()
            # id|name|description|is_default|sp_name
        return raw

    def get_fcp_templates_details(self, template_id_list=None):
        """Get templates detail info by template_id_list

        :param template_id_list: must be a list or None

        If template_id_list=None, will get all the templates detail info.

        Detail info including two parts: base info and fcp device info, these
        two parts info will use two cmds to get from db and return out, outer
        method will join these two return output.

        'tmpl_cmd' is used to get base info from template table and
        template_sp_mapping table.

        tmpl_cmd result format:
        id|name|description|is_default|sp_name

        'devices_cmd' is used to get fcp device info. Device's template id is
        gotten from template_fcp_mapping table, device's usage info is gotten
        from fcp table. Because not all the templates' fcp device is in fcp
        table, so the fcp device's template id should being gotten from
        template_fcp_mapping table insteading of fcp table.

        'devices_cmd' result format:
        fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id

        In 'devices_cmd' result: the first three properties are from
        template_fcp_mapping table, and the others are from fcp table.
        when the device is not in fcp table, all the properties in fcp
        table will be None. For example: template '12345678' has a fcp
        "1aaa" on path 0, but this device is not in fcp table, the
        query result will be as below.

        1aaa|12345678|0|||||||||
        """
        tmpl_cmd = (
            "SELECT t.id, t.name, t.description, "
            "t.is_default, ts.sp_name "
            "FROM template AS t "
            "LEFT OUTER JOIN template_sp_mapping AS ts "
            "ON t.id=ts.tmpl_id")

        devices_cmd = (
            "SELECT tf.fcp_id, tf.tmpl_id, tf.path, fcp.assigner_id, "
            "fcp.connections, fcp.reserved, fcp.wwpn_npiv, fcp.wwpn_phy, "
            "fcp.chpid, fcp.state, fcp.owner, fcp.tmpl_id "
            "FROM template_fcp_mapping AS tf "
            "LEFT OUTER JOIN fcp "
            "ON tf.fcp_id=fcp.fcp_id")

        with get_fcp_conn() as conn:
            if template_id_list:
                tmpl_result = conn.execute(
                    tmpl_cmd + " WHERE t.id IN (%s)" %
                    ','.join('?' * len(template_id_list)),
                    template_id_list)

                devices_result = conn.execute(
                    devices_cmd + " WHERE tf.tmpl_id "
                    "IN (%s)" %
                    ','.join('?' * len(template_id_list)),
                    template_id_list)
            else:
                tmpl_result = conn.execute(tmpl_cmd)
                devices_result = conn.execute(devices_cmd)

            tmpl_result = tmpl_result.fetchall()
            devices_result = devices_result.fetchall()

        return tmpl_result, devices_result

    def bulk_delete_fcp_from_template(self, fcp_id_list, fcp_template_id):
        """Delete multiple FCP records from the table template_fcp_mapping in the
        specified fcp template only if the FCP devices are available."""
        records_to_delete = [(fcp_template_id, fcp_id)
                             for fcp_id in fcp_id_list]
        with get_fcp_conn() as conn:
            conn.executemany(
                "DELETE FROM template_fcp_mapping "
                "WHERE fcp_id NOT IN ("
                "SELECT fcp_id FROM fcp "
                "WHERE fcp.connections<>0 OR fcp.reserved<>0) "
                "AND tmpl_id=? AND fcp_id=?",
                records_to_delete)

    def delete_fcp_template(self, template_id):
        """Remove fcp template record from template, template_sp_mapping,
        template_fcp_mapping and fcp tables."""
        with get_fcp_conn() as conn:
            if self.fcp_template_allocated_in_db(template_id):
                errmsg = ("The FCP device template has FCP devices allocated, "
                          "hence the template is not allowed for deletion.")
                LOG.error(errmsg)
                raise exception.SDKBaseException(msg=errmsg)
            conn.execute("DELETE FROM template WHERE id=?",
                         (template_id,))
            conn.execute("DELETE FROM template_sp_mapping WHERE tmpl_id=?",
                         (template_id,))
            conn.execute("DELETE FROM template_fcp_mapping WHERE tmpl_id=?",
                         (template_id,))
            LOG.debug("Template record %s is removed from "
                      "template, template_sp_mapping and "
                      "template_fcp_mapping tables" % template_id)


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
