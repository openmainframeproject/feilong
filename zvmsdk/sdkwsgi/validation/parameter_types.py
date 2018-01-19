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

import re
import unicodedata

import six


def single_param(schema):
    ret = multi_params(schema)
    ret['maxItems'] = 1
    return ret


def multi_params(schema):
    return {'type': 'array', 'items': schema}


class ValidationRegex(object):
    def __init__(self, regex, reason):
        self.regex = regex
        self.reason = reason


def _is_printable(char):
    category = unicodedata.category(char)
    return (not category.startswith("C") and
            (not category.startswith("Z") or category == "Zs"))


def _get_all_chars():
    for i in range(0xFFFF):
        yield six.unichr(i)


def _build_regex_range(ws=True, invert=False, exclude=None):
    if exclude is None:
        exclude = []
    regex = ""
    in_range = False
    last = None
    last_added = None

    def valid_char(char):
        if char in exclude:
            result = False
        elif ws:
            result = _is_printable(char)
        else:
            # Zs is the unicode class for space characters, of which
            # there are about 10 in this range.
            result = (_is_printable(char) and
                      unicodedata.category(char) != "Zs")
        if invert is True:
            return not result
        return result

    # iterate through the entire character range. in_
    for c in _get_all_chars():
        if valid_char(c):
            if not in_range:
                regex += re.escape(c)
                last_added = c
            in_range = True
        else:
            if in_range and last != last_added:
                regex += "-" + re.escape(last)
            in_range = False
        last = c
    else:
        if in_range:
            regex += "-" + re.escape(c)
    return regex


valid_name_regex_base = '^(?![%s])[%s]*(?<![%s])$'


valid_name_regex = ValidationRegex(
    valid_name_regex_base % (
        _build_regex_range(ws=False, invert=True),
        _build_regex_range(),
        _build_regex_range(ws=False, invert=True)),
    "printable characters. Can not start or end with whitespace.")


name = {
    'type': 'string', 'minLength': 1, 'maxLength': 255,
    'format': 'name'
}


positive_integer = {
    'type': ['integer', 'string'],
    'pattern': '^[0-9]*$', 'minimum': 1
}


ipv4 = {
    'type': 'string', 'format': 'ipv4'
}


nic_info = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'nic_id': {'type': 'string'},
            'mac_addr': {'type': 'string'}
        },
        'additionalProperties': False
    }
}


boolean = {
    'type': ['boolean', 'string'],
    'enum': [True, 'True', 'TRUE', 'true', '1', 'ON', 'On', 'on',
             'YES', 'Yes', 'yes',
             False, 'False', 'FALSE', 'false', '0', 'OFF', 'Off', 'off',
             'NO', 'No', 'no']
}


rdev_list = {
    'type': ['string'],
    'pattern': '^([0-9a-fA-F]{,4})(\s+[0-9a-fA-F]{,4}){,2}$'
}


rdev = {
    'type': ['string'], 'minLength': 1, 'maxLength': 4,
    'pattern': '^[0-9a-fA-F]{,4}$'
}


vdev = {
    'type': ['string'], 'minLength': 1, 'maxLength': 4,
    'pattern': '^[0-9a-fA-F]{,4}$'
}


vdev_list = {
    'type': 'array',
    'minItems': 1,
    'items': {
        'type': 'string',
        'pattern': '^[0-9a-fA-F]{,4}$'
    },
    'uniqueItems': True
}

image_list = {
    'maxItems': 1,
    'items': {
        'format': 'name',
        'maxLength': 255,
        'minLength': 1,
        'type': 'string'
    },
    'type': 'array'
}

url = {
    'type': ['string'],
    'pattern': '^https?:/{2}|^file:/{3}\w.+$'
}


mac_address = {
    'type': 'string',
    'pattern': '^([0-9a-fA-F]{2})(:[0-9a-fA-F]{2}){5}$'
}


