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


import os
import re
import time
import unittest

from zvmconnector import connector
from zvmsdk import api
from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG


def set_conf(section, opt, value):
    CONF[section][opt] = value


class SDKAPIRequestHandler(object):

    def __init__(self):
        self.client = connector.ZVMConnector(CONF.sdkserver.bind_addr)

    def _call(self, func_name, *args, **kwargs):
        results = self.client.send_request(func_name, *args, **kwargs)
        if results['overallRC'] == 0:
            return results['output']
        else:
            msg = ("SDK request %(api)s failed with parameters: %(args)s "
                   "%(kwargs)s . Error messages: %(errmsg)s" %
                   {'api': func_name, 'args': str(args), 'kwargs': str(kwargs),
                    'errmsg': results['errmsg']})
            raise exception.SDKBaseException(msg, results)

    def guest_start(self, *args, **kwargs):
        return self._call('guest_start', *args, **kwargs)

    def guest_stop(self, *args, **kwargs):
        return self._call('guest_stop', *args, **kwargs)

    def guest_reboot(self, *args, **kwargs):
        return self._call('guest_reboot', *args, **kwargs)

    def guest_reset(self, *args, **kwargs):
        return self._call('guest_reset', *args, **kwargs)

    def guest_pause(self, *args, **kwargs):
        return self._call('guest_pause', *args, **kwargs)

    def guest_unpause(self, *args, **kwargs):
        return self._call('guest_unpause', *args, **kwargs)

    def guest_get_power_state(self, *args, **kwargs):
        return self._call('guest_get_power_state', *args, **kwargs)

    def guest_get_info(self, *args, **kwargs):
        return self._call('guest_get_info', *args, **kwargs)

    def guest_list(self, *args, **kwargs):
        return self._call('guest_list', *args, **kwargs)

    def host_get_info(self, *args, **kwargs):
        return self._call('host_get_info', *args, **kwargs)

    def host_diskpool_get_info(self, *args, **kwargs):
        return self._call('host_diskpool_get_info', *args, **kwargs)

    def image_delete(self, *args, **kwargs):
        return self._call('image_delete', *args, **kwargs)

    def image_get_root_disk_size(self, *args, **kwargs):
        return self._call('image_get_root_disk_size', *args, **kwargs)

    def image_import(self, *args, **kwargs):
        return self._call('image_import', *args, **kwargs)

    def image_query(self, *args, **kwargs):
        return self._call('image_query', *args, **kwargs)

    def image_export(self, *args, **kwargs):
        return self._call('image_export', *args, **kwargs)

    def guest_deploy(self, *args, **kwargs):
        return self._call('guest_deploy', *args, **kwargs)

    def guest_create_nic(self, *args, **kwargs):
        return self._call('guest_create_nic', *args, **kwargs)

    def guest_delete_nic(self, *args, **kwargs):
        return self._call('guest_delete_nic', *args, **kwargs)

    def guest_get_definition_info(self, *args, **kwargs):
        return self._call('guest_get_definition_info', *args, **kwargs)

    def guest_create(self, *args, **kwargs):
        return self._call('guest_create', *args, **kwargs)

    def guest_create_disks(self, *args, **kwargs):
        return self._call('guest_create_disks', *args, **kwargs)

    def guest_delete_disks(self, *args, **kwargs):
        return self._call('guest_delete_disks', *args, **kwargs)

    def guest_nic_couple_to_vswitch(self, *args, **kwargs):
        return self._call('guest_nic_couple_to_vswitch', *args, **kwargs)

    def guest_nic_uncouple_from_vswitch(self, *args, **kwargs):
        return self._call('guest_nic_uncouple_from_vswitch', *args, **kwargs)

    def vswitch_get_list(self, *args, **kwargs):
        return self._call('vswitch_get_list', *args, **kwargs)

    def vswitch_create(self, *args, **kwargs):
        return self._call('vswitch_create', *args, **kwargs)

    def guest_get_console_output(self, *args, **kwargs):
        return self._call('guest_get_console_output', *args, **kwargs)

    def guest_delete(self, *args, **kwargs):
        return self._call('guest_delete', *args, **kwargs)

    def guest_inspect_cpus(self, *args, **kwargs):
        return self._call('guest_inspect_cpus', *args, **kwargs)

    def guest_inspect_mem(self, *args, **kwargs):
        return self._call('guest_inspect_mem', *args, **kwargs)

    def guest_inspect_vnics(self, *args, **kwargs):
        return self._call('guest_inspect_vnics', *args, **kwargs)

    def vswitch_grant_user(self, *args, **kwargs):
        return self._call('vswitch_grant_user', *args, **kwargs)

    def vswitch_revoke_user(self, *args, **kwargs):
        return self._call('vswitch_revoke_user', *args, **kwargs)

    def vswitch_set_vlan_id_for_user(self, *args, **kwargs):
        return self._call('vswitch_set_vlan_id_for_user', *args, **kwargs)

    def guest_config_minidisks(self, *args, **kwargs):
        return self._call('guest_config_minidisks', *args, **kwargs)

    def vswitch_set(self, *args, **kwargs):
        return self._call('vswitch_set', *args, **kwargs)

    def vswitch_delete(self, *args, **kwargs):
        return self._call('vswitch_delete', *args, **kwargs)

    def volume_attach(self, *args, **kwargs):
        return self._call('volume_attach', *args, **kwargs)

    def volume_detach(self, *args, **kwargs):
        return self._call('volume_detach', *args, **kwargs)

    def guest_create_network_interface(self, *args, **kwargs):
        return self._call('guest_create_network_interface', *args, **kwargs)


