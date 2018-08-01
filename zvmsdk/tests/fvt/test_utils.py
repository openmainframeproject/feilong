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
import os
import re
import requests
import shutil
import six
import tempfile
import time

from zvmsdk import api
from zvmsdk import config
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils


config.load_config()
CONF = config.CONF
TEST_IP_POOL = []
# This list contains list of tuples with info (name, path, distro)
TEST_IMAGE_LIST = []


def get_test_image_list():
    global TEST_IMAGES_LIST
    for image in CONF.tests.images.split(','):
        info = image.strip(' ').split(':')
        # use image_file_name-distro as the image name
        name = os.path.basename(info[0]) + '-' + info[1]
        TEST_IMAGE_LIST.append((name, info[0], info[1]))


# get image list from CONF
get_test_image_list()


class TestzCCClient(object):

    def __init__(self):
        self.base_url = CONF.tests.restapi_url

    def _get_admin_token(self, path):
        token = ''
        if os.path.exists(path):
            with open(path, 'r') as fd:
                token = fd.read().strip()
        return token

    def _get_token(self):
        _headers = {'Content-Type': 'application/json'}
        path = '/etc/zvmsdk/token.dat'
        default_admin_token = self._get_admin_token(path)
        _headers['X-Admin-Token'] = default_admin_token

        url = self.base_url + '/token'
        method = 'POST'
        response = requests.request(method, url, headers=_headers)
        token = response.headers['X-Auth-Token']

        return token

    def request(self, url, method, body, headers=None):
        _headers = {'Content-Type': 'application/json'}
        _headers.update(headers or {})

        # Add token here so every request will validate before proceed
        _headers['X-Auth-Token'] = self._get_token()

        response = requests.request(method, url, data=body, headers=_headers)
        return response

    def api_request(self, url, method='GET', body=None, headers=None):

        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body, headers)

    def image_query(self, image_name):
        url = '/images?imagename=%s' % image_name
        return self.api_request(url=url, method='GET')

    def image_import(self, image_path, os_version):
        image_name = os.path.basename(image_path)
        url = 'file://' + image_path
        image_meta = '''{"os_version": "%s"}''' % os_version

        body = """{"image": {"image_name": "%s",
                             "url": "%s",
                             "image_meta": %s}}""" % (image_name, url,
                                                      image_meta)

        return self.api_request(url='/images', method='POST', body=body)

    def image_export(self, image_name):
        url = '/images/%s' % image_name
        tempDir = tempfile.mkdtemp()
        os.chmod(tempDir, 0o777)
        dest_url = ''.join(['file://', tempDir, '/', image_name])
        body = """{"location": {"dest_url": "%s"}}""" % (dest_url)

        try:
            resp = self.api_request(url=url, method='PUT', body=body)
        finally:
            shutil.rmtree(tempDir)
        return resp

    def image_delete(self, image_name):
        url = '/images/%s' % image_name
        return self.api_request(url=url, method='DELETE')

    def image_get_root_disk_size(self, image_name):
        url = '/images/%s/root_disk_size' % image_name
        return self.api_request(url=url, method='GET')

    def _get_data_file(self, fpath):
        if fpath:
            return open(fpath, 'rb')

    def file_import(self, fpath):
        url = '/files'
        headers = {'Content-Type': 'application/octet-stream'}
        body = self._get_data_file(fpath)
        return self.api_request(url=url, method='PUT', body=body,
                                headers=headers)

    def file_export(self, fpath):
        url = '/files'
        headers = {'Content-Type': 'application/octet-stream'}
        body = {'source_file': fpath}
        body = json.dumps(body)
        return self.api_request(url=url, method='POST', body=body,
                                headers=headers)

    def guest_create(self, userid, vcpus=1, memory=2048,
                     disk_list=[{"size": "5500", "is_boot_disk": "True"}],
                     user_profile=CONF.zvm.user_profile,
                     max_cpu=CONF.zvm.user_default_max_cpu,
                     max_mem=CONF.zvm.user_default_max_memory):
        body = {"guest": {"userid": userid, "vcpus": vcpus,
                          "memory": memory, "disk_list": disk_list,
                          "user_profile": user_profile,
                          "max_cpu": max_cpu, "max_mem": max_mem}}
        body = json.dumps(body)
        return self.api_request(url='/guests', method='POST', body=body)

    def guest_delete(self, userid):
        url = '/guests/%s' % userid
        return self.api_request(url=url, method='DELETE')

    def guest_list(self):
        return self.api_request(url='/guests', method="GET")

    def _guest_action(self, userid, body):
        url = '/guests/%s/action' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_deploy(self, userid, image_name=None, transportfiles=None,
                     remotehost=None, vdev="100"):
        if transportfiles is not None:
            body = """{"action": "deploy",
                      "image": "%s",
                      "vdev": "%s",
                      "transportfiles": "%s"}""" % (image_name, vdev,
                                                    transportfiles)
        else:
            body = """{"action": "deploy",
                   "image": "%s",
                   "vdev": "%s"}""" % (image_name, vdev)

        return self._guest_action(userid, body)

    def guest_create_nic(self, userid, vdev="1000", nic_id=None,
                         mac_addr=None, active=False):
        content = {"nic": {"vdev": vdev}}
        if active:
            content["nic"]["active"] = "True"
        else:
            content["nic"]["active"] = "False"
        if nic_id is not None:
            content["nic"]["nic_id"] = nic_id

        if mac_addr is not None:
            content["nic"]["mac_addr"] = mac_addr

        body = json.dumps(content)
        url = '/guests/%s/nic' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_delete_nic(self, userid, vdev="1000", active=False):
        if active:
            body = '{"active": "True"}'
        else:
            body = '{"active": "False"}'

        url = '/guests/%s/nic/%s' % (userid, vdev)
        return self.api_request(url=url, method='DELETE', body=body)

    def guest_get_nic_vswitch_info(self, userid):
        # TODO: related rest api to be removed
        url = '/guests/%s/nic' % userid
        return self.api_request(url=url, method='GET')

    def guest_create_network_interface(self, userid, os_version,
                                       guest_networks, active=False):
        content = {"interface": {"os_version": os_version,
                                 "guest_networks": guest_networks}}
        if active:
            content["interface"]["active"] = "True"
        else:
            content["interface"]["active"] = "False"

        body = json.dumps(content)

        url = '/guests/%s/interface' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_delete_network_interface(self, userid,
                                       os_version,
                                       vdev="1000", active=False):
        content = {"interface": {"os_version": os_version,
                                 "vdev": vdev}}
        if active:
            content["interface"]["active"] = "True"
        else:
            content["interface"]["active"] = "False"
        body = json.dumps(content)

        url = '/guests/%s/interface' % userid
        return self.api_request(url=url, method='DELETE', body=body)

    def guest_nic_couple_to_vswitch(self, userid, nic_vdev,
                                    vswitch_name=CONF.tests.vswitch,
                                    active=False):
        if active:
            content = {"info": {"couple": "True",
                                "vswitch": vswitch_name, "active": True}}
        else:
            content = {"info": {"couple": "True",
                                "vswitch": vswitch_name, "active": False}}
        body = json.dumps(content)

        url = '/guests/%s/nic/%s' % (userid, nic_vdev)
        return self.api_request(url=url, method='PUT', body=body)

    def guest_nic_uncouple_from_vswitch(self, userid, nic_vdev, active=False):
        if active:
            body = '{"info": {"couple": "False", "active": "True"}}'
        else:
            body = '{"info": {"couple": "False", "active": "False"}}'

        url = '/guests/%s/nic/%s' % (userid, nic_vdev)
        return self.api_request(url=url, method='PUT', body=body)

    def guest_create_disks(self, userid, disk_list):
        content = {"disk_info": {"disk_list": disk_list}}
        body = json.dumps(content)
        url = '/guests/%s/disks' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_delete_disks(self, userid, disk_vdev_list):
        content = {"vdev_info": {"vdev_list": disk_vdev_list}}
        body = json.dumps(content)
        url = '/guests/%s/disks' % userid
        return self.api_request(url=url, method='DELETE', body=body)

    def guest_config_minidisks(self, userid, disk_list):
        disk_info = {"disk_info": {"disk_list": disk_list}}
        body = json.dumps(disk_info)
        url = '/guests/%s/disks' % userid

        return self.api_request(url=url, method='PUT', body=body)

    def guest_get_definition_info(self, userid):
        url = '/guests/%s' % userid
        return self.api_request(url=url, method='GET')

    def guest_get_info(self, userid):
        url = '/guests/%s/info' % userid
        return self.api_request(url=url, method='GET')

    def guest_get_power_state(self, userid):
        url = '/guests/%s/power_state' % userid
        return self.api_request(url=url, method='GET')

    def guest_start(self, userid):
        body = '{"action": "start"}'
        return self._guest_action(userid, body)

    def guest_stop(self, userid):
        body = '{"action": "stop", "timeout": 300, "poll_interval": 15}'
        return self._guest_action(userid, body)

    def guest_get_console_output(self, userid):
        body = '{"action": "get_console_output"}'
        return self._guest_action(userid, body)

    def guest_softstop(self, userid):
        body = '{"action": "softstop", "timeout": 300, "poll_interval": 20}'
        return self._guest_action(userid, body)

    def guest_capture(self, userid, image_name, capture_type='rootonly',
                       compress_level=6):
        body = {"action": "capture",
                "image": image_name,
                "capture_type": capture_type,
                "compress_level": compress_level}
        body = json.dumps(body)
        return self._guest_action(userid, body)

    def guest_pause(self, userid):
        body = '{"action": "pause"}'
        return self._guest_action(userid, body)

    def guest_unpause(self, userid):
        body = '{"action": "unpause"}'
        return self._guest_action(userid, body)

    def guest_reboot(self, userid):
        body = '{"action": "reboot"}'
        return self._guest_action(userid, body)

    def guest_resize_cpus(self, userid, cpu_cnt):
        body = """{"action": "resize_cpus",
                   "cpu_cnt": %s}""" % cpu_cnt
        return self._guest_action(userid, body)

    def guest_pre_migrate_vm(self, userid):
        body = {"action": "register_vm"}
        body = json.dumps(body)
        return self._guest_action(userid, body)

    def guest_live_migrate_vm(self, userid, destination,
                                         parms, operation):
        body = {"action": "live_migrate_vm",
                   "destination": destination,
                   "parms": parms,
                   "operation": operation}
        body = json.dumps(body)
        return self._guest_action(userid, body)

    def guest_live_resize_cpus(self, userid, cpu_cnt):
        body = """{"action": "live_resize_cpus",
                   "cpu_cnt": %s}""" % cpu_cnt
        return self._guest_action(userid, body)

    def guest_reset(self, userid):
        body = '{"action": "reset"}'
        return self._guest_action(userid, body)

    def guest_inspect_stats(self, userid):
        url = '/guests/stats?userid=%s' % userid
        return self.api_request(url=url, method='GET')

    def guest_inspect_vnics(self, userid=None):
        url = '/guests/interfacestats?userid=%s' % userid
        return self.api_request(url=url, method='GET')

    def guests_get_nic_info(self, userid=None, nic_id=None, vswitch=None):
        if ((userid is None) and
            (nic_id is None) and
            (vswitch is None)):
            append = ''
        else:
            append = "?"
            if userid is not None:
                append += 'userid=%s&' % userid
            if nic_id is not None:
                append += 'nic_id=%s&' % nic_id
            if vswitch is not None:
                append += 'vswitch=%s&' % vswitch
            append = append.strip('&')
        url = '/guests/nics%s' % append
        return self.api_request(url=url, method='GET')

    def vswitch_create(self, name, rdev=None, controller='*',
                       connection='CONNECT', network_type='ETHERNET',
                       router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                       gvrp='GVRP', queue_mem=8, native_vid=1,
                       persist=True):
        vsw_info = {'name': name,
                    'rdev': rdev,
                    'controller': controller,
                    'connection': connection,
                    'network_type': network_type,
                    'router': router,
                    'vid': vid,
                    'port_type': port_type,
                    'gvrp': gvrp,
                    'queue_mem': queue_mem,
                    'native_vid': native_vid,
                    'persist': persist}
        body = json.dumps({"vswitch": vsw_info})
        return self.api_request(url='/vswitches', method='POST', body=body)

    def vswitch_delete(self, vswitch_name):
        url = '/vswitches/%s' % vswitch_name
        return self.api_request(url=url, method='DELETE')

    def vswitch_get_list(self):
        return self.api_request(url='/vswitches', method='GET')

    def vswitch_query(self, vswitch_name):
        url = '/vswitches/%s' % vswitch_name
        return self.api_request(url=url, method='GET')

    def vswitch_grant_user(self, vswitch_name, userid):
        url = '/vswitches/%s' % vswitch_name
        body = '{"vswitch": {"grant_userid": "%s"}}' % userid
        return self.api_request(url=url, method='PUT', body=body)


