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
from zvmsdk import exception
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

    @mock.patch('zvmsdk.smutclient.SMUTClient.execute_cmd_direct')
    def test_execute_cmd(self, mock_execute_cmd):
        user_id = 'fakevm'
        cmd_str = 'ls'
        mock_execute_cmd.return_value = {'overallRC': 0}
        self.linux_dist.execute_cmd(user_id, cmd_str)
        mock_execute_cmd.assert_called_once_with(user_id, cmd_str)

    def test_create_network_configuration_files(self):
        pass

    @mock.patch('zvmsdk.dist.rhel._set_zfcp_multipath')
    @mock.patch('zvmsdk.dist.rhel6._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.check_zfcp_module')
    def test_config_volume_attach_active(self, check_module,
                                         online_device, zfcp_config,
                                         zfcp_multipath):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        self.linux_dist.config_volume_attach_active(fcp, assigner_id,
                                                    wwpn, lun, multipath)
        check_module.assert_called_once_with(assigner_id)
        online_device.assert_called_once_with(assigner_id, fcp)
        zfcp_config.assert_called_once_with(assigner_id, fcp, wwpn, lun)
        zfcp_multipath.assert_called_once_with(assigner_id)

    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel6._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.check_zfcp_module')
    def test_config_volume_attach_active_rollback(self, check_module,
                                                  online_device, zfcp_config,
                                                  offline_device):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        zfcp_config.side_effect = exception.SDKSMUTRequestFailed({}, 'err')
        self.assertRaises(exception.SDKSMUTRequestFailed,
                          self.linux_dist.config_volume_attach_active,
                          fcp, assigner_id, wwpn, lun, multipath)
        check_module.assert_called_once_with(assigner_id)
        online_device.assert_called_once_with(assigner_id, fcp)
        offline_device.assert_called_once_with(assigner_id, fcp, wwpn,
                                               lun, multipath)

    @mock.patch('zvmsdk.dist.rhel6._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    def test_config_volume_detach_active(self, offline_device,
                                         restart_multipath):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        self.linux_dist.config_volume_detach_active(fcp, assigner_id,
                                                    wwpn, lun, multipath)
        offline_device.assert_called_once_with(assigner_id, fcp, wwpn,
                                               lun, multipath)
        restart_multipath.assert_called_once_with(assigner_id)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_online_fcp_device(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        cmd_cio_ignore = 'cio_ignore -r %s' % fcp
        cmd_online_dev = 'chccwdev -e %s' % fcp
        self.linux_dist._online_fcp_device(assigner_id, fcp)
        exec_cmd.assert_has_calls([mock.call(assigner_id, cmd_cio_ignore),
                                   mock.call(assigner_id, cmd_online_dev)])

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_offline_fcp_device(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        cmd_offline_dev = 'chccwdev -d %s' % fcp
        self.linux_dist._offline_fcp_device(assigner_id, fcp,
                                            wwpn, lun, multipath)
        exec_cmd.assert_called_once_with(assigner_id, cmd_offline_dev)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_config_files(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        # add to port(WWPN)
        unit_add = "echo '%s' > " % target_lun
        unit_add += "/sys/bus/ccw/drivers/zfcp/%(device)s/%(wwpn)s/unit_add"\
                    % {'device': device, 'wwpn': target_wwpn}
        set_zfcp_conf = 'echo %(device)s %(wwpn)s %(lun)s >> /etc/zfcp.conf'\
                        % {'device': device, 'wwpn': target_wwpn,
                           'lun': target_lun}
        trigger_uevent = 'echo add >> /sys/bus/ccw/devices/%s/uevent' % device
        self.linux_dist._set_zfcp_config_files(assigner_id, fcp,
                                               target_wwpn, target_lun)
        exec_cmd.assert_has_calls([mock.call(assigner_id, unit_add),
                                   mock.call(assigner_id, set_zfcp_conf),
                                   mock.call(assigner_id, trigger_uevent)])

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_restart_multipath(self, exec_cmd):
        assigner_id = 'fakeid'
        self.linux_dist._restart_multipath(assigner_id)
        start_multipathd = '/sbin/multipath -r'
        exec_cmd.assert_called_once_with(assigner_id, start_multipathd)

    @mock.patch('zvmsdk.dist.rhel6._restart_multipath')
    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_multipath(self, exec_cmd, restart_multipath):
        assigner_id = 'fakeid'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode "*"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e %s > /etc/multipath.conf' % conf_file
        cmd_mpathconf = 'mpathconf'
        self.linux_dist._set_zfcp_multipath(assigner_id)
        exec_cmd.assert_has_calls([mock.call(assigner_id, cmd_conf),
                                   mock.call(assigner_id, cmd_mpathconf)])
        restart_multipath.assert_called_once_with(assigner_id)


class RHEL7TestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(RHEL7TestCase, cls).setUpClass()
        cls.os_version = 'redhat7.2'

    def setUp(self):
        super(RHEL7TestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist(self.os_version)()

    @mock.patch('zvmsdk.dist.rhel._set_zfcp_multipath')
    @mock.patch('zvmsdk.dist.rhel7._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.check_zfcp_module')
    def test_config_volume_attach_active(self, check_module,
                                         online_device, zfcp_config,
                                         zfcp_multipath):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        self.linux_dist.config_volume_attach_active(fcp, assigner_id,
                                                    wwpn, lun, multipath)
        check_module.assert_called_once_with(assigner_id)
        online_device.assert_called_once_with(assigner_id, fcp)
        zfcp_config.assert_called_once_with(assigner_id, fcp, wwpn, lun)
        zfcp_multipath.assert_called_once_with(assigner_id)

    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    @mock.patch('zvmsdk.dist.rhel7._set_zfcp_config_files')
    @mock.patch('zvmsdk.dist.rhel._online_fcp_device')
    @mock.patch('zvmsdk.dist.LinuxDist.check_zfcp_module')
    def test_config_volume_attach_active_rollback(self, check_module,
                                                  online_device, zfcp_config,
                                                  offline_device):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        zfcp_config.side_effect = exception.SDKSMUTRequestFailed({}, 'err')
        self.assertRaises(exception.SDKSMUTRequestFailed,
                          self.linux_dist.config_volume_attach_active,
                          fcp, assigner_id, wwpn, lun, multipath)
        check_module.assert_called_once_with(assigner_id)
        online_device.assert_called_once_with(assigner_id, fcp)
        offline_device.assert_called_once_with(assigner_id, fcp, wwpn,
                                               lun, multipath)

    @mock.patch('zvmsdk.dist.rhel7._restart_multipath')
    @mock.patch('zvmsdk.dist.rhel._offline_fcp_device')
    def test_config_volume_detach_active(self, offline_device,
                                         restart_multipath):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        wwpn = '0x5005076812341234'
        lun = '0x0026000000000000'
        multipath = True
        self.linux_dist.config_volume_detach_active(fcp, assigner_id,
                                                    wwpn, lun, multipath)
        offline_device.assert_called_once_with(assigner_id, fcp, wwpn,
                                               lun, multipath)
        restart_multipath.assert_called_once_with(assigner_id)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_config_files(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        set_zfcp_conf = 'echo %(device)s %(wwpn)s %(lun)s >> /etc/zfcp.conf'\
                        % {'device': device, 'wwpn': target_wwpn,
                           'lun': target_lun}
        self.linux_dist._set_zfcp_config_files(assigner_id, fcp,
                                               target_wwpn, target_lun)
        exec_cmd.assert_called_once_with(assigner_id, set_zfcp_conf)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_restart_multipath(self, exec_cmd):
        assigner_id = 'fakeid'
        self.linux_dist._restart_multipath(assigner_id)
        start_multipathd = '/sbin/multipath -r'
        exec_cmd.assert_called_once_with(assigner_id, start_multipathd)

    @mock.patch('zvmsdk.dist.rhel7._restart_multipath')
    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_multipath(self, exec_cmd, restart_multipath):
        assigner_id = 'fakeid'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode "*"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e %s > /etc/multipath.conf' % conf_file
        cmd_mpathconf = 'mpathconf'
        self.linux_dist._set_zfcp_multipath(assigner_id)
        exec_cmd.assert_has_calls([mock.call(assigner_id, cmd_conf),
                                   mock.call(assigner_id, cmd_mpathconf)])
        restart_multipath.assert_called_once_with(assigner_id)


class SLESTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(SLESTestCase, cls).setUpClass()

    def setUp(self):
        super(SLESTestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.sles11_dist = self.dist_manager.get_linux_dist('sles11')()
        self.sles12_dist = self.dist_manager.get_linux_dist('sles12')()

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_config_files(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        device = '0.0.%s' % fcp
        host_config = '/sbin/zfcp_host_configure %s 1' % device
        disk_config = '/sbin/zfcp_disk_configure ' +\
                      '%(device)s %(wwpn)s %(lun)s 1' %\
                      {'device': device, 'wwpn': target_wwpn,
                       'lun': target_lun}
        self.sles11_dist._set_zfcp_config_files(assigner_id, fcp,
                                               target_wwpn, target_lun)
        exec_cmd.assert_has_calls([mock.call(assigner_id, host_config),
                                   mock.call(assigner_id, disk_config)])

        self.sles12_dist._set_zfcp_config_files(assigner_id, fcp,
                                               target_wwpn, target_lun)
        exec_cmd.assert_has_calls([mock.call(assigner_id, host_config),
                                   mock.call(assigner_id, disk_config)])

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_restart_multipath(self, exec_cmd):
        assigner_id = 'fakeid'
        self.sles11_dist._restart_multipath(assigner_id)
        start_multipathd = 'systemctl restart multipathd'
        exec_cmd.assert_called_with(assigner_id, start_multipathd)

        self.sles12_dist._restart_multipath(assigner_id)
        start_multipathd = 'systemctl restart multipathd'
        exec_cmd.assert_called_with(assigner_id, start_multipathd)

    @mock.patch('zvmsdk.dist.sles._restart_multipath')
    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_multipath(self, exec_cmd, restart_multipath):
        assigner_id = 'fakeid'
        modprobe = 'modprobe dm_multipath'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode "*"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e %s > /etc/multipath.conf' % conf_file
        self.sles11_dist._set_zfcp_multipath(assigner_id)
        exec_cmd.assert_has_calls([mock.call(assigner_id, modprobe),
                                   mock.call(assigner_id, cmd_conf)])
        restart_multipath.assert_called_with(assigner_id)

        self.sles12_dist._set_zfcp_multipath(assigner_id)
        exec_cmd.assert_has_calls([mock.call(assigner_id, modprobe),
                                   mock.call(assigner_id, cmd_conf)])
        restart_multipath.assert_called_with(assigner_id)


class UBUNTUTestCase(base.SDKTestCase):

    @classmethod
    def setUpClass(cls):
        super(UBUNTUTestCase, cls).setUpClass()

    def setUp(self):
        super(UBUNTUTestCase, self).setUp()
        self.dist_manager = dist.LinuxDistManager()
        self.linux_dist = self.dist_manager.get_linux_dist('ubuntu16')()

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_check_multipath_tools(self, exec_cmd):
        assigner_id = 'fakeid'
        multipath = 'multipath'
        errmsg = 'multipath-tools not installed.'
        self.linux_dist._check_multipath_tools(assigner_id)
        exec_cmd.assert_called_with(assigner_id, multipath, msg=errmsg)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_restart_multipath(self, exec_cmd):
        assigner_id = 'fakeid'
        self.linux_dist._restart_multipath(assigner_id)
        reload_map = 'systemctl restart multipath-tools.service'
        exec_cmd.assert_called_with(assigner_id, reload_map)

    @mock.patch('zvmsdk.dist.ubuntu._restart_multipath')
    @mock.patch('zvmsdk.dist.ubuntu._check_multipath_tools')
    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_set_zfcp_multipath(self, exec_cmd, check_multipath,
                                restart_multipath):
        assigner_id = 'fakeid'
        conf_file = '#blacklist {\n'
        conf_file += '#\tdevnode "*"\n'
        conf_file += '#}\n'
        cmd_conf = 'echo -e %s > /etc/multipath.conf' % conf_file
        self.linux_dist._set_zfcp_multipath(assigner_id)
        check_multipath.assert_called_with(assigner_id)
        exec_cmd.assert_called_with(assigner_id, cmd_conf)
        restart_multipath.assert_called_with(assigner_id)

    @mock.patch.object(dist.LinuxDist, 'execute_cmd')
    def test_offline_fcp_device(self, exec_cmd):
        fcp = '1fc5'
        assigner_id = 'fakeid'
        target_wwpn = '0x5005076812341234'
        target_lun = '0x0026000000000000'
        multipath = True
        device = '0.0.%s' % fcp
        target = '%s:%s:%s' % (device, target_wwpn, target_lun)
        disk_offline = '/sbin/chzdev zfcp-lun %s -d' % target
        host_offline = '/sbin/chzdev zfcp-host %s -d' % fcp
        offline_dev = 'chccwdev -d %s' % fcp
        self.linux_dist._offline_fcp_device(assigner_id, fcp,
                                            target_wwpn, target_lun, multipath)
        exec_cmd.assert_has_calls([mock.call(assigner_id, disk_offline),
                                   mock.call(assigner_id, host_offline),
                                   mock.call(assigner_id, offline_dev)])