class SDKAPITestUtils(object):

    def __init__(self):
        self.sdkapi = SDKAPIRequestHandler()
        self.rawapi = api.SDKAPI()

    def image_import(self, image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version):

        image_name = os.path.basename(image_path)
        image_url = ''.join(('file://', image_path))
        try:
            self.sdkapi.image_import(image_name, image_url,
                                  {'os_version': os_version})
        except exception.SDKBaseException as err:
            if err.results['rc'] == 300 and err.results['rs'] == 13:
                # image already exists
                return
            else:
                raise

    def is_guest_exist(self, userid):
        cmd = 'sudo vmcp q %s' % userid
        rc, output = zvmutils.execute(cmd)
        if re.search('(^HCP\w\w\w003E)', output):
            # userid not exist
            return False
        return True

    def get_available_userid_ipaddr(self):
        userid_list = CONF.tests.userid_list.split(' ')
        ip_list = CONF.tests.ip_addr_list.split(' ')
        for uid in userid_list:
            if self.is_guest_exist(uid):
                try:
                    self.sdkapi.guest_delete(uid)
                except exception.SDKBaseException as e:
                    print("WARNING: Delete guest failed: %s" %
                          e.format_message())
                continue
            else:
                idx = userid_list.index(uid)
                return uid, ip_list[idx]

    def _get_next_userid_ipaddr(self, userid):
        userids = CONF.tests.userid_list.split(' ')
        ip_list = CONF.tests.ip_addr_list.split(' ')
        idx = userids.index(userid)
        if (idx + 1) == len(userids):
            # the userid is the last one in userids, return the first one
            return userids[0], ip_list[0]
        else:
            return userids[idx + 1], ip_list[idx + 1]

    def guest_deploy(self, userid=None, cpu=1, memory=1024,
                     image_path=CONF.tests.image_path,
                     os_version=CONF.tests.image_os_version,
                     ip_addr=None):
        image_name = os.path.basename(image_path)
        url = 'file://' + image_path

        print("Checking if image %s exists or not, import it if not exists" %
              image_name)
        try:
            self.sdkapi.image_query(image_name)
        except exception.SDKBaseException as err:
            errmsg = err.format_message()
            print('WARNING: image not exist, image_query failed with '
                  'reason : %s, will import image now' % errmsg)
            print("Importing image %s ..." % image_name)
            self.sdkapi.image_import(image_name, url,
                        {'os_version': os_version})

        print("Using image %s ..." % image_name)

        ipaddr = '0.4.0.4'
        if userid is None:
            userid, ip_addr = self.get_available_userid_ipaddr()
        ip_addr = ip_addr or ipaddr
        print("Using userid %s and IP addr %s ..." % (userid, ip_addr))

        user_profile = CONF.zvm.user_profile

        size = self.sdkapi.image_get_root_disk_size(image_name)
        print("root disk size is %s" % size)
        disks_list = [{'size': size,
                       'is_boot_disk': True,
                       'disk_pool': CONF.zvm.disk_pool}]

        # Create vm in zVM
        print("Creating userid %s ..." % userid)
        try:
            self.sdkapi.guest_create(userid, cpu, memory, disks_list,
                                  user_profile)
        except exception.SDKBaseException as err:
            errmsg = err.format_message()
            print("WARNING: create userid failed: %s" % errmsg)
            if err.results['rc'] == 400 and err.results['rs'] == 8:
                print("userid %s still exist" % userid)
                # switch to new userid
                userid, ip_addr = self._get_next_userid_ipaddr(userid)
                print("turn to use new userid %s and IP addr 5s" %
                      (userid, ip_addr))
                self.sdkapi.guest_create(userid, cpu, memory, disks_list,
                                      user_profile)

        assert self.wait_until_create_userid_complete(userid)

        # Deploy image on vm
        print("Deploying userid %s ..." % userid)
        self.sdkapi.guest_deploy(userid, image_name)

        # Create nic and configure it
        guest_networks = [{
            'ip_addr': ip_addr,
            'gateway_addr': CONF.tests.gateway_v4,
            'cidr': CONF.tests.cidr,
        }]
        netinfo = self.sdkapi.guest_create_network_interface(
                                        userid, os_version, guest_networks)
        nic_vdev = netinfo[0]['nic_vdev']
        self.sdkapi.guest_nic_couple_to_vswitch(userid, nic_vdev,
                                             CONF.tests.vswitch)
        self.sdkapi.vswitch_grant_user(CONF.tests.vswitch, userid)

        # Power on the vm, then put MN's public key into vm
        print("Power on userid %s ..." % userid)
        self.sdkapi.guest_start(userid)

        return userid, ip_addr

    def guest_destroy(self, userid):
        try:
            self.sdkapi.guest_delete(userid)
        except exception.SDKBaseException as err:
            print("WARNING: deleting userid failed: %s" % err.format_message())

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
                                self.sdkapi.guest_get_power_state, userid)

    def wait_until_guest_in_connection_state(self, userid, expect_state):
        return self._wait_until(True, self.rawapi._vmops.is_reachable, userid)

    def wait_until_create_userid_complete(self, userid):
        return self._wait_until(True, self.is_guest_exist, userid)


class SDKAPIBaseTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(SDKAPIBaseTestCase, self).__init__(methodName)
        self.sdkapi = SDKAPIRequestHandler()
        self.sdkutils = SDKAPITestUtils()

    def set_conf(self, section, opt, value):
        old_value = CONF[section][opt]
        CONF[section][opt] = value
        self.addCleanup(set_conf, section, opt, old_value)


class SDKAPIGuestBaseTestCase(SDKAPIBaseTestCase):
    """Base test class for testcases that require a deployed vm."""

    def setUp(self):
        super(SDKAPIGuestBaseTestCase, self).setUp()

        # create test server
        self.userid, self.ip_addr = self.sdkutils.get_available_userid_ipaddr()
        try:
            self.userid, self.ip_addr = self.sdkutils.guest_deploy(
                        userid=self.userid, ip_addr=self.ip_addr)
        finally:
            self.addCleanup(self.sdkutils.guest_destroy, self.userid)
