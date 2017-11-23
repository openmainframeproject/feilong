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

from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


APIVERSION = '1.0'


@wsgi_wrapper.SdkWsgify
def home(req):
    min_version = APIVERSION
    max_version = APIVERSION

    version_data = {
        'version': '%s' % APIVERSION,
        'max_version': max_version,
        'min_version': min_version,
    }
    output = {
        "rs": 0,
        "overallRC": 0,
        "modID": None,
        "rc": 0,
        "errmsg": "",
        "output": version_data
    }
    info_json = json.dumps(output)
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    req.response.status = 200

    return req.response
