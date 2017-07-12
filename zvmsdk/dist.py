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


import abc
import six

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


@six.add_metaclass(abc.ABCMeta)
class LinuxDist(object):
    """Linux distribution base class

    Due to we need to interact with linux dist and inject different files
    according to the dist version. Currently only RHEL and SLES are supported
    """

    def create_network_configuration_files(self, file_path, network_info):
        """Generate network configuration files to instance."""
        base_vdev = CONF.zvm.default_nic_vdev
        device_num = 0
        cfg_files = []
        cmd_strings = ''
        udev_cfg_str = ''
        dns_cfg_str = ''
        route_cfg_str = ''
        cmd_str = None
        file_path = self._get_network_file_path()
        file_name_route = file_path + 'routes'

        file_name_dns = self._get_dns_filename()
        for vif in network_info:
            file_name = self._get_device_filename(device_num)
            network = vif['network']
            (cfg_str, cmd_str, dns_str,
                route_str) = self._generate_network_configuration(network,
                                                base_vdev, device_num)
            LOG.debug('Network configure file content is: %s', cfg_str)
            target_net_conf_file_name = file_path + file_name
            cfg_files.append((target_net_conf_file_name, cfg_str))
            udev_cfg_str += self._get_udev_configuration(device_num,
                                '0.0.' + str(base_vdev).zfill(4))
            if cmd_str is not None:
                cmd_strings += cmd_str
            if len(dns_str) > 0:
                dns_cfg_str += dns_str
            if len(route_str) > 0:
                route_cfg_str += route_str
            base_vdev = str(hex(int(base_vdev, 16) + 3))[2:]
            device_num += 1

        if len(dns_cfg_str) > 0:
            cfg_files.append((file_name_dns, dns_cfg_str))
        self._append_udev_info(cfg_files, file_name_route, route_cfg_str,
                               udev_cfg_str)
        return cfg_files, cmd_strings

    def _generate_network_configuration(self, network, vdev, device_num):
        ip_v4 = dns_str = ''

        subnets_v4 = [s for s in network['subnets'] if s['version'] == 4]

        if len(subnets_v4[0]['ips']) > 0:
            ip_v4 = subnets_v4[0]['ips'][0]['address']
        if len(subnets_v4[0]['dns']) > 0:
            for dns in subnets_v4[0]['dns']:
                dns_str += 'nameserver ' + dns['address'] + '\n'
        netmask_v4 = str(subnets_v4[0].as_netaddr().netmask)
        gateway_v4 = subnets_v4[0]['gateway']['address'] or ''
        broadcast_v4 = str(subnets_v4[0].as_netaddr().broadcast)
        device = self._get_device_name(device_num)
        address_read = str(vdev).zfill(4)
        address_write = str(hex(int(vdev, 16) + 1))[2:].zfill(4)
        address_data = str(hex(int(vdev, 16) + 2))[2:].zfill(4)
        subchannels = '0.0.%s' % address_read.lower()
        subchannels += ',0.0.%s' % address_write.lower()
        subchannels += ',0.0.%s' % address_data.lower()

        cfg_str = self._get_cfg_str(device, broadcast_v4, gateway_v4,
                                    ip_v4, netmask_v4, address_read,
                                    subchannels)
        cmd_str = self._get_cmd_str(address_read, address_write,
                                    address_data)
        route_str = self._get_route_str(gateway_v4)

        return cfg_str, cmd_str, dns_str, route_str

    def get_device_name(self, device_num):
        return self._get_device_name(device_num)

    @abc.abstractmethod
    def _get_network_file_path(self):
        """Get network file configuration path."""
        pass

    @abc.abstractmethod
    def get_change_passwd_command(self, admin_password):
        """construct change password command

        :admin_password: the password to be changed to
        """
        pass

    @abc.abstractmethod
    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        """construct configuration file of network device."""
        pass

    @abc.abstractmethod
    def _get_device_filename(self, device_num):
        """construct the name of a network device file."""
        pass

    @abc.abstractmethod
    def _get_route_str(self, gateway_v4):
        """construct a router string."""
        pass

    @abc.abstractmethod
    def _get_cmd_str(self, address_read, address_write, address_data):
        """construct network startup command string."""
        pass

    @abc.abstractmethod
    def _get_dns_filename(self):
        """construct the name of dns file."""
        pass

    @abc.abstractmethod
    def get_znetconfig_contents(self):
        """construct znetconfig file will be called during first boot."""
        pass

    @abc.abstractmethod
    def _get_device_name(self, device_num):
        """construct the name of a network device."""
        pass

    @abc.abstractmethod
    def _get_udev_configuration(self, device, dev_channel):
        """construct udev configuration info."""
        pass

    @abc.abstractmethod
    def _append_udev_info(self, cfg_files, file_name_route, route_cfg_str,
                          udev_cfg_str):
        pass

    @abc.abstractmethod
    def get_scp_string(self, root, fcp, wwpn, lun):
        """construct scp_data string for ipl parameter"""
        pass

    @abc.abstractmethod
    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        """construct the lines composing the script to generate
           the /etc/zipl.conf file
        """
        pass


