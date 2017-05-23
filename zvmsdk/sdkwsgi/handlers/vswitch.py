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

from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper

_VSWITCHACTION = None
CONF = config.CONF
LOG = log.LOG


class VswitchAction(object):
    def list(self):
        LOG.info('list vswitchs')

    @validation.schema(vswitch.create)
    def create(self, body):
        LOG.info('create vswitch')


def get_action():
    global _VSWITCHACTION
    if _VSWITCHACTION is None:
        _VSWITCHACTION = VswitchAction()
    return _VSWITCHACTION


@wsgi_wrapper.SdkWsgify
def vswitch_list(req):
    tokens.validate(req)

    def _vswitch_list(req):
        action = get_action()
        action.list()

    _vswitch_list(req)


@wsgi_wrapper.SdkWsgify
def vswitch_create(req):
    tokens.validate(req)

    def _vswitch_create(req):
        action = get_action()
        body = util.extract_json(req.body)

        action.create(body=body)

    _vswitch_create(req)
