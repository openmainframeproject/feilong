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
"""Handlers for sdk API.

Individual handlers are associated with URL paths in the
ROUTE_DECLARATIONS dictionary. At the top level each key is a Routes
compliant path. The value of that key is a dictionary mapping
individual HTTP request methods to a Python function representing a
simple WSGI application for satisfying that request.

The ``make_map`` method processes ROUTE_DECLARATIONS to create a
Routes.Mapper, including automatic handlers to respond with a
405 when a request is made against a valid URL with an invalid
method.
"""

import routes
import webob

from zvmsdk import exception
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi.handlers import root
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.handlers import vm


# When adding URLs here, do not use regex patterns in
# the path parameters (e.g. {uuid:[0-9a-zA-Z-]+}) as that will lead
# to 404s that are controlled outside of the individual resources
# and thus do not include specific information on the why of the 404.
ROUTE_DECLARATIONS = {
    '/': {
        'GET': root.home,
    },
    '/token': {
        'POST': tokens.create,
    },
    '/vm': {
        'GET': vm.list_vm,
    },
    '/vm/{uuid}/action': {
        'POST': vm.action,
    }
}


def dispatch(environ, start_response, mapper):
    """Find a matching route for the current request.

    If no match is found, raise a 404 response.
    If there is a matching route, but no matching handler
    for the given method, raise a 405.
    """
    result = mapper.match(environ=environ)
    if result is None:
        raise webob.exc.HTTPNotFound(
            json_formatter=util.json_error_formatter)
    # We can't reach this code without action being present.
    handler = result.pop('action')
    environ['wsgiorg.routing_args'] = ((), result)
    return handler(environ, start_response)


def handle_405(environ, start_response):
    """Return a 405 response when method is not allowed.

    If _methods are in routing_args, send an allow header listing
    the methods that are possible on the provided URL.
    """
    _methods = util.wsgi_path_item(environ, '_methods')
    headers = {}
    if _methods:
        # Ensure allow header is a python 2 or 3 native string (thus
        # not unicode in python 2 but stay a string in python 3)
        # In the process done by Routes to save the allowed methods
        # to its routing table they become unicode in py2.
        headers['allow'] = str(_methods)
    raise webob.exc.HTTPMethodNotAllowed(
        ('The method specified is not allowed for this resource.'),
        headers=headers, json_formatter=util.json_error_formatter)


def make_map(declarations):
    """Process route declarations to create a Route Mapper."""
    mapper = routes.Mapper()
    for route, targets in declarations.items():
        allowed_methods = []
        for method in targets:
            mapper.connect(route, action=targets[method],
                           conditions=dict(method=[method]))
            allowed_methods.append(method)
        allowed_methods = ', '.join(allowed_methods)
        mapper.connect(route, action=handle_405, _methods=allowed_methods)
    return mapper


class SdkHandler(object):
    """Serve sdk API.

    Dispatch to handlers defined in ROUTE_DECLARATIONS.
    """

    def __init__(self, **local_config):
        # NOTE(cdent): Local config currently unused.
        self._map = make_map(ROUTE_DECLARATIONS)

    def __call__(self, environ, start_response):
        # Check that an incoming request with a content-length header
        # that is an integer > 0 and not empty, also has a content-type
        # header that is not empty. If not raise a 400.
        clen = environ.get('CONTENT_LENGTH')
        try:
            if clen and (int(clen) > 0) and not environ.get('CONTENT_TYPE'):
                raise webob.exc.HTTPBadRequest(
                   ('content-type header required when content-length > 0'),
                   json_formatter=util.json_error_formatter)
        except ValueError as exc:
            raise webob.exc.HTTPBadRequest(
                ('content-length header must be an integer'),
                json_formatter=util.json_error_formatter)
        try:
            return dispatch(environ, start_response, self._map)
        # Trap the NotFound exceptions raised by the objects used
        # with the API and transform them into webob.exc.HTTPNotFound.
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(
                exc, json_formatter=util.json_error_formatter)
        # Trap the HTTPNotFound that can be raised by dispatch()
        # when no route is found. The exception is passed through to
        # the FaultWrap middleware without causing an alarming log
        # message.
        except webob.exc.HTTPNotFound:
            raise
        except Exception as exc:
            raise
