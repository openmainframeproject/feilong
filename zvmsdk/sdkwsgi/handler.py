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

import routes
import webob

from zvmsdk import exception
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi.handlers import guest
from zvmsdk.sdkwsgi.handlers import host
from zvmsdk.sdkwsgi.handlers import image
from zvmsdk.sdkwsgi.handlers import root
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.handlers import vswitch

from zvmsdk import log
LOG = log.LOG


ROUTE_DECLARATIONS = {
    '/': {
        'GET': root.home,
    },
    '/guest': {
        'POST': guest.guest_create,
    },
    '/guest/{uuid}': {
        'DELETE': guest.guest_delete,
    },
    '/guest/{uuid}/nic': {
        'GET': guest.guest_get_nic_info,
        'POST': guest.guest_create_nic,
        'PUT': guest.guest_couple_uncouple_nic,
    },
    '/guest/{uuid}/info': {
        'GET': guest.guest_get_info,
    },
    '/guest/{uuid}/power_state': {
        'GET': guest.guest_get_power_state,
    },
    '/guest/{uuid}/action': {
        'POST': guest.guest_action,
    },
    '/host/guests': {
        'GET': host.host_list_guests,
    },
    '/host/info': {
        'GET': host.host_get_info,
    },
    '/host/disk_info/{disk}': {
        'GET': host.host_get_disk_info,
    },
    '/image': {
        'POST': image.image_create,
    },
    '/image/{name}': {
        'DELETE': image.image_delete,
    },
    '/image/{name}/root_disk_size': {
        'GET': image.image_get_root_disk_size,
    },
    '/token': {
        'POST': tokens.create,
    },
    '/vswitch': {
        'GET': vswitch.vswitch_list,
        'POST': vswitch.vswitch_create,
    },
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

    handler = result.pop('action')

    environ['wsgiorg.routing_args'] = ((), result)
    try:
        return handler(environ, start_response)
    except exception.ValidationError as exc:
        raise webob.exc.HTTPBadRequest(
            ('JSON does not validate: %(error)s') % {'error': exc})


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
        self._map = make_map(ROUTE_DECLARATIONS)

    def __call__(self, environ, start_response):
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
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(
                exc, json_formatter=util.json_error_formatter)
        except webob.exc.HTTPNotFound:
            raise
        except Exception as exc:
            raise
