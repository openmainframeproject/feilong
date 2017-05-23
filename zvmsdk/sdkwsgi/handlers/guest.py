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
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import guest
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper

_VMACTION = None
CONF = config.CONF
LOG = log.LOG


class VMAction(object):
    def start(self, id):
        LOG.info('start guest %s', id)

    def list(self):
        LOG.info('list guests')

    def stop(self, id):
        LOG.info('stop guest %s', id)

    def pause(self, id):
        LOG.info('pause guest %s', id)

    def unpause(self, id):
        LOG.info('unpause guest %s', id)

    @validation.schema(guest.create)
    def create(self, body):
        LOG.info('create guest')


def get_action():
    global _VMACTION
    if _VMACTION is None:
        _VMACTION = VMAction()
    return _VMACTION


@wsgi_wrapper.SdkWsgify
def guest_list(req):
    tokens.validate(req)

    def _guest_list(req):
        action = get_action()
        action.list()

    _guest_list(req)


@wsgi_wrapper.SdkWsgify
def guest_create(req):
    tokens.validate(req)

    def _guest_create(req):
        action = get_action()
        body = util.extract_json(req.body)

        action.create(body=body)

    _guest_create(req)


@wsgi_wrapper.SdkWsgify
def guest_action(req):

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
