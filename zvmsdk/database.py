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

from zvmsdk import config

CONF = config.CONF


class Database(object):

    def __init__(self):

        database = self._prepare()
        self._conn = sqlite3.connect(database)
        # autocommit
        self._conn.isolation_level = None

    def _prepare(self):
        file_mode = 777

        if not os.path.exists(CONF.database.path):
            os.makedirs(CONF.database.path, file_mode)
        else:
            mode = oct(os.stat(CONF.database.path).st_mode)[-3:]
            if mode != '777':
                os.chmod(CONF.database.path, file_mode)

        return ''.join((CONF.database.path, "/", CONF.database.name))

    def create_table(self, table_name, attribute):

        create_table_sql = ' '.join((
                        'create table if not exists %s (' % table_name,
                        '%s);' % attribute))
        self._conn.execute(create_table_sql)

    def drop_table(self, table_name):
        drop_table_sql = 'DROP TABLE %s' % table_name
        self._conn.execute(drop_table_sql)

    def delete_table_record(self, table_name, filter):
        delete_record_sql = 'DELETE FROM %s WHERE %s' % (table_name, filter)
        self._conn.execute(delete_record_sql)

    def insert_table_record(self, table_name, values, column_set=None):

        if column_set is not None:
            insert_record_sql = ('INSERT INTO %s (%s) VALUES %s' %
                                 (table_name, column_set, values))
        else:
            insert_record_sql = ('INSERT INTO %s VALUES %s' %
                                 (table_name, values))
        self._conn.execute(insert_record_sql)

    def update_table_record(self, table_name, values, filter=None):

        if filter is None:
            update_record_sql = 'UPDATE %s SET %s' % (table_name, values)
        else:
            update_record_sql = ('UPDATE %s SET %s WHERE %s' %
                                 (table_name, values, filter))
        self._conn.execute(update_record_sql)

    def select_table_record(self, table_name, column_set='*', filter=None):
        if filter is None:
            select_record_sql = 'SELECT %s FROM %s' % (column_set, table_name)
        else:
            select_record_sql = ('SELECT %s FROM %s WHERE %s' %
                                 (column_set, table_name, filter))
        cur = self._conn.cursor()
        cur.execute(select_record_sql)
        result = cur.fetchall()
        cur.close()
        return result
