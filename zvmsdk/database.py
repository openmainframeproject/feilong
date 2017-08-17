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

CONF = config.CONF


class Database(object):

    def __init__(self):
        self._prepare()

    def _prepare(self):
        file_mode = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO

        if not os.path.exists(CONF.database.path):
            os.makedirs(CONF.database.path, file_mode)
        else:
            path_mode = oct(os.stat(CONF.database.path).st_mode)[-3:]
            if path_mode != '777':
                os.chmod(CONF.database.path, file_mode)

        database = ''.join((CONF.database.path, "/", CONF.database.name))
        self._conn = sqlite3.connect(database)

        db_mode = oct(os.stat(database).st_mode)[-3:]
        if db_mode != '777':
            os.chmod(database, file_mode)

        # autocommit
        self._conn.isolation_level = None

    def create_table(self, table_name, attribute):

        create_table_sql = ' '.join((
                        'create table if not exists %s (' % self.table_name,
                        '%s);' % attribute))
        self._conn.execute(create_table_sql)
