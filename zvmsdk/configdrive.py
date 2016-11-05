import config as CONF
import constants as const
import os
import dist
import vmops
from utils import ZVMException
from log import LOG
import utils as zvmutils
import tarfile
import six
import tempfile
import shutil
import stat


_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


def get_cfg_str(ip_v4, address_read = CONF.zvm_default_nic_vdev):
    cfg_str = 'DEVICE=\"' + CONF.device + '\"\n'
    cfg_str += 'BOOTPROTO=\"static\"\n'
    cfg_str += 'BROADCAST=\"' + CONF.broadcast_v4 + '\"\n'
    cfg_str += 'GATEWAY=\"' + CONF.gateway_v4 + '\"\n'
    cfg_str += 'IPADDR=\"' + ip_v4 + '\"\n'
    cfg_str += 'NETMASK=\"' + CONF.netmask_v4 + '\"\n'
    cfg_str += 'NETTYPE=\"qeth\"\n'
    cfg_str += 'ONBOOT=\"yes\"\n'
    cfg_str += 'PORTNAME=\"PORT' + address_read + '\"\n'
    cfg_str += 'OPTIONS=\"layer2=1\"\n'
    cfg_str += 'SUBCHANNELS=\"' + CONF.subchannels + '\"\n'
    return cfg_str


def generate_net_file(ip_addr, net_file_path):
    cfg_str = get_cfg_str(ip_addr)
    generate_file(cfg_str, net_file_path)


def get_znetconfig_str(os_version):
    linuxdist = dist.ListDistManager().get_linux_dist(os_version)()
    udev_settle = linuxdist.get_znetconfig_contents()
    znetconfig = '\n'.join(('# !/bin/sh', udev_settle))
    znetconfig += '\nrm -rf /tmp/znetconfig.sh\n'
    return znetconfig


def generate_znetconfig_file(znetconfig_path, os_version):
    znetconfig = get_znetconfig_str(os_version)
    generate_file(znetconfig, znetconfig_path)


def get_meta_data_str():
    meta_data = '{\"files\": [{\"path\": \"/etc/sysconfig/network-scripts/ifcfg-enccw0.0.1000\", '
    meta_data += '\"content_path\": \"/content/0000\"}, {\"path\": \"/tmp/znetconfig.sh\", \"content_path\": \"/content/0001\"}], '
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


def create_config_drive(ip_addr, os_version):
    if not os.path.exists(CONF.tempdir):
        os.mkdir(CONF.tempdir)
    cfg_dir = os.path.join(CONF.tempdir, 'openstack')
    if os.path.exists(cfg_dir):
        shutil.rmtree(cfg_dir)
    content_dir = os.path.join(cfg_dir, 'content')
    latest_dir = os.path.join(cfg_dir, 'latest')
    os.mkdir(cfg_dir)
    os.mkdir(content_dir)
    os.mkdir(latest_dir)

    net_file = os.path.join(content_dir, '0000')
    generate_net_file(ip_addr, net_file)
    znetconfig_file = os.path.join(content_dir, '0001')
    generate_znetconfig_file(znetconfig_file, os_version)
    meta_data_path = os.path.join(latest_dir, 'meta_data.json')
    generate_meta_data(meta_data_path)
    network_data_path = os.path.join(latest_dir, 'network_data.json')
    generate_file('{}', network_data_path)
    vendor_data_path = os.path.join(latest_dir, 'vendor_data.json')
    generate_file('{}', vendor_data_path)

    tar_path = os.path.join(CONF.tempdir, 'cfgdrive.tgz')
    tar = tarfile.open(tar_path, "w:gz")
    os.chdir(CONF.tempdir)
    tar.add('openstack')
    tar.close()

    return tar_path

