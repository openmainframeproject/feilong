# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Simple middleware for request logging."""

import logging

from zvmsdk import log
from zvmsdk.sdkwsgi import util

LOG = log.LOG


class RequestLog(object):
    """WSGI Middleware to write a simple request log to.

    Borrowed from Paste Translogger
    """

    format = ('%(REMOTE_ADDR)s "%(REQUEST_METHOD)s %(REQUEST_URI)s" '
              'status: %(status)s length: %(bytes)s headers: %(headers)s '
              'exc_info: %(exc_info)s')

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        LOG.debug('Starting request: %s "%s %s"',
                  environ['REMOTE_ADDR'], environ['REQUEST_METHOD'],
                  util.get_request_uri(environ))
        return self._log_and_call(environ, start_response)

    def _log_and_call(self, environ, start_response):
        req_uri = util.get_request_uri(environ)

        def _local_response(status, headers, exc_info=None):
            size = None
            for name, value in headers:
                if name.lower() == 'content-length':
                    size = value

            self._write_log(environ, req_uri, status, size, headers,
                            exc_info)
            return start_response(status, headers, exc_info)

        return self.application(environ, _local_response)

    def _write_log(self, environ, req_uri, status, size, headers, exc_info):
        if size is None:
            size = '-'
        log_format = {
                'REMOTE_ADDR': environ.get('REMOTE_ADDR', '-'),
                'REQUEST_METHOD': environ['REQUEST_METHOD'],
                'REQUEST_URI': req_uri,
                'status': status.split(None, 1)[0],
                'bytes': size,
                'headers': headers,
                'exc_info': exc_info
        }
        if LOG.isEnabledFor(logging.INFO):
            LOG.info(self.format, log_format)
        else:
            LOG.debug(self.format, log_format)
