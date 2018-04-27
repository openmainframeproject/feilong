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

import json
import os
import requests
import six
import threading

# TODO:set up configuration file only for RESTClient and configure this value
TOKEN_LOCK = threading.Lock()

REST_REQUEST_ERROR = [{'overallRC': 101, 'modID': 110, 'rc': 101},
                      {1: "Request to zVM Cloud Connector failed: %(error)s",
                       2: "Token file not found: %(error)s",
                       3: "Request to url: %(url)s got unexpected response: "
                       "status_code: %(status)s, reason: %(reason)s, "
                       "text: %(text)s",
                       4: "Get Token failed: %(error)s"},
                       "zVM Cloud Connector request failed",
                       ]
SERVICE_UNAVAILABLE_ERROR = [{'overallRC': 503, 'modID': 110, 'rc': 503},
                             {2: "Service is unavailable. reason: %(reason)s,"
                              " text: %(text)s"},
                             "Service is unavailable",
                             ]
INVALID_API_ERROR = [{'overallRC': 400, 'modID': 110, 'rc': 400},
                     {1: "Invalid API name, '%(msg)s'"},
                     "Invalid API name",
                     ]


class UnexpectedResponse(Exception):
    def __init__(self, resp):
        self.resp = resp


class ServiceUnavailable(Exception):
    def __init__(self, resp):
        self.resp = resp


class TokenNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class TokenFileOpenError(Exception):
    def __init__(self, msg):
        self.msg = msg


class CACertNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class APINameNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ArgsFormatError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def fill_kwargs_in_body(body, **kwargs):
    for key in kwargs.keys():
        body[key] = kwargs.get(key)


def req_version(start_index, *args, **kwargs):
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


def req_guest_live_resize_cpus(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'live_resize_cpus',
            'cpu_cnt': args[start_index]}
    return url, body


def req_guest_capture(start_index, *args, **kwargs):
    url = '/guests/%s/action'
    body = {'action': 'capture',
            'image': args[start_index]}
    fill_kwargs_in_body(body, **kwargs)
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


def req_guest_delete_network_interface(start_index, *args, **kwargs):
    url = '/guests/%s/interface'
    body = {'interface': {'os_version': args[start_index],
                          'vdev': args[start_index + 1]}}
    fill_kwargs_in_body(body['interface'], **kwargs)
    return url, body


def req_guest_get_power_state(start_index, *args, **kwargs):
    url = '/guests/%s/power_state'
    body = None
    return url, body


def req_guest_create_disks(start_index, *args, **kwargs):
    url = '/guests/%s/disks'
    body = {'disk_info': {'disk_list': args[start_index]}}
    return url, body


def req_guest_delete_disks(start_index, *args, **kwargs):
    url = '/guests/%s/disks'
    body = {'vdev_info': {'vdev_list': args[start_index]}}
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
    url = '/host/diskpool'
    poolname = kwargs.get('disk_pool', None)
    append = ''
    if poolname is not None:
        append += "?poolname=%s" % poolname
    url += append
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


def req_vswitch_query(start_index, *args, **kwargs):
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


