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


create_nic = {
    'type': 'object',
    'properties': {
        'nic': {
            'type': 'object',
            'properties': {
                'vdev': parameter_types.vdev,
                'nic_id': parameter_types.nic_id,
                'mac_addr': parameter_types.mac_address,
                'active': parameter_types.boolean,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['nic'],
    'additionalProperties': False,
}


create_network_interface = {
    'type': 'object',
    'properties': {
        'interface': {
            'type': 'object',
            'properties': {
                'os_version': {'type': 'string'},
                'guest_networks': parameter_types.network_list,
                'active': parameter_types.boolean,
            },
            'required': ['os_version', 'guest_networks'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['interface'],
    'additionalProperties': False,
}


config_minidisks = {
    'type': 'object',
    'properties': {
        'disk_info': {
            'type': 'object',
            'properties': {
                'disk_list': parameter_types.disk_conf,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['disk_info'],
    'additionalProperties': False,
}


create_disks = {
    'type': 'object',
    'properties': {
        'disk_info': {
            'type': 'object',
            'properties': {
                'disk_list': parameter_types.disk_list,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['disk_info'],
    'additionalProperties': False,
}


delete_disks = {
    'type': 'object',
    'properties': {
        'vdev_info': {
            'type': 'object',
            'properties': {
                'vdev_list': parameter_types.vdev_list,
            },
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['vdev_info'],
    'additionalProperties': False,
}


nic_couple_uncouple = {
    'type': 'object',
    'properties': {
        'info': {
            'type': 'object',
            'properties': {
                'couple': parameter_types.boolean,
                'active': parameter_types.boolean,
                'vswitch': parameter_types.vswitch_name,
            },
            # FIXME: vswitch should be required when it's couple
            'required': ['couple'],
            'additionalProperties': False,
        },
        'additionalProperties': False,
    },
    'required': ['info'],
    'additionalProperties': False,
}


deploy = {
    'type': 'object',
    'properties': {
        'image': parameter_types.name,
        'transportfiles': {'type': ['string']},
        'remotehost': parameter_types.remotehost,
        'vdev': parameter_types.vdev,
    },
    'required': ['image'],
    'additionalProperties': False,
}


capture = {
    'type': 'object',
    'properties': {
        'image': parameter_types.name,
        'capturetype': parameter_types.capture_type,
        'compresslevel': parameter_types.compress_level,
    },
    'required': ['image'],
    'additionalProperties': False,
}


userid_list_query = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.single_param(parameter_types.userid_list),
    },
    'additionalProperties': False
}


nic_DB_info = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid,
        'nic_id': parameter_types.nic_id,
        'vswitch': parameter_types.vswitch_name,
    },
    'additionalProperties': False,
}


stop = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid,
        'timeout': parameter_types.positive_integer,
        'poll_interval': parameter_types.positive_integer,
    },
    'additionalProperties': False,
}

softstop = {
    'type': 'object',
    'properties': {
        'userid': parameter_types.userid,
        'timeout': parameter_types.positive_integer,
        'poll_interval': parameter_types.positive_integer,
    },
    'additionalProperties': False,
}