class ZVMConnectorTestUtils(object):

    def __init__(self):
        self.client = TestzCCClient()
        self.rawapi = api.SDKAPI()
        self._smutclient = smutclient.get_smutclient()

    def generate_test_userid(self):
        '''Generate an userid base on time line.'''
        prefix = six.text_type(CONF.tests.userid_prefix)[-3:].rjust(3, 't')
        userid = prefix + '%05d' % ((time.time() * 10) % 100000)
        time.sleep(1)
        return userid.upper()

    def generate_test_ip(self):
        '''Generate test IP address.'''
        global TEST_IP_POOL
        if TEST_IP_POOL == []:
            TEST_IP_POOL = CONF.tests.ip_addr_list.split(' ')

        return TEST_IP_POOL.pop()

    def import_image_if_not_exist(self, image_path, os_version):

        # TODO: re-write once image_upload implemented. To support run fvt
        #       against remote zCC rest server
        image_name = os.path.basename(image_path)
        print("Checking if image %s exists or not, import it if not exists" %
              image_name)

        resp = self.client.image_query(image_name)
        if resp.status_code == 404:
            # image does not exist
            print('WARNING: image not exist, image_query failed with '
                  'reason : %s, will import image now' % resp.content)
            print("Importing image %s ..." % image_name)
            self.client.image_import(image_path, os_version)

        return image_name

    def get_image_root_disk_size(self, image_name):
        resp = self.client.image_get_root_disk_size(image_name)
        errmsg = "failed to get image root disk size for %s" % image_name
        assert resp.status_code == 200, errmsg
        return json.loads(resp.content)['output']

    def is_guest_exist(self, userid):
        cmd = 'sudo vmcp q %s' % userid
        output = zvmutils.execute(cmd)[1]
        if re.search('(^HCP\w\w\w003E)', output):
            # userid not exist
            return False
        return True

    def is_guest_reachable(self, userid):
        return self._smutclient.get_guest_connection_status(userid)

