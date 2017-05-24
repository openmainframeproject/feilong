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

from zvmsdk import api as sdkapi
from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import guest
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper

_VMACTION = None
_VMHANDLER = None
CONF = config.CONF
LOG = log.LOG


class VMHandler(object):
    def list(self):
        LOG.info('list guests')

    @validation.schema(guest.create)
    def create(self, body):
        LOG.info('create guest')

    def get_info(self, id):
        LOG.info('guest get info %s', id)

    def get_power_state(self, id):
        LOG.info('guest get power %s', id)

    def delete(self, id):
        LOG.info('guest delete %s', id)

    def get_nic_info(self, id):
        LOG.info('guest get nic info %s', id)

    @validation.schema(guest.create_nic)
    def create_nic(self, id, body=None):
        LOG.info('create nic for %s', id)

    @validation.schema(guest.couple_uncouple_nic)
    def couple_uncouple_nic(self, id, body=None):
        LOG.info('couple uncouple nic %s', id)
        info = body['info']
        api = sdkapi.SDKAPI()

        persist = info.get('persist', True)
        persist = util.bool_from_string(persist, strict=True)

        couple = util.bool_from_string(info['couple'], strict=True)

        if couple:
            api.guest_nic_couple_to_vswitch(info['vswitch'],
                info['port'], id, persist=persist)
        else:
            api.guest_nic_uncouple_from_vswitch(info['vswitch'],
                info['port'], id, persist=persist)


class VMAction(object):
    def start(self, id):
        LOG.info('start guest %s', id)

    def stop(self, id):
        LOG.info('stop guest %s', id)

    def pause(self, id):
        LOG.info('pause guest %s', id)

    def unpause(self, id):
        LOG.info('unpause guest %s', id)

    def get_conole_output(self, id):
        LOG.info('get console %s', id)


def get_action():
    global _VMACTION
    if _VMACTION is None:
        _VMACTION = VMAction()
    return _VMACTION


def get_handler():
    global _VMHANDLER
    if _VMHANDLER is None:
        _VMHANDLER = VMHandler()
    return _VMHANDLER


@wsgi_wrapper.SdkWsgify
def guest_list(req):
    tokens.validate(req)

    def _guest_list(req):
        action = get_handler()
        action.list()

    _guest_list(req)


@wsgi_wrapper.SdkWsgify
def guest_get_info(req):
    tokens.validate(req)

    def _guest_get_info(uuid):
        action = get_handler()
        action.get_info(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_info(uuid)


@wsgi_wrapper.SdkWsgify
def guest_get_power_state(req):
    tokens.validate(req)

    def _guest_get_power_state(uuid):
        action = get_handler()
        action.get_power_state(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_power_state(uuid)


@wsgi_wrapper.SdkWsgify
def guest_create(req):
    tokens.validate(req)

    def _guest_create(req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.create(body=body)

    _guest_create(req)


@wsgi_wrapper.SdkWsgify
def guest_action(req):
    tokens.validate(req)

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


@wsgi_wrapper.SdkWsgify
def guest_delete(req):
    tokens.validate(req)

    def _guest_delete(uuid):
        action = get_handler()
        action.delete(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_delete(uuid)


@wsgi_wrapper.SdkWsgify
def guest_get_nic_info(req):
    tokens.validate(req)

    def _guest_get_nic_info(uuid):
        action = get_handler()
        action.get_nic_info(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_nic_info(uuid)


@wsgi_wrapper.SdkWsgify
def guest_create_nic(req):
    tokens.validate(req)

    def _guest_create_nic(uuid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.create_nic(uuid, body=body)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_create_nic(uuid, req)


@wsgi_wrapper.SdkWsgify
def guest_couple_uncouple_nic(req):
    tokens.validate(req)

    def _guest_couple_uncouple_nic(uuid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.couple_uncouple_nic(uuid, body=body)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_couple_uncouple_nic(uuid, req)
