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

import webob.exc

from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk.sdkwsgi import util

_VMACTION = None
CONF = config.CONF
LOG = log.LOG


class VMAction(object):
    def start(self, id):
        LOG.info('start vm %s', id)

    def list(self):
        LOG.info('list vms')

    def stop(self, id):
        LOG.info('stop vm %s', id)

    def pause(self, id):
        LOG.info('pause vm %s', id)

    def unpause(self, id):
        LOG.info('unpause vm %s', id)


def get_action():
    global _VMACTION
    if _VMACTION is None:
        _VMACTION = VMAction()
    return _VMACTION


@wsgi_wrapper.SdkWsgify
def guest_list(req):

    # @tokens.validate(req)
    def _guest_list(req):
        action = get_action()
        action.list()

    _guest_list(req)


@wsgi_wrapper.SdkWsgify
def guest_action(req):
    # @tokens.validate(req)
    def _guest_action(uuid, req):
        action = get_action()
        data = util.extract_json(req.body)
        for method, parm in data.items():
            func = getattr(action, method, None)
            if func:
                func(uuid)
            else:
                LOG.info('action %s is invalid', method)
                raise webob.exc.HTTPBadRequest()

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_action(uuid, req)