# Save data used for comprsing RESTful request
# method: request type
# args_required: arguments in args are required, record the count here.
#                if len(args) not equal to this number, raise exception
# params_path: parameters amount in url path
# request: function that provide url and body for comprosing a request
DATABASE = {
    'version': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_version},
    'guest_create': {
        'method': 'POST',
        'args_required': 3,
        'params_path': 0,
        'request': req_guest_create},
    'guest_list': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_guest_list},
    'guest_inspect_stats': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_inspect_stats},
    'guest_inspect_vnics': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_inspect_vnics},
    'guests_get_nic_info': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_guests_get_nic_info},
    'guest_delete': {
        'method': 'DELETE',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_delete},
    'guest_get_definition_info': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_get_definition_info},
    'guest_start': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_start},
    'guest_stop': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_stop},
    'guest_softstop': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_softstop},
    'guest_pause': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_pause},
    'guest_unpause': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_unpause},
    'guest_reboot': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_reboot},
    'guest_reset': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_reset},
    'guest_get_console_output': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_get_console_output},
    'guest_live_resize_cpus': {
        'method': 'POST',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_live_resize_cpus},
    'guest_capture': {
        'method': 'POST',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_capture},
    'guest_deploy': {
        'method': 'POST',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_deploy},
    'guest_get_info': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_get_info},
    'guest_get_nic_vswitch_info': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_get_nic_vswitch_info},
    'guest_create_nic': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_create_nic},
    'guest_delete_nic': {
        'method': 'DELETE',
        'args_required': 2,
        'params_path': 2,
        'request': req_guest_delete_nic},
    'guest_nic_couple_to_vswitch': {
        'method': 'PUT',
        'args_required': 3,
        'params_path': 2,
        'request': req_guest_nic_couple_to_vswitch},
    'guest_nic_uncouple_from_vswitch': {
        'method': 'PUT',
        'args_required': 2,
        'params_path': 2,
        'request': req_guest_nic_uncouple_from_vswitch},
    'guest_create_network_interface': {
        'method': 'POST',
        'args_required': 3,
        'params_path': 1,
        'request': req_guest_create_network_interface},
    'guest_delete_network_interface': {
        'method': 'DELETE',
        'args_required': 3,
        'params_path': 1,
        'request': req_guest_delete_network_interface},
    'guest_get_power_state': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_guest_get_power_state},
    'guest_create_disks': {
        'method': 'POST',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_create_disks},
    'guest_delete_disks': {
        'method': 'DELETE',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_delete_disks},
    'guest_config_minidisks': {
        'method': 'PUT',
        'args_required': 2,
        'params_path': 1,
        'request': req_guest_config_minidisks},
    'volume_attach': {
        'method': 'POST',
        'args_required': 3,
        'params_path': 1,
        'request': req_volume_attach},
    'volume_detach': {
        'method': 'DELETE',
        'args_required': 3,
        'params_path': 1,
        'request': req_volume_detach},
    'host_get_info': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_host_get_info},
    'host_diskpool_get_info': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_host_diskpool_get_info},
    'image_import': {
        'method': 'POST',
        'args_required': 3,
        'params_path': 0,
        'request': req_image_import},
    'image_query': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_image_query},
    'image_delete': {
        'method': 'DELETE',
        'args_required': 1,
        'params_path': 1,
        'request': req_image_delete},
    'image_export': {
        'method': 'PUT',
        'args_required': 2,
        'params_path': 1,
        'request': req_image_export},
    'image_get_root_disk_size': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_image_get_root_disk_size},
    'token_create': {
        'method': 'POST',
        'args_required': 0,
        'params_path': 0,
        'request': req_token_create},
    'vswitch_get_list': {
        'method': 'GET',
        'args_required': 0,
        'params_path': 0,
        'request': req_vswitch_get_list},
    'vswitch_create': {
        'method': 'POST',
        'args_required': 1,
        'params_path': 0,
        'request': req_vswitch_create},
    'vswitch_delete': {
        'method': 'DELETE',
        'args_required': 1,
        'params_path': 1,
        'request': req_vswitch_delete},
    'vswitch_grant_user': {
        'method': 'PUT',
        'args_required': 2,
        'params_path': 1,
        'request': req_vswitch_grant_user},
    'vswitch_query': {
        'method': 'GET',
        'args_required': 1,
        'params_path': 1,
        'request': req_vswitch_query},
    'vswitch_revoke_user': {
        'method': 'PUT',
        'args_required': 2,
        'params_path': 1,
        'request': req_vswitch_revoke_user},
    'vswitch_set_vlan_id_for_user': {
        'method': 'PUT',
        'args_required': 3,
        'params_path': 1,
        'request': req_vswitch_set_vlan_id_for_user},
}


