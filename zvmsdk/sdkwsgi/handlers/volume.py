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

from zvmsdk import api
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper


_VOLUMEACTION = None
LOG = log.LOG


class VolumeAction(object):
    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)

    def attach(self, userid, body):
        info = body['info']
        guest = {'guest': {'os_type': info['os_type'],
                           'name': userid}}
        volume = info['volume']
        connection = info['connection']
        rollback = info['rollback']

        self.api.volume_attach(guest, volume, connection,
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

        self.api.volume_detach(guest, volume, connection,
                               is_rollback_in_failure=rollback)


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
        action.attach(userid, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _volume_attach(userid, req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def volume_detach(req):

    def _volume_detach(userid, req):
        action = get_action()
        body = util.extract_json(req.body)
        action.detach(userid, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _volume_detach(userid, req)
