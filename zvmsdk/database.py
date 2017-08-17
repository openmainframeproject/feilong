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


import os
import sqlite3
import stat

from zvmsdk import config
from zvmsdk import constants as const

CONF = config.CONF

_DB_OPERATOR = None


def get_DbOperator():
    global _DB_OPERATOR

    if _DB_OPERATOR is not None:
        return _DB_OPERATOR

    _DB_OPERATOR = DbOperator()
    return _DB_OPERATOR


class DbOperator(object):

    def __init__(self):
        self._prepare()

    def _prepare(self):
        path_mode = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO
        file_mode = stat.S_IRUSR + stat.S_IWUSR + stat.S_IRGRP +\
                    stat.S_IWGRP + stat.S_IROTH + stat.S_IWOTH

        if not os.path.exists(CONF.database.path):
            os.makedirs(CONF.database.path, path_mode)
        else:
            path_mode = oct(os.stat(CONF.database.path).st_mode)[-3:]
            if path_mode != '777':
                os.chmod(CONF.database.path, path_mode)

        database = ''.join((CONF.database.path, "/", const.DATABASE_NAME))
        self._conn = sqlite3.connect(database)

        db_mode = os.stat(database).st_mode

        mu = (db_mode & stat.S_IRWXU) >> 6
        mg = (db_mode & stat.S_IRWXG) >> 3
        mo = db_mode & stat.S_IRWXO

        if ((mu < 6) or (mg < 6) or (mo < 6)):
            os.chmod(database, file_mode)

        # autocommit
        self._conn.isolation_level = None
