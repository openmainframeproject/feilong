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
import time
import unittest

from sdkclient import client
from zvmsdk import config
from zvmsdk.tests.sdkwsgi import api_sample


CONF = config.CONF
CONN_REST = 'rest'
CONN_SOCKET = 'socket'


class SDKClientTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(SDKClientTestCase, self).__init__(methodName)
        self.apibase = api_sample.APITestBase()
        self.restclient = client.SDKClient(connection_type=CONN_REST,
                                           port=8888)
        self.sockclient = client.SDKClient(connection_type=CONN_SOCKET)
        self.userid_rest = 'RESTT%03d' % (time.time() % 1000)
        self.userid_sock = 'SOCKT%03d' % (time.time() % 1000)

    def setUp(self):
        pass

    def _guest_create(self, conn_type):
        api_name = 'guest_create'
        vcpus = 1
        memory = 1024
        disks = [{'size': '3g', 'is_boot_disk': True}]
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid, vcpus,
                                               memory, disk_list=disks)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid, vcpus,
                                               memory, disk_list=disks)
        return res

    def _guest_delete(self, conn_type):
        api_name = 'guest_delete'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_start(self, conn_type):
        api_name = 'guest_start'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_stop(self, conn_type):
        api_name = 'guest_stop'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_deploy(self, conn_type, vdev=None, image=None):
        api_name = 'guest_deploy'
        if image is None:
            image = 'rhel67eckd_small_1100cyl.img'
        if vdev is None:
            vdev = '100'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid, image,
                                               vdev=vdev)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid, image,
                                               vdev=vdev)
        return res

    def _image_create(self, conn_type):
        image_fname = 'rhel67eckd_small_1100cyl.img'
        image_fpath = CONF.tests.image_path
        url = "file://" + image_fpath
        image_meta = {"os_version": "rhel6.7"}
        api_name = 'image_import'
        if conn_type == CONN_REST:
            res = self.restclient.send_request(api_name, image_fname, url,
                                               image_meta)
        else:
            res = self.sockclient.send_request(api_name, image_fname, url,
                                               image_meta)
        return res

    def _guest_create_nic(self, conn_type, vdev="1000"):
        api_name = 'guest_create_nic'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid, vdev=vdev)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid, vdev=vdev)
        return res

    def _guest_delete_nic(self, conn_type, vdev="1000"):
        api_name = 'guest_delete_nic'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid, vdev)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid, vdev)
        return res

    def _guest_get_definition_info(self, conn_type):
        api_name = 'guest_get_definition_info'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_get_info(self, conn_type):
        api_name = 'guest_get_info'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.sockclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_get_power_state(self, conn_type):
        api_name = 'guest_get_power_state'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_inspect_stats(self, conn_type):
        api_name = 'guest_inspect_stats'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _guest_get_vnics_info(self, conn_type):
        api_name = 'guest_inspect_vnics'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid)
        return res

    def _vswitch_create(self, conn_type):
        api_name = 'vswitch_create'
        if conn_type == CONN_REST:
            vsw_name = 'RESTVSW1'
            rdev = '2000'
            res = self.restclient.send_request(api_name, vsw_name, rdev=rdev)
        else:
            vsw_name = 'SOCKVSW1'
            rdev = '2000'
            res = self.sockclient.send_request(api_name, vsw_name, rdev=rdev)
        return res

    def _vswitch_delete(self, conn_type, vsw_name=None):
        api_name = 'vswitch_delete'
        vswitch_name = vsw_name
        if conn_type == CONN_REST:
            if vsw_name is None:
                vswitch_name = 'RESTVSW1'
            res = self.sockclient.send_request(api_name, vswitch_name)
        else:
            if vsw_name is None:
                vswitch_name = 'SOCKVSW1'
            res = self.sockclient.send_request(api_name, vswitch_name)
        return res

    def _vswitch_couple(self, conn_type, vsw=None, vdev="2000"):
        api_name = 'guest_nic_couple_to_vswitch'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            vswitch = vsw
            if vsw is None:
                vswitch = 'RESTVSW1'
            res = self.restclient.send_request(api_name, userid, vdev,
                                               vswitch)
        else:
            userid = self.userid_sock
            vswitch = vsw
            if vsw is None:
                vswitch = 'SOCKVSW1'
            res = self.sockclient.send_request(api_name, userid, vdev,
                                               vswitch)
        return res

    def _vswitch_uncouple(self, conn_type, vdev="2000"):
        api_name = 'guest_nic_uncouple_from_vswitch'
        if conn_type == CONN_REST:
            userid = self.userid_rest
            res = self.restclient.send_request(api_name, userid, vdev)
        else:
            userid = self.userid_sock
            res = self.sockclient.send_request(api_name, userid, vdev)
        return res

    def test_guest_create_delete(self):
        resp_rest = self._guest_create(CONN_REST)
        resp_sock = self._guest_create(CONN_SOCKET)
        self.assertEqual(resp_rest, resp_sock)

        try:
            resp_rest = self._guest_deploy(CONN_REST)
            resp_sock = self._guest_deploy(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._guest_create_nic(CONN_REST)
            resp_sock = self._guest_create_nic(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._guest_get_definition_info(CONN_REST)
            resp_sock = self._guest_get_definition_info(CONN_SOCKET)
            # FIXME:definition info must be defferent
            resp = json.dumps(resp_sock)
            self.apibase.verify_result('test_guest_get', resp)

            resp_rest = self._guest_get_info(CONN_REST)
            resp_sock = self._guest_get_info(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)
            resp = json.dumps(resp_sock)
            self.apibase.verify_result('test_guest_get_info', resp)

            resp_rest = self._guest_get_power_state(CONN_REST)
            resp_sock = self._guest_get_power_state(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)
            resp = json.dumps(resp_sock)
            self.apibase.verify_result('test_guest_get_power_state',
                                       resp)

            resp_rest = self._guest_inspect_stats(CONN_REST)
            resp_sock = self._guest_inspect_stats(CONN_SOCKET)
            resp = json.dumps(resp_sock)
            self.apibase.verify_result('test_guests_get_stats',
                                       resp)

            resp_rest = self._guest_get_vnics_info(CONN_REST)
            resp_sock = self._guest_get_vnics_info(CONN_SOCKET)
            resp = json.dumps(resp_sock)
            self.apibase.verify_result('test_guests_get_vnics_info',
                                       resp)

            resp_rest = self._guest_create_nic(CONN_REST, "2000")
            resp_sock = self._guest_create_nic(CONN_SOCKET, "2000")
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._vswitch_create(CONN_REST)
            resp_sock = self._vswitch_create(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._vswitch_couple(CONN_REST)
            resp_sock = self._vswitch_couple(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._vswitch_uncouple(CONN_REST)
            resp_sock = self._vswitch_uncouple(CONN_SOCKET)
            self.assertEqual(resp_rest, resp_sock)

            resp_rest = self._guest_delete_nic(CONN_REST, '2000')
            resp_sock = self._guest_delete_nic(CONN_SOCKET, '2000')
            self.assertEqual(resp_rest, resp_sock)

            self._guest_stop(CONN_REST)
            self._guest_stop(CONN_SOCKET)

        except Exception as e:
            raise e
        finally:
            self._guest_delete(CONN_REST)
            self._guest_delete(CONN_SOCKET)
            self._vswitch_delete(CONN_REST)
            self._vswitch_delete(CONN_SOCKET)
