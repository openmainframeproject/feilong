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

    @validation.schema(guest.create)
    def create(self, body):
        guest = body['guest']

        userid = guest['userid']
        vcpus = guest['vcpus']
        memory = guest['memory']

        disk_list = guest.get('disk_list', None)
        user_profile = guest.get('user_profile', None)

        if user_profile is not None:
            self.api.guest_create(userid, vcpus, memory, disk_list=disk_list,
                                  user_profile=user_profile)
        else:
            self.api.guest_create(userid, vcpus, memory, disk_list=disk_list)

    def list(self):
        # list all guest on the given host
        guests = self.api.guest_list()
        return guests

    def get_info(self, userid):
        info = self.api.guest_get_info(userid)
        return info

    def get(self, userid):
        definition = self.api.guest_get_definition_info(userid)
        return definition

    def update(self, userid, body):
        pass

    def get_power_state(self, userid):
        state = self.api.guest_get_power_state(userid)
        return state

    def delete(self, userid):
        self.api.guest_delete(userid)

    def get_nic(self, userid):
        return self.api.guest_get_nic_vswitch_info(userid)

    def delete_nic(self, userid, vdev, body):
        active = body.get('vdev', False)

        self.api.guest_delete_nic(userid, vdev, active=active)

    def get_cpu_info(self, userid_list):
        return self.api.guest_inspect_cpus(userid_list)

    def get_memory_info(self, userid_list):
        return self.api.guest_inspect_mem(userid_list)

    def get_vnics_info(self, userid_list):
        return self.api.guest_inspect_vnics(userid_list)

    @validation.schema(guest.create_nic)
    def create_nic(self, userid, body=None):
        nic = body['nic']

        vdev = nic.get('vdev', None)
        nic_id = nic.get('nic_id', None)
        mac_addr = nic.get('mac_addr', None)
        ip_addr = nic.get('ip_addr', None)
        active = nic.get('active', False)

        self.api.guest_create_nic(userid, vdev=vdev, nic_id=nic_id,
            mac_addr=mac_addr, ip_addr=ip_addr, active=active)

    @validation.schema(guest.couple_uncouple_nic)
    def couple_uncouple_nic(self, userid, vdev, body):
        info = body['info']

        active = info.get('active', False)
        active = util.bool_from_string(active, strict=True)

        couple = util.bool_from_string(info['couple'], strict=True)

        if couple:
            self.api.guest_nic_couple_to_vswitch(userid,
                vdev, info['vswitch'], active=active)
        else:
            self.api.guest_nic_uncouple_from_vswitch(userid, vdev,
                                                     active=active)


class VMAction(object):
    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)

    def start(self, userid, data):
        try:
            self.api.guest_start(userid)
        except Exception:
            # FIXME: need to be specific on the exception handling
            LOG.info('failed to start %s', userid)

    def stop(self, userid, data):
        self.api.guest_stop(userid)

    def get_console_output(self, userid, data):
        self.api.guest_get_console_output(userid)

    # FIXME: add validation to the request
    # @validation.schema(guest.deploy)
    def deploy(self, userid, data):
        LOG.debug('start to deploy on %s', userid)

        userid = data['userid']
        image_name = data['image']

        transportfiles = data.get('transportfiles', None)
        remotehost = data.get('remotehost', None)
        vdev = data.get('vdev', None)

        self.api.guest_deploy(userid, image_name,
            transportfiles=transportfiles, remotehost=remotehost,
            vdev=vdev)


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

    def _guest_get_info(userid):
        action = get_handler()
        return action.get_info(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_get_info(userid)

    info_json = json.dumps({'info': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get(req):

    def _guest_get(userid):
        action = get_handler()
        return action.get(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_get(userid)

    info_json = json.dumps({'definition': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_power_state(req):

    def _guest_get_power_state(userid):
        action = get_handler()
        return action.get_power_state(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_get_power_state(userid)

    info_json = json.dumps({'power_state': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


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
def guest_update(req):

    def _guest_update(userid, body):
        action = get_handler()

        action.update(userid, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    body = util.extract_json(req.body)

    _guest_update(userid, body)


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

    def _guest_action(userid, req):
        action = get_action()
        data = util.extract_json(req.body)
        if len(data) == 0 or 'action' not in data:
            msg = 'action not exist or is empty'
            LOG.info(msg)
            raise webob.exc.HTTPBadRequest(explanation=msg)

        method = data['action']
        func = getattr(action, method, None)
        if func:
            func(userid, data)
        else:
            msg = 'action %s is invalid' % method
            raise webob.exc.HTTPBadRequest(msg)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _guest_action(userid, req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_delete(req):

    def _guest_delete(userid):
        action = get_handler()
        action.delete(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _guest_delete(userid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_nic_info(req):

    def _guest_get_nic_info(userid):
        action = get_handler()
        action.get_nic(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _guest_get_nic_info(userid)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_delete_nic(req):
    def _guest_delete_nic(userid, vdev, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.delete_nic(userid, vdev, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    vdev = util.wsgi_path_item(req.environ, 'vdev')

    _guest_delete_nic(userid, vdev, req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create_nic(req):

    def _guest_create_nic(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.create_nic(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    _guest_create_nic(userid, req)


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_couple_uncouple_nic(req):

    def _guest_couple_uncouple_nic(userid, vdev, req):
        action = get_handler()
        body = util.extract_json(req.body)

        action.couple_uncouple_nic(userid, vdev, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    vdev = util.wsgi_path_item(req.environ, 'vdev')

    _guest_couple_uncouple_nic(userid, vdev, req)


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
