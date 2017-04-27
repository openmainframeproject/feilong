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

from zvmsdk import api
from zvmsdk.tests.unit import base


class SDKAPITestCase(base.SDKTestCase):
    """Testcases for compute APIs."""
    def setUp(self):
        super(SDKAPITestCase, self).setUp()
        self.api = api.SDKAPI()
        self._vmops = mock.MagicMock()

    def test_init_ComputeAPI(self):
        self.assertTrue(isinstance(self.api, api.SDKAPI))

    @mock.patch("zvmsdk.vmops.VMOps.get_info")
    def test_get_vm_info(self, ginfo):
        self.api.get_vm_info('fakevm')
        ginfo.assert_called_once_with('fakevm')

    def test_deploy_image_to_vm(self):
        self._vmops.deploy_image_to_vm(mock.sentinel.user_id,
                                mock.sentinel.image_name,
                                mock.sentinel.transportfiles,
                                mock.sentinel.vdev)
        self._vmops.deploy_image_to_vm.assert_called_with(
                                mock.sentinel.user_id,
                                mock.sentinel.image_name,
                                mock.sentinel.transportfiles,
                                mock.sentinel.vdev)
