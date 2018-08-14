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

from zvmsdk.sdkwsgi.validation import parameter_types


attach = {
    'type': 'object',
    'properties': {
        'info': {
            'type': 'object',
            'properties': {
                'connection': parameter_types.connection_info,
            },
            'required': ['connection'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['info'],
    'additionalProperties': False,
}


detach = {
    'type': 'object',
    'properties': {
        'info': {
            'type': 'object',
            'properties': {
                'connection': parameter_types.connection_info,
            },
            'required': ['connection'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['info'],
    'additionalProperties': False,
}


get_volume_connector = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid_list,
    },
    'additionalProperties': False,
}
