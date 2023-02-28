#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2022 IBM Corp.
#
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
from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import volume
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk import utils


_VOLUMEACTION = None
CONF = config.CONF
LOG = log.LOG


class VolumeAction(object):
    def __init__(self):
        self.client = connector.ZVMConnector(connection_type='socket',
                                             ip_addr=CONF.sdkserver.bind_addr,
                                             port=CONF.sdkserver.bind_port)

    @validation.schema(volume.attach)
    def attach(self, body):
        info = body['info']
        connection = info['connection']

        info = self.client.send_request('volume_attach', connection)

        return info

    @validation.schema(volume.detach)
    def detach(self, body):
        info = body['info']
        connection = info['connection']

        info = self.client.send_request('volume_detach', connection)

        return info

    @validation.query_schema(volume.get_volume_connector)
    def get_volume_connector(self, req, userid, reserve, fcp_template_id,
                             sp_name):
        conn = self.client.send_request('get_volume_connector',
                                        userid, reserve, fcp_template_id,
                                        sp_name)
        return conn

    @validation.query_schema(volume.get_fcp_templates)
    def get_fcp_templates(self, req, template_id_list, assigner_id,
                          default_sp_list, host_default):
        return self.client.send_request('get_fcp_templates',
                                        template_id_list,
                                        assigner_id,
                                        default_sp_list,
                                        host_default)

    @validation.query_schema(volume.get_fcp_templates_details)
    def get_fcp_templates_details(self, req, template_id_list, raw,
                                  statistics, sync_with_zvm):
        return self.client.send_request('get_fcp_templates_details',
                                        template_id_list,
                                        raw=raw,
                                        statistics=statistics,
                                        sync_with_zvm=sync_with_zvm)

    def delete_fcp_template(self, template_id):
        return self.client.send_request('delete_fcp_template', template_id)

    @validation.query_schema(volume.get_fcp_usage)
    def get_fcp_usage(self, req, fcp):
        return self.client.send_request('get_fcp_usage', fcp)

    @validation.schema(volume.set_fcp_usage)
    def set_fcp_usage(self, fcp, body=None):
        userid = body['info']['userid']
        reserved = body['info']['reserved']
        connections = body['info']['connections']
        fcp_template_id = body['info']['fcp_template_id']
        if not fcp_template_id:
            fcp_template_id = ''
        return self.client.send_request('set_fcp_usage',
                                        fcp, userid, reserved,
                                        connections, fcp_template_id)

    def volume_refresh_bootmap(self, fcpchannel, wwpn, lun, wwid,
                               transportfiles, guest_networks, fcp_template_id):
        info = self.client.send_request('volume_refresh_bootmap',
                                        fcpchannel, wwpn, lun, wwid,
                                        transportfiles, guest_networks, fcp_template_id)
        return info

    @validation.schema(volume.create_fcp_template)
    def create_fcp_template(self, body=None):
        name = body.get('name')
        description = body.get('description', '')
        fcp_devices = body.get('fcp_devices', '')
        host_default = body.get('host_default', False)
        min_fcp_paths_count = body.get('min_fcp_paths_count', None)
        # ensure host_default parameter is boolean type
        # because of the sqlite FCP database's requirements
        valid_true_values = [True, 'True', 'TRUE', 'true', '1',
                             'ON', 'On', 'on', 'YES', 'Yes', 'yes']
        if host_default in valid_true_values:
            host_default = True
        else:
            host_default = False
        default_sp_list = body.get('storage_providers', [])

        ret = self.client.send_request('create_fcp_template', name,
                                       description=description,
                                       fcp_devices=fcp_devices,
                                       host_default=host_default,
                                       default_sp_list=default_sp_list,
                                       min_fcp_paths_count=min_fcp_paths_count)
        return ret

    @validation.schema(volume.edit_fcp_template)
    def edit_fcp_template(self, body=None):
        fcp_template_id = body.get('fcp_template_id')
        name = body.get('name', None)
        description = body.get('description', None)
        fcp_devices = body.get('fcp_devices', None)
        default_sp_list = body.get('storage_providers', None)
        min_fcp_paths_count = body.get('min_fcp_paths_count', None)
        # Due to the pre-validation in schemas/volume.py,
        # host_default only has 2 possible value types:
        # i.e. None or a value defined in parameter_types.boolean
        host_default = body.get('host_default', None)
        # ensure host_default parameter is boolean type
        # because of the sqlite FCP database's requirements
        valid_true_values = [True, 'True', 'TRUE', 'true', '1',
                             'ON', 'On', 'on', 'YES', 'Yes', 'yes']
        if host_default in valid_true_values:
            host_default = True
        elif host_default is not None:
            host_default = False
        ret = self.client.send_request('edit_fcp_template',
                                       fcp_template_id,
                                       name=name, description=description,
                                       fcp_devices=fcp_devices,
                                       host_default=host_default,
                                       default_sp_list=default_sp_list,
                                       min_fcp_paths_count=min_fcp_paths_count)
        return ret


