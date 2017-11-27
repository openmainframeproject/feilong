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
import six


REST_REQUEST_ERROR = [{'overallRC': 101, 'modID': 110, 'rc': 101},
                      {1: "Request to zVM Cloud Connector failed:: %(error)s"},
                       "zVM Cloud Connector request failed",
                       ]
INVALID_API_ERROR = [{'overallRC': 400, 'modID': 110, 'rc': 400},
                     {1: "Invalid API name, '%(msg)s'"},
                     "Invalid API name",
                     ]


def fill_kwargs_in_body(body, **kwargs):
    for key in kwargs.keys():
        body[key] = kwargs.get(key)


def req_home(start_index, *args, **kwargs):
    url = '/'
    body = None
    return url, body


def req_guest_list(start_index, *args, **kwargs):
    url = '/guests'
    body = None
    return url, body


def req_guest_delete(start_index, *args, **kwargs):
    url = '/guests/%s'
    body = None
    return url, body


def req_guest_get_definition_info(start_index, *args, **kwargs):
    url = '/guests/%s'
    body = None
    return url, body


def req_guest_create(start_index, *args, **kwargs):
    url = '/guests'
    body = {'guest': {'userid': args[start_index],
                      'vcpus': args[start_index + 1],
                      'memory': args[start_index + 2]}}
    fill_kwargs_in_body(body['guest'], **kwargs)
    return url, body


def req_guest_inspect_stats(start_index, *args, **kwargs):
    url = '/guests/stats?userid=%s'
    body = None
    return url, body


def req_guest_inspect_vnics(start_index, *args, **kwargs):
    url = '/guests/vnicsinfo?userid=%s'
    body = None
    return url, body


def req_guests_get_nic_info(start_index, *args, **kwargs):
    url = '/guests/nics'
    # process appends in GET method
    userid = kwargs.get('userid', None)
    nic_id = kwargs.get('nic_id', None)
    vswitch = kwargs.get('vswitch', None)
    if ((userid is None) and
        (nic_id is None) and
        (vswitch is None)):
            append = ''
    else:
        append = "?"
        if userid is not None:
            append += 'userid=%s&' % userid
        if nic_id is not None:
            append += 'nic_id=%s&' % nic_id
        if vswitch is not None:
            append += 'vswitch=%s&' % vswitch
        append = append.strip('&')
    url = url + append
    body = None
    return url, body


# FIXME: the order of args need adjust
def req_guest_start(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'start'}
    return url, body


def req_guest_stop(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'stop'}
    fill_kwargs_in_body(body, **kwargs)
    return url, body


def req_guest_softstop(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'softstop'}
    fill_kwargs_in_body(body, **kwargs)
    return url, body


def req_guest_pause(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'pause'}
    return url, body


def req_guest_unpause(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'unpause'}
    return url, body


def req_guest_reboot(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'reboot'}
    return url, body


def req_guest_reset(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'reset'}
    return url, body


def req_guest_get_console_output(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'get_console_output'}
    return url, body


def req_guest_capture(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'capture'}
    return url, body


def req_guest_deploy(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'deploy',
            'image': args[start_index]}
    fill_kwargs_in_body(body, **kwargs)
    return url, body


def req_guest_get_info(start_index, *args, **kwargs):
    url = '/guests/%s/info'
    body = None
    return url, body


def req_guest_get_nic_vswitch_info(start_index, *args, **kwargs):
    url = '/guests/%s/nic'
    body = None
    return url, body


def req_guest_create_nic(start_index, *args, **kwargs):
    url = '/guests/%s/nic'
    body = {'nic': {}}
    fill_kwargs_in_body(body['nic'], **kwargs)
    return url, body


def req_guest_delete_nic(start_index, *args, **kwargs):
    url = '/guests/%s/nic/%s'
    body = {}
    fill_kwargs_in_body(body, **kwargs)
    return url, body


def req_guest_nic_couple_to_vswitch(start_index, *args, **kwargs):
    url = '/guests/%s/nic/%s'
    body = {'info': {'couple': True,
                     'vswitch': args[start_index]}}
    fill_kwargs_in_body(body['info'], **kwargs)
    return url, body


def req_guest_nic_uncouple_from_vswitch(start_index, *args, **kwargs):
    url = '/guests/%s/nic/%s'
    body = {'info': {'couple': False}}
    fill_kwargs_in_body(body['info'], **kwargs)
    return url, body


