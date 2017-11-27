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

from zvmconnector import connector
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VSWITCHACTION = None
LOG = log.LOG


class VswitchAction(object):
    def __init__(self):
        self.client = connector.ZVMConnector()

    def list(self):
        return self.client.send_request('vswitch_get_list')

    @validation.schema(vswitch.create)
    def create(self, body):
        vsw = body['vswitch']
        name = vsw['name']
        rdev = vsw['rdev']

        controller = vsw.get('controller', '*')
        connection = vsw.get('connection', "CONNECT")
        network_type = vsw.get('network_type', "IP")
        router = vsw.get('router', "NONROUTER")
        vid = vsw.get('vid', "UNAWARE")
        port_type = vsw.get('port_type', "ACCESS")
        gvrp = vsw.get('gvrp', "GVRP")
        queue_mem = vsw.get('queue_mem', 8)
        native_vid = vsw.get('native_vid', 1)
        persist = vsw.get('persist', True)
        persist = util.bool_from_string(persist, strict=True)

        info = self.client.send_request('vswitch_create', name, rdev,
                                        controller=controller,
                                        connection=connection,
                                        network_type=network_type,
                                        router=router, vid=vid,
                                        port_type=port_type, gvrp=gvrp,
                                        queue_mem=queue_mem,
                                        native_vid=native_vid,
                                        persist=persist)
        return info

    def delete(self, name):
        info = self.client.send_request('vswitch_delete', name)
        return info

    @validation.schema(vswitch.update)
    def update(self, name, body):
        vsw = body['vswitch']
        # TODO: only allow one param at most once

        if 'grant_userid' in vsw:
            userid = vsw['grant_userid']
            info = self.client.send_request('vswitch_grant_user',
                                            name, userid)
            return info

        if 'revoke_userid' in vsw:
            userid = vsw['revoke_userid']
            info = self.client.send_request('vswitch_revoke_user',
                                            name, userid)
            return info

        if 'user_vlan_id' in vsw:
            userid = vsw['user_vlan_id']['userid']
            vlanid = vsw['user_vlan_id']['vlanid']
            info = self.client.send_request('vswitch_set_vlan_id_for_user',
                                            name, userid, vlanid)
            return info


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
    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_create(req):

    def _vswitch_create(req):
        action = get_action()
        body = util.extract_json(req.body)

        return action.create(body=body)

    info = _vswitch_create(req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_already_exists)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_delete(req):

    def _vswitch_delete(name):
        action = get_action()

        return action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    info = _vswitch_delete(name)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_update(req):

    def _vswitch_update(name, req):
        body = util.extract_json(req.body)
        action = get_action()

        return action.update(name, body=body)

    name = util.wsgi_path_item(req.environ, 'name')

    info = _vswitch_update(name, req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    return req.response
