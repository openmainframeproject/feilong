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


class socketConnection(object):
    """Client based on socket."""
    def __init__(self, ip_addr='127.0.0.1', port=2000, timeout=3600):
        self.client = socketclient.SDKSocketClient(ip_addr, port, timeout)

    def send_request(self, api_name, *api_args, **api_kwargs):
        """Refer to SDK API documentation.

        :param api_name:       SDK API name
        :param *api_args:      SDK API sequence parameters
        :param **api_kwargs:   SDK API keyword parameters
        """
        return self.client.call(api_name, *api_args, **api_kwargs)


class restConnection(object):
    """Client based on REST API."""
    def __init__(self, ip_addr='127.0.0.1', port=8080, ssl_enabled=False,
                 verify=False):
        self.client = restclient.RESTClient(ip_addr, port, ssl_enabled, verify)

    def request_token(self, authentication_path):
        if not authentication_path:
            # TODO(bjcb): implement this exception
            raise Exception("Authentication file is necessary!")
        return self.client.get_token(authentication_path)

    def send_request(self, token, api_name, *api_args, **api_kwargs):
        """Refer to SDK API documentation.

        :param token:          Token data for authentication
        :param api_name:       SDK API name
        :param *api_args:      SDK API sequence parameters
        :param **api_kwargs:   SDK API keyword parameters
        """
        if not token:
            # TODO(bjcb): implement this exception
            raise Exception("token is necessary for rest connection!")
        return self.client.call(token, api_name, *api_args, **api_kwargs)


def get_connector(ip_addr=None, port=None, timeout=3600,
                  connection_type='rest', ssl_enabled=False, verify=False):
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
    """
    if connection_type not in [CONN_TYPE_REST, CONN_TYPE_SOCKET]:
        raise Exception("The value of connection_type is invalid, it should "
                        "be rest or socket.")

    if connection_type == CONN_TYPE_SOCKET:
        return socketConnection(ip_addr or '127.0.0.1', port or 2000,
                                timeout)
    else:
        return restConnection(ip_addr or '127.0.0.1', port or 8080,
                              ssl_enabled=ssl_enabled, verify=verify)
