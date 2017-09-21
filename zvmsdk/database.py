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


from datetime import datetime
import contextlib
import os
import six
import sqlite3
import threading
import uuid

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


_DIR_MODE = 0755
_VOLUME_CONN = None
_NETWORK_CONN = None
_IMAGE_CONN = None
_GUEST_CONN = None
_DBLOCK_VOLUME = threading.RLock()
_DBLOCK_NETWORK = threading.RLock()
_DBLOCK_IMAGE = threading.RLock()
_DBLOCK_GUEST = threading.RLock()


@contextlib.contextmanager
def get_volume_conn():
    global _VOLUME_CONN, _DBLOCK_VOLUME
    if not _VOLUME_CONN:
        _VOLUME_CONN = _init_db_conn(const.DATABASE_VOLUME)

    _DBLOCK_VOLUME.acquire()
    try:
        yield _VOLUME_CONN
    except Exception as err:
        LOG.error("Execute SQL statements error: %s", six.text_type(err))
        raise exception.SDKDatabaseException(msg=err)
    finally:
        _DBLOCK_VOLUME.release()


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
                'userid       varchar(8),',
                'interface    varchar(4),',
                'switch       varchar(8),',
                'port         varchar(128),',
                'comments     varchar(128),',
                'primary key (userid, interface));'))
        with get_network_conn() as conn:
            conn.execute(create_table_sql)

    def _get_switch_by_user_interface(self, userid, interface):
        with get_network_conn() as conn:
            res = conn.execute("SELECT * FROM switch "
                               "WHERE userid=? and interface=?",
                               (userid.upper(), interface))
            switch_record = res.fetchall()

        if len(switch_record) == 1:
            return switch_record[0]
        elif len(switch_record) == 0:
            return None

    def switch_delete_record_for_userid(self, userid):
        """Remove userid switch record from switch table."""
        with get_network_conn() as conn:
            conn.execute("DELETE FROM switch WHERE userid=?",
                         (userid.upper(),))
            LOG.debug("Switch record for user %s is removed from "
                      "switch table" % userid.upper())

    def switch_delete_record_for_nic(self, userid, interface):
        """Remove userid switch record from switch table."""
        with get_network_conn() as conn:
            conn.execute("DELETE FROM switch WHERE userid=? and interface=?",
                         (userid.upper(), interface))
            LOG.debug("Switch record for user %s with nic %s is removed from "
                      "switch table" % (userid.upper(), interface))

    def switch_add_record(self, userid, interface, port=None,
                          switch=None, comments=None):
        """Add userid and nic name address into switch table."""
        with get_network_conn() as conn:
            conn.execute("INSERT INTO switch VALUES (?, ?, ?, ?, ?)",
                         (userid.upper(), interface, switch, port, comments))
            LOG.debug("New record in the switch table: user %s, "
                      "nic %s, port %s" %
                      (userid.upper(), interface, port))

    def switch_update_record_with_switch(self, userid, interface,
                                         switch=None):
        """Update information in switch table."""
        if not self._get_switch_by_user_interface(userid, interface):
            msg = "User %s with nic %s does not exist in DB" % (userid.upper(),
                                                                interface)
            LOG.error(msg)
            obj_desc = ('User %s with nic %s' % (userid.upper(), interface))
            raise exception.SDKObjectNotExistError(obj_desc,
                                                   modID=self._module_id)

        if switch is not None:
            with get_network_conn() as conn:
                conn.execute("UPDATE switch SET switch=? "
                             "WHERE userid=? and interface=?",
                             (switch, userid.upper(), interface))
                LOG.debug("Set switch to %s for user %s with nic %s "
                          "in switch table" %
                          (switch, userid.upper(), interface))
        else:
            with get_network_conn() as conn:
                conn.execute("UPDATE switch SET switch=NULL "
                             "WHERE userid=? and interface=?",
                             (userid.upper(), interface))
                LOG.debug("Set switch to None for user %s with nic %s "
                          "in switch table" %
                          (userid.upper(), interface))

    def switch_select_table(self):
        with get_network_conn() as conn:
            result = conn.execute("SELECT * FROM switch")
            nic_settings = result.fetchall()
        return nic_settings

    def switch_select_record_for_userid(self, userid):
        with get_network_conn() as conn:
            result = conn.execute("SELECT * FROM switch "
                                  "WHERE userid=?", (userid.upper(),))
            switch_info = result.fetchall()
        return switch_info

    def switch_select_record(self, userid=None, nic_id=None, vswitch=None):
        if ((userid is None) and
            (nic_id is None) and
            (vswitch is None)):
            return self.switch_select_table()

        sql_cmd = "SELECT * FROM switch WHERE"
        sql_var = []
        if userid is not None:
            sql_cmd += " userid=? and"
            sql_var.append(userid.upper())
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
            return result.fetchall()


