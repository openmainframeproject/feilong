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

import random
import re
import unittest

from zvmsdk.tests.fvt import test_utils
from zvmsdk.tests.fvt import test_guest
from zvmsdk.tests.fvt import test_host
from zvmsdk.tests.fvt import test_image
from zvmsdk.tests.fvt import test_version


TEST_IMAGE_LIST = test_utils.TEST_IMAGE_LIST
rdm_idx = random.randint(0, len(TEST_IMAGE_LIST) - 1)

bvt_testcases = [
    test_guest.GuestHandlerTestCase("test_guest_create_with_profile_multiple_disks_with_vdev")
    test_guest.GuestHandlerTestCase("test_guest_create_with_ipl_cms")
]


bvt = unittest.TestSuite()
bvt.addTests(bvt_testcases)
