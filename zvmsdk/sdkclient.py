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
import socket


class SDKClient(object):
    """"""
    
    def __init__(self, addr='127.0.0.1', port=2000):
        self.addr = addr
        self.port = port

    def call(self, func, *args, **kwargs):
        """Send API call to SDK server and return results"""
        # Create client socket
        try:
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            return {'overallRC': 1,
                    'rc': 1,
                    'rs': 1,
                    'errmsg': 'Failed to create client socket: %s' % msg,
                    'output': ''}

        # Connect SDK server
        try:
            cs.connect((self.addr, self.port))
        except socket.error as msg:
            cs.close()
            return {'overallRC': 1,
                    'rc': 1,
                    'rs': 2,
                    'errmsg': 'Failed to connect SDK server: %s' % msg,
                    'output': ''}

        # Prepare the data to be sent
        api_data = json.dumps((func, args, kwargs))
        print "generated command: %s" % api_data
        # Send the API call data to SDK server
        sent = 0
        total_len = len(api_data)
        got_error = False
        while (sent < total_len):
            this_sent = cs.send(api_data[sent:])
            if this_sent == 0:
                got_error = True
                break
            sent += this_sent
        if got_error or sent != total_len:
            cs.close()
            return {'overallRC': 1,
                    'rc': 1,
                    'rs': 3,
                    'errmsg': ('Failed to send API call to SDK server,'
                               '%d bytes sent. API call: %s') % (sent,
                                                                 api_data),
                    'output': ''}
        else:
            print "API call is sent to SDK server successfully: %s" % api_data

        # Receive data from server
        return_blocks = []
        while True:
            # TODO: Add timeout to socket, otherwise when SDK server got
            # uncaught exception or shutdown, the client would be blocked
            # here forever.
            block = cs.recv(4096)
            if not block:
                break
            return_blocks.append(block)
        # Close the socket
        cs.close()

        # Transform the received stream to standard result form
        # This client assumes that the server would return result in
        # the standard result form, so client just return the received
        # data
        if return_blocks != []:
            result = json.loads(''.join(return_blocks))
            print "Received results from server: %s" % result
        else:
            result = {'overallRC': 1,
                      'rc': 1,
                      'rs': 4,
                      'errmsg': ('Failed to receive API results from'
                                 'SDK server'),
                      'output': ''}
        return result