class VolumeDbOperator(object):

    def __init__(self):
        self._initialize_table_volumes()
        self._initialize_table_volume_attachments()
        self._VOLUME_STATUS_FREE = 'free'
        self._VOLUME_STATUS_IN_USE = 'in-use'
        self._mod_id = "volume"

    def _initialize_table_volumes(self):
        # The snapshots table doesn't exist by now, but it must be there when
        # we decide to support copy volumes. So leave 'snapshot-id' there as a
        # placeholder, since it's hard to migrate a database table in future.
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS volumes(',
            'id             char(36)      PRIMARY KEY,',
            'protocol_type  varchar(8)    NOT NULL,',
            'size           varchar(8)    NOT NULL,',
            'status         varchar(32),',
            'image_id       char(36),',
            'snapshot_id    char(36),',
            'deleted        smallint      DEFAULT 0,',
            'deleted_at     char(26),',
            'comment        varchar(128))'))
        with get_volume_conn() as conn:
            conn.execute(sql)

    def _initialize_table_volume_attachments(self):
        sql = ' '.join((
            'CREATE TABLE IF NOT EXISTS volume_attachments(',
            'id               char(36)      PRIMARY KEY,',
            'volume_id        char(36)      NOT NULL,',
            'instance_id      char(36)      NOT NULL,',
            'connection_info  varchar(256)  NOT NULL,',
            'mountpoint       varchar(32),',
            'deleted          smallint      DEFAULT 0,',
            'deleted_at       char(26),',
            'comment          varchar(128))'))
        with get_volume_conn() as conn:
            conn.execute(sql)

    def get_volume_by_id(self, volume_id):
        """Query a volume from  database by its id.
        The id must be a 36-character string.
        """
        if not volume_id:
            msg = "Volume id must be specified!"
            raise exception.SDKInvalidInputFormat(msg)

        with get_volume_conn() as conn:
            result_list = conn.execute(
                "SELECT * FROM volumes WHERE id=? AND deleted=0", (volume_id,)
                ).fetchall()

        if len(result_list) == 1:
            return result_list[0]
        elif len(result_list) == 0:
            LOG.debug("Volume %s is not found!" % volume_id)
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
            raise exception.SDKInvalidInputFormat(msg)

        volume_id = str(uuid.uuid4())
        protocol_type = volume['protocol_type']
        size = volume['size']
        status = self._VOLUME_STATUS_FREE
        image_id = volume.get('image_id', None)
        snapshot_id = volume.get('snapshot_id', None)
        deleted = '0'
        deleted_at = None
        comment = volume.get('comment', None)

        with get_volume_conn() as conn:
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
            raise exception.SDKInvalidInputFormat(msg)

        # get current volume properties
        volume_id = volume['id']
        old_volume = self.get_volume_by_id(volume_id)
        if not old_volume:
            obj_desc = "Volume %s" % volume_id
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID=self._mod_id)
        else:
            (_, _, size, status, image_id, snapshot_id, _, _, comment
             ) = old_volume

        size = volume.get('size', size)
        status = volume.get('status', status)
        image_id = volume.get('image_id', image_id)
        snapshot_id = volume.get('snapshot_id', snapshot_id)
        comment = volume.get('comment', comment)

        with get_volume_conn() as conn:
            conn.execute(' '.join((
                "UPDATE volumes",
                "SET size=?, status=?, image_id=?, snapshot_id=?, comment=?"
                "WHERE id=?")),
                (size, status, image_id, snapshot_id, comment, volume_id))

    def delete_volume(self, volume_id):
        """Delete a volume from database."""
        if not volume_id:
            msg = "Volume id must be specified!"
            raise exception.SDKInvalidInputFormat(msg)

        volume = self.get_volume_by_id(volume_id)
        if not volume:
            obj_desc = "Volume %s" % volume_id
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID=self._mod_id)

        time = str(datetime.now())
        with get_volume_conn() as conn:
            conn.execute(' '.join((
                "UPDATE volumes",
                "SET deleted=1, deleted_at=?",
                "WHERE id=?")),
                (time, volume_id))

    def get_attachment_by_volume_id(self, volume_id):
        """Query a volume-instance attachment map from database by volume id.
        The id must be a 36-character string.
        """
        if not volume_id:
            msg = "Volume id must be specified!"
            raise exception.SDKInvalidInputFormat(msg)

        with get_volume_conn() as conn:
            result_list = conn.execute(' '.join((
                "SELECT * FROM volume_attachments",
                "WHERE volume_id=? AND deleted=0")),
                (volume_id,)
                ).fetchall()

        if len(result_list) == 1:
            return result_list[0]
        elif len(result_list) == 0:
            LOG.debug("Attachment info of volume %s is not found!" % volume_id)
            return None

    def get_attachments_by_instance_id(self, instance_id):
        """Query a volume-instance attachment map database by instance id.
        The id must be a 36-character string.
        """
        if not instance_id:
            msg = "Instance id must be specified!"
            raise exception.SDKInvalidInputFormat(msg)

        with get_volume_conn() as conn:
            result_list = conn.execute(' '.join((
                "SELECT * FROM volume_attachments",
                "WHERE instance_id=? AND deleted=0")),
                (instance_id,)
                ).fetchall()

        if len(result_list) > 0:
            return result_list
        else:
            LOG.debug(
                "Attachments info of instance %s is not found!" % instance_id)
            return None

    def insert_volume_attachment(self, volume_attachment):
        """Insert a volume-instance attachment map into database.
        The volume-instance attachment map is represented by a dict of
        following properties:
        id: unique id of this attachment map. Auto generated and can not be
        specified.
        volume_id, volume id, must be specified.
        instance_id, instance id, must be specified.
        connection_info: all connection information about this attachment,
        represented by a dict defined by specific implementations. Must be
        specified.
        mountpoint: the mount point on which the volume will be attached on,
        optional.
        deleted: if deleted, auto generated and can not be specified.
        deleted_at: auto generated and can not be specified.
        comment: any comment, optional.
        """
        if not (isinstance(volume_attachment, dict) and
                'volume_id' in volume_attachment.keys() and
                'instance_id' in volume_attachment.keys() and
                'connection_info' in volume_attachment.keys()):
            msg = ("Invalid volume_attachment database entry %s !"
                   ) % volume_attachment
            raise exception.SDKInvalidInputFormat(msg)

        # TOOD  volume and instance must exist
        volume_id = volume_attachment['volume_id']
        if not self.get_volume_by_id(volume_id):
            obj_desc = "Volume %s" % volume_id
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID=self._mod_id)
        instance_id = volume_attachment['instance_id']
        # FIXME  need to use get_instance function by Dong Yan

        # attachment must not exist
        with get_volume_conn() as conn:
            count = conn.execute(' '.join((
                "SELECT COUNT(*) FROM volume_attachments",
                "WHERE volume_id=? AND instance_id=? AND deleted=0")),
                (volume_id, instance_id)
                ).fetchone()[0]
        if count > 0:
            raise exception.SDKVolumeOperationError(
                rs=3, vol=volume_id, inst=instance_id)

        attachment_id = str(uuid.uuid4())
        connection_info = str(volume_attachment['connection_info'])
        mountpoint = volume_attachment.get('mountpoint', None)
        deleted = '0'
        deleted_at = None
        comment = volume_attachment.get('comment', None)

        with get_volume_conn() as conn:
            conn.execute(' '.join((
                "INSERT INTO volume_attachments",
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)")),
                (attachment_id, volume_id, instance_id, connection_info,
                 mountpoint, deleted, deleted_at, comment))

    def delete_volume_attachment(self, volume_id, instance_id):
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
        if not volume_id or not instance_id:
            msg = "Volume id and instance id must be specified!"
            raise exception.SDKInvalidInputFormat(msg)

        # if volume-instance attachment exists in the database
        with get_volume_conn() as conn:
            count = conn.execute(' '.join((
                "SELECT COUNT(*) FROM volume_attachments",
                "WHERE volume_id=? AND instance_id=? AND deleted=0")),
                (volume_id, instance_id)
                ).fetchone()[0]

        if count == 0:
            raise exception.SDKVolumeOperationError(
                rs=4, vol=volume_id, inst=instance_id)
        elif count > 1:
            msg = ("Duplicated records found in volume_attachment with "
                   "volume_id %s and instance_id %s !"
                   ) % (volume_id, instance_id)
            raise exception.SDKDatabaseException(msg=msg)

        time = str(datetime.now())
        with get_volume_conn() as conn:
            conn.execute(' '.join((
                "UPDATE volume_attachments",
                "SET deleted=1, deleted_at=?",
                "WHERE volume_id=? AND instance_id=?")),
                (time, volume_id, instance_id))


class ImageDbOperator(object):

    def __init__(self):
        self._create_image_table()
        self._module_id = 'image'

    def _create_image_table(self):
        create_image_table_sql = ' '.join((
                'CREATE TABLE IF NOT EXISTS image (',
                'imagename                varchar(128) PRIMARY KEY,',
                'imageosdistro            varchar(16),',
                'md5sum                   varchar(32),',
                'disk_size_units          varchar(16),',
                'image_size_in_bytes      varchar(32),',
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
        else:
            with get_image_conn() as conn:
                result = conn.execute("SELECT * FROM image")
                image_list = result.fetchall()

        if not image_list:
            obj_desc = "Image with name: %s" % imagename
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc,
                                                   modID=self._module_id)
        return image_list

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
            'id             char(36)      PRIMARY KEY,',
            'userid         varchar(8)    NOT NULL UNIQUE,',
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

    def add_guest(self, userid, meta='', comments=''):
        # Generate uuid automatically
        guest_id = str(uuid.uuid4())
        net_set = '0'
        with get_guest_conn() as conn:
            conn.execute(
                "INSERT INTO guests VALUES (?, ?, ?, ?, ?)",
                (guest_id, userid.upper(), meta, net_set, comments))

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
                "DELETE FROM guests WHERE userid=?", (userid.upper(),))

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
            sql_var.append(userid.upper())
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
        userid = userid.upper()
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
            sql_cmd += " comments=?,"
            sql_var.append(comments)

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
        userid = userid.upper()
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
