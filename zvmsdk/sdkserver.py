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
import os
import socket
import sys
import threading

from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception


CONF = config.CONF


class SDKServer(object):
    def __init__(self):
        self.sdkapi = api.SDKAPI()
        self.server_socket = self.setup()

    def log_error(self, msg):
        print msg

    def log_info(self, msg):
        print msg

    def log_warn(self, msg):
        print msg

    def send_results(self, client, results):
        """ send back results to client in the json format of:
        {'overallRC': x, 'rc': x, 'rs': x, 'errmsg': 'msg', 'output': 'out'}
        """
        json_results = json.dumps(results)
        sent = 0
        total_len = len(json_results)
        got_error = False
        while (sent < total_len):
            this_sent = client.send(json_results[sent:])
            if this_sent == 0:
                got_error = True
                break
            sent += this_sent
        if got_error or sent != total_len:
            self.log_error("Failed to send back clients the results: %s" %
                      json_results)
        else:
            self.log_info("Results sent back to client successfully.")
        # Close the connection
        client.close()

    def serve_API(self, client):
        """ Read client request and call target SDK API"""
        self.log_info("new thread started to handle client request")
        data = client.recv(4096)
        api_data = json.loads(data)
        # API_data should be in the form [funcname, args_list, kwargs_dict]
        if not isinstance(api_data, list) or len(api_data) != 3:
            msg = "SDK server got wrong input: %s" % data
            self.log_error(msg)
            result = {'overallRC': 2, 'rc': 2, 'rs': 1,
                      'errmsg': msg,
                      'output': ''}
            self.send_results(client, results)
            os._exit()
        else:
            (func_name, api_args, api_kwargs) = api_data
            self.log_info("func: %s, args: %s, kwargs: %s" % (func_name,
                                                              str(api_args),
                                                              str(api_kwargs)))
            try:
                api_func = getattr(self.sdkapi, func_name)
            except AttributeError:
                msg = "Wrong API name: %s." % func_name
                log_error(msg)
                results = {'overallRC': 2, 'rc': 2, 'rs': 2,
                           'errmsg': msg,
                           'output': ''}
                self.send_results(client, results)
                os._exit()
            # invoke target API function
            try:
                return_data = api_func(*api_args, **api_kwargs)
            except exception.SDKBaseException as e:
                # get the error info from exception attribute
                # All SDKbaseexception should eventually has a
                # results attribute defined which can be used by
                # sdkserver here
                if e.results:
                    results = {'overallRC': e.results['overallRC'],
                               'rc': e.results['rc'], 'rs': e.results['rs'],
                               'errmsg': e.format_message(),
                               'output': ''}
                else:
                    results = {'overallRC': 2,
                               'rc': 2, 'rs': 3,
                               'errmsg': str(e),
                               'output': ''}
            except Exception as e:
                results = {'overallRC': 2, 'rc': 2, 'rs': 3,
                           'errmsg': str(e),
                           'output': ''}
            else:
                if not return_data:
                    return_data = ''
                results = {'overallRC': 0, 'rc': 0, 'rs': 0,
                           'errmsg': '',
                           'output': return_data}
            # Send back the final results
            self.send_results(client, results)

    def setup(self):
        #create server socket
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            self.log_error("Failed to create SDK server socket: %s" % msg)
            sys.exit(1)

        # bind server address and port
        host = CONF.sdkserver.bind_addr
        port = CONF.sdkserver.bind_port
        try:
            server_sock.bind((host, port))
        except socket.error as msg:
            self.log_error("Failed to bind to (%s, %d), reason: %s" %
                             (host, port, msg))
            server_sock.close()
            sys.exit(1)

        # Start listening
        server_sock.listen(5)
        self.log_info("SDK server now listening")
        return server_sock

    def run(self):
        # Keep running in a loop to handle client connections
        while True:
            # Wait client connection
            conn, addr = self.server_socket.accept()
            self.log_info("Connected with %s:%s" % (addr[0], addr[1]))
            # Start a new thread to call the API
            thread = threading.Thread(target=self.serve_API, args=(conn,))
            thread.start()


def start_daemon():
    server = SDKServer()
    server.run()


if __name__ == '__main__':
    start_daemon()
