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
                'connection': parameter_types.connection_type,
                'queue_mem': {
                    'type': ['integer'],
                    'minimum': 1,
                    'maximum': 8,
                },
                'router': parameter_types.router_type,
                'network_type': parameter_types.network_type,
                'vid': parameter_types.vid_type,
                'port_type': parameter_types.port_type,
                'gvrp': parameter_types.gvrp_type,
                'native_vid': parameter_types.native_vid_type,
            },
            'required': ['name'],
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
