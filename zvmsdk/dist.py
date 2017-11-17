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
import netaddr
import os
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

    def create_network_configuration_files(self, file_path, guest_networks,
                                           first, active=False):
        """Generate network configuration files for guest vm
        :param list guest_networks:  a list of network info for the guest.
               It has one dictionary that contain some of the below keys for
               each network, the format is:
               {'ip_addr': (str) IP address,
               'dns_addr': (list) dns addresses,
               'gateway_addr': (str) gateway address,
               'cidr': (str) cidr format
               'nic_vdev': (str) VDEV of the nic}

               Example for guest_networks:
               [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000'},
               {'ip_addr': '192.168.96.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003}]
        :returns cfg_files: the network interface configuration file name
                            and file content
                 cmd_strings: shell command, helps to enable the network
                              interface, will be put into znetconfig file
                 clean_cmd: if first is true, it is used to erase the previous
                           network interface configuration, will be put into
                           invokeScript file
                 net_enable_cmd: 'ip addr' and 'ip link' command to enable the
                                 new network interface
        """
        cfg_files = []
        cmd_strings = ''
        udev_cfg_str = ''
        dns_cfg_str = ''
        route_cfg_str = ''
        net_enable_cmd = ''
        cmd_str = None
        file_path = self._get_network_file_path()
        file_name_route = file_path + 'routes'
        if first:
            clean_cmd = self._get_clean_command()
        else:
            clean_cmd = ''

        file_name_dns = self._get_dns_filename()
        for network in guest_networks:
            base_vdev = network['nic_vdev'].lower()
            file_name = self._get_device_filename(base_vdev)
            (cfg_str, cmd_str, dns_str,
                route_str, net_cmd) = self._generate_network_configuration(
                                                network,
                                                base_vdev, active=active)
            LOG.debug('Network configure file content is: %s', cfg_str)
            target_net_conf_file_name = file_path + file_name
            cfg_files.append((target_net_conf_file_name, cfg_str))
            udev_cfg_str += self._get_udev_configuration(base_vdev,
                                '0.0.' + str(base_vdev).zfill(4))
            self._append_udev_rules_file(cfg_files, base_vdev)
            if cmd_str is not None:
                cmd_strings += cmd_str
            if net_cmd is not None:
                net_enable_cmd += net_cmd
            if len(dns_str) > 0:
                dns_cfg_str += dns_str
            if len(route_str) > 0:
                route_cfg_str += route_str

        if len(dns_cfg_str) > 0:
            cfg_files.append((file_name_dns, dns_cfg_str))
        cmd_strings = self._append_udev_info(cmd_strings, cfg_files,
                                             file_name_route,
                                             route_cfg_str,
                                             udev_cfg_str, first)
        return cfg_files, cmd_strings, clean_cmd, net_enable_cmd

    def _generate_network_configuration(self, network, vdev, active=False):
        ip_v4 = dns_str = gateway_v4 = ''
        netmask_v4 = broadcast_v4 = ''
        net_cmd = ''
        if (('ip_addr' in network.keys()) and
            (network['ip_addr'] is not None)):
            ip_v4 = network['ip_addr']

        if (('gateway_addr' in network.keys()) and
            (network['gateway_addr'] is not None)):
            gateway_v4 = network['gateway_addr']

        if (('dns_addr' in network.keys()) and
            (network['dns_addr'] is not None) and
            (len(network['dns_addr']) > 0)):
            for dns in network['dns_addr']:
                dns_str += 'nameserver ' + dns + '\n'

        if (('cidr' in network.keys()) and
            (network['cidr'] is not None)):
            netmask_v4 = str(netaddr.IPNetwork(network['cidr']).netmask)
            broadcast_v4 = str(netaddr.IPNetwork(network['cidr']).broadcast)

        device = self._get_device_name(vdev)
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
        if active and ip_v4 != '':
            if (('cidr' in network.keys()) and
                (network['cidr'] is not None)):
                mask = network['cidr'].rpartition('/')[2]
            else:
                mask = '32'
            full_ip = '%s/%s' % (ip_v4, mask)
            net_cmd = self._enable_network_interface(device, full_ip,
                                                     broadcast_v4)

        return cfg_str, cmd_str, dns_str, route_str, net_cmd

    def get_simple_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -A',
                          'cio_ignore -u'))

    def get_device_name(self, vdev):
        return self._get_device_name(vdev)

    @abc.abstractmethod
    def _get_network_file_path(self):
        """Get network file configuration path."""
        pass

    def get_change_passwd_command(self, admin_password):
        """construct change password command

        :admin_password: the password to be changed to
        """
        return "echo 'root:%s' | chpasswd" % admin_password

    @abc.abstractmethod
    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        """construct configuration file of network device."""
        pass

    @abc.abstractmethod
    def _get_device_filename(self, vdev):
        """construct the name of a network device file."""
        pass

    @abc.abstractmethod
    def _get_route_str(self, gateway_v4):
        """construct a router string."""
        pass

    @abc.abstractmethod
    def _enable_network_interface(self, device, ip, broadcast):
        """construct a router string."""
        pass

    @abc.abstractmethod
    def _get_clean_command(self):
        """construct a clean command to remove."""
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
    def _get_device_name(self, vdev):
        """construct the name of a network device."""
        pass

    @abc.abstractmethod
    def _get_udev_configuration(self, device, dev_channel):
        """construct udev configuration info."""
        pass

    @abc.abstractmethod
    def _get_udev_rules(self, channel_read, channel_write, channel_data):
        """construct udev rules info."""
        pass

    @abc.abstractmethod
    def _append_udev_info(self, cmd_str, cfg_files, file_name_route,
                          route_cfg_str, udev_cfg_str, first=False):
        return cmd_str

    @abc.abstractmethod
    def _append_udev_rules_file(self, cfg_files, base_vdev):
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

    @abc.abstractmethod
    def create_active_net_interf_cmd(self):
        """construct active command which will initialize and configure vm."""
        pass