def req_guest_create_network_interface(start_index, *args, **kwargs):
    url = '/guests/%s/interface'
    body = {'interface': {'os_version': args[start_index],
                          'guest_networks': args[start_index + 1]}}
    fill_kwargs_in_body(body['interface'], **kwargs)
    return url, body


def req_guest_get_power_state(start_index, *args, **kwargs):
    url = '/guests/%s/power_state'
    body = None
    return url, body


def req_guest_create_disks(start_index, *args, **kwargs):
    url = '/guests/%s/disks'
    body = {'disk_info': {}}
    fill_kwargs_in_body(body['disk_info'], **kwargs)
    return url, body


def req_guest_delete_disks(start_index, *args, **kwargs):
    url = '/guests/%s/disks'
    body = {'vdev_info': {}}
    fill_kwargs_in_body(body['vdev_info'], **kwargs)
    return url, body


def req_guest_config_minidisks(start_index, *args, **kwargs):
    url = '/guests/%s/disks'
    body = {'disk_info': {'disk_list': args[start_index]}}
    fill_kwargs_in_body(body['disk_info'], **kwargs)
    return url, body


# FIXME: (userid, os_type) in one params, how to parse?
def req_volume_attach(start_index, *args, **kwargs):
    url = '/guests/%s/volumes'
    body = {'info': {'os_type': args[start_index],
                     'volume': args[start_index + 1],
                     'connection': args[start_index + 2],
                     'rollback': args[start_index + 3]}}
    fill_kwargs_in_body(body['info'], **kwargs)
    return url, body


# FIXME: (userid, os_type) in one params, how to parse?
def req_volume_detach(start_index, *args, **kwargs):
    url = '/guests/%s/volumes'
    body = {'info': {'os_type': args[start_index],
                     'volume': args[start_index + 1],
                     'connection': args[start_index + 2],
                     'rollback': args[start_index + 3]}}
    fill_kwargs_in_body(body['info'], **kwargs)
    return url, body


def req_host_get_info(start_index, *args, **kwargs):
    url = '/host'
    body = None
    return url, body


def req_host_diskpool_get_info(start_index, *args, **kwargs):
    url = '/host/disk/%s'
    body = None
    return url, body


def req_image_import(start_index, *args, **kwargs):
    url = '/images'
    body = {'image': {'image_name': args[start_index],
                      'url': args[start_index + 1],
                      'image_meta': args[start_index + 2]}}
    fill_kwargs_in_body(body['image'], **kwargs)
    return url, body


def req_image_query(start_index, *args, **kwargs):
    url = '/images'
    image_name = kwargs.get('imagename', None)
    if image_name is None:
        append = ''
    else:
        append = "?"
        append += "imagename=%s" % image_name
    url += append
    body = None
    return url, body


def req_image_delete(start_index, *args, **kwargs):
    url = '/images/%s'
    body = None
    return url, body


def req_image_export(start_index, *args, **kwargs):
    url = '/images/%s'
    body = {'location': {'dest_url': args[start_index]}}
    fill_kwargs_in_body(body['location'], **kwargs)
    return url, body


def req_image_get_root_disk_size(start_index, *args, **kwargs):
    url = '/images/%s/root_disk_size'
    body = None
    return url, body


def req_token_create(start_index, *args, **kwargs):
    url = '/token'
    body = None
    return url, body


def req_vswitch_get_list(start_index, *args, **kwargs):
    url = '/vswitches'
    body = None
    return url, body


def req_vswitch_create(start_index, *args, **kwargs):
    url = '/vswitches'
    body = {'vswitch': {'name': args[start_index]}}
    fill_kwargs_in_body(body['vswitch'], **kwargs)
    return url, body


def req_vswitch_delete(start_index, *args, **kwargs):
    url = '/vswitches/%s'
    body = None
    return url, body


def req_vswitch_grant_user(start_index, *args, **kwargs):
    url = '/vswitches/%s'
    body = {'vswitch': {'grant_userid': args[start_index]}}
    fill_kwargs_in_body(body['vswitch'], **kwargs)
    return url, body


def req_vswitch_revoke_user(start_index, *args, **kwargs):
    url = '/vswitches/%s'
    body = {'vswitch': {'revoke_userid': args[start_index]}}
    fill_kwargs_in_body(body['vswitch'], **kwargs)
    return url, body


