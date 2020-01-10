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
import mock

from zvmsdk import dist
from zvmsdk.tests.unit import base


class RHEL6TestCase(base.SDKTestCase):
    """Testcases for different distros."""

    @classmethod
    def setUpClass(cls):
        super(RHEL6TestCase, cls).setUpClass()
        cls.os_version = 'redhat6.7'

    def setUp(self):
        super(RHEL6TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    def test_create_network_configuration_files(self):
        pass

    @mock.patch('zvmsdk.dist.LinuxDist._reload_rules_config_file')
    @mock.patch('zvmsdk.dist.LinuxDist._add_udev_rules')
    @mock.patch('zvmsdk.dist.LinuxDist._get_wwids')
    def test_create_mount_point_multipath(self,
                                          get_wwids, add_rules,
                                          reload_rules):
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        mount_point = '/dev/sde'
        multipath = True
        get_wwids.return_value = 'fake_ret'
        add_rules.return_value = 'fake_ret'
        reload_rules.return_value = 'fake_ret'
        self.linux_dist.create_mount_point(fcp, wwpns, lun,
                                           mount_point, multipath)
        get_wwids.assert_called_once_with()
        add_rules.assert_called_once_with(mount_point, lun, multipath)
        reload_rules.assert_called_once_with(multipath)

    def test_get_source_devices(self):
        fcp = '1fc5'
        lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        expect = ('SourceDevices=(`ls /dev/disk/by-path/ | '
                  'grep "ccw-%s-zfcp-.*:%s"`)\n'
                  % (device, lun))
        ret = self.linux_dist._get_source_devices(fcp, lun)
        self.assertEqual(ret, expect)

    def test_get_wwids(self):
        wwids = 'declare -a WWIDs\n'
        wwids += 'LEN=${#SourceDevices[@]}\n'
        wwids += 'for ((i=0;i<$LEN;i++)) do\n'
        wwids += ('    WWIDs[i]=`/lib/udev/scsi_id --page 0x83 '
                  '--whitelisted /dev/disk/by-path/${SourceDevices[i]}`\n')
        wwids += 'done\n'
        ret = self.linux_dist._get_wwids()
        self.assertEqual(ret, wwids)

    def test_add_udev_rules_multipath(self):
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sde'
        var_target_file = 'TargetFile="sde"\n'
        var_lun = 'LUN="%s"\n' % lun
        config_file_lib = '/lib/udev/rules.d/56-zfcp.rules'
        find_config = 'ConfigLib="%s"\n' % config_file_lib
        find_config += 'if [ -e "$ConfigLib" ]\n'
        find_config += 'then\n'
        find_config += '    ConfigFile="/lib/udev/rules.d/56-zfcp.rules"\n'
        find_config += 'else\n'
        find_config += '    ConfigFile="/etc/udev/rules.d/56-zfcp.rules"\n'
        find_config += 'fi\n'
        var_config_file = find_config
        link_item = ('KERNEL==\\"dm-*\\", '
                     'ENV{DM_UUID}==\\"mpath-$WWID\\", '
                     'SYMLINK+=\\"$TargetFile\\"')
        var_link_items = 'for WWID in ${WWIDs[@]}\n'
        var_link_items += 'do\n'
        var_link_items += '    LinkItem="%s"\n' % link_item
        var_link_items += '    echo -e $LinkItem >> $ConfigFile\n'
        var_link_items += 'done\n'
        add_rules_cmd = ''.join((var_target_file,
                                 var_lun,
                                 var_config_file,
                                 var_link_items))
        ret = self.linux_dist._add_udev_rules(mount_point, lun, multipath)
        self.assertEqual(ret, add_rules_cmd)

    def test_reload_udev_rules_multipath(self):
        multipath = True
        reload_cmd = 'udevadm control --reload'
        create_symlink_cmd = 'udevadm trigger --sysname-match=dm-*'
        expect = '\n'.join((reload_cmd,
                            create_symlink_cmd))
        ret = self.linux_dist._reload_rules_config_file(multipath)
        self.assertEqual(ret, expect)

    @mock.patch('zvmsdk.dist.LinuxDist.create_mount_point')
    @mock.patch('zvmsdk.dist.rhel._set_zfcp_multipath')
    @mock.patch('zvmsdk.dist.LinuxDist.wait_for_file_ready')
    @mock.patch('zvmsdk.dist.LinuxDist.settle_file_system')
    @mock.patch('zvmsdk.dist.rhel6._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel6._set_sysfs')
    @mock.patch('zvmsdk.dist.LinuxDist._check_auto_scan')
    @mock.patch('zvmsdk.dist.LinuxDist._check_npiv_enabled')
    @mock.patch('zvmsdk.dist.LinuxDist._get_active_wwpns')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.modprobe_zfcp_module')
    def test_get_volume_attach_configuration_cmds(self, check_module,
                                                  online_device, active_wwpns,
                                                  check_npiv, check_scan,
                                                  set_sysfs, zfcp_config,
                                                  settle, wait_file,
                                                  zfcp_multipath,
                                                  create_mount_point):
        """ RHEL6 """
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        check_module.return_value = 'fake_ret'
        online_device.return_value = 'fake_ret'
        zfcp_config.return_value = 'fake_ret'
        zfcp_multipath.return_value = 'fake_ret'
        create_mount_point.return_value = 'fake_ret'
        active_wwpns.return_value = 'fake_ret'
        check_npiv.return_value = 'fake_ret'
        check_scan.return_value = 'fake_ret'
        set_sysfs.return_value = 'fake_ret'
        settle.return_value = 'fake_ret'
        wait_file.return_value = 'fake_ret'
        self.linux_dist.get_volume_attach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, True)
        check_module.assert_called_once_with()
        online_device.assert_called_once_with(fcp)
        active_wwpns.assert_called_once_with(fcp)
        check_npiv.assert_called_once_with(fcp)
        check_scan.assert_called_once_with()
        set_sysfs.assert_called_once_with(fcp, wwpns, lun)
        zfcp_config.assert_called_once_with(fcp, lun)
        settle.assert_called_once_with()
        wait_file.assert_called_once_with(fcp, lun)
        zfcp_multipath.assert_called_once_with(True)
        create_mount_point.assert_called_once_with(fcp, wwpns,
                                                   lun, mount_point,
                                                   multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel6._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel._delete_zfcp_config_records')
    @mock.patch('zvmsdk.dist.LinuxDist._disconnect_volume')
    def test_get_volume_detach_configuration_cmds_1(self, disconnect_volume,
                                                  delete_zfcp_records,
                                                  offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):
        """ RHEL6, connections == 2"""
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        delete_zfcp_records.return_value = 'fake_ret'
        disconnect_volume.return_value = 'fake_ret'
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, 2)
        disconnect_volume.assert_called_once_with(fcp, lun, True)
        delete_zfcp_records.assert_called_once_with(fcp, lun)
        remove_mount_point.assert_called_once_with(mount_point, wwpns,
                                                   lun, multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel6._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel._delete_zfcp_config_records')
    @mock.patch('zvmsdk.dist.LinuxDist._disconnect_volume')
    def test_get_volume_detach_configuration_cmds_2(self, disconnect_volume,
                                                  delete_zfcp_records,
                                                  offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):
        """ RHEL6, connections < 1"""
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        delete_zfcp_records.return_value = 'fake_ret'
        disconnect_volume.return_value = 'fake_ret'
        # connections < 1
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, 0)
        disconnect_volume.assert_called_once_with(fcp, lun, True)
        delete_zfcp_records.assert_called_once_with(fcp, lun)
        offline_device.assert_called_once_with(fcp)
        restart_multipath.assert_called_once_with()
        remove_mount_point.assert_called_once_with(mount_point, wwpns,
                                                   lun, multipath)

    def test_online_fcp_device(self):
        fcp = '1fc5'
        cmd_cio_ignore = '/sbin/cio_ignore -r %s > /dev/null\n' % fcp
        cmd_online_dev = '/sbin/chccwdev -e %s > /dev/null\n' % fcp
        ret = self.linux_dist._online_fcp_device(fcp)
        expect = cmd_cio_ignore + cmd_online_dev
        self.assertEqual(ret, expect)

    def test_offline_fcp_device(self):
        fcp = '1fc5'
        cmd_offline_dev = 'chccwdev -d %s\n' % fcp
        ret = self.linux_dist._offline_fcp_device(fcp)
        expect = cmd_offline_dev
        self.assertEqual(ret, expect)

    def test_set_zfcp_config_files(self):
        """ RHEL6 """
        fcp = '1fc5'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        data = {'device': device, 'lun': target_lun}
        # add to port(WWPN)
        set_zfcp_conf = 'for wwpn in ${ActiveWWPNs[@]}\n'
        set_zfcp_conf += 'do\n'
        set_zfcp_conf += ('    echo "%(device)s $wwpn %(lun)s" >> '
                          '/etc/zfcp.conf\n' % data)
        set_zfcp_conf += 'done\n'
        set_zfcp_conf += ('echo "add" >> /sys/bus/ccw/devices/%s/uevent\n'
                          % device)
        ret = self.linux_dist._set_zfcp_config_files(fcp, target_lun)
        expect = set_zfcp_conf
        self.assertEqual(ret, expect)

    def test_restart_multipath(self):
        ret = self.linux_dist._restart_multipath()
        expect = 'service multipathd restart\n'
        self.assertEqual(ret, expect)

    def test_set_zfcp_multipath_new(self):
        """ RHEL6 """
        modprobe = 'modprobe dm-multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        cmd_mpathconf = 'mpathconf'
        restart = 'service multipathd restart\n'
        expect = '\n'.join((modprobe,
                            cmd_conf,
                            cmd_mpathconf,
                            'sleep 2',
                            restart,
                            'sleep 2\n'))
        ret = self.linux_dist._set_zfcp_multipath(True)
        self.assertEqual(ret, expect)

    def test_set_zfcp_multipath_not_new(self):
        """ RHEL6, same to all rhel"""
        rescan = 'for host in `ls /sys/class/scsi_host/`\n'
        rescan += 'do\n'
        rescan += '    echo "- - -" > /sys/class/scsi_host/$host/scan\n'
        rescan += 'done\n'
        ret = self.linux_dist._set_zfcp_multipath(False)
        self.assertEqual(ret, rescan)


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
               'nic_vdev': '1000'}]
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
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[11])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[12])

    @mock.patch('zvmsdk.dist.LinuxDist.create_mount_point')
    @mock.patch('zvmsdk.dist.rhel._set_zfcp_multipath')
    @mock.patch('zvmsdk.dist.LinuxDist.wait_for_file_ready')
    @mock.patch('zvmsdk.dist.LinuxDist.settle_file_system')
    @mock.patch('zvmsdk.dist.rhel7._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel7._set_sysfs')
    @mock.patch('zvmsdk.dist.LinuxDist._check_auto_scan')
    @mock.patch('zvmsdk.dist.LinuxDist._check_npiv_enabled')
    @mock.patch('zvmsdk.dist.LinuxDist._get_active_wwpns')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.modprobe_zfcp_module')
    def test_get_volume_attach_configuration_cmds(self, check_module,
                                                  online_device, active_wwpns,
                                                  check_npiv, check_scan,
                                                  set_sysfs, zfcp_config,
                                                  settle, wait_file,
                                                  zfcp_multipath,
                                                  create_mount_point):

        """ RHEL7 """
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        check_module.return_value = 'fake_ret'
        online_device.return_value = 'fake_ret'
        zfcp_config.return_value = 'fake_ret'
        zfcp_multipath.return_value = 'fake_ret'
        create_mount_point.return_value = 'fake_ret'
        active_wwpns.return_value = 'fake_ret'
        check_npiv.return_value = 'fake_ret'
        check_scan.return_value = 'fake_ret'
        set_sysfs.return_value = 'fake_ret'
        settle.return_value = 'fake_ret'
        wait_file.return_value = 'fake_ret'
        self.linux_dist.get_volume_attach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, True)
        check_module.assert_called_once_with()
        online_device.assert_called_once_with(fcp)
        active_wwpns.assert_called_once_with(fcp)
        check_npiv.assert_called_once_with(fcp)
        check_scan.assert_called_once_with()
        set_sysfs.assert_called_once_with(fcp, wwpns, lun)
        zfcp_config.assert_called_once_with(fcp, lun)
        settle.assert_called_once_with()
        wait_file.assert_called_once_with(fcp, lun)
        zfcp_multipath.assert_called_once_with(True)
        create_mount_point.assert_called_once_with(fcp, wwpns,
                                                   lun, mount_point,
                                                   multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel7._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel._delete_zfcp_config_records')
    @mock.patch('zvmsdk.dist.LinuxDist._disconnect_volume')
    def test_get_volume_detach_configuration_cmds_1(self, disconnect_volume,
                                                  delete_zfcp_records,
                                                  offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):

        """ RHEL7 """
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        delete_zfcp_records.return_value = 'fake_ret'
        disconnect_volume.return_value = 'fake_ret'
        # connections == 2
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, 2)
        disconnect_volume.assert_called_once_with(fcp, lun, True)
        delete_zfcp_records.assert_called_once_with(fcp, lun)
        remove_mount_point.assert_called_once_with(mount_point, wwpns,
                                                   lun, multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel7._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel._delete_zfcp_config_records')
    @mock.patch('zvmsdk.dist.LinuxDist._disconnect_volume')
    def test_get_volume_detach_configuration_cmds_2(self, disconnect_volume,
                                                  delete_zfcp_records,
                                                  offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):

        """ RHEL7 """
        fcp = '1fc5'
        wwpns = ['0x5005076812341234', '0x5005076812345678']
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        delete_zfcp_records.return_value = 'fake_ret'
        disconnect_volume.return_value = 'fake_ret'

        # connections < 1
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpns, lun,
                                                             multipath,
                                                             mount_point, 0)
        disconnect_volume.assert_called_once_with(fcp, lun, True)
        delete_zfcp_records.assert_called_once_with(fcp, lun)
        offline_device.assert_called_once_with(fcp)
        restart_multipath.assert_called_once_with()
        remove_mount_point.assert_called_once_with(mount_point, wwpns,
                                                   lun, multipath)

    def test_set_zfcp_config_files(self):
        """ RHEL7, same to rhel6"""
        pass

    def test_restart_multipath(self):
        ret = self.linux_dist._restart_multipath()
        expect = 'systemctl restart multipathd.service\n'
        self.assertEqual(ret, expect)

    def test_set_zfcp_multipath_new(self):
        """ RHEL7"""
        modprobe = 'modprobe dm-multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        cmd_mpathconf = 'mpathconf'
        restart = 'systemctl restart multipathd.service\n'
        expect = '\n'.join((modprobe,
                            cmd_conf,
                            cmd_mpathconf,
                            'sleep 2',
                            restart,
                            'sleep 2\n'))
        ret = self.linux_dist._set_zfcp_multipath(True)
        self.assertEqual(ret, expect)

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
                           'nic_vdev': '1000'}]
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
        self.assertEqual('DNS1="9.0.2.1"', cfg_str[11])
        self.assertEqual('DNS2="9.0.3.1"', cfg_str[12])

class SLESTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(SLESTestCase, cls).setUpClass()

    def setUp(self):
        super(SLESTestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.sles11_dist = self.dist_manager.get_linux_dist('sles11')()
        self.sles12_dist = self.dist_manager.get_linux_dist('sles12')()

    def test_set_zfcp_config_files(self):
        """ sles """
        fcp = '1fc5'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        host_config = '/sbin/zfcp_host_configure %s 1' % device
        disk_config = 'for wwpn in ${ActiveWWPNs[@]}\n'
        disk_config += 'do\n'
        disk_config += '    /sbin/zfcp_disk_configure ' +\
                      '%(device)s $wwpn %(lun)s 1\n' %\
                      {'device': device, 'lun': target_lun}
        disk_config += 'done\n'
        create_config = 'touch /etc/udev/rules.d/51-zfcp-%s.rules' % device
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
        check_channel += 'for wwpn in ${ActiveWWPNs[@]}\n'
        check_channel += 'do\n'
        check_channel += ('    echo "ACTION==\\"add\\", KERNEL==\\"rport-*\\",'
                          ' ATTR{port_name}==\\"$wwpn\\", '
                          'SUBSYSTEMS==\\"ccw\\", KERNELS==\\"%(device)s\\",'
                          'ATTR{[ccw/%(device)s]$wwpn/unit_add}='
                          '\\"%(lun)s\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device, 'lun': target_lun})
        check_channel += 'done\n'
        expect = '\n'.join((host_config,
                            'sleep 1',
                            disk_config,
                            'sleep 1',
                            create_config,
                            check_channel))
        ret = self.sles11_dist._set_zfcp_config_files(fcp,
                                                      target_lun)
        self.assertEqual(ret, expect)

        ret = self.sles12_dist._set_zfcp_config_files(fcp, target_lun)
        self.assertEqual(ret, expect)

    def test_restart_multipath(self):
        ret = self.sles11_dist._restart_multipath()
        start_multipathd = 'systemctl restart multipathd\n'
        self.assertEqual(ret, start_multipathd)

        ret = self.sles12_dist._restart_multipath()
        start_multipathd = 'systemctl restart multipathd\n'
        self.assertEqual(ret, start_multipathd)

    def test_set_zfcp_multipath(self):
        """ SLES """
        modprobe = 'modprobe dm_multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        restart = 'systemctl restart multipathd\n'
        expect = '\n'.join((modprobe,
                            cmd_conf,
                            restart))
        ret = self.sles11_dist._set_zfcp_multipath(True)
        self.assertEqual(ret, expect)

        ret = self.sles12_dist._set_zfcp_multipath(True)
        self.assertEqual(ret, expect)


class UBUNTUTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(UBUNTUTestCase, cls).setUpClass()

    def setUp(self):
        super(UBUNTUTestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist('ubuntu16')()

    def test_check_multipath_tools(self):
        multipath = 'multipath'
        ret = self.linux_dist._check_multipath_tools()
        self.assertEqual(ret, multipath)

    def test_restart_multipath(self):
        reload_map = 'systemctl restart multipath-tools.service\n'
        ret = self.linux_dist._restart_multipath()
        self.assertEqual(ret, reload_map)

    def test_set_zfcp_multipath(self):
        """ Ubuntu """
        modprobe = 'multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        conf_file = 'defaults {\n'
        conf_file += '\tfind_multipaths no\n'
        conf_file += '}\n'
        cmd_conf = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        restart = 'systemctl restart multipath-tools.service\n'
        expect = '\n'.join((modprobe,
                            cmd_conf,
                            restart))
        ret = self.linux_dist._set_zfcp_multipath(True)
        self.assertEqual(ret, expect)

    def test_offline_fcp_device(self):
        """ Ubuntu """
        fcp = '1fc5'
        host_offline = '/sbin/chzdev zfcp-host %s -d' % fcp
        offline_dev = 'chccwdev -d %s' % fcp
        ret = self.linux_dist._offline_fcp_device(fcp)

        expect = '\n'.join((host_offline,
                            offline_dev))
        self.assertEqual(ret, expect)