class rhel(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network-scripts/'

    def get_change_passwd_command(self, admin_password):
        return 'echo %s|passwd --stdin root' % admin_password

    def assemble_zfcp_srcdev(self, fcp, wwpn, lun):
        path = '/dev/disk/by-path/ccw-0.0.%(fcp)s-zfcp-0x%(wwpn)s:0x%(lun)s'
        srcdev = path % {'fcp': fcp, 'wwpn': wwpn, 'lun': lun}
        return srcdev

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        cfg_str = 'DEVICE=\"' + device + '\"\n'
        cfg_str += 'BOOTPROTO=\"static\"\n'
        cfg_str += 'BROADCAST=\"' + broadcast_v4 + '\"\n'
        cfg_str += 'GATEWAY=\"' + gateway_v4 + '\"\n'
        cfg_str += 'IPADDR=\"' + ip_v4 + '\"\n'
        cfg_str += 'NETMASK=\"' + netmask_v4 + '\"\n'
        cfg_str += 'NETTYPE=\"qeth\"\n'
        cfg_str += 'ONBOOT=\"yes\"\n'
        cfg_str += 'PORTNAME=\"PORT' + address_read + '\"\n'
        cfg_str += 'OPTIONS=\"layer2=1\"\n'
        cfg_str += 'SUBCHANNELS=\"' + subchannels + '\"\n'
        return cfg_str

    def _get_route_str(self, gateway_v4):
        return ''

    def _get_cmd_str(self, address_read, address_write, address_data):
        return ''

    def _get_dns_filename(self):
        return '/etc/resolv.conf'

    def _get_device_name(self, device_num):
        return 'eth' + str(device_num)

    def _get_udev_configuration(self, device, dev_channel):
        return ''

    def _append_udev_info(self, cfg_files, file_name_route, route_cfg_str,
                          udev_cfg_str):
        pass


class rhel6(rhel):
    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'service network restart',
                          'cio_ignore -u'))

    def _get_device_filename(self, device_num):
        return 'ifcfg-eth' + str(device_num)

    def _get_device_name(self, device_num):
        return 'eth' + str(device_num)

    def get_scp_string(self, root, fcp, wwpn, lun):
        return ("=root=%(root)s selinux=0 "
                "rd_ZFCP=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s") % {
                'root': root, 'fcp': fcp, 'wwpn': wwpn, 'lun': lun}

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        return ['#!/bin/bash\n',
                ('echo -e "[defaultboot]\\n'
                 'timeout=5\\n'
                 'default=boot-from-volume\\n'
                 'target=/boot/\\n'
                 '[boot-from-volume]\\n'
                 'image=%(image)s\\n'
                 'ramdisk=%(ramdisk)s\\n'
                 'parameters=\\"root=%(root)s '
                 'rd_ZFCP=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s selinux=0\\""'
                 '>/etc/zipl_volume.conf\n'
                 'zipl -c /etc/zipl_volume.conf')
                % {'image': image, 'ramdisk': ramdisk, 'root': root,
                   'fcp': fcp, 'wwpn': wwpn, 'lun': lun}]


