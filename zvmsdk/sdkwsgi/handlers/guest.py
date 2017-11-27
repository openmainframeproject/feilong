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

from zvmconnector import connector
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import guest
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VMACTION = None
_VMHANDLER = None
LOG = log.LOG


class VMHandler(object):
    def __init__(self):
        self.client = connector.ZVMConnector()

    @validation.schema(guest.create)
    def create(self, body):
        guest = body['guest']

        userid = guest['userid']
        vcpus = guest['vcpus']
        memory = guest['memory']

        disk_list = guest.get('disk_list', None)
        user_profile = guest.get('user_profile', None)

        if user_profile is not None:
            info = self.client.send_request('guest_create', userid, vcpus,
                                            memory, disk_list=disk_list,
                                            user_profile=user_profile)
        else:
            info = self.client.send_request('guest_create', userid, vcpus,
                                            memory, disk_list=disk_list)

        return info

    def list(self):
        # list all guest on the given host
        info = self.client.send_request('guest_list')
        return info

    def get_info(self, userid):
        info = self.client.send_request('guest_get_info', userid)
        return info

    def get_definition_info(self, userid):
        info = self.client.send_request('guest_get_definition_info', userid)
        return info

    def get_power_state(self, userid):
        info = self.client.send_request('guest_get_power_state', userid)
        return info

    def delete(self, userid):
        info = self.client.send_request('guest_delete', userid)
        return info

    def get_nic_vswitch_info(self, userid):
        info = self.client.send_request('guest_get_nic_vswitch_info', userid)
        return info

    def delete_nic(self, userid, vdev, body):
        active = body.get('active', False)
        active = util.bool_from_string(active, strict=True)

        info = self.client.send_request('guest_delete_nic', userid, vdev,
                                        active=active)
        return info

    @validation.query_schema(guest.userid_list_query)
    def inspect_stats(self, req, userid_list):
        info = self.client.send_request('guest_inspect_stats',
                                        userid_list)
        return info

    @validation.query_schema(guest.userid_list_query)
    def inspect_vnics(self, req, userid_list):
        info = self.client.send_request('guest_inspect_vnics',
                                        userid_list)
        return info

    # @validation.query_schema(guest.nic_DB_info)
    # FIXME: the above validation will fail with "'dict' object has no
    # attribute 'dict_of_lists'"
    def get_nic_DB_info(self, req, userid=None, nic_id=None, vswitch=None):
        info = self.client.send_request('guests_get_nic_info', userid=userid,
                                        nic_id=nic_id, vswitch=vswitch)
        return info

    @validation.schema(guest.create_nic)
    def create_nic(self, userid, body=None):
        nic = body['nic']

        vdev = nic.get('vdev', None)
        nic_id = nic.get('nic_id', None)
        mac_addr = nic.get('mac_addr', None)
        active = nic.get('active', False)
        active = util.bool_from_string(active, strict=True)

        info = self.client.send_request('guest_create_nic', userid,
                                        vdev=vdev, nic_id=nic_id,
                                        mac_addr=mac_addr,
                                        active=active)
        return info

    @validation.schema(guest.create_network_interface)
    def create_network_interface(self, userid, body=None):
        interface = body['interface']
        version = interface['os_version']
        networks = interface.get('guest_networks', None)
        active = interface.get('active', False)
        active = util.bool_from_string(active, strict=True)
        info = self.client.send_request('guest_create_network_interface',
                                        userid, os_version=version,
                                        guest_networks=networks,
                                        active=active)
        return info

    @validation.schema(guest.create_disks)
    def create_disks(self, userid, body=None):
        disk_info = body['disk_info']
        disk_list = disk_info.get('disk_list', None)
        info = self.client.send_request('guest_create_disks', userid,
                                        disk_list)
        return info

    @validation.schema(guest.config_minidisks)
    def config_minidisks(self, userid, body=None):
        disk_info = body['disk_info']
        disk_list = disk_info.get('disk_list', None)
        info = self.client.send_request('guest_config_minidisks', userid,
                                        disk_list)
        return info

    @validation.schema(guest.delete_disks)
    def delete_disks(self, userid, body=None):
        vdev_info = body['vdev_info']
        vdev_list = vdev_info.get('vdev_list', None)

        info = self.client.send_request('guest_delete_disks', userid,
                                        vdev_list)

        return info

    @validation.schema(guest.nic_couple_uncouple)
    def nic_couple_uncouple(self, userid, vdev, body):
        info = body['info']

        active = info.get('active', False)
        active = util.bool_from_string(active, strict=True)

        couple = util.bool_from_string(info['couple'], strict=True)

        if couple:
            info = self.client.send_request('guest_nic_couple_to_vswitch',
                                            userid, vdev, info['vswitch'],
                                            active=active)
        else:
            info = self.client.send_request('guest_nic_uncouple_from_vswitch',
                                            userid, vdev,
                                            active=active)
        return info