def get_action():
    global _VOLUMEACTION
    if _VOLUMEACTION is None:
        _VOLUMEACTION = VolumeAction()
    return _VOLUMEACTION


@util.SdkWsgify
@tokens.validate
def volume_attach(req):

    def _volume_attach(req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.attach(body=body)

    info = _volume_attach(req)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response


@util.SdkWsgify
@tokens.validate
def volume_detach(req):

    def _volume_detach(req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.detach(body=body)

    info = _volume_detach(req)
    info_json = json.dumps(info)

    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response


@util.SdkWsgify
@tokens.validate
def volume_refresh_bootmap(req):

    def _volume_refresh_bootmap(req, fcpchannel, wwpn, lun, wwid,
                                transportfiles, guest_networks, fcp_template_id):
        action = get_action()
        return action.volume_refresh_bootmap(fcpchannel, wwpn, lun, wwid,
                                             transportfiles, guest_networks, fcp_template_id)

    body = util.extract_json(req.body)
    info = _volume_refresh_bootmap(req, body['info']['fcpchannel'],
                                   body['info']['wwpn'], body['info']['lun'],
                                   body['info'].get('wwid', ""),
                                   body['info'].get('transportfiles', ""),
                                   body['info'].get('guest_networks', []),
                                   body['info'].get('fcp_template_id', None))
    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response


@util.SdkWsgify
@tokens.validate
def get_volume_connector(req):
    def _get_volume_conn(req, userid, reserve, fcp_template_id, sp_name):
        action = get_action()
        return action.get_volume_connector(req, userid, reserve,
                                           fcp_template_id, sp_name)

    userid = util.wsgi_path_item(req.environ, 'userid')
    body = util.extract_json(req.body)
    reserve = body['info']['reserve']
    fcp_template_id = body['info'].get('fcp_template_id', None)
    sp_name = body['info'].get('storage_provider', None)
    conn = _get_volume_conn(req, userid, reserve, fcp_template_id, sp_name)
    conn_json = json.dumps(conn)

    req.response.content_type = 'application/json'
    req.response.body = utils.to_utf8(conn_json)
    req.response.status = util.get_http_code_from_sdk_return(conn, default=200)
    return req.response


@util.SdkWsgify
@tokens.validate
def get_fcp_usage(req):
    def _get_fcp_usage(req, fcp):
        action = get_action()
        return action.get_fcp_usage(req, fcp)

    fcp = util.wsgi_path_item(req.environ, 'fcp_id')
    ret = _get_fcp_usage(req, fcp)

    ret_json = json.dumps(ret)
    req.response.status = util.get_http_code_from_sdk_return(ret,
                    additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    req.response.body = utils.to_utf8(ret_json)
    return req.response


@util.SdkWsgify
@tokens.validate
def set_fcp_usage(req):
    def _set_fcp_usage(req, fcp):
        action = get_action()
        body = util.extract_json(req.body)
        return action.set_fcp_usage(fcp, body=body)
    fcp = util.wsgi_path_item(req.environ, 'fcp_id')

    ret = _set_fcp_usage(req, fcp)
    ret_json = json.dumps(ret)
    req.response.body = utils.to_utf8(ret_json)
    req.response.content_type = 'application/json'
    req.response.status = 200
    return req.response


@util.SdkWsgify
@tokens.validate
def create_fcp_template(req):
    def _create_fcp_template(req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.create_fcp_template(body=body)

    ret = _create_fcp_template(req)
    ret_json = json.dumps(ret)
    req.response.body = utils.to_utf8(ret_json)
    req.response.status = util.get_http_code_from_sdk_return(ret)
    req.response.content_type = 'application/json'


@util.SdkWsgify
@tokens.validate
def edit_fcp_template(req):
    def _edit_fcp_template(req_body):
        action = get_action()
        return action.edit_fcp_template(body=req_body)

    body = util.extract_json(req.body)
    body['fcp_template_id'] = util.wsgi_path_item(req.environ, 'template_id')
    ret = _edit_fcp_template(body)
    ret_json = json.dumps(ret)
    req.response.body = utils.to_utf8(ret_json)
    req.response.status = util.get_http_code_from_sdk_return(ret)
    req.response.content_type = 'application/json'


@util.SdkWsgify
@tokens.validate
def get_fcp_templates(req):
    def _get_fcp_templates(req, template_id_list, assigner_id,
                           default_sp_list, host_default):
        action = get_action()
        return action.get_fcp_templates(req, template_id_list, assigner_id,
                                        default_sp_list, host_default)

    template_id_list = req.GET.get('template_id_list', None)
    assigner_id = req.GET.get('assigner_id', None)
    default_sp_list = req.GET.get('storage_providers', None)
    host_default = req.GET.get('host_default', None)

    valid_true_values = [True, 'True', 'TRUE', 'true', '1',
                        'ON', 'On', 'on', 'YES', 'Yes', 'yes']
    if host_default:
        if host_default in valid_true_values:
            host_default = True
        else:
            host_default = False

    ret = _get_fcp_templates(req, template_id_list, assigner_id,
                             default_sp_list, host_default)

    ret_json = json.dumps(ret)
    req.response.status = util.get_http_code_from_sdk_return(
        ret, additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    req.response.body = utils.to_utf8(ret_json)
    return req.response


@util.SdkWsgify
@tokens.validate
def get_fcp_templates_details(req):
    def _get_fcp_templates_details(req, template_id_list, raw, statistics,
                                   sync_with_zvm):
        action = get_action()
        return action.get_fcp_templates_details(req, template_id_list, raw,
                                                statistics, sync_with_zvm)

    template_id_list = req.GET.get('template_id_list', None)

    raw = req.GET.get('raw', 'false')
    if raw.lower() == 'true':
        raw = True
    else:
        raw = False

    statistics = req.GET.get('statistics', 'true')
    if statistics.lower() == 'true':
        statistics = True
    else:
        statistics = False

    sync_with_zvm = req.GET.get('sync_with_zvm', 'false')
    if sync_with_zvm.lower() == 'true':
        sync_with_zvm = True
    else:
        sync_with_zvm = False
    ret = _get_fcp_templates_details(req, template_id_list, raw, statistics,
                                     sync_with_zvm)

    ret_json = json.dumps(ret)
    req.response.status = util.get_http_code_from_sdk_return(ret,
                    additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    req.response.body = utils.to_utf8(ret_json)
    return req.response


@util.SdkWsgify
@tokens.validate
def delete_fcp_template(req):
    def _delete_fcp_template(template_id):
        action = get_action()

        return action.delete_fcp_template(template_id)

    template_id = util.wsgi_path_item(req.environ, 'template_id')
    info = _delete_fcp_template(template_id)

    info_json = json.dumps(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.status = util.get_http_code_from_sdk_return(info,
                    additional_handler=util.handle_not_found)
    req.response.content_type = 'application/json'
    return req.response
