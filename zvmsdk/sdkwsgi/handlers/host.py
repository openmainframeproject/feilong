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

from zvmsdk import api
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_HOSTACTION = None
LOG = log.LOG


class HostAction(object):

    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)

    def get_info(self):
        info = self.api.host_get_info()
        return info

    def get_disk_info(self, diskname):
        info = self.api.host_diskpool_get_info(disk_pool=diskname)
        return info


def get_action():
    global _HOSTACTION
    if _HOSTACTION is None:
        _HOSTACTION = HostAction()
    return _HOSTACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def host_get_info(req):

    def _host_get_info():
        action = get_action()
        return action.get_info()

    info = _host_get_info()
    info_json = json.dumps({'host': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def host_get_disk_info(req):

    def _host_get_disk_info(diskname):
        action = get_action()
        return action.get_disk_info(diskname)

    diskname = util.wsgi_path_item(req.environ, 'disk')

    info = _host_get_disk_info(diskname)
    info_json = json.dumps({'disk_info': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response
