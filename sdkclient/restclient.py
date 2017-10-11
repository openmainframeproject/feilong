# Copyright 2017 IBM Corp.
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

import datetime
import json
import jwt
import requests

from zvmsdk import config


CONF = config.CONF

# parameters amount in path
PARAM_IN_PATH = {
    'home': 0,
    'guest_create': 0,
    'guest_list': 0,
    'guest_get_cpu_info': 0,
    'guest_get_memory_info': 0,
    'guest_get_vnics_info': 0,
    'guest_delete': 1,
    'guest_get': 1,
    'guest_update': 1,
    'guest_action': 1,
    'guest_get_info': 1,
    'guest_get_nic_info': 1,
    'guest_create_nic': 1,
    'guest_delete_nic': 2,
    'guest_couple_uncouple_nic': 2,
    'guest_create_network_interface': 1,
    'guest_get_power_state': 1,
    'guest_create_disks': 1,
    'guest_delete_disks': 1,
    'volume_attach': 1,
    'volume_detach': 1,
    'host_get_info': 0,
    'host_get_disk_info': 1,
    'image_create': 0,
    'image_query': 0,
    'image_delete': 1,
    'image_export': 1,
    'image_get_root_disk_size': 1,
    'token_create': 0,
    'vswitch_list': 0,
    'vswitch_create': 0,
    'vswitch_delete': 1,
    'vswitch_update': 1,
}


API2URL = {
    'home': '/',
    'guest_create': '/guests',
    'guest_list': '/guests',
    'guest_get_cpu_info': '/guests/cpuinfo',
    'guest_get_memory_info': '/guests/meminfo',
    'guest_get_vnics_info': '/guests/vnicsinfo',
    'guest_delete': 'guests/%s',
    'guest_get': 'guests/%s',
    'guest_update': 'guests/%s',
    'guest_action': '/guests/%s/action',
    'guest_get_info': '/guests/%s/info',
    'guest_get_nic_info': '/guests/%s/nic',
    'guest_create_nic': '/guests/%s/nic',
    'guest_delete_nic': '/guests/%s/nic/%s',
    'guest_couple_uncouple_nic': '/guests/%s/nic/%s',
    'guest_create_network_interface': '/guests/%s/interface',
    'guest_get_power_state': '/guests/%s/power_state',
    'guest_create_disks': '/guests/%s/disks',
    'guest_delete_disks': '/guests/%s/disks',
    'volume_attach': '/guests/%s/volumes',
    'volume_detach': '/guests/%s/volumes',
    'host_get_info': '/host',
    'host_get_disk_info': '/host/disk/%s',
    'image_create': '/images',
    'image_query': '/images',
    'image_delete': '/images/%s',
    'image_export': '/images/%s',
    'image_get_root_disk_size': '/images/%s/root_disk_size',
    'token_create': '/token',
    'vswitch_list': '/vswitchs',
    'vswitch_create': '/vswitchs',
    'vswitch_delete': '/vswitchs/%s',
    'vswitch_update': '/vswitchs/%s',
}


API2METHOD = {
    'home': 'GET',
    'guest_create': 'POST',
    'guest_list': 'GET',
    'guest_get_cpu_info': 'GET',
    'guest_get_memory_info': 'GET',
    'guest_get_vnics_info': 'GET',
    'guest_delete': 'DELETE',
    'guest_get': 'GET',
    'guest_update': 'PUT',
    'guest_action': 'POST',
    'guest_get_info': 'GET',
    'guest_get_nic_info': 'GET',
    'guest_create_nic': 'POST',
    'guest_delete_nic': 'DELETE',
    'guest_couple_uncouple_nic': 'PUT',
    'guest_create_network_interface': 'POST',
    'guest_get_power_state': 'GET',
    'guest_create_disks': 'POST',
    'guest_delete_disks': 'DELETE',
    'volume_attach': 'POST',
    'volume_detach': 'DELETE',
    'host_get_info': 'GET',
    'host_get_disk_info': 'GET',
    'image_create': 'POST',
    'image_query': 'GET',
    'image_delete': 'DELETE',
    'image_export': 'PUT',
    'image_get_root_disk_size': 'GET',
    'token_create': 'POST',
    'vswitch_list': 'GET',
    'vswitch_create': 'POST',
    'vswitch_delete': 'DELETE',
    'vswitch_update': 'PUT',
}


