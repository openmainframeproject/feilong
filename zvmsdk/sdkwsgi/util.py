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

import webob
from webob.dec import wsgify

from zvmsdk import log


LOG = log.LOG
SDKWSGI_MODID = 120


def extract_json(body):
    try:
        LOG.debug('Decoding body: %s', body)
        data = json.loads(body)
    except ValueError as exc:
        msg = ('Malformed JSON: %(error)s') % {'error': exc}
        LOG.debug(msg)
        raise webob.exc.HTTPBadRequest(msg,
            json_formatter=json_error_formatter)
    return data


def json_error_formatter(body, status, title, environ):
    """A json_formatter for webob exceptions."""
    body = webob.exc.strip_tags(body)
    status_code = int(status.split(None, 1)[0])
    error_dict = {
        'status': status_code,
        'title': title,
        'detail': body
    }
    return {'errors': [error_dict]}


def wsgi_path_item(environ, name):
    """Extract the value of a named field in a URL.

    Return None if the name is not present or there are no path items.
    """
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


def get_request_uri(environ):
    name = environ.get('SCRIPT_NAME', '')
    info = environ.get('PATH_INFO', '')
    req_uri = name + info
    if environ.get('QUERY_STRING'):
        req_uri += '?' + environ['QUERY_STRING']
    return req_uri


def get_http_code_from_sdk_return(msg, additional_handler=None, default=200):
    LOG.debug("Get msg to handle: %s", msg)

    if 'overallRC' in msg:
        ret = msg['overallRC']

        if ret != 0:
            # same definition to sdk layer
            if ret in [400, 404, 409, 501, 503]:
                return ret

            # 100 mean validation error in sdk layer and
            # lead to a 400 badrequest
            if ret in [100]:
                return 400

            # Add a special handle for smut return
            if additional_handler:
                ret = additional_handler(msg)
                if ret:
                    return ret

            # ok, we reach here because can't handle it
            LOG.info("The msg <%s> lead to return internal error", msg)
            return 500
        else:
            # return default code
            return default


def handle_not_found(msg):

    if 'overallRC' in msg and 'rc' in msg and 'rs' in msg:
        # overall rc: 8, rc: 212, rs: 40 means vswitch not exist
        if (msg['overallRC'] == 8 and msg['rc'] == 212 and
            msg['rs'] == 40):
            LOG.debug('vswitch does not exist, change ret to 404')
            return 404

        # overall rc: 4, rc: 5, rs: 402 means vswitch not exist
        if (msg['overallRC'] == 4 and msg['rc'] == 5 and
            msg['rs'] == 402):
            LOG.debug('disk pool not exist, change ret to 404')
            return 404

        # overall rc: 300, rc: 300, rs: 20 means image not exist
        if (msg['overallRC'] == 300 and msg['rc'] == 300 and
            msg['rs'] == 20):
            LOG.debug('image not exist, change ret to 404')
            return 404

        # overall rc: 8, rc: 400, rs: 4 means guest not exist
        if (msg['overallRC'] == 8 and msg['rc'] == 400 and
            msg['rs'] == 4):
            LOG.debug('guest not exist, change ret to 404')
            return 404

        # overall rc: 8, rc: 200, rs: 4 means guest not exist
        if (msg['overallRC'] == 8 and msg['rc'] == 200 and
            msg['rs'] == 4):
            LOG.debug('guest not exist, change ret to 404')
            return 404

        # overall rc: 300, rc:300, rs: 3, error message contains
        # "not linked; not in CP directory" means target vdev not exist
        if (msg['overallRC'] == 300 and msg['rc'] == 300 and
            msg['rs'] == 3 and 'not linked; not in CP directory' in
            msg['errmsg']):
            LOG.debug('deploy target vdev not exist,'
                      ' change ret to 404')
            return 404
    return 0


def handle_already_exists(msg):
    if 'overallRC' in msg and 'rc' in msg and 'rs' in msg:
        # overall rc: 8, rc: 212, rs: 36 means vswitch already exist
        if (msg['overallRC'] == 8 and msg['rc'] == 212 and
            msg['rs'] == 36):
            LOG.debug('vswitch already exist, change ret to 409')
            return 409

        # overall rc: 300, rc: 300, rc: 13 means image already exist
        if (msg['overallRC'] == 300 and msg['rc'] == 300 and
            msg['rs'] == 13):
            LOG.debug('image already exist, change ret to 409')
            return 409

        # overall rc: 8, rc: 400, rs: 8 means guest already exist
        if (msg['overallRC'] == 8 and msg['rc'] == 400 and
            msg['rs'] == 8):
            LOG.debug('guest already exist, change ret to 409')
            return 409

    # not handle it well, go to default
    return 0


class SdkWsgify(wsgify):

    def call_func(self, req, *args, **kwargs):
        """Add json_error_formatter to any webob HTTPExceptions."""
        try:
            return super(SdkWsgify, self).call_func(req, *args, **kwargs)
        except webob.exc.HTTPException as exc:
            msg = ('encounter %(error)s error') % {'error': exc}
            LOG.debug(msg)
            exc.json_formatter = json_error_formatter
            code = exc.status_int
            explanation = six.text_type(exc)

            fault_data = {
                'overallRC': 400,
                'rc': 400,
                'rs': code,
                'modID': SDKWSGI_MODID,
                'output': '',
                'errmsg': explanation}
            exc.text = six.text_type(json.dumps(fault_data))
            raise exc
