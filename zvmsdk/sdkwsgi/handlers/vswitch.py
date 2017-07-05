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

from zvmsdk import api
from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VSWITCHACTION = None
CONF = config.CONF
LOG = log.LOG


class VswitchAction(object):
    def __init__(self):
        self.api = api.SDKAPI()

    def list(self):
        info = self.api.vswitch_get_list()

        return info

    @validation.schema(vswitch.create)
    def create(self, body):
        LOG.info('create vswitch')

    def delete(self, name):
        pass


def get_action():
    global _VSWITCHACTION
    if _VSWITCHACTION is None:
        _VSWITCHACTION = VswitchAction()
    return _VSWITCHACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_list(req):
    def _vswitch_list(req):
        action = get_action()
        return action.list()

    info = _vswitch_list(req)
    info_json = json.dumps({'vswlist': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_create(req):

    def _vswitch_create(req):
        action = get_action()
        body = util.extract_json(req.body)

        action.create(body=body)

    _vswitch_create(req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_delete(req):

    def _vswitch_delete(name):
        action = get_action()

        action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _vswitch_delete(name)
