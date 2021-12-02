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


get_fcp_usage = {
    'type': 'object',
    'properties': {
        'fcp_id': parameter_types.fcp_id,
    },
    'required': ['fcp_id'],
    'additionalProperties': False,
}


get_all_fcp_usage = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid_list_array,
        'statistics': parameter_types.single_param(parameter_types.boolean),
        'sync_with_zvm': parameter_types.single_param(parameter_types.boolean),
    },
    'additionalProperties': False,
}


set_fcp_usage = {
    'type': 'object',
    'properties': {
        'info': {
            'type': 'object',
            'properties': {
                'userid': parameter_types.userid,
                'reserved': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 1,
                },
                'connections': {
                    'type': ['integer'],
                },
            },
            'required': ['reserved', 'connections'],
            'additionalProperties': False,
        }
    },
    'required': ['info'],
    'additionalProperties': False,
}


get_volume_connector = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid_list,
        'info': {
            'type': 'object',
            'properties': {
                'reserve': parameter_types.boolean,
            },
            'required': ['info'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'additionalProperties': False,

}
