# Copyright 2017,2018 IBM Corp.
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

    @validation.schema(volume.get_volume_connector)
    def get_volume_connector(self, req, userid):
        conn = self.client.send_request('get_volume_connector', userid)
        return conn


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
def get_volume_connecotr(req):
    def _get_volume_conn(req, userid):
        action = get_action()
        return action.get_volume_connector(req, userid)

    userid = util.wsgi_path_item(req.environ, 'userid')
    conn = _get_volume_conn(req, userid)
    conn_json = json.dumps(conn)

    req.response.content_type = 'application/json'
    req.response.body = utils.to_utf8(conn_json)
    req.response.status = util.get_http_code_from_sdk_return(conn, default=200)
    return req.response
