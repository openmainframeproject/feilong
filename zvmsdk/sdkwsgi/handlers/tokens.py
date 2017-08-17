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

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.sdkwsgi import wsgi_wrapper


CONF = config.CONF
LOG = log.LOG

DEFAULT_TOKEN_VALIDATION_PERIOD = 30


@wsgi_wrapper.SdkWsgify
def create(req):
    if 'X-Auth-User' not in req.headers:
        LOG.debug('no X-Auth-User given in reqeust header')
        raise exception.ZVMUnauthorized()

    if (req.headers['X-Auth-User'] != CONF.wsgi.user or
        req.headers['X-Auth-Password'] != CONF.wsgi.password):
        LOG.debug('X-Auth-User or X-Auth-Password incorrect')
        raise exception.ZVMUnauthorized()

    expires = CONF.wsgi.token_validation_period
    if expires < 0:
        expires = DEFAULT_TOKEN_VALIDATION_PERIOD

    expired_elapse = datetime.timedelta(seconds=expires)
    expired_time = datetime.datetime.utcnow() + expired_elapse
    payload = jwt.encode({'exp': expired_time}, CONF.wsgi.password)

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
            raise exception.ZVMUnauthorized()

        try:
            jwt.decode(req.headers['X-Auth-Token'], CONF.wsgi.password)
        except jwt.ExpiredSignatureError:
            LOG.debug('token validation failed because it is expired')
            raise exception.ZVMUnauthorized()
        except jwt.DecodeError:
            LOG.debug('token not valid')
            raise exception.ZVMUnauthorized()
        except Exception:
            LOG.debug('unknown exception occur during token validation')
            raise exception.ZVMUnauthorized()

        return function(req, *args, **kwargs)
    return wrap_func
