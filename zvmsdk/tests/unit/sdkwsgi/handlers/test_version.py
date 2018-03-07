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

import json
import mock
import unittest

from zvmsdk.sdkwsgi.handlers import version
from zvmsdk import version as sdk_version


class HandlersRootTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_version(self):
        req = mock.Mock()
        ver_str = {"rc": 0,
                   "overallRC": 0,
                   "errmsg": "",
                   "modID": None,
                   "output":
                   {"api_version": version.APIVERSION,
                    "min_version": version.APIVERSION,
                    "version": sdk_version.__version__,
                    "max_version": version.APIVERSION,
                    },
                   "rs": 0}
        res = version.version(req)
        self.assertEqual('application/json', req.response.content_type)
        # version_json = json.dumps(ver_res)
        # version_str = utils.to_utf8(version_json)
        ver_res = json.loads(req.response.body.decode('utf-8'))
        self.assertEqual(ver_str, ver_res)
        self.assertEqual('application/json', res.content_type)
