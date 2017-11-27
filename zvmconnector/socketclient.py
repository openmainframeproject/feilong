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


import json
import six
import socket


SDKCLIENT_MODID = 110
SOCKET_ERROR = [{'overallRC': 101, 'modID': SDKCLIENT_MODID, 'rc': 101},
                {1: "Failed to create client socket, error: %(error)s",
                 2: ("Failed to connect SDK server %(addr)s:%(port)s, "
                     "error: %(error)s"),
                 3: ("Failed to send all API call data to SDK server, "
                    "only %(sent)d bytes sent. API call: %(api)s"),
                 4: "Client receive empty data from SDK server",
                 5: ("Client got socket error when sending API call to "
                     "SDK server, error: %(error)s"),
                 6: ("Client got socket error when receiving response "
                     "from SDK server, error: %(error)s")},
                "SDK client or server get socket error",
                ]
INVALID_API_ERROR = [{'overallRC': 400, 'modID': SDKCLIENT_MODID, 'rc': 400},
                     {1: "Invalid API name, '%(msg)s'"},
                     "Invalid API name"
                     ]


class SDKSocketClient(object):

    def __init__(self, addr='127.0.0.1', port=2000, request_timeout=3600):
        self.addr = addr
        self.port = port
        # request_timeout is used to set the client socket timeout when
        # waiting results returned from server.
        self.timeout = request_timeout

    def _construct_api_name_error(self, msg):
        results = INVALID_API_ERROR[0]
        results.update({'rs': 1,
                        'errmsg': INVALID_API_ERROR[1][1] % {'msg': msg},
                        'output': ''})
        return results

    def _construct_socket_error(self, rs, **kwargs):
        results = SOCKET_ERROR[0]
        results.update({'rs': rs,
                        'errmsg': SOCKET_ERROR[1][rs] % kwargs,
                        'output': ''})
        return results

    def call(self, func, *api_args, **api_kwargs):
        """Send API call to SDK server and return results"""
        if not isinstance(func, str) or (func == ''):
            msg = ('Invalid input for API name, should be a'
                   'string, type: %s specified.') % type(func)
            return self._construct_api_name_error(msg)

        # Create client socket
        try:
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as err:
            return self._construct_socket_error(1, error=six.text_type(err))

        try:
            # Set socket timeout
            cs.settimeout(self.timeout)
            # Connect SDK server
            try:
                cs.connect((self.addr, self.port))
            except socket.error as err:
                return self._construct_socket_error(2, addr=self.addr,
                                                    port=self.port,
                                                    error=six.text_type(err))

            # Prepare the data to be sent
            api_data = json.dumps((func, api_args, api_kwargs))
            # Send the API call data to SDK server
            sent = 0
            total_len = len(api_data)
            got_error = False
            try:
                while (sent < total_len):
                    this_sent = cs.send(api_data[sent:])
                    if this_sent == 0:
                        got_error = True
                        break
                    sent += this_sent
            except socket.error as err:
                return self._construct_socket_error(5,
                                                    error=six.text_type(err))
            if got_error or sent != total_len:
                return self._construct_socket_error(3, sent=sent,
                                                    api=api_data)

            # Receive data from server
            return_blocks = []
            try:
                while True:
                    block = cs.recv(4096)
                    if not block:
                        break
                    return_blocks.append(block)
            except socket.error as err:
                # When the sdkserver cann't handle all the client request,
                # some client request would be rejected.
                # Under this case, the client socket can successfully
                # connect/send, but would get exception in recv with error:
                # "error: [Errno 104] Connection reset by peer"
                return self._construct_socket_error(6,
                                                    error=six.text_type(err))
        finally:
            # Always close the client socket to avoid too many hanging
            # socket left.
            cs.close()

        # Transform the received stream to standard result form
        # This client assumes that the server would return result in
        # the standard result form, so client just return the received
        # data
        if return_blocks != []:
            results = json.loads(''.join(return_blocks))
        else:
            results = self._construct_socket_error(4)
        return results