class rhel7(rhel):
    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'cio_ignore -u'))

    def _get_device_filename(self, device_num):
        # Construct a device like ifcfg-enccw0.0.1000, ifcfg-enccw0.0.1003
        base = int(CONF.zvm.default_nic_vdev, 16)
        device = str(hex(base + device_num * 3))[2:]
        return 'ifcfg-enccw0.0.' + str(device).zfill(4)

    def _get_device_name(self, device_num):
        # Construct a device like enccw0.0.1000, enccw0.0.1003
        base = int(CONF.zvm.default_nic_vdev, 16)
        device = str(hex(base + device_num * 3))[2:]
        return 'enccw0.0.' + str(device).zfill(4)

    def get_scp_string(self, root, fcp, wwpn, lun):
        return ("=root=%(root)s selinux=0 zfcp.allow_lun_scan=0 "
                "rd.zfcp=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s") % {
                'root': root, 'fcp': fcp, 'wwpn': wwpn, 'lun': lun}

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        return ['#!/bin/bash\n',
                ('echo -e "[defaultboot]\\n'
                 'timeout=5\\n'
                 'default=boot-from-volume\\n'
                 'target=/boot/\\n'
                 '[boot-from-volume]\\n'
                 'image=%(image)s\\n'
                 'ramdisk=%(ramdisk)s\\n'
                 'parameters=\\"root=%(root)s '
                 'rd.zfcp=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s '
                 'zfcp.allow_lun_scan=0 selinux=0\\""'
                 '>/etc/zipl_volume.conf\n'
                 'zipl -c /etc/zipl_volume.conf')
                % {'image': image, 'ramdisk': ramdisk, 'root': root,
                   'fcp': fcp, 'wwpn': wwpn, 'lun': lun}]


class sles(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network/'

    def _get_cidr_from_ip_netmask(self, ip, netmask):
        netmask_fields = netmask.split('.')
        bin_str = ''
        for octet in netmask_fields:
            bin_str += bin(int(octet))[2:].zfill(8)
        mask = str(len(bin_str.rstrip('0')))
        cidr_v4 = ip + '/' + mask
        return cidr_v4

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        cidr_v4 = self._get_cidr_from_ip_netmask(ip_v4, netmask_v4)
        cfg_str = "BOOTPROTO=\'static\'\n"
        cfg_str += "IPADDR=\'%s\'\n" % cidr_v4
        cfg_str += "BROADCAST=\'%s\'\n" % broadcast_v4
        cfg_str += "STARTMODE=\'onboot\'\n"
        cfg_str += ("NAME=\'OSA Express Network card (%s)\'\n" %
                    address_read)
        return cfg_str

    def _get_route_str(self, gateway_v4):
        route_str = 'default %s - -\n' % gateway_v4
        return route_str

    def _get_cmd_str(self, address_read, address_write, address_data):
        cmd_str = 'qeth_configure -l 0.0.%s ' % address_read.lower()
        cmd_str += '0.0.%(write)s 0.0.%(data)s 1\n' % {'write':
                address_write.lower(), 'data': address_data.lower()}
        return cmd_str

    def _get_dns_filename(self):
        return '/etc/resolv.conf'

    def _get_device_filename(self, device_num):
        return 'ifcfg-eth' + str(device_num)

    def _get_device_name(self, device_num):
        return 'eth' + str(device_num)

    def _append_udev_info(self, cfg_files, file_name_route, route_cfg_str,
                          udev_cfg_str):
        udev_file_name = '/etc/udev/rules.d/70-persistent-net.rules'
        cfg_files.append((udev_file_name, udev_cfg_str))
        if len(route_cfg_str) > 0:
            cfg_files.append((file_name_route, route_cfg_str))

    def _get_udev_configuration(self, device, dev_channel):
        cfg_str = 'SUBSYSTEM==\"net\", ACTION==\"add\", DRIVERS==\"qeth\",'
        cfg_str += ' KERNELS==\"%s\", ATTR{type}==\"1\",' % dev_channel
        cfg_str += ' KERNEL==\"eth*\", NAME=\"eth%s\"\n' % device

        return cfg_str

    def get_scp_string(self, root, fcp, wwpn, lun):
        return ("=root=%(root)s "
                "zfcp.device=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s") % {
                'root': root, 'fcp': fcp, 'wwpn': wwpn, 'lun': lun}

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        return ['#!/bin/bash\n',
                ('echo -e "[defaultboot]\\n'
                 'default=boot-from-volume\\n'
                 '[boot-from-volume]\\n'
                 'image=%(image)s\\n'
                 'target = /boot/zipl\\n'
                 'ramdisk=%(ramdisk)s\\n'
                 'parameters=\\"root=%(root)s '
                 'zfcp.device=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s\\""'
                 '>/etc/zipl_volume.conf\n'
                 'mkinitrd\n'
                 'zipl -c /etc/zipl_volume.conf')
                % {'image': image, 'ramdisk': ramdisk, 'root': root,
                   'fcp': fcp, 'wwpn': wwpn, 'lun': lun}]

    def assemble_zfcp_srcdev(self, fcp, wwpn, lun):
        path = '/dev/disk/by-path/ccw-0.0.%(fcp)s-zfcp-0x%(wwpn)s:0x%(lun)s'
        srcdev = path % {'fcp': fcp, 'wwpn': wwpn, 'lun': lun}
        return srcdev


class sles11(sles):
    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'sleep 2',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'service network restart',
                          'cio_ignore -u'))

    def get_change_passwd_command(self, admin_password):
        return 'echo %s|passwd --stdin root' % admin_password