class rhel(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network-scripts/'

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

    def _get_device_name(self, vdev):
        return 'eth' + str(vdev).zfill(4)

    def _get_udev_configuration(self, device, dev_channel):
        return ''

    def _append_udev_info(self, cmd_str, cfg_files, file_name_route,
                          route_cfg_str, udev_cfg_str, first=False):
        return cmd_str

    def _get_udev_rules(self, channel_read, channel_write, channel_data):
        """construct udev rules info."""
        return ''

    def _append_udev_rules_file(self, cfg_files, base_vdev):
        pass

    def _enable_network_interface(self, device, ip, broadcast):
        return ''


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

    def _get_device_filename(self, vdev):
        return 'ifcfg-eth' + str(vdev).zfill(4)

    def _get_all_device_filename(self):
        return 'ifcfg-eth*'

    def _get_device_name(self, vdev):
        return 'eth' + str(vdev).zfill(4)

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

    def create_active_net_interf_cmd(self):
        return 'service zvmguestconfigure start'

    def _get_clean_command(self):
        files = os.path.join(self._get_network_file_path(),
                             self._get_all_device_filename())
        return '\nrm -f %s\n' % files


class rhel7(rhel):
    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'cio_ignore -u'))

    def _get_device_filename(self, vdev):
        # Construct a device like ifcfg-enccw0.0.1000, ifcfg-enccw0.0.1003
        return 'ifcfg-enccw0.0.' + str(vdev).zfill(4)

    def _get_all_device_filename(self):
        return 'ifcfg-enccw0.0.*'

    def _get_device_name(self, vdev):
        # Construct a device like enccw0.0.1000, enccw0.0.1003
        return 'enccw0.0.' + str(vdev).zfill(4)

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

    def _enable_network_interface(self, device, ip, broadcast):
        if len(broadcast) > 0:
            activeIP_str = 'ip addr add %s broadcast %s dev %s\n' % (ip,
                                                    broadcast, device)
        else:
            activeIP_str = 'ip addr add %s dev %s\n' % (ip, device)
        activeIP_str += 'ip link set dev %s up' % device
        return activeIP_str

    def create_active_net_interf_cmd(self):
        return 'systemctl start zvmguestconfigure.service'

    def _get_clean_command(self):
        files = os.path.join(self._get_network_file_path(),
                             self._get_all_device_filename())
        return '\nrm -f %s\n' % files


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
        cmd_str += ('echo "0.0.%(read)s,0.0.%(write)s,0.0.%(data)s #`date`"'
                    ' >>/boot/zipl/active_devices.txt\n' % {'read':
                    address_read.lower(), 'write': address_write.lower(),
                    'data': address_data.lower()})
        return cmd_str

    def _get_dns_filename(self):
        return '/etc/resolv.conf'

    def _get_device_filename(self, vdev):
        return 'ifcfg-eth' + str(vdev).zfill(4)

    def _get_all_device_filename(self):
        return 'ifcfg-eth*'

    def _get_device_name(self, vdev):
        return 'eth' + str(vdev).zfill(4)

    def _append_udev_info(self, cmd_str, cfg_files, file_name_route,
                          route_cfg_str, udev_cfg_str, first=False):
        udev_file_name = '/etc/udev/rules.d/70-persistent-net.rules'
        if first:
            cfg_files.append((udev_file_name, udev_cfg_str))
            if len(route_cfg_str) > 0:
                cfg_files.append((file_name_route, route_cfg_str))
        else:
            cmd_str += ("echo '%s'"
                        ' >>%s\n' % (udev_cfg_str, udev_file_name))
            if len(route_cfg_str) > 0:
                cmd_str += ('echo "%s"'
                        ' >>%s\n' % (route_cfg_str, file_name_route))
        return cmd_str

    def _get_udev_configuration(self, device, dev_channel):
        cfg_str = 'SUBSYSTEM==\"net\", ACTION==\"add\", DRIVERS==\"qeth\",'
        cfg_str += ' KERNELS==\"%s\", ATTR{type}==\"1\",' % dev_channel
        cfg_str += ' KERNEL==\"eth*\", NAME=\"eth%s\"\n' % device

        return cfg_str

    def _append_udev_rules_file(self, cfg_files, base_vdev):
        rules_file_name = '/etc/udev/rules.d/51-qeth-0.0.%s.rules' % base_vdev
        read_ch = '0.0.' + base_vdev
        write_ch = '0.0.' + str(hex(int(base_vdev, 16) + 1))[2:]
        data_ch = '0.0.' + str(hex(int(base_vdev, 16) + 2))[2:]
        udev_rules_str = self._get_udev_rules(read_ch, write_ch, data_ch)
        cfg_files.append((rules_file_name, udev_rules_str))

    def _get_udev_rules(self, channel_read, channel_write, channel_data):
        """construct udev rules info."""
        sub_str = '%(read)s %%k %(read)s %(write)s %(data)s qeth' % {
                                      'read': channel_read,
                                       'read': channel_read,
                                       'write': channel_write,
                                       'data': channel_data}
        rules_str = '# Configure qeth device at'
        rules_str += ' %(read)s/%(write)s/%(data)s\n' % {
                             'read': channel_read,
                             'write': channel_write,
                             'data': channel_data}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"drivers\", KERNEL=='
               '\"qeth\", IMPORT{program}=\"collect %s\"\n') % sub_str
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(read)s\", IMPORT{program}="collect %(channel)s\"\n') % {
                                 'read': channel_read, 'channel': sub_str}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(write)s\", IMPORT{program}=\"collect %(channel)s\"\n') % {
                            'write': channel_write, 'channel': sub_str}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(data)s\", IMPORT{program}=\"collect %(channel)s\"\n') % {
                                'data': channel_data, 'channel': sub_str}
        rules_str += ('ACTION==\"remove\", SUBSYSTEM==\"drivers\", KERNEL==\"'
           'qeth\", IMPORT{program}=\"collect --remove %s\"\n') % sub_str
        rules_str += ('ACTION==\"remove\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(read)s\", IMPORT{program}=\"collect --remove %(channel)s\"\n'
                   ) % {'read': channel_read, 'channel': sub_str}
        rules_str += ('ACTION==\"remove\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(write)s\", IMPORT{program}=\"collect --remove %(channel)s\"\n'
                   ) % {'write': channel_write, 'channel': sub_str}
        rules_str += ('ACTION==\"remove\", SUBSYSTEM==\"ccw\", KERNEL==\"'
           '%(data)s\", IMPORT{program}=\"collect --remove %(channel)s\"\n'
                   ) % {'data': channel_data, 'channel': sub_str}
        rules_str += ('TEST==\"[ccwgroup/%(read)s]\", GOTO=\"qeth-%(read)s'
           '-end\"\n') % {'read': channel_read, 'read': channel_read}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccw\", ENV{COLLECT_'
           '%(read)s}==\"0\", ATTR{[drivers/ccwgroup:qeth]group}=\"'
           '%(read)s,%(write)s,%(data)s\"\n') % {
                    'read': channel_read, 'read': channel_read,
                    'write': channel_write, 'data': channel_data}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"drivers\", KERNEL==\"qeth'
           '\", ENV{COLLECT_%(read)s}==\"0\", ATTR{[drivers/'
           'ccwgroup:qeth]group}=\"%(read)s,%(write)s,%(data)s\"\n'
           'LABEL=\"qeth-%(read)s-end\"\n') % {
            'read': channel_read, 'read': channel_read, 'write': channel_write,
            'data': channel_data, 'read': channel_read}
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccwgroup\", KERNEL=='
           '\"%s\", ATTR{layer2}=\"1\"\n') % channel_read
        rules_str += ('ACTION==\"add\", SUBSYSTEM==\"ccwgroup\", KERNEL=='
           '\"%s\", ATTR{online}=\"1\"\n') % channel_read
        return rules_str

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

    def _enable_network_interface(self, device, ip, broadcast):
        return ''

    def _get_clean_command(self):
        files = os.path.join(self._get_network_file_path(),
                             self._get_all_device_filename())
        cmd = '\nrm -f %s\n' % files
        all_udev_rules_files = '/etc/udev/rules.d/51-qeth-0.0.*'
        cmd += 'rm -f %s\n' % all_udev_rules_files
        cmd += '> /boot/zipl/active_devices.txt\n'
        return cmd


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

    def create_active_net_interf_cmd(self):
        return 'service zvmguestconfigure start'


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

    def create_active_net_interf_cmd(self):
        return 'systemctl start zvmguestconfigure.service'

    def _enable_network_interface(self, device, ip, broadcast):
        if len(broadcast) > 0:
            activeIP_str = 'ip addr add %s broadcast %s dev %s\n' % (ip,
                                                    broadcast, device)
        else:
            activeIP_str = 'ip addr add %s dev %s\n' % (ip, device)
        activeIP_str += 'ip link set dev %s up' % device
        return activeIP_str


