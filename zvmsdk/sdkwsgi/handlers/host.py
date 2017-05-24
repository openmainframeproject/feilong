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

from zvmsdk import config
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import wsgi_wrapper

_HOSTACTION = None
CONF = config.CONF
LOG = log.LOG


class HostAction(object):
    def list(self, name):
        LOG.info('list guest for a host')

    def get_info(self, name):
        LOG.info('get host info')

    def get_disk_info(self, name, diskname):
        LOG.info('get host disk info')


def get_action():
    global _HOSTACTION
    if _HOSTACTION is None:
        _HOSTACTION = HostAction()
    return _HOSTACTION


@wsgi_wrapper.SdkWsgify
def host_list_guests(req):
    tokens.validate(req)

    def _host_list_guests(req):
        action = get_action()
        action.list()

    name = util.wsgi_path_item(req.environ, 'name')
    _host_list_guests(name)


@wsgi_wrapper.SdkWsgify
def host_get_info(req):

    def _host_get_info(name):
        action = get_action()
        action.get_info(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _host_get_info(name)


@wsgi_wrapper.SdkWsgify
def host_get_disk_info(req):

    def _host_get_disk_info(uuid, req):
        action = get_action()
        action.get_disk_info(name, req)

    name = util.wsgi_path_item(req.environ, 'name')
    _host_get_disk_info(name, req)
