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

import json

from zvmconnector import connector
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VOLUMEACTION = None
LOG = log.LOG


class VolumeAction(object):
    def __init__(self):
        self.client = connector.ZVMConnector()

    def attach(self, userid, body):
        info = body['info']
        guest = {'guest': {'os_type': info['os_type'],
                           'name': userid}}
        volume = info['volume']
        connection = info['connection']
        rollback = info['rollback']

        info = self.client.send_request('volume_attach', guest, volume,
                                        connection,
                                        is_rollback_in_failure=rollback)

        return info

    @validation.schema(vswitch.create)
    def detach(self, userid, body):
        info = body['info']
        guest = {'guest': {'os_type': info['os_type'],
                           'name': userid}}
        volume = info['volume']
        connection = info['connection']
        rollback = info['rollback']

        info = self.client.send_request('volume_detach', guest, volume,
                                        connection,
                                        is_rollback_in_failure=rollback)

        return info


def get_action():
    global _VOLUMEACTION
    if _VOLUMEACTION is None:
        _VOLUMEACTION = VolumeAction()
    return _VOLUMEACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def volume_attach(req):

    def _volume_attach(userid, req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.attach(userid, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _volume_attach(userid, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def volume_detach(req):

    def _volume_detach(userid, req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.detach(userid, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _volume_detach(userid, req)
    info_json = json.dumps(info)

    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response