class ubuntu(LinuxDist):
    def create_network_configuration_files(self, file_path, guest_networks,
                                           first, active=False):
        """Generate network configuration files for guest vm
        :param list guest_networks:  a list of network info for the guest.
               It has one dictionary that contain some of the below keys for
               each network, the format is:
               {'ip_addr': (str) IP address,
               'dns_addr': (list) dns addresses,
               'gateway_addr': (str) gateway address,
               'cidr': (str) cidr format
               'nic_vdev': (str) VDEV of the nic}

               Example for guest_networks:
               [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000'},
               {'ip_addr': '192.168.96.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003}]
        """
        cfg_files = []
        cmd_strings = ''
        network_config_file_name = self._get_network_file()
        network_cfg_str = 'auto lo\n'
        network_cfg_str += 'iface lo inet loopback\n'
        net_enable_cmd = ''
        if first:
            clean_cmd = self._get_clean_command()
        else:
            clean_cmd = ''
            network_cfg_str = ''

        for network in guest_networks:
            base_vdev = network['nic_vdev'].lower()
            network_hw_config_fname = self._get_device_filename(base_vdev)
            network_hw_config_str = self._get_network_hw_config_str(base_vdev)
            cfg_files.append((network_hw_config_fname, network_hw_config_str))
            (cfg_str, dns_str) = self._generate_network_configuration(network,
                                    base_vdev)
            LOG.debug('Network configure file content is: %s', cfg_str)
            network_cfg_str += cfg_str
            if len(dns_str) > 0:
                network_cfg_str += dns_str
        if first:
            cfg_files.append((network_config_file_name, network_cfg_str))
        else:
            cmd_strings = ('echo "%s" >>%s\n' % (network_cfg_str,
                                                 network_config_file_name))
        return cfg_files, cmd_strings, clean_cmd, net_enable_cmd

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
        ip_v4 = dns_str = gateway_v4 = ''
        netmask_v4 = broadcast_v4 = ''
        if (('ip_addr' in network.keys()) and
            (network['ip_addr'] is not None)):
            ip_v4 = network['ip_addr']

        if (('gateway_addr' in network.keys()) and
            (network['gateway_addr'] is not None)):
            gateway_v4 = network['gateway_addr']

        if (('dns_addr' in network.keys()) and
            (network['dns_addr'] is not None) and
            (len(network['dns_addr']) > 0)):
            for dns in network['dns_addr']:
                dns_str += 'dns-nameservers ' + dns + '\n'

        if (('cidr' in network.keys()) and
            (network['cidr'] is not None)):
            netmask_v4 = str(netaddr.IPNetwork(network['cidr']).netmask)
            broadcast_v4 = str(netaddr.IPNetwork(network['cidr']).broadcast)

        device = self._get_device_name(vdev)
        cfg_str = self._get_cfg_str(device, broadcast_v4, gateway_v4,
                                    ip_v4, netmask_v4)

        return cfg_str, dns_str

    def _get_route_str(self, gateway_v4):
        return ''

    def _get_cmd_str(self, address_read, address_write, address_data):
        return ''

    def _enable_network_interface(self, device, ip):
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

    def _append_udev_info(self, cmd_str, cfg_files, file_name_route,
                          route_cfg_str, udev_cfg_str, first=False):
        return cmd_str

    def get_scp_string(self, root, fcp, wwpn, lun):
        pass

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        pass

    def _get_udev_rules(self, channel_read, channel_write, channel_data):
        """construct udev rules info."""
        return ''

    def _append_udev_rules_file(self, cfg_files, base_vdev):
        pass

    def create_active_net_interf_cmd(self):
        return "systemctl start zvmguestconfigure.service"

    def _get_clean_command(self):
        files = self._get_device_filename('*')
        cmd = '\nrm -f %s\n' % files
        return cmd


class ubuntu16(ubuntu):
    pass


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
