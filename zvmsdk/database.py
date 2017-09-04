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


import contextlib
from datetime import datetime
import os
import six
import sqlite3
import stat
from time import sleep
import uuid

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG

_DB_OPERATOR = None


def get_DbOperator():
    global _DB_OPERATOR

    if _DB_OPERATOR is not None:
        return _DB_OPERATOR

    _DB_OPERATOR = DbOperator()
    return _DB_OPERATOR


@contextlib.contextmanager
def get_db_conn():
    """Get a database connection object to execute some SQL statements
    and release the connection object finally.
    """
    _op = get_DbOperator()
    (i, conn) = _op.get_connection()
    try:
        yield conn
    except Exception as err:
        LOG.error("Execute SQL statements error: %s", six.text_type(err))
        raise exception.DatabaseException(msg=err)
    finally:
        _op.release_connection(i)


class DbOperator(object):

    def __init__(self):
        # make pool size as a config item if necessary
        self._pool_size = 3
        self._conn_pool = {}
        self._free_conn = {}
        self._prepare()

    def _prepare(self):
        path_mode = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO
        file_mode = (stat.S_IRUSR + stat.S_IWUSR + stat.S_IRGRP +
                     stat.S_IWGRP + stat.S_IROTH + stat.S_IWOTH)

        if not os.path.exists(CONF.database.path):
            os.makedirs(CONF.database.path, path_mode)
        else:
            mode = oct(os.stat(CONF.database.path).st_mode)[-3:]
            if mode != '777':
                os.chmod(CONF.database.path, path_mode)

        # Initialize a very first connection to activate the database and
        # check for its modes
        database = ''.join((CONF.database.path, "/", const.DATABASE_NAME))
        conn = sqlite3.connect(database, check_same_thread=False)

        db_mode = os.stat(database).st_mode

        mu = (db_mode & stat.S_IRWXU) >> 6
        mg = (db_mode & stat.S_IRWXG) >> 3
        mo = db_mode & stat.S_IRWXO

        if ((mu < 6) or (mg < 6) or (mo < 6)):
            os.chmod(database, file_mode)
        conn.isolation_level = None
        self._conn_pool[0] = conn
        self._free_conn[0] = True

        # Create other connections of the pool
        for i in range(1, self._pool_size):
            conn = sqlite3.connect(database)
            # autocommit
            conn.isolation_level = None
            self._conn_pool[i] = conn
            self._free_conn[i] = True

    def get_connection(self):
        timeout = 5
        for _ in range(timeout):
            for i in range(self._pool_size):
                # Not really thread safe, fix if necessary
                if self._free_conn[i]:
                    self._free_conn[i] = False
                    return i, self._conn_pool[i]
            sleep(1)
        # If timeout happens, it means the pool is too small to meet
        # request performance, so enlarge it
        raise exception.DBTimeout("Get database connection time out!")

    def release_connection(self, i):
        self._free_conn[i] = True


class NetworkDbOperator(object):

    def __init__(self):
        self._create_switch_table()

    def _create_switch_table(self):
        create_table_sql = ' '.join((
                'create table if not exists switch (',
                'node varchar(8),',
                'interface varchar(4),',
                'switch varchar(8),',
                'port varchar(128),',
                'comments varchar(128),',
                'primary key (node, interface));'))
        with get_db_conn() as conn:
            conn.execute(create_table_sql)

    def switch_delete_record_for_node(self, node):
        """Remove node switch record from switch table."""
        with get_db_conn() as conn:
            conn.execute("DELETE FROM switch WHERE node=?", (node,))

    def switch_delete_record_for_nic(self, node, interface):
        """Remove node switch record from switch table."""
        with get_db_conn() as conn:
            conn.execute("DELETE FROM switch WHERE node=? and interface=?",
                         (node, interface))

    def switch_add_record_for_nic(self, node, interface, port=None):
        """Add node name and nic name address into switch table."""
        if port is not None:
            with get_db_conn() as conn:
                conn.execute("INSERT INTO switch (node, interface, port) "
                             "VALUES (?, ?, ?)",
                             (node, interface, port))
        else:
            with get_db_conn() as conn:
                conn.execute("INSERT INTO switch (node, interface) "
                             "VALUES (?, ?)",
                             (node, interface))

    def switch_updat_record_with_switch(self, node, interface, switch=None):
        """Update information in switch table."""
        if switch is not None:
            with get_db_conn() as conn:
                conn.execute("UPDATE switch SET switch=? "
                             "WHERE node=? and interface=?",
                             (switch, node, interface))
        else:
            with get_db_conn() as conn:
                conn.execute("UPDATE switch SET switch=NULL "
                             "WHERE node=? and interface=?",
                             (node, interface))

    def switch_select_table(self):
        with get_db_conn() as conn:
            result = conn.execute("SELECT * FROM switch")
            nic_settings = result.fetchall()
        return nic_settings

    def switch_select_record_for_node(self, node):
        with get_db_conn() as conn:
            result = conn.execute("SELECT interface, switch FROM switch "
                                  "WHERE node=?", (node,))
            switch_info = result.fetchall()
        return switch_info


