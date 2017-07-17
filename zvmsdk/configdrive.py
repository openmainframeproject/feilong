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


import os
import dist
import tarfile
import shutil
import stat

from zvmsdk import config


CONF = config.CONF


_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


def _generate_vdev(base, offset):
    """Generate virtual device number based on base vdev
    :param base: base virtual device number, string of 4 bit hex.
    :param offset: offset to base, integer.
    """
    vdev = hex(int(base, 16) + offset)[2:]
    return vdev.rjust(4, '0')


def get_cfg_str(network_interface_info, os_version):
    ip_v4 = network_interface_info['ip_addr']
    address_read = network_interface_info['nic_vdev']
    broadcast_v4 = network_interface_info['broadcast_v4']
    gateway_v4 = network_interface_info['gateway_v4']
    netmask_v4 = network_interface_info['netmask_v4']

    nic_vdev = network_interface_info['nic_vdev']
    subchannels = ','.join(('0.0.' + nic_vdev,
                            '0.0.' + _generate_vdev(nic_vdev, 1),
                            '0.0.' + _generate_vdev(nic_vdev, 2)))

    linuxdist = dist.LinuxDistManager().get_linux_dist(os_version)()
    device_num = 0
    device_name = linuxdist.get_device_name(device_num)
    cfg_str = 'DEVICE=' + device_name + '\n'
    cfg_str += 'BOOTPROTO=static\n'
    cfg_str += 'BROADCAST=' + broadcast_v4 + '\n'
    cfg_str += 'GATEWAY=' + gateway_v4 + '\n'
    cfg_str += 'IPADDR=' + ip_v4 + '\n'
    cfg_str += 'NETMASK=' + netmask_v4 + '\n'
    cfg_str += 'NETTYPE=qeth\n'
    cfg_str += 'ONBOOT=yes\n'
    cfg_str += 'PORTNAME=PORT' + address_read + '\n'
    cfg_str += 'OPTIONS=\"layer2=1\"\n'
    cfg_str += 'SUBCHANNELS=' + subchannels + '\n'
    return cfg_str


def generate_net_file(network_interface_info, net_file_path, os_version):
    cfg_str = get_cfg_str(network_interface_info, os_version)
    generate_file(cfg_str, net_file_path)


def get_znetconfig_str(os_version):
    linuxdist = dist.LinuxDistManager().get_linux_dist(os_version)()
    udev_settle = linuxdist.get_znetconfig_contents()
    znetconfig = '\n'.join(('# !/bin/sh', udev_settle))
    znetconfig += '\nrm -rf /tmp/znetconfig.sh\n'
    return znetconfig


def generate_znetconfig_file(znetconfig_path, os_version):
    znetconfig = get_znetconfig_str(os_version)
    generate_file(znetconfig, znetconfig_path)


def get_meta_data_str():
    meta_data = '{\"files\":[{\"path\":' +\
        '\"/etc/sysconfig/network-scripts/ifcfg-enccw0.0.1000\", '
    meta_data += '\"content_path\": \"/content/0000\"},' +\
            '{\"path\": \"/tmp/znetconfig.sh\", \"content_path\":' +\
            ' \"/content/0001\"}], '
    meta_data += '\"uuid\": \"4ec7a80d-201a-4c17-afbc-b0a93b66133b\", '
    meta_data += '\"availability_zone\": \"nova\", '
    meta_data += '\"hostname\": \"eckdrh72.5.novalocal\", '
    meta_data += '\"launch_index\": 0, '
    meta_data += '\"project_id\": \"94f8dc6644f24785a1383959dbba3f9e\", '
    meta_data += '\"name\": \"eckdrh72.5\"}'
    return meta_data


def generate_meta_data(meta_data_path):
    meta_data = get_meta_data_str()
    generate_file(meta_data, meta_data_path)


def generate_file(file_content, path):
    f = open(path, 'w')
    f.write(file_content)
    f.close()


def create_config_drive(network_interface_info, os_version):
    """Generate config driver for zVM guest vm.

    :param dict network_interface_info: Required keys:
        ip_addr - (str) IP address
        nic_vdev - (str) VDEV of the nic
        gateway_v4 - IPV4 gateway
        broadcast_v4 - IPV4 broadcast address
        netmask_v4 - IPV4 netmask
    :param str os_version: operating system version of the guest
    """
    if not os.path.exists(CONF.guest.temp_path):
        os.mkdir(CONF.guest.temp_path)
    cfg_dir = os.path.join(CONF.guest.temp_path, 'openstack')
    if os.path.exists(cfg_dir):
        shutil.rmtree(cfg_dir)
    content_dir = os.path.join(cfg_dir, 'content')
    latest_dir = os.path.join(cfg_dir, 'latest')
    os.mkdir(cfg_dir)
    os.mkdir(content_dir)
    os.mkdir(latest_dir)

    net_file = os.path.join(content_dir, '0000')
    generate_net_file(network_interface_info, net_file, os_version)
    znetconfig_file = os.path.join(content_dir, '0001')
    generate_znetconfig_file(znetconfig_file, os_version)
    meta_data_path = os.path.join(latest_dir, 'meta_data.json')
    generate_meta_data(meta_data_path)
    network_data_path = os.path.join(latest_dir, 'network_data.json')
    generate_file('{}', network_data_path)
    vendor_data_path = os.path.join(latest_dir, 'vendor_data.json')
    generate_file('{}', vendor_data_path)

    tar_path = os.path.join(CONF.guest.temp_path, 'cfgdrive.tgz')
    tar = tarfile.open(tar_path, "w:gz")
    os.chdir(CONF.guest.temp_path)
    tar.add('openstack')
    tar.close()

    return tar_path