API2BODY = {
    'home': None,
    'guest_create': 'body_guest_create',
    'guest_list': None,
    'guest_get_cpu_info': None,
    'guest_get_memory_info': None,
    'guest_get_vnics_info': None,
    'guest_delete': None,
    'guest_get': None,
    'guest_update': 'body_guest_update',
    'guest_action': 'body_guest_action',
    'guest_get_info': None,
    'guest_get_nic_info': None,
    'guest_create_nic': 'body_guest_create_nic',
    'guest_delete_nic': 'body_guest_delete_nic',
    'guest_couple_uncouple_nic': 'body_guest_couple_uncouple_nic',
    'guest_create_network_interface': 'body_guest_create_network_interface',
    'guest_get_power_state': None,
    'guest_create_disks': 'body_guest_create_disks',
    'guest_delete_disks': 'body_guest_delete_disks',
    'volume_attach': 'body_volume_attach',
    'volume_detach': 'body_volume_detach',
    'host_get_info': None,
    'host_get_disk_info': None,
    'image_create': 'body_image_create',
    'image_query': None,
    'image_delete': None,
    'image_export': 'body_image_export',
    'image_get_root_disk_size': None,
    'token_create': None,
    'vswitch_list': None,
    'vswitch_create': 'body_vswitch_create',
    'vswitch_delete': None,
    'vswitch_update': 'body_vswitch_update',
}


def body_guest_update(start_index, *args, **kwargs):
    return None


def body_guest_create(start_index, *args, **kwargs):
    body = {'guest': {'userid': args[start_index],
                      'vcpus': args[start_index + 1],
                      'memory': args[start_index + 2],
                      'disk_list': kwargs.get('disk_list', None),
                      'user_profile': kwargs.get('user_profile', None)}}
    body_str = json.dumps(body)
    return body_str


# FIXME: the order of args need adjust
def body_guest_action(start_index, *args, **kwargs):
    body = {'action': args[start_index]}
    body_str = json.dumps(body)
    return body_str


def body_guest_create_nic(start_index, *args, **kwargs):
    body = {'nic': {'vdev': kwargs.get('vdev', None),
                    'nic_id': kwargs.get('nic_id', None),
                    'mac_addr': kwargs.get('mac_addr', None),
                    'ip_addr': kwargs.get('ip_addr', None),
                    'active': kwargs.get('active', False)}}
    body_str = json.dumps(body)
    return body_str


def body_guest_delete_nic(start_index, *args, **kwargs):
    body = {'active': kwargs.get('active', False)}
    body_str = json.dumps(body)
    return body_str


def body_guest_couple_uncouple_nic(start_index, *args, **kwargs):
    body = {'info': {'couple': args[start_index],
                     'vswitch': args[start_index + 1],
                     'active': kwargs.get('active', False)}}
    body_str = json.dumps(body)
    return body_str


def body_guest_create_network_interface(start_index, *args, **kwargs):
    body = {'interface': {'os_version': args[start_index],
                          'guest_networks': args[start_index + 1],
                          'active': kwargs.get('active', False)}}
    body_str = json.dumps(body)
    return body_str


def body_guest_create_disks(start_index, *args, **kwargs):
    body = {'disk_info': {'disk_list': kwargs.get('disk_list', None)}}
    body_str = json.dumps(body)
    return body_str