def req_vswitch_set_vlan_id_for_user(start_index, *args, **kwargs):
    url = '/vswitches/%s'
    body = {'vswitch': {'user_vlan_id': {'userid': args[start_index],
                                         'vlanid': args[start_index + 1]}}}
    fill_kwargs_in_body(body['vswitch'], **kwargs)
    return url, body


# parameters amount in path
PARAM_IN_PATH = {
    'home': 0,
    'guest_create': 0,
    'guest_list': 0,
    'guest_inspect_stats': 1,
    'guest_inspect_vnics': 1,
    'guests_get_nic_info': 0,
    'guest_delete': 1,
    'guest_get_definition_info': 1,
    'guest_start': 1,
    'guest_stop': 1,
    'guest_softstop': 1,
    'guest_pause': 1,
    'guest_unpause': 1,
    'guest_reboot': 1,
    'guest_reset': 1,
    'guest_get_console_output': 1,
    'guest_capture': 1,
    'guest_deploy': 1,
    'guest_get_info': 1,
    'guest_get_nic_vswitch_info': 1,
    'guest_create_nic': 1,
    'guest_delete_nic': 2,
    'guest_nic_couple_to_vswitch': 2,
    'guest_nic_uncouple_from_vswitch': 2,
    'guest_create_network_interface': 1,
    'guest_get_power_state': 1,
    'guest_create_disks': 1,
    'guest_delete_disks': 1,
    'guest_config_minidisks': 1,
    'volume_attach': 1,
    'volume_detach': 1,
    'host_get_info': 0,
    'host_diskpool_get_info': 1,
    'image_import': 0,
    'image_query': 1,
    'image_delete': 1,
    'image_export': 1,
    'image_get_root_disk_size': 1,
    'token_create': 0,
    'vswitch_get_list': 0,
    'vswitch_create': 0,
    'vswitch_delete': 1,
    'vswitch_grant_user': 1,
    'vswitch_revoke_user': 1,
    'vswitch_set_vlan_id_for_user': 1,
}


API2METHOD = {
    'home': 'GET',
    'guest_create': 'POST',
    'guest_list': 'GET',
    'guest_inspect_stats': 'GET',
    'guest_inspect_vnics': 'GET',
    'guests_get_nic_info': 'GET',
    'guest_delete': 'DELETE',
    'guest_get_definition_info': 'GET',
    'guest_start': 'POST',
    'guest_stop': 'POST',
    'guest_softstop': 'POST',
    'guest_pause': 'POST',
    'guest_unpause': 'POST',
    'guest_reboot': 'POST',
    'guest_reset': 'POST',
    'guest_get_console_output': 'POST',
    'guest_capture': 'POST',
    'guest_deploy': 'POST',
    'guest_get_info': 'GET',
    'guest_get_nic_vswitch_info': 'GET',
    'guest_create_nic': 'POST',
    'guest_delete_nic': 'DELETE',
    'guest_nic_couple_to_vswitch': 'PUT',
    'guest_nic_uncouple_from_vswitch': 'PUT',
    'guest_create_network_interface': 'POST',
    'guest_get_power_state': 'GET',
    'guest_create_disks': 'POST',
    'guest_delete_disks': 'DELETE',
    'guest_config_minidisks': 'PUT',
    'volume_attach': 'POST',
    'volume_detach': 'DELETE',
    'host_get_info': 'GET',
    'host_diskpool_get_info': 'GET',
    'image_import': 'POST',
    'image_query': 'GET',
    'image_delete': 'DELETE',
    'image_export': 'PUT',
    'image_get_root_disk_size': 'GET',
    'token_create': 'POST',
    'vswitch_get_list': 'GET',
    'vswitch_create': 'POST',
    'vswitch_delete': 'DELETE',
    'vswitch_grant_user': 'PUT',
    'vswitch_revoke_user': 'PUT',
    'vswitch_set_vlan_id_for_user': 'PUT',
}