class sles12(sles):
    def get_znetconfig_contents(self):
        remove_route = 'rm -f %s/ifroute-eth*' % self._get_network_file_path()
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'sleep 2',
                          remove_route,
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'cio_ignore -u'))

    def get_change_passwd_command(self, admin_password):
        return "echo 'root:%s' | chpasswd" % admin_password

    def get_scp_string(self, root, fcp, wwpn, lun):
        return ("=root=%(root)s zfcp.allow_lun_scan=0 "
                "zfcp.device=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s") % {
                'root': root, 'fcp': fcp, 'wwpn': wwpn, 'lun': lun}

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        return ['#!/bin/bash\n',
                ('echo -e "[defaultboot]\\n'
                 'default=boot-from-volume\\n'
                 '[boot-from-volume]\\n'
                 'image=%(image)s\\n'
                 'target = /boot/zipl\\n'
                 'ramdisk=%(ramdisk)s\\n'
                 'parameters=\\"root=%(root)s '
                 'zfcp.device=0.0.%(fcp)s,0x%(wwpn)s,0x%(lun)s '
                 'zfcp.allow_lun_scan=0\\""'
                 '>/etc/zipl_volume.conf\n'
                 'mkinitrd\n'
                 'zipl -c /etc/zipl_volume.conf')
                % {'image': image, 'ramdisk': ramdisk, 'root': root,
                   'fcp': fcp, 'wwpn': wwpn, 'lun': lun}]


