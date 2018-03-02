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
from zvmsdk.sdkwsgi import util
from zvmsdk import utils
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi.schemas import image


_HOSTACTION = None
CONF = config.CONF
LOG = log.LOG


class HostAction(object):

    def __init__(self):
        self.client = connector.ZVMConnector(connection_type='socket',
                                             ip_addr=CONF.sdkserver.bind_addr,
                                             port=CONF.sdkserver.bind_port)

    def get_info(self):
        info = self.client.send_request('host_get_info')
        return info

    @validation.query_schema(image.diskpool)
    def diskpool_get_info(self, req, poolname):
        info = self.client.send_request('host_diskpool_get_info',
                                        disk_pool=poolname)
        return info


def get_action():
    global _HOSTACTION
    if _HOSTACTION is None:
        _HOSTACTION = HostAction()
    return _HOSTACTION


@util.SdkWsgify
@tokens.validate
def host_get_info(req):

    def _host_get_info():
        action = get_action()
        return action.get_info()

    info = _host_get_info()
    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@util.SdkWsgify
@tokens.validate
def host_get_disk_info(req):

    def _host_get_disk_info(req, poolname):
        action = get_action()
        return action.diskpool_get_info(req, poolname)

    poolname = None
    if 'poolname' in req.GET:
        poolname = req.GET['poolname']
    info = _host_get_disk_info(req, poolname)
    info_json = json.dumps(info)
    req.response.status = util.get_http_code_from_sdk_return(info,
        additional_handler=util.handle_not_found)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response
