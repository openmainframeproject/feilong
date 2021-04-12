# Copyright 2017,2020 IBM Corp.
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
from jinja2 import Environment, FileSystemLoader

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
    , UBUNTU16 and RHCOS4 are supported.
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
        dns_v4 = []
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
                dns_v4.append(dns)

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
                                    subchannels, dns_v4)
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

    @abc.abstractmethod
    def get_volume_attach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, new):
        "generate punch script for attachment configuration"
        pass

    @abc.abstractmethod
    def get_volume_detach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, connections):
        "generate punch script for detachment configuration"
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

    def get_template(self, module, template_name):
        relative_path = module + "/templates"
        base_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(base_path, relative_path,
                                          template_name)
        template_file_directory = os.path.dirname(template_file_path)
        template_loader = FileSystemLoader(searchpath=template_file_directory)
        env = Environment(loader=template_loader)
        template = env.get_template(template_name)
        return template

    def get_extend_partition_cmds(self):
        template = self.get_template("vmactions", "grow_root_volume.j2")
        content = template.render()
        return content


class rhel(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network-scripts/'

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels, dns_v4):
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
        if (dns_v4 is not None) and (len(dns_v4) > 0):
            i = 1
            for dns in dns_v4:
                cfg_str += 'DNS' + str(i) + '=\"' + dns + '\"\n'
                i += 1
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

    def generate_set_hostname_script(self, hostname):
        lines = ['#!/bin/bash\n',
                 'sed -i "s/^HOSTNAME=.*/HOSTNAME=%s/" '
                    '/etc/sysconfig/network\n' % hostname,
                 '/bin/hostname %s\n' % hostname]
        return lines

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, new):
        "generate punch script for attachment configuration"
        func_name = 'get_volume_attach_configuration_cmds'
        raise exception.SDKFunctionNotImplementError(func=func_name,
                                                     modID='volume')

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, connections):
        "generate punch script for detachment configuration"
        func_name = 'get_volume_attach_configuration_cmds'
        raise exception.SDKFunctionNotImplementError(func=func_name,
                                                     modID='volume')


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

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, new):
        """rhel7"""
        template = self.get_template("volumeops", "rhel7_attach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename)
        return content

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, connections):
        """rhel7"""
        template = self.get_template("volumeops", "rhel7_detach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename)
        return content


class rhel8(rhel7):
    """docstring for rhel8"""

    def _get_device_filename(self, vdev):
        return 'ifcfg-enc' + str(vdev).zfill(4)

    def _get_all_device_filename(self):
        return 'ifcfg-enc*'

    def _get_device_name(self, vdev):
        # Construct a device like enc1000
        return 'enc' + str(vdev).zfill(4)

    def _get_clean_command(self):
        files = os.path.join(self._get_network_file_path(),
                             self._get_all_device_filename())
        return '\nrm -f %s\n' % files

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, new):
        """rhel8 attach script generation"""
        template = self.get_template("volumeops", "rhel8_attach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename)
        return content

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, connections):
        """rhel8 detach script generation"""
        template = self.get_template("volumeops", "rhel8_detach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename)
        return content


class rhcos(LinuxDist):
    def create_coreos_parameter(self, network_info, userid):
        # Create the coreos parameters for ZCC, includes ignitionUrl, diskType,
        # nicID and ipConfig, then save them in a temp file
        try:
            vif = network_info[0]
            ip_addr = vif['ip_addr']
            gateway_addr = vif['gateway_addr']
            netmask = vif['cidr'].split("/")[-1]
            nic_name = "enc" + vif['nic_vdev']
            # update dns name server info if they're defined in subnet
            _dns = ["", ""]
            if 'dns_addr' in vif.keys():
                if ((vif['dns_addr'] is not None) and
                    (len(vif['dns_addr']) > 0)):
                    _index = 0
                    for dns in vif['dns_addr']:
                        _dns[_index] = dns
                        _index += 1
            # transfor network info and hostname into form of
            # ip=<client-IP>:[<peer>]:<gateway-IP>:<netmask>:<client_hostname>
            # :<interface>:none[:[<dns1>][:<dns2>]]
            result = "%s::%s:%s:%s:%s:none:%s:%s" % (ip_addr, gateway_addr,
                                                     netmask, userid, nic_name,
                                                     _dns[0], _dns[1])
            tmp_path = self._smtclient.get_guest_path(userid.upper())
            LOG.debug("Created coreos fixed ip parameter: %(result)s, "
                      "writing them to tempfile: %(tmp_path)s/fixed_ip_param"
                      % {'result': result, 'tmp_path': tmp_path})
            with open('%s/fixed_ip_param' % tmp_path, 'w') as f:
                f.write(result)
                f.write('\n')
            return True
        except Exception as err:
            LOG.error("Failed to create coreos parameter for userid '%s',"
                      "error: %s" % (userid, err))
            return False

    def read_coreos_parameter(self, userid):
        # read coreos fixed ip parameters from tempfile by matching userid
        tmp_path = self._smtclient.get_guest_path(userid.upper())
        tmp_file_path = ('%s/fixed_ip_param' % tmp_path)
        with open(tmp_file_path, 'r') as f:
            fixed_ip_parameter = f.read().replace('\n', '')
            LOG.debug('Read coreos fixed ip parameter: %(parameter)s '
                      'from tempfile: %(filename)s'
                      % {'parameter': fixed_ip_parameter,
                      'filename': tmp_file_path})
        # Clean up tempfile
        self._smtclient.clean_temp_folder(tmp_path)
        return fixed_ip_parameter

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, new):
        "generate punch script for attachment configuration"
        func_name = 'get_volume_attach_configuration_cmds'
        raise exception.SDKFunctionNotImplementError(func=func_name,
                                                     modID='volume')

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpns,
                                             target_lun, multipath,
                                             mount_point, connections):
        "generate punch script for detachment configuration"
        func_name = 'get_volume_attach_configuration_cmds'
        raise exception.SDKFunctionNotImplementError(func=func_name,
                                                     modID='volume')

    def _append_udev_info(self, cmd_str, cfg_files, file_name_route,
                      route_cfg_str, udev_cfg_str, first=False):
        pass

    def _append_udev_rules_file(self, cfg_files, base_vdev):
        pass

    def _delete_vdev_info(self, vdev):
        pass

    def _enable_network_interface(self, device, ip, broadcast):
        pass

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels):
        pass

    def _get_clean_command(self):
        pass

    def _get_cmd_str(self, address_read, address_write, address_data):
        pass

    def _get_device_filename(self, vdev):
        pass

    def _get_device_name(self, vdev):
        pass

    def _get_dns_filename(self):
        pass

    def _get_network_file_path(self):
        pass

    def _get_route_str(self, gateway_v4):
        pass

    def _get_udev_configuration(self, device, dev_channel):
        pass

    def _get_udev_rules(self, channel_read, channel_write, channel_data):
        pass

    def create_active_net_interf_cmd(self):
        pass

    def get_scp_string(self, root, fcp, wwpn, lun):
        pass

    def get_zipl_script_lines(self, image, ramdisk, root, fcp, wwpn, lun):
        pass

    def get_znetconfig_contents(self):
        pass