remotehost = {
    'type': ['string'],
    'pattern': '^[a-zA-Z0-9\-]+\@([0-9]{1,3}(.[0-9]{1,3}){3}$|'
    '[a-zA-Z0-9\-]+(.[a-zA-Z0-9\-]){1,}$)'
}


userid = {
    'type': ['string'],
    'minLength': 1,
    'maxLength': 8,
    'pattern': '^(\w{,8})$'
}


vswitch_name = {
    'type': ['string'], 'minLength': 1, 'maxLength': 8
}


controller = {
    'type': ['string'],
    'anyOf': [
        {'pattern': '\*'},
        {'minLength': 1, 'maxLength': 8}
        ]
}


nic_id = {
    'type': ['string']
}


cidr = {
    'type': ['string'],
    'format': 'cidr'
}


userid_list = {
    'type': ['string'],
    # TODO:validate userid_list in inspect APIs
    'pattern': '^(\w{,8})(,\w{,8}){0,}$'
}

userid_list_array = {
    'items': {
        'type': ['string'],
        'minLength': 1,
        'maxLength': 8,
        'pattern': '^(\w{,8})(,\w{,8}){0,}$'

    },
    'type': 'array'
}

file_type = {
    'type': 'string',
    'enum': ['ext2', 'ext3', 'ext4', 'xfs']
}

disk_pool = {
    'type': 'string',
    'pattern': '^\w+:\w+$'
}

disk_list = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'size': {'type': 'string'},
            'format': file_type,
            'is_boot_disk': boolean,
            'disk_pool': {'type': 'string', 'pattern': '^\w+:\w+$'}
        },
        'required': ['size'],
        'additionalProperties': False
    }
}


disk_conf = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'vdev': vdev,
            'format': file_type,
            'mntdir': {'type': 'string'}
        },
        'required': ['vdev', 'format', 'mntdir'],
        'additionalProperties': False
    }
}


image_meta = {
    'type': 'object',
    'properties': {
        'os_version': {'type': 'string'},
        # md5 shoule be 32 hexadeciaml numbers
        'md5sum': {'type': 'string', 'pattern': '^[0-9a-fA-F]{32}$'}
    },
    'required': ['os_version'],
    'additionalProperties': False
}


command = {
    'type': 'string'
}

network_list = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'ip_addr': ipv4,
            'dns_addr': {'type': 'array',
                        'items': ipv4},
            'gateway_addr': ipv4,
            'mac_addr': mac_address,
            'cidr': cidr,
            'nic_vdev': vdev,
            'nic_id': {'type': 'string'}},
    },
    'additionalProperties': False
}

capture_type = {
    'type': 'string',
    'enum': ['rootonly', 'alldisks']
}

compress_level = {
    'type': ['integer'],
    'pattern': '^[0-9]$'
}

user_vlan_id = {
    'type': 'object',
    'properties': {
        'userid': userid,
        'vlanid': {'type': ['integer'],
                   'minimum': 1,
                   'maximum': 4094,
                  }
    },
    'required': ['userid', "vlanid"],
    'additionalProperties': False
}

connection_type = {
    'type': 'string',
    'enum': ['CONnect', 'DISCONnect', 'NOUPLINK']
}

router_type = {
    'type': 'string',
    'enum': ['NONrouter', 'PRIrouter']
}

network_type = {
    'type': 'string',
    'enum': ['IP', 'ETHernet']
}

vid_type = {
    'oneOf': [
        {'type': 'string', 'enum': ['UNAWARE', 'AWARE']},
        {'type': 'integer', 'minimum': 1, 'maximum': 4094}
    ]
}

port_type = {
    'type': 'string',
    'enum': ['ACCESS', 'TRUNK']
}

gvrp_type = {
    'type': 'string',
    'enum': ['GVRP', 'NOGVRP']
}

native_vid_type = {
    'oneOf': [
        {'type': 'null'},
        {'type': 'integer', 'minimum': 1, 'maximum': 4094}
    ]
}
