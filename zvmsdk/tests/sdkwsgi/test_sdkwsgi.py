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

import requests
import os

from zvmsdk import config


CONF = config.CONF


class TestSDKClient(object):

    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"

    def _get_admin_token(self, path):
        token = ''
        if os.path.exists(path):
            with open(path, 'r') as fd:
                token = fd.read().strip()
        return token

    def _get_token(self):
        _headers = {'Content-Type': 'application/json'}
        path = '/etc/zvmsdk/token.dat'
        default_admin_token = self._get_admin_token(path)
        _headers['X-Admin-Token'] = default_admin_token

        url = self.base_url + '/token'
        method = 'POST'
        response = requests.request(method, url, headers=_headers)
        token = response.headers['X-Auth-Token']

        return token

    def request(self, url, method, body, headers=None):
        _headers = {'Content-Type': 'application/json'}
        _headers.update(headers or {})

        # Add token here so every request will validate before proceed
        _headers['X-Auth-Token'] = self._get_token()

        response = requests.request(method, url, data=body, headers=_headers)
        return response

    def api_request(self, url, method='GET', body=None):

        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body)
