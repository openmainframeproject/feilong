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


from zvmconnector import socketclient
from zvmconnector import restclient


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

    def __init__(self, ip_addr='127.0.0.1', port=8080, timeout=3600):
        self.client = restclient.RESTClient(ip_addr, port, timeout)

    def request(self, api_name, *api_args, **api_kwargs):
        return self.client.call(api_name, *api_args, **api_kwargs)


class ZVMConnector(object):

    def __init__(self, ip_addr=None, port=None, timeout=3600,
                 connection_type=None):
        """
        :param str ip_addr:         IP address of SDK server
        :param int port:            Port of SDK server daemon
        :param int timeout:         Wait timeout if request no response
        :param str connection_type: The value should be 'socket' or 'rest'
        """
        if connection_type is None:
            if ((ip_addr is None) or
                (ip_addr == '127.0.0.1')):
                connection_type = CONN_TYPE_SOCKET
            else:
                connection_type = CONN_TYPE_REST
        self.conn = self._get_connection(ip_addr, port, timeout,
                                         connection_type)

    def _get_connection(self, ip_addr, port, timeout, connection_type):
        if connection_type == CONN_TYPE_SOCKET:
            return socketConnection(ip_addr or '127.0.0.1', port or 2000,
                                    timeout)
        else:
            return restConnection(ip_addr or '127.0.0.1', port or 2000,
                                    timeout)

    def send_request(self, api_name, *api_args, **api_kwargs):
        """Refer to SDK API documentation.

        :param api_name:       SDK API name
        :param *api_args:      SDK API sequence parameters
        :param **api_kwargs:   SDK API keyword parameters
        """
        return self.conn.request(api_name, *api_args, **api_kwargs)
