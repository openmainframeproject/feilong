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
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import wsgi_wrapper


CONF = config.CONF
LOG = log.LOG


class VMAction(object):
    def start(self, id):
        LOG.info('start vm %s', id)


@wsgi_wrapper.SdkWsgify
def list_vm(req):
    @tokens.validate(req)
    def _list_vm(req)
        pass

    _list_vm(req)


@wsgi_wrapper.SdkWsgify
def action(req):
    @tokens.validate(req)
    def _action(uuid, req):
        vmaction = VMAction()
        data = util.extract_json(req.body)
        for method, parm in data.items():
            f = getattr(vmaction, method, None)
            if f:
                f(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _action(uuid, req)
