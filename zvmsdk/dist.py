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


import abc
import netaddr
import os
import six

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smtclient


CONF = config.CONF
LOG = log.LOG


@six.add_metaclass(abc.ABCMeta)
class LinuxDist(object):
    """Linux distribution base class

    Due to we need to interact with linux dist and inject different files
    according to the dist version. Currently RHEL6, RHEL7, SLES11, SLES12
    and UBUNTU16 are supported.
    """
    def __init__(self):
        self._smtclient = smtclient.get_smtclient()

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
        ip_cidr = netmask_v4 = broadcast_v4 = ''
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
            ip_cidr = network['cidr']
            netmask_v4 = str(netaddr.IPNetwork(ip_cidr).netmask)
            broadcast_v4 = str(netaddr.IPNetwork(ip_cidr).broadcast)
            if broadcast_v4 == 'None':
                broadcast_v4 = ''

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
            if ip_cidr != '':
                mask = ip_cidr.rpartition('/')[2]
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

    def get_network_configuration_files(self, vdev):
        vdev = vdev.lower()
        file_path = self._get_network_file_path()
        device = self._get_device_filename(vdev)
        target_net_conf_file_name = os.path.join(file_path, device)
        return target_net_conf_file_name

    def delete_vdev_info(self, vdev):
        cmd = self._delete_vdev_info(vdev)
        return cmd

    @abc.abstractmethod
    def _get_network_file_path(self):
        """Get network file configuration path."""
        pass

    def get_change_passwd_command(self, admin_password):
        """construct change password command

        :admin_password: the password to be changed to
        """
        return "echo 'root:%s' | chpasswd" % admin_password

    def modprobe_zfcp_module(self):
        # modprobe zfcp module
        modprobe = 'modprobe zfcp\n'
        return modprobe

    @abc.abstractmethod
    def _get_source_device_path(self, fcp, target_wwpn, target_lun):
        # A sample path for rhel/sles is like:
        #   '/dev/disk/by-path/ccw-0.0.1fb3-zfcp-0x5005076801102991:0x0021000000000000'.
        # On Ubuntu it's like:
        #   '/dev/disk/by-path/ccw-0.0.1fb3-fc-0x5005076801102991-lun-33'
        pass

    def _get_wwid(self):
        var_wwid_line = ('wwid_line=`/sbin/udevadm info --query=all '
                         '--name=$SourceDevice | egrep -a -i \"ID_SERIAL=\"`')
        var_wwid = 'WWID=${wwid_line##*=}\n'
        wwid = '\n'.join((var_wwid_line,
                          var_wwid))
        return wwid

    def _get_rules_config_file_path(self):
        config_file_lib = '/lib/udev/rules.d/56-zfcp.rules'
        find_config = 'ConfigLib="%s"\n' % config_file_lib
        find_config += 'if [ -e "$ConfigLib" ]\n'
        find_config += 'then\n'
        find_config += '    ConfigFile="/lib/udev/rules.d/56-zfcp.rules"\n'
        find_config += 'else\n'
        find_config += '    ConfigFile="/etc/udev/rules.d/56-zfcp.rules"\n'
        find_config += 'fi\n'
        # TODO: if /etc/xxx not exist?
        return find_config

    def _add_udev_rules(self, mount_point, target_wwpn, target_lun, multipath):
        # TODO: mount_point format check?
        # get var value of TargetFile, WWPN, LUN
        target_filename = mount_point.replace('/dev/', '')
        var_target_file = 'TargetFile="%s"\n' % target_filename
        var_wwpn = 'WWPN="%s"\n' % target_wwpn
        var_lun = 'LUN="%s"\n' % target_lun
        # find the right path of config file
        var_config_file = self._get_rules_config_file_path()
        # add rules
        if multipath:
            # KERNEL: device name in kernel
            # ENV: environment variable
            # SYMLINK: create symbol link for device under /dev
            link_item = ('KERNEL==\\"dm-*\\", '
                         'ENV{DM_UUID}==\\"mpath-$WWID\\", '
                         'SYMLINK+=\\"$TargetFile\\"')
        else:
            link_item = ('KERNEL==\\"sd*\\", ATTRS{wwpn}==\\"$WWPN\\", '
                         'ATTRS{fcp_lun}==\\"$LUN\\", '
                         'SYMLINK+=\\"$TargetFile%n\\"')
        var_link_item = 'LinkItem="%s"\n' % link_item
        add_rules_cmd = ''.join((var_target_file,
                                 var_wwpn,
                                 var_lun,
                                 var_config_file,
                                 var_link_item,
                                 'echo -e $LinkItem >> $ConfigFile\n'))
        return add_rules_cmd

    def _remove_udev_rules(self, mount_point, target_wwpn, target_lun,
                           multipath):
        # TODO: mount_point format check?
        # get file name
        target_filename = mount_point.replace('/dev/', '')
        var_target_file = 'TargetFile="%s"\n' % target_filename
        var_wwpn = 'WWPN="%s"\n' % target_wwpn
        var_lun = 'LUN="%s"\n' % target_lun
        # find the right path of config file
        var_config_file = self._get_rules_config_file_path()
        # remove rules
        if multipath:
            remove_rules_cmd = ('sed -i -e /SYMLINK+=\\"$TargetFile\\"/d '
                                '$ConfigFile\n')
        else:
            remove_rules_cmd = ('sed -i -e '
                                '/SYMLINK+=\\"$TargetFile%n\\"/d '
                                '$ConfigFile\n')
        cmds = ''.join((var_target_file,
                        var_wwpn,
                        var_lun,
                        var_config_file,
                        remove_rules_cmd))
        return cmds

    def _reload_rules_config_file(self, multipath):
        # reload the rules by sending reload signal to systemd-udevd
        reload_cmd = 'udevadm control --reload'
        # trigger uevent with the device path in /sys
        if multipath:
            create_symlink_cmd = 'udevadm trigger --sysname-match=dm-*'
        else:
            create_symlink_cmd = 'udevadm trigger --sysname-match=sd*'
        return '\n'.join((reload_cmd,
                          create_symlink_cmd))

    def create_mount_point(self, fcp, target_wwpn,
                          target_lun, mount_point, multipath):
        # get path of source device
        var_source_device = self._get_source_device_path(fcp,
                                                         target_wwpn,
                                                         target_lun)
        # get WWID
        var_wwid = self._get_wwid()
        # add rules into config file
        add_rules = self._add_udev_rules(mount_point, target_wwpn, target_lun,
                                         multipath)
        # reload the rules
        reload_rules = self._reload_rules_config_file(multipath)
        return ''.join((var_source_device,
                        var_wwid,
                        add_rules,
                        reload_rules))

    def remove_mount_point(self, mount_point, target_wwpn, target_lun,
                           multipath):
        # remove rules
        remove_rules = self._remove_udev_rules(mount_point, target_wwpn,
                                               target_lun, multipath)
        # reload the rules
        reload_rules = self._reload_rules_config_file(multipath)
        return '\n'.join((remove_rules,
                          reload_rules))

    def settle_file_system(self):
        # Settle the file system so when we are done
        # the device is fully available
        settle = 'if [[ $(which udevadm 2> /dev/null) != \'\' ]]; then\n'
        settle += '    udevadm settle\n'
        settle += 'else\n'
        settle += '    udevsettle\n'
        settle += 'fi\n'
        return settle

    def wait_for_file_ready(self, fcp, target_wwpn, target_lun):
        # Sometimes the file takes longer to appear.
        # We will wait up to 3 minutes.
        var_src_dev = self._get_source_device_path(fcp, target_wwpn,
                                                   target_lun)
        scripts = 'if [[ ! -e $SourceDevice ]]; then\n'
        scripts += '    maxTime=0\n'
        scripts += '    for time in 1 2 2 5 10 10 30 60 60\n'
        scripts += '    do\n'
        scripts += '      if [[ -e $SourceDevice ]]; then\n'
        scripts += '        break\n'
        scripts += '      fi\n'
        scripts += '      maxTime=$maxTime+$time\n'
        scripts += '      sleep $time\n'
        scripts += '    done\n'
        scripts += 'fi\n'
        return '\n'.join((var_src_dev,
                          scripts))

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point):
        shell_cmds = ''
        shell_cmds += self.modprobe_zfcp_module()
        shell_cmds += self._online_fcp_device(fcp)
        shell_cmds += self._set_sysfs(fcp, target_wwpn, target_lun)
        shell_cmds += self._set_zfcp_config_files(fcp, target_wwpn, target_lun)
        shell_cmds += self.settle_file_system()
        shell_cmds += self.wait_for_file_ready(fcp, target_wwpn, target_lun)
        # TODO:rollback??
        if multipath:
            shell_cmds += self._set_zfcp_multipath()
        if mount_point != '':
            shell_cmds += self.create_mount_point(fcp, target_wwpn, target_lun,
                                                  mount_point, multipath)
        return '\n'.join(('#!/bin/bash', shell_cmds))

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point):
        shell_cmds = ''
        shell_cmds += self._offline_fcp_device(fcp, target_wwpn,
                                               target_lun, multipath)
        if multipath:
            shell_cmds += self._restart_multipath()
        if mount_point != '':
            shell_cmds += self.remove_mount_point(mount_point, target_wwpn,
                                                  target_lun, multipath)
        return '\n'.join(('#!/bin/bash', shell_cmds))

    @abc.abstractmethod
    def _online_fcp_device(self, fcp):
        pass

    @abc.abstractmethod
    def _offline_fcp_device(self, fcp, target_wwpn,
                            target_lun, multipath):
        pass

    @abc.abstractmethod
    def _set_sysfs(self, fcp, target_wwpn, target_lun):
        pass

    @abc.abstractmethod
    def _set_zfcp_config_files(self, fcp, target_wwpn, target_lun):
        pass

    @abc.abstractmethod
    def _restart_multipath(self):
        pass

    @abc.abstractmethod
    def _set_zfcp_multipath(self):
        pass

    @abc.abstractmethod
    def _config_to_persistent(self, multipath):
        pass

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

    @abc.abstractmethod
    def _delete_vdev_info(self, vdev):
        """delete udev rules file."""
        pass

    def generate_set_hostname_script(self, hostname):
        lines = ['#!/bin/bash\n',
                 'echo -n %s > /etc/hostname\n' % hostname,
                 '/bin/hostname %s\n' % hostname]
        return lines


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

    def _delete_vdev_info(self, vdev):
        return ''

    def _online_fcp_device(self, fcp):
        """rhel online zfcp. sampe to all rhel distro."""
        # cio_ignore
        cio_ignore = '/sbin/cio_ignore -r %s > /dev/null\n' % fcp
        # set the fcp online
        online_dev = '/sbin/chccwdev -e %s > /dev/null\n' % fcp
        return cio_ignore + online_dev

    def _offline_fcp_device(self, fcp, target_wwpn, target_lun, multipath):
        """rhel offline zfcp. sampe to all rhel distro."""
        offline_dev = 'chccwdev -d %s' % fcp
        delete_records = self._delete_zfcp_config_records(fcp,
                                                          target_wwpn,
                                                          target_lun)
        return '\n'.join((offline_dev,
                          delete_records))

    def _set_zfcp_multipath(self):
        """sampe to all rhel distro"""
        # update multipath configuration
        modprobe = 'modprobe dm-multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        conf_cmd = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        mpathconf = 'mpathconf'
        restart = self._restart_multipath()
        return '\n'.join((modprobe,
                          conf_cmd,
                          mpathconf,
                          'sleep 2',
                          restart,
                          'sleep 2\n'))

    def _config_to_persistent(self):
        """rhel"""
        pass

    def _delete_zfcp_config_records(self, fcp, target_wwpn, target_lun):
        """rhel"""
        device = '0.0.%s' % fcp
        data = {'wwpn': target_wwpn, 'lun': target_lun,
                'device': device, 'zfcpConf': '/etc/zfcp.conf'}
        delete_records_cmd = ('sed -i -e '
                              '\"/%(device)s %(wwpn)s %(lun)s/d\" '
                              '%(zfcpConf)s\n' % data)
        return delete_records_cmd

    def _get_source_device_path(self, fcp, target_wwpn, target_lun):
        """rhel"""
        device = '0.0.%s' % fcp
        data = {'device': device, 'wwpn': target_wwpn, 'lun': target_lun}
        var_source_device = ('SourceDevice="/dev/disk/by-path/ccw-%(device)s-'
                             'zfcp-%(wwpn)s:%(lun)s"\n' % data)
        return var_source_device


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

    def _restart_multipath(self):
        """rhel6"""
        restart_multipathd = 'service multipathd restart\n'
        return restart_multipathd

    def _set_sysfs(self, fcp, target_wwpn, target_lun):
        """rhel6 set WWPN and LUN in sysfs"""
        device = '0.0.%s' % fcp
        port_add = "echo '%s' > " % target_wwpn
        port_add += "/sys/bus/ccw/drivers/zfcp/%s/port_add" % device
        unit_add = "echo '%s' > " % target_lun
        unit_add += "/sys/bus/ccw/drivers/zfcp/%(device)s/%(wwpn)s/unit_add\n"\
                    % {'device': device, 'wwpn': target_wwpn}
        return '\n'.join((port_add,
                          unit_add))

    def _set_zfcp_config_files(self, fcp, target_wwpn, target_lun):
        """rhel6 set WWPN and LUN in configuration files"""
        device = '0.0.%s' % fcp
        set_zfcp_conf = 'echo "%(device)s %(wwpn)s %(lun)s" >> /etc/zfcp.conf'\
                        % {'device': device, 'wwpn': target_wwpn,
                           'lun': target_lun}
        trigger_uevent = 'echo "add" >> /sys/bus/ccw/devices/%s/uevent\n'\
                         % device
        return '\n'.join((set_zfcp_conf,
                          trigger_uevent))

    def generate_set_hostname_script(self, hostname):
        lines = ['#!/bin/bash\n',
                 'sed -i "s/^HOSTNAME=.*/HOSTNAME=%s/" '
                    '/etc/sysconfig/network\n' % hostname,
                 '/bin/hostname %s\n' % hostname]
        return lines


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
        activeIP_str += 'ip link set dev %s up\n' % device
        return activeIP_str

    def create_active_net_interf_cmd(self):
        return 'systemctl start zvmguestconfigure.service'

    def _get_clean_command(self):
        files = os.path.join(self._get_network_file_path(),
                             self._get_all_device_filename())
        return '\nrm -f %s\n' % files

    def _set_sysfs(self, fcp, target_wwpn, target_lun):
        """rhel7 set WWPN and LUN in sysfs"""
        device = '0.0.%s' % fcp
        unit_add = "echo '%s' > " % target_lun
        unit_add += "/sys/bus/ccw/drivers/zfcp/%(device)s/%(wwpn)s/unit_add\n"\
                    % {'device': device, 'wwpn': target_wwpn}
        return unit_add

    def _set_zfcp_config_files(self, fcp, target_wwpn, target_lun):
        """rhel7 set WWPN and LUN in configuration files"""
        device = '0.0.%s' % fcp
        set_zfcp_conf = 'echo "%(device)s %(wwpn)s %(lun)s" >> /etc/zfcp.conf'\
                        % {'device': device, 'wwpn': target_wwpn,
                           'lun': target_lun}
        trigger_uevent = 'echo "add" >> /sys/bus/ccw/devices/%s/uevent\n'\
                         % device
        return '\n'.join((set_zfcp_conf,
                          trigger_uevent))

    def _restart_multipath(self):
        """rhel7"""
        restart_multipathd = 'systemctl restart multipathd.service\n'
        return restart_multipathd


