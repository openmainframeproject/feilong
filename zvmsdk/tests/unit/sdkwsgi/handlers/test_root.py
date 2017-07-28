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
import mock
import unittest

from zvmsdk.sdkwsgi.handlers import root
from zvmsdk import utils


class HandlersRootTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_root(self):
        req = mock.Mock()
        version = {"versions": [{"version": "1.0",
                                 "max_version": "1.0",
                                 "min_version": "1.0"}]}
        res = root.home(req)
        self.assertEqual('application/json', req.response.content_type)
        version_json = json.dumps(version)
        version_str = utils.to_utf8(version_json)
        self.assertEqual(version_str, req.response.body)
        self.assertEqual('application/json', res.content_type)
