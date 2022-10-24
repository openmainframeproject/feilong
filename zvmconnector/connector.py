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

import fcntl
from datetime import datetime

from zvmsdk import log

from zvmconnector import socketclient
from zvmconnector import restclient


LOG = log.LOG


CONN_TYPE_SOCKET = 'socket'
CONN_TYPE_REST = 'rest'


class baseConnection(object):
    def request(self, api_name, *api_args, **api_kwargs):
        pass


class socketConnection(baseConnection):

    def __init__(self, ip_addr='127.0.0.1', port=2000, timeout=3600):
        self.client = socketclient.SDKSocketClient(ip_addr, port, timeout)

    def request(self, api_name, *api_args, **api_kwargs):
        return self.client.call(api_name, *api_args, **api_kwargs)


class restConnection(baseConnection):

    def __init__(self, ip_addr='127.0.0.1', port=8080, ssl_enabled=False,
                 verify=False, token_path=None):
        self.client = restclient.RESTClient(ip_addr, port, ssl_enabled, verify,
                                            token_path)

    def request(self, api_name, *api_args, **api_kwargs):
        return self.client.call(api_name, *api_args, **api_kwargs)


class ZVMConnector(object):

    def __init__(self, ip_addr=None, port=None, timeout=3600,
                 connection_type=None, ssl_enabled=False, verify=False,
                 token_path=None):
        """
        :param str ip_addr:         IP address of SDK server
        :param int port:            Port of SDK server daemon
        :param int timeout:         Wait timeout if request no response
        :param str connection_type: The value should be 'socket' or 'rest'
        :param boolean ssl_enabled: Whether SSL enabled or not. If enabled,
                                    use HTTPS instead of HTTP. The https
                                    server should enable SSL to support this.
        :param boolean/str verify:  Either a boolean, in which case it
                                    controls whether we verify the server's
                                    TLS certificate, or a string, in which
                                    case it must be a path to a CA bundle
                                    to use. Default to False.
        :param str token_path:      The path of token file.
        """
        if (connection_type is not None and
                connection_type.lower() == CONN_TYPE_SOCKET):
            connection_type = CONN_TYPE_SOCKET
        else:
            connection_type = CONN_TYPE_REST
        self.conn = self._get_connection(ip_addr, port, timeout,
                                         connection_type, ssl_enabled, verify,
                                         token_path)

    def _get_connection(self, ip_addr, port, timeout,
                        connection_type, ssl_enabled, verify,
                        token_path):
        if connection_type == CONN_TYPE_SOCKET:
            return socketConnection(ip_addr or '127.0.0.1', port or 2000,
                                    timeout)
        else:
            return restConnection(ip_addr or '127.0.0.1', port or 8080,
                                  ssl_enabled=ssl_enabled, verify=verify,
                                  token_path=token_path)

    def send_request(self, api_name, *api_args, **api_kwargs):
        """Refer to SDK API documentation.

        :param api_name:       SDK API name
        :param *api_args:      SDK API sequence parameters
        :param **api_kwargs:   SDK API keyword parameters
        """
        info = self.conn.request(api_name, *api_args, **api_kwargs)

        # {'overallRC': 101, 'modID': 110, 'rc': 101, 'rs': 2, 'errmsg':
        # 'Failed to connect SDK server 127.0.0.1:2000, error: [Errno 111]
        # Connection refused', 'output': ''}

        if info.get('overallRC') == 101 and info.get('rc') == 101 and \
            info.get("rs") == 2 and \
            info.get("errmsg").__contains__('Failed to connect SDK server'):

            # handle retry again
            _handle_retry_with_lock()

            info = self.conn.request(api_name, *api_args, **api_kwargs)

        return info


# command that gonna restart sdkserver, it must be systemctl
# as we ask for SUDO for such command and ask for SELinux
COMMAND = "sudo systemctl restart sdkserver"


# retry the command to get a chance to redo the command
def _handle_retry():
    import subprocess
    import time

    try:
        p = subprocess.Popen(COMMAND, stdout=subprocess.PIPE, shell=True)
        out = p.communicate()
        LOG.info("executed command: %s, result is: %s", COMMAND, out)
    except Exception as err:
        LOG.info(err)

    # try after sleep to give time of sdkserver startup functional
    time.sleep(1)


LOCKFILE = "/etc/zvmsdk/sdkserver_retry.lck"
RETRYFILE = "/etc/zvmsdk/sdkserver_retry.last"


def _handle_retry_with_lock():
    # we need handle following situation
    # 2+ zvmsdk httpd service running and all found sdkserver not running
    # we need make sure there is one restart and only one
    dt = datetime.now()
    ts = datetime.timestamp(dt)

    # we need get time to try get lock time first
    with Locker():
        # if we get lock, read the time that did action
        try:
            f = open(RETRYFILE, "r")
            told = f.read()
            f.close()
        except Exception as err:
            LOG.info("failed to operate: %s", err)
            told = ""

        LOG.info("old/new ts is %s/%s", told, ts)
        # if it's updated during we try to get lock
        try:
            if len(told) == 0 or float(told) < float(ts):
                # retry
                _handle_retry()

                # write current timestamp
                f = open(RETRYFILE, "w+")
                dt = datetime.now()
                ts = datetime.timestamp(dt)
                f.write(str(ts))
                f.close()
        except Exception as err:
            LOG.info("failed to retry: %s", err)


class Locker:

    def __enter__(self):
        try:
            self.fp = open(LOCKFILE, "w+")
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX)
        except Exception as err:
            LOG.debug("failed to operate: %s", err)
            self.fp = None

    def __exit__(self, _type, value, tb):
        if self.fp:
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