API2REQ = {
    'home': req_home,
    'guest_create': req_guest_create,
    'guest_list': req_guest_list,
    'guest_inspect_stats': req_guest_inspect_stats,
    'guest_inspect_vnics': req_guest_inspect_vnics,
    'guests_get_nic_info': req_guests_get_nic_info,
    'guest_delete': req_guest_delete,
    'guest_get_definition_info': req_guest_get_definition_info,
    'guest_start': req_guest_start,
    'guest_stop': req_guest_stop,
    'guest_softstop': req_guest_softstop,
    'guest_pause': req_guest_pause,
    'guest_unpause': req_guest_unpause,
    'guest_reboot': req_guest_reboot,
    'guest_reset': req_guest_reset,
    'guest_get_console_output': req_guest_get_console_output,
    'guest_capture': req_guest_capture,
    'guest_deploy': req_guest_deploy,
    'guest_get_info': req_guest_get_info,
    'guest_get_nic_vswitch_info': req_guest_get_nic_vswitch_info,
    'guest_create_nic': req_guest_create_nic,
    'guest_delete_nic': req_guest_delete_nic,
    'guest_nic_couple_to_vswitch': req_guest_nic_couple_to_vswitch,
    'guest_nic_uncouple_from_vswitch': req_guest_nic_uncouple_from_vswitch,
    'guest_create_network_interface': req_guest_create_network_interface,
    'guest_get_power_state': req_guest_get_power_state,
    'guest_create_disks': req_guest_create_disks,
    'guest_delete_disks': req_guest_delete_disks,
    'guest_config_minidisks': req_guest_config_minidisks,
    'volume_attach': req_volume_attach,
    'volume_detach': req_volume_detach,
    'host_get_info': req_host_get_info,
    'host_diskpool_get_info': req_host_diskpool_get_info,
    'image_import': req_image_import,
    'image_query': req_image_query,
    'image_delete': req_image_delete,
    'image_export': req_image_export,
    'image_get_root_disk_size': req_image_get_root_disk_size,
    'token_create': req_token_create,
    'vswitch_get_list': req_vswitch_get_list,
    'vswitch_create': req_vswitch_create,
    'vswitch_delete': req_vswitch_delete,
    'vswitch_grant_user': req_vswitch_grant_user,
    'vswitch_revoke_user': req_vswitch_revoke_user,
    'vswitch_set_vlan_id_for_user': req_vswitch_set_vlan_id_for_user,
}


class RESTClient(object):

    def __init__(self, ip='127.0.0.1', port=8888, timeout=30):
        self.base_url = "http://" + ip + ":" + str(port)

    def _tmp_token(self):
        expires = 30

        expired_elapse = datetime.timedelta(seconds=expires)
        expired_time = datetime.datetime.utcnow() + expired_elapse
        # payload = jwt.encode({'exp': expired_time}, CONF.wsgi.password)
        payload = jwt.encode({'exp': expired_time}, 'password')

        return payload

    def _get_token(self):
        _headers = {'Content-Type': 'application/json'}
        # _headers['X-Auth-User'] = CONF.wsgi.user
        # _headers['X-Auth-Password'] = CONF.wsgi.password

        url = self.base_url + '/token'
        method = 'POST'
        response = requests.request(method, url, headers=_headers)
        token = response.headers['X-Auth-Token']

        return token

    def _get_url_body(self, api_name, method, *args, **kwargs):
        count_params_in_path = PARAM_IN_PATH[api_name]
        func = API2REQ[api_name]
        url, body = func(count_params_in_path, *args, **kwargs)
        if count_params_in_path > 0:
            full_url = url % tuple(args[0:count_params_in_path])
        else:
            full_url = url
        return full_url, body

    def _process_rest_response(self, response):
        res_dict = json.loads(response.content)
        # return res_dict.get('output', None)
        return res_dict

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
        # check api_name exist or not
        if api_name not in API2METHOD.keys():
            strError = {'msg': 'API name for RESTClient not exist.'}
            results = INVALID_API_ERROR[0]
            results.update({'rs': 1,
                            'errmsg': INVALID_API_ERROR[1][1] % strError,
                            'output': ''})
            return results
        # get method by api_name
        method = API2METHOD[api_name]
        # get url,body with api_name and method
        url, body = self._get_url_body(api_name, method, *args, **kwargs)
        try:
            if body is None:
                response = self.api_request(url, method)
            else:
                body = json.dumps(body)
                response = self.api_request(url, method, body)
            # change response to SDK format
            results = self._process_rest_response(response)
        except Exception as err:
            errmsg = REST_REQUEST_ERROR[1][1] % {'error': six.text_type(err)}
            results = REST_REQUEST_ERROR[0]
            results.update({'rs': 1, 'errmsg': errmsg, 'output': ''})

        return results
