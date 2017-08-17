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


LOG = log.LOG


class RequestLog(object):
    """WSGI Middleware to write a simple request log to.

    Borrowed from Paste Translogger
    """

    format = ('%(REMOTE_ADDR)s "%(REQUEST_METHOD)s %(REQUEST_URI)s" '
              'status: %(status)s len: %(bytes)s ')

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        LOG.debug('Starting request: %s "%s %s"',
                  environ['REMOTE_ADDR'], environ['REQUEST_METHOD'],
                   self._get_uri(environ))
        if LOG.isEnabledFor(logging.INFO):
            return self._log_app(environ, start_response)
        else:
            return self.application(environ, start_response)

    @staticmethod
    def _get_uri(environ):
        name = environ.get('SCRIPT_NAME', '')
        info = environ.get('PATH_INFO', '')
        req_uri = name + info
        if environ.get('QUERY_STRING'):
            req_uri += '?' + environ['QUERY_STRING']
        return req_uri

    def _log_app(self, environ, start_response):
        req_uri = self._get_uri(environ)

        def _start_response(status, headers, exc_info=None):
            """We need to gaze at the content-length, if set, to
            write log info.
            """
            size = None
            for name, value in headers:
                if name.lower() == 'content-length':
                    size = value
            self.write_log(environ, req_uri, status, size)
            return start_response(status, headers, exc_info)

        return self.application(environ, _start_response)

    def write_log(self, environ, req_uri, status, size):
        """Write the log info out in a formatted form to ``LOG.info``.
        """
        if size is None:
            size = '-'
        log_format = {
                'REMOTE_ADDR': environ.get('REMOTE_ADDR', '-'),
                'REQUEST_METHOD': environ['REQUEST_METHOD'],
                'REQUEST_URI': req_uri,
                'status': status.split(None, 1)[0],
                'bytes': size,
        }
        LOG.info(self.format, log_format)
