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
"""Handler for the root of the sdk API."""

import datetime
import functools
import jwt
import webob.exc


from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import config
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG

DEFAULT_TOKEN_VALIDATION_PERIOD = 30


@wsgi_wrapper.SdkWsgify
def create(req):
    expires = CONF.wsgi.token_validation_period
    if expires < 0:
        expires = DEFAULT_TOKEN_VALIDATION_PERIOD

    expired_elapse = datetime.timedelta(seconds=expires)
    expired_time = datetime.datetime.utcnow() + expired_elapse
    payload = jwt.encode({'exp': expired_time}, 'username')

    req.response.headers.add('X-Auth-Token', payload)

    return req.response


# To validate the token, it is possible the token is expired or the
# token is not validated at all
def validate(function):
    @functools.wraps(function)
    def wrap_func(req, *args, **kwargs):

        # by default, no token validation used
        if CONF.wsgi.auth == 'none':
            return function(req, *args, **kwargs)

        # so, this is for token validation
        if 'X-Auth-Token' not in req.headers:
            LOG.debug('no X-Auth-Token given in reqeust header')
            raise webob.exc.HTTPUnauthorized()

        try:
            jwt.decode(req.headers['X-Auth-Token'], 'username')
        except jwt.ExpiredSignatureError:
            LOG.debug('token validation failed because it is expired')
            raise webob.exc.HTTPUnauthorized()
        except jwt.DecodeError:
            LOG.debug('token not valid')
            raise webob.exc.HTTPUnauthorized()
        except Exception:
            LOG.debug('unknown exception occur during token validation')
            raise webob.exc.HTTPUnauthorized()

        return function(req, *args, **kwargs)
    return wrap_func