class VMAction(object):
    def __init__(self):
        self.client = connector.ZVMConnector()

    def start(self, userid, body):
        info = self.client.send_request('guest_start', userid)

        return info

    @validation.schema(guest.stop)
    def stop(self, userid, body):
        timeout = body.get('timeout', None)
        poll_interval = body.get('poll_interval', None)

        info = self.client.send_request('guest_stop', userid,
                                        timeout=timeout,
                                        poll_interval=poll_interval)

        return info

    @validation.schema(guest.softstop)
    def softstop(self, userid, body):
        timeout = body.get('timeout', None)
        poll_interval = body.get('poll_interval', None)

        info = self.client.send_request('guest_softstop', userid,
                                        timeout=timeout,
                                        poll_interval=poll_interval)

        return info

    def pause(self, userid, body):
        info = self.client.send_request('guest_pause', userid)

        return info

    def unpause(self, userid, body):
        info = self.client.send_request('guest_unpause', userid)

        return info

    def reboot(self, userid, body):
        info = self.client.send_request('guest_reboot', userid)

        return info

    def reset(self, userid, body):
        info = self.client.send_request('guest_reset', userid)

        return info

    def get_console_output(self, userid, body):
        info = self.client.send_request('guest_get_console_output',
                                        userid)

        return info

    @validation.schema(guest.deploy)
    def deploy(self, userid, body):
        image_name = body['image']

        transportfiles = body.get('transportfiles', None)
        remotehost = body.get('remotehost', None)
        vdev = body.get('vdev', None)

        info = self.client.send_request('guest_deploy', userid,
                                        image_name,
                                        transportfiles=transportfiles,
                                        remotehost=remotehost,
                                        vdev=vdev)
        return info

    @validation.schema(guest.capture)
    def capture(self, userid, body):
        image_name = body['image']

        capture_type = body.get('capturetype', None)
        compress_level = body.get('compresslevel', None)

        info = self.client.send_request('guest_capture', userid,
                                        image_name,
                                        capture_type=capture_type,
                                    compress_level=compress_level)
        return info


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

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get(req):

    def _guest_get(userid):
        action = get_handler()
        return action.get_definition_info(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_get(userid)

    # info we got looks like:
    # {'user_direct': [u'USER RESTT305 PASSW0RD 1024m 1024m G',
    #                  u'INCLUDE OSDFLT']}
    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
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

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@util.expected_errors(400)
@tokens.validate
def guest_create(req):

    def _guest_create(req):
        action = get_handler()
        body = util.extract_json(req.body)

        return action.create(body=body)

    info = _guest_create(req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_already_exists)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_list(req):
    def _guest_list():
        action = get_handler()
        return action.list()

    info = _guest_list()
    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = 200
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_action(req):

    def _guest_action(userid, req):
        action = get_action()
        body = util.extract_json(req.body)
        if len(body) == 0 or 'action' not in body:
            msg = 'action not exist or is empty'
            LOG.info(msg)
            raise webob.exc.HTTPBadRequest(explanation=msg)

        method = body['action']
        func = getattr(action, method, None)
        if func:
            body.pop('action')
            return func(userid, body=body)
        else:
            msg = 'action %s is invalid' % method
            raise webob.exc.HTTPBadRequest(msg)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_action(userid, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_delete(req):

    def _guest_delete(userid):
        action = get_handler()
        return action.delete(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_delete(userid)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_nic_info(req):

    def _guest_get_nic_info(userid):
        action = get_handler()
        return action.get_nic_vswitch_info(userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_get_nic_info(userid)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_delete_nic(req):
    def _guest_delete_nic(userid, vdev, req):
        action = get_handler()
        body = util.extract_json(req.body)

        return action.delete_nic(userid, vdev, body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    vdev = util.wsgi_path_item(req.environ, 'vdev')

    info = _guest_delete_nic(userid, vdev, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create_nic(req):

    def _guest_create_nic(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        return action.create_nic(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_create_nic(userid, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_couple_uncouple_nic(req):

    def _guest_couple_uncouple_nic(userid, vdev, req):
        action = get_handler()
        body = util.extract_json(req.body)

        return action.nic_couple_uncouple(userid, vdev, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    vdev = util.wsgi_path_item(req.environ, 'vdev')

    info = _guest_couple_uncouple_nic(userid, vdev, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create_network_interface(req):

    def _guest_create_network_interface(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)

        return action.create_network_interface(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')
    info = _guest_create_network_interface(userid, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.content_type = 'application/json'
    return req.response


def _get_userid_list(req):
    userids = []
    if 'userid' in req.GET.keys():
        userid = req.GET.get('userid')

        userids = userid.split(',')

    return userids


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_stats(req):

    userid_list = _get_userid_list(req)

    def _guest_get_stats(req, userid_list):
        action = get_handler()
        return action.inspect_stats(req, userid_list)

    info = _guest_get_stats(req, userid_list)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_get_vnics_info(req):

    userid_list = _get_userid_list(req)

    def _guest_get_vnics_info(req, userid_list):
        action = get_handler()
        return action.inspect_vnics(req, userid_list)

    info = _guest_get_vnics_info(req, userid_list)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guests_get_nic_info(req):

    def _guests_get_nic_DB_info(req, userid=None, nic_id=None, vswitch=None):
        action = get_handler()
        return action.get_nic_DB_info(req, userid=userid, nic_id=nic_id,
                                      vswitch=vswitch)
    userid = req.GET.get('userid', None)
    nic_id = req.GET.get('nic_id', None)
    vswitch = req.GET.get('vswitch', None)

    info = _guests_get_nic_DB_info(req, userid=userid, nic_id=nic_id,
                                   vswitch=vswitch)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_config_disks(req):

    def _guest_config_minidisks(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)
        return action.config_minidisks(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')

    info = _guest_config_minidisks(userid, req)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_create_disks(req):

    def _guest_create_disks(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)
        return action.create_disks(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')

    info = _guest_create_disks(userid, req)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def guest_delete_disks(req):

    def _guest_delete_disks(userid, req):
        action = get_handler()
        body = util.extract_json(req.body)
        return action.delete_disks(userid, body=body)

    userid = util.wsgi_path_item(req.environ, 'userid')

    info = _guest_delete_disks(userid, req)

    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response