class ubuntu(LinuxDist):
    def create_network_configuration_files(self, file_path, network_info):
        """Generate network configuration files to instance."""
        base_vdev = CONF.zvm.default_nic_vdev
        cfg_files = []
        cmd_strings = ''
        network_config_file_name = self._get_network_file()
        network_cfg_str = 'auto lo\n'
        network_cfg_str += 'iface lo inet loopback\n'

        for vif in network_info:
            network_hw_config_fname = self._get_device_filename(base_vdev)
            network_hw_config_str = self._get_network_hw_config_str(base_vdev)
            cfg_files.append((network_hw_config_fname, network_hw_config_str))
            network = vif['network']
            (cfg_str, dns_str) = self._generate_network_configuration(network,
                base_vdev)
            LOG.debug('Network configure file content is: %s', cfg_str)
            network_cfg_str += cfg_str
            if len(dns_str) > 0:
                network_cfg_str += dns_str
            base_vdev = str(hex(int(base_vdev, 16) + 3))[2:]
        cfg_files.append((network_config_file_name, network_cfg_str))
        return cfg_files, cmd_strings

    def _get_network_file(self):
        return '/etc/network/interfaces'

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4):
        cfg_str = 'auto ' + device + '\n'
        cfg_str += 'iface ' + device + ' inet static\n'
        cfg_str += 'address ' + ip_v4 + '\n'
        cfg_str += 'netmask ' + netmask_v4 + '\n'
        cfg_str += 'broadcast ' + broadcast_v4 + '\n'
        cfg_str += 'gateway ' + gateway_v4 + '\n'
        return cfg_str

    def _generate_network_configuration(self, network, vdev):
        ip_v4 = dns_str = ''
        subnets_v4 = [s for s in network['subnets'] if s['version'] == 4]

        if len(subnets_v4[0]['ips']) > 0:
            ip_v4 = subnets_v4[0]['ips'][0]['address']
        if len(subnets_v4[0]['dns']) > 0:
            for dns in subnets_v4[0]['dns']:
                dns_str += 'dns-nameservers ' + dns['address'] + '\n'
        netmask_v4 = str(subnets_v4[0].as_netaddr().netmask)
        gateway_v4 = subnets_v4[0]['gateway']['address'] or ''
        broadcast_v4 = str(subnets_v4[0].as_netaddr().broadcast)
        device = self._get_device_name(vdev)
        cfg_str = self._get_cfg_str(device, broadcast_v4, gateway_v4,
                                    ip_v4, netmask_v4)
        return cfg_str, dns_str

    def _get_route_str(self, gateway_v4):
        return ''

    def _get_cmd_str(self, address_read, address_write, address_data):
        return ''

    def _get_device_name(self, device_num):
        return 'enc' + str(device_num)

    def _get_dns_filename(self):
        return ''

    def _get_device_filename(self, device_num):
        return '/etc/sysconfig/hardware/config-ccw-0.0.' + str(device_num)

    def _get_network_hw_config_str(self, base_vdev):
        ccwgroup_chans_str = ' '.join((
                            '0.0.' + str(hex(int(base_vdev, 16)))[2:],
                            '0.0.' + str(hex(int(base_vdev, 16) + 1))[2:],
                            '0.0.' + str(hex(int(base_vdev, 16) + 2))[2:]))
        return '\n'.join(('CCWGROUP_CHANS=(' + ccwgroup_chans_str + ')',
                          'QETH_OPTIONS=layer2'))

    def _get_network_file_path(self):
        pass

    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'sleep 2',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          '/etc/init.d/networking restart',
                          'cio_ignore -u'))

    def _get_udev_configuration(self, device, dev_channel):
        return ''

    def _append_udev_info(self, cfg_files, file_name_route, route_cfg_str,
                          udev_cfg_str):
        pass

    def get_scp_string(self, root, fcp, wwpn, lun):
        pass

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        pass


class ubuntu16(ubuntu):

    def get_change_passwd_command(self, admin_password):
        return "echo 'root:%s' | chpasswd" % admin_password


class LinuxDistManager(object):
    def get_linux_dist(self, os_version):
        distro, release = self.parse_dist(os_version)
        return globals()[distro + release]

    def _parse_release(self, os_version, distro, remain):
        supported = {'rhel': ['6', '7'],
                     'sles': ['11', '12'],
                     'ubuntu': ['16']}
        releases = supported[distro]

        for r in releases:
            if remain.startswith(r):
                return r
        else:
            msg = 'Can not handle os: %s' % os_version
            raise exception.ZVMException(msg=msg)

    def parse_dist(self, os_version):
        """Separate os and version from os_version.

        Possible return value are only:
        ('rhel', x.y) and ('sles', x.y) where x.y may not be digits
        """
        supported = {'rhel': ['rhel', 'redhat', 'red hat'],
                    'sles': ['suse', 'sles'],
                    'ubuntu': ['ubuntu']}
        os_version = os_version.lower()
        for distro, patterns in supported.items():
            for i in patterns:
                if os_version.startswith(i):
                    # Not guarrentee the version is digital
                    remain = os_version.split(i, 2)[1]
                    release = self._parse_release(os_version, distro, remain)
                    return distro, release

        msg = 'Can not handle os: %s' % os_version
        raise exception.ZVMException(msg=msg)
