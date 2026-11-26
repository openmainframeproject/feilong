#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2026 IBM Corp.
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

import mock
import threading
import time
import unittest

from zvmsdk import hostevents


class ParseEventLineTestCase(unittest.TestCase):

    def test_logon(self):
        self.assertEqual(
            ('LOGON', 'LINUX001'),
            hostevents.parse_event_line(
                'EVENT LOGON    userid=linux001 type=0\n'))

    def test_logoff(self):
        self.assertEqual(
            ('LOGOFF', 'LINUX001'),
            hostevents.parse_event_line(
                'EVENT LOGOFF   userid=LINUX001 type=1'))

    def test_invalid_lines(self):
        for line in ('', 'INFO: Listening', 'EVENT LOGON userid=TOOLONGID1 '
                     'type=0', 'EVENT OTHER userid=A type=0',
                     'EVENT LOGON userid=A;rm type=0'):
            self.assertIsNone(hostevents.parse_event_line(line))


class HostEventMonitorTestCase(unittest.TestCase):

    def setUp(self):
        self.monitor = hostevents.HostEventMonitor(
            cmd=['true'], restart_delay=3600)
        # Pretend the thread already runs so get_events does not start smcli
        self.monitor._thread = threading.current_thread()
        self.addCleanup(self.monitor.stop)

    def _active(self):
        self.monitor._active = True

    def test_no_since_returns_last_seq_only(self):
        self._active()
        self.monitor._add_event('LOGON', 'A')
        res = self.monitor.get_events()
        self.assertEqual([], res['events'])
        self.assertEqual(self.monitor._seq, res['last_seq'])
        self.assertFalse(res['missed'])

    def test_events_since(self):
        self._active()
        start = self.monitor._seq
        self.monitor._add_event('LOGON', 'A')
        self.monitor._add_event('LOGOFF', 'B')
        res = self.monitor.get_events(since=start)
        self.assertEqual(['A', 'B'], [e['userid'] for e in res['events']])
        self.assertEqual(start + 2, res['last_seq'])
        self.assertFalse(res['missed'])
        res = self.monitor.get_events(since=res['last_seq'])
        self.assertEqual([], res['events'])
        self.assertFalse(res['missed'])

    def test_missed_when_buffer_overflow(self):
        monitor = hostevents.HostEventMonitor(
            cmd=['true'], buffer_size=2, restart_delay=3600)
        self.addCleanup(monitor.stop)
        monitor._thread = threading.current_thread()
        monitor._active = True
        start = monitor._seq
        for i in range(5):
            monitor._add_event('LOGON', 'A%d' % i)
        res = monitor.get_events(since=start)
        self.assertTrue(res['missed'])
        self.assertEqual(2, len(res['events']))

    def test_missed_when_since_from_before_restart(self):
        self._active()
        res = self.monitor.get_events(since=self.monitor._seq + 1000)
        self.assertTrue(res['missed'])

    def test_inactive_returns_immediately(self):
        start = time.time()
        res = self.monitor.get_events(since=self.monitor._seq, timeout=10)
        self.assertLess(time.time() - start, 5)
        self.assertFalse(res['active'])

    def test_long_poll_wakes_on_event(self):
        self._active()
        since = self.monitor._seq
        timer = threading.Timer(
            0.2, self.monitor._add_event, args=('LOGOFF', 'A'))
        timer.start()
        self.addCleanup(timer.cancel)
        res = self.monitor.get_events(since=since, timeout=10)
        self.assertEqual(1, len(res['events']))
        self.assertEqual('LOGOFF', res['events'][0]['type'])

    def test_long_poll_times_out(self):
        self._active()
        start = time.time()
        res = self.monitor.get_events(since=self.monitor._seq, timeout=1)
        self.assertGreaterEqual(time.time() - start, 0.9)
        self.assertEqual([], res['events'])
        self.assertTrue(res['active'])

    def test_collects_events_from_subprocess(self):
        script = ("echo 'EVENT LOGON    userid=LINUX001 type=0'; "
                  "echo 'INFO: noise'; "
                  "echo 'EVENT LOGOFF   userid=LINUX001 type=1'; sleep 5")
        monitor = hostevents.HostEventMonitor(
            cmd=['sh', '-c', script], restart_delay=3600)
        self.addCleanup(monitor.stop)
        since = monitor._seq
        monitor.start()
        deadline = time.time() + 10
        events = []
        while time.time() < deadline and len(events) < 2:
            res = monitor.get_events(since=since, timeout=1)
            events = res['events']
        self.assertEqual(['LOGON', 'LOGOFF'], [e['type'] for e in events])
        self.assertTrue(res['active'])

    def _start_and_get_proc(self, script):
        monitor = hostevents.HostEventMonitor(
            cmd=['sh', '-c', script], restart_delay=3600)
        monitor.start()
        deadline = time.time() + 5
        while monitor._proc is None and time.time() < deadline:
            time.sleep(0.05)
        self.assertIsNotNone(monitor._proc)
        return monitor, monitor._proc

    def _wait_exit(self, proc):
        # the monitor thread is in proc.wait(), so poll() can lag a moment
        deadline = time.time() + 5
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        return proc.poll()

    def test_stop_terminates_subprocess(self):
        monitor, proc = self._start_and_get_proc('sleep 30')
        monitor.stop()
        self.assertIsNotNone(self._wait_exit(proc))

    def test_stop_kills_subprocess_ignoring_sigterm(self):
        monitor, proc = self._start_and_get_proc(
            'trap "" TERM; while :; do sleep 1; done')
        time.sleep(0.3)
        with mock.patch.object(hostevents, 'STOP_WAIT_SECONDS', 0.5):
            monitor.stop()
        self.assertIsNotNone(self._wait_exit(proc))

    def test_stop_monitor_without_monitor(self):
        with mock.patch.object(hostevents, '_MONITOR', None):
            hostevents.stop_monitor()

    def test_stop_monitor_stops_started_monitor(self):
        fake = mock.Mock()
        with mock.patch.object(hostevents, '_MONITOR', fake):
            hostevents.stop_monitor()
        fake.stop.assert_called_once_with()
