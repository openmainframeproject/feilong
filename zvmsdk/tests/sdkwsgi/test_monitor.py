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

import threading
import time

from zvmsdk.tests.sdkwsgi import base
from zvmsdk.tests.sdkwsgi import test_utils
from zvmsdk import config
from zvmsdk import monitor

CONF = config.CONF


class MonitorTestCase(base.ZVMConnectorBaseTestCase):

    def __init__(self, methodName='runTest'):
        super(MonitorTestCase, self).__init__(methodName)
        self.test_utils = test_utils.ZVMConnectorTestUtils()
        self.userid1 = None
        self.userid2 = None

    def setUp(self):
        super(MonitorTestCase, self).setUp()

        # create test servers
        try:
            self.userid1 = self.test_utils.guest_deploy()[0]
            self.userid2 = self.test_utils.guest_deploy()[0]
        finally:
            self.addCleanup(self.test_utils.guest_destroy, self.userid1)
            self.addCleanup(self.test_utils.guest_destroy, self.userid2)

    def test_monitor(self):
        self.assertEqual(True, True)


class MeteringCacheTestCase(base.ZVMConnectorBaseTestCase):

    def setUp(self):
        self.set_conf('monitor', 'cache_interval', 1000)
        self.mc = monitor.MeteringCache(('typeA', 'typeB'))
        self.addCleanup(self.mc._reset(('typeA', 'typeB')))

    def test_init(self):
        self.assertListEqual(self.mc._cache.keys(), ['typeA', 'typeB'])
        self.assertEqual(self.mc._cache['typeA'].keys(),
                         ['expiration', 'data'])
        self.assertEqual(self.mc._cache['typeB'].keys(),
                         ['expiration', 'data'])
        self.assertEqual(self.mc._cache['typeA']['data'], {})
        self.assertEqual(self.mc._cache['typeB']['data'], {})
        self.assertIsInstance(self.mc._lock, threading.RLock)
        self.assertListEqual(self.mc._types, ['typeA', 'typeB'])

    def test_set_get_delete(self):
        self.mc.set('typeA', 'data1', 'value1')
        self.mc.set('typeA', 'data2', 'value2')
        self.mc.set('typeB', 'data1', 'value1')
        self.mc.set('typeB', 'data2', 'value2')
        self.assertListEqual(self.mc._cache['typeA']['data'].keys(),
                         ['data1', 'data2'])
        self.assertListEqual(self.mc._cache['typeB']['data'].keys(),
                         ['data1', 'data2'])
        self.assertListEqual(self.mc._cache['typeA']['data']['data1'],
                             'value1')
        self.assertListEqual(self.mc._cache['typeB']['data']['data1'],
                             'value1')
        # Test get
        self.assertEqual(self.mc.get('typeA', 'data1'), 'value1')
        self.assertEqual(self.mc.get('typeA', 'data2'), 'value2')
        # Delete
        self.mc.delete('typeA', 'data1')
        self.assertEqual(self.mc.get('typeA', 'data1'), None)
        self.assertEqual(self.mc.get('typeA', 'data2'), 'value2')

    def test_refresh_and_expire(self):
        data = {'data1': 'value1',
                'data2': 'value2'}
        # Test refresh
        self.mc.refresh('typeA', data)
        self.assertEqual(self.mc.get('typeA', 'data1'), 'value1')
        self.assertEqual(self.mc.get('typeA', 'data2'), 'value2')
        self.set_conf('monitor', 'cache_interval', 1)
        # Test expire
        self.mc.refresh('typeA', data)
        time.sleep(2)
        self.assertEqual(self.mc.get('typeA', 'data1'), None)
        self.assertEqual(self.mc.get('typeA', 'data2'), None)
