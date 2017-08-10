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


from zvmsdk import client as zvmclient
from zvmsdk import smutclient
from zvmsdk import xcatclient
from zvmsdk import config
from zvmsdk.tests.unit import base


CONF = config.CONF


class SDKZVMClientTestCase(base.SDKTestCase):
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()

    def test_get_zvmclient(self):
        self._zvmclient = zvmclient.get_zvmclient()
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self._zvmclient, xcatclient.XCATClient))
        elif CONF.zvm.client_type == 'smut':
            self.assertTrue(isinstance(self._zvmclient,
                                       smutclient.SMUTsClient))
