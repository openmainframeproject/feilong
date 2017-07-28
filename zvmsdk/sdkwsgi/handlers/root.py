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

from zvmsdk.sdkwsgi import microversion
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


@wsgi_wrapper.SdkWsgify
def home(req):
    min_version = microversion.min_version_string()
    max_version = microversion.max_version_string()

    version_data = {
        'version': '%s' % min_version,
        'max_version': max_version,
        'min_version': min_version,
    }
    version_json = json.dumps({'versions': [version_data]})
    req.response.body = utils.to_utf8(version_json)
    req.response.content_type = 'application/json'

    return req.response