# Will use the first image as the default image to deploy guest.
    def deploy_guest(self, userid=None, cpu=1, memory=2048,
                     image_path=TEST_IMAGE_LIST[0][1],
                     os_version=TEST_IMAGE_LIST[0][2],
                     ip_addr=None):
        # Import image if specified, otherwise use the default image
        image_name = self.import_image_if_not_exist(image_path, os_version)
        print("Using image %s ..." % image_name)

        # Get available userid and ip from conf if not specified.
        userid = userid or self.generate_test_userid()
        ip_addr = ip_addr or self.generate_test_ip()
        print("Using userid %s and IP addr %s ..." % (userid, ip_addr))

        # Create vm in zVM
        size = self.get_image_root_disk_size(image_name)
        print("root disk size is %s" % size)
        disks_list = [{"size": size,
                       "is_boot_disk": True,
                       "disk_pool": CONF.zvm.disk_pool}]

        print("Creating userid %s ..." % userid)

        resp_gc = self.client.guest_create(userid, cpu, memory,
                                        disk_list=disks_list)
        assert resp_gc.status_code == 200, ("Failed to create userid %s" %
                                            userid)
        assert self.wait_until_create_userid_complete(userid)

        # Deploy image on vm
        # TODO: deploy with transportfiles specified
        print("Deploying userid %s ..." % userid)
        self.client.guest_deploy(userid, image_name)

        guest_networks = [{'ip_addr': ip_addr, 'cidr': CONF.tests.cidr}]
        resp_gcni = self.client.guest_create_network_interface(userid,
                                                   os_version, guest_networks)
        assert resp_gcni.status_code == 200, "Failed to create nif %s" % userid
        nic_vdev = json.loads(resp_gcni.content)['output'][0]['nic_vdev']

        self.client.guest_nic_couple_to_vswitch(userid, nic_vdev,
                                             CONF.tests.vswitch)
        self.client.vswitch_grant_user(CONF.tests.vswitch, userid)

        return userid, ip_addr

    def destroy_guest(self, userid):
        resp = self.client.guest_delete(userid)
        if resp.status_code != 200:
            print("WARNING: deleting userid failed: %s" % resp.content)

        self._wait_until(False, self.is_guest_exist, userid)

    def softstop_guest(self, userid):
        self.client.guest_softstop(userid)
        self.wait_until_guest_in_power_state(userid, 'off')

    def _wait_until(self, expect_state, func, *args, **kwargs):
        """Looping call func until get expected state, otherwise 1 min timeout.

        :param expect_state:    expected state
        :param func:            function or method to be called
        :param *args, **kwargs: parameters for the function
        """
        _inc_slp = [1, 2, 2, 5, 5, 5, 10, 10, 10, 10, 10, 15, 15, 20]
        # sleep intervals, total timeout 120 seconds
        for _slp in _inc_slp:
            real_state = func(*args, **kwargs)
            if real_state == expect_state:
                return True
            else:
                time.sleep(_slp)

        # timeout
        return False

    def get_guest_power_state(self, userid):
        resp = self.client.guest_get_power_state(userid)
        power_state = json.loads(resp.content)['output']
        return power_state

    def wait_until_guest_in_power_state(self, userid, expect_state):
        return self._wait_until(expect_state, self.get_guest_power_state,
                                userid)

    def wait_until_guest_reachable(self, userid):
        return self._wait_until(True, self.rawapi._vmops.is_reachable, userid)

    def wait_until_create_userid_complete(self, userid):
        return self._wait_until(True, self.is_guest_exist, userid)

    def power_on_guest_until_reachable(self, userid):
        self.client.guest_start(userid)
        return self.wait_until_guest_reachable(userid)
