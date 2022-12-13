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


import unittest

from zvmsdk import config


CONF = config.CONF


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This can be used to set up confs before running all cases
        super(SDKTestCase, cls).setUpClass()
        cls.old_db_dir = CONF.database.dir
        set_conf('database', 'dir', '/tmp/')
        set_conf('zvm', 'disk_pool', 'ECKD:TESTPOOL')
        set_conf('image', 'sdk_image_repository', '/tmp/')
        set_conf('zvm', 'namelist', 'TSTNLIST')
        set_conf('logging', 'log_dir', '/tmp/zvmsdk_ut_logs/')

    @classmethod
    def tearDownClass(cls):
        super(SDKTestCase, cls).tearDownClass()
        # Restore the original db path
        CONF.database.dir = cls.old_db_dir

    def setUp(self):
        super(SDKTestCase, self).setUp()

    def _fake_fun(self, value=None):
        return lambda *args, **kwargs: value
