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

"""z/VM guest logon/logoff events for the ``/host/events`` API.

The sdkserver owns a single ``smcli Event_Subscribe`` subprocess and keeps the
events it prints in a bounded in-memory buffer. API consumers read the buffer
with ``HostEventMonitor.get_events``, which supports long polling, so they do
not have to poll z/VM for power state changes.

NOTE: the ``smcli Event_Subscribe`` command line and its output format are an
internal interface of this module. They are not stable and are not part of
the Feilong contract; the contract is the ``host_get_events`` API only.
"""

import collections
import os
import re
import signal
import subprocess
import threading
import time

from zvmsdk import log


LOG = log.LOG

SMCLI_EVENT_CMD = ['sudo', '/opt/zthin/bin/smcli', 'Event_Subscribe']

# Events kept for slow consumers. A consumer that falls further behind than
# this gets 'missed': True and must resynchronize.
EVENT_BUFFER_SIZE = 4096
# Upper limit of a single long poll. It stays below common HTTP gateway
# timeouts so the request is not cut off by a proxy or the web server.
MAX_WAIT_SECONDS = 30
# Delay before smcli is started again after it exited.
RESTART_DELAY_SECONDS = 30
# How long stop() waits for smcli to exit before it is killed.
STOP_WAIT_SECONDS = 5

# The only line format accepted from smcli, for example:
#   EVENT LOGON    userid=LINUX001 type=0
_EVENT_RE = re.compile(
    r'^EVENT\s+(LOGON|LOGOFF)\s+userid=([A-Za-z0-9$#@_-]{1,8})\s+type=[01]$')

_MONITOR = None
_MONITOR_LOCK = threading.Lock()


def get_monitor():
    global _MONITOR
    with _MONITOR_LOCK:
        if _MONITOR is None:
            _MONITOR = HostEventMonitor()
        return _MONITOR


def stop_monitor():
    """Stop the monitor and its smcli subprocess, if they were started."""
    with _MONITOR_LOCK:
        monitor = _MONITOR
    if monitor is not None:
        monitor.stop()


def parse_event_line(line):
    """Parse one smcli output line.

    :returns: (event_type, userid) or None when the line is not an event.
    """
    match = _EVENT_RE.match(line.strip())
    if not match:
        return None
    return match.group(1), match.group(2).upper()


class HostEventMonitor(object):

    def __init__(self, cmd=None, buffer_size=EVENT_BUFFER_SIZE,
                 restart_delay=RESTART_DELAY_SECONDS):
        self._cmd = list(cmd or SMCLI_EVENT_CMD)
        self._restart_delay = restart_delay
        self._events = collections.deque(maxlen=buffer_size)
        # The sequence starts at the start time in ms, so a consumer holding
        # a sequence from before an sdkserver restart sees 'missed' and
        # resynchronizes.
        self._seq = int(time.time() * 1000)
        self._cond = threading.Condition()
        self._active = False
        self._stopped = threading.Event()
        self._thread = None
        self._proc = None

    def start(self):
        with self._cond:
            if self._thread is not None:
                return
            self._thread = threading.Thread(target=self._run,
                                            name='host-event-monitor')
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        """Stop collecting and make sure the smcli subprocess is gone.

        The sdkserver calls this (stop_monitor) when it stops, from its
        signal handler and from the end of start_daemon. Otherwise smcli is
        left running after a restart: sudo moves it out
        of the service cgroup, so systemd does not clean it up, and it takes
        events away from the next subscriber.

        smcli is started in its own session and the signal goes to the whole
        process group. A signal sent only to the sudo process is not relayed
        to smcli when it comes from the same process group as sudo.
        """
        self._stopped.set()
        proc = self._proc
        if proc is None:
            return
        if not self._signal_group(proc, signal.SIGTERM):
            return
        deadline = time.time() + STOP_WAIT_SECONDS
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if proc.poll() is None:
            self._signal_group(proc, signal.SIGKILL)

    @staticmethod
    def _signal_group(proc, sig):
        try:
            os.killpg(proc.pid, sig)
        except OSError:
            return False
        return True

    def _set_active(self, active):
        with self._cond:
            self._active = active
            self._cond.notify_all()

    def _add_event(self, event_type, userid):
        with self._cond:
            self._seq += 1
            self._events.append({'seq': self._seq, 'type': event_type,
                                 'userid': userid,
                                 'time': int(time.time())})
            self._cond.notify_all()

    def _run(self):
        while not self._stopped.is_set():
            try:
                self._consume_smcli()
            except Exception as err:
                LOG.error("Host event monitor failed: %s", err)
            self._set_active(False)
            if self._stopped.wait(self._restart_delay):
                break
            LOG.warning("Restarting smcli Event_Subscribe")

    def _consume_smcli(self):
        proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,
                                close_fds=True, universal_newlines=True,
                                start_new_session=True)
        self._proc = proc
        LOG.info("Started smcli Event_Subscribe, pid %s", proc.pid)
        self._set_active(True)
        try:
            for line in proc.stdout:
                parsed = parse_event_line(line)
                if parsed is None:
                    LOG.debug("Ignored unexpected Event_Subscribe output")
                    continue
                self._add_event(*parsed)
        finally:
            self._proc = None
            proc.stdout.close()
            rc = proc.wait()
            LOG.warning("smcli Event_Subscribe exited with rc %s", rc)

    def get_events(self, since=None, timeout=0):
        """Return the events newer than ``since``, waiting up to ``timeout``.

        :param since: sequence of the last event the caller has seen. When
            None, no events are returned and the result only tells the
            current ``last_seq`` to start from.
        :param timeout: seconds to wait for a new event when there is none.
        :returns: dict with 'last_seq', 'active' (smcli is running),
            'missed' (events were lost, the caller must resynchronize) and
            'events' (list of dicts with seq, type, userid and time).
        """
        self.start()
        timeout = min(max(timeout, 0), MAX_WAIT_SECONDS)
        deadline = time.time() + timeout
        with self._cond:
            while True:
                newer = []
                missed = False
                if since is not None:
                    newer = [e for e in self._events if e['seq'] > since]
                    missed = since > self._seq or (
                        since < self._seq and
                        (not newer or newer[0]['seq'] != since + 1))
                remaining = deadline - time.time()
                if (since is None or newer or missed or remaining <= 0 or
                        not self._active):
                    return {'last_seq': self._seq, 'active': self._active,
                            'missed': missed, 'events': newer}
                self._cond.wait(remaining)
