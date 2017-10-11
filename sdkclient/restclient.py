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


USERID_IN_PATH = {
    'host_get_info': False,
    'guest_get_info': True,
    'guest_update': True,
    'guest_create': False,
    'guest_action': True,
}


API2URL = {
    'host_get_info': '/host',
    'guest_get_info': '/guests/{userid}/info',
    'guest_update': '/guests/{userid}',
    'guest_create': '/guests',
    'guest_action': '/guests/%s/action',
}


API2METHOD = {
    'host_get_info': 'GET',
    'guest_get_info': 'GET',
    'guest_update': 'PUT',
    'guest_create': 'POST',
    'guest_action': 'POST',
}


API2BODY = {
    'host_get_info': None,
    'guest_get_info': None,
    'guest_update': 'body_guest_update',
    'guest_create': 'body_guest_create',
    'guest_action': 'body_guest_action',
}


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
        if USERID_IN_PATH[api_name]:
            url = API2URL[api_name] % args[0]
        else:
            url = API2URL[api_name]
        method = API2METHOD[api_name]
        # generate body from args and kwargs
        body = self._get_body(api_name, *args, **kwargs)
        # response with JSON format
        response = self.api_request(url, method, body)
        # change response to SDK format
        result = self._process_rest_response(response)
        return result


def body_guest_update(*args, **kwargs):
    return None


def body_guest_create(*args, **kwargs):
    body = {'guest': {'userid': args[0],
                      'vcpus': args[1],
                      'memory': args[2],
                      'disk_list': kwargs.get('disk_list', None),
                      'user_profile': kwargs.get('user_profile', None)}}
    body_str = json.dumps(body)
    return body_str


def body_guest_action(*args, **kwargs):
    body = {'action': args[1]}
    body_str = json.dumps(body)
    return body_str
