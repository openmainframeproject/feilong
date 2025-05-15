#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2018 IBM Corp.
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
import sys
import threading
import traceback
from time import time, sleep
from random import randrange

from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import returncode
from zvmsdk import constants

if six.PY3:
    import queue as Queue
else:
    import Queue


CONF = config.CONF
LOG = log.LOG


class SDKServer(object):
    def __init__(self):
        # Initailize SDK API
        self.sdkapi = api.SDKAPI()
        self.server_socket = None
        self.request_queue = Queue.Queue(maxsize=
                                         CONF.sdkserver.request_queue_size)
        
        rate_limit_config_dict = {}
        for entry in [cnf_entry.strip() for cnf_entry in CONF.sdkserver.smapi_rate_limit_per_window.split(',')]:
            fields = entry.split(':')
            rate_limit_config_dict[fields[0].strip()] = int(fields[1].strip())
        
        self.outstanding_requests = 0
        self.outstanding_counter_lock = threading.Lock()
        self.rate_limit_config = rate_limit_config_dict
        self.rate_window_records = {}
        self.rate_window_lock = threading.Lock()
        self.postponed_requests = {}

    def log_error(self, msg):
        thread = threading.current_thread().name
        msg = ("[%s] %s" % (thread, msg))
        LOG.error(msg)

    def log_info(self, msg):
        thread = threading.current_thread().name
        msg = ("[%s] %s" % (thread, msg))
        LOG.info(msg)

    def log_warn(self, msg):
        thread = threading.current_thread().name
        msg = ("[%s] %s" % (thread, msg))
        LOG.warning(msg)

    def log_debug(self, msg):
        thread = threading.current_thread().name
        msg = ("[%s] %s" % (thread, msg))
        LOG.debug(msg)

    def construct_internal_error(self, msg):
        self.log_error(msg)
        error = returncode.errors['internal']
        results = error[0]
        results['modID'] = returncode.ModRCs['sdkserver']
        results.update({'rs': 1,
                        'errmsg': error[1][1] % {'msg': msg},
                        'output': ''})
        return results

    def construct_api_name_error(self, msg):
        self.log_error(msg)
        error = returncode.errors['API']
        results = error[0]
        results['modID'] = returncode.ModRCs['sdkserver']
        results.update({'rs': 1,
                        'errmsg': error[1][1] % {'msg': msg},
                        'output': ''})
        return results

    def send_results(self, client, addr, results):
        """ send back results to client in the json format of:
        {'overallRC': x, 'modID': x, 'rc': x, 'rs': x, 'errmsg': 'msg',
         'output': 'out'}
        """
        json_results = json.dumps(results)
        json_results = json_results.encode()

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
            self.log_error("(%s:%s) Failed to send back results to client, "
                           "results: %s" % (addr[0], addr[1], json_results))
        else:
            self.log_debug("(%s:%s) Results sent back to client successfully."
                           % (addr[0], addr[1]))
    
    def _assert_within_rate_limit(self, client, addr):
        """
        Ensures that handling the request does not violate rate-limit
        specified configuration. It peeks the data from accepted clients socket, so that
        it is still available for processing the request later. If configuration value of
        smapi_rate_limit_window_size_seconds is less than or equal to 0, rate limit check
        would be bypassed. The check is done on the basis values specified in "smapi_rate_limit_per_window"
        in the configuration. The format for its value is "total:N1, FUNC1: N2, FUNC2: N3, ...".
        For example,
        [sdkserver]
        smapi_rate_limit_per_window = total:30, guests_get_nic_info:5, guest_get_info : 20 ...
        For all the available function names, refer zvmsdk.api.SDKAPI class

        Raises:
            _RateLimitReached: If the configured rate threshold is reached
        """
        
        if CONF.sdkserver.smapi_rate_limit_window_size_seconds <= 0:
            return
        
        data = client.recv(4096, socket.MSG_PEEK)
        data = bytes.decode(data)
        
        # Any error getting the data sent by client is an error condition
        # and SMAPI request won't be made in such cases. So, such cases
        # do not apply for rate limit check. Not logging any error message
        # as that would be logged during "recv" also.
        if not data:
            return
        
        api_data = json.loads(data)

        if not isinstance(api_data, list) or len(api_data) != 3:
            return

        # Check called API is supported by SDK
        (func_name, api_args, api_kwargs) = api_data
        current_window_num = int(time() / CONF.sdkserver.smapi_rate_limit_window_size_seconds)
        self.log_debug(f'Checking rate limit filter for {func_name}. Current window = {current_window_num}')
        counts = self.rate_window_records.get(current_window_num, {})
        if not counts:
            # Cleanup previously existing entries
            with self.rate_window_lock:
                self.rate_window_records = {
                    current_window_num: {
                        'total': 1,
                        func_name: 1
                    }
                }
        else:
            new_total = counts['total'] + 1
            new_func_name_count = counts.get('func_name', 0) + 1
            allowed_total = int(self.rate_limit_config.get('total', constants.SMAPI_RATE_LIMIT_DEFAULT_TOTAL))
            allowed_func_name_count = int(self.rate_limit_config.get(func_name, sys.maxsize))
            if new_total <= allowed_total and new_func_name_count <= allowed_func_name_count:
                self.log_debug(f'Request for {func_name} passes rate limit filter. New total = {new_total}, \
                    new {func_name} count = {new_func_name_count}')
                with self.rate_window_lock:
                    self.rate_window_records[current_window_num].update({
                        'total': new_total,
                        func_name: new_func_name_count
                    })
            else:
                self.log_warn(f'Request for {func_name} cannot be made as rate limit is reached. \
                    Current counts are: {self.rate_window_records}')
                raise _RateLimitReached(f'Request {func_name}({api_args}, {api_kwargs}) skipped as rate limit is reached')
    
    def _assert_within_outstanding_limit(self):
        """
        Ensures that number of transactions for which response is yet to be received does not
        exceed configured value (smapi_max_outstanding_requests). If configured value is less
        than or equal to 0, the outstanding limit check is bypassed.

        Raises:
            _MaxOutstandingLimitReached: If number of outstanding requests has reached the configured max value
        """
        if CONF.sdkserver.smapi_max_outstanding_requests <= 0:
            return
        
        self.log_debug(f'Checking outstanding limit. Max outstanding requests = {CONF.sdkserver.smapi_max_outstanding_requests}')
        if self.outstanding_requests > CONF.sdkserver.smapi_max_outstanding_requests:
            raise _MaxOutstandingLimitReached(
                f'Max outstanding requests limit reached. Current outstanding = {self.outstanding_requests}')

    def serve_API(self, client, addr):
        """ Read client request and call target SDK API"""
        self.log_debug("(%s:%s) Handling new request from client." %
                       (addr[0], addr[1]))
        results = None
        api_request_made = False
        request_postponed = False
        try:
            self._assert_within_outstanding_limit()
            self._assert_within_rate_limit(client, addr)
            
            # The rate limit has passed, so clear the postponed requests entry for this connection
            # if present. This is for scenario in which request from client was postponed and now
            # it is tried again.
            self.postponed_requests.pop(f'{addr[0]}:{addr[1]}', None)
            
            data = client.recv(4096)
            data = bytes.decode(data)
            # When client failed to send the data or quit before sending the
            # data, server side would receive null data.
            # In such case, server would not send back any info and just
            # terminate this thread.
            if not data:
                self.log_warn("(%s:%s) Failed to receive data from client." %
                              (addr[0], addr[1]))
                return
            api_data = json.loads(data)

            # API_data should be in the form [funcname, args_list, kwargs_dict]
            if not isinstance(api_data, list) or len(api_data) != 3:
                msg = ("(%s:%s) SDK server got wrong input: '%s' from client."
                       % (addr[0], addr[1], data))
                results = self.construct_internal_error(msg)
                return

            # Check called API is supported by SDK
            (func_name, api_args, api_kwargs) = api_data
            
            self.log_debug("(%s:%s) Request func: %s, args: %s, kwargs: %s" %
                           (addr[0], addr[1], func_name, str(api_args),
                            str(api_kwargs)))
            try:
                api_func = getattr(self.sdkapi, func_name)
            except AttributeError:
                msg = ("(%s:%s) SDK server got wrong API name: %s from"
                       "client." % (addr[0], addr[1], func_name))
                results = self.construct_api_name_error(msg)
                return

            # invoke target API function
            with self.outstanding_counter_lock:
                self.outstanding_requests += 1
            api_request_made = True
            self.log_info(f'Requesting API for {func_name} ({api_args}, {api_kwargs})')
            return_data = api_func(*api_args, **api_kwargs)
        except (_RateLimitReached, _MaxOutstandingLimitReached) as e:
            request_postponed = True
            request_key = f'{addr[0]}:{addr[1]}'
            if request_key not in self.postponed_requests:
                self.postponed_requests[request_key] = int(time())
            elapsed_seconds = int(time()) - self.postponed_requests[request_key]
            if elapsed_seconds > CONF.sdkserver.smapi_request_postpone_threshold_seconds:
                self.postponed_requests.pop(request_key, None)
                request_postponed = False
                results = self.construct_internal_error(
                    f'Unable to process request as sdkserver is under heavy load. Waited for {elapsed_seconds} seconds')
            else:
                self.log_error(f'({addr[0]}:{addr[1]} {str(e)}). Limit reached, postponing the request.')
                # The sleep is necessary because there are other worker threads waiting on ".get" of request_queue.
                # If sleep is not added, it will immediately picked from the queue by any worker thread and
                # same rate limit condition would be met. Sleep for random duration is added so that postponed
                # requests are not attempted at once.
                sleep(randrange(1000, 3000) / 1000)
                self.request_queue.put((client, addr))
            
        except exception.SDKBaseException as e:
            self.log_error("(%s:%s) %s" % (addr[0], addr[1],
                                           traceback.format_exc()))
            # get the error info from exception attribute
            # All SDKbaseexception should eventually has a
            # results attribute defined which can be used by
            # sdkserver here
            if e.results is None:
                msg = ("(%s:%s) SDK server got exception without results "
                       "defined, error: %s" % (addr[0], addr[1],
                                               e.format_message()))
                results = self.construct_internal_error(msg)
            else:
                results = {'overallRC': e.results['overallRC'],
                           'modID': e.results['modID'],
                           'rc': e.results['rc'],
                           'rs': e.results['rs'],
                           'errmsg': e.format_message(),
                           'output': ''}
        except Exception as e:
            self.log_error("(%s:%s) %s" % (addr[0], addr[1],
                                           traceback.format_exc()))
            msg = ("(%s:%s) SDK server got unexpected exception: "
                   "%s" % (addr[0], addr[1], repr(e)))
            results = self.construct_internal_error(msg)
        else:
            if return_data is None:
                return_data = ''
            results = {'overallRC': 0, 'modID': None,
                       'rc': 0, 'rs': 0,
                       'errmsg': '',
                       'output': return_data}
        finally:
            if api_request_made:
                with self.outstanding_counter_lock:
                    self.outstanding_requests -= 1
        # Send back the final results
        try:
            if results is not None:
                self.send_results(client, addr, results)
        except Exception as e:
            # This should not happen in normal case.
            # A special case is the server side socket is closed/removed
            # before the send() action.
            self.log_error("(%s:%s) %s" % (addr[0], addr[1], repr(e)))
        finally:
            # If rate limit is exceeded, the request from client will be processed later.
            # So, let's not close the client connection in this case
            if not request_postponed:
                # Close the connection to make sure the thread socket got
                # closed even when it got unexpected exceptions.
                self.log_debug("(%s:%s) Finish handling request, closing "
                            "socket." % (addr[0], addr[1]))
                client.close()

    def worker_loop(self):
        # The worker thread would continuously fetch request from queue
        # in a while loop.
        while True:
            try:
                # This get() function raise Empty exception when there's no
                # available item in queue
                clt_socket, clt_addr = self.request_queue.get(block=False)
            except Queue.Empty:
                self.log_debug("No more item in request queue, worker will "
                               "exit now.")
                break
            except Exception as err:
                self.log_error("Failed to get request item from queue, error: "
                               "%s. Worker will exit now." % repr(err))
                break
            else:
                self.serve_API(clt_socket, clt_addr)
                self.request_queue.task_done()

    def setup(self):
        # create server socket
        try:
            self.server_socket = socket.socket(socket.AF_INET,
                                               socket.SOCK_STREAM)
        except socket.error as msg:
            self.log_error("Failed to create SDK server socket: %s" % msg)
            sys.exit(1)

        server_sock = self.server_socket
        # bind server address and port
        host = CONF.sdkserver.bind_addr
        port = CONF.sdkserver.bind_port
        try:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((host, port))
        except socket.error as msg:
            self.log_error("Failed to bind to (%s, %d), reason: %s" %
                             (host, port, msg))
            server_sock.close()
            sys.exit(1)

        # Start listening
        server_sock.listen(5)
        self.log_info("SDK server now listening")

    def run(self):
        # Keep running in a loop to handle client connections
        while True:
            # Wait client connection
            conn, addr = self.server_socket.accept()
            self.log_debug("(%s:%s) Client connected." % (addr[0],
                                                           addr[1]))
            # This put() function would be blocked here until there's
            # a slot in the queue
            self.request_queue.put((conn, addr))
            thread_count = threading.active_count()
            if thread_count <= CONF.sdkserver.max_worker_count:
                thread = threading.Thread(target=self.worker_loop)
                self.log_debug("Worker count: %d, starting new worker: %s" %
                               (thread_count - 1, thread.name))
                thread.start()


def start_daemon():
    server = SDKServer()
    try:
        server.setup()
        server.run()
    except Exception as err:
        LOG.error("sdkserver caught exception: %s", err)
    finally:
        # This finally won't catch exceptions from child thread, so
        # the close here is safe.
        LOG.error("SDK server now stop running unexpectedly")
        if server.server_socket is not None:
            server.log_info("Closing the server socket.")
            server.server_socket.close()


class _RateLimitReached(RuntimeError):
    pass


class _MaxOutstandingLimitReached(RuntimeError):
    pass
