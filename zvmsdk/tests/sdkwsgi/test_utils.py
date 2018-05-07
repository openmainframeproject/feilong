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
import six
import time

from zvmsdk import api
from zvmsdk import config
from zvmsdk import utils as zvmutils

CONF = config.CONF
TEST_IP_POOL = []


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

    def api_request(self, url, method='GET', body=None):

        full_uri = '%s%s' % (self.base_url, url)
        return self.request(full_uri, method, body)

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

    def image_get_root_disk_size(self, image_name):
        url = '/images/%s/root_disk_size' % image_name
        return self.api_request(url=url, method='GET')

    def guest_create(self, userid, vcpus, memory, disk_list=None,
                     user_profile=CONF.zvm.user_profile,
                     max_cpu=CONF.zvm.user_default_max_cpu,
                     max_mem=CONF.zvm.user_default_max_memory):
        body = """{"guest": {"userid": "%s", "vcpus": 1,
                             "memory": 1024,
                             "disk_list": [{"size": "1100",
                                            "is_boot_disk": "True"}]}}"""
        body = body % userid
        return self.api_request(url='/guests', method='POST',
                                       body=body)

    def guest_delete(self, userid):
        url = '/guests/%s' % userid
        return self.api_request(url=url, method='DELETE')

    def _guest_action(self, userid, body):
        url = '/guests/%s/action' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_deploy(self, userid, image_name=None, transportfiles=None,
                     remotehost=None, vdev=None):

        if vdev is None:
            vdev = "100"

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

    def guest_create_network_interface(self, userid, os_version, vdev='1000',
                                       ip_addr="192.168.95.123", active=False):
        content = {"interface": {"os_version": os_version,
                                 "guest_networks":
                                    [{"ip_addr": ip_addr,
                                     "dns_addr": ["9.0.3.1"],
                                     "gateway_addr": CONF.tests.gateway_v4,
                                     "cidr": CONF.tests.cidr,
                                     "nic_vdev": vdev}]}}
        if active:
            content["interface"]["active"] = "True"
        else:
            content["interface"]["active"] = "False"
        body = json.dumps(content)

        url = '/guests/%s/interface' % userid
        return self.api_request(url=url, method='POST', body=body)

    def guest_delete_network_interface(self, userid, os_version, vdev,
                                       active=False):
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
                                "vswitch": vswitch_name, "active": "True"}}
        else:
            content = {"info": {"couple": "True",
                                "vswitch": vswitch_name, "active": "False"}}
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

    def vswitch_grant_user(self, vswitch_name, userid):
        url = '/vswitches/%s' % vswitch_name
        body = '{"vswitch": {"grant_userid": "%s"}}' % userid
        return self.api_request(url=url, method='PUT', body=body)

    def guest_start(self, userid):
        body = '{"action": "start"}'
        return self._guest_action(userid, body)


class ZVMConnectorTestUtils(object):

    def __init__(self):
        self.client = TestzCCClient()
        self.rawapi = api.SDKAPI()

    def generate_test_userid(self):
        '''Generate an userid base on time line.'''
        prefix = six.text_type(CONF.tests.userid_prefix)[-3:].rjust(3, 't')
        userid = prefix + '%05d' % ((time.time() * 10) % 100000)
        time.sleep(1)
        return userid

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

    def deploy_guest(self, userid=None, cpu=1, memory=1024,
                     image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version,
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

        resp_gcni = self.client.guest_create_network_interface(
                                        userid, os_version, ip_addr=ip_addr)
        assert resp_gcni.status_code == 200, "Failed to create nif %s" % userid
        nic_vdev = json.loads(resp_gcni.content)['output'][0]['nic_vdev']

        self.client.guest_nic_couple_to_vswitch(userid, nic_vdev,
                                             CONF.tests.vswitch)
        self.client.vswitch_grant_user(CONF.tests.vswitch, userid)

        # Power on the vm
        print("Power on userid %s ..." % userid)
        self.client.guest_start(userid)
        # Wait IUCV path
        self.wait_until_guest_in_connection_state(userid, True)

        return userid, ip_addr

    def destroy_guest(self, userid):
        resp = self.client.guest_delete(userid)
        if resp.status_code != 200:
            print("WARNING: deleting userid failed: %s" % resp.content)

        self._wait_until(False, self.is_guest_exist, userid)

    def _wait_until(self, expect_state, func, *args, **kwargs):
        """Looping call func until get expected state, otherwise 1 min timeout.

        :param expect_state:    expected state
        :param func:            function or method to be called
        :param *args, **kwargs: parameters for the function
        """
        _inc_slp = [1, 2, 2, 5, 10, 20, 20]
        # sleep intervals, total timeout 60 seconds
        for _slp in _inc_slp:
            real_state = func(*args, **kwargs)
            if real_state == expect_state:
                return True
            else:
                time.sleep(_slp)

        # timeout
        return False

    def wait_until_guest_in_power_state(self, userid, expect_state):
        return self._wait_until(expect_state,
                                self._reqh.guest_get_power_state, userid)

    def wait_until_guest_in_connection_state(self, userid, expect_state):
        return self._wait_until(True, self.rawapi._vmops.is_reachable, userid)

    def wait_until_create_userid_complete(self, userid):
        return self._wait_until(True, self.is_guest_exist, userid)
