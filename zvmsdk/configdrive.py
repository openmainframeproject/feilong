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


def generate_file(file_content, path):
    f = open(path, 'w')
    f.write(file_content)
    f.close()


def get_meta_data_str(userid):
    # TODO: Remove the hard code of interface name for different Linux distros
    # TODO: Multi network interface support
    # TODO: Host name support
    # TODO: Remove keywords not in use. e.g. availability zone, uuid ...
    meta_data = '{\"files\":[{\"path\":' +\
        '\"/etc/sysconfig/network-scripts/ifcfg-enccw0.0.1000\", '
    meta_data += '\"content_path\": \"/content/0000\"},' +\
            '{\"path\": \"/tmp/znetconfig.sh\", \"content_path\":' +\
            ' \"/content/0001\"}], '
    meta_data += '\"uuid\": \"4ec7a80d-201a-4c17-afbc-b0a93b66133b\", '
    meta_data += '\"availability_zone\": \"nova\", '
    meta_data += '\"hostname\": \"%s\", ' % userid
    meta_data += '\"launch_index\": 0, '
    meta_data += '\"project_id\": \"94f8dc6644f24785a1383959dbba3f9e\", '
    meta_data += '\"name\": \"%s\"}' % userid
    return meta_data


def generate_meta_data(userid, meta_data_path):
    meta_data = get_meta_data_str(userid)
    generate_file(meta_data, meta_data_path)


def create_config_drive(userid, network_interface_info, os_version):
    """Generate config driver for zVM guest vm.

    :param str userid: the userid of guest vm
    :param dict network_interface_info: Required keys:
        ip_addr - (str) IP address
        nic_vdev - (str) VDEV of the nic
        gateway_v4 - IPV4 gateway
        cidr - network CIDR
    :param str os_version: operating system version of the guest
    """
    if not os.path.exists(CONF.guest.temp_path):
        os.makedirs(CONF.guest.temp_path)
    cfg_dir = os.path.join(CONF.guest.temp_path, 'configdrive')
    if os.path.exists(cfg_dir):
        shutil.rmtree(cfg_dir)
    content_dir = os.path.join(cfg_dir, 'content')
    latest_dir = os.path.join(cfg_dir, 'latest')
    os.mkdir(cfg_dir)
    os.mkdir(content_dir)
    os.mkdir(latest_dir)

    dist_manager = dist.LinuxDistManager()
    linuxdist = dist_manager.get_linux_dist(os_version)()

    subnet_info = {
        'version': 4,
        'ips': [{'address': network_interface_info['ip_addr']}],
        'dns': [],
        'cidr': network_interface_info['cidr'],
        'gateway': {'address': network_interface_info['gateway_v4']}}
    network_info = [{'network': {'subnets': [subnet_info]}}]

    files_and_cmds = linuxdist.create_network_configuration_files(
                                            CONF.guest.temp_path, network_info)
    (net_conf_files, net_conf_cmds) = files_and_cmds

    net_file = os.path.join(content_dir, '0000')
    generate_file(net_conf_files[0][1], net_file)
    znetconfig_file = os.path.join(content_dir, '0001')
    generate_file(net_conf_cmds, znetconfig_file)

    meta_data_path = os.path.join(latest_dir, 'meta_data.json')
    generate_meta_data(userid, meta_data_path)

    network_data_path = os.path.join(latest_dir, 'network_data.json')
    generate_file('{}', network_data_path)

    vendor_data_path = os.path.join(latest_dir, 'vendor_data.json')
    generate_file('{}', vendor_data_path)

    tar_path = os.path.join(CONF.guest.temp_path, 'cfgdrive.tgz')
    tar = tarfile.open(tar_path, "w:gz")
    os.chdir(CONF.guest.temp_path)
    tar.add('configdrive')
    tar.close()

    return tar_path
