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
    @mock.patch('zvmsdk.dist.LinuxDist._get_wwid')
    @mock.patch.object(dist.rhel, '_get_source_device_path')
    def test_create_mount_point_multipath(self, get_source_path,
                                          get_wwid, add_rules,
                                          reload_rules):
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        mount_point = '/dev/sde'
        multipath = True
        get_source_path.return_value = 'fake_ret'
        get_wwid.return_value = 'fake_ret'
        add_rules.return_value = 'fake_ret'
        reload_rules.return_value = 'fake_ret'
        self.linux_dist.create_mount_point(fcp, wwpn, lun,
                                           mount_point, multipath)
        get_source_path.assert_called_once_with(fcp, wwpn, lun)
        get_wwid.assert_called_once_with()
        add_rules.assert_called_once_with(mount_point, wwpn, lun, multipath)
        reload_rules.assert_called_once_with(multipath)

    def test_get_source_device_path(self):
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        data = {'device': device, 'wwpn': wwpn, 'lun': lun}
        expect = ('SourceDevice="/dev/disk/by-path/ccw-%(device)s-'
                  'zfcp-%(wwpn)s:%(lun)s"\n' % data)
        ret = self.linux_dist._get_source_device_path(fcp, wwpn, lun)
        self.assertEqual(ret, expect)

    def test_get_wwid(self):
        var_wwid_line = ('wwid_line=`/sbin/udevadm info --query=all '
                         '--name=$SourceDevice | egrep -a -i \"ID_SERIAL=\"`')
        var_wwid = 'WWID=${wwid_line##*=}\n'
        wwid = '\n'.join((var_wwid_line,
                          var_wwid))
        ret = self.linux_dist._get_wwid()
        self.assertEqual(ret, wwid)

    def test_add_udev_rules_multipath(self):
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sde'
        var_target_file = 'TargetFile="sde"\n'
        var_wwpn = 'WWPN="%s"\n' % wwpn
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
        var_link_item = 'LinkItem="%s"\n' % link_item
        add_rules_cmd = ''.join((var_target_file,
                                 var_wwpn,
                                 var_lun,
                                 var_config_file,
                                 var_link_item,
                                 'echo -e $LinkItem >> $ConfigFile\n'))
        ret = self.linux_dist._add_udev_rules(mount_point, wwpn, lun,
                                              multipath)
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
    @mock.patch('zvmsdk.dist.rhel6._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.modprobe_zfcp_module')
    def test_get_volume_attach_configuration_cmds(self, check_module,
                                                  online_device, zfcp_config,
                                                  zfcp_multipath,
                                                  create_mount_point):
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        check_module.return_value = 'fake_ret'
        online_device.return_value = 'fake_ret'
        zfcp_config.return_value = 'fake_ret'
        zfcp_multipath.return_value = 'fake_ret'
        create_mount_point.return_value = 'fake_ret'
        self.linux_dist.get_volume_attach_configuration_cmds(fcp, wwpn, lun,
                                                             multipath,
                                                             mount_point)
        check_module.assert_called_once_with()
        online_device.assert_called_once_with(fcp)
        zfcp_config.assert_called_once_with(fcp, wwpn, lun)
        zfcp_multipath.assert_called_once_with()
        create_mount_point.assert_called_once_with(fcp, wwpn,
                                                   lun, mount_point,
                                                   multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel6._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    def test_get_volume_detach_configuration_cmds(self, offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):
        """ RHEL6 """
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpn, lun,
                                                             multipath,
                                                             mount_point)
        offline_device.assert_called_once_with(fcp, wwpn,
                                               lun, multipath)
        restart_multipath.assert_called_once_with()
        remove_mount_point.assert_called_once_with(mount_point, wwpn,
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
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        device = '0.0.%s' % fcp
        cmd_offline_dev = 'chccwdev -d %s' % fcp
        data = {'wwpn': wwpn, 'lun': lun,
                'device': device, 'zfcpConf': '/etc/zfcp.conf'}
        cmd_delete_records = ('sed -i -e '
                              '\"/%(device)s %(wwpn)s %(lun)s/d\" '
                              '%(zfcpConf)s\n' % data)
        ret = self.linux_dist._offline_fcp_device(fcp, wwpn, lun, multipath)
        expect = '\n'.join((cmd_offline_dev,
                            cmd_delete_records))
        self.assertEqual(ret, expect)

    def test_set_zfcp_config_files(self):
        """ RHEL6 """
        fcp = '1fc5'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        # add to port(WWPN)
        set_zfcp_conf = 'echo "%(device)s %(wwpn)s %(lun)s" >> /etc/zfcp.conf'\
                        % {'device': device, 'wwpn': target_wwpn,
                           'lun': target_lun}
        trigger_uevent = 'echo "add" >> /sys/bus/ccw/devices/%s/uevent\n'\
                         % device
        ret = self.linux_dist._set_zfcp_config_files(fcp, target_wwpn,
                                                     target_lun)
        expect = '\n'.join((set_zfcp_conf,
                            trigger_uevent))
        self.assertEqual(ret, expect)

    def test_restart_multipath(self):
        ret = self.linux_dist._restart_multipath()
        expect = 'service multipathd restart\n'
        self.assertEqual(ret, expect)

    def test_set_zfcp_multipath(self):
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
        ret = self.linux_dist._set_zfcp_multipath()
        self.assertEqual(ret, expect)


class RHEL7TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(RHEL7TestCase, cls).setUpClass()
        cls.os_version = 'redhat7.2'

    def setUp(self):
        super(RHEL7TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    @mock.patch('zvmsdk.dist.LinuxDist.create_mount_point')
    @mock.patch('zvmsdk.dist.rhel._set_zfcp_multipath')
    @mock.patch('zvmsdk.dist.rhel7._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.LinuxDist.wait_for_file_ready')
    @mock.patch('zvmsdk.dist.LinuxDist.settle_file_system')
    @mock.patch('zvmsdk.dist.rhel7._set_sysfs')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.modprobe_zfcp_module')
    def test_get_volume_attach_configuration_cmds(self, check_module,
                                                  online_device,
                                                  set_sysfs,
                                                  settle_file,
                                                  wait_file,
                                                  zfcp_config,
                                                  zfcp_multipath,
                                                  create_mount_point):
        """ RHEL7 """
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        check_module.return_value = 'fake_ret'
        online_device.return_value = 'fake_ret'
        set_sysfs.return_value = ''
        settle_file.return_value = ''
        wait_file.return_value = ''
        zfcp_config.return_value = 'fake_ret'
        zfcp_multipath.return_value = 'fake_ret'
        create_mount_point.return_value = 'fake_ret'
        self.linux_dist.get_volume_attach_configuration_cmds(fcp, wwpn, lun,
                                                             multipath,
                                                             mount_point)
        check_module.assert_called_once_with()
        online_device.assert_called_once_with(fcp)
        set_sysfs.assert_called_once_with(fcp, wwpn, lun)
        settle_file.assert_called_once_with()
        wait_file.assert_called_once_with(fcp, wwpn, lun)
        zfcp_config.assert_called_once_with(fcp, wwpn, lun)
        zfcp_multipath.assert_called_once_with()
        create_mount_point.assert_called_once_with(fcp, wwpn, lun, mount_point,
                                                   multipath)

    @mock.patch('zvmsdk.dist.LinuxDist.remove_mount_point')
    @mock.patch('zvmsdk.dist.rhel7._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    def test_get_volume_detach_configuration_cmds(self, offline_device,
                                                  restart_multipath,
                                                  remove_mount_point):
        fcp = '1fc5'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        mount_point = '/dev/sdz'
        offline_device.return_value = 'fake_ret'
        restart_multipath.return_value = 'fake_ret'
        remove_mount_point.return_value = 'fake_ret'
        self.linux_dist.get_volume_detach_configuration_cmds(fcp, wwpn, lun,
                                                             multipath,
                                                             mount_point)
        offline_device.assert_called_once_with(fcp, wwpn, lun, multipath)
        restart_multipath.assert_called_once_with()
        remove_mount_point.assert_called_once_with(mount_point, wwpn,
                                                   lun, multipath)

    def test_set_zfcp_config_files(self):
        """ RHEL7 """
        fcp = '1fc5'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        # add to port(WWPN)
        set_zfcp_conf = 'echo "%(device)s %(wwpn)s %(lun)s" >> '\
                        '/etc/zfcp.conf' % {'device': device,
                                             'wwpn': target_wwpn,
                                             'lun': target_lun}
        trigger_uevent = 'echo "add" >> /sys/bus/ccw/devices/%s/uevent\n'\
                         % device
        ret = self.linux_dist._set_zfcp_config_files(fcp, target_wwpn,
                                                     target_lun)
        expect = '\n'.join((set_zfcp_conf,
                            trigger_uevent))
        self.assertEqual(ret, expect)

    def test_restart_multipath(self):
        ret = self.linux_dist._restart_multipath()
        expect = 'systemctl restart multipathd.service\n'
        self.assertEqual(ret, expect)

    def test_set_zfcp_multipath(self):
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
        ret = self.linux_dist._set_zfcp_multipath()
        self.assertEqual(ret, expect)


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
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        host_config = '/sbin/zfcp_host_configure %s 1' % device
        disk_config = '/sbin/zfcp_disk_configure ' +\
                      '%(device)s %(wwpn)s %(lun)s 1' %\
                      {'device': device, 'wwpn': target_wwpn,
                       'lun': target_lun}
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
        check_channel += ('echo "ACTION==\\"add\\", KERNEL==\\"rport-*\\", '
                          'ATTR{port_name}==\\"%(wwpn)s\\", '
                          'SUBSYSTEMS==\\"ccw\\", KERNELS==\\"%(device)s\\",'
                          'ATTR{[ccw/%(device)s]%(wwpn)s/unit_add}='
                          '\\"%(lun)s\\""'
                          '| tee -a /etc/udev/rules.d/51-zfcp-%(device)s.rules'
                          '\n' % {'device': device, 'wwpn': target_wwpn,
                                  'lun': target_lun})
        expect = '\n'.join((host_config,
                            'sleep 2',
                            disk_config,
                            'sleep 2',
                            create_config,
                            check_channel))
        ret = self.sles11_dist._set_zfcp_config_files(fcp, target_wwpn,
                                                      target_lun)
        self.assertEqual(ret, expect)

        ret = self.sles12_dist._set_zfcp_config_files(fcp, target_wwpn,
                                                      target_lun)
        self.assertEqual(ret, expect)

    def test_restart_multipath(self):
        ret = self.sles11_dist._restart_multipath()
        start_multipathd = 'systemctl restart multipathd\n'
        self.assertEqual(ret, start_multipathd)

        ret = self.sles12_dist._restart_multipath()
        start_multipathd = 'systemctl restart multipathd\n'
        self.assertEqual(ret, start_multipathd)

    def test_set_zfcp_multipath(self):
        modprobe = 'modprobe dm_multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode \\"*\\"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e "%s" > /etc/multipath.conf' % conf_file
        restart = 'systemctl restart multipathd\n'
        expect = '\n'.join((modprobe,
                            cmd_conf,
                            restart))
        ret = self.sles11_dist._set_zfcp_multipath()
        self.assertEqual(ret, expect)

        ret = self.sles12_dist._set_zfcp_multipath()
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
        ret = self.linux_dist._set_zfcp_multipath()
        self.assertEqual(ret, expect)

    def test_offline_fcp_device(self):
        fcp = '1fc5'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        multipath = True
        device = '0.0.%s' % fcp
        target = '%s:%s:%s' % (device, target_wwpn, target_lun)
        disk_offline = '/sbin/chzdev zfcp-lun %s -d' % target
        host_offline = '/sbin/chzdev zfcp-host %s -d' % fcp
        offline_dev = 'chccwdev -d %s' % fcp
        ret = self.linux_dist._offline_fcp_device(fcp, target_wwpn,
                                                  target_lun, multipath)

        expect = '\n'.join((disk_offline,
                            host_offline,
                            offline_dev))
        self.assertEqual(ret, expect)
