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
import os
import sqlite3
import stat
from time import sleep

from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.exception import ZVMSDKInternalError


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
        LOG.error('Execute SQL statements error: ', err)
        raise exception.ZVMSDKInternalError(msg=err)
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
        file_mode = stat.S_IRUSR + stat.S_IWUSR + stat.S_IRGRP +\
                    stat.S_IWGRP + stat.S_IROTH + stat.S_IWOTH

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
        raise ZVMSDKInternalError("Get database connection time out!")

    def release_connection(self, i):
        self._free_conn[i] = True
