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


import mock


from zvmsdk import client
from zvmsdk import exception
from zvmsdk import utils as zvmutils
from zvmsdk.config import CONF
from zvmsdk.tests.unit import base


class SDKZVMClientTestCase(base.SDKTestCase):
    """Testcases for compute APIs."""
    def setUp(self):
        super(SDKZVMClientTestCase, self).setUp()
        self.zvmclient = client.get_zvmclient()

    def test_get_zvmclient(self):
        if CONF.zvm.client_type == 'xcat':
            self.assertTrue(isinstance(self.zvmclient, client.XCATClient))


class SDKXCATCientTestCases(SDKZVMClientTestCase):
    """Test cases for xcat zvm client."""

    def setUp(self):
        super(SDKXCATCientTestCases, self).setUp()

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_mac(self, xrequest):
        xrequest.return_value = ["fakereturn: 1234"]
        url = "/xcatws/tables/mac?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode mac"
        body = [commands]

        info = self.zvmclient._delete_mac("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info["fakereturn"], 1234)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_mac_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self.zvmclient._delete_mac, 'fakenode')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_switch(self, xrequest):
        xrequest.return_value = ["fakereturn: 1234"]
        url = "/xcatws/tables/switch?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode switch"
        body = [commands]

        info = self.zvmclient._delete_switch("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info["fakereturn"], 1234)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_switch_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self.zvmclient._delete_switch, 'fakenode')

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_host(self, xrequest):
        xrequest.return_value = ["fakereturn: 1234"]
        url = "/xcatws/tables/hosts?userName=" +\
                CONF.xcat.username + "&password=" +\
                CONF.xcat.password + "&format=json"
        commands = "-d node=fakenode hosts"
        body = [mac_commands]

        info = self.zvmclient._delete_host("fakenode")
        xrequest.assert_called_once_with("PUT", url, body)
        self.assertEqual(info["fakereturn"], 1234)

    @mock.patch.object(zvmutils, 'xcat_request')
    def test_delete_host_fail(self, xrequest):
        xrequest.side_effect = exception.ZVMNetworkError(msg='msg')
        self.assertRaises(exception.ZVMNetworkError,
                          self.zvmclient._delete_host, 'fakenode')
