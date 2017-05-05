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
import jwt
import webob.exc


from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import api
from zvmsdk import config
from zvmsdk import log


TOKEN_EXPIRE_TIME = 30


@wsgi_wrapper.SdkWsgify
def create(req):
    expired_elapse = datetime.timedelta(seconds=TOKEN_EXPIRE_TIME)
    expired_time = datetime.datetime.utcnow() + expired_elapse
    payload = jwt.encode({'exp': expired_time}, 'username')

    req.response.headers.add('X-Auth-Token', payload)

    return req.response


# To validate the token, it is possible the token is expired or the
# token is not validated at all
def validate(req):
    if 'X-Auth-Token' not in req.headers:
        return webob.exc.HTTPUnauthorized()

    try:
        jwt.decode(token, 'username')
    except jwt.ExpiredSignatureError:
        LOG.debug('token validation failed because it is expired')
        return webob.exc.HTTPUnauthorized()
    except jwt.DecodeError:
        LOG.debug('token not valid')
        return webob.exc.HTTPUnauthorized()
    except Exception:
        LOG.debug('unknonw exception occur during token validation')
        return webob.exc.HTTPUnauthorized()
