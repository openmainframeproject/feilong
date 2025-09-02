#  SPDX-License-Identifier: Apache-2.0
#
#  Copyright 2025 Contributors to the Feilong Project.
#  Copyright 2017,2021 IBM Corp.
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
import os

from jinja2 import Template
from zvmsdk import dist
from zvmsdk import smtclient
from zvmsdk.tests.unit import base


class RHEL7TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(RHEL7TestCase, cls).setUpClass()
        cls.os_version = 'redhat7.2'

    def setUp(self):
        super(RHEL7TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    def test_create_network_configuration_files(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mtu': 1600}]
        file_path = '/etc/sysconfig/network-scripts/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
                             file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual('DEVICE="enccw0.0.1000"', cfg_str[0])
        self.assertEqual('BROADCAST="192.168.95.255"', cfg_str[2])
        self.assertEqual('GATEWAY="192.168.95.1"', cfg_str[3])
        self.assertEqual('IPADDR="192.168.95.10"', cfg_str[4])
        self.assertEqual('MTU="1600"', cfg_str[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[13])

    def test_create_network_configuration_files_multi_nics(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mtu': 1600},
              {'ip_addr': '192.168.96.11',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003',
               'mtu': 1500}]
        file_path = '/etc/sysconfig/network-scripts/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
                             file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual('DEVICE="enccw0.0.1000"', cfg_str[0])
        self.assertEqual('BROADCAST="192.168.95.255"', cfg_str[2])
        self.assertEqual('GATEWAY="192.168.95.1"', cfg_str[3])
        self.assertEqual('IPADDR="192.168.95.10"', cfg_str[4])
        self.assertEqual('MTU="1600"', cfg_str[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[13])

        cfg_str2 = net_conf_files[1][1].split('\n')
        self.assertEqual('DEVICE="enccw0.0.1003"', cfg_str2[0])
        self.assertEqual('BROADCAST="192.168.96.255"', cfg_str2[2])
        self.assertEqual('GATEWAY=""', cfg_str2[3])
        self.assertEqual('IPADDR="192.168.96.11"', cfg_str2[4])
        self.assertEqual('MTU="1500"', cfg_str2[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str2[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str2[13])

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_attach_configuration_cmds(self, get_template,
                                                  template_render):

        """ RHEL7 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        self.linux_dist.get_volume_attach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point)
        # check function called assertions
        get_template.assert_called_once_with("volumeops",
                                             "rhel7_attach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz')

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_1(self,
                                                    get_template,
                                                    template_render):

        """ RHEL7 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 2)
        get_template.assert_called_once_with("volumeops",
                                             "rhel7_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=0)

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_2(self,
                                                    get_template,
                                                    template_render):

        """ RHEL7 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections < 1
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 0)
        get_template.assert_called_once_with("volumeops",
                                             "rhel7_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=1)

    def test_set_zfcp_config_files(self):
        """ RHEL7, same to rhel6"""
        pass


class RHEL8TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(RHEL8TestCase, cls).setUpClass()
        cls.os_version = 'redhat8.1'

    def setUp(self):
        super(RHEL8TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    def test_create_network_configuration_files(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
                           'dns_addr': ['9.0.2.1', '9.0.3.1'],
                           'gateway_addr': '192.168.95.1',
                           'cidr': "192.168.95.0/24",
                           'nic_vdev': '1000',
                           'mtu': 8000}]
        file_path = '/etc/sysconfig/network-scripts/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
            file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual('DEVICE="enc1000"', cfg_str[0])
        self.assertEqual('BROADCAST="192.168.95.255"', cfg_str[2])
        self.assertEqual('GATEWAY="192.168.95.1"', cfg_str[3])
        self.assertEqual('IPADDR="192.168.95.10"', cfg_str[4])
        self.assertEqual('MTU="8000"', cfg_str[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[13])

    def test_create_network_configuration_files_multi_nics(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mtu': 1600},
              {'ip_addr': '192.168.96.11',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003',
               'mtu': 1500}]
        file_path = '/etc/sysconfig/network-scripts/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
                             file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual('DEVICE="enc1000"', cfg_str[0])
        self.assertEqual('BROADCAST="192.168.95.255"', cfg_str[2])
        self.assertEqual('GATEWAY="192.168.95.1"', cfg_str[3])
        self.assertEqual('IPADDR="192.168.95.10"', cfg_str[4])
        self.assertEqual('MTU="1600"', cfg_str[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[13])

        cfg_str2 = net_conf_files[1][1].split('\n')
        self.assertEqual('DEVICE="enc1003"', cfg_str2[0])
        self.assertEqual('BROADCAST="192.168.96.255"', cfg_str2[2])
        self.assertEqual('GATEWAY=""', cfg_str2[3])
        self.assertEqual('IPADDR="192.168.96.11"', cfg_str2[4])
        self.assertEqual('MTU="1500"', cfg_str2[11])
        self.assertEqual('DNS1="9.0.2.1"', cfg_str2[12])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str2[13])

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_attach_configuration_cmds(self, get_template,
                                                  template_render):

        """ RHEL8 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        self.linux_dist.get_volume_attach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point)
        # check function called assertions
        get_template.assert_called_once_with("volumeops",
                                             "rhel8_attach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz')

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_1(self,
                                                    get_template,
                                                    template_render):

        """ RHEL8 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 2)
        get_template.assert_called_once_with("volumeops",
                                             "rhel8_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=0)

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_2(self,
                                                    get_template,
                                                    template_render):

        """ RHEL8 """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 0
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 0)
        get_template.assert_called_once_with("volumeops",
                                             "rhel8_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=1)


class RHCOS4TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(RHCOS4TestCase, cls).setUpClass()
        cls.os_version = 'rhcos4'
        os.makedirs("/tmp/FakeID")

    def setUp(self):
        super(RHCOS4TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()
        self._smtclient = smtclient.SMTClient()

    @mock.patch.object(smtclient.SMTClient, 'get_guest_path')
    def test_create_coreos_parameter(self, guest_path):
        network_info = [{'nic_vdev': '1000',
                        'ip_addr': '10.10.0.217',
                        'gateway_addr': '10.10.0.1',
                        'dns_addr': ['10.10.0.250', '10.10.0.51'],
                        'mac_addr': 'fa:16:3e:7a:1b:87',
                        'cidr': '10.10.0.0/24',
                        'nic_id': 'adca70f3-8509-44d4-92d4-2c1c14b3f25e',
                        'mtu': '1000'}]
        userid = "FakeID"
        guest_path.return_value = "/tmp/FakeID"
        res = self.linux_dist.create_coreos_parameter(network_info, userid)
        self.assertEqual(res, "10.10.0.217::10.10.0.1:24:FakeID:enc1000:none:"
                              "10.10.0.250:10.10.0.51;1000")

    @mock.patch.object(smtclient.SMTClient, 'get_guest_path')
    def test_read_coreos_parameter(self, guest_path):
        guest_path.return_value = "/tmp/FakeID"
        userid = "FakeID"
        network_info = [{'nic_vdev': '1000',
                        'ip_addr': '10.10.0.217',
                        'gateway_addr': '10.10.0.1',
                        'dns_addr': ['10.10.0.250', '10.10.0.51'],
                        'mac_addr': 'fa:16:3e:7a:1b:87',
                        'cidr': '10.10.0.0/24',
                        'nic_id': 'adca70f3-8509-44d4-92d4-2c1c14b3f25e',
                        'mtu': '1000'}]
        self.linux_dist.create_coreos_parameter_temp_file(network_info, userid)
        param = self.linux_dist.read_coreos_parameter(userid)
        self.assertEqual(param,
                         '10.10.0.217::10.10.0.1:24:FakeID:'
                         'enc1000:none:10.10.0.250:10.10.0.51;1000')


class SLES15TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(SLES15TestCase, cls).setUpClass()
        cls.os_version = 'sles15'

    def setUp(self):
        super(SLES15TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    def test_create_network_configuration_files(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
                           'gateway_addr': '192.168.95.1',
                           'cidr': "192.168.95.0/24",
                           'nic_vdev': '1000',
                           'mtu': 8000}]
        file_path = '/etc/sysconfig/network/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
            file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual("BOOTPROTO='static'", cfg_str[0])
        self.assertEqual("IPADDR='192.168.95.10'", cfg_str[1])
        self.assertEqual("NETMASK='255.255.255.0'", cfg_str[2])
        self.assertEqual("BROADCAST='192.168.95.255'", cfg_str[3])
        self.assertEqual("NAME='OSA Express Network card (1000)'", cfg_str[5])
        self.assertEqual("MTU='8000'", cfg_str[6])

    def test_create_network_configuration_files_multi_nics(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
                           'gateway_addr': '192.168.95.1',
                           'cidr': "192.168.95.0/24",
                           'nic_vdev': '1000',
                           'mtu': 8000},
                           {'ip_addr': '192.168.96.11',
                            'dns_addr': ['9.0.2.1', '9.0.3.1'],
                            'gateway_addr': '192.168.96.1',
                            'cidr': "192.168.96.0/24",
                            'nic_vdev': '1003',
                            'mtu': 1500}]
        file_path = '/etc/sysconfig/network/'
        first = False
        files_and_cmds = self.linux_dist.create_network_configuration_files(
            file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        cfg_str = net_conf_files[0][1].split('\n')
        self.assertEqual("BOOTPROTO='static'", cfg_str[0])
        self.assertEqual("IPADDR='192.168.95.10'", cfg_str[1])
        self.assertEqual("NETMASK='255.255.255.0'", cfg_str[2])
        self.assertEqual("BROADCAST='192.168.95.255'", cfg_str[3])
        self.assertEqual("NAME='OSA Express Network card (1000)'", cfg_str[5])
        self.assertEqual("MTU='8000'", cfg_str[6])

        cfg_str2 = net_conf_files[2][1].split('\n')
        self.assertEqual("BOOTPROTO='static'", cfg_str2[0])
        self.assertEqual("IPADDR='192.168.96.11'", cfg_str2[1])
        self.assertEqual("NETMASK='255.255.255.0'", cfg_str2[2])
        self.assertEqual("BROADCAST='192.168.96.255'", cfg_str2[3])
        self.assertEqual("NAME='OSA Express Network card (1003)'", cfg_str2[5])
        self.assertEqual("MTU='1500'", cfg_str2[6])

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_attach_configuration_cmds(self, get_template,
                                                  template_render):

        """ SLES """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        self.linux_dist.get_volume_attach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point)
        # check function called assertions
        get_template.assert_called_once_with("volumeops",
                                             "sles_attach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz')

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_1(self,
                                                    get_template,
                                                    template_render):

        """ SLES """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 2)
        get_template.assert_called_once_with(
            "volumeops",
            "sles_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=0)

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_2(self,
                                                    get_template,
                                                    template_render):

        """ SLES """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 0 and is_last_volume shoud be 1
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 0)
        get_template.assert_called_once_with(
            "volumeops",
            "sles_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                target_filename='sdz',
                                                is_last_volume=1)


class UBUNTU22TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(UBUNTU22TestCase, cls).setUpClass()
        cls.os_version = 'ubuntu22'

    def setUp(self):
        super(UBUNTU22TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    def test_create_network_configuration_files(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
                           'dns_addr': ['9.0.2.1', '9.0.3.1'],
                           'gateway_addr': '192.168.95.1',
                           'cidr': "192.168.95.0/24",
                           'nic_vdev': '1000',
                           'mtu': 6000}]
        file_path = '/etc/netplan/'
        first = True
        files_and_cmds = self.linux_dist.create_network_configuration_files(
            file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        ret = net_conf_files[0][1]
        expect = {'network':
                        {'ethernets':
                            {'enc1000':
                                {'addresses': ['192.168.95.10/24'],
                                'gateway4': '192.168.95.1',
                                'mtu': '6000',
                                'nameservers':
                                    {'addresses': ['9.0.2.1', '9.0.3.1']}
                                }
                            },
                        'version': 2
                        }
                    }
        self.assertEqual(ret, expect)

    def test_create_network_configuration_files_multi_nics(self):
        guest_networks = [{'ip_addr': '192.168.95.10',
                           'dns_addr': ['9.0.2.1', '9.0.3.1'],
                           'gateway_addr': '192.168.95.1',
                           'cidr': "192.168.95.0/24",
                           'nic_vdev': '1000',
                           'mtu': 6000},
                           {'ip_addr': '192.168.96.11',
                            'dns_addr': ['9.0.2.1', '9.0.3.1'],
                            'gateway_addr': '192.168.96.1',
                            'cidr': "192.168.96.0/24",
                            'nic_vdev': '1003',
                            'mtu': 1500}]
        file_path = '/etc/netplan/'
        first = True
        files_and_cmds = self.linux_dist.create_network_configuration_files(
            file_path, guest_networks, first, active=False)
        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds
        ret = net_conf_files[0][1]
        expect = {'network':
                        {'ethernets':
                            {'enc1000':
                                {'addresses': ['192.168.95.10/24'],
                                'gateway4': '192.168.95.1',
                                'mtu': '6000',
                                'nameservers':
                                    {'addresses': ['9.0.2.1', '9.0.3.1']}
                                },
                             'enc1003':
                                {'addresses': ['192.168.96.11/24'],
                                'gateway4': '192.168.96.1',
                                'mtu': '1500',
                                'nameservers':
                                    {'addresses': ['9.0.2.1', '9.0.3.1']}
                                }
                            },
                        'version': 2
                        }
                    }
        self.assertEqual(ret, expect)

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_attach_configuration_cmds(self, get_template,
                                                  template_render):

        """ UBUNTU """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        self.linux_dist.get_volume_attach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point)
        # check function called assertions
        get_template.assert_called_once_with("volumeops",
                                             "ubuntu_attach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0026000000000000',
                                                lun_id=38,
                                                target_filename='sdz')

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_1(self,
                                                    get_template,
                                                    template_render):

        """ UBUNTU """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0100000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 2)
        get_template.assert_called_once_with(
                "volumeops",
                "ubuntu_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0100000000000000',
                                                lun_id='0x0100000000000000',
                                                target_filename='sdz',
                                                is_last_volume=0)

    @mock.patch('jinja2.Template.render')
    @mock.patch('zvmsdk.dist.LinuxDist.get_template')
    def test_get_volume_detach_configuration_cmds_2(self,
                                                    get_template,
                                                    template_render):

        """ UBUNTU """
        fcp_list = '1fc5 2fc5'
        wwpns = '0x5005076812341234 0x5005076812345678'
        lun = '0x0100000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        get_template.return_value = Template('fake template {{fcp}}')
        # connections == 0
        self.linux_dist.get_volume_detach_configuration_cmds(fcp_list, wwpns,
                                                             lun, multipath,
                                                             mount_point, 0)
        get_template.assert_called_once_with("volumeops",
                                             "ubuntu_detach_volume.j2")
        template_render.assert_called_once_with(fcp_list='1fc5 2fc5',
                                                wwpns=wwpns,
                                                lun='0x0100000000000000',
                                                lun_id='0x0100000000000000',
                                                target_filename='sdz',
                                                is_last_volume=1)
