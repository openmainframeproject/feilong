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

"""Deployment handling for sdk API."""

import json
import six
import sys
import traceback
import webob

from zvmsdk import log
from zvmsdk.sdkwsgi import handler
from zvmsdk.sdkwsgi import requestlog
from zvmsdk.sdkwsgi import util


LOG = log.LOG
NAME = "zvm-cloud-connector"


def _find_fault(clazz, encountered=None):
    if not encountered:
        encountered = []
    for subclass in clazz.__subclasses__():
        if subclass not in encountered:
            encountered.append(subclass)
            for subsubclass in _find_fault(subclass, encountered):
                yield subsubclass
            yield subclass


class Fault(webob.exc.HTTPException):

    def __init__(self, exception):
        self.wrapped_exc = exception
        for key, value in list(self.wrapped_exc.headers.items()):
            self.wrapped_exc.headers[key] = str(value)
        self.status_int = exception.status_int

    @webob.dec.wsgify()
    def __call__(self, req):

        code = self.wrapped_exc.status_int
        explanation = self.wrapped_exc.explanation
        LOG.debug("Returning %(code)s to user: %(explanation)s",
                  {'code': code, 'explanation': explanation})

        fault_data = {
                'overallRC': 400,
                'rc': 400,
                'rs': code,
                'modID': util.SDKWSGI_MODID,
                'output': '',
                'errmsg': explanation}
        if code == 413 or code == 429:
            retry = self.wrapped_exc.headers.get('Retry-After', None)
            if retry:
                fault_data['retryAfter'] = retry

        self.wrapped_exc.content_type = 'application/json'
        self.wrapped_exc.charset = 'UTF-8'
        self.wrapped_exc.text = six.text_type(json.dumps(fault_data))

        return self.wrapped_exc

    def __str__(self):
        return self.wrapped_exc.__str__()


class FaultWrapper(object):
    """Calls down the middleware stack, making exceptions into faults."""

    _status_to_type = {}

    @staticmethod
    def status_to_type(status):
        if not FaultWrapper._status_to_type:
            for clazz in _find_fault(webob.exc.HTTPError):
                FaultWrapper._status_to_type[clazz.code] = clazz
        return FaultWrapper._status_to_type.get(
                                  status, webob.exc.HTTPInternalServerError)()

    def __init__(self, application):
        self.application = application

    def _error(self, inner, req):
        exc_info = traceback.extract_tb(sys.exc_info()[2])[-1]
        LOG.info('Got unhandled exception: %s', exc_info)

        safe = getattr(inner, 'safe', False)
        headers = getattr(inner, 'headers', None)
        status = getattr(inner, 'code', 500)
        if status is None:
            status = 500

        outer = self.status_to_type(status)
        if headers:
            outer.headers = headers

        if safe:
            outer.explanation = '%s: %s' % (inner.__class__.__name__,
                                            inner.message)

        return Fault(outer)

    @webob.dec.wsgify()
    def __call__(self, req):
        try:
            return req.get_response(self.application)
        except Exception as ex:
            return self._error(ex, req)


class HeaderControl(object):

    def __init__(self, application):
        self.application = application

    @webob.dec.wsgify
    def __call__(self, req):

        response = req.get_response(self.application)
        response.headers.add('cache-control', 'no-cache')
        return response


def deploy(project_name):
    """Assemble the middleware pipeline"""
    request_log = requestlog.RequestLog
    header_addon = HeaderControl
    fault_wrapper = FaultWrapper
    application = handler.SdkHandler()

    # currently we have 3 middleware
    for middleware in (header_addon,
                       fault_wrapper,
                       request_log,
                       ):
        if middleware:
            application = middleware(application)

    return application


def loadapp(project_name=NAME):
    application = deploy(project_name)
    return application


def init_application():
    # build and return WSGI app
    return loadapp()
