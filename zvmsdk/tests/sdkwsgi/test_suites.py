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

import unittest

from zvmsdk.tests.sdkwsgi import test_guest
from zvmsdk.tests.sdkwsgi import test_host
from zvmsdk.tests.sdkwsgi import test_image
from zvmsdk.tests.sdkwsgi import test_version


bvt_testcases = [
    test_guest.GuestHandlerTestCase("test_guest_create_deploy_capture_delete"),
    test_host.HostTestCase("test_host_info"),
    test_image.ImageTestCase("test_image_create_delete"),
    test_version.VersionTestCase("test_version"),
]


bvt = unittest.TestSuite()
bvt.addTests(bvt_testcases)
