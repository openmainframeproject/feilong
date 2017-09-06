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
import shutil
import tarfile

from zvmsdk import client as zvmclient
from zvmsdk import config
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log


_NetworkOPS = None
CONF = config.CONF
LOG = log.LOG


def get_networkops():
    global _NetworkOPS
    if _NetworkOPS is None:
        _NetworkOPS = NetworkOPS()
    return _NetworkOPS


class NetworkOPS(object):
    """Configuration check and manage MAC address API
       oriented towards SDK driver
    """
    def __init__(self):
        self.zvmclient = zvmclient.get_zvmclient()
        self._dist_manager = dist.LinuxDistManager()

    def create_nic(self, vm_id, vdev=None, nic_id=None,
                   mac_addr=None, ip_addr=None, active=False):
        return self.zvmclient.create_nic(vm_id, vdev=vdev, nic_id=nic_id,
                                         mac_addr=mac_addr, ip_addr=ip_addr,
                                         active=active)

    def get_vm_nic_vswitch_info(self, vm_id):
        return self.zvmclient.get_vm_nic_vswitch_info(vm_id)

    def get_vswitch_list(self):
        return self.zvmclient.get_vswitch_list()

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False):
        self.zvmclient.couple_nic_to_vswitch(userid, nic_vdev,
                                             vswitch_name, active=active)

    def uncouple_nic_from_vswitch(self, userid, nic_vdev,
                                  active=False):
        self.zvmclient.uncouple_nic_from_vswitch(userid,
                                                 nic_vdev,
                                                 active=active)

    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='IP',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):
        self.zvmclient.add_vswitch(name, rdev=rdev, controller=controller,
                                   connection=connection,
                                   network_type=network_type,
                                   router=router, vid=vid,
                                   port_type=port_type, gvrp=gvrp,
                                   queue_mem=queue_mem,
                                   native_vid=native_vid,
                                   persist=persist)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        self.zvmclient.grant_user_to_vswitch(vswitch_name, userid)

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        self.zvmclient.revoke_user_from_vswitch(vswitch_name, userid)

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        self.zvmclient.set_vswitch_port_vlan_id(vswitch_name, userid, vlan_id)

    def set_vswitch(self, vswitch_name, **kwargs):
        self.zvmclient.set_vswitch(vswitch_name, **kwargs)

    def delete_vswitch(self, vswitch_name, persist=True):
        self.zvmclient.delete_vswitch(vswitch_name, persist)

    def delete_nic(self, userid, vdev, active=False):
        self.zvmclient.delete_nic(userid, vdev,
                                  active=active)

    def network_configuration(self, userid, os_version, network_info):
        if len(network_info) == 0:
            raise exception.ZVMInvalidInput(
                    msg="Network information is required")
        os_node = CONF.zvm.host
        instance_path = self.zvmclient.get_instance_path(os_node, userid)
        network_doscript = self._generate_network_doscript(userid,
                                                           os_version,
                                                           network_info,
                                                           instance_path)
        fileClass = "X"
        try:
            self.zvmclient.punch_file(userid, network_doscript, fileClass)
        finally:
            LOG.debug('Removing the instance path %s ', instance_path)
            shutil.rmtree(instance_path)

    # Prepare and create network doscript for instance
    def _generate_network_doscript(self, userid, os_version,
                                   network_info, instance_path):
        path_contents = []
        content_dir = {}
        files_map = []

        # Create network configuration files
        LOG.debug('Creating network configuration files '
                  'for guest: %s' % userid)
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        files_and_cmds = linuxdist.create_network_configuration_files(
                             instance_path, network_info)

        (net_conf_files, net_conf_cmds) = files_and_cmds

        # Add network configure files to path_contents
        if len(net_conf_files) > 0:
            path_contents.extend(net_conf_files)

        net_cmd_file = self._create_znetconfig(net_conf_cmds,
                                               linuxdist)
        # Add znetconfig file to path_contents
        if len(net_cmd_file) > 0:
            path_contents.extend(net_cmd_file)

        if len(path_contents) == 0:
            raise exception.ZVMNetworkError(
                        msg="Failed to generate network configuration files")

        for (path, contents) in path_contents:
            key = "%04i" % len(content_dir)
            files_map.append({'target_path': path,
                        'source_file': "%s" % key})
            content_dir[key] = contents
            filepath = os.path.join(instance_path, key)
            self._add_file(filepath, contents)

        self._create_invokeScript(instance_path, files_map)
        network_doscript = self._create_network_doscript(instance_path)
        return network_doscript

    def _add_file(self, filepath, data):
        f = open(filepath, "wb")
        f.write(data)
        f.close()

    def _remove_file(self, filepath):
        for file in os.listdir(filepath):
            os.remove(filepath + "/" + file)

    def _create_znetconfig(self, commands, linuxdist):
        LOG.debug('Creating znetconfig file')

        udev_settle = linuxdist.get_znetconfig_contents()
        net_cmd_file = []
        if udev_settle:
            if len(commands) == 0:
                znetconfig = '\n'.join(('#!/bin/bash', udev_settle))
            else:
                znetconfig = '\n'.join(('#!/bin/bash', commands, udev_settle))
            znetconfig += '\nrm -rf /tmp/znetconfig.sh\n'
            # Create a temp file in instance to execute above commands
            net_cmd_file.append(('/tmp/znetconfig.sh', znetconfig))  # nosec

        return net_cmd_file

    def _create_invokeScript(self, instance_path, files_map):
        LOG.debug('Creating invokeScript shell')
        invokeScript = "invokeScript.sh"

        conf = "#!/bin/bash \n"
        command = ''
        for file in files_map:
            target_path = file['target_path']
            source_file = file['source_file']
            # potential risk: whether target_path exist
            command += 'mv ' + source_file + ' ' + target_path + '\n'

        command += '/bin/bash /tmp/znetconfig.sh\n'
        command += '/bin/bash rm -rf invokeScript.sh\n'

        fh = open(instance_path + "/" + invokeScript, "w")
        fh.write(conf)
        fh.write(command)
        fh.close()

    def _create_network_doscript(self, instance_path):
        # Generate the tar package for punch
        LOG.debug('Creating network doscript')
        network_doscript = os.path.join(instance_path, 'network.doscript')
        tar = tarfile.open(network_doscript, "w")
        for file in os.listdir(instance_path):
            tar.add(instance_path + "/" + file, arcname=file)
        tar.close()
        return network_doscript