class VolumeDBUtils(object):

    def __init__(self):
        self._initialize_table_volumes()
        self._initialize_table_volume_attachments()
        self._VOLUME_STATUS_FREE = 'free'
        self._VOLUME_STATUS_IN_USE = 'in-use'

    def _initialize_table_volumes(self):
        # The snapshots table doesn't exist by now, but it must be there when
        # we decide to support copy volumes. So leave 'snapshot-id' there as a
        # placeholder, since it's hard to migrate a database table in future.
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS volumes(',
            'id             char(36)      PRIMARY KEY,',
            'protocol_type  varchar(32)   NOT NULL,',
            'size           varchar(8)    NOT NULL,',
            'status         varchar(32),',
            'image_id       char(36),',
            'snapshot_id    char(36),',
            'deleted        smallint      DEFAULT 0,',
            'deleted_at     char(26),',
            'comment        varchar(128))'))
        with get_db_conn() as conn:
            conn.execute(sql)

    def _initialize_table_volume_attachments(self):
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS volume_attachments(',
            'id               char(36)      PRIMARY KEY,',
            'volume_id        char(36)      NOT NULL,',
            'instance_id      char(36)      NOT NULL,',
            'connection_info  varchar(256)  NOT NULL,',
            'mountpoint       varchar(32)   NOT NULL,',
            'deleted          smallint      DEFAULT 0,',
            'deleted_at       char(26),',
            'comment          varchar(128))'))
        with get_db_conn() as conn:
            conn.execute(sql)

    def get_volume_by_id(self, volume_id):
        """Query a volume form database by its id.
        The id must be a 36-character string.
        """
        if not volume_id:
            msg = "Volume id must be specified!"
            raise exception.DatabaseException(msg=msg)

        with get_db_conn() as conn:
            result_list = conn.execute(
                "SELECT * FROM volumes WHERE id=:id AND deleted=0",
                {'id': volume_id}
                ).fetchall()

        if len(result_list) == 1:
            return result_list[0]
        elif len(result_list) == 0:
            LOG.debug("Volume with id: %s not found!" % volume_id)
            return None

    def insert_volume(self, volume):
        """Insert a volume into database.
        The volume is represented by a dict of all volume properties:
        id: volume id, auto generated and can not be specified.
        protocol_type: protocol type to access the volume, like 'fc' or
                      'iscsi', must be specified.
        size: volume size in Terabytes, Gigabytes or Megabytes, must be
              specified.
        status: volume status, auto generated and can not be specified.
        image_id: source image id when boot-from-volume, optional.
        snapshot_id: snapshot id when a volume comes from a snapshot, optional.
        deleted: if deleted, auto generated and can not be specified.
        deleted_at: auto generated and can not be specified.
        comment: any comment, optional.
        """
        if not (isinstance(volume, dict) and
                'protocol_type' in volume.keys() and
                'size' in volume.keys()):
            msg = "Invalid volume database entry %s !" % volume
            raise exception.DatabaseException(msg=msg)

        volume_id = str(uuid.uuid4())
        protocol_type = volume['protocol_type']
        size = volume['size']
        status = self._VOLUME_STATUS_FREE
        image_id = None
        if 'image_id' in volume.keys():
            image_id = volume['image_id']
        snapshot_id = None
        if 'snapshot_id' in volume.keys():
            snapshot_id = volume['snapshot_id']
        deleted = '0'
        deleted_at = None
        comment = None
        if 'comment' in volume.keys():
            comment = volume['comment']

        with get_db_conn() as conn:
            conn.execute(
                "INSERT INTO volumes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (volume_id, protocol_type, size, status, image_id, snapshot_id,
                 deleted, deleted_at, comment))

        return volume_id

    def update_volume(self, volume):
        """Update a volume in database.
        The volume is represented by a dict of all volume properties:
        id: volume id, must be specified.
        protocol_type: protocol type to access the volume, like 'fc' or
                      'iscsi', can not update, don't set.
        size: volume size in Terabytes, Gigabytes or Megabytes, optional.
        status: volume status, optional.
        image_id: source image id when boot-from-volume, optional.
        snapshot_id: snapshot id when a volume comes from a snapshot, optional.
        deleted: if deleted, can not be updated, use delete_volume() to delete.
        deleted_at: auto generated and can not be specified.
        comment: any comment, optional.
        """
        if not (isinstance(volume, dict) and
                'id' in volume.keys()):
            msg = "Invalid volume database entry %s !" % volume
            raise exception.DatabaseException(msg=msg)

        # get current volume properties
        volume_id = volume['id']
        old_volume = self.get_volume_by_id(volume_id)
        if not old_volume:
            msg = "Volume %s not found in database!" % volume_id
            raise exception.DatabaseException(msg=msg)
        else:
            (_, _, size, status, image_id, snapshot_id, _, _, comment
             ) = old_volume

        if 'size' in volume.keys():
            size = volume['size']
        if 'status' in volume.keys():
            status = volume['status']
        if 'image_id' in volume.keys():
            image_id = volume['image_id']
        if 'snapshot_id' in volume.keys():
            snapshot_id = volume['snapshot_id']
        if 'comment' in volume.keys():
            comment = volume['comment']

        with get_db_conn() as conn:
            conn.execute(' '.join((
                "UPDATE volumes",
                "SET size=?, status=?, image_id=?, snapshot_id=?, comment=?"
                "WHERE id=?")),
                (size, status, image_id, snapshot_id, comment, volume_id))

    def delete_volume(self, volume_id):
        """Delete a volume from database."""
        if not volume_id:
            msg = "Volume id must be specified!"
            raise exception.DatabaseException(msg=msg)

        volume = self.get_volume_by_id(volume_id)
        if not volume:
            msg = "Volume %s not found in database!" % volume_id
            raise exception.DatabaseException(msg=msg)

        time = str(datetime.now())
        with get_db_conn() as conn:
            conn.execute(' '.join((
                "UPDATE volumes",
                "SET deleted=1, deleted_at=?",
                "WHERE id=?")),
                (time, volume_id))


