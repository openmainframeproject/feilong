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


import requests

from zvmsdk import config


CONF = config.CONF


API2URL = {
    'host_get_info': '/host',
    'guest_get_info': '/guest/{userid}/info',
}


API2METHOD = {
    'host_get_info': 'GET',
    'guest_get_info': 'GET',
    'guest_update': 'PUT',
}


API2BODY = {
    'host_get_info': None,
    'guest_get_info': None,
    'guest_update': body_guest_update,
}


class RESTClient(object):

    def __init__(self, ip, port, timeout):
        self.base_url = "http://"+ ip + ":" + port

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
            func = API2BODY[api_name]
            return func(*args, **kwargs)
        return None

    def request(self, url, method, body, headers=None):
        _headers = {'Content-Type': 'application/json'}
        _headers.update(headers or {})

        _headers['X-Auth-Token'] = self._get_token()

        response = requests.request(method, url, data=body, headers=_headers)
        return response

    def api_request(self, url, method='GET', body=None):

        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body)

    def call(self, api_name, *args, **kwargs):
        url = API2URL[api_name]
        method = API2METHOD[api_name]
        # generate body from args and kwargs
        body = self._get_body(api_name, *args, **kwargs)
        self.api_request(url, method, body)


def body_guest_update(*args, **kwargs):
    return None