class sles(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network/'

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        cfg_str = "BOOTPROTO=\'static\'\n"
        cfg_str += "IPADDR=\'%s\'\n" % ip_v4
        cfg_str += "NETMASK=\'%s\'\n" % netmask_v4
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

    def _delete_vdev_info(self, vdev):
        """handle udev rules file."""
        vdev = vdev.lower()
        rules_file_name = '/etc/udev/rules.d/51-qeth-0.0.%s.rules' % vdev
        cmd = 'rm -f %s\n' % rules_file_name

        address = '0.0.%s' % str(vdev).zfill(4)
        udev_file_name = '/etc/udev/rules.d/70-persistent-net.rules'
        cmd += "sed -i '/%s/d' %s\n" % (address, udev_file_name)
        cmd += "sed -i '/%s/d' %s\n" % (address,
                                        '/boot/zipl/active_devices.txt')
        return cmd

    def _online_fcp_device(self, fcp):
        """sles online fcp"""
        # cio_ignore
        cio_ignore = '/sbin/cio_ignore -r %s > /dev/null\n' % fcp
        # set the fcp online
        online_dev = '/sbin/chccwdev -e %s > /dev/null\n' % fcp
        return cio_ignore + online_dev

    def _set_sysfs(self, fcp, target_wwpn, target_lun):
        """sles set WWPN and LUN in sysfs"""
        device = '0.0.%s' % fcp
        unit_add = "echo '%s' > " % target_lun
        unit_add += "/sys/bus/ccw/drivers/zfcp/%(device)s/%(wwpn)s/unit_add\n"\
                    % {'device': device, 'wwpn': target_wwpn}
        return unit_add

    def _set_zfcp_config_files(self, fcp, target_wwpn, target_lun):
        """sles set WWPN and LUN in configuration files"""
        device = '0.0.%s' % fcp
        # host config
        host_config = '/sbin/zfcp_host_configure %s 1' % device
        # disk config
        disk_config = '/sbin/zfcp_disk_configure ' +\
                      '%(device)s %(wwpn)s %(lun)s 1' %\
                      {'device': device, 'wwpn': target_wwpn,
                       'lun': target_lun}
        create_config = 'touch /etc/udev/rules.d/51-zfcp-%s.rules' % device
        # check if the file already contains the zFCP channel
        check_channel = ('out=`cat "/etc/udev/rules.d/51-zfcp-%s.rules" '
                         '| egrep -i "ccw/%s]online"`\n' % (device, device))
        check_channel += 'if [[ ! $out ]]; then\n'
        check_channel += ('  echo "ACTION==\\"add\\", SUBSYSTEM==\\"ccw\\", '
                          'KERNEL==\\"%(device)s\\", IMPORT{program}=\\"'
                          'collect %(device)s %%k %(device)s zfcp\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device})
        check_channel += ('  echo "ACTION==\\"add\\", SUBSYSTEM==\\"drivers\\"'
                          ', KERNEL==\\"zfcp\\", IMPORT{program}=\\"'
                          'collect %(device)s %%k %(device)s zfcp\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device})
        check_channel += ('  echo "ACTION==\\"add\\", '
                          'ENV{COLLECT_%(device)s}==\\"0\\", '
                          'ATTR{[ccw/%(device)s]online}=\\"1\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device})
        check_channel += 'fi\n'
        check_channel += ('echo "ACTION==\\"add\\", KERNEL==\\"rport-*\\", '
                          'ATTR{port_name}==\\"%(wwpn)s\\", '
                          'SUBSYSTEMS==\\"ccw\\", KERNELS==\\"%(device)s\\",'
                          'ATTR{[ccw/%(device)s]%(wwpn)s/unit_add}='
                          '\\"%(lun)s\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device, 'wwpn': target_wwpn,
                                  'lun': target_lun})
        return '\n'.join((host_config,
                          'sleep 2',
                          disk_config,
                          'sleep 2',
                          create_config,
                          check_channel))

    def _restart_multipath(self):
        """sles restart multipath"""
        # reload device mapper
        reload_map = 'systemctl restart multipathd\n'
        return reload_map

    def _set_zfcp_multipath(self):
        """sles"""
        # modprobe DM multipath kernel module
        modprobe = 'modprobe dm_multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        conf_cmd = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        restart = self._restart_multipath()
        return '\n'.join((modprobe,
                          conf_cmd,
                          restart))

    def _offline_fcp_device(self, fcp, target_wwpn, target_lun, multipath):
        """sles offline zfcp. sampe to all rhel distro."""
        device = '0.0.%s' % fcp
        # disk config
        disk_config = '/sbin/zfcp_disk_configure ' +\
                      '%(device)s %(wwpn)s %(lun)s 0' %\
                      {'device': device, 'wwpn': target_wwpn,
                       'lun': target_lun}
        # host config
        host_config = '/sbin/zfcp_host_configure %s 0' % device
        return '\n'.join((disk_config,
                          host_config))

    def _config_to_persistent(self):
        """sles"""
        pass

    def _get_source_device_path(self, fcp, target_wwpn, target_lun):
        """sles"""
        device = '0.0.%s' % fcp
        data = {'device': device, 'wwpn': target_wwpn, 'lun': target_lun}
        var_source_device = ('SourceDevice="/dev/disk/by-path/ccw-%(device)s-'
                             'zfcp-%(wwpn)s:%(lun)s"\n' % data)
        return var_source_device


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
                          'cio_ignore -u',
                          'wicked ifreload all'))

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
        activeIP_str += 'ip link set dev %s up\n' % device
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

    def get_network_configuration_files(self, vdev):
        vdev = vdev.lower()
        network_hw_config_fname = self._get_device_filename(vdev)
        return network_hw_config_fname

    def delete_vdev_info(self, vdev):
        cmd = self._delete_vdev_info(vdev)
        return cmd

    def _delete_vdev_info(self, vdev):
        """handle vdev related info."""
        vdev = vdev.lower()
        network_config_file_name = self._get_network_file()
        device = self._get_device_name(vdev)
        cmd = '\n'.join(("num=$(sed -n '/auto %s/=' %s)" % (device,
                                                    network_config_file_name),
                        "dns=$(awk 'NR==(\"\'$num\'\"+6)&&"
                        "/dns-nameservers/' %s)" %
                                                    network_config_file_name,
                        "if [[ -n $dns ]]; then",
                        "  sed -i '/auto %s/,+6d' %s" % (device,
                                                    network_config_file_name),
                        "else",
                        "  sed -i '/auto %s/,+5d' %s" % (device,
                                                    network_config_file_name),
                        "fi"))
        return cmd

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
            ip_cidr = network['cidr']
            netmask_v4 = str(netaddr.IPNetwork(ip_cidr).netmask)
            broadcast_v4 = str(netaddr.IPNetwork(ip_cidr).broadcast)
            if broadcast_v4 == 'None':
                broadcast_v4 = ''

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

    def _online_fcp_device(self, fcp):
        """ubuntu online fcp"""
        return ''

    def _set_sysfs(self, fcp, target_wwpn, target_lun):
        """ubuntu set WWPN and LUN in sysfs"""
        return ''

    def _set_zfcp_config_files(self, fcp, target_wwpn, target_lun):
        """ubuntu zfcp configuration """
        host_config = '/sbin/chzdev zfcp-host %s -e' % fcp

        device = '0.0.%s' % fcp
        target = '%s:%s:%s' % (device, target_wwpn, target_lun)
        disk_config = '/sbin/chzdev zfcp-lun %s -e\n' % target
        return '\n'.join((host_config,
                          disk_config))

    def _check_multipath_tools(self):
        multipath = 'multipath'
        return multipath

    def _restart_multipath(self):
        """ubuntu"""
        # restart multipathd
        reload_map = 'systemctl restart multipath-tools.service\n'
        return reload_map

    def _set_zfcp_multipath(self):
        """ubuntu multipath setup
        multipath-tools and multipath-tools-boot must be set.
        Now only when the find_multpaths set to 'no', can the multipath
        command has output. maybe a bug?
        """
        modprobe = self._check_multipath_tools()
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        conf_file = 'defaults {\n'
        conf_file += '\tfind_multipaths no\n'
        conf_file += '}\n'
        conf_cmd = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        restart = self._restart_multipath()
        return '\n'.join((modprobe,
                          conf_cmd,
                          restart))

    def _offline_fcp_device(self, fcp, target_wwpn, target_lun, multipath):
        """ubuntu offline zfcp."""
        device = '0.0.%s' % fcp
        target = '%s:%s:%s' % (device, target_wwpn, target_lun)
        disk_offline = '/sbin/chzdev zfcp-lun %s -d' % target
        host_offline = '/sbin/chzdev zfcp-host %s -d' % fcp
        offline_dev = 'chccwdev -d %s' % fcp
        return '\n'.join((disk_offline,
                          host_offline,
                          offline_dev))

    def _config_to_persistent(self):
        """ubuntu"""
        pass

    def _format_lun(self, lun):
        """ubuntu"""
        target_lun = int(lun[2:6], 16)
        return target_lun

    def _get_source_device_path(self, fcp, target_wwpn, target_lun):
        """ubuntu"""
        target_lun = self._format_lun(target_lun)
        device = '0.0.%s' % fcp
        data = {'device': device, 'wwpn': target_wwpn, 'lun': target_lun}
        var_source_device = ('SourceDevice="/dev/disk/by-path/ccw-%(device)s-'
                             'fc-%(wwpn)s-lun-%(lun)s"\n' % data)
        return var_source_device


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
