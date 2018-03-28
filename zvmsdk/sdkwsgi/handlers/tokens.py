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

"""Handler for the root of the sdk API."""

import datetime
import functools
import jwt
import os
import threading

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk.sdkwsgi import util


CONF = config.CONF
LOG = log.LOG

DEFAULT_TOKEN_VALIDATION_PERIOD = 3600
TOKEN_LOCK = threading.Lock()


def get_admin_token(path):
    if os.path.exists(path):
        TOKEN_LOCK.acquire()
        try:
            with open(path, 'r') as fd:
                token = fd.read().strip()
        except Exception:
            LOG.debug('token file open failed.')
            raise exception.ZVMUnauthorized()
        finally:
            TOKEN_LOCK.release()
    else:
        LOG.debug('token configuration file not found.')
        raise exception.ZVMUnauthorized()
    return token


@util.SdkWsgify
def create(req):
    # Check if token validation closed
    if CONF.wsgi.auth.lower() == 'none':
        user_token = 'server-auth-closed'
        req.response.headers.add('X-Auth-Token', user_token)
        return req.response
    # Validation is open, so start to validate the admin-token
    if 'X-Admin-Token' not in req.headers:
        LOG.debug('no X-Admin-Token given in reqeust header')
        raise exception.ZVMUnauthorized()
    token_file_path = CONF.wsgi.token_path
    admin_token = get_admin_token(token_file_path)
    if (req.headers['X-Admin-Token'] != admin_token):
        LOG.debug('X-Admin-Token incorrect')
        raise exception.ZVMUnauthorized()

    expires = CONF.wsgi.token_validation_period
    if expires < 0:
        expires = DEFAULT_TOKEN_VALIDATION_PERIOD

    expired_elapse = datetime.timedelta(seconds=expires)
    expired_time = datetime.datetime.utcnow() + expired_elapse
    payload = {'exp': expired_time}
    user_token = jwt.encode(payload, admin_token)

    req.response.headers.add('X-Auth-Token', user_token)

    return req.response


# To validate the token, it is possible the token is expired or the
# token is not validated at all
def validate(function):
    @functools.wraps(function)
    def wrap_func(req, *args, **kwargs):

        # by default, no token validation used
        if CONF.wsgi.auth.lower() == 'none':
            return function(req, *args, **kwargs)

        # so, this is for token validation
        if 'X-Auth-Token' not in req.headers:
            LOG.debug('no X-Auth-Token given in reqeust header')
            raise exception.ZVMUnauthorized()

        token_file_path = CONF.wsgi.token_path
        admin_token = get_admin_token(token_file_path)
        try:
            jwt.decode(req.headers['X-Auth-Token'], admin_token)
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
