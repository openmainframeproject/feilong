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

from zvmsdk import config
from zvmsdk import dist
from zvmsdk import log
from zvmsdk import smutclient
from zvmsdk import utils as zvmutils


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
        self._smutclient = smutclient.get_smutclient()
        self._dist_manager = dist.LinuxDistManager()

    def create_nic(self, userid, vdev=None, nic_id=None,
                   mac_addr=None, active=False):
        zvmutils.check_guest_exist(userid)

        return self._smutclient.create_nic(userid, vdev=vdev, nic_id=nic_id,
                                           mac_addr=mac_addr, active=active)

    def get_vm_nic_vswitch_info(self, userid):
        zvmutils.check_guest_exist(userid)

        return self._smutclient.get_vm_nic_vswitch_info(userid)

    def get_vswitch_list(self):
        return self._smutclient.get_vswitch_list()

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False):
        zvmutils.check_guest_exist(userid)

        self._smutclient.couple_nic_to_vswitch(userid, nic_vdev,
                                               vswitch_name, active=active)

    def uncouple_nic_from_vswitch(self, userid, nic_vdev,
                                  active=False):
        zvmutils.check_guest_exist(userid)

        self._smutclient.uncouple_nic_from_vswitch(userid,
                                                   nic_vdev,
                                                   active=active)

    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='IP',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):
        self._smutclient.add_vswitch(name, rdev=rdev, controller=controller,
                                     connection=connection,
                                     network_type=network_type,
                                     router=router, vid=vid,
                                     port_type=port_type, gvrp=gvrp,
                                     queue_mem=queue_mem,
                                     native_vid=native_vid,
                                     persist=persist)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        self._smutclient.grant_user_to_vswitch(vswitch_name, userid)

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        self._smutclient.revoke_user_from_vswitch(vswitch_name, userid)

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        self._smutclient.set_vswitch_port_vlan_id(vswitch_name, userid,
                                                  vlan_id)

    def set_vswitch(self, vswitch_name, **kwargs):
        self._smutclient.set_vswitch(vswitch_name, **kwargs)

    def delete_vswitch(self, vswitch_name, persist=True):
        self._smutclient.delete_vswitch(vswitch_name, persist)

    def delete_nic(self, userid, vdev, active=False):
        zvmutils.check_guest_exist(userid)

        self._smutclient.delete_nic(userid, vdev,
                                    active=active)

    def network_configuration(self, userid, os_version, network_info,
                              active=False):
        network_file_path = self._smutclient.get_guest_temp_path(userid,
                                                                 'network')
        LOG.debug('Creating folder %s to contain network configuration files'
                  % network_file_path)
        # check whether network interface has already been set for the guest
        # if not, means this the first time to set the network interface
        first = self._smutclient.is_first_network_config(userid)
        (network_doscript, active_cmds) = self._generate_network_doscript(
                                                           userid,
                                                           os_version,
                                                           network_info,
                                                           network_file_path,
                                                           first,
                                                           active=active)
        fileClass = "X"
        try:
            self._smutclient.punch_file(userid, network_doscript, fileClass)
        finally:
            LOG.debug('Removing the folder %s ', network_file_path)
            shutil.rmtree(network_file_path)

        # update guest db to mark the network is already set
        if first:
            self._smutclient.update_guestdb_with_net_set(userid)

        # using zvmguestconfigure tool to parse network_doscript
        if active:
            self._smutclient.execute_cmd(userid, active_cmds)

    # Prepare and create network doscript for instance
    def _generate_network_doscript(self, userid, os_version, network_info,
                                   network_file_path, first, active=False):
        path_contents = []
        content_dir = {}
        files_map = []

        # Create network configuration files
        LOG.debug('Creating network configuration files '
                  'for guest %s in the folder %s' %
                  (userid, network_file_path))
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        files_and_cmds = linuxdist.create_network_configuration_files(
                             network_file_path, network_info,
                             first, active=active)

        (net_conf_files, net_conf_cmds,
         clean_cmd, net_enable_cmd) = files_and_cmds

        # Add network configure files to path_contents
        if len(net_conf_files) > 0:
            path_contents.extend(net_conf_files)

        # restart_cmds = ''
        # if active:
        #    restart_cmds = linuxdist.restart_network()
        net_cmd_file = self._create_znetconfig(net_conf_cmds,
                                               linuxdist,
                                               net_enable_cmd,
                                               active=active)
        # Add znetconfig file to path_contents
        if len(net_cmd_file) > 0:
            path_contents.extend(net_cmd_file)

        for (path, contents) in path_contents:
            key = "%04i" % len(content_dir)
            files_map.append({'target_path': path,
                        'source_file': "%s" % key})
            content_dir[key] = contents
            file_name = os.path.join(network_file_path, key)
            self._add_file(file_name, contents)

        self._create_invokeScript(network_file_path, clean_cmd, files_map)
        network_doscript = self._create_network_doscript(network_file_path)

        # get command about zvmguestconfigure
        active_cmds = ''
        if active:
            active_cmds = linuxdist.create_active_net_interf_cmd()

        return network_doscript, active_cmds

    def _add_file(self, file_name, data):
        with open(file_name, "w") as f:
            f.write(data)

    def _create_znetconfig(self, commands, linuxdist, append_cmd,
                           active=False):
        LOG.debug('Creating znetconfig file')
        if active:
            znet_content = linuxdist.get_simple_znetconfig_contents()
        else:
            znet_content = linuxdist.get_znetconfig_contents()
        net_cmd_file = []
        if znet_content:
            if len(commands) == 0:
                znetconfig = '\n'.join(('#!/bin/bash', znet_content))
            else:
                znetconfig = '\n'.join(('#!/bin/bash', commands,
                                        'sleep 2', znet_content))
            if len(append_cmd) > 0:
                znetconfig += '\n%s\n' % append_cmd
            znetconfig += '\nrm -rf /tmp/znetconfig.sh\n'
            # Create a temp file in instance to execute above commands
            net_cmd_file.append(('/tmp/znetconfig.sh', znetconfig))  # nosec

        return net_cmd_file

    def _create_invokeScript(self, network_file_path, commands,
                             files_map):
        """invokeScript: Configure zLinux os network

        invokeScript is included in the network.doscript, it is used to put
        the network configuration file to the directory where it belongs and
        call znetconfig to configure the network
        """
        LOG.debug('Creating invokeScript shell in the folder %s'
                  % network_file_path)
        invokeScript = "invokeScript.sh"

        conf = "#!/bin/bash \n"
        command = commands
        for file in files_map:
            target_path = file['target_path']
            source_file = file['source_file']
            # potential risk: whether target_path exist
            command += 'mv ' + source_file + ' ' + target_path + '\n'

        command += 'sleep 2\n'
        command += '/bin/bash /tmp/znetconfig.sh\n'
        command += 'rm -rf invokeScript.sh\n'

        scriptfile = os.path.join(network_file_path, invokeScript)
        with open(scriptfile, "w") as f:
            f.write(conf)
            f.write(command)

    def _create_network_doscript(self, network_file_path):
        """doscript: contains a invokeScript.sh which will do the special work

        The network.doscript contains network configuration files and it will
        be used by zvmguestconfigure to configure zLinux os network when it
        starts up
        """
        # Generate the tar package for punch
        LOG.debug('Creating network doscript in the folder %s'
                  % network_file_path)
        network_doscript = os.path.join(network_file_path, 'network.doscript')
        tar = tarfile.open(network_doscript, "w")
        for file in os.listdir(network_file_path):
            file_name = os.path.join(network_file_path, file)
            tar.add(file_name, arcname=file)
        tar.close()
        return network_doscript

    def get_nic_info(self, userid=None, nic_id=None, vswitch=None):
        return self._smutclient.get_nic_info(userid=userid, nic_id=nic_id,
                                             vswitch=vswitch)
