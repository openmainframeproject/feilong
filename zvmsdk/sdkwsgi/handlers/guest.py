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
import webob.exc

from zvmsdk import api
from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import guest
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VMACTION = None
_VMHANDLER = None
CONF = config.CONF
LOG = log.LOG


class VMHandler(object):
    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)
        pass

    @validation.schema(guest.create)
    def create(self, body):
        guest = body['guest']

        userid = guest['userid']
        vcpus = guest['vcpus']
        memory = guest['memory']

        disk_list = guest.get('disk_list', None)
        user_profile = guest.get('user_profile', None)

        self.api.guest_create(userid, vcpus, memory, disk_list=disk_list,
                              user_profile=user_profile)

    @validation.schema(guest.deploy)
    def deploy(self, body):
        guest = body['guest']
        userid = guest['userid']
        image_name = guest['image_name']

        transportfiles = guest.get('transportfiles', None)
        remotehost = guest.get('remotehost', None)
        vdev = guest.get('vdev', None)

        self.api.guest_deploy(userid, image_name,
            transportfiles=transportfiles, remotehost=remotehost,
            vdev=vdev)

    def list(self):
        # list all guest on the given host
        guests = self.api.host_list_guests()
        return guests

    def get_info(self, id):
        LOG.info('guest get info %s', id)

    def get(self, id):
        LOG.info('get definition %s', id)

    def update(self, id, body):
        pass

    def get_power_state(self, id):
        LOG.info('guest get power %s', id)

    def delete(self, id):
        LOG.info('guest delete %s', id)

    def get_nic_info(self, id):
        LOG.info('guest get nic info %s', id)

    def get_cpu_info(self, userid_list):
        LOG.info('guest get cpu info %s', userid_list)

    def get_memory_info(self, userid_list):
        LOG.info('guest get memory info %s', userid_list)

    def get_vnics_info(self, userid_list):
        LOG.info('guest get vnics info %s', userid_list)

    @validation.schema(guest.create_nic)
    def create_nic(self, id, body=None):
        LOG.info('create nic for %s', id)

    @validation.schema(guest.couple_uncouple_nic)
    def couple_uncouple_nic(self, id, body=None):
        LOG.info('couple uncouple nic %s', id)
        info = body['info']

        persist = info.get('persist', True)
        persist = util.bool_from_string(persist, strict=True)

        couple = util.bool_from_string(info['couple'], strict=True)

        if couple:
            self.api.guest_nic_couple_to_vswitch(info['vswitch'],
                info['port'], id, persist=persist)
        else:
            self.api.guest_nic_uncouple_from_vswitch(info['vswitch'],
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
@tokens.validate
def guest_get_info(req):

    def _guest_get_info(uuid):
        action = get_handler()
        action.get_info(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_info(uuid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get(req):

    def _guest_get(uuid):
        action = get_handler()
        action.get(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get(uuid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_power_state(req):

    def _guest_get_power_state(uuid):
        action = get_handler()
        action.get_power_state(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_power_state(uuid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create(req):

    def _guest_create(req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.create(body=body)

    _guest_create(req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_deploy(req):

    def _guest_deploy(req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.deploy(body=body)

    _guest_deploy(req)

@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_update(req):

    def _guest_update(uuid, body):
        action = get_handler()

        action.update(uuid, body)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    body = util.extract_json(req.body)

    _guest_update(uuid, body)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_list(req):
    def _guest_list():
        action = get_handler()
        return action.list()

    info = _guest_list()
    info_json = json.dumps({'guests': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_action(req):

    def _guest_action(uuid, req):
        action = get_action()
        data = util.extract_json(req.body)
        if len(data) == 0:
            LOG.info('action is empty')
            raise webob.exc.HTTPBadRequest()

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
@tokens.validate
def guest_delete(req):

    def _guest_delete(uuid):
        action = get_handler()
        action.delete(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_delete(uuid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_nic_info(req):

    def _guest_get_nic_info(uuid):
        action = get_handler()
        action.get_nic_info(uuid)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_get_nic_info(uuid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create_nic(req):

    def _guest_create_nic(uuid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.create_nic(uuid, body=body)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_create_nic(uuid, req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_couple_uncouple_nic(req):

    def _guest_couple_uncouple_nic(uuid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.couple_uncouple_nic(uuid, body=body)

    uuid = util.wsgi_path_item(req.environ, 'uuid')
    _guest_couple_uncouple_nic(uuid, req)


def _get_userid_list(req):
    userids = []
    if 'userid' in req.GET.keys():
        userids = req.GET.getall('userid')

    return userids


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_cpu_info(req):

    userid_list = _get_userid_list(req)

    def _guest_get_cpu_info(userid_list):
        action = get_handler()
        action.get_cpu_info(userid_list)

    _guest_get_cpu_info(userid_list)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_memory_info(req):

    userid_list = _get_userid_list(req)

    def _guest_get_memory_info(userid_list):
        action = get_handler()
        action.get_memory_info(userid_list)

    _guest_get_memory_info(userid_list)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_vnics_info(req):

    userid_list = _get_userid_list(req)

    def _guest_get_vnics_info(userid_list):
        action = get_handler()
        action.get_vnics_info(userid_list)

    _guest_get_vnics_info(userid_list)