class RESTClient(object):

    def __init__(self, ip='127.0.0.1', port=8888,
                 ssl_enabled=False, verify=False,
                 token_path='/etc/zvmsdk/token.dat'):
        # SSL enable or not
        if ssl_enabled:
            self.base_url = "https://" + ip + ":" + str(port)
        else:
            self.base_url = "http://" + ip + ":" + str(port)
        # if value of verify is str, means its value is
        # the path of CA certificate
        if type(verify) == str:
            if not os.path.exists(verify):
                raise CACertNotFound('CA certificate file not found.')
        self.verify = verify
        self.token_path = token_path

    def _check_arguments(self, api_name, *args, **kwargs):
        # check api_name exist or not
        if api_name not in DATABASE.keys():
            msg = "API name %s not exist." % api_name
            raise APINameNotFound(msg)
        # check args count is valid
        count = DATABASE[api_name]['args_required']
        if len(args) < count:
            msg = "Missing some args,please check:%s." % args
            raise ArgsFormatError(msg)
        if len(args) > count:
            msg = "Too many args,please check:%s." % args
            raise ArgsFormatError(msg)

    def _get_admin_token(self, path):
        if os.path.exists(path):
            TOKEN_LOCK.acquire()
            try:
                with open(path, 'r') as fd:
                    token = fd.read().strip()
            except Exception:
                raise TokenFileOpenError('token file open failed.')
            finally:
                TOKEN_LOCK.release()
        else:
            raise TokenNotFound('token file not found.')
        return token

    def _get_token(self):
        _headers = {'Content-Type': 'application/json'}
        admin_token = self._get_admin_token(self.token_path)
        _headers['X-Admin-Token'] = admin_token

        url = self.base_url + '/token'
        method = 'POST'
        response = requests.request(method, url, headers=_headers,
                                    verify=self.verify)
        if response.status_code == 503:
            # service unavailable
            raise ServiceUnavailable(response)
        else:
            try:
                token = response.headers['X-Auth-Token']
            except KeyError:
                raise UnexpectedResponse(response)

        return token

    def _get_url_body(self, api_name, method, *args, **kwargs):
        count_params_in_path = DATABASE[api_name]['params_path']
        func = DATABASE[api_name]['request']
        url, body = func(count_params_in_path, *args, **kwargs)
        if count_params_in_path > 0:
            full_url = url % tuple(args[0:count_params_in_path])
        else:
            full_url = url
        return full_url, body

    def _process_rest_response(self, response):
        if 'application/json' in response.headers['Content-Type']:
            res_dict = json.loads(response.content)
            # return res_dict.get('output', None)
            return res_dict
        else:
            # Currently, all the response content from zvmsdk wsgi are
            # 'application/json' type. If it is not, the response may be
            # sent by HTTP server due to internal server error or time out,
            # it is an unexpected response to the rest client.
            # If new content-type is added to the response by sdkwsgi, the
            # parsing function here is also required to change.
            raise UnexpectedResponse(response)

    def request(self, url, method, body, headers=None):
        _headers = {'Content-Type': 'application/json'}
        _headers.update(headers or {})

        _headers['X-Auth-Token'] = self._get_token()
        response = requests.request(method, url, data=body, headers=_headers,
                                    verify=self.verify)
        return response

    def api_request(self, url, method='GET', body=None):
        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body)

    def call(self, api_name, *args, **kwargs):
        try:
            # check validation of arguments
            self._check_arguments(api_name, *args, **kwargs)
            # get method by api_name
            method = DATABASE[api_name]['method']
            # get url,body with api_name and method
            url, body = self._get_url_body(api_name, method, *args, **kwargs)
            if body is None:
                response = self.api_request(url, method)
            else:
                body = json.dumps(body)
                response = self.api_request(url, method, body)
            # change response to SDK format
            results = self._process_rest_response(response)

        except TokenFileOpenError as err:
            errmsg = REST_REQUEST_ERROR[1][4] % {'error': err.msg}
            results = REST_REQUEST_ERROR[0]
            results.update({'rs': 4, 'errmsg': errmsg, 'output': ''})
        except TokenNotFound as err:
            errmsg = REST_REQUEST_ERROR[1][2] % {'error': err.msg}
            results = REST_REQUEST_ERROR[0]
            results.update({'rs': 2, 'errmsg': errmsg, 'output': ''})
        except UnexpectedResponse as err:
            errmsg = REST_REQUEST_ERROR[1][3] % ({
                'url': err.resp.url, 'status': err.resp.status_code,
                'reason': err.resp.reason, 'text': err.resp.text})
            results = REST_REQUEST_ERROR[0]
            results.update({'rs': 3, 'errmsg': errmsg, 'output': ''})
        except ServiceUnavailable as err:
            errmsg = SERVICE_UNAVAILABLE_ERROR[1][2] % {
                'reason': err.resp.reason, 'text': err.resp.text}
            results = SERVICE_UNAVAILABLE_ERROR[0]
            results.update({'rs': 2, 'errmsg': errmsg, 'output': ''})
        except Exception as err:
            errmsg = REST_REQUEST_ERROR[1][1] % {'error': six.text_type(err)}
            results = REST_REQUEST_ERROR[0]
            results.update({'rs': 1, 'errmsg': errmsg, 'output': ''})

        return results
