#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

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

import unittest

from zvmsdk.sdkwsgi import util


class SDKWsgiUtilsTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(SDKWsgiUtilsTestCase, self).__init__(methodName)

    def test_get_http_code_from_sdk_return(self):
        msg = {}
        msg['overallRC'] = 404
        ret = util.get_http_code_from_sdk_return(msg, default=201)
        self.assertEqual(404, ret)

        msg['overallRC'] = 400
        ret = util.get_http_code_from_sdk_return(msg)
        self.assertEqual(400, ret)

        msg['overallRC'] = 100
        ret = util.get_http_code_from_sdk_return(msg, default=200)
        self.assertEqual(400, ret)

        msg['overallRC'] = 0
        ret = util.get_http_code_from_sdk_return(msg, default=204)
        self.assertEqual(204, ret)

        msg['overallRC'] = 300
        ret = util.get_http_code_from_sdk_return(msg, default=201)
        self.assertEqual(500, ret)

    def test_get_http_code_from_sdk_return_with_already_exist(self):
        msg = {}
        msg['overallRC'] = 8
        msg['rc'] = 212
        msg['rs'] = 36

        ret = util.get_http_code_from_sdk_return(msg,
            additional_handler=util.handle_already_exists)
        self.assertEqual(409, ret)

        msg['rc'] = 100
        ret = util.get_http_code_from_sdk_return(msg,
            additional_handler=util.handle_already_exists)
        self.assertEqual(500, ret)

    def test_mask_tuple_password(self):
        source = [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '0'),
            ('X-Auth-Token', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAi'
                             'OjE2NTgyODEwODR9.LiUjn4yK7SNdsdArrgFBRr0wk9L_C'
                             'la7QQFxW94o3aw'),
            ('cache-control', 'no-cache')]
        target = [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '0'),
            ('X-Auth-Token', '***'),
            ('cache-control', 'no-cache')]
        ret = util.mask_tuple_password(source)
        self.assertEqual(ret, target)
        source = [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '0'),
            ('X-Auth-Token', ''),
            ('cache-control', 'no-cache')]
        target = [
            ('Content-Type', 'text/html; charset=UTF-8'),
            ('Content-Length', '0'),
            ('X-Auth-Token', '***'),
            ('cache-control', 'no-cache')]
        ret = util.mask_tuple_password(source)
        self.assertEqual(ret, target)
