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
"""Utility methods for placement API."""

import functools
import json
import six

import webob

from zvmsdk import log


LOG = log.LOG


def loads(s, **kwargs):
    return json.loads(s, **kwargs)


def check_accept(*types):
    """If accept is set explicitly, try to follow it.

    If there is no match for the incoming accept header
    send a 406 response code.

    If accept is not set send our usual content-type in
    response.
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(req):
            if req.accept:
                best_match = req.accept.best_match(types)
                if not best_match:
                    type_string = ', '.join(types)
                    raise webob.exc.HTTPNotAcceptable(
                        ('Only %(type)s is provided') % {'type': type_string},
                        json_formatter=json_error_formatter)
            return f(req)
        return decorated_function
    return decorator


def extract_json(body):
    try:
        data = loads(body)
    except ValueError as exc:
        msg = ('Malformed JSON: %(error)s') % {'error': exc}
        LOG.debug(msg)
        raise webob.exc.HTTPBadRequest(msg,
            json_formatter=json_error_formatter)
    return data


def json_error_formatter(body, status, title, environ):
    """A json_formatter for webob exceptions."""
    # Clear out the html that webob sneaks in.
    body = webob.exc.strip_tags(body)
    # Get status code out of status message. webob's error formatter
    # only passes entire status string.
    status_code = int(status.split(None, 1)[0])
    error_dict = {
        'status': status_code,
        'title': title,
        'detail': body
    }
    # If the request id middleware has had a chance to add an id,
    # put it in the error response.

    return {'errors': [error_dict]}


def require_content(content_type):
    """Decorator to require a content type in a handler."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(req):
            if req.content_type != content_type:
                # webob's unset content_type is the empty string so
                # set it the error message content to 'None' to make
                # a useful message in that case. This also avoids a
                # KeyError raised when webob.exc eagerly fills in a
                # Template for output we will never use.
                if not req.content_type:
                    req.content_type = 'None'
                raise webob.exc.HTTPUnsupportedMediaType(
                    ('The media type %(bad_type)s is not supported, '
                      'use %(good_type)s') %
                    {'bad_type': req.content_type,
                     'good_type': content_type},
                    json_formatter=json_error_formatter)
            else:
                return f(req)
        return decorated_function
    return decorator


def wsgi_path_item(environ, name):
    """Extract the value of a named field in a URL.

    Return None if the name is not present or there are no path items.
    """
    # NOTE(cdent): For the time being we don't need to urldecode
    # the value as the entire placement API has paths that accept no
    # encoded values.
    try:
        return environ['wsgiorg.routing_args'][1][name]
    except (KeyError, IndexError):
        return None


TRUE_STRINGS = ('1', 't', 'true', 'on', 'y', 'yes')
FALSE_STRINGS = ('0', 'f', 'false', 'off', 'n', 'no')


def bool_from_string(subject, strict=False, default=False):
    if isinstance(subject, bool):
        return subject
    if not isinstance(subject, six.string_types):
        subject = six.text_type(subject)

    lowered = subject.strip().lower()

    if lowered in TRUE_STRINGS:
        return True
    elif lowered in FALSE_STRINGS:
        return False
    elif strict:
        acceptable = ', '.join(
            "'%s'" % s for s in sorted(TRUE_STRINGS + FALSE_STRINGS))
        msg = ("Unrecognized value '%(val)s', acceptable values are:"
               " %(acceptable)s") % {'val': subject,
                                     'acceptable': acceptable}
        raise ValueError(msg)
    else:
        return default
