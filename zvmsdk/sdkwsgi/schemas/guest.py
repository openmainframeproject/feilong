# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from zvmsdk.sdkwsgi.validation import parameter_types


create = {
    'type': 'object',
    'properties': {
        'guest': {
            'type': 'object',
            'properties': {
                'name': parameter_types.name,
                'cpu': parameter_types.positive_integer,
                'memory': parameter_types.positive_integer,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['guest'],
    'additionalProperties': False,
}


create_nic = {
    'type': 'object',
    'properties': {
        'nic': {
            'type': 'object',
            'properties': {
                'nic_info': parameter_types.nic_info,
                'ip': parameter_types.ipv4,
            },
            'required': ['nic_info'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['nic'],
    'additionalProperties': False,
}
