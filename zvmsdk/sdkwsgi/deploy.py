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

import webob

from zvmsdk.sdkwsgi import handler
from zvmsdk.sdkwsgi import microversion
from zvmsdk.sdkwsgi import requestlog


NAME = "sdk"


def walk_class_hierarchy(clazz, encountered=None):
    """Walk class hierarchy, yielding most derived classes first."""
    if not encountered:
        encountered = []
    for subclass in clazz.__subclasses__():
        if subclass not in encountered:
            encountered.append(subclass)
            # drill down to leaves first
            for subsubclass in walk_class_hierarchy(subclass, encountered):
                yield subsubclass
            yield subclass


class FaultWrapper(object):
    """Calls down the middleware stack, making exceptions into faults."""

    _status_to_type = {}

    @staticmethod
    def status_to_type(status):
        if not FaultWrapper._status_to_type:
            for clazz in walk_class_hierarchy(webob.exc.HTTPError):
                FaultWrapper._status_to_type[clazz.code] = clazz
        return FaultWrapper._status_to_type.get(
                                  status, webob.exc.HTTPInternalServerError)()

    def __init__(self, application):
        self.application = application

    def _error(self, inner, req):

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
                                            inner.msg)

        return outer

    @webob.dec.wsgify()
    def __call__(self, req):
        try:
            return req.get_response(self.application)
        except Exception as ex:
            return self._error(ex, req)


def deploy(project_name):
    """Assemble the middleware pipeline leading to the placement app."""
    microversion_middleware = microversion.MicroversionMiddleware
    request_log = requestlog.RequestLog
    fault_wrap = FaultWrapper
    application = handler.SdkHandler()

    for middleware in (fault_wrap,
                       microversion_middleware,
                       request_log,
                       ):
        if middleware:
            application = middleware(application)

    return application


def loadapp(project_name=NAME):
    application = deploy(project_name)
    return application
