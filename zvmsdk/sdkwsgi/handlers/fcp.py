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


_FCPACTION = None
CONF = config.CONF
LOG = log.LOG


class FCPAction(object):
    def __init__(self):
        self.client = connector.ZVMConnector(connection_type='socket',
                                             ip_addr=CONF.sdkserver.bind_addr,
                                             port=CONF.sdkserver.bind_port)

    def get_connector(self, body):
        # currently
        assigner_id = body['assigner_id']
        info = self.client.send_request('volume_get_connector',
                                        assigner_id)
        return info


def get_action():
    global _FCPACTION
    if _FCPACTION is None:
        _FCPACTION = FCPAction()
    return _FCPACTION


@util.SdkWsgify
@tokens.validate
def get_connector(req):
    def _get_connector(userid, req):
        action = get_action()
        body = util.extract_json(req.body)
        return action.get_connector(userid, body)

    info = _get_connector(req)
    info_json = json.dumps(info)

    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = util.get_http_code_from_sdk_return(info, default=200)
    return req.response