class GuestDbOperator(object):

    def __init__(self):
        self._create_guests_table()

    def _create_guests_table(self):
        """"""
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS guests(',
            'id             char(36)      PRIMARY KEY,',
            'userid         varchar(8)    NOT NULL UNIQUE,',
            'metadata       varchar(255),',
            'comments       text)'))
        with get_db_conn() as conn:
            conn.execute(sql)

    def add_guest(self, userid, meta='', comments=''):
        # Generate uuid automatically
        id = str(uuid.uuid4())
        with get_db_conn() as conn:
            conn.execute(
                "INSERT INTO guests VALUES (?, ?, ?, ?)",
                (id, userid, meta, comments))

    def delete_guest_by_id(self, id):
        with get_db_conn() as conn:
            conn.execute(
                "DELETE FROM guests WHERE id=?", (id,))

    def delete_guest_by_userid(self, userid):
        with get_db_conn() as conn:
            conn.execute(
                "DELETE FROM guests WHERE userid=?", (userid,))

    def update_guest_by_id(self, uuid, userid=None, meta=None, comments=None):
        if (userid is None) and (meta is None) and (comments is None):
            msg = ("Update guest with id: %s failed, no field "
                   "specified to be updated." % uuid)
            LOG.error(msg)
            raise exception.DatabaseException(msg=msg)

        sql_cmd = "UPDATE guests SET"
        sql_var = []
        if userid is not None:
            sql_cmd += " userid=?,"
            sql_var.append(userid)
        if meta is not None:
            sql_cmd += " metadata=?,"
            sql_var.append(meta)
        if comments is not None:
            sql_cmd += " comments=?,"
            sql_var.append(comments)

        # remove the tailing comma
        sql_cmd = sql_cmd.strip(',')
        # Add the id filter
        sql_cmd += " WHERE id=?"
        sql_var.append(uuid)

        with get_db_conn() as conn:
            conn.execute(sql_cmd, sql_var)

    def update_guest_by_userid(self, userid, meta=None, comments=None):
        if (meta is None) and (comments is None):
            msg = ("Update guest with userid: %s failed, no field "
                   "specified to be updated." % userid)
            LOG.error(msg)
            raise exception.DatabaseException(msg=msg)

        sql_cmd = "UPDATE guests SET"
        sql_var = []
        if meta is not None:
            sql_cmd += " metadata=?,"
            sql_var.append(meta)
        if comments is not None:
            sql_cmd += " comments=?,"
            sql_var.append(comments)

        # remove the tailing comma
        sql_cmd = sql_cmd.strip(',')
        # Add the id filter
        sql_cmd += " WHERE userid=?"
        sql_var.append(userid)

        with get_db_conn() as conn:
            conn.execute(sql_cmd, sql_var)

    def get_guest_list(self):
        with get_db_conn() as conn:
            res = conn.execute("SELECT * FROM guests")
            guests = res.fetchall()
        return guests

    def get_guest_by_id(self, id):
        with get_db_conn() as conn:
            res = conn.execute("SELECT * FROM guests "
                               "WHERE id=?", (id,))
            guest = res.fetchall()
        # As id is the primary key, the filtered entry number should be 0 or 1
        if len(guest) == 1:
            return guest[0]
        elif len(guest) == 0:
            LOG.debug("Guest with id: %s not found from DB!" % id)
            return None
        # Code shouldn't come here, just in case
        return None

    def get_guest_by_userid(self, userid):
        with get_db_conn() as conn:
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
