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
                'userid': parameter_types.userid,
                'vcpus': parameter_types.positive_integer,
                'memory': parameter_types.positive_integer,
                # profile is similar to userid
                'user_profile': parameter_types.userid,
                'disk_list': parameter_types.disk_list,
            },
            'required': ['userid', 'vcpus', 'memory'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['guest'],
    'additionalProperties': False,
}


deploy = {
    'type': 'object',
    'properties': {
        'guest': {
            'type': 'object',
            'properties': {
                'userid': parameter_types.userid,
                'image_name': parameter_types.name,

                # FIXME
                'transportfiles': parameter_types.name,
                'remotehost': parameter_types.name,
                'vdev': parameter_types.vdev,

            },
            'required': ['userid', 'image_name'],
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
                'vdev': parameter_types.vdev,
                # FIXME
                'nic_id': parameter_types.name,
                'mac_addr': parameter_types.name,
                'ip_addr': parameter_types.ipv4,
                'active': parameter_types.boolean,
                'persist': parameter_types.boolean,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['nic'],
    'additionalProperties': False,
}


couple_uncouple_nic = {
    'type': 'object',
    'properties': {
        'info': {
            'type': 'object',
            'properties': {
                'couple': parameter_types.boolean,
                'vswitch': parameter_types.name,
                'vdev': parameter_types.vdev,
                'persist': parameter_types.boolean,
            },
            'required': ['couple', 'vswitch', 'vdev'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['info'],
    'additionalProperties': False,
}