class rhcos4(rhcos):
    pass


class sles(LinuxDist):
    def _get_network_file_path(self):
        return '/etc/sysconfig/network/'

    def _get_cfg_str(self, device, broadcast_v4, gateway_v4, ip_v4,
                     netmask_v4, address_read, subchannels, dns_v4):
        cfg_str = "BOOTPROTO=\'static\'\n"
        cfg_str += "IPADDR=\'%s\'\n" % ip_v4
        cfg_str += "NETMASK=\'%s\'\n" % netmask_v4
        cfg_str += "BROADCAST=\'%s\'\n" % broadcast_v4
        cfg_str += "STARTMODE=\'onboot\'\n"
        cfg_str += ("NAME=\'OSA Express Network card (%s)\'\n" %
                    address_read)
        if (dns_v4 is not None) and (len(dns_v4) > 0):
            self.dns_v4 = dns_v4
        else:
            self.dns_v4 = None
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

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, new):
        """sles attach script generation"""
        template = self.get_template("volumeops", "sles_attach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        # TODO: also consider is first attach or not
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename)
        return content

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, connections):
        """sles detach script generation"""
        if connections > 0:
            # if this volume is the last volume
            # we need to know it and offline the FCP devices
            is_last_volume = 0
        else:
            is_last_volume = 1
        template = self.get_template("volumeops", "sles_detach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        content = template.render(fcp=fcp, lun=target_lun,
                                  target_filename=target_filename,
                                  is_last_volume=is_last_volume)
        return content


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


