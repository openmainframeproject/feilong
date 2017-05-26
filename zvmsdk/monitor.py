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

import time


class MeteringCache(object):
    """Cache for metering data."""
    _CTYPES = ('cpumem', 'vnics')

    def __init__(self):
        self._reset()

    def _reset(self):
        for type in self._CTYPES:
            self.cache[type]['expiration'] = time.time()
            self.cache[type]['data'] = {}

    def set(self, ctype, data):
        """Set or update cache content.

        @ctype:    cache type.
        @data:    cache data.
        """
        self.cache[ctype]['data'][data['userid']] = data

    def get(self, ctype, userid):
        if(time.time() > self.cache[ctype]['expiration']):
            return None
        else:
            return self.cache[ctype]['data'].get(userid, None)

    def delete(self, ctype, userid):
        if userid in self.cache[ctype]['data']:
            del self.cache[ctype]['data'][userid]

    def clear(self, ctype='all'):
        if ctype == 'all':
            self._reset()
        else:
            if ctype in self._CTYPES:
                self.cache[ctype]['data'] = {}
