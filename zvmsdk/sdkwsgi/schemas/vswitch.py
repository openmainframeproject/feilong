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
        'vswitch': {
            'type': 'object',
            'properties': {
                'name': parameter_types.vswitch_name,
                'rdev': parameter_types.rdev_list,
                # FIXME: controller has its own conventions
                'controller': parameter_types.controller,
                'persist': parameter_types.boolean,
                'connection': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 2,
                },
                'queue_mem': {
                    'type': ['integer'],
                    'minimum': 1,
                    'maximum': 8,
                },
                'router': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 2,
                },
                'network_type': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 2,
                },
                'vid': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 4094,
                },
                'port_type': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 2,
                },
                'update': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 3,
                },
                'gvrp': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 2,
                },
                'native_vid': {
                    'type': ['integer'],
                    'minimum': 0,
                    'maximum': 4094,
                },
            },
            'required': ['name', 'rdev'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['vswitch'],
    'additionalProperties': False,
}


update = {
    'type': 'object',
    'properties': {
        'vswitch': {
            'type': 'object',
            'properties': {
                 'grant_userid': parameter_types.userid,
                 'user_vlan_id': parameter_types.user_vlan_id,
                 'revoke_userid': parameter_types.userid,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['vswitch'],
    'additionalProperties': False,
}