def body_guest_delete_disks(start_index, *args, **kwargs):
    body = {'vdev_info': {'vdev_list': kwargs.get('vdev_list', None)}}
    body_str = json.dumps(body)
    return body_str


# FIXME: (userid, os_type) in one params, how to parse?
def body_volume_attach(start_index, *args, **kwargs):
    body = {'info': {'os_type': args[start_index],
                     'volume': args[start_index + 1],
                     'connection': args[start_index + 2],
                     'rollback': args[start_index + 3]}}
    body_str = json.dumps(body)
    return body_str


# FIXME: (userid, os_type) in one params, how to parse?
def body_volume_detach(start_index, *args, **kwargs):
    body = {'info': {'os_type': args[start_index],
                     'volume': args[start_index + 1],
                     'connection': args[start_index + 2],
                     'rollback': args[start_index + 3]}}
    body_str = json.dumps(body)
    return body_str


def body_image_create(start_index, *args, **kwargs):
    body = {'image': {'image_name': args[start_index],
                      'url': args[start_index + 1],
                      'image_meta': args[start_index + 2],
                      'remotehost': kwargs.get('remotehost', None)}}
    body_str = json.dumps(body)
    return body_str


def body_image_export(start_index, *args, **kwargs):
    body = {'location': {'dest_url': args[start_index],
                         'remotehost': kwargs.get('remotehost', None)}}
    body_str = json.dumps(body)
    return body_str


def body_vswitch_create(start_index, *args, **kwargs):
    # TODO: just two elements in body?
    body = {'vswitch': {'name': args[start_index],
                        'rdev': kwargs.get('rdev', None)}}
    body_str = json.dumps(body)
    return body_str


def body_vswitch_update(*args, **kwargs):
    body = {'vswitch': {'grant_userid': kwargs.get('grant_userid', None),
                        'revoke_userid': kwargs.get('revoke_userid', None),
                        'user_vlan_id': kwargs.get('user_vlan_id', None)}}
    body_str = json.dumps(body)
    return body_str


class RESTClient(object):

    def __init__(self, ip='127.0.0.1', port='8888', timeout=30):
        self.base_url = "http://" + ip + ":" + port

    def _tmp_token(self):
        expires = 30

        expired_elapse = datetime.timedelta(seconds=expires)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        payload = jwt.encode({'exp': expired_time}, CONF.wsgi.password)

        return payload

    def _get_token(self):
        _headers = {'Content-Type': 'application/json'}
        _headers['X-Auth-User'] = CONF.wsgi.user
        _headers['X-Auth-Password'] = CONF.wsgi.password

        url = self.base_url + '/token'
        method = 'POST'
        response = requests.request(method, url, headers=_headers)
        token = response.headers['X-Auth-Token']

        return token

    def _get_body(self, api_name, *args, **kwargs):
        if API2BODY[api_name] is not None:
            func = eval(API2BODY[api_name])
            return func(*args, **kwargs)
        return None

    def _process_rest_response(self, response):
        res_dict = json.loads(response.content)
        return res_dict['output']

    def request(self, url, method, body, headers=None):
        _headers = {'Content-Type': 'application/json'}
        _headers.update(headers or {})

        # _headers['X-Auth-Token'] = self._get_token()
        _headers['X-Auth-Token'] = self._tmp_token()

        response = requests.request(method, url, data=body, headers=_headers)
        return response

    def api_request(self, url, method='GET', body=None):

        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body)

    def call(self, api_name, *args, **kwargs):
        count_params_in_path = PARAM_IN_PATH[api_name]
        if count_params_in_path > 0:
            url = API2URL[api_name] % tuple(args[0:count_params_in_path])
        else:
            url = API2URL[api_name]
        method = API2METHOD[api_name]
        # generate body from args and kwargs
        body = self._get_body(count_params_in_path, api_name, *args, **kwargs)
        # response with JSON format
        response = self.api_request(url, method, body)
        # change response to SDK format
        result = self._process_rest_response(response)
        return result