class sles15(sles12):
    """docstring for sles15"""
    def get_znetconfig_contents(self):
        remove_route = 'rm -f %s/ifroute-eth*' % self._get_network_file_path()
        replace_var = 'NETCONFIG_DNS_STATIC_SERVERS'
        replace_file = '/etc/sysconfig/network/config'
        remove_dns_cfg = "sed -i '/^\s*%s=\"/d' %s" % (replace_var,
                replace_file)

        if self.dns_v4:
            dns_addrs = ' '.join(self.dns_v4)
            netconfig_dns = '%s="%s"' % (replace_var, dns_addrs)
            set_dns = "echo '%s' >> %s" % (netconfig_dns, replace_file)

            return '\n'.join(('cio_ignore -R',
                              'znetconf -R -n',
                              'sleep 2',
                              remove_route,
                              remove_dns_cfg,
                              set_dns,
                              'udevadm trigger',
                              'udevadm settle',
                              'sleep 2',
                              'znetconf -A',
                              'cio_ignore -u',
                              'wicked ifreload all'))
        else:
            return '\n'.join(('cio_ignore -R',
                              'znetconf -R -n',
                              'sleep 2',
                              remove_route,
                              remove_dns_cfg,
                              'udevadm trigger',
                              'udevadm settle',
                              'sleep 2',
                              'znetconf -A',
                              'cio_ignore -u',
                              'wicked ifreload all'))


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

    def _check_multipath_tools(self):
        multipath = 'multipath'
        return multipath

    def _format_lun(self, lun):
        """ubuntu"""
        target_lun = int(lun[2:6], 16)
        return target_lun

    def get_volume_attach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, new):
        """ubuntu attach script generation"""
        template = self.get_template("volumeops", "ubuntu_attach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        # the parameter 'target_lun' is hex for either v7k or ds8k:
        # for v7k, target_lun[2] == '0' and target_lun[6:] == '0'
        # for ds8k, target_lun[2] == '4'

        # in the future, we add support to other storage provider whose lun
        # id may use bits in target_lun[6:], such as, 0x0003040200000000

        # when attach v7k volume:
        #   1. if the lun id less than 256,
        #   the file under /dev/disk/by-path/ will as below,
        #   take 'lun id = 0' as example:
        #   ccw-0.0.5c03-fc-0x5005076802400c1a-lun-0,the the lun id is decimal.
        #   2. if the lun id is equal or more than 256,
        #   the file under /dev/disk/by-path/ will as below,
        #   take 'lun id = 256' as example:
        #   ccw-0.0.1a0d-fc-0x500507680b26bac7-lun-0x0100000000000000,
        #   the lun id is hex.
        # when attach ds8k volume:
        #   the file under /dev/disk/by-path/ will as below,
        #   take "volume id 140c" as example:
        #   ccw-0.0.1a0d-fc-0x5005076306035388-lun-0x4014400c00000000,
        #   the lun id is always hex.
        lun = self._format_lun(target_lun)
        if all([x == '0' for x in target_lun[6:]]) and lun < 256:
            lun_id = lun
        else:
            lun_id = target_lun
        # TODO: also consider is first attach or not
        content = template.render(fcp=fcp, lun=target_lun, lun_id=lun_id,
                                  target_filename=target_filename)
        return content

    def get_volume_detach_configuration_cmds(self, fcp, target_wwpn,
                                             target_lun, multipath,
                                             mount_point, connections):
        """ubuntu detach script generation"""
        if connections > 0:
            # if this volume is the last volume
            # we need to know it and offline the FCP devices
            is_last_volume = 0
        else:
            is_last_volume = 1
        template = self.get_template("volumeops", "ubuntu_detach_volume.j2")
        target_filename = mount_point.replace('/dev/', '')
        lun = self._format_lun(target_lun)
        if all([x == '0' for x in target_lun[6:]]) and lun < 256:
            lun_id = lun
        else:
            lun_id = target_lun
        content = template.render(fcp=fcp, lun=target_lun, lun_id=lun_id,
                                  target_filename=target_filename,
                                  is_last_volume=is_last_volume)
        return content


class ubuntu16(ubuntu):
    pass


class ubuntu20(ubuntu):
    def _get_device_filename(self, device_num):
        return '/etc/netplan/' + str(device_num) + '.yaml'

    def _get_network_file(self):
        return '/etc/netplan/00-zvmguestconfigure-config.yaml'

    def _get_network_file_path(self):
        return '/etc/netplan/'

    def get_znetconfig_contents(self):
        return '\n'.join(('cio_ignore -R',
                          'znetconf -R -n',
                          'sleep 2',
                          'udevadm trigger',
                          'udevadm settle',
                          'sleep 2',
                          'znetconf -A',
                          'netplan apply',
                          'cio_ignore -u'))

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
        net_enable_cmd = ''
        if first:
            clean_cmd = self._get_clean_command()
        else:
            clean_cmd = ''

        for network in guest_networks:
            base_vdev = network['nic_vdev'].lower()
            (cfg_str) = self._generate_network_configuration(network,
                                    base_vdev)
            LOG.debug('Network configure file content is: %s', cfg_str)
        if first:
            cfg_files.append((network_config_file_name, cfg_str))
        else:
            # TODO: create interface with cmd_strings after VM deployed
            raise Exception('Ubuntu20 is not supported to create interface'
                            'after VM deployed.')

        return cfg_files, cmd_strings, clean_cmd, net_enable_cmd

    def _generate_network_configuration(self, network, vdev):
        ip_v4 = dns_str = gateway_v4 = ''
        cidr = ''
        dns_v4 = []
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
                dns_v4.append(dns)

        if (('cidr' in network.keys()) and
            (network['cidr'] is not None)):
            cidr = network['cidr'].split('/')[1]

        device = self._get_device_name(vdev)
        if dns_v4:
            cfg_str = {'network':
                            {'ethernets':
                                {device:
                                    {'addresses': [ip_v4 + '/' + cidr],
                                     'gateway4': gateway_v4,
                                     'nameservers':
                                        {'addresses': dns_v4}
                                    }
                                },
                            'version': 2
                            }
                        }
        else:
            cfg_str = {'network':
                            {'ethernets':
                                {device:
                                    {'addresses': [ip_v4 + '/' + cidr],
                                     'gateway4': gateway_v4
                                    }
                                },
                            'version': 2
                            }
                        }
        return cfg_str


class LinuxDistManager(object):
    def get_linux_dist(self, os_version):
        distro, release = self.parse_dist(os_version)
        return globals()[distro + release]

    def _parse_release(self, os_version, distro, remain):
        supported = {'rhel': ['6', '7', '8'],
                     'sles': ['11', '12', '15'],
                     'ubuntu': ['16', '20'],
                     'rhcos': ['4']}
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
                    'ubuntu': ['ubuntu'],
                    'rhcos': ['rhcos', 'coreos', 'red hat coreos']}
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
